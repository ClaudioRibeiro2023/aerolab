"""
Memory v2 - Long-Term Memory

Memória de longo prazo usando PostgreSQL + pgvector.
Armazena conhecimento persistente com busca semântica.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
import logging

import asyncpg
from asyncpg import Pool
from openai import AsyncOpenAI

from .config import MemoryConfig, get_memory_config
from .types import Memory, MemoryType, MemoryQuery, MemorySearchResult, MemoryStatus


logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Long-Term Memory com PostgreSQL + pgvector.
    
    Features:
    - Armazenamento persistente de memórias
    - Busca semântica por embedding
    - Decay temporal para relevância
    - Consolidação de memórias similares
    """
    
    CREATE_TABLES_SQL = """
    -- Habilitar extensão vector
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- Tabela de memórias de longo prazo
    CREATE TABLE IF NOT EXISTS long_term_memories (
        id VARCHAR(64) PRIMARY KEY,
        content TEXT NOT NULL,
        summary TEXT,
        embedding vector({dimensions}),
        
        -- Contexto
        agent_id VARCHAR(64),
        user_id VARCHAR(64),
        project_id INTEGER,
        
        -- Relevância
        importance_score FLOAT DEFAULT 0.5,
        access_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMP,
        
        -- Status
        status VARCHAR(32) DEFAULT 'active',
        priority VARCHAR(32) DEFAULT 'medium',
        
        -- Relacionamentos
        parent_id VARCHAR(64),
        related_ids JSONB DEFAULT '[]',
        
        -- Tags e metadados
        tags JSONB DEFAULT '[]',
        metadata JSONB DEFAULT '{{}}',
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Índices
    CREATE INDEX IF NOT EXISTS idx_ltm_agent ON long_term_memories(agent_id);
    CREATE INDEX IF NOT EXISTS idx_ltm_user ON long_term_memories(user_id);
    CREATE INDEX IF NOT EXISTS idx_ltm_project ON long_term_memories(project_id);
    CREATE INDEX IF NOT EXISTS idx_ltm_status ON long_term_memories(status);
    CREATE INDEX IF NOT EXISTS idx_ltm_created ON long_term_memories(created_at);
    
    -- Índice HNSW para busca vetorial
    CREATE INDEX IF NOT EXISTS idx_ltm_embedding_hnsw ON long_term_memories 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    
    -- Tabela de consolidações
    CREATE TABLE IF NOT EXISTS memory_consolidations (
        id SERIAL PRIMARY KEY,
        source_ids JSONB NOT NULL,
        result_id VARCHAR(64) NOT NULL,
        consolidation_type VARCHAR(32),
        similarity_score FLOAT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        self.ltm_config = self.config.long_term
        
        self._pool: Optional[Pool] = None
        self._openai: Optional[AsyncOpenAI] = None
        
        # Métricas
        self.total_stored = 0
        self.total_retrieved = 0
        self.consolidations = 0
    
    async def _get_pool(self) -> Pool:
        """Retorna pool de conexões."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.config.postgres.url,
                min_size=2,
                max_size=10
            )
        return self._pool
    
    async def _get_openai(self) -> AsyncOpenAI:
        """Retorna cliente OpenAI."""
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=self.config.embedding.openai_api_key)
        return self._openai
    
    async def initialize(self) -> None:
        """Inicializa banco de dados."""
        pool = await self._get_pool()
        
        sql = self.CREATE_TABLES_SQL.replace(
            "{dimensions}",
            str(self.ltm_config.embedding_dimensions)
        )
        
        async with pool.acquire() as conn:
            await conn.execute(sql)
        
        logger.info("Long-term memory inicializada")
    
    async def _generate_embedding(self, text: str) -> list[float]:
        """Gera embedding para o texto."""
        client = await self._get_openai()
        
        response = await client.embeddings.create(
            model=self.ltm_config.embedding_model,
            input=text,
            dimensions=self.ltm_config.embedding_dimensions
        )
        
        return response.data[0].embedding
    
    async def store(self, memory: Memory) -> str:
        """
        Armazena uma memória de longo prazo.
        
        Args:
            memory: Memória a armazenar
            
        Returns:
            ID da memória
        """
        pool = await self._get_pool()
        
        # Garantir tipo correto
        memory.memory_type = MemoryType.LONG_TERM
        memory.updated_at = datetime.now()
        
        # Gerar embedding se não existir
        if memory.embedding is None:
            memory.embedding = await self._generate_embedding(memory.content)
        
        embedding_str = "[" + ",".join(str(x) for x in memory.embedding) + "]"
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO long_term_memories (
                    id, content, summary, embedding,
                    agent_id, user_id, project_id,
                    importance_score, access_count, last_accessed,
                    status, priority, parent_id, related_ids,
                    tags, metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4::vector,
                    $5, $6, $7,
                    $8, $9, $10,
                    $11, $12, $13, $14,
                    $15, $16, $17, $18
                )
                ON CONFLICT (id) DO UPDATE SET
                    content = $2,
                    summary = $3,
                    embedding = $4::vector,
                    importance_score = $8,
                    access_count = $9,
                    last_accessed = $10,
                    status = $11,
                    priority = $12,
                    related_ids = $14,
                    tags = $15,
                    metadata = $16,
                    updated_at = $18
            """,
                memory.id, memory.content, memory.summary, embedding_str,
                memory.agent_id, memory.user_id, memory.project_id,
                memory.importance_score, memory.access_count, memory.last_accessed,
                memory.status.value, memory.priority.value, memory.parent_id,
                json.dumps(memory.related_ids),
                json.dumps(memory.tags), json.dumps(memory.metadata),
                memory.created_at, memory.updated_at
            )
        
        self.total_stored += 1
        logger.debug(f"Memória {memory.id} armazenada no long-term")
        
        return memory.id
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """
        Recupera uma memória por ID.
        
        Args:
            memory_id: ID da memória
            
        Returns:
            Memory ou None
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM long_term_memories WHERE id = $1
            """, memory_id)
            
            if not row:
                return None
            
            # Atualizar acesso
            await conn.execute("""
                UPDATE long_term_memories 
                SET access_count = access_count + 1, last_accessed = NOW()
                WHERE id = $1
            """, memory_id)
        
        self.total_retrieved += 1
        
        return self._row_to_memory(row)
    
    def _row_to_memory(self, row) -> Memory:
        """Converte row do banco para Memory."""
        return Memory(
            id=row["id"],
            content=row["content"],
            summary=row["summary"],
            memory_type=MemoryType.LONG_TERM,
            priority=row["priority"],
            status=MemoryStatus(row["status"]),
            agent_id=row["agent_id"],
            user_id=row["user_id"],
            project_id=row["project_id"],
            importance_score=row["importance_score"],
            access_count=row["access_count"],
            last_accessed=row["last_accessed"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            parent_id=row["parent_id"],
            related_ids=json.loads(row["related_ids"]) if row["related_ids"] else []
        )
    
    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 10,
        threshold: float = 0.5
    ) -> list[MemorySearchResult]:
        """
        Busca memórias por similaridade semântica.
        
        Args:
            query: Query de busca
            agent_id: Filtrar por agente
            user_id: Filtrar por usuário
            project_id: Filtrar por projeto
            limit: Número máximo de resultados
            threshold: Threshold mínimo de similaridade
            
        Returns:
            Lista de MemorySearchResult
        """
        pool = await self._get_pool()
        
        # Gerar embedding da query
        query_embedding = await self._generate_embedding(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Construir filtros
        filters = ["status = 'active'"]
        params = [embedding_str, limit]
        param_idx = 3
        
        if agent_id:
            filters.append(f"agent_id = ${param_idx}")
            params.append(agent_id)
            param_idx += 1
        
        if user_id:
            filters.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if project_id:
            filters.append(f"project_id = ${param_idx}")
            params.append(project_id)
            param_idx += 1
        
        where_clause = " AND ".join(filters)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *,
                       1 - (embedding <=> $1::vector) as similarity
                FROM long_term_memories
                WHERE {where_clause}
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, *params)
            
            results = []
            for row in rows:
                similarity = row["similarity"]
                
                if similarity < threshold:
                    continue
                
                memory = self._row_to_memory(row)
                
                # Aplicar decay temporal
                if self.config.enable_decay:
                    decay = memory.calculate_decay(self.ltm_config.decay_rate)
                    effective_score = similarity * decay
                else:
                    effective_score = similarity
                
                results.append(MemorySearchResult(
                    memory=memory,
                    score=effective_score,
                    match_type="semantic"
                ))
            
            # Reordenar por score efetivo
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results
    
    async def search_by_query(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """
        Busca usando MemoryQuery estruturado.
        
        Args:
            query: Query estruturada
            
        Returns:
            Lista de resultados
        """
        return await self.search(
            query=query.query,
            agent_id=query.agent_id,
            user_id=query.user_id,
            project_id=query.project_id,
            limit=query.limit
        )
    
    async def find_similar(
        self,
        memory_id: str,
        limit: int = 5,
        threshold: float = 0.8
    ) -> list[MemorySearchResult]:
        """
        Encontra memórias similares a uma memória existente.
        
        Args:
            memory_id: ID da memória de referência
            limit: Número de resultados
            threshold: Threshold de similaridade
            
        Returns:
            Lista de memórias similares
        """
        memory = await self.get(memory_id)
        if not memory:
            return []
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Buscar embedding da memória
            row = await conn.fetchrow("""
                SELECT embedding FROM long_term_memories WHERE id = $1
            """, memory_id)
            
            if not row or not row["embedding"]:
                return []
            
            embedding_str = str(row["embedding"])
            
            # Buscar similares
            rows = await conn.fetch("""
                SELECT *,
                       1 - (embedding <=> $1::vector) as similarity
                FROM long_term_memories
                WHERE id != $2
                  AND status = 'active'
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """, embedding_str, memory_id, limit)
            
            results = []
            for row in rows:
                if row["similarity"] >= threshold:
                    results.append(MemorySearchResult(
                        memory=self._row_to_memory(row),
                        score=row["similarity"],
                        match_type="similar"
                    ))
            
            return results
    
    async def consolidate_similar(
        self,
        threshold: float = 0.9,
        max_consolidations: int = 10
    ) -> int:
        """
        Consolida memórias muito similares.
        
        Memórias com alta similaridade são mescladas para
        reduzir redundância e melhorar eficiência.
        
        Args:
            threshold: Threshold de similaridade para consolidação
            max_consolidations: Máximo de consolidações por execução
            
        Returns:
            Número de consolidações realizadas
        """
        pool = await self._get_pool()
        consolidation_count = 0
        
        async with pool.acquire() as conn:
            # Buscar memórias ativas ordenadas por criação
            rows = await conn.fetch("""
                SELECT id, content, embedding FROM long_term_memories
                WHERE status = 'active' AND embedding IS NOT NULL
                ORDER BY created_at
                LIMIT 100
            """)
            
            processed = set()
            
            for i, row in enumerate(rows):
                if row["id"] in processed or consolidation_count >= max_consolidations:
                    continue
                
                # Buscar similares a esta memória
                similar = await conn.fetch("""
                    SELECT id, content,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM long_term_memories
                    WHERE id != $2
                      AND status = 'active'
                      AND embedding IS NOT NULL
                      AND 1 - (embedding <=> $1::vector) >= $3
                    LIMIT 5
                """, str(row["embedding"]), row["id"], threshold)
                
                if similar:
                    # Marcar todas como processadas
                    similar_ids = [s["id"] for s in similar]
                    processed.add(row["id"])
                    processed.update(similar_ids)
                    
                    # Criar memória consolidada
                    all_content = row["content"] + "\n\n" + "\n\n".join(s["content"] for s in similar)
                    
                    # Gerar sumário da consolidação
                    openai = await self._get_openai()
                    summary_response = await openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "user", "content": f"Summarize these related memories in one concise paragraph:\n\n{all_content[:2000]}"}
                        ],
                        max_tokens=200
                    )
                    summary = summary_response.choices[0].message.content
                    
                    # Criar nova memória consolidada
                    consolidated = Memory(
                        content=summary,
                        summary=f"Consolidated from {len(similar) + 1} memories",
                        memory_type=MemoryType.LONG_TERM,
                        status=MemoryStatus.CONSOLIDATED,
                        related_ids=[row["id"]] + similar_ids
                    )
                    
                    await self.store(consolidated)
                    
                    # Arquivar memórias originais
                    await conn.execute("""
                        UPDATE long_term_memories
                        SET status = 'archived', parent_id = $1
                        WHERE id = ANY($2)
                    """, consolidated.id, [row["id"]] + similar_ids)
                    
                    # Registrar consolidação
                    await conn.execute("""
                        INSERT INTO memory_consolidations (source_ids, result_id, consolidation_type, similarity_score)
                        VALUES ($1, $2, 'merge', $3)
                    """, json.dumps([row["id"]] + similar_ids), consolidated.id, threshold)
                    
                    consolidation_count += 1
                    self.consolidations += 1
        
        return consolidation_count
    
    async def delete(self, memory_id: str) -> bool:
        """Remove uma memória."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM long_term_memories WHERE id = $1
            """, memory_id)
            
            return "DELETE 1" in result
    
    async def archive(self, memory_id: str) -> bool:
        """Arquiva uma memória."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE long_term_memories SET status = 'archived' WHERE id = $1
            """, memory_id)
            
            return "UPDATE 1" in result
    
    async def get_stats(self, agent_id: Optional[str] = None) -> dict:
        """Retorna estatísticas."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            if agent_id:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM long_term_memories
                    WHERE agent_id = $1 AND status = 'active'
                """, agent_id)
            else:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM long_term_memories WHERE status = 'active'
                """)
            
            return {
                "total_memories": count,
                "total_stored": self.total_stored,
                "total_retrieved": self.total_retrieved,
                "consolidations": self.consolidations
            }
    
    def get_metrics(self) -> dict:
        """Retorna métricas."""
        return {
            "total_stored": self.total_stored,
            "total_retrieved": self.total_retrieved,
            "consolidations": self.consolidations
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._pool:
            await self._pool.close()


# Singleton
_long_term_memory: Optional[LongTermMemory] = None


def get_long_term_memory(config: Optional[MemoryConfig] = None) -> LongTermMemory:
    """Retorna o long-term memory singleton."""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemory(config)
    return _long_term_memory

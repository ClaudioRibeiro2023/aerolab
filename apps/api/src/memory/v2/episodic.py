"""
Memory v2 - Episodic Memory

Memória episódica usando PostgreSQL.
Armazena histórico de execuções para aprendizado.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import logging

import asyncpg
from asyncpg import Pool

from .config import MemoryConfig, get_memory_config
from .types import Episode


logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Episodic Memory com PostgreSQL.
    
    Features:
    - Registro de episódios (execuções completas)
    - Busca por tarefas similares
    - Aprendizado de padrões
    - Replay de experiências bem-sucedidas
    """
    
    CREATE_TABLES_SQL = """
    -- Tabela de episódios
    CREATE TABLE IF NOT EXISTS episodes (
        id VARCHAR(64) PRIMARY KEY,
        agent_id VARCHAR(64) NOT NULL,
        session_id VARCHAR(64),
        user_id VARCHAR(64),
        project_id INTEGER,
        
        -- Tarefa
        task_description TEXT NOT NULL,
        task_type VARCHAR(64),
        
        -- Execução
        steps JSONB DEFAULT '[]',
        tool_calls JSONB DEFAULT '[]',
        decisions JSONB DEFAULT '[]',
        
        -- Resultado
        outcome VARCHAR(32),
        result TEXT,
        error TEXT,
        
        -- Métricas
        duration_ms FLOAT DEFAULT 0,
        token_count INTEGER DEFAULT 0,
        tool_call_count INTEGER DEFAULT 0,
        
        -- Avaliação
        user_feedback TEXT,
        rating FLOAT,
        lessons_learned JSONB DEFAULT '[]',
        
        -- Timestamps
        started_at TIMESTAMP DEFAULT NOW(),
        completed_at TIMESTAMP,
        
        -- Metadados
        metadata JSONB DEFAULT '{}'
    );
    
    -- Índices
    CREATE INDEX IF NOT EXISTS idx_episodes_agent ON episodes(agent_id);
    CREATE INDEX IF NOT EXISTS idx_episodes_user ON episodes(user_id);
    CREATE INDEX IF NOT EXISTS idx_episodes_project ON episodes(project_id);
    CREATE INDEX IF NOT EXISTS idx_episodes_outcome ON episodes(outcome);
    CREATE INDEX IF NOT EXISTS idx_episodes_task_type ON episodes(task_type);
    CREATE INDEX IF NOT EXISTS idx_episodes_started ON episodes(started_at);
    CREATE INDEX IF NOT EXISTS idx_episodes_rating ON episodes(rating);
    
    -- Full-text search
    CREATE INDEX IF NOT EXISTS idx_episodes_task_gin ON episodes 
        USING gin(to_tsvector('english', task_description));
    
    -- Tabela de padrões aprendidos
    CREATE TABLE IF NOT EXISTS learned_patterns (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(64) NOT NULL,
        pattern_type VARCHAR(64) NOT NULL,
        pattern_data JSONB NOT NULL,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        confidence FLOAT DEFAULT 0.5,
        last_used TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_patterns_agent ON learned_patterns(agent_id);
    CREATE INDEX IF NOT EXISTS idx_patterns_type ON learned_patterns(pattern_type);
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        self.episodic_config = self.config.episodic
        
        self._pool: Optional[Pool] = None
        
        # Métricas
        self.total_episodes = 0
        self.successful_episodes = 0
        self.patterns_learned = 0
    
    async def _get_pool(self) -> Pool:
        """Retorna pool de conexões."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.config.postgres.url,
                min_size=2,
                max_size=10
            )
        return self._pool
    
    async def initialize(self) -> None:
        """Inicializa banco de dados."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute(self.CREATE_TABLES_SQL)
        
        logger.info("Episodic memory inicializada")
    
    async def start_episode(
        self,
        agent_id: str,
        task_description: str,
        task_type: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Episode:
        """
        Inicia um novo episódio.
        
        Args:
            agent_id: ID do agente
            task_description: Descrição da tarefa
            task_type: Tipo da tarefa
            session_id: ID da sessão
            user_id: ID do usuário
            project_id: ID do projeto
            
        Returns:
            Episode criado
        """
        episode = Episode(
            agent_id=agent_id,
            task_description=task_description,
            task_type=task_type,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id
        )
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO episodes (
                    id, agent_id, session_id, user_id, project_id,
                    task_description, task_type, started_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                episode.id, agent_id, session_id, user_id, project_id,
                task_description, task_type, episode.started_at
            )
        
        self.total_episodes += 1
        logger.debug(f"Episódio {episode.id} iniciado")
        
        return episode
    
    async def update_episode(self, episode: Episode) -> None:
        """
        Atualiza um episódio em andamento.
        
        Args:
            episode: Episódio a atualizar
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE episodes SET
                    steps = $2,
                    tool_calls = $3,
                    decisions = $4,
                    token_count = $5,
                    tool_call_count = $6,
                    metadata = $7
                WHERE id = $1
            """,
                episode.id,
                json.dumps(episode.steps),
                json.dumps(episode.tool_calls),
                json.dumps(episode.decisions),
                episode.token_count,
                episode.tool_call_count,
                json.dumps(episode.metadata)
            )
    
    async def complete_episode(
        self,
        episode: Episode,
        outcome: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Finaliza um episódio.
        
        Args:
            episode: Episódio a finalizar
            outcome: Resultado (success, failure, partial)
            result: Resultado textual
            error: Mensagem de erro se houver
        """
        episode.complete(outcome, result, error)
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE episodes SET
                    steps = $2,
                    tool_calls = $3,
                    decisions = $4,
                    outcome = $5,
                    result = $6,
                    error = $7,
                    duration_ms = $8,
                    token_count = $9,
                    tool_call_count = $10,
                    completed_at = $11,
                    metadata = $12
                WHERE id = $1
            """,
                episode.id,
                json.dumps(episode.steps),
                json.dumps(episode.tool_calls),
                json.dumps(episode.decisions),
                outcome,
                result,
                error,
                episode.duration_ms,
                episode.token_count,
                episode.tool_call_count,
                episode.completed_at,
                json.dumps(episode.metadata)
            )
        
        if outcome == "success":
            self.successful_episodes += 1
        
        logger.debug(f"Episódio {episode.id} finalizado: {outcome}")
    
    async def get(self, episode_id: str) -> Optional[Episode]:
        """Recupera um episódio por ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM episodes WHERE id = $1
            """, episode_id)
            
            if not row:
                return None
            
            return self._row_to_episode(row)
    
    def _row_to_episode(self, row) -> Episode:
        """Converte row para Episode."""
        return Episode(
            id=row["id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            project_id=row["project_id"],
            task_description=row["task_description"],
            task_type=row["task_type"],
            steps=json.loads(row["steps"]) if row["steps"] else [],
            tool_calls=json.loads(row["tool_calls"]) if row["tool_calls"] else [],
            decisions=json.loads(row["decisions"]) if row["decisions"] else [],
            outcome=row["outcome"],
            result=row["result"],
            error=row["error"],
            duration_ms=row["duration_ms"] or 0,
            token_count=row["token_count"] or 0,
            tool_call_count=row["tool_call_count"] or 0,
            user_feedback=row["user_feedback"],
            rating=row["rating"],
            lessons_learned=json.loads(row["lessons_learned"]) if row["lessons_learned"] else [],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
    
    async def search_similar_tasks(
        self,
        task_description: str,
        agent_id: Optional[str] = None,
        successful_only: bool = True,
        limit: int = 5
    ) -> list[Episode]:
        """
        Busca episódios com tarefas similares.
        
        Args:
            task_description: Descrição da tarefa
            agent_id: Filtrar por agente
            successful_only: Retornar apenas sucessos
            limit: Número de resultados
            
        Returns:
            Lista de episódios similares
        """
        pool = await self._get_pool()
        
        # Construir query
        filters = []
        params = [task_description, limit]
        param_idx = 3
        
        if agent_id:
            filters.append(f"agent_id = ${param_idx}")
            params.append(agent_id)
            param_idx += 1
        
        if successful_only:
            filters.append("outcome = 'success'")
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *,
                       ts_rank(to_tsvector('english', task_description), 
                               plainto_tsquery('english', $1)) as rank
                FROM episodes
                WHERE {where_clause}
                  AND completed_at IS NOT NULL
                ORDER BY rank DESC, rating DESC NULLS LAST
                LIMIT $2
            """, *params)
            
            return [self._row_to_episode(row) for row in rows]
    
    async def get_best_approach(
        self,
        task_type: str,
        agent_id: str
    ) -> Optional[dict]:
        """
        Retorna a melhor abordagem conhecida para um tipo de tarefa.
        
        Args:
            task_type: Tipo de tarefa
            agent_id: ID do agente
            
        Returns:
            Dicionário com passos e ferramentas recomendadas
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Buscar episódios bem-sucedidos do mesmo tipo
            rows = await conn.fetch("""
                SELECT steps, tool_calls, decisions, rating
                FROM episodes
                WHERE agent_id = $1
                  AND task_type = $2
                  AND outcome = 'success'
                ORDER BY rating DESC NULLS LAST, completed_at DESC
                LIMIT 5
            """, agent_id, task_type)
            
            if not rows:
                return None
            
            # Analisar padrões comuns
            tool_frequency = {}
            step_patterns = []
            
            for row in rows:
                tools = json.loads(row["tool_calls"]) if row["tool_calls"] else []
                for tool in tools:
                    tool_name = tool.get("tool", "unknown")
                    tool_frequency[tool_name] = tool_frequency.get(tool_name, 0) + 1
                
                steps = json.loads(row["steps"]) if row["steps"] else []
                if steps:
                    step_patterns.append([s.get("action") for s in steps])
            
            # Ordenar ferramentas por frequência
            recommended_tools = sorted(
                tool_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                "task_type": task_type,
                "sample_count": len(rows),
                "recommended_tools": [t[0] for t in recommended_tools[:5]],
                "step_patterns": step_patterns[:3]
            }
    
    async def add_feedback(
        self,
        episode_id: str,
        feedback: str,
        rating: Optional[float] = None
    ) -> None:
        """
        Adiciona feedback do usuário a um episódio.
        
        Args:
            episode_id: ID do episódio
            feedback: Feedback textual
            rating: Avaliação numérica (0-5)
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE episodes SET
                    user_feedback = $2,
                    rating = $3
                WHERE id = $1
            """, episode_id, feedback, rating)
    
    async def add_lesson(self, episode_id: str, lesson: str) -> None:
        """
        Adiciona lição aprendida a um episódio.
        
        Args:
            episode_id: ID do episódio
            lesson: Lição aprendida
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE episodes SET
                    lessons_learned = lessons_learned || $2::jsonb
                WHERE id = $1
            """, episode_id, json.dumps([lesson]))
    
    async def learn_pattern(
        self,
        agent_id: str,
        pattern_type: str,
        pattern_data: dict,
        success: bool
    ) -> None:
        """
        Registra um padrão aprendido.
        
        Args:
            agent_id: ID do agente
            pattern_type: Tipo de padrão
            pattern_data: Dados do padrão
            success: Se foi bem-sucedido
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Verificar se padrão já existe
            existing = await conn.fetchrow("""
                SELECT id, success_count, failure_count FROM learned_patterns
                WHERE agent_id = $1 AND pattern_type = $2 AND pattern_data = $3
            """, agent_id, pattern_type, json.dumps(pattern_data))
            
            if existing:
                # Atualizar contadores
                if success:
                    await conn.execute("""
                        UPDATE learned_patterns SET
                            success_count = success_count + 1,
                            confidence = (success_count + 1.0) / (success_count + failure_count + 1.0),
                            last_used = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """, existing["id"])
                else:
                    await conn.execute("""
                        UPDATE learned_patterns SET
                            failure_count = failure_count + 1,
                            confidence = success_count / (success_count + failure_count + 1.0),
                            last_used = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """, existing["id"])
            else:
                # Criar novo padrão
                await conn.execute("""
                    INSERT INTO learned_patterns (
                        agent_id, pattern_type, pattern_data,
                        success_count, failure_count, confidence, last_used
                    ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                    agent_id, pattern_type, json.dumps(pattern_data),
                    1 if success else 0,
                    0 if success else 1,
                    1.0 if success else 0.0
                )
                
                self.patterns_learned += 1
    
    async def get_patterns(
        self,
        agent_id: str,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> list[dict]:
        """
        Retorna padrões aprendidos.
        
        Args:
            agent_id: ID do agente
            pattern_type: Filtrar por tipo
            min_confidence: Confiança mínima
            
        Returns:
            Lista de padrões
        """
        pool = await self._get_pool()
        
        filters = ["agent_id = $1", "confidence >= $2"]
        params = [agent_id, min_confidence]
        param_idx = 3
        
        if pattern_type:
            filters.append(f"pattern_type = ${param_idx}")
            params.append(pattern_type)
        
        where_clause = " AND ".join(filters)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT * FROM learned_patterns
                WHERE {where_clause}
                ORDER BY confidence DESC, last_used DESC
            """, *params)
            
            return [
                {
                    "pattern_type": row["pattern_type"],
                    "pattern_data": json.loads(row["pattern_data"]),
                    "confidence": row["confidence"],
                    "success_count": row["success_count"],
                    "failure_count": row["failure_count"]
                }
                for row in rows
            ]
    
    async def cleanup_old_episodes(self, days: Optional[int] = None) -> int:
        """
        Remove episódios antigos.
        
        Args:
            days: Dias para manter (usa configuração se não especificado)
            
        Returns:
            Número de episódios removidos
        """
        days = days or self.episodic_config.retention_days
        cutoff = datetime.now() - timedelta(days=days)
        
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM episodes WHERE started_at < $1
            """, cutoff)
            
            # Extrair número de linhas deletadas
            count = int(result.split()[-1]) if result else 0
            
            return count
    
    async def get_stats(self, agent_id: Optional[str] = None) -> dict:
        """Retorna estatísticas."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            if agent_id:
                total = await conn.fetchval("""
                    SELECT COUNT(*) FROM episodes WHERE agent_id = $1
                """, agent_id)
                successful = await conn.fetchval("""
                    SELECT COUNT(*) FROM episodes 
                    WHERE agent_id = $1 AND outcome = 'success'
                """, agent_id)
            else:
                total = await conn.fetchval("SELECT COUNT(*) FROM episodes")
                successful = await conn.fetchval("""
                    SELECT COUNT(*) FROM episodes WHERE outcome = 'success'
                """)
            
            return {
                "total_episodes": total,
                "successful_episodes": successful,
                "success_rate": successful / max(total, 1),
                "patterns_learned": self.patterns_learned
            }
    
    def get_metrics(self) -> dict:
        """Retorna métricas."""
        return {
            "total_episodes": self.total_episodes,
            "successful_episodes": self.successful_episodes,
            "patterns_learned": self.patterns_learned
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._pool:
            await self._pool.close()


# Singleton
_episodic_memory: Optional[EpisodicMemory] = None


def get_episodic_memory(config: Optional[MemoryConfig] = None) -> EpisodicMemory:
    """Retorna o episodic memory singleton."""
    global _episodic_memory
    if _episodic_memory is None:
        _episodic_memory = EpisodicMemory(config)
    return _episodic_memory

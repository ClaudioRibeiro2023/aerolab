"""
RAG v2 - Vector Store com pgvector

Implementação de vector store usando PostgreSQL com pgvector.
Suporta:
- Busca por similaridade de cosseno
- Índices HNSW para performance
- Full-text search com pg_trgm
- Hybrid search (vector + keyword)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from enum import Enum
import json
import logging

import asyncpg
from asyncpg import Pool
import numpy as np

from .config import RAGConfig, get_rag_config
from .embeddings import EmbeddingService, get_embedding_service


logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Tipos de índice vetorial."""
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"


@dataclass
class Document:
    """Documento armazenado."""
    id: Optional[int] = None
    project_id: int = 0
    title: str = ""
    content: str = ""
    source: Optional[str] = None
    content_type: Optional[str] = None
    metadata: Optional[dict] = None
    summary: Optional[str] = None
    chunk_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DocumentChunk:
    """Chunk de documento com embedding."""
    id: Optional[int] = None
    document_id: int = 0
    content: str = ""
    chunk_index: int = 0
    embedding: Optional[list[float]] = None
    previous_chunk: Optional[str] = None
    next_chunk: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    # Score de busca (não persistido)
    score: float = 0.0


@dataclass
class SearchResult:
    """Resultado de busca."""
    chunk: DocumentChunk
    document: Document
    score: float
    search_type: str  # vector, keyword, hybrid


class VectorStore:
    """
    Vector Store com PostgreSQL + pgvector.
    
    Features:
    - Armazenamento de documentos e chunks
    - Busca vetorial com similaridade de cosseno
    - Busca por keywords com full-text search
    - Hybrid search combinando ambos
    - Índices HNSW para performance
    """
    
    # SQL para criação de tabelas
    CREATE_TABLES_SQL = """
    -- Habilitar extensões
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    -- Tabela de documentos
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source VARCHAR(512),
        content_type VARCHAR(64),
        metadata JSONB,
        summary TEXT,
        chunk_count INTEGER DEFAULT 0,
        processing_status VARCHAR(32) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Índices para documentos
    CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
    CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
    CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
    CREATE INDEX IF NOT EXISTS idx_documents_content_trgm ON documents USING gin(content gin_trgm_ops);
    
    -- Tabela de chunks
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        embedding vector({dimensions}),
        previous_chunk TEXT,
        next_chunk TEXT,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Índices para chunks
    CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
    CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm ON document_chunks USING gin(content gin_trgm_ops);
    
    -- Índice HNSW para busca vetorial (mais eficiente)
    CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON document_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    
    -- Tabela de cache de queries
    CREATE TABLE IF NOT EXISTS rag_query_cache (
        id SERIAL PRIMARY KEY,
        query_hash VARCHAR(64) UNIQUE NOT NULL,
        query TEXT NOT NULL,
        result JSONB NOT NULL,
        retrieval_method VARCHAR(64),
        documents_retrieved INTEGER,
        hit_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMP DEFAULT NOW(),
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_cache_hash ON rag_query_cache(query_hash);
    CREATE INDEX IF NOT EXISTS idx_cache_expires ON rag_query_cache(expires_at);
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        self._pool: Optional[Pool] = None
        self._embedding_service: Optional[EmbeddingService] = None
    
    async def _get_pool(self) -> Pool:
        """Retorna pool de conexões."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.config.database.postgres_url,
                min_size=2,
                max_size=10
            )
        return self._pool
    
    async def _get_embedding_service(self) -> EmbeddingService:
        """Retorna serviço de embeddings."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service(self.config)
        return self._embedding_service
    
    async def initialize(self) -> None:
        """Inicializa banco de dados com tabelas e índices."""
        pool = await self._get_pool()
        
        # Substituir placeholder de dimensões
        sql = self.CREATE_TABLES_SQL.replace(
            "{dimensions}",
            str(self.config.embedding.dimensions)
        )
        
        async with pool.acquire() as conn:
            await conn.execute(sql)
        
        logger.info("Vector store inicializado com sucesso")
    
    async def add_document(self, doc: Document) -> int:
        """
        Adiciona um documento.
        
        Args:
            doc: Documento a adicionar
            
        Returns:
            ID do documento criado
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO documents (project_id, title, content, source, content_type, metadata, summary)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, doc.project_id, doc.title, doc.content, doc.source, 
                doc.content_type, json.dumps(doc.metadata) if doc.metadata else None, doc.summary)
            
            return row["id"]
    
    async def add_chunk(self, chunk: DocumentChunk) -> int:
        """
        Adiciona um chunk de documento.
        
        Args:
            chunk: Chunk a adicionar
            
        Returns:
            ID do chunk criado
        """
        pool = await self._get_pool()
        
        # Converter embedding para formato pgvector
        embedding_str = None
        if chunk.embedding:
            embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO document_chunks (document_id, content, chunk_index, embedding, 
                                            previous_chunk, next_chunk, metadata)
                VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                RETURNING id
            """, chunk.document_id, chunk.content, chunk.chunk_index, embedding_str,
                chunk.previous_chunk, chunk.next_chunk, 
                json.dumps(chunk.metadata) if chunk.metadata else None)
            
            # Atualizar contador de chunks no documento
            await conn.execute("""
                UPDATE documents SET chunk_count = chunk_count + 1, updated_at = NOW()
                WHERE id = $1
            """, chunk.document_id)
            
            return row["id"]
    
    async def add_chunks_batch(self, chunks: list[DocumentChunk]) -> list[int]:
        """
        Adiciona múltiplos chunks em batch.
        
        Args:
            chunks: Lista de chunks
            
        Returns:
            Lista de IDs criados
        """
        if not chunks:
            return []
        
        pool = await self._get_pool()
        ids = []
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                for chunk in chunks:
                    embedding_str = None
                    if chunk.embedding:
                        embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"
                    
                    row = await conn.fetchrow("""
                        INSERT INTO document_chunks (document_id, content, chunk_index, embedding,
                                                    previous_chunk, next_chunk, metadata)
                        VALUES ($1, $2, $3, $4::vector, $5, $6, $7)
                        RETURNING id
                    """, chunk.document_id, chunk.content, chunk.chunk_index, embedding_str,
                        chunk.previous_chunk, chunk.next_chunk,
                        json.dumps(chunk.metadata) if chunk.metadata else None)
                    
                    ids.append(row["id"])
                
                # Atualizar contador de chunks
                doc_ids = list(set(c.document_id for c in chunks))
                for doc_id in doc_ids:
                    count = sum(1 for c in chunks if c.document_id == doc_id)
                    await conn.execute("""
                        UPDATE documents SET chunk_count = chunk_count + $1, updated_at = NOW()
                        WHERE id = $2
                    """, count, doc_id)
        
        return ids
    
    async def search_vector(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        project_id: Optional[int] = None,
        threshold: float = 0.0
    ) -> list[SearchResult]:
        """
        Busca por similaridade vetorial.
        
        Args:
            query_embedding: Embedding da query
            top_k: Número de resultados
            project_id: Filtrar por projeto
            threshold: Threshold mínimo de similaridade
            
        Returns:
            Lista de SearchResult ordenada por similaridade
        """
        pool = await self._get_pool()
        
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Query com filtro opcional de projeto
        project_filter = ""
        params = [embedding_str, top_k]
        
        if project_id is not None:
            project_filter = "AND d.project_id = $3"
            params.append(project_id)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT 
                    c.id, c.document_id, c.content, c.chunk_index, c.metadata as chunk_metadata,
                    c.previous_chunk, c.next_chunk, c.created_at,
                    d.id as doc_id, d.title, d.source, d.content_type, d.metadata as doc_metadata,
                    1 - (c.embedding <=> $1::vector) as similarity
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL {project_filter}
                ORDER BY c.embedding <=> $1::vector
                LIMIT $2
            """, *params)
            
            results = []
            for row in rows:
                if row["similarity"] < threshold:
                    continue
                
                chunk = DocumentChunk(
                    id=row["id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    previous_chunk=row["previous_chunk"],
                    next_chunk=row["next_chunk"],
                    metadata=json.loads(row["chunk_metadata"]) if row["chunk_metadata"] else None,
                    created_at=row["created_at"],
                    score=row["similarity"]
                )
                
                doc = Document(
                    id=row["doc_id"],
                    title=row["title"],
                    source=row["source"],
                    content_type=row["content_type"],
                    metadata=json.loads(row["doc_metadata"]) if row["doc_metadata"] else None
                )
                
                results.append(SearchResult(
                    chunk=chunk,
                    document=doc,
                    score=row["similarity"],
                    search_type="vector"
                ))
            
            return results
    
    async def search_keyword(
        self,
        query: str,
        top_k: int = 10,
        project_id: Optional[int] = None
    ) -> list[SearchResult]:
        """
        Busca por keywords usando full-text search.
        
        Args:
            query: Query de busca
            top_k: Número de resultados
            project_id: Filtrar por projeto
            
        Returns:
            Lista de SearchResult ordenada por relevância
        """
        pool = await self._get_pool()
        
        # Query com filtro opcional de projeto
        project_filter = ""
        params = [query, top_k]
        
        if project_id is not None:
            project_filter = "AND d.project_id = $3"
            params.append(project_id)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT 
                    c.id, c.document_id, c.content, c.chunk_index, c.metadata as chunk_metadata,
                    c.previous_chunk, c.next_chunk, c.created_at,
                    d.id as doc_id, d.title, d.source, d.content_type, d.metadata as doc_metadata,
                    similarity(c.content, $1) as sim_score
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.content % $1 {project_filter}
                ORDER BY c.content <-> $1
                LIMIT $2
            """, *params)
            
            results = []
            for row in rows:
                chunk = DocumentChunk(
                    id=row["id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    previous_chunk=row["previous_chunk"],
                    next_chunk=row["next_chunk"],
                    metadata=json.loads(row["chunk_metadata"]) if row["chunk_metadata"] else None,
                    created_at=row["created_at"],
                    score=row["sim_score"]
                )
                
                doc = Document(
                    id=row["doc_id"],
                    title=row["title"],
                    source=row["source"],
                    content_type=row["content_type"],
                    metadata=json.loads(row["doc_metadata"]) if row["doc_metadata"] else None
                )
                
                results.append(SearchResult(
                    chunk=chunk,
                    document=doc,
                    score=row["sim_score"],
                    search_type="keyword"
                ))
            
            return results
    
    async def search_hybrid(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 10,
        project_id: Optional[int] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> list[SearchResult]:
        """
        Busca híbrida combinando vector e keyword search.
        Usa Reciprocal Rank Fusion (RRF) para combinar resultados.
        
        Args:
            query: Query textual
            query_embedding: Embedding da query
            top_k: Número de resultados finais
            project_id: Filtrar por projeto
            vector_weight: Peso da busca vetorial
            keyword_weight: Peso da busca por keywords
            
        Returns:
            Lista de SearchResult ordenada por score combinado
        """
        # Buscar mais resultados para ter margem para fusion
        fetch_k = top_k * 3
        
        # Buscar em paralelo
        vector_results, keyword_results = await asyncio.gather(
            self.search_vector(query_embedding, fetch_k, project_id),
            self.search_keyword(query, fetch_k, project_id)
        )
        
        # RRF: Reciprocal Rank Fusion
        k = self.config.retrieval.rrf_k
        chunk_scores: dict[int, float] = {}
        chunk_data: dict[int, SearchResult] = {}
        
        # Scores de busca vetorial
        for rank, result in enumerate(vector_results):
            chunk_id = result.chunk.id
            rrf_score = vector_weight * (1 / (k + rank + 1))
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + rrf_score
            chunk_data[chunk_id] = result
        
        # Scores de busca por keywords
        for rank, result in enumerate(keyword_results):
            chunk_id = result.chunk.id
            rrf_score = keyword_weight * (1 / (k + rank + 1))
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + rrf_score
            if chunk_id not in chunk_data:
                chunk_data[chunk_id] = result
        
        # Ordenar por score combinado
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for chunk_id, score in sorted_chunks:
            result = chunk_data[chunk_id]
            results.append(SearchResult(
                chunk=result.chunk,
                document=result.document,
                score=score,
                search_type="hybrid"
            ))
        
        return results
    
    async def delete_document(self, doc_id: int) -> bool:
        """Deleta um documento e seus chunks."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM documents WHERE id = $1
            """, doc_id)
            
            return "DELETE 1" in result
    
    async def get_document(self, doc_id: int) -> Optional[Document]:
        """Busca um documento por ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM documents WHERE id = $1
            """, doc_id)
            
            if not row:
                return None
            
            return Document(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                content=row["content"],
                source=row["source"],
                content_type=row["content_type"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                summary=row["summary"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
    
    async def list_documents(
        self,
        project_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[Document]:
        """Lista documentos de um projeto."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM documents 
                WHERE project_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, project_id, limit, offset)
            
            return [
                Document(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    content=row["content"],
                    source=row["source"],
                    content_type=row["content_type"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    summary=row["summary"],
                    chunk_count=row["chunk_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    async def get_stats(self, project_id: Optional[int] = None) -> dict:
        """Retorna estatísticas do vector store."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            if project_id:
                doc_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM documents WHERE project_id = $1", project_id
                )
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.project_id = $1
                """, project_id)
            else:
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
                chunk_count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
            
            return {
                "documents": doc_count,
                "chunks": chunk_count,
                "project_id": project_id
            }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._pool:
            await self._pool.close()


# Singleton
_vector_store: Optional[VectorStore] = None


def get_vector_store(config: Optional[RAGConfig] = None) -> VectorStore:
    """Retorna o vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(config)
    return _vector_store

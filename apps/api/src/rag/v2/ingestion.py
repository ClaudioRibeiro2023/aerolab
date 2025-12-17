"""
RAG v2 - Ingestion Pipeline

Pipeline de ingestão de documentos com:
- Chunking semântico
- Extração de entidades
- Geração de embeddings
- Indexação em vector e graph stores
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Callable
from enum import Enum
import logging
import re
import hashlib

from .config import RAGConfig, ChunkingConfig, get_rag_config
from .embeddings import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, Document, DocumentChunk, get_vector_store
from .graph_store import GraphStore, Entity, Relation, GraphDocument, EntityType, RelationType, get_graph_store


logger = logging.getLogger(__name__)


class DocumentStatus(str, Enum):
    """Status de processamento do documento."""
    PENDING = "pending"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ChunkResult:
    """Resultado de chunking."""
    chunks: list[str]
    chunk_count: int
    avg_chunk_size: int
    method: str


@dataclass
class EntityExtractionResult:
    """Resultado de extração de entidades."""
    entities: list[Entity]
    relations: list[Relation]
    extraction_time_ms: float


@dataclass
class IngestionResult:
    """Resultado de ingestão de documento."""
    document_id: int
    chunk_count: int
    entity_count: int
    relation_count: int
    total_time_ms: float
    status: DocumentStatus
    error: Optional[str] = None


class SemanticChunker:
    """
    Chunker semântico para documentos.
    
    Features:
    - Chunking por separadores semânticos
    - Overlap para contexto
    - Respeita limites de tamanho
    - Preserva contexto de vizinhos
    """
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
    
    def chunk(self, text: str) -> ChunkResult:
        """
        Divide texto em chunks semânticos.
        
        Args:
            text: Texto para dividir
            
        Returns:
            ChunkResult com chunks e metadados
        """
        if not text.strip():
            return ChunkResult(chunks=[], chunk_count=0, avg_chunk_size=0, method="empty")
        
        # Tentar cada separador em ordem de prioridade
        chunks = self._split_by_separators(text, self.config.separators)
        
        # Mesclar chunks pequenos
        merged = self._merge_small_chunks(chunks)
        
        # Dividir chunks grandes
        final = self._split_large_chunks(merged)
        
        # Adicionar overlap
        if self.config.chunk_overlap > 0:
            final = self._add_overlap(final)
        
        avg_size = sum(len(c) for c in final) // max(len(final), 1)
        
        return ChunkResult(
            chunks=final,
            chunk_count=len(final),
            avg_chunk_size=avg_size,
            method="semantic" if self.config.use_semantic_chunking else "fixed"
        )
    
    def _split_by_separators(self, text: str, separators: list[str]) -> list[str]:
        """Divide texto usando separadores em ordem de prioridade."""
        if not separators:
            return [text]
        
        current_sep = separators[0]
        remaining_seps = separators[1:]
        
        parts = text.split(current_sep)
        
        # Se conseguiu dividir em partes menores que o limite, usa essa divisão
        if all(len(p) <= self.config.max_chunk_size for p in parts):
            # Recursivamente dividir partes grandes
            result = []
            for part in parts:
                if len(part) > self.config.chunk_size and remaining_seps:
                    result.extend(self._split_by_separators(part, remaining_seps))
                elif part.strip():
                    result.append(part.strip())
            return result
        
        # Senão, tenta o próximo separador
        if remaining_seps:
            return self._split_by_separators(text, remaining_seps)
        
        # Fallback: divisão por caracteres
        return self._split_by_chars(text)
    
    def _split_by_chars(self, text: str) -> list[str]:
        """Divide texto por número de caracteres."""
        chunks = []
        for i in range(0, len(text), self.config.chunk_size):
            chunk = text[i:i + self.config.chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks
    
    def _merge_small_chunks(self, chunks: list[str]) -> list[str]:
        """Mescla chunks pequenos."""
        if not chunks:
            return []
        
        merged = []
        current = chunks[0]
        
        for chunk in chunks[1:]:
            if len(current) + len(chunk) < self.config.min_chunk_size * 2:
                current = current + " " + chunk
            else:
                if len(current) >= self.config.min_chunk_size:
                    merged.append(current)
                current = chunk
        
        if current and len(current) >= self.config.min_chunk_size:
            merged.append(current)
        elif current and merged:
            merged[-1] = merged[-1] + " " + current
        elif current:
            merged.append(current)
        
        return merged
    
    def _split_large_chunks(self, chunks: list[str]) -> list[str]:
        """Divide chunks que excedem o tamanho máximo."""
        result = []
        for chunk in chunks:
            if len(chunk) > self.config.max_chunk_size:
                result.extend(self._split_by_chars(chunk))
            else:
                result.append(chunk)
        return result
    
    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Adiciona overlap entre chunks."""
        if len(chunks) <= 1:
            return chunks
        
        overlap_size = self.config.chunk_overlap
        result = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            # Pegar final do chunk anterior como contexto
            overlap = prev_chunk[-overlap_size:] if len(prev_chunk) > overlap_size else prev_chunk
            
            # Adicionar overlap no início do chunk atual
            result.append(f"...{overlap}...\n\n{current_chunk}")
        
        return result


class EntityExtractor:
    """
    Extrator de entidades usando LLM.
    
    Extrai:
    - Pessoas, organizações, locais
    - Tecnologias, conceitos, produtos
    - Relações entre entidades
    """
    
    EXTRACTION_PROMPT = """Extract entities and relationships from the following text.

Text:
{text}

Return a JSON object with:
1. "entities": array of objects with "name", "type" (Person, Organization, Location, Technology, Concept, Product), and "description"
2. "relations": array of objects with "source", "target", "type" (MENTIONS, RELATED_TO, PART_OF, USES, DEPENDS_ON)

JSON:"""

    def __init__(self, config: RAGConfig):
        self.config = config
        self._client = None
    
    async def _get_client(self):
        """Retorna cliente OpenAI."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.config.embedding.openai_api_key)
        return self._client
    
    async def extract(self, text: str) -> EntityExtractionResult:
        """
        Extrai entidades e relações do texto.
        
        Args:
            text: Texto para extrair
            
        Returns:
            EntityExtractionResult com entidades e relações
        """
        start = datetime.now()
        
        # Limitar texto para evitar excesso de tokens
        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        try:
            client = await self._get_client()
            
            response = await client.chat.completions.create(
                model=self.config.query.hyde_model,
                messages=[
                    {"role": "user", "content": self.EXTRACTION_PROMPT.format(text=text)}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Parse entidades
            entities = []
            for e in result.get("entities", []):
                try:
                    entity_type = EntityType(e.get("type", "Concept"))
                except ValueError:
                    entity_type = EntityType.CONCEPT
                
                entities.append(Entity(
                    name=e.get("name", ""),
                    entity_type=entity_type,
                    description=e.get("description")
                ))
            
            # Parse relações
            relations = []
            for r in result.get("relations", []):
                try:
                    rel_type = RelationType(r.get("type", "RELATED_TO"))
                except ValueError:
                    rel_type = RelationType.RELATED_TO
                
                relations.append(Relation(
                    source_id=r.get("source", ""),
                    target_id=r.get("target", ""),
                    relation_type=rel_type
                ))
            
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            return EntityExtractionResult(
                entities=entities,
                relations=relations,
                extraction_time_ms=elapsed
            )
            
        except Exception as e:
            logger.error(f"Erro na extração de entidades: {e}")
            return EntityExtractionResult(
                entities=[],
                relations=[],
                extraction_time_ms=0
            )
    
    def extract_simple(self, text: str) -> EntityExtractionResult:
        """
        Extração simples baseada em padrões (sem LLM).
        
        Mais rápido mas menos preciso.
        """
        start = datetime.now()
        entities = []
        
        # Extrair URLs
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls:
            entities.append(Entity(
                name=url,
                entity_type=EntityType.TECHNOLOGY,
                description="URL encontrada no texto"
            ))
        
        # Extrair emails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        for email in emails:
            entities.append(Entity(
                name=email,
                entity_type=EntityType.PERSON,
                description="Email encontrado no texto"
            ))
        
        # Extrair palavras capitalizadas (possíveis nomes/organizações)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        for name in set(capitalized[:10]):  # Limitar a 10
            entities.append(Entity(
                name=name,
                entity_type=EntityType.CONCEPT,
                description="Nome próprio encontrado"
            ))
        
        elapsed = (datetime.now() - start).total_seconds() * 1000
        
        return EntityExtractionResult(
            entities=entities,
            relations=[],
            extraction_time_ms=elapsed
        )


class IngestionPipeline:
    """
    Pipeline de ingestão de documentos.
    
    Fluxo:
    1. Chunking: divide documento em chunks semânticos
    2. Embedding: gera embeddings para cada chunk
    3. Vector Indexing: indexa no PostgreSQL/pgvector
    4. Entity Extraction: extrai entidades (opcional)
    5. Graph Indexing: indexa no Neo4j (opcional)
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        
        # Componentes
        self.chunker = SemanticChunker(self.config.chunking)
        self.extractor = EntityExtractor(self.config)
        
        self._embedding_service: Optional[EmbeddingService] = None
        self._vector_store: Optional[VectorStore] = None
        self._graph_store: Optional[GraphStore] = None
        
        # Callbacks
        self._progress_callback: Optional[Callable] = None
        
        # Métricas
        self.total_documents = 0
        self.total_chunks = 0
        self.total_entities = 0
        self.failed_documents = 0
    
    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """Define callback de progresso."""
        self._progress_callback = callback
    
    def _report_progress(self, status: str, progress: float) -> None:
        """Reporta progresso."""
        if self._progress_callback:
            self._progress_callback(status, progress)
    
    async def _get_embedding_service(self) -> EmbeddingService:
        """Retorna serviço de embeddings."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service(self.config)
        return self._embedding_service
    
    async def _get_vector_store(self) -> VectorStore:
        """Retorna vector store."""
        if self._vector_store is None:
            self._vector_store = get_vector_store(self.config)
        return self._vector_store
    
    async def _get_graph_store(self) -> GraphStore:
        """Retorna graph store."""
        if self._graph_store is None:
            self._graph_store = get_graph_store(self.config)
        return self._graph_store
    
    async def ingest_document(
        self,
        title: str,
        content: str,
        project_id: int,
        source: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        extract_entities: bool = True,
        use_llm_extraction: bool = False
    ) -> IngestionResult:
        """
        Ingere um documento completo.
        
        Args:
            title: Título do documento
            content: Conteúdo do documento
            project_id: ID do projeto
            source: Fonte do documento (URL, arquivo, etc)
            content_type: Tipo de conteúdo (text, markdown, html, etc)
            metadata: Metadados adicionais
            extract_entities: Se deve extrair entidades
            use_llm_extraction: Se deve usar LLM para extração (mais preciso, mais lento)
            
        Returns:
            IngestionResult com status e métricas
        """
        start = datetime.now()
        
        try:
            self._report_progress("chunking", 0.1)
            
            # 1. Chunking
            chunk_result = self.chunker.chunk(content)
            
            if not chunk_result.chunks:
                return IngestionResult(
                    document_id=0,
                    chunk_count=0,
                    entity_count=0,
                    relation_count=0,
                    total_time_ms=0,
                    status=DocumentStatus.FAILED,
                    error="Documento vazio ou inválido"
                )
            
            self._report_progress("embedding", 0.2)
            
            # 2. Gerar embeddings
            embedding_service = await self._get_embedding_service()
            embeddings = await embedding_service.embed_texts(chunk_result.chunks)
            
            self._report_progress("indexing", 0.5)
            
            # 3. Salvar documento
            vector_store = await self._get_vector_store()
            
            doc = Document(
                project_id=project_id,
                title=title,
                content=content,
                source=source,
                content_type=content_type,
                metadata=metadata
            )
            
            doc_id = await vector_store.add_document(doc)
            
            # 4. Salvar chunks
            chunks_to_add = []
            for i, (chunk_text, emb_result) in enumerate(zip(chunk_result.chunks, embeddings)):
                prev_chunk = chunk_result.chunks[i - 1][:200] if i > 0 else None
                next_chunk = chunk_result.chunks[i + 1][:200] if i < len(chunk_result.chunks) - 1 else None
                
                chunk = DocumentChunk(
                    document_id=doc_id,
                    content=chunk_text,
                    chunk_index=i,
                    embedding=emb_result.embedding,
                    previous_chunk=prev_chunk,
                    next_chunk=next_chunk,
                    metadata={"char_count": len(chunk_text)}
                )
                chunks_to_add.append(chunk)
            
            await vector_store.add_chunks_batch(chunks_to_add)
            
            # 5. Extração de entidades (opcional)
            entity_count = 0
            relation_count = 0
            
            if extract_entities:
                self._report_progress("extracting", 0.7)
                
                if use_llm_extraction:
                    # Extrair de uma amostra dos chunks
                    sample_text = "\n\n".join(chunk_result.chunks[:5])
                    extraction_result = await self.extractor.extract(sample_text)
                else:
                    extraction_result = self.extractor.extract_simple(content)
                
                entity_count = len(extraction_result.entities)
                relation_count = len(extraction_result.relations)
                
                # 6. Indexar no grafo
                if extraction_result.entities:
                    self._report_progress("graph_indexing", 0.85)
                    
                    graph_store = await self._get_graph_store()
                    
                    graph_doc = GraphDocument(
                        id=f"doc_{doc_id}",
                        document_id=doc_id,
                        title=title,
                        source=source,
                        entities=extraction_result.entities,
                        relations=extraction_result.relations
                    )
                    
                    await graph_store.add_document(graph_doc)
            
            self._report_progress("completed", 1.0)
            
            # Atualizar métricas
            self.total_documents += 1
            self.total_chunks += chunk_result.chunk_count
            self.total_entities += entity_count
            
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            return IngestionResult(
                document_id=doc_id,
                chunk_count=chunk_result.chunk_count,
                entity_count=entity_count,
                relation_count=relation_count,
                total_time_ms=elapsed,
                status=DocumentStatus.COMPLETED
            )
            
        except Exception as e:
            self.failed_documents += 1
            logger.error(f"Erro na ingestão: {e}")
            
            return IngestionResult(
                document_id=0,
                chunk_count=0,
                entity_count=0,
                relation_count=0,
                total_time_ms=(datetime.now() - start).total_seconds() * 1000,
                status=DocumentStatus.FAILED,
                error=str(e)
            )
    
    async def ingest_batch(
        self,
        documents: list[dict],
        project_id: int,
        extract_entities: bool = True,
        max_concurrent: int = 5
    ) -> list[IngestionResult]:
        """
        Ingere múltiplos documentos em batch.
        
        Args:
            documents: Lista de dicts com title, content, source, metadata
            project_id: ID do projeto
            extract_entities: Se deve extrair entidades
            max_concurrent: Máximo de documentos simultâneos
            
        Returns:
            Lista de IngestionResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def ingest_with_semaphore(doc: dict) -> IngestionResult:
            async with semaphore:
                return await self.ingest_document(
                    title=doc.get("title", "Untitled"),
                    content=doc.get("content", ""),
                    project_id=project_id,
                    source=doc.get("source"),
                    content_type=doc.get("content_type"),
                    metadata=doc.get("metadata"),
                    extract_entities=extract_entities
                )
        
        tasks = [ingest_with_semaphore(doc) for doc in documents]
        return await asyncio.gather(*tasks)
    
    def get_metrics(self) -> dict:
        """Retorna métricas do pipeline."""
        return {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "total_entities": self.total_entities,
            "failed_documents": self.failed_documents,
            "success_rate": (self.total_documents - self.failed_documents) / max(self.total_documents, 1)
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        tasks = []
        
        if self._embedding_service:
            tasks.append(self._embedding_service.close())
        if self._vector_store:
            tasks.append(self._vector_store.close())
        if self._graph_store:
            tasks.append(self._graph_store.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Singleton
_ingestion_pipeline: Optional[IngestionPipeline] = None


def get_ingestion_pipeline(config: Optional[RAGConfig] = None) -> IngestionPipeline:
    """Retorna o pipeline de ingestão singleton."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline(config)
    return _ingestion_pipeline

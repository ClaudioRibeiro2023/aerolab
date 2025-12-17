"""
RAG v2 - Pipeline Principal

Pipeline completo de RAG integrando:
- Query Processing (expansion, HyDE, decomposition)
- Hybrid Search (vector + graph + keyword)
- Reranking (Cohere)
- Context Assembly
- Response Generation
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, AsyncGenerator
import logging
import json

from openai import AsyncOpenAI

from .config import RAGConfig, RetrievalMethod, get_rag_config
from .embeddings import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, SearchResult, get_vector_store
from .graph_store import GraphStore, get_graph_store
from .reranker import Reranker, RerankResult, get_reranker
from .query_processor import QueryProcessor, ProcessedQuery, get_query_processor


logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Contexto recuperado para geração."""
    chunks: list[SearchResult]
    reranked: list[RerankResult]
    sources: list[dict]
    total_tokens: int
    retrieval_time_ms: float
    
    def to_string(self, max_tokens: int = 8000) -> str:
        """Converte contexto para string formatada."""
        context_parts = []
        current_tokens = 0
        
        for result in self.reranked:
            chunk = result.original_result.chunk
            doc = result.original_result.document
            
            # Estimar tokens (aproximado: 4 chars = 1 token)
            chunk_tokens = len(chunk.content) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            context_part = f"""
[Source: {doc.title}]
{chunk.content}
---"""
            context_parts.append(context_part)
            current_tokens += chunk_tokens
        
        return "\n".join(context_parts)


@dataclass
class RAGResponse:
    """Resposta completa do RAG."""
    query: str
    answer: str
    context: RAGContext
    processed_query: ProcessedQuery
    sources: list[dict]
    confidence: float
    generation_time_ms: float
    total_time_ms: float
    model: str
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "query": self.query,
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "metrics": {
                "retrieval_time_ms": self.context.retrieval_time_ms,
                "generation_time_ms": self.generation_time_ms,
                "total_time_ms": self.total_time_ms,
                "chunks_retrieved": len(self.context.chunks),
                "chunks_used": len(self.context.reranked)
            },
            "model": self.model
        }


class RAGPipeline:
    """
    Pipeline completo de Retrieval-Augmented Generation.
    
    Fluxo:
    1. Query Processing: expansion, HyDE, decomposition
    2. Retrieval: hybrid search (vector + graph + keyword)
    3. Reranking: Cohere rerank
    4. Context Assembly: monta contexto respeitando limite de tokens
    5. Generation: gera resposta com LLM
    
    Features:
    - Streaming de respostas
    - Múltiplos métodos de retrieval
    - Fallback automático
    - Métricas detalhadas
    """
    
    SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
1. Answer ONLY based on the context provided below
2. If the context doesn't contain enough information, say so clearly
3. Cite sources when relevant using [Source: title]
4. Be concise but thorough
5. If asked for a list, format it clearly
6. Use the same language as the user's question

Context:
{context}"""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        
        # Componentes
        self._embedding_service: Optional[EmbeddingService] = None
        self._vector_store: Optional[VectorStore] = None
        self._graph_store: Optional[GraphStore] = None
        self._reranker: Optional[Reranker] = None
        self._query_processor: Optional[QueryProcessor] = None
        self._llm_client: Optional[AsyncOpenAI] = None
        
        # Métricas
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_retrieval_time = 0
        self.total_generation_time = 0
    
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
    
    async def _get_reranker(self) -> Reranker:
        """Retorna reranker."""
        if self._reranker is None:
            self._reranker = get_reranker(self.config)
        return self._reranker
    
    async def _get_query_processor(self) -> QueryProcessor:
        """Retorna processador de queries."""
        if self._query_processor is None:
            self._query_processor = get_query_processor(self.config)
        return self._query_processor
    
    async def _get_llm_client(self) -> AsyncOpenAI:
        """Retorna cliente LLM."""
        if self._llm_client is None:
            self._llm_client = AsyncOpenAI(api_key=self.config.embedding.openai_api_key)
        return self._llm_client
    
    async def initialize(self) -> None:
        """Inicializa todos os componentes."""
        vector_store = await self._get_vector_store()
        graph_store = await self._get_graph_store()
        
        await asyncio.gather(
            vector_store.initialize(),
            graph_store.initialize()
        )
        
        logger.info("RAG Pipeline inicializado")
    
    async def retrieve(
        self,
        query: str,
        project_id: Optional[int] = None,
        method: Optional[RetrievalMethod] = None
    ) -> RAGContext:
        """
        Recupera contexto relevante para a query.
        
        Args:
            query: Query de busca
            project_id: ID do projeto para filtrar
            method: Método de retrieval (default: hybrid)
            
        Returns:
            RAGContext com chunks e metadados
        """
        start_time = datetime.now()
        method = method or self.config.retrieval.method
        
        # Gerar embedding da query
        embedding_service = await self._get_embedding_service()
        query_embedding_result = await embedding_service.embed_text(query)
        query_embedding = query_embedding_result.embedding
        
        # Buscar por método
        vector_store = await self._get_vector_store()
        
        if method == RetrievalMethod.VECTOR:
            results = await vector_store.search_vector(
                query_embedding,
                top_k=self.config.retrieval.top_k,
                project_id=project_id,
                threshold=self.config.retrieval.similarity_threshold
            )
        elif method == RetrievalMethod.KEYWORD:
            results = await vector_store.search_keyword(
                query,
                top_k=self.config.retrieval.top_k,
                project_id=project_id
            )
        elif method == RetrievalMethod.GRAPH:
            # Buscar por grafo e depois buscar chunks relacionados
            graph_store = await self._get_graph_store()
            entities, _ = await graph_store.get_subgraph(query, max_entities=10)
            
            # Buscar documentos que mencionam as entidades
            entity_ids = [e.id for e in entities if e.id]
            doc_mapping = await graph_store.get_documents_for_entities(entity_ids)
            
            # Buscar chunks desses documentos
            all_doc_ids = set()
            for doc_ids in doc_mapping.values():
                all_doc_ids.update(doc_ids)
            
            # Fallback para vector search se não houver resultados do grafo
            if not all_doc_ids:
                results = await vector_store.search_vector(
                    query_embedding,
                    top_k=self.config.retrieval.top_k,
                    project_id=project_id
                )
            else:
                results = await vector_store.search_vector(
                    query_embedding,
                    top_k=self.config.retrieval.top_k,
                    project_id=project_id
                )
                # Filtrar para apenas documentos do grafo
                results = [r for r in results if r.document.id in all_doc_ids]
        else:  # HYBRID
            results = await vector_store.search_hybrid(
                query,
                query_embedding,
                top_k=self.config.retrieval.top_k,
                project_id=project_id,
                vector_weight=self.config.retrieval.vector_weight,
                keyword_weight=self.config.retrieval.keyword_weight
            )
        
        # Reranking
        reranker = await self._get_reranker()
        reranked = await reranker.rerank(
            query,
            results,
            top_n=self.config.retrieval.top_n
        )
        
        # Montar sources
        sources = []
        seen_docs = set()
        for result in reranked:
            doc = result.original_result.document
            if doc.id not in seen_docs:
                seen_docs.add(doc.id)
                sources.append({
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "score": result.rerank_score
                })
        
        # Calcular tempo
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return RAGContext(
            chunks=results,
            reranked=reranked,
            sources=sources,
            total_tokens=sum(len(r.original_result.chunk.content) // 4 for r in reranked),
            retrieval_time_ms=elapsed
        )
    
    async def retrieve_with_processing(
        self,
        query: str,
        project_id: Optional[int] = None
    ) -> tuple[RAGContext, ProcessedQuery]:
        """
        Recupera com processamento avançado de query.
        
        Aplica query expansion, HyDE, decomposition para melhorar recall.
        """
        query_processor = await self._get_query_processor()
        processed = await query_processor.process(query)
        
        # Buscar com todas as variações da query
        all_results: list[SearchResult] = []
        
        # Query original
        main_context = await self.retrieve(query, project_id)
        all_results.extend([r.original_result for r in main_context.reranked])
        
        # HyDE se disponível
        if processed.hyde_document:
            embedding_service = await self._get_embedding_service()
            hyde_embedding = await embedding_service.embed_text(processed.hyde_document)
            vector_store = await self._get_vector_store()
            
            hyde_results = await vector_store.search_vector(
                hyde_embedding.embedding,
                top_k=self.config.retrieval.top_k // 2,
                project_id=project_id
            )
            all_results.extend(hyde_results)
        
        # Sub-queries
        for sub_query in processed.sub_queries[:2]:  # Limitar a 2
            sub_context = await self.retrieve(sub_query, project_id)
            all_results.extend([r.original_result for r in sub_context.reranked])
        
        # Deduplicate por chunk ID
        seen = set()
        unique_results = []
        for r in all_results:
            if r.chunk.id not in seen:
                seen.add(r.chunk.id)
                unique_results.append(r)
        
        # Rerank final
        reranker = await self._get_reranker()
        final_reranked = await reranker.rerank(
            query,
            unique_results,
            top_n=self.config.retrieval.top_n
        )
        
        # Atualizar contexto
        main_context.reranked = final_reranked
        main_context.chunks = unique_results
        
        return main_context, processed
    
    async def generate(
        self,
        query: str,
        context: RAGContext,
        stream: bool = False
    ) -> str:
        """
        Gera resposta baseada no contexto.
        
        Args:
            query: Query original
            context: Contexto recuperado
            stream: Se deve fazer streaming
            
        Returns:
            Resposta gerada
        """
        client = await self._get_llm_client()
        
        # Montar contexto
        context_str = context.to_string(max_tokens=self.config.max_context_tokens)
        system_prompt = self.SYSTEM_PROMPT.format(context=context_str)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = await client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
            stream=stream
        )
        
        if stream:
            return response  # Retorna stream para ser consumido
        
        return response.choices[0].message.content
    
    async def generate_stream(
        self,
        query: str,
        context: RAGContext
    ) -> AsyncGenerator[str, None]:
        """
        Gera resposta em streaming.
        
        Args:
            query: Query original
            context: Contexto recuperado
            
        Yields:
            Chunks de texto da resposta
        """
        client = await self._get_llm_client()
        
        context_str = context.to_string(max_tokens=self.config.max_context_tokens)
        system_prompt = self.SYSTEM_PROMPT.format(context=context_str)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        stream = await client.chat.completions.create(
            model=self.config.llm_model,
            messages=messages,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def query(
        self,
        query: str,
        project_id: Optional[int] = None,
        use_advanced_processing: bool = True
    ) -> RAGResponse:
        """
        Executa pipeline completo: retrieve + generate.
        
        Args:
            query: Query do usuário
            project_id: ID do projeto para filtrar
            use_advanced_processing: Se deve usar query processing avançado
            
        Returns:
            RAGResponse com resposta completa
        """
        total_start = datetime.now()
        self.total_queries += 1
        
        try:
            # Retrieval
            if use_advanced_processing:
                context, processed_query = await self.retrieve_with_processing(query, project_id)
            else:
                context = await self.retrieve(query, project_id)
                query_processor = await self._get_query_processor()
                processed_query = ProcessedQuery(original_query=query)
            
            self.total_retrieval_time += context.retrieval_time_ms
            
            # Generation
            gen_start = datetime.now()
            answer = await self.generate(query, context)
            gen_time = (datetime.now() - gen_start).total_seconds() * 1000
            self.total_generation_time += gen_time
            
            # Calcular confiança baseada nos scores de reranking
            if context.reranked:
                confidence = sum(r.rerank_score for r in context.reranked) / len(context.reranked)
            else:
                confidence = 0.0
            
            total_time = (datetime.now() - total_start).total_seconds() * 1000
            
            self.successful_queries += 1
            
            return RAGResponse(
                query=query,
                answer=answer,
                context=context,
                processed_query=processed_query,
                sources=context.sources,
                confidence=confidence,
                generation_time_ms=gen_time,
                total_time_ms=total_time,
                model=self.config.llm_model
            )
            
        except Exception as e:
            self.failed_queries += 1
            logger.error(f"Erro no pipeline RAG: {e}")
            raise
    
    async def query_stream(
        self,
        query: str,
        project_id: Optional[int] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Executa pipeline com streaming da resposta.
        
        Yields:
            Dicionários com chunks de resposta e metadados
        """
        total_start = datetime.now()
        
        # Retrieval
        context, processed_query = await self.retrieve_with_processing(query, project_id)
        
        # Yield contexto primeiro
        yield {
            "type": "context",
            "sources": context.sources,
            "retrieval_time_ms": context.retrieval_time_ms
        }
        
        # Stream da resposta
        full_answer = ""
        async for chunk in self.generate_stream(query, context):
            full_answer += chunk
            yield {
                "type": "chunk",
                "content": chunk
            }
        
        # Yield final
        total_time = (datetime.now() - total_start).total_seconds() * 1000
        yield {
            "type": "done",
            "total_time_ms": total_time,
            "answer_length": len(full_answer)
        }
    
    def get_metrics(self) -> dict:
        """Retorna métricas do pipeline."""
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": self.successful_queries / max(self.total_queries, 1),
            "avg_retrieval_time_ms": self.total_retrieval_time / max(self.successful_queries, 1),
            "avg_generation_time_ms": self.total_generation_time / max(self.successful_queries, 1)
        }
    
    async def close(self) -> None:
        """Fecha todos os componentes."""
        tasks = []
        
        if self._embedding_service:
            tasks.append(self._embedding_service.close())
        if self._vector_store:
            tasks.append(self._vector_store.close())
        if self._graph_store:
            tasks.append(self._graph_store.close())
        if self._reranker:
            tasks.append(self._reranker.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Singleton
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline(config: Optional[RAGConfig] = None) -> RAGPipeline:
    """Retorna o pipeline RAG singleton."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(config)
    return _rag_pipeline

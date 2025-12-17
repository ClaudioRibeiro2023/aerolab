"""
RAG v2 - Reranker com Cohere

Serviço de reranking para melhorar relevância dos resultados.
Suporta:
- Cohere Rerank API
- BGE Reranker local como fallback
- Batch processing
"""

import asyncio
from dataclasses import dataclass
from typing import Optional, Any
import logging

import cohere
from cohere import AsyncClient as CohereAsyncClient

from .config import RAGConfig, RerankConfig, RerankModel, get_rag_config
from .vector_store import SearchResult


logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Resultado de reranking."""
    original_result: SearchResult
    rerank_score: float
    original_rank: int
    new_rank: int


class Reranker:
    """
    Serviço de reranking com Cohere.
    
    Features:
    - Reranking com Cohere API
    - Fallback para modelo local (BGE)
    - Batch processing para eficiência
    - Métricas de uso
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        self.rerank_config = self.config.rerank
        
        # Cliente Cohere
        self._cohere_client: Optional[CohereAsyncClient] = None
        
        # Modelo local (lazy load)
        self._local_model = None
        self._local_tokenizer = None
        
        # Métricas
        self.total_requests = 0
        self.cohere_requests = 0
        self.fallback_requests = 0
    
    async def _get_cohere_client(self) -> CohereAsyncClient:
        """Retorna cliente Cohere."""
        if self._cohere_client is None:
            self._cohere_client = CohereAsyncClient(
                api_key=self.rerank_config.cohere_api_key
            )
        return self._cohere_client
    
    def _load_local_model(self):
        """Carrega modelo local BGE Reranker."""
        if self._local_model is not None:
            return
        
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch
            
            model_name = self.rerank_config.fallback_model
            self._local_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._local_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Mover para GPU se disponível
            if torch.cuda.is_available():
                self._local_model = self._local_model.cuda()
            
            self._local_model.eval()
            logger.info(f"Modelo local {model_name} carregado")
            
        except ImportError:
            logger.warning("transformers/torch não instalados, fallback desabilitado")
            raise
    
    async def rerank_with_cohere(
        self,
        query: str,
        results: list[SearchResult],
        top_n: Optional[int] = None
    ) -> list[RerankResult]:
        """
        Rerank usando Cohere API.
        
        Args:
            query: Query original
            results: Resultados a reranquear
            top_n: Número de resultados a retornar
            
        Returns:
            Lista de RerankResult ordenada por relevância
        """
        if not results:
            return []
        
        top_n = top_n or self.rerank_config.top_n
        self.total_requests += 1
        self.cohere_requests += 1
        
        try:
            client = await self._get_cohere_client()
            
            # Preparar documentos para reranking
            documents = [r.chunk.content for r in results]
            
            # Chamar API
            response = await client.rerank(
                model=self.rerank_config.model.value,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=False
            )
            
            # Processar resultados
            reranked = []
            for i, result in enumerate(response.results):
                original_idx = result.index
                reranked.append(RerankResult(
                    original_result=results[original_idx],
                    rerank_score=result.relevance_score,
                    original_rank=original_idx,
                    new_rank=i
                ))
            
            return reranked
            
        except Exception as e:
            logger.error(f"Erro no Cohere rerank: {e}")
            
            if self.rerank_config.use_fallback:
                logger.info("Usando fallback local")
                return await self.rerank_local(query, results, top_n)
            
            raise
    
    async def rerank_local(
        self,
        query: str,
        results: list[SearchResult],
        top_n: Optional[int] = None
    ) -> list[RerankResult]:
        """
        Rerank usando modelo local (BGE Reranker).
        
        Args:
            query: Query original
            results: Resultados a reranquear
            top_n: Número de resultados a retornar
            
        Returns:
            Lista de RerankResult ordenada por relevância
        """
        if not results:
            return []
        
        top_n = top_n or self.rerank_config.top_n
        self.total_requests += 1
        self.fallback_requests += 1
        
        try:
            self._load_local_model()
        except Exception as e:
            logger.error(f"Falha ao carregar modelo local: {e}")
            # Retornar resultados originais ordenados por score
            return [
                RerankResult(
                    original_result=r,
                    rerank_score=r.score,
                    original_rank=i,
                    new_rank=i
                )
                for i, r in enumerate(sorted(results, key=lambda x: x.score, reverse=True)[:top_n])
            ]
        
        import torch
        
        # Preparar pares query-documento
        pairs = [(query, r.chunk.content) for r in results]
        
        # Tokenizar
        inputs = self._local_tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Mover para GPU se disponível
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Inferência
        with torch.no_grad():
            outputs = self._local_model(**inputs)
            scores = outputs.logits.squeeze(-1).cpu().numpy()
        
        # Ordenar por score
        scored_results = list(zip(range(len(results)), results, scores))
        scored_results.sort(key=lambda x: x[2], reverse=True)
        
        # Retornar top_n
        reranked = []
        for new_rank, (original_rank, result, score) in enumerate(scored_results[:top_n]):
            reranked.append(RerankResult(
                original_result=result,
                rerank_score=float(score),
                original_rank=original_rank,
                new_rank=new_rank
            ))
        
        return reranked
    
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_n: Optional[int] = None
    ) -> list[RerankResult]:
        """
        Rerank resultados (usa Cohere por padrão, fallback para local).
        
        Args:
            query: Query original
            results: Resultados a reranquear
            top_n: Número de resultados a retornar
            
        Returns:
            Lista de RerankResult ordenada por relevância
        """
        if not self.rerank_config.enabled:
            # Retornar resultados originais sem reranking
            top_n = top_n or self.rerank_config.top_n
            return [
                RerankResult(
                    original_result=r,
                    rerank_score=r.score,
                    original_rank=i,
                    new_rank=i
                )
                for i, r in enumerate(results[:top_n])
            ]
        
        if self.rerank_config.cohere_api_key:
            return await self.rerank_with_cohere(query, results, top_n)
        else:
            return await self.rerank_local(query, results, top_n)
    
    async def rerank_batch(
        self,
        queries: list[str],
        results_list: list[list[SearchResult]],
        top_n: Optional[int] = None
    ) -> list[list[RerankResult]]:
        """
        Rerank múltiplas queries em batch.
        
        Args:
            queries: Lista de queries
            results_list: Lista de resultados para cada query
            top_n: Número de resultados a retornar
            
        Returns:
            Lista de listas de RerankResult
        """
        tasks = [
            self.rerank(query, results, top_n)
            for query, results in zip(queries, results_list)
        ]
        
        return await asyncio.gather(*tasks)
    
    def get_metrics(self) -> dict:
        """Retorna métricas do serviço."""
        return {
            "total_requests": self.total_requests,
            "cohere_requests": self.cohere_requests,
            "fallback_requests": self.fallback_requests,
            "cohere_rate": self.cohere_requests / max(self.total_requests, 1),
            "fallback_rate": self.fallback_requests / max(self.total_requests, 1)
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._cohere_client:
            # Cohere client não precisa de close explícito
            pass


# Singleton
_reranker: Optional[Reranker] = None


def get_reranker(config: Optional[RAGConfig] = None) -> Reranker:
    """Retorna o reranker singleton."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker(config)
    return _reranker

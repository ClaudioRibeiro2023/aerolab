"""
RAG v2 - Embedding Service

Serviço de geração de embeddings com suporte a:
- OpenAI text-embedding-3-large/small
- Batch processing
- Caching em Redis
- Retry automático
"""

import asyncio
import hashlib
import json
from typing import Optional
from dataclasses import dataclass
import logging

import openai
from openai import AsyncOpenAI
import redis.asyncio as redis
import numpy as np

from .config import RAGConfig, EmbeddingConfig, get_rag_config


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Resultado de embedding."""
    text: str
    embedding: list[float]
    model: str
    dimensions: int
    tokens_used: int
    cached: bool = False


class EmbeddingService:
    """
    Serviço de geração de embeddings.
    
    Features:
    - Geração de embeddings com OpenAI
    - Batch processing para eficiência
    - Cache em Redis para economia
    - Retry automático com backoff
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        self.embedding_config = self.config.embedding
        
        # Cliente OpenAI
        self.client = AsyncOpenAI(api_key=self.embedding_config.openai_api_key)
        
        # Redis para cache
        self._redis: Optional[redis.Redis] = None
        
        # Métricas
        self.total_requests = 0
        self.cache_hits = 0
        self.total_tokens = 0
    
    async def _get_redis(self) -> redis.Redis:
        """Retorna conexão Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.config.database.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
        return self._redis
    
    def _cache_key(self, text: str) -> str:
        """Gera chave de cache para o texto."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"emb:{self.embedding_config.model.value}:{text_hash}"
    
    async def _get_cached(self, text: str) -> Optional[list[float]]:
        """Busca embedding no cache."""
        if not self.config.cache.cache_embeddings:
            return None
        
        try:
            r = await self._get_redis()
            cached = await r.get(self._cache_key(text))
            if cached:
                self.cache_hits += 1
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Erro ao buscar cache: {e}")
        
        return None
    
    async def _set_cache(self, text: str, embedding: list[float]) -> None:
        """Salva embedding no cache."""
        if not self.config.cache.cache_embeddings:
            return
        
        try:
            r = await self._get_redis()
            await r.setex(
                self._cache_key(text),
                self.config.cache.embedding_ttl,
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            EmbeddingResult com o embedding e metadados
        """
        self.total_requests += 1
        
        # Verificar cache
        cached = await self._get_cached(text)
        if cached:
            return EmbeddingResult(
                text=text,
                embedding=cached,
                model=self.embedding_config.model.value,
                dimensions=len(cached),
                tokens_used=0,
                cached=True
            )
        
        # Gerar embedding
        for attempt in range(self.embedding_config.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_config.model.value,
                    input=text,
                    dimensions=self.embedding_config.dimensions
                )
                
                embedding = response.data[0].embedding
                tokens = response.usage.total_tokens
                self.total_tokens += tokens
                
                # Salvar no cache
                await self._set_cache(text, embedding)
                
                return EmbeddingResult(
                    text=text,
                    embedding=embedding,
                    model=self.embedding_config.model.value,
                    dimensions=len(embedding),
                    tokens_used=tokens,
                    cached=False
                )
                
            except openai.RateLimitError:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit, aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Erro ao gerar embedding: {e}")
                if attempt == self.embedding_config.max_retries - 1:
                    raise
        
        raise RuntimeError("Falha ao gerar embedding após retries")
    
    async def embed_texts(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        Gera embeddings para múltiplos textos (batch).
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de EmbeddingResult
        """
        results: list[EmbeddingResult] = []
        uncached_texts: list[str] = []
        uncached_indices: list[int] = []
        
        # Verificar cache para cada texto
        for i, text in enumerate(texts):
            cached = await self._get_cached(text)
            if cached:
                results.append(EmbeddingResult(
                    text=text,
                    embedding=cached,
                    model=self.embedding_config.model.value,
                    dimensions=len(cached),
                    tokens_used=0,
                    cached=True
                ))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                results.append(None)  # Placeholder
        
        # Processar textos não cacheados em batches
        if uncached_texts:
            for batch_start in range(0, len(uncached_texts), self.embedding_config.batch_size):
                batch_end = min(batch_start + self.embedding_config.batch_size, len(uncached_texts))
                batch = uncached_texts[batch_start:batch_end]
                
                for attempt in range(self.embedding_config.max_retries):
                    try:
                        response = await self.client.embeddings.create(
                            model=self.embedding_config.model.value,
                            input=batch,
                            dimensions=self.embedding_config.dimensions
                        )
                        
                        self.total_tokens += response.usage.total_tokens
                        
                        for j, emb_data in enumerate(response.data):
                            text = batch[j]
                            embedding = emb_data.embedding
                            
                            # Salvar no cache
                            await self._set_cache(text, embedding)
                            
                            # Atualizar resultado
                            idx = uncached_indices[batch_start + j]
                            results[idx] = EmbeddingResult(
                                text=text,
                                embedding=embedding,
                                model=self.embedding_config.model.value,
                                dimensions=len(embedding),
                                tokens_used=response.usage.total_tokens // len(batch),
                                cached=False
                            )
                        
                        break
                        
                    except openai.RateLimitError:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limit, aguardando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    except Exception as e:
                        logger.error(f"Erro ao gerar embeddings: {e}")
                        if attempt == self.embedding_config.max_retries - 1:
                            raise
        
        return [r for r in results if r is not None]
    
    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores."""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))
    
    def get_metrics(self) -> dict:
        """Retorna métricas do serviço."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_requests, 1),
            "total_tokens": self.total_tokens
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._redis:
            await self._redis.close()


# Singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(config: Optional[RAGConfig] = None) -> EmbeddingService:
    """Retorna o serviço de embeddings singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(config)
    return _embedding_service

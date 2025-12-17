"""
RAG v2 - Query Processor

Processamento avançado de queries incluindo:
- Query expansion
- HyDE (Hypothetical Document Embeddings)
- Step-back prompting
- Query decomposition
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Any
import logging
import hashlib

from openai import AsyncOpenAI

from .config import RAGConfig, QueryConfig, get_rag_config


logger = logging.getLogger(__name__)


@dataclass
class ProcessedQuery:
    """Query processada."""
    original_query: str
    expanded_queries: list[str] = field(default_factory=list)
    hyde_document: Optional[str] = None
    step_back_query: Optional[str] = None
    sub_queries: list[str] = field(default_factory=list)
    
    @property
    def all_queries(self) -> list[str]:
        """Retorna todas as variações da query."""
        queries = [self.original_query]
        queries.extend(self.expanded_queries)
        if self.step_back_query:
            queries.append(self.step_back_query)
        queries.extend(self.sub_queries)
        return queries


class QueryProcessor:
    """
    Processador de queries para RAG.
    
    Features:
    - Query expansion: gera variações da query
    - HyDE: gera documento hipotético para busca
    - Step-back: faz pergunta mais geral primeiro
    - Decomposition: quebra query complexa em sub-queries
    """
    
    EXPANSION_PROMPT = """Given the following search query, generate {count} alternative phrasings 
that could help find relevant information. Return only the alternative queries, one per line.

Original query: {query}

Alternative queries:"""

    HYDE_PROMPT = """Given the following question, write a hypothetical document passage that 
would answer this question. The passage should be informative and detailed.

Question: {query}

Hypothetical passage:"""

    STEP_BACK_PROMPT = """Given the following specific question, generate a more general, 
higher-level question that could help understand the broader context.

Specific question: {query}

General question:"""

    DECOMPOSITION_PROMPT = """Break down the following complex question into {count} simpler 
sub-questions that together would help answer the original question.
Return only the sub-questions, one per line.

Complex question: {query}

Sub-questions:"""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        self.query_config = self.config.query
        
        # Cliente OpenAI
        self._client: Optional[AsyncOpenAI] = None
        
        # Cache de processamento
        self._cache: dict[str, ProcessedQuery] = {}
        
        # Métricas
        self.total_processed = 0
        self.cache_hits = 0
    
    async def _get_client(self) -> AsyncOpenAI:
        """Retorna cliente OpenAI."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.config.embedding.openai_api_key)
        return self._client
    
    def _cache_key(self, query: str) -> str:
        """Gera chave de cache."""
        return hashlib.sha256(query.encode()).hexdigest()
    
    async def _call_llm(self, prompt: str) -> str:
        """Chama LLM para processamento."""
        client = await self._get_client()
        
        response = await client.chat.completions.create(
            model=self.query_config.hyde_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    async def expand_query(self, query: str) -> list[str]:
        """
        Gera variações da query para melhorar recall.
        
        Args:
            query: Query original
            
        Returns:
            Lista de queries expandidas
        """
        if not self.query_config.enable_expansion:
            return []
        
        try:
            prompt = self.EXPANSION_PROMPT.format(
                query=query,
                count=self.query_config.expansion_count
            )
            
            response = await self._call_llm(prompt)
            
            # Parse linhas
            queries = [q.strip() for q in response.split("\n") if q.strip()]
            return queries[:self.query_config.expansion_count]
            
        except Exception as e:
            logger.error(f"Erro na expansão de query: {e}")
            return []
    
    async def generate_hyde(self, query: str) -> Optional[str]:
        """
        Gera documento hipotético (HyDE) para a query.
        
        O embedding do documento hipotético geralmente é mais
        próximo de documentos reais relevantes do que o embedding
        da query direta.
        
        Args:
            query: Query original
            
        Returns:
            Documento hipotético ou None
        """
        if not self.query_config.enable_hyde:
            return None
        
        try:
            prompt = self.HYDE_PROMPT.format(query=query)
            return await self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Erro na geração HyDE: {e}")
            return None
    
    async def generate_step_back(self, query: str) -> Optional[str]:
        """
        Gera pergunta step-back (mais geral).
        
        Útil para queries muito específicas onde contexto
        mais amplo pode ajudar.
        
        Args:
            query: Query original
            
        Returns:
            Query mais geral ou None
        """
        if not self.query_config.enable_step_back:
            return None
        
        try:
            prompt = self.STEP_BACK_PROMPT.format(query=query)
            return await self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Erro na geração step-back: {e}")
            return None
    
    async def decompose_query(self, query: str) -> list[str]:
        """
        Decompõe query complexa em sub-queries.
        
        Args:
            query: Query complexa
            
        Returns:
            Lista de sub-queries
        """
        if not self.query_config.enable_decomposition:
            return []
        
        try:
            prompt = self.DECOMPOSITION_PROMPT.format(
                query=query,
                count=self.query_config.max_sub_queries
            )
            
            response = await self._call_llm(prompt)
            
            # Parse linhas
            queries = [q.strip() for q in response.split("\n") if q.strip()]
            return queries[:self.query_config.max_sub_queries]
            
        except Exception as e:
            logger.error(f"Erro na decomposição de query: {e}")
            return []
    
    async def process(self, query: str, use_cache: bool = True) -> ProcessedQuery:
        """
        Processa query aplicando todas as técnicas configuradas.
        
        Args:
            query: Query original
            use_cache: Se deve usar cache
            
        Returns:
            ProcessedQuery com todas as variações
        """
        self.total_processed += 1
        
        # Verificar cache
        cache_key = self._cache_key(query)
        if use_cache and cache_key in self._cache:
            self.cache_hits += 1
            return self._cache[cache_key]
        
        # Processar em paralelo
        tasks = [
            self.expand_query(query),
            self.generate_hyde(query),
            self.generate_step_back(query),
            self.decompose_query(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        expanded = results[0] if not isinstance(results[0], Exception) else []
        hyde = results[1] if not isinstance(results[1], Exception) else None
        step_back = results[2] if not isinstance(results[2], Exception) else None
        sub_queries = results[3] if not isinstance(results[3], Exception) else []
        
        processed = ProcessedQuery(
            original_query=query,
            expanded_queries=expanded,
            hyde_document=hyde,
            step_back_query=step_back,
            sub_queries=sub_queries
        )
        
        # Salvar no cache
        if use_cache:
            self._cache[cache_key] = processed
        
        return processed
    
    async def process_batch(self, queries: list[str]) -> list[ProcessedQuery]:
        """
        Processa múltiplas queries.
        
        Args:
            queries: Lista de queries
            
        Returns:
            Lista de ProcessedQuery
        """
        tasks = [self.process(q) for q in queries]
        return await asyncio.gather(*tasks)
    
    def classify_query(self, query: str) -> dict:
        """
        Classifica o tipo de query para otimizar retrieval.
        
        Args:
            query: Query a classificar
            
        Returns:
            Dicionário com classificações
        """
        query_lower = query.lower()
        
        # Detectar tipo de pergunta
        is_factual = any(w in query_lower for w in ["o que é", "what is", "define", "quem é", "who is"])
        is_comparison = any(w in query_lower for w in ["diferença", "difference", "compare", "versus", "vs"])
        is_how = any(w in query_lower for w in ["como", "how to", "how do", "como fazer"])
        is_why = any(w in query_lower for w in ["por que", "why", "por quê"])
        is_list = any(w in query_lower for w in ["liste", "list", "quais são", "enumere"])
        
        # Complexidade
        word_count = len(query.split())
        is_complex = word_count > 15 or "e" in query_lower and "ou" in query_lower
        
        return {
            "is_factual": is_factual,
            "is_comparison": is_comparison,
            "is_how": is_how,
            "is_why": is_why,
            "is_list": is_list,
            "is_complex": is_complex,
            "word_count": word_count,
            "suggested_method": self._suggest_method({
                "is_factual": is_factual,
                "is_comparison": is_comparison,
                "is_how": is_how,
                "is_complex": is_complex
            })
        }
    
    def _suggest_method(self, classification: dict) -> str:
        """Sugere método de retrieval baseado na classificação."""
        if classification["is_complex"]:
            return "decompose_then_hybrid"
        elif classification["is_factual"]:
            return "vector"
        elif classification["is_comparison"]:
            return "graph"
        else:
            return "hybrid"
    
    def get_metrics(self) -> dict:
        """Retorna métricas do processador."""
        return {
            "total_processed": self.total_processed,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_processed, 1),
            "cache_size": len(self._cache)
        }
    
    def clear_cache(self) -> None:
        """Limpa cache de processamento."""
        self._cache.clear()


# Singleton
_query_processor: Optional[QueryProcessor] = None


def get_query_processor(config: Optional[RAGConfig] = None) -> QueryProcessor:
    """Retorna o processador de queries singleton."""
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessor(config)
    return _query_processor

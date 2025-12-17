"""
Agentic RAG Engine - RAG que planeja, executa e itera autonomamente.

Sprint 2: Agentic RAG Engine
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from ..core.types import DomainType, RAGMode, RAGQuery, RAGResult, RAGSource

logger = logging.getLogger(__name__)


class SearchStrategy(str, Enum):
    """Estratégias de busca."""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    GRAPH = "graph"
    MULTI_HOP = "multi_hop"


@dataclass
class SearchPlan:
    """Plano de busca gerado pelo agente."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    intent: str = ""
    strategies: List[SearchStrategy] = field(default_factory=list)
    sub_queries: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    expected_sources: int = 10
    confidence_threshold: float = 0.7
    max_iterations: int = 3


@dataclass
class SearchIteration:
    """Resultado de uma iteração de busca."""
    iteration: int
    strategy: SearchStrategy
    query: str
    results: List[RAGSource]
    quality_score: float
    feedback: str = ""


@dataclass
class AgenticRAGResult:
    """Resultado completo do Agentic RAG."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    answer: str = ""
    sources: List[RAGSource] = field(default_factory=list)
    confidence: float = 0.0
    
    # Planning
    plan: Optional[SearchPlan] = None
    
    # Iterations
    iterations: List[SearchIteration] = field(default_factory=list)
    total_iterations: int = 0
    
    # Quality
    hallucination_check: bool = False
    hallucination_score: float = 0.0
    
    # Performance
    latency_ms: float = 0.0
    tokens_used: int = 0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


class AgenticRAGEngine:
    """
    Engine de Agentic RAG - RAG que pensa antes de buscar.
    
    Features:
    - Query Analysis & Intent Detection
    - Search Planning
    - Multi-Strategy Search
    - Iterative Refinement
    - Quality Assessment
    - Hallucination Detection
    - Source Verification
    """
    
    def __init__(
        self,
        domain: DomainType,
        embedding_model: str = "text-embedding-3-large",
        llm_model: str = "gpt-4o",
        vector_store: Optional[Any] = None
    ):
        self.domain = domain
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.vector_store = vector_store
        
        # Components
        self.planner = SearchPlanner()
        self.executor = SearchExecutor()
        self.evaluator = QualityEvaluator()
        self.synthesizer = AnswerSynthesizer()
        self.verifier = HallucinationVerifier()
        
        logger.info("AgenticRAGEngine initialized for domain: %s", domain.value)
    
    async def query(
        self,
        query: str,
        context: Optional[Dict] = None,
        max_iterations: int = 3,
        confidence_threshold: float = 0.7
    ) -> AgenticRAGResult:
        """
        Execute an agentic RAG query.
        
        1. Analyze query and create search plan
        2. Execute searches in parallel/sequence
        3. Evaluate quality and iterate if needed
        4. Synthesize answer with citations
        5. Verify for hallucinations
        """
        start_time = datetime.now()
        result = AgenticRAGResult(query=query)
        
        logger.info("Starting Agentic RAG query: %s", query[:100])
        
        # Step 1: Create search plan
        plan = await self.planner.create_plan(
            query=query,
            domain=self.domain,
            context=context,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold
        )
        result.plan = plan
        logger.debug("Search plan created with %d strategies", len(plan.strategies))
        
        # Step 2: Execute iterative search
        all_sources = []
        iterations = []
        
        for iteration in range(max_iterations):
            # Execute searches for this iteration
            iteration_results = await self._execute_iteration(
                plan=plan,
                iteration=iteration,
                previous_results=all_sources
            )
            iterations.append(iteration_results)
            
            # Collect sources
            all_sources.extend(iteration_results.results)
            
            # Evaluate quality
            quality = await self.evaluator.assess(
                query=query,
                sources=all_sources,
                threshold=confidence_threshold
            )
            
            logger.debug("Iteration %d: quality=%.2f", iteration + 1, quality.score)
            
            # Check if quality is sufficient
            if quality.score >= confidence_threshold:
                logger.info("Quality threshold met at iteration %d", iteration + 1)
                break
            
            # Refine plan for next iteration
            plan = await self.planner.refine_plan(
                plan=plan,
                feedback=quality.feedback,
                iteration=iteration + 1
            )
        
        result.iterations = iterations
        result.total_iterations = len(iterations)
        
        # Step 3: Deduplicate and rank sources
        unique_sources = self._deduplicate_sources(all_sources)
        ranked_sources = await self._rank_sources(query, unique_sources)
        result.sources = ranked_sources[:10]  # Top 10 sources
        
        # Step 4: Synthesize answer
        answer = await self.synthesizer.generate(
            query=query,
            sources=result.sources,
            domain=self.domain
        )
        result.answer = answer.text
        result.confidence = answer.confidence
        result.tokens_used = answer.tokens_used
        
        # Step 5: Verify hallucinations
        verification = await self.verifier.verify(
            answer=result.answer,
            sources=result.sources
        )
        result.hallucination_check = True
        result.hallucination_score = verification.score
        
        # If hallucination detected, regenerate with stricter constraints
        if verification.score > 0.3:
            logger.warning("Hallucination detected (score=%.2f), regenerating", verification.score)
            answer = await self.synthesizer.generate(
                query=query,
                sources=result.sources,
                domain=self.domain,
                strict_grounding=True
            )
            result.answer = answer.text
            result.confidence = answer.confidence * 0.9  # Reduce confidence
        
        # Calculate latency
        result.latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info("Agentic RAG completed: confidence=%.2f, iterations=%d, latency=%.0fms",
                   result.confidence, result.total_iterations, result.latency_ms)
        
        return result
    
    async def _execute_iteration(
        self,
        plan: SearchPlan,
        iteration: int,
        previous_results: List[RAGSource]
    ) -> SearchIteration:
        """Execute a single search iteration."""
        # Select strategy for this iteration
        strategy_idx = iteration % len(plan.strategies)
        strategy = plan.strategies[strategy_idx]
        
        # Select query
        if iteration == 0:
            search_query = plan.query
        elif iteration < len(plan.sub_queries):
            search_query = plan.sub_queries[iteration]
        else:
            search_query = plan.query
        
        # Execute search
        results = await self.executor.search(
            query=search_query,
            strategy=strategy,
            filters=plan.filters,
            limit=plan.expected_sources
        )
        
        # Calculate quality
        quality = await self.evaluator.assess_iteration(
            query=search_query,
            results=results
        )
        
        return SearchIteration(
            iteration=iteration,
            strategy=strategy,
            query=search_query,
            results=results,
            quality_score=quality
        )
    
    def _deduplicate_sources(self, sources: List[RAGSource]) -> List[RAGSource]:
        """Remove duplicate sources."""
        seen_ids = set()
        unique = []
        for source in sources:
            if source.id not in seen_ids:
                seen_ids.add(source.id)
                unique.append(source)
        return unique
    
    async def _rank_sources(
        self,
        query: str,
        sources: List[RAGSource]
    ) -> List[RAGSource]:
        """Rank sources by relevance."""
        # Simple ranking by score for now
        return sorted(sources, key=lambda s: s.score, reverse=True)


# ============================================================
# SUPPORTING CLASSES
# ============================================================

class SearchPlanner:
    """Plans search strategies based on query analysis."""
    
    async def create_plan(
        self,
        query: str,
        domain: DomainType,
        context: Optional[Dict],
        max_iterations: int,
        confidence_threshold: float
    ) -> SearchPlan:
        """Create a search plan."""
        # Analyze query intent
        intent = await self._analyze_intent(query)
        
        # Select strategies based on intent
        strategies = self._select_strategies(intent, domain)
        
        # Generate sub-queries for multi-hop
        sub_queries = await self._generate_sub_queries(query, intent)
        
        return SearchPlan(
            query=query,
            intent=intent,
            strategies=strategies,
            sub_queries=sub_queries,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold
        )
    
    async def refine_plan(
        self,
        plan: SearchPlan,
        feedback: str,
        iteration: int
    ) -> SearchPlan:
        """Refine plan based on feedback."""
        # Adjust strategies based on feedback
        refined = SearchPlan(
            query=plan.query,
            intent=plan.intent,
            strategies=plan.strategies,
            sub_queries=plan.sub_queries,
            max_iterations=plan.max_iterations,
            confidence_threshold=plan.confidence_threshold
        )
        
        # Add alternative strategies if initial ones failed
        if iteration > 0 and SearchStrategy.MULTI_HOP not in refined.strategies:
            refined.strategies.append(SearchStrategy.MULTI_HOP)
        
        return refined
    
    async def _analyze_intent(self, query: str) -> str:
        """Analyze query intent."""
        # Simple intent detection
        query_lower = query.lower()
        if any(w in query_lower for w in ["como", "how", "qual", "what"]):
            return "informational"
        elif any(w in query_lower for w in ["compare", "diferença", "versus"]):
            return "comparison"
        elif any(w in query_lower for w in ["exemplo", "example", "caso"]):
            return "example"
        else:
            return "general"
    
    def _select_strategies(self, intent: str, domain: DomainType) -> List[SearchStrategy]:
        """Select search strategies."""
        strategies = [SearchStrategy.HYBRID]  # Always start with hybrid
        
        if intent == "comparison":
            strategies.append(SearchStrategy.MULTI_HOP)
        elif intent == "example":
            strategies.append(SearchStrategy.KEYWORD)
        
        return strategies
    
    async def _generate_sub_queries(self, query: str, intent: str) -> List[str]:
        """Generate sub-queries for complex questions."""
        # Simple sub-query generation
        sub_queries = []
        
        if intent == "comparison":
            # Extract entities and create comparison queries
            sub_queries = [
                f"Definição de {query.split()[0]}",
                f"Características de {query.split()[-1]}"
            ]
        
        return sub_queries


class SearchExecutor:
    """Executes searches with different strategies."""
    
    async def search(
        self,
        query: str,
        strategy: SearchStrategy,
        filters: Dict[str, Any],
        limit: int
    ) -> List[RAGSource]:
        """Execute a search with given strategy."""
        # Simulated search results
        results = []
        
        for i in range(min(limit, 5)):
            results.append(RAGSource(
                id=f"source_{strategy.value}_{i}",
                content=f"Content for query '{query[:50]}...' using {strategy.value} strategy.",
                score=0.9 - (i * 0.1),
                metadata={
                    "strategy": strategy.value,
                    "query": query
                }
            ))
        
        return results


class QualityEvaluator:
    """Evaluates search result quality."""
    
    async def assess(
        self,
        query: str,
        sources: List[RAGSource],
        threshold: float
    ) -> Any:
        """Assess overall quality."""
        if not sources:
            return type("Quality", (), {"score": 0.0, "feedback": "No sources found"})()
        
        avg_score = sum(s.score for s in sources) / len(sources)
        
        feedback = ""
        if avg_score < threshold:
            feedback = "Sources have low relevance scores"
        
        return type("Quality", (), {"score": avg_score, "feedback": feedback})()
    
    async def assess_iteration(
        self,
        query: str,
        results: List[RAGSource]
    ) -> float:
        """Assess iteration quality."""
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)


class AnswerSynthesizer:
    """Synthesizes answers from sources."""
    
    async def generate(
        self,
        query: str,
        sources: List[RAGSource],
        domain: DomainType,
        strict_grounding: bool = False
    ) -> Any:
        """Generate answer from sources."""
        # Build context from sources
        context = "\n\n".join([
            f"[{i+1}] {s.content}"
            for i, s in enumerate(sources[:5])
        ])
        
        # Generate answer (simulated)
        answer = f"Based on the available information about '{query[:50]}' in the {domain.value} domain:\n\n"
        answer += f"The analysis of {len(sources)} sources indicates that "
        answer += "this topic requires consideration of multiple factors. "
        
        if strict_grounding:
            answer += "All statements are directly supported by the provided sources."
        
        return type("Answer", (), {
            "text": answer,
            "confidence": 0.85 if not strict_grounding else 0.75,
            "tokens_used": len(answer.split()) * 4
        })()


class HallucinationVerifier:
    """Verifies answers for hallucinations."""
    
    async def verify(
        self,
        answer: str,
        sources: List[RAGSource]
    ) -> Any:
        """Verify answer against sources."""
        # Simulated verification
        # In production, this would use NLI or other verification methods
        
        source_content = " ".join(s.content for s in sources)
        
        # Simple overlap check
        answer_words = set(answer.lower().split())
        source_words = set(source_content.lower().split())
        
        overlap = len(answer_words & source_words) / len(answer_words) if answer_words else 0
        
        # Higher overlap = lower hallucination score
        hallucination_score = 1 - min(overlap * 2, 1.0)
        
        return type("Verification", (), {
            "score": hallucination_score,
            "grounded": hallucination_score < 0.3
        })()


# ============================================================
# FACTORY
# ============================================================

def create_agentic_rag(domain: DomainType, **kwargs) -> AgenticRAGEngine:
    """Factory function to create Agentic RAG engine."""
    return AgenticRAGEngine(domain=domain, **kwargs)

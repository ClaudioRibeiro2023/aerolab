"""
LLM Evaluations - Avaliação de qualidade de respostas LLM.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class EvaluationType(str, Enum):
    """Tipos de avaliação."""
    RELEVANCE = "relevance"         # Relevância da resposta
    COHERENCE = "coherence"         # Coerência do texto
    FLUENCY = "fluency"             # Fluência linguística
    GROUNDEDNESS = "groundedness"   # Fundamentação em contexto
    HALLUCINATION = "hallucination" # Detecção de alucinação
    TOXICITY = "toxicity"           # Detecção de toxicidade
    SAFETY = "safety"               # Avaliação de segurança
    ACCURACY = "accuracy"           # Precisão factual
    HELPFULNESS = "helpfulness"     # Utilidade da resposta


@dataclass
class EvaluationResult:
    """Resultado de uma avaliação."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Referência
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
    # Tipo
    type: EvaluationType = EvaluationType.RELEVANCE
    
    # Score
    score: float = 0.0  # 0.0 - 1.0
    passed: bool = True
    threshold: float = 0.5
    
    # Detalhes
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    
    # Metadata
    evaluator: str = ""  # model ou human
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "type": self.type.value,
            "score": self.score,
            "passed": self.passed,
            "threshold": self.threshold,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "evaluator": self.evaluator,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EvaluationSuite:
    """Conjunto de avaliações."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Evaluations
    evaluation_types: List[EvaluationType] = field(default_factory=list)
    
    # Results
    results: List[EvaluationResult] = field(default_factory=list)
    
    # Aggregates
    overall_score: float = 0.0
    pass_rate: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_result(self, result: EvaluationResult) -> None:
        """Adiciona resultado."""
        self.results.append(result)
        self._update_aggregates()
    
    def _update_aggregates(self) -> None:
        """Atualiza métricas agregadas."""
        if not self.results:
            return
        
        self.overall_score = sum(r.score for r in self.results) / len(self.results)
        self.pass_rate = len([r for r in self.results if r.passed]) / len(self.results)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "evaluationTypes": [e.value for e in self.evaluation_types],
            "results": [r.to_dict() for r in self.results],
            "overallScore": self.overall_score,
            "passRate": self.pass_rate,
            "createdAt": self.created_at.isoformat(),
        }


class LLMEvaluator:
    """
    Avaliador de qualidade LLM.
    
    Executa avaliações de qualidade em respostas LLM.
    """
    
    def __init__(self):
        self._results: Dict[str, List[EvaluationResult]] = {}  # trace_id -> results
    
    async def evaluate_relevance(
        self,
        query: str,
        response: str,
        context: Optional[str] = None
    ) -> EvaluationResult:
        """Avalia relevância da resposta."""
        # Em produção: usar LLM para avaliar
        # Por agora: heurística simples
        
        score = 0.8  # Placeholder
        
        # Verificar overlap de palavras
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words) / len(query_words) if query_words else 0
        
        score = min(0.5 + overlap, 1.0)
        
        return EvaluationResult(
            type=EvaluationType.RELEVANCE,
            score=score,
            passed=score >= 0.5,
            threshold=0.5,
            reasoning=f"Word overlap: {overlap:.2%}",
            evaluator="heuristic"
        )
    
    async def evaluate_groundedness(
        self,
        response: str,
        context: str
    ) -> EvaluationResult:
        """Avalia se resposta é fundamentada no contexto."""
        # Em produção: usar LLM para verificar claims
        
        # Heurística: verificar se palavras do contexto aparecem na resposta
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        
        grounded_words = context_words & response_words
        score = len(grounded_words) / len(response_words) if response_words else 0
        
        return EvaluationResult(
            type=EvaluationType.GROUNDEDNESS,
            score=score,
            passed=score >= 0.3,
            threshold=0.3,
            reasoning=f"Grounded words: {len(grounded_words)}",
            evaluator="heuristic"
        )
    
    async def evaluate_hallucination(
        self,
        response: str,
        context: str,
        facts: Optional[List[str]] = None
    ) -> EvaluationResult:
        """Detecta alucinações na resposta."""
        # Em produção: verificar claims contra base de conhecimento
        
        # Placeholder: assumir baixa taxa de alucinação
        score = 0.9  # 0.9 = 10% chance de alucinação
        
        return EvaluationResult(
            type=EvaluationType.HALLUCINATION,
            score=score,
            passed=score >= 0.7,
            threshold=0.7,
            reasoning="Hallucination detection placeholder",
            evaluator="heuristic"
        )
    
    async def evaluate_coherence(
        self,
        response: str
    ) -> EvaluationResult:
        """Avalia coerência do texto."""
        # Heurística simples baseada em estrutura
        
        sentences = response.split('.')
        has_structure = len(sentences) >= 2
        has_length = len(response) >= 50
        
        score = 0.5
        if has_structure:
            score += 0.25
        if has_length:
            score += 0.25
        
        return EvaluationResult(
            type=EvaluationType.COHERENCE,
            score=score,
            passed=score >= 0.5,
            threshold=0.5,
            reasoning=f"Sentences: {len(sentences)}, Length: {len(response)}",
            evaluator="heuristic"
        )
    
    async def evaluate_toxicity(
        self,
        response: str
    ) -> EvaluationResult:
        """Detecta conteúdo tóxico."""
        # Em produção: usar modelo de toxicidade
        
        toxic_keywords = ["hate", "kill", "violence", "offensive"]
        response_lower = response.lower()
        
        has_toxic = any(kw in response_lower for kw in toxic_keywords)
        score = 0.0 if has_toxic else 1.0
        
        return EvaluationResult(
            type=EvaluationType.TOXICITY,
            score=score,
            passed=score >= 0.9,
            threshold=0.9,
            reasoning="No toxic content detected" if score == 1.0 else "Potential toxic content",
            evaluator="keyword_filter"
        )
    
    async def run_evaluation_suite(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        evaluation_types: Optional[List[EvaluationType]] = None
    ) -> EvaluationSuite:
        """Executa suite completa de avaliações."""
        suite = EvaluationSuite(
            name="Full Evaluation",
            evaluation_types=evaluation_types or [
                EvaluationType.RELEVANCE,
                EvaluationType.COHERENCE,
                EvaluationType.TOXICITY
            ]
        )
        
        for eval_type in suite.evaluation_types:
            if eval_type == EvaluationType.RELEVANCE:
                result = await self.evaluate_relevance(query, response, context)
            elif eval_type == EvaluationType.COHERENCE:
                result = await self.evaluate_coherence(response)
            elif eval_type == EvaluationType.TOXICITY:
                result = await self.evaluate_toxicity(response)
            elif eval_type == EvaluationType.GROUNDEDNESS and context:
                result = await self.evaluate_groundedness(response, context)
            elif eval_type == EvaluationType.HALLUCINATION and context:
                result = await self.evaluate_hallucination(response, context)
            else:
                continue
            
            suite.add_result(result)
        
        return suite
    
    def store_results(
        self,
        trace_id: str,
        results: List[EvaluationResult]
    ) -> None:
        """Armazena resultados."""
        for result in results:
            result.trace_id = trace_id
        self._results[trace_id] = results
    
    def get_results(self, trace_id: str) -> List[EvaluationResult]:
        """Obtém resultados por trace."""
        return self._results.get(trace_id, [])
    
    def get_aggregate_scores(
        self,
        trace_ids: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Obtém scores agregados."""
        all_results = []
        
        if trace_ids:
            for tid in trace_ids:
                all_results.extend(self._results.get(tid, []))
        else:
            for results in self._results.values():
                all_results.extend(results)
        
        if not all_results:
            return {}
        
        # Agregar por tipo
        by_type: Dict[str, List[float]] = {}
        for result in all_results:
            if result.type.value not in by_type:
                by_type[result.type.value] = []
            by_type[result.type.value].append(result.score)
        
        return {
            eval_type: sum(scores) / len(scores)
            for eval_type, scores in by_type.items()
        }


# Singleton
_evaluator: Optional[LLMEvaluator] = None


def get_evaluator() -> LLMEvaluator:
    """Obtém avaliador."""
    global _evaluator
    if _evaluator is None:
        _evaluator = LLMEvaluator()
    return _evaluator

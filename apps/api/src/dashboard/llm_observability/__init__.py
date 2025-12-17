"""
LLM Observability - Métricas específicas para LLMs.

Features:
- Token usage e custos
- Latência por modelo
- Qualidade (hallucination, accuracy)
- Comparações A/B de modelos
"""

from .traces import LLMTrace, LLMSpan, get_trace_collector
from .evaluations import LLMEvaluator, EvaluationResult
from .costs import LLMCostTracker, ModelPricing
from .latency import LatencyTracker, LatencyPercentiles

__all__ = [
    "LLMTrace",
    "LLMSpan",
    "get_trace_collector",
    "LLMEvaluator",
    "EvaluationResult",
    "LLMCostTracker",
    "ModelPricing",
    "LatencyTracker",
    "LatencyPercentiles",
]

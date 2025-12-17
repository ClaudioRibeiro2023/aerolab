"""
AI Insights - Insights inteligentes para dashboards.

Features:
- Detecção de anomalias
- Previsão de tendências
- Análise de causa raiz
- Resumos em linguagem natural
"""

from .anomalies import AnomalyDetector, Anomaly
from .forecasting import Forecaster, Forecast
from .recommendations import RecommendationEngine, Recommendation
from .summaries import InsightSummarizer

__all__ = [
    "AnomalyDetector",
    "Anomaly",
    "Forecaster",
    "Forecast",
    "RecommendationEngine",
    "Recommendation",
    "InsightSummarizer",
]

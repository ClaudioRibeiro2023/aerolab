"""
Dashboard Module v2 - Sistema completo de dashboards e observability.

Features:
- 25+ tipos de widgets
- Real-time updates via WebSocket
- LLM/Agent/RAG observability
- AI-powered insights
- Alertas e incidentes
- Embedded analytics
"""

# Core components
from .core.widgets import Widget, WidgetType, WidgetConfig
from .core.layouts import Layout, LayoutType, GridPosition
from .core.datasources import DataSource, DataSourceType
from .core.themes import Theme, ThemeConfig
from .service import DashboardService, get_dashboard_service

# Metrics
from .metrics import (
    MetricCollector,
    Metric,
    MetricType,
    TimeSeriesAggregator,
    MetricStorage,
    QueryEngine,
)

# LLM Observability
from .llm_observability import (
    LLMTrace,
    LLMSpan,
    get_trace_collector,
    LLMEvaluator,
    LLMCostTracker,
    LatencyTracker,
)

# Agent Observability
from .agent_observability import (
    AgentTrace,
    AgentSpan,
    AgentTraceCollector,
    get_agent_trace_collector,
    AgentMetrics,
    AgentPerformance,
    ExecutionReplay,
    DecisionAnalyzer,
)

# Alerts
from .alerts import (
    AlertRule,
    AlertCondition,
    AlertSeverity,
    AlertEngine,
    NotificationChannel,
    ChannelType,
    Incident,
    IncidentStatus,
)

# Insights
from .insights import (
    AnomalyDetector,
    Anomaly,
    Forecaster,
    Forecast,
    RecommendationEngine,
    Recommendation,
    InsightSummarizer,
)

__all__ = [
    # Core
    "Widget",
    "WidgetType",
    "WidgetConfig",
    "Layout",
    "LayoutType",
    "GridPosition",
    "DataSource",
    "DataSourceType",
    "Theme",
    "ThemeConfig",
    # Service
    "DashboardService",
    "get_dashboard_service",
    # Metrics
    "MetricCollector",
    "Metric",
    "MetricType",
    "TimeSeriesAggregator",
    "MetricStorage",
    "QueryEngine",
    # LLM Observability
    "LLMTrace",
    "LLMSpan",
    "get_trace_collector",
    "LLMEvaluator",
    "LLMCostTracker",
    "LatencyTracker",
    # Agent Observability
    "AgentTrace",
    "AgentSpan",
    "AgentTraceCollector",
    "get_agent_trace_collector",
    "AgentMetrics",
    "AgentPerformance",
    "ExecutionReplay",
    "DecisionAnalyzer",
    # Alerts
    "AlertRule",
    "AlertCondition",
    "AlertSeverity",
    "AlertEngine",
    "NotificationChannel",
    "ChannelType",
    "Incident",
    "IncidentStatus",
    # Insights
    "AnomalyDetector",
    "Anomaly",
    "Forecaster",
    "Forecast",
    "RecommendationEngine",
    "Recommendation",
    "InsightSummarizer",
]

__version__ = "2.0.0"

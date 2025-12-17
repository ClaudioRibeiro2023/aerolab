"""
Dashboard Templates - Templates pré-definidos para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class TemplateCategory(str, Enum):
    """Categorias de templates."""
    LLM_OBSERVABILITY = "llm_observability"
    AGENT_MONITORING = "agent_monitoring"
    SYSTEM_METRICS = "system_metrics"
    COST_ANALYSIS = "cost_analysis"
    USER_ANALYTICS = "user_analytics"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


@dataclass
class WidgetTemplate:
    """Template de widget."""
    id: str
    title: str
    type: str
    query: str
    description: str = ""
    
    # Configuração
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Posição sugerida
    default_width: int = 4
    default_height: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "query": self.query,
            "description": self.description,
            "config": self.config,
            "defaultWidth": self.default_width,
            "defaultHeight": self.default_height,
        }


@dataclass
class DashboardTemplate:
    """Template de dashboard."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    
    # Widgets
    widgets: List[WidgetTemplate] = field(default_factory=list)
    
    # Layout
    layout: Dict[str, Any] = field(default_factory=dict)
    
    # Configurações padrão
    default_time_range: str = "24h"
    auto_refresh: bool = True
    refresh_interval_seconds: int = 30
    
    # Thumbnail
    thumbnail_url: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    author: str = "system"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    # Popularity
    use_count: int = 0
    rating: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "widgets": [w.to_dict() for w in self.widgets],
            "layout": self.layout,
            "defaultTimeRange": self.default_time_range,
            "autoRefresh": self.auto_refresh,
            "refreshIntervalSeconds": self.refresh_interval_seconds,
            "thumbnailUrl": self.thumbnail_url,
            "tags": self.tags,
            "author": self.author,
            "version": self.version,
            "createdAt": self.created_at.isoformat(),
            "useCount": self.use_count,
            "rating": self.rating,
        }


class TemplateManager:
    """Gerenciador de templates de dashboard."""
    
    def __init__(self):
        self._templates: Dict[str, DashboardTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Carrega templates built-in."""
        # LLM Overview
        self.register_template(DashboardTemplate(
            id="llm_overview",
            name="LLM Overview",
            description="Monitor LLM calls, costs, latency and quality metrics",
            category=TemplateCategory.LLM_OBSERVABILITY,
            widgets=[
                WidgetTemplate(
                    id="total_requests",
                    title="Total Requests",
                    type="metric_card",
                    query="sum(llm_requests_total)",
                    config={"metric": {"format": "number", "showTrend": True}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="success_rate",
                    title="Success Rate",
                    type="metric_card",
                    query="rate(llm_success_total) / rate(llm_requests_total)",
                    config={"metric": {"format": "percent", "showTrend": True}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="total_cost",
                    title="Total Cost",
                    type="metric_card",
                    query="sum(llm_cost_usd)",
                    config={"metric": {"format": "currency", "showTrend": True}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="avg_latency",
                    title="Avg Latency",
                    type="metric_card",
                    query="avg(llm_latency_ms)",
                    config={"metric": {"format": "duration", "showTrend": True}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="request_rate",
                    title="Request Rate",
                    type="line_chart",
                    query="rate(llm_requests_total[5m])",
                    config={"chart": {"showLegend": True, "smooth": True}},
                    default_width=6,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="latency_distribution",
                    title="Latency Distribution",
                    type="area_chart",
                    query="histogram_quantile(0.50, llm_latency_bucket), histogram_quantile(0.95, llm_latency_bucket), histogram_quantile(0.99, llm_latency_bucket)",
                    config={"chart": {"showLegend": True, "stacked": False}},
                    default_width=6,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="cost_by_model",
                    title="Cost by Model",
                    type="pie_chart",
                    query="sum(llm_cost_usd) by (model)",
                    config={"chart": {"showLegend": True}},
                    default_width=4,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="top_errors",
                    title="Top Errors",
                    type="table",
                    query="topk(10, count(llm_errors) by (error_type))",
                    config={"table": {"sortable": True, "pageSize": 5}},
                    default_width=8,
                    default_height=3,
                ),
            ],
            tags=["llm", "observability", "costs"],
        ))
        
        # Agent Monitoring
        self.register_template(DashboardTemplate(
            id="agent_monitoring",
            name="Agent Monitoring",
            description="Monitor agent executions, performance and decisions",
            category=TemplateCategory.AGENT_MONITORING,
            widgets=[
                WidgetTemplate(
                    id="active_agents",
                    title="Active Agents",
                    type="metric_card",
                    query="count(distinct(agent_name))",
                    config={"metric": {"format": "number"}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="executions_24h",
                    title="Executions (24h)",
                    type="metric_card",
                    query="sum(agent_executions_total[24h])",
                    config={"metric": {"format": "number", "showTrend": True}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="agent_success_rate",
                    title="Success Rate",
                    type="gauge",
                    query="rate(agent_success_total) / rate(agent_executions_total) * 100",
                    config={"gauge": {"min": 0, "max": 100, "unit": "%"}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="avg_execution_time",
                    title="Avg Execution Time",
                    type="metric_card",
                    query="avg(agent_execution_duration_ms)",
                    config={"metric": {"format": "duration"}},
                    default_width=3,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="executions_timeline",
                    title="Executions Timeline",
                    type="area_chart",
                    query="sum(rate(agent_executions_total[5m])) by (agent_name)",
                    config={"chart": {"showLegend": True, "stacked": True}},
                    default_width=12,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="agent_leaderboard",
                    title="Agent Performance",
                    type="table",
                    query="topk(10, avg(agent_success_rate) by (agent_name))",
                    config={"table": {"sortable": True}},
                    default_width=6,
                    default_height=4,
                ),
                WidgetTemplate(
                    id="tool_usage",
                    title="Tool Usage",
                    type="bar_chart",
                    query="sum(agent_tool_calls) by (tool_name)",
                    config={"chart": {"showLegend": False}},
                    default_width=6,
                    default_height=4,
                ),
            ],
            tags=["agents", "monitoring", "performance"],
        ))
        
        # Cost Analysis
        self.register_template(DashboardTemplate(
            id="cost_analysis",
            name="Cost Analysis",
            description="Analyze LLM costs, trends and optimization opportunities",
            category=TemplateCategory.COST_ANALYSIS,
            widgets=[
                WidgetTemplate(
                    id="total_spend_mtd",
                    title="Total Spend (MTD)",
                    type="metric_card",
                    query="sum(llm_cost_usd[30d])",
                    config={"metric": {"format": "currency", "prefix": "$"}},
                    default_width=4,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="cost_projection",
                    title="Monthly Projection",
                    type="metric_card",
                    query="sum(llm_cost_usd[7d]) * 4",
                    config={"metric": {"format": "currency", "prefix": "$"}},
                    default_width=4,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="cost_per_request",
                    title="Avg Cost/Request",
                    type="metric_card",
                    query="avg(llm_cost_per_request_usd)",
                    config={"metric": {"format": "currency", "precision": 4}},
                    default_width=4,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="daily_costs",
                    title="Daily Costs",
                    type="bar_chart",
                    query="sum(llm_cost_usd) by (day)",
                    config={"chart": {"showLegend": False}},
                    default_width=12,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="cost_by_model",
                    title="Cost by Model",
                    type="donut_chart",
                    query="sum(llm_cost_usd) by (model)",
                    config={"chart": {"showLegend": True}},
                    default_width=6,
                    default_height=4,
                ),
                WidgetTemplate(
                    id="cost_by_user",
                    title="Cost by User",
                    type="table",
                    query="topk(10, sum(llm_cost_usd) by (user_id))",
                    config={"table": {"sortable": True}},
                    default_width=6,
                    default_height=4,
                ),
            ],
            tags=["costs", "analysis", "budget"],
        ))
        
        # System Overview
        self.register_template(DashboardTemplate(
            id="system_overview",
            name="System Overview",
            description="Overall system health and performance metrics",
            category=TemplateCategory.SYSTEM_METRICS,
            widgets=[
                WidgetTemplate(
                    id="system_health",
                    title="System Health",
                    type="gauge",
                    query="avg(system_health_score) * 100",
                    config={"gauge": {"min": 0, "max": 100, "thresholds": [
                        {"value": 90, "color": "#10b981"},
                        {"value": 70, "color": "#f59e0b"},
                        {"value": 0, "color": "#ef4444"},
                    ]}},
                    default_width=4,
                    default_height=3,
                ),
                WidgetTemplate(
                    id="active_sessions",
                    title="Active Sessions",
                    type="metric_card",
                    query="count(active_sessions)",
                    config={"metric": {"format": "number", "showTrend": True}},
                    default_width=4,
                    default_height=2,
                ),
                WidgetTemplate(
                    id="error_rate",
                    title="Error Rate",
                    type="metric_card",
                    query="rate(errors_total) / rate(requests_total) * 100",
                    config={"metric": {"format": "percent"}},
                    default_width=4,
                    default_height=2,
                ),
            ],
            tags=["system", "health", "overview"],
        ))
    
    def register_template(self, template: DashboardTemplate):
        """Registra um template."""
        self._templates[template.id] = template
        logger.debug(f"Registered template: {template.id}")
    
    def get_template(self, template_id: str) -> Optional[DashboardTemplate]:
        """Obtém template por ID."""
        return self._templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[DashboardTemplate]:
        """Lista templates com filtros."""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        return sorted(templates, key=lambda t: t.use_count, reverse=True)
    
    def use_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Usa um template para criar configuração de dashboard.
        
        Incrementa contador de uso e retorna configuração.
        """
        template = self._templates.get(template_id)
        if not template:
            return None
        
        template.use_count += 1
        
        # Gerar configuração de dashboard
        widgets = []
        layout_items = []
        
        x, y = 0, 0
        max_cols = 12
        
        for widget in template.widgets:
            widgets.append({
                "id": f"{widget.id}_{datetime.now().timestamp()}",
                "title": widget.title,
                "type": widget.type,
                "query": widget.query,
                "config": widget.config,
            })
            
            layout_items.append({
                "widgetId": widgets[-1]["id"],
                "position": {
                    "x": x,
                    "y": y,
                    "w": widget.default_width,
                    "h": widget.default_height,
                },
            })
            
            x += widget.default_width
            if x >= max_cols:
                x = 0
                y += widget.default_height
        
        return {
            "name": f"New {template.name}",
            "description": template.description,
            "widgets": widgets,
            "layout": {
                "type": "grid",
                "columns": max_cols,
                "items": layout_items,
            },
            "defaultTimeRange": template.default_time_range,
            "autoRefresh": template.auto_refresh,
            "refreshIntervalSeconds": template.refresh_interval_seconds,
            "tags": template.tags,
        }
    
    def create_custom_template(
        self,
        name: str,
        description: str,
        dashboard_config: Dict[str, Any],
        author: str = "user",
    ) -> DashboardTemplate:
        """Cria template customizado a partir de dashboard."""
        template_id = f"custom_{datetime.now().timestamp()}"
        
        widgets = [
            WidgetTemplate(
                id=w.get("id", f"w_{i}"),
                title=w.get("title", "Widget"),
                type=w.get("type", "metric_card"),
                query=w.get("query", ""),
                config=w.get("config", {}),
            )
            for i, w in enumerate(dashboard_config.get("widgets", []))
        ]
        
        template = DashboardTemplate(
            id=template_id,
            name=name,
            description=description,
            category=TemplateCategory.CUSTOM,
            widgets=widgets,
            layout=dashboard_config.get("layout", {}),
            default_time_range=dashboard_config.get("defaultTimeRange", "24h"),
            author=author,
            tags=["custom"],
        )
        
        self.register_template(template)
        return template
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Lista categorias com contagem."""
        category_counts = {}
        for template in self._templates.values():
            cat = template.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return [
            {"category": cat.value, "count": category_counts.get(cat.value, 0)}
            for cat in TemplateCategory
        ]


# Singleton
_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Obtém gerenciador de templates."""
    global _manager
    if _manager is None:
        _manager = TemplateManager()
    return _manager

"""
Dashboard API Routes - FastAPI endpoints for dashboard services.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from ..service import get_dashboard_service
from ..metrics import MetricCollector, QueryEngine, MetricStorage
from ..alerts import AlertEngine, AlertRule, AlertSeverity
from ..alerts.incidents import IncidentManager
from ..insights import AnomalyDetector, Forecaster, RecommendationEngine, InsightSummarizer
from ..llm_observability import get_trace_collector, LLMCostTracker, LatencyTracker
from ..agent_observability import get_agent_trace_collector, AgentMetrics
from ..builder import get_template_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ============================================================
# Request/Response Models
# ============================================================


class DashboardCreate(BaseModel):
    """Create dashboard request."""

    name: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    folder_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DashboardUpdate(BaseModel):
    """Update dashboard request."""

    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_seconds: Optional[int] = None


class WidgetCreate(BaseModel):
    """Create widget request."""

    title: str
    type: str
    query: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, int]] = None


class AlertRuleCreate(BaseModel):
    """Create alert rule request."""

    name: str
    description: Optional[str] = None
    metric: str
    operator: str
    threshold: float
    severity: str = "warning"
    duration_minutes: int = 5
    channel_ids: List[str] = Field(default_factory=list)


class IncidentCreate(BaseModel):
    """Create incident request."""

    title: str
    description: Optional[str] = None
    severity: str = "sev3"
    alert_rule_ids: List[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Query request."""

    query: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TimeRangeParams(BaseModel):
    """Time range parameters."""

    start: Optional[str] = None
    end: Optional[str] = None
    preset: Optional[str] = "24h"


# ============================================================
# Dashboard Endpoints
# ============================================================


@router.get("/dashboards")
async def list_dashboards(
    folder_id: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
):
    """List all dashboards."""
    service = get_dashboard_service()

    tag_list = tags.split(",") if tags else None
    dashboards = service.list_dashboards(
        folder_id=folder_id, tags=tag_list, limit=limit, offset=offset
    )

    return {
        "dashboards": [d.to_dict() for d in dashboards],
        "total": len(dashboards),
    }


@router.post("/dashboards")
async def create_dashboard(data: DashboardCreate):
    """Create a new dashboard."""
    service = get_dashboard_service()

    # Use template if provided
    if data.template_id:
        template_manager = get_template_manager()
        config = template_manager.use_template(data.template_id)
        if config:
            config["name"] = data.name
            if data.description:
                config["description"] = data.description
            dashboard = service.create_dashboard(**config)
            return dashboard.to_dict()

    dashboard = service.create_dashboard(
        name=data.name,
        description=data.description,
        folder_id=data.folder_id,
        tags=data.tags,
    )

    return dashboard.to_dict()


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get dashboard by ID."""
    service = get_dashboard_service()
    dashboard = service.get_dashboard(dashboard_id)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return dashboard.to_dict()


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(dashboard_id: str, data: DashboardUpdate):
    """Update a dashboard."""
    service = get_dashboard_service()

    updates = data.dict(exclude_none=True)
    dashboard = service.update_dashboard(dashboard_id, **updates)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return dashboard.to_dict()


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(dashboard_id: str):
    """Delete a dashboard."""
    service = get_dashboard_service()
    result = service.delete_dashboard(dashboard_id)

    if not result:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return {"success": True}


# ============================================================
# Widget Endpoints
# ============================================================


@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget(dashboard_id: str, data: WidgetCreate):
    """Add widget to dashboard."""
    service = get_dashboard_service()

    widget = service.add_widget(
        dashboard_id=dashboard_id,
        title=data.title,
        widget_type=data.type,
        query=data.query,
        description=data.description,
        config=data.config,
        position=data.position,
    )

    if not widget:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return widget.to_dict()


@router.delete("/dashboards/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(dashboard_id: str, widget_id: str):
    """Remove widget from dashboard."""
    service = get_dashboard_service()
    result = service.remove_widget(dashboard_id, widget_id)

    if not result:
        raise HTTPException(status_code=404, detail="Widget not found")

    return {"success": True}


# ============================================================
# Query Endpoints
# ============================================================


@router.post("/query")
async def execute_query(data: QueryRequest):
    """Execute metrics query."""
    storage = MetricStorage()
    engine = QueryEngine(storage)

    # Parse time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    if data.start_time:
        start_time = datetime.fromisoformat(data.start_time)
    if data.end_time:
        end_time = datetime.fromisoformat(data.end_time)

    try:
        result = engine.execute(data.query, start_time=start_time, end_time=end_time)
        return result.to_dict() if hasattr(result, "to_dict") else {"data": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics")
async def list_metrics():
    """List available metrics."""
    collector = MetricCollector()
    metrics = collector.list_metrics()

    return {
        "metrics": [
            {
                "name": m.name,
                "type": m.type.value,
                "description": m.description,
                "labels": m.labels,
            }
            for m in metrics
        ]
    }


# ============================================================
# Alerts Endpoints
# ============================================================


@router.get("/alerts/rules")
async def list_alert_rules():
    """List all alert rules."""
    engine = AlertEngine()
    rules = engine.list_rules()

    return {
        "rules": [r.to_dict() for r in rules],
        "total": len(rules),
    }


@router.post("/alerts/rules")
async def create_alert_rule(data: AlertRuleCreate):
    """Create alert rule."""
    engine = AlertEngine()

    rule = AlertRule(
        id=f"rule_{datetime.now().timestamp()}",
        name=data.name,
        description=data.description,
        severity=AlertSeverity(data.severity),
        conditions=[
            {
                "metric": data.metric,
                "operator": data.operator,
                "threshold": data.threshold,
            }
        ],
        for_duration=timedelta(minutes=data.duration_minutes),
        channel_ids=data.channel_ids,
    )

    engine.add_rule(rule)
    return rule.to_dict()


@router.get("/alerts/firing")
async def get_firing_alerts():
    """Get currently firing alerts."""
    engine = AlertEngine()
    firing = engine.get_firing_alerts()

    return {
        "alerts": [r.to_dict() for r in firing],
        "count": len(firing),
    }


# ============================================================
# Incidents Endpoints
# ============================================================


@router.get("/incidents")
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
):
    """List incidents."""
    manager = IncidentManager()

    if status == "open":
        incidents = manager.list_open()
    else:
        incidents = manager.list_all()

    if severity:
        incidents = [i for i in incidents if i.severity == severity]

    return {
        "incidents": [i.to_dict() for i in incidents[:limit]],
        "total": len(incidents),
    }


@router.post("/incidents")
async def create_incident(data: IncidentCreate):
    """Create incident."""
    manager = IncidentManager()

    incident = manager.create(
        title=data.title,
        description=data.description,
        severity=data.severity,
        alert_rule_ids=data.alert_rule_ids,
    )

    return incident.to_dict()


@router.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str, user_id: str = Query(...)):
    """Acknowledge incident."""
    manager = IncidentManager()
    incident = manager.get(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.acknowledge(user_id)
    return incident.to_dict()


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    root_cause: str = Query(...),
    resolution: str = Query(...),
):
    """Resolve incident."""
    manager = IncidentManager()
    incident = manager.get(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.resolve(root_cause, resolution)
    return incident.to_dict()


# ============================================================
# Insights Endpoints
# ============================================================


@router.post("/insights/anomalies")
async def detect_anomalies(
    metric: str,
    start_time: Optional[str] = None,
    sensitivity: float = 0.5,
):
    """Detect anomalies in metric data."""
    detector = AnomalyDetector(sensitivity=sensitivity)
    storage = MetricStorage()

    end = datetime.now()
    start = datetime.fromisoformat(start_time) if start_time else end - timedelta(hours=24)

    points = storage.read(metric, start, end)
    values = [p.value for p in points]
    timestamps = [p.timestamp for p in points]

    anomalies = detector.detect_all(values, timestamps, metric)

    return {
        "anomalies": [a.to_dict() for a in anomalies],
        "count": len(anomalies),
    }


@router.post("/insights/forecast")
async def generate_forecast(
    metric: str,
    periods: int = 10,
    method: str = "auto",
):
    """Generate forecast for metric."""
    forecaster = Forecaster()
    storage = MetricStorage()

    end = datetime.now()
    start = end - timedelta(days=7)

    points = storage.read(metric, start, end)
    values = [p.value for p in points]
    timestamps = [p.timestamp for p in points]

    if method == "linear":
        forecast = forecaster.linear_regression(values, timestamps, periods, metric)
    elif method == "exponential":
        forecast = forecaster.exponential_smoothing(values, timestamps, 0.3, periods, metric)
    else:
        forecast = forecaster.auto_forecast(values, timestamps, periods, metric)

    return forecast.to_dict()


@router.get("/insights/recommendations")
async def get_recommendations():
    """Get AI recommendations."""
    engine = RecommendationEngine()

    # Get current metrics (mock for now)
    metrics = {
        "avg_cost_per_request": 0.05,
        "p95_latency_ms": 2000,
        "error_rate": 0.02,
        "cache_hit_rate": 0.4,
    }

    _ = engine.analyze(metrics)  # Analyze populates internal state
    active = engine.get_active_recommendations()

    return {
        "recommendations": [r.to_dict() for r in active],
        "summary": engine.get_summary(),
    }


@router.get("/insights/summary")
async def get_insights_summary(period: str = "day"):
    """Get insights summary."""
    summarizer = InsightSummarizer()

    # Get current metrics (would come from actual data)
    metrics = {
        "total_requests": 50000,
        "success_rate": 0.97,
        "avg_latency_ms": 150,
        "p95_latency_ms": 450,
        "total_cost_usd": 125.50,
        "error_rate": 0.03,
    }

    summary = summarizer.generate_summary(metrics, period)
    return summary.to_dict()


# ============================================================
# LLM Observability Endpoints
# ============================================================


@router.get("/llm/traces")
async def list_llm_traces(
    limit: int = 50,
    user_id: Optional[str] = None,
    model: Optional[str] = None,
):
    """List LLM traces."""
    collector = get_trace_collector()
    traces = collector.list_traces(limit=limit)

    if user_id:
        traces = [t for t in traces if t.user_id == user_id]

    return {
        "traces": [t.to_dict() for t in traces],
        "total": len(traces),
    }


@router.get("/llm/traces/{trace_id}")
async def get_llm_trace(trace_id: str):
    """Get LLM trace details."""
    collector = get_trace_collector()
    trace = collector.get_trace(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace.to_dict()


@router.get("/llm/costs")
async def get_llm_costs(
    period: str = "day",
    group_by: str = "model",
):
    """Get LLM cost analysis."""
    tracker = LLMCostTracker()

    if group_by == "model":
        costs = tracker.get_costs_by_model()
    elif group_by == "user":
        costs = tracker.get_costs_by_user()
    else:
        costs = tracker.get_total_costs()

    return {
        "costs": costs,
        "period": period,
    }


@router.get("/llm/latency")
async def get_llm_latency():
    """Get LLM latency metrics."""
    tracker = LatencyTracker()
    percentiles = tracker.get_percentiles()

    return {
        "percentiles": percentiles.to_dict() if hasattr(percentiles, "to_dict") else percentiles,
    }


# ============================================================
# Agent Observability Endpoints
# ============================================================


@router.get("/agents/traces")
async def list_agent_traces(
    agent_name: Optional[str] = None,
    limit: int = 50,
):
    """List agent execution traces."""
    collector = get_agent_trace_collector()
    traces = collector.list_traces(agent_name=agent_name, limit=limit)

    return {
        "traces": [t.to_dict() for t in traces],
        "total": len(traces),
    }


@router.get("/agents/traces/{trace_id}")
async def get_agent_trace(trace_id: str):
    """Get agent trace details."""
    collector = get_agent_trace_collector()
    trace = collector.get_trace(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace.to_dict()


@router.get("/agents/metrics")
async def get_agent_metrics(
    agent_name: Optional[str] = None,
    period_hours: int = 24,
):
    """Get agent performance metrics."""
    metrics = AgentMetrics()

    if agent_name:
        performance = metrics.get_performance(agent_name, period_hours)
        return performance.to_dict()
    else:
        all_performance = metrics.get_all_agents_performance(period_hours)
        return {
            "agents": [p.to_dict() for p in all_performance],
            "summary": metrics.get_summary(),
        }


# ============================================================
# Templates Endpoints
# ============================================================


@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
):
    """List dashboard templates."""
    manager = get_template_manager()
    templates = manager.list_templates()

    if category:
        templates = [t for t in templates if t.category.value == category]

    return {
        "templates": [t.to_dict() for t in templates],
        "categories": manager.get_categories(),
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get template details."""
    manager = get_template_manager()
    template = manager.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


# ============================================================
# Health & Stats
# ============================================================


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
    }


@router.get("/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    service = get_dashboard_service()
    dashboards = await service.list_dashboards()

    return {
        "dashboards": {
            "total": len(dashboards),
        },
        "timestamp": datetime.now().isoformat(),
    }

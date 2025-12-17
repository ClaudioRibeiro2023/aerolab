"""
Analytics Engine - Analytics e métricas por domínio.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from ..core.types import DomainType

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Tipos de métricas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class EventType(str, Enum):
    """Tipos de eventos."""
    CHAT = "chat"
    WORKFLOW = "workflow"
    RAG_QUERY = "rag_query"
    COMPLIANCE_CHECK = "compliance_check"
    DOCUMENT_PROCESS = "document_process"
    ERROR = "error"


@dataclass
class Metric:
    """Métrica individual."""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AnalyticsEvent:
    """Evento de analytics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CHAT
    domain: Optional[DomainType] = None
    
    # Event data
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Performance
    duration_ms: float = 0.0
    tokens_used: int = 0
    
    # User
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DomainStats:
    """Estatísticas de um domínio."""
    domain: DomainType
    
    # Usage
    total_chats: int = 0
    total_queries: int = 0
    total_workflows: int = 0
    
    # Performance
    avg_response_time_ms: float = 0.0
    avg_tokens_per_request: float = 0.0
    
    # Quality
    avg_confidence: float = 0.0
    compliance_score: float = 100.0
    
    # Agents
    most_used_agents: List[str] = field(default_factory=list)
    
    # Time
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)


@dataclass
class UsageSummary:
    """Resumo de uso geral."""
    # Totals
    total_events: int = 0
    total_users: int = 0
    total_sessions: int = 0
    
    # By domain
    events_by_domain: Dict[str, int] = field(default_factory=dict)
    
    # By type
    events_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Performance
    avg_response_time_ms: float = 0.0
    total_tokens_used: int = 0
    
    # Time series
    events_per_day: Dict[str, int] = field(default_factory=dict)
    
    # Period
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)


class AnalyticsEngine:
    """
    Engine de analytics para Domain Studio.
    
    Features:
    - Event tracking
    - Metrics collection
    - Domain statistics
    - Usage summaries
    - Time series data
    - ROI calculation
    """
    
    def __init__(self):
        self._events: List[AnalyticsEvent] = []
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        
        logger.info("AnalyticsEngine initialized")
    
    # ============================================================
    # EVENT TRACKING
    # ============================================================
    
    async def track_event(
        self,
        event_type: EventType,
        domain: Optional[DomainType] = None,
        action: str = "",
        details: Optional[Dict] = None,
        duration_ms: float = 0.0,
        tokens_used: int = 0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AnalyticsEvent:
        """Track an analytics event."""
        event = AnalyticsEvent(
            type=event_type,
            domain=domain,
            action=action,
            details=details or {},
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            user_id=user_id,
            session_id=session_id
        )
        
        self._events.append(event)
        
        logger.debug("Tracked event: %s/%s", event_type.value, action)
        return event
    
    async def track_chat(
        self,
        domain: DomainType,
        agent: str,
        response_time_ms: float,
        tokens: int,
        confidence: float = 0.0,
        user_id: Optional[str] = None
    ) -> AnalyticsEvent:
        """Track a chat event."""
        return await self.track_event(
            event_type=EventType.CHAT,
            domain=domain,
            action="chat",
            details={
                "agent": agent,
                "confidence": confidence
            },
            duration_ms=response_time_ms,
            tokens_used=tokens,
            user_id=user_id
        )
    
    async def track_workflow(
        self,
        domain: DomainType,
        workflow_name: str,
        status: str,
        duration_ms: float,
        steps_completed: int,
        user_id: Optional[str] = None
    ) -> AnalyticsEvent:
        """Track a workflow event."""
        return await self.track_event(
            event_type=EventType.WORKFLOW,
            domain=domain,
            action=f"workflow_{status}",
            details={
                "workflow": workflow_name,
                "status": status,
                "steps_completed": steps_completed
            },
            duration_ms=duration_ms,
            user_id=user_id
        )
    
    async def track_error(
        self,
        domain: Optional[DomainType],
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None
    ) -> AnalyticsEvent:
        """Track an error event."""
        return await self.track_event(
            event_type=EventType.ERROR,
            domain=domain,
            action=error_type,
            details={
                "message": error_message,
                "context": context or {}
            }
        )
    
    # ============================================================
    # METRICS
    # ============================================================
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Record a metric."""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {}
        )
        
        self._metrics[name].append(metric)
        
        return metric
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Increment a counter metric."""
        return self.record_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Set a gauge metric."""
        return self.record_metric(name, value, MetricType.GAUGE, labels)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    async def get_domain_stats(
        self,
        domain: DomainType,
        period_days: int = 30
    ) -> DomainStats:
        """Get statistics for a domain."""
        period_start = datetime.now() - timedelta(days=period_days)
        
        # Filter events for domain and period
        domain_events = [
            e for e in self._events
            if e.domain == domain and e.timestamp >= period_start
        ]
        
        # Calculate stats
        chats = [e for e in domain_events if e.type == EventType.CHAT]
        queries = [e for e in domain_events if e.type == EventType.RAG_QUERY]
        workflows = [e for e in domain_events if e.type == EventType.WORKFLOW]
        
        # Response times
        response_times = [e.duration_ms for e in domain_events if e.duration_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Tokens
        tokens = [e.tokens_used for e in domain_events if e.tokens_used > 0]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0
        
        # Confidence
        confidences = [
            e.details.get("confidence", 0) 
            for e in chats 
            if "confidence" in e.details
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Most used agents
        agent_counts = defaultdict(int)
        for e in chats:
            agent = e.details.get("agent")
            if agent:
                agent_counts[agent] += 1
        most_used = sorted(agent_counts.keys(), key=lambda a: agent_counts[a], reverse=True)[:5]
        
        return DomainStats(
            domain=domain,
            total_chats=len(chats),
            total_queries=len(queries),
            total_workflows=len(workflows),
            avg_response_time_ms=avg_response_time,
            avg_tokens_per_request=avg_tokens,
            avg_confidence=avg_confidence,
            most_used_agents=most_used,
            period_start=period_start,
            period_end=datetime.now()
        )
    
    async def get_usage_summary(
        self,
        period_days: int = 30
    ) -> UsageSummary:
        """Get overall usage summary."""
        period_start = datetime.now() - timedelta(days=period_days)
        
        # Filter events
        recent_events = [e for e in self._events if e.timestamp >= period_start]
        
        # By domain
        events_by_domain = defaultdict(int)
        for e in recent_events:
            if e.domain:
                events_by_domain[e.domain.value] += 1
        
        # By type
        events_by_type = defaultdict(int)
        for e in recent_events:
            events_by_type[e.type.value] += 1
        
        # Users and sessions
        users = set(e.user_id for e in recent_events if e.user_id)
        sessions = set(e.session_id for e in recent_events if e.session_id)
        
        # Performance
        response_times = [e.duration_ms for e in recent_events if e.duration_ms > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        total_tokens = sum(e.tokens_used for e in recent_events)
        
        # Events per day
        events_per_day = defaultdict(int)
        for e in recent_events:
            day = e.timestamp.strftime("%Y-%m-%d")
            events_per_day[day] += 1
        
        return UsageSummary(
            total_events=len(recent_events),
            total_users=len(users),
            total_sessions=len(sessions),
            events_by_domain=dict(events_by_domain),
            events_by_type=dict(events_by_type),
            avg_response_time_ms=avg_response_time,
            total_tokens_used=total_tokens,
            events_per_day=dict(events_per_day),
            period_start=period_start,
            period_end=datetime.now()
        )
    
    # ============================================================
    # ROI CALCULATION
    # ============================================================
    
    async def calculate_roi(
        self,
        domain: DomainType,
        period_days: int = 30,
        cost_per_token: float = 0.00001,
        time_saved_per_task_minutes: float = 30,
        hourly_rate: float = 50.0
    ) -> Dict[str, Any]:
        """Calculate ROI for a domain."""
        stats = await self.get_domain_stats(domain, period_days)
        
        # Costs
        tokens_used = stats.avg_tokens_per_request * (
            stats.total_chats + stats.total_queries
        )
        token_cost = tokens_used * cost_per_token
        
        # Time saved
        tasks_completed = stats.total_chats + stats.total_workflows
        time_saved_hours = (tasks_completed * time_saved_per_task_minutes) / 60
        value_generated = time_saved_hours * hourly_rate
        
        # ROI
        roi = ((value_generated - token_cost) / max(token_cost, 0.01)) * 100
        
        return {
            "domain": domain.value,
            "period_days": period_days,
            "tasks_completed": tasks_completed,
            "tokens_used": int(tokens_used),
            "token_cost_usd": round(token_cost, 2),
            "time_saved_hours": round(time_saved_hours, 1),
            "value_generated_usd": round(value_generated, 2),
            "roi_percent": round(roi, 1),
            "stats": {
                "total_chats": stats.total_chats,
                "total_workflows": stats.total_workflows,
                "avg_response_time_ms": round(stats.avg_response_time_ms, 0)
            }
        }
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_events(
        self,
        format: str = "json",
        period_days: Optional[int] = None
    ) -> Any:
        """Export events."""
        events = self._events
        if period_days:
            cutoff = datetime.now() - timedelta(days=period_days)
            events = [e for e in events if e.timestamp >= cutoff]
        
        if format == "json":
            return [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "domain": e.domain.value if e.domain else None,
                    "action": e.action,
                    "duration_ms": e.duration_ms,
                    "tokens_used": e.tokens_used,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in events
            ]
        
        return events


# ============================================================
# FACTORY
# ============================================================

_engine: Optional[AnalyticsEngine] = None

def get_analytics_engine() -> AnalyticsEngine:
    """Get singleton analytics engine."""
    global _engine
    if _engine is None:
        _engine = AnalyticsEngine()
    return _engine

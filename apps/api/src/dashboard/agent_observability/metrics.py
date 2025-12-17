"""
Agent Metrics - Métricas de performance de agentes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformance:
    """Performance de um agente."""
    agent_name: str = ""
    
    # Volume
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    # Success rate
    success_rate: float = 0.0
    
    # Latency
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    
    # Tokens
    total_tokens: int = 0
    avg_tokens_per_execution: float = 0.0
    
    # Costs
    total_cost_usd: float = 0.0
    avg_cost_per_execution: float = 0.0
    
    # Tool usage
    total_tool_calls: int = 0
    avg_tool_calls_per_execution: float = 0.0
    tool_usage: Dict[str, int] = field(default_factory=dict)
    
    # LLM calls
    total_llm_calls: int = 0
    avg_llm_calls_per_execution: float = 0.0
    
    # Time period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "agentName": self.agent_name,
            "totalExecutions": self.total_executions,
            "successfulExecutions": self.successful_executions,
            "failedExecutions": self.failed_executions,
            "successRate": round(self.success_rate, 4),
            "avgLatencyMs": round(self.avg_latency_ms, 2),
            "p50LatencyMs": round(self.p50_latency_ms, 2),
            "p95LatencyMs": round(self.p95_latency_ms, 2),
            "p99LatencyMs": round(self.p99_latency_ms, 2),
            "minLatencyMs": round(self.min_latency_ms, 2),
            "maxLatencyMs": round(self.max_latency_ms, 2),
            "totalTokens": self.total_tokens,
            "avgTokensPerExecution": round(self.avg_tokens_per_execution, 2),
            "totalCostUsd": round(self.total_cost_usd, 4),
            "avgCostPerExecution": round(self.avg_cost_per_execution, 6),
            "totalToolCalls": self.total_tool_calls,
            "avgToolCallsPerExecution": round(self.avg_tool_calls_per_execution, 2),
            "toolUsage": self.tool_usage,
            "totalLlmCalls": self.total_llm_calls,
            "avgLlmCallsPerExecution": round(self.avg_llm_calls_per_execution, 2),
            "periodStart": self.period_start.isoformat() if self.period_start else None,
            "periodEnd": self.period_end.isoformat() if self.period_end else None,
        }


@dataclass
class ExecutionRecord:
    """Registro de execução para cálculo de métricas."""
    agent_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    tokens: int
    cost_usd: float
    tool_calls: int
    llm_calls: int
    tools_used: List[str] = field(default_factory=list)
    error: Optional[str] = None


class AgentMetrics:
    """
    Coletor de métricas de agentes.
    
    Rastreia e agrega métricas de performance de agentes.
    """
    
    def __init__(self, retention_hours: int = 168):  # 7 dias
        self._executions: List[ExecutionRecord] = []
        self._retention = timedelta(hours=retention_hours)
    
    def record_execution(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        tokens: int = 0,
        cost_usd: float = 0.0,
        tool_calls: int = 0,
        llm_calls: int = 0,
        tools_used: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        """Registra uma execução de agente."""
        record = ExecutionRecord(
            agent_name=agent_name,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            tokens=tokens,
            cost_usd=cost_usd,
            tool_calls=tool_calls,
            llm_calls=llm_calls,
            tools_used=tools_used or [],
            error=error,
        )
        
        self._executions.append(record)
        self._cleanup_old_records()
    
    def _cleanup_old_records(self):
        """Remove registros antigos."""
        cutoff = datetime.now() - self._retention
        self._executions = [
            e for e in self._executions
            if e.timestamp > cutoff
        ]
    
    def get_performance(
        self,
        agent_name: str,
        period_hours: int = 24,
    ) -> AgentPerformance:
        """Obtém métricas de performance de um agente."""
        cutoff = datetime.now() - timedelta(hours=period_hours)
        
        executions = [
            e for e in self._executions
            if e.agent_name == agent_name and e.timestamp > cutoff
        ]
        
        if not executions:
            return AgentPerformance(agent_name=agent_name)
        
        # Calcular métricas
        latencies = [e.duration_ms for e in executions]
        successful = [e for e in executions if e.success]
        
        # Tool usage
        tool_usage = defaultdict(int)
        for e in executions:
            for tool in e.tools_used:
                tool_usage[tool] += 1
        
        return AgentPerformance(
            agent_name=agent_name,
            total_executions=len(executions),
            successful_executions=len(successful),
            failed_executions=len(executions) - len(successful),
            success_rate=len(successful) / len(executions),
            avg_latency_ms=statistics.mean(latencies),
            p50_latency_ms=self._percentile(latencies, 50),
            p95_latency_ms=self._percentile(latencies, 95),
            p99_latency_ms=self._percentile(latencies, 99),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            total_tokens=sum(e.tokens for e in executions),
            avg_tokens_per_execution=sum(e.tokens for e in executions) / len(executions),
            total_cost_usd=sum(e.cost_usd for e in executions),
            avg_cost_per_execution=sum(e.cost_usd for e in executions) / len(executions),
            total_tool_calls=sum(e.tool_calls for e in executions),
            avg_tool_calls_per_execution=sum(e.tool_calls for e in executions) / len(executions),
            tool_usage=dict(tool_usage),
            total_llm_calls=sum(e.llm_calls for e in executions),
            avg_llm_calls_per_execution=sum(e.llm_calls for e in executions) / len(executions),
            period_start=cutoff,
            period_end=datetime.now(),
        )
    
    def get_all_agents_performance(
        self,
        period_hours: int = 24,
    ) -> List[AgentPerformance]:
        """Obtém performance de todos os agentes."""
        agent_names = set(e.agent_name for e in self._executions)
        return [
            self.get_performance(name, period_hours)
            for name in agent_names
        ]
    
    def get_top_agents(
        self,
        metric: str = "total_executions",
        limit: int = 10,
        period_hours: int = 24,
    ) -> List[AgentPerformance]:
        """Obtém top agentes por métrica."""
        performances = self.get_all_agents_performance(period_hours)
        
        # Ordenar por métrica
        reverse = metric not in ["avg_latency_ms", "p95_latency_ms", "failed_executions"]
        
        return sorted(
            performances,
            key=lambda p: getattr(p, metric, 0),
            reverse=reverse
        )[:limit]
    
    def get_error_analysis(
        self,
        agent_name: Optional[str] = None,
        period_hours: int = 24,
    ) -> Dict[str, Any]:
        """Análise de erros."""
        cutoff = datetime.now() - timedelta(hours=period_hours)
        
        executions = [
            e for e in self._executions
            if e.timestamp > cutoff and not e.success
        ]
        
        if agent_name:
            executions = [e for e in executions if e.agent_name == agent_name]
        
        # Agrupar erros
        error_counts = defaultdict(int)
        error_by_agent = defaultdict(int)
        
        for e in executions:
            error_key = e.error or "Unknown error"
            error_counts[error_key] += 1
            error_by_agent[e.agent_name] += 1
        
        return {
            "totalErrors": len(executions),
            "errorTypes": dict(error_counts),
            "errorsByAgent": dict(error_by_agent),
            "topErrors": sorted(
                error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }
    
    def get_time_series(
        self,
        agent_name: str,
        metric: str = "count",
        interval_minutes: int = 60,
        period_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Obtém série temporal de métricas."""
        cutoff = datetime.now() - timedelta(hours=period_hours)
        
        executions = [
            e for e in self._executions
            if e.agent_name == agent_name and e.timestamp > cutoff
        ]
        
        # Agrupar por intervalo
        interval = timedelta(minutes=interval_minutes)
        buckets = defaultdict(list)
        
        for e in executions:
            bucket_time = e.timestamp.replace(
                minute=(e.timestamp.minute // interval_minutes) * interval_minutes,
                second=0,
                microsecond=0
            )
            buckets[bucket_time].append(e)
        
        # Calcular métrica por bucket
        series = []
        current = cutoff.replace(minute=0, second=0, microsecond=0)
        
        while current <= datetime.now():
            bucket_executions = buckets.get(current, [])
            
            if metric == "count":
                value = len(bucket_executions)
            elif metric == "success_rate":
                value = (
                    len([e for e in bucket_executions if e.success]) / len(bucket_executions)
                    if bucket_executions else 0
                )
            elif metric == "avg_latency":
                value = (
                    statistics.mean(e.duration_ms for e in bucket_executions)
                    if bucket_executions else 0
                )
            elif metric == "total_tokens":
                value = sum(e.tokens for e in bucket_executions)
            elif metric == "total_cost":
                value = sum(e.cost_usd for e in bucket_executions)
            else:
                value = 0
            
            series.append({
                "timestamp": current.isoformat(),
                "value": value,
            })
            
            current += interval
        
        return series
    
    def _percentile(self, data: List[float], p: float) -> float:
        """Calcula percentil."""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        
        if f == c:
            return sorted_data[int(k)]
        
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)
    
    def get_summary(self) -> Dict[str, Any]:
        """Resumo geral de métricas."""
        now = datetime.now()
        last_24h = [
            e for e in self._executions
            if e.timestamp > now - timedelta(hours=24)
        ]
        
        agent_names = set(e.agent_name for e in last_24h)
        
        return {
            "totalExecutions24h": len(last_24h),
            "uniqueAgents": len(agent_names),
            "successRate": (
                len([e for e in last_24h if e.success]) / len(last_24h)
                if last_24h else 0
            ),
            "totalTokens24h": sum(e.tokens for e in last_24h),
            "totalCost24h": sum(e.cost_usd for e in last_24h),
            "avgLatencyMs": (
                statistics.mean(e.duration_ms for e in last_24h)
                if last_24h else 0
            ),
        }


# Singleton
_metrics: Optional[AgentMetrics] = None


def get_agent_metrics() -> AgentMetrics:
    """Obtém métricas de agentes."""
    global _metrics
    if _metrics is None:
        _metrics = AgentMetrics()
    return _metrics

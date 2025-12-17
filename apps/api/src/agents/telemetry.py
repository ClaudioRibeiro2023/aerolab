"""
Sistema de Telemetria para Agentes.

Rastreia métricas de performance, custos e qualidade de agentes.

Features:
- Rastreamento de latência por step (model, tool, RAG)
- Contagem de tokens (input, output, cache)
- Custos por execução e acumulados
- Success rate por modelo e ferramenta
- Histórico de execuções
- Export para sistemas externos (Prometheus, DataDog)

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Telemetry System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Metrics      │  │ Traces       │  │ Logs         │      │
│  │ Collector    │  │ Collector    │  │ Collector    │      │
│  │              │  │              │  │              │      │
│  │ - Counters   │  │ - Spans      │  │ - Events     │      │
│  │ - Gauges     │  │ - Context    │  │ - Errors     │      │
│  │ - Histograms │  │ - Timing     │  │ - Debug      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │ Exporter  │                            │
│                    │           │                            │
│                    │ - Console │                            │
│                    │ - File    │                            │
│                    │ - Remote  │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from contextlib import contextmanager
from enum import Enum
import statistics
import sqlite3


class MetricType(Enum):
    """Tipos de métrica."""
    COUNTER = "counter"      # Sempre incrementa
    GAUGE = "gauge"          # Valor atual
    HISTOGRAM = "histogram"  # Distribuição


class SpanType(Enum):
    """Tipos de span para tracing."""
    AGENT_RUN = "agent_run"
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    RAG_RETRIEVAL = "rag_retrieval"
    PLANNING = "planning"
    MEMORY_ACCESS = "memory_access"


@dataclass
class Metric:
    """Métrica individual."""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Span:
    """Span para tracing distribuído."""
    trace_id: str
    span_id: str
    name: str
    span_type: SpanType
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    parent_span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"  # ok, error
    error_message: Optional[str] = None
    
    def finish(self, status: str = "ok", error: Optional[str] = None):
        """Finaliza o span."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        self.error_message = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "type": self.span_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "parent_span_id": self.parent_span_id,
            "attributes": self.attributes,
            "status": self.status,
            "error": self.error_message
        }


@dataclass
class ExecutionStats:
    """Estatísticas de execução."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    latencies: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)
    
    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return statistics.median(self.latencies)
    
    @property
    def p95_latency_ms(self) -> float:
        if len(self.latencies) < 2:
            return self.avg_latency_ms
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx]
    
    @property
    def p99_latency_ms(self) -> float:
        if len(self.latencies) < 2:
            return self.avg_latency_ms
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[idx]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.success_rate,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_cost_usd": self.total_cost_usd,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms
        }


class MetricsCollector:
    """
    Coletor de métricas.
    
    Coleta e agrega métricas de performance.
    """
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._metrics: List[Metric] = []
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: float = 1, labels: Optional[Dict] = None):
        """Incrementa um counter."""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value
            self._add_metric(Metric(
                name=name,
                value=self._counters[key],
                metric_type=MetricType.COUNTER,
                labels=labels or {}
            ))
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None):
        """Define um gauge."""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
            self._add_metric(Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                labels=labels or {}
            ))
    
    def observe(self, name: str, value: float, labels: Optional[Dict] = None):
        """Observa um valor para histogram."""
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            
            # Limitar tamanho
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            
            self._add_metric(Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                labels=labels or {}
            ))
    
    def _make_key(self, name: str, labels: Optional[Dict]) -> str:
        """Cria chave única para métrica."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_metric(self, metric: Metric):
        """Adiciona métrica ao histórico."""
        self._metrics.append(metric)
        if len(self._metrics) > self.max_history:
            self._metrics = self._metrics[-self.max_history:]
    
    def get_counter(self, name: str, labels: Optional[Dict] = None) -> float:
        """Obtém valor de counter."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Optional[Dict] = None) -> float:
        """Obtém valor de gauge."""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict] = None) -> Dict[str, float]:
        """Obtém estatísticas de histogram."""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        
        if not values:
            return {"count": 0, "mean": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "p50": statistics.median(values),
            "p95": sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 1 else sorted_values[-1],
            "p99": sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 1 else sorted_values[-1]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Retorna todas as métricas."""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {k: self.get_histogram_stats(k) for k in self._histograms}
        }


class TraceCollector:
    """
    Coletor de traces.
    
    Gerencia spans para rastreamento distribuído.
    """
    
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: Dict[str, List[Span]] = {}
        self._active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
    
    def _generate_id(self) -> str:
        """Gera ID único."""
        import uuid
        return uuid.uuid4().hex[:16]
    
    def start_trace(self, name: str = "agent_run") -> str:
        """Inicia um novo trace."""
        trace_id = self._generate_id()
        with self._lock:
            self._traces[trace_id] = []
        return trace_id
    
    def start_span(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> Span:
        """Inicia um novo span."""
        span = Span(
            trace_id=trace_id,
            span_id=self._generate_id(),
            name=name,
            span_type=span_type,
            parent_span_id=parent_span_id,
            attributes=attributes or {}
        )
        
        with self._lock:
            self._active_spans[span.span_id] = span
            if trace_id in self._traces:
                self._traces[trace_id].append(span)
        
        return span
    
    def end_span(self, span: Span, status: str = "ok", error: Optional[str] = None):
        """Finaliza um span."""
        span.finish(status, error)
        with self._lock:
            if span.span_id in self._active_spans:
                del self._active_spans[span.span_id]
    
    @contextmanager
    def span_context(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict] = None
    ):
        """Context manager para spans."""
        span = self.start_span(trace_id, name, span_type, parent_span_id, attributes)
        try:
            yield span
            self.end_span(span, "ok")
        except Exception as e:
            self.end_span(span, "error", str(e))
            raise
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Obtém todos os spans de um trace."""
        return self._traces.get(trace_id, [])
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Retorna resumo de um trace."""
        spans = self.get_trace(trace_id)
        if not spans:
            return {}
        
        total_duration = sum(s.duration_ms for s in spans)
        by_type = {}
        for span in spans:
            if span.span_type.value not in by_type:
                by_type[span.span_type.value] = {"count": 0, "duration_ms": 0}
            by_type[span.span_type.value]["count"] += 1
            by_type[span.span_type.value]["duration_ms"] += span.duration_ms
        
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "total_duration_ms": total_duration,
            "by_type": by_type,
            "has_errors": any(s.status == "error" for s in spans)
        }


class AgentTelemetry:
    """
    Sistema completo de telemetria para agentes.
    
    Exemplo:
        telemetry = AgentTelemetry(agent_id="researcher")
        
        # Iniciar rastreamento
        trace_id = telemetry.start_execution()
        
        # Rastrear chamada de modelo
        with telemetry.track_model_call(trace_id, "gpt-4o") as span:
            response = await model.generate(...)
            span.attributes["tokens_in"] = response.usage.input
            span.attributes["tokens_out"] = response.usage.output
        
        # Finalizar
        telemetry.end_execution(trace_id, success=True, tokens_in=100, tokens_out=50, cost=0.01)
        
        # Obter estatísticas
        stats = telemetry.get_stats()
    """
    
    def __init__(
        self,
        agent_id: str = "default",
        enable_persistence: bool = False,
        db_path: str = "./data/telemetry"
    ):
        self.agent_id = agent_id
        self.enable_persistence = enable_persistence
        self.db_path = Path(db_path)
        
        self.metrics = MetricsCollector()
        self.traces = TraceCollector()
        
        self._stats = ExecutionStats()
        self._model_stats: Dict[str, ExecutionStats] = {}
        self._tool_stats: Dict[str, ExecutionStats] = {}
        
        if enable_persistence:
            self._init_db()
    
    def _init_db(self):
        """Inicializa banco para persistência."""
        self.db_path.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path / "telemetry.db") as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    trace_id TEXT,
                    success INTEGER,
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    cost_usd REAL,
                    latency_ms REAL,
                    timestamp TEXT,
                    metadata TEXT
                )
            """)
    
    def start_execution(self) -> str:
        """Inicia rastreamento de uma execução."""
        trace_id = self.traces.start_trace("agent_run")
        self.metrics.increment("agent_executions_total", labels={"agent_id": self.agent_id})
        return trace_id
    
    def end_execution(
        self,
        trace_id: str,
        success: bool = True,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: float = 0.0,
        latency_ms: Optional[float] = None
    ):
        """Finaliza rastreamento de execução."""
        # Calcular latência do trace se não fornecida
        if latency_ms is None:
            spans = self.traces.get_trace(trace_id)
            latency_ms = sum(s.duration_ms for s in spans)
        
        # Atualizar estatísticas
        self._stats.total_executions += 1
        if success:
            self._stats.successful_executions += 1
        else:
            self._stats.failed_executions += 1
        
        self._stats.total_tokens_input += tokens_in
        self._stats.total_tokens_output += tokens_out
        self._stats.total_cost_usd += cost
        self._stats.latencies.append(latency_ms)
        
        # Limitar histórico de latências
        if len(self._stats.latencies) > 10000:
            self._stats.latencies = self._stats.latencies[-10000:]
        
        # Métricas
        self.metrics.increment(
            "agent_executions_success" if success else "agent_executions_failed",
            labels={"agent_id": self.agent_id}
        )
        self.metrics.increment("agent_tokens_input_total", tokens_in, {"agent_id": self.agent_id})
        self.metrics.increment("agent_tokens_output_total", tokens_out, {"agent_id": self.agent_id})
        self.metrics.increment("agent_cost_usd_total", cost, {"agent_id": self.agent_id})
        self.metrics.observe("agent_latency_ms", latency_ms, {"agent_id": self.agent_id})
        
        # Persistir se habilitado
        if self.enable_persistence:
            self._persist_execution(trace_id, success, tokens_in, tokens_out, cost, latency_ms)
    
    def _persist_execution(
        self,
        trace_id: str,
        success: bool,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        latency_ms: float
    ):
        """Persiste execução no banco."""
        import uuid
        with sqlite3.connect(self.db_path / "telemetry.db") as conn:
            conn.execute("""
                INSERT INTO executions 
                (id, agent_id, trace_id, success, tokens_in, tokens_out, cost_usd, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uuid.uuid4().hex[:12],
                self.agent_id,
                trace_id,
                1 if success else 0,
                tokens_in,
                tokens_out,
                cost,
                latency_ms,
                datetime.now().isoformat()
            ))
    
    @contextmanager
    def track_model_call(
        self,
        trace_id: str,
        model_id: str,
        parent_span_id: Optional[str] = None
    ):
        """Context manager para rastrear chamada de modelo."""
        with self.traces.span_context(
            trace_id,
            f"model_call:{model_id}",
            SpanType.MODEL_CALL,
            parent_span_id,
            {"model_id": model_id}
        ) as span:
            start = time.time()
            try:
                yield span
                latency = (time.time() - start) * 1000
                
                # Atualizar stats do modelo
                if model_id not in self._model_stats:
                    self._model_stats[model_id] = ExecutionStats()
                
                stats = self._model_stats[model_id]
                stats.total_executions += 1
                stats.successful_executions += 1
                stats.latencies.append(latency)
                
                self.metrics.observe("model_latency_ms", latency, {"model_id": model_id})
                self.metrics.increment("model_calls_total", labels={"model_id": model_id})
                
            except Exception:
                if model_id in self._model_stats:
                    self._model_stats[model_id].failed_executions += 1
                self.metrics.increment("model_errors_total", labels={"model_id": model_id})
                raise
    
    @contextmanager
    def track_tool_call(
        self,
        trace_id: str,
        tool_name: str,
        parent_span_id: Optional[str] = None
    ):
        """Context manager para rastrear chamada de ferramenta."""
        with self.traces.span_context(
            trace_id,
            f"tool_call:{tool_name}",
            SpanType.TOOL_CALL,
            parent_span_id,
            {"tool_name": tool_name}
        ) as span:
            start = time.time()
            try:
                yield span
                latency = (time.time() - start) * 1000
                
                # Atualizar stats da ferramenta
                if tool_name not in self._tool_stats:
                    self._tool_stats[tool_name] = ExecutionStats()
                
                stats = self._tool_stats[tool_name]
                stats.total_executions += 1
                stats.successful_executions += 1
                stats.latencies.append(latency)
                
                self.metrics.observe("tool_latency_ms", latency, {"tool_name": tool_name})
                self.metrics.increment("tool_calls_total", labels={"tool_name": tool_name})
                
            except Exception:
                if tool_name in self._tool_stats:
                    self._tool_stats[tool_name].failed_executions += 1
                self.metrics.increment("tool_errors_total", labels={"tool_name": tool_name})
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas."""
        return {
            "agent_id": self.agent_id,
            "overall": self._stats.to_dict(),
            "by_model": {k: v.to_dict() for k, v in self._model_stats.items()},
            "by_tool": {k: v.to_dict() for k, v in self._tool_stats.items()}
        }
    
    def get_cost_summary(self, period_days: int = 30) -> Dict[str, Any]:
        """Retorna resumo de custos."""
        return {
            "total_cost_usd": self._stats.total_cost_usd,
            "total_tokens": self._stats.total_tokens_input + self._stats.total_tokens_output,
            "avg_cost_per_execution": self._stats.total_cost_usd / max(self._stats.total_executions, 1),
            "by_model": {
                model_id: stats.total_cost_usd
                for model_id, stats in self._model_stats.items()
            }
        }
    
    def reset_stats(self):
        """Reseta estatísticas."""
        self._stats = ExecutionStats()
        self._model_stats.clear()
        self._tool_stats.clear()


# Factory
def create_telemetry(
    agent_id: str,
    enable_persistence: bool = False
) -> AgentTelemetry:
    """Cria instância de telemetria."""
    return AgentTelemetry(
        agent_id=agent_id,
        enable_persistence=enable_persistence
    )


# Global registry
_telemetry_instances: Dict[str, AgentTelemetry] = {}


def get_telemetry(agent_id: str) -> AgentTelemetry:
    """Obtém ou cria telemetria para um agente."""
    if agent_id not in _telemetry_instances:
        _telemetry_instances[agent_id] = AgentTelemetry(agent_id)
    return _telemetry_instances[agent_id]

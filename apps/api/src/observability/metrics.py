"""
Sistema de métricas Prometheus para AgentOS.

Fornece:
- Contadores de requisições
- Histogramas de latência
- Gauges de estado do sistema
- Endpoint /metrics compatível com Prometheus
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class MetricValue:
    """Valor de uma métrica."""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Contador monotônico crescente."""
    
    def __init__(self, name: str, description: str, labels: list = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, value: float = 1.0, **labels):
        """Incrementa o contador."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] += value
    
    def get(self, **labels) -> float:
        """Obtém valor atual."""
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0.0)
    
    def collect(self) -> list:
        """Coleta todos os valores para export."""
        result = []
        with self._lock:
            for labels_tuple, value in self._values.items():
                labels = dict(labels_tuple)
                result.append(MetricValue(value=value, labels=labels))
        return result


class Gauge:
    """Valor que pode subir ou descer."""
    
    def __init__(self, name: str, description: str, labels: list = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
        self._lock = threading.Lock()
    
    def set(self, value: float, **labels):
        """Define o valor."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = value
    
    def inc(self, value: float = 1.0, **labels):
        """Incrementa o valor."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value
    
    def dec(self, value: float = 1.0, **labels):
        """Decrementa o valor."""
        self.inc(-value, **labels)
    
    def get(self, **labels) -> float:
        """Obtém valor atual."""
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0.0)
    
    def collect(self) -> list:
        """Coleta todos os valores."""
        result = []
        with self._lock:
            for labels_tuple, value in self._values.items():
                labels = dict(labels_tuple)
                result.append(MetricValue(value=value, labels=labels))
        return result


class Histogram:
    """Histograma para medir distribuições."""
    
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    
    def __init__(self, name: str, description: str, labels: list = None, buckets: tuple = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._totals: Dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def observe(self, value: float, **labels):
        """Registra uma observação."""
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._sums[key] += value
            self._totals[key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[key][bucket] += 1
    
    def collect(self) -> Dict[str, Any]:
        """Coleta estatísticas."""
        result = {}
        with self._lock:
            for key in self._totals.keys():
                labels = dict(key)
                label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                prefix = f"{self.name}{{{label_str}}}" if labels else self.name
                
                result[f"{prefix}_count"] = self._totals[key]
                result[f"{prefix}_sum"] = self._sums[key]
                
                for bucket in self.buckets:
                    result[f"{prefix}_bucket{{le=\"{bucket}\"}}"] = self._counts[key].get(bucket, 0)
                result[f"{prefix}_bucket{{le=\"+Inf\"}}"] = self._totals[key]
        
        return result


class MetricsRegistry:
    """Registry central de métricas."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register(self, metric):
        """Registra uma métrica."""
        self._metrics[metric.name] = metric
        return metric
    
    def get(self, name: str):
        """Obtém uma métrica pelo nome."""
        return self._metrics.get(name)
    
    def collect_all(self) -> str:
        """Coleta todas as métricas em formato Prometheus."""
        lines = []
        
        for name, metric in self._metrics.items():
            # Tipo da métrica
            metric_type = "counter" if isinstance(metric, Counter) else \
                         "gauge" if isinstance(metric, Gauge) else "histogram"
            
            lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {metric_type}")
            
            if isinstance(metric, Histogram):
                for key, value in metric.collect().items():
                    lines.append(f"{key} {value}")
            else:
                for mv in metric.collect():
                    if mv.labels:
                        label_str = ",".join(f'{k}="{v}"' for k, v in mv.labels.items())
                        lines.append(f"{name}{{{label_str}}} {mv.value}")
                    else:
                        lines.append(f"{name} {mv.value}")
            
            lines.append("")
        
        return "\n".join(lines)


# Registry global
registry = MetricsRegistry()

# Métricas padrão do AgentOS
REQUEST_COUNT = registry.register(Counter(
    "agentos_requests_total",
    "Total de requisições HTTP",
    labels=["method", "endpoint", "status"]
))

REQUEST_LATENCY = registry.register(Histogram(
    "agentos_request_duration_seconds",
    "Latência das requisições HTTP",
    labels=["method", "endpoint"]
))

AGENT_EXECUTIONS = registry.register(Counter(
    "agentos_agent_executions_total",
    "Total de execuções de agentes",
    labels=["agent_name", "status"]
))

AGENT_EXECUTION_DURATION = registry.register(Histogram(
    "agentos_agent_execution_seconds",
    "Duração das execuções de agentes",
    labels=["agent_name"]
))

ACTIVE_AGENTS = registry.register(Gauge(
    "agentos_active_agents",
    "Número de agentes ativos"
))

TOKENS_USED = registry.register(Counter(
    "agentos_tokens_total",
    "Total de tokens utilizados",
    labels=["agent_name", "model"]
))

CACHE_HITS = registry.register(Counter(
    "agentos_cache_hits_total",
    "Total de cache hits",
    labels=["cache_type"]
))

CACHE_MISSES = registry.register(Counter(
    "agentos_cache_misses_total",
    "Total de cache misses",
    labels=["cache_type"]
))

ERRORS = registry.register(Counter(
    "agentos_errors_total",
    "Total de erros",
    labels=["type", "source"]
))


def get_metrics_text() -> str:
    """Retorna métricas em formato texto Prometheus."""
    return registry.collect_all()


def track_request(method: str, endpoint: str, status: int, duration: float):
    """Rastreia uma requisição HTTP."""
    REQUEST_COUNT.inc(method=method, endpoint=endpoint, status=str(status))
    REQUEST_LATENCY.observe(duration, method=method, endpoint=endpoint)


def track_agent_execution(agent_name: str, success: bool, duration: float, tokens: int = 0, model: str = "unknown"):
    """Rastreia execução de um agente."""
    status = "success" if success else "error"
    AGENT_EXECUTIONS.inc(agent_name=agent_name, status=status)
    AGENT_EXECUTION_DURATION.observe(duration, agent_name=agent_name)
    if tokens > 0:
        TOKENS_USED.inc(tokens, agent_name=agent_name, model=model)


def track_error(error_type: str, source: str):
    """Rastreia um erro."""
    ERRORS.inc(type=error_type, source=source)


def set_active_agents(count: int):
    """Define número de agentes ativos."""
    ACTIVE_AGENTS.set(count)

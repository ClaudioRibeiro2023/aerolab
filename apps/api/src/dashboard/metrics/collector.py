"""
Metric Collector - Coleta unificada de métricas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import uuid
import threading
import logging

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Tipos de métricas."""
    COUNTER = "counter"      # Sempre cresce
    GAUGE = "gauge"          # Pode subir/descer
    HISTOGRAM = "histogram"  # Distribuição
    SUMMARY = "summary"      # Percentis


@dataclass
class MetricLabel:
    """Label de métrica."""
    name: str
    value: str


@dataclass
class MetricPoint:
    """Ponto de dados de uma métrica."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Definição de uma métrica."""
    name: str
    type: MetricType
    description: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    
    # Dados
    points: List[MetricPoint] = field(default_factory=list)
    
    # Limites
    max_points: int = 10000
    
    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Registra um valor."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
        
        # Manter limite
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points:]
    
    def get_latest(self, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Obtém valor mais recente."""
        if not self.points:
            return None
        
        if labels:
            # Filtrar por labels
            matching = [
                p for p in reversed(self.points)
                if all(p.labels.get(k) == v for k, v in labels.items())
            ]
            return matching[0].value if matching else None
        
        return self.points[-1].value
    
    def get_series(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """Obtém série temporal."""
        points = self.points
        
        if start:
            points = [p for p in points if p.timestamp >= start]
        if end:
            points = [p for p in points if p.timestamp <= end]
        if labels:
            points = [
                p for p in points
                if all(p.labels.get(k) == v for k, v in labels.items())
            ]
        
        return points
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "unit": self.unit,
            "labels": self.labels,
            "pointCount": len(self.points),
            "latestValue": self.get_latest(),
        }


class MetricCollector:
    """
    Coletor central de métricas.
    
    Responsável por:
    - Registrar métricas
    - Coletar de múltiplas fontes
    - Agregar dados
    """
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._collectors: List[Callable] = []
        self._lock = threading.RLock()
    
    def register(
        self,
        name: str,
        type: MetricType,
        description: str = "",
        unit: str = "",
        labels: List[str] = None
    ) -> Metric:
        """Registra uma nova métrica."""
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            metric = Metric(
                name=name,
                type=type,
                description=description,
                unit=unit,
                labels=labels or []
            )
            self._metrics[name] = metric
            return metric
    
    def record(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Registra valor de uma métrica."""
        with self._lock:
            metric = self._metrics.get(name)
            if metric:
                metric.record(value, labels)
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Incrementa counter."""
        with self._lock:
            metric = self._metrics.get(name)
            if metric and metric.type == MetricType.COUNTER:
                current = metric.get_latest(labels) or 0
                metric.record(current + value, labels)
    
    def get(self, name: str) -> Optional[Metric]:
        """Obtém métrica por nome."""
        return self._metrics.get(name)
    
    def get_all(self) -> List[Metric]:
        """Lista todas as métricas."""
        return list(self._metrics.values())
    
    def get_value(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Obtém valor de uma métrica."""
        metric = self._metrics.get(name)
        if metric:
            return metric.get_latest(labels)
        return None
    
    def get_series(
        self,
        name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricPoint]:
        """Obtém série temporal."""
        metric = self._metrics.get(name)
        if metric:
            return metric.get_series(start, end, labels)
        return []
    
    def add_collector(self, collector: Callable) -> None:
        """Adiciona coletor customizado."""
        self._collectors.append(collector)
    
    async def collect_all(self) -> None:
        """Executa todos os coletores."""
        for collector in self._collectors:
            try:
                if callable(collector):
                    result = collector()
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                logger.error(f"Collector error: {e}")
    
    def to_prometheus_format(self) -> str:
        """Exporta métricas em formato Prometheus."""
        lines = []
        
        for metric in self._metrics.values():
            lines.append(f"# HELP {metric.name} {metric.description}")
            lines.append(f"# TYPE {metric.name} {metric.type.value}")
            
            latest = metric.get_latest()
            if latest is not None:
                lines.append(f"{metric.name} {latest}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Exporta todas as métricas como dict."""
        return {
            name: metric.to_dict()
            for name, metric in self._metrics.items()
        }


# Métricas padrão do sistema
def create_default_metrics(collector: MetricCollector) -> None:
    """Cria métricas padrão."""
    # Agent metrics
    collector.register(
        "agent_executions_total",
        MetricType.COUNTER,
        "Total de execuções de agentes",
        labels=["agent_name", "status"]
    )
    
    collector.register(
        "agent_execution_duration_seconds",
        MetricType.HISTOGRAM,
        "Duração das execuções",
        unit="seconds",
        labels=["agent_name"]
    )
    
    collector.register(
        "agent_tokens_total",
        MetricType.COUNTER,
        "Total de tokens usados",
        labels=["agent_name", "model"]
    )
    
    collector.register(
        "agent_cost_usd",
        MetricType.COUNTER,
        "Custo total em USD",
        unit="USD",
        labels=["agent_name", "model"]
    )
    
    collector.register(
        "agent_success_rate",
        MetricType.GAUGE,
        "Taxa de sucesso",
        labels=["agent_name"]
    )
    
    # System metrics
    collector.register(
        "active_agents",
        MetricType.GAUGE,
        "Agentes ativos"
    )
    
    collector.register(
        "active_conversations",
        MetricType.GAUGE,
        "Conversas ativas"
    )
    
    collector.register(
        "api_requests_total",
        MetricType.COUNTER,
        "Total de requisições API",
        labels=["endpoint", "method", "status"]
    )
    
    collector.register(
        "api_latency_seconds",
        MetricType.HISTOGRAM,
        "Latência da API",
        unit="seconds",
        labels=["endpoint"]
    )


# Singleton
_collector: Optional[MetricCollector] = None


def get_metric_collector() -> MetricCollector:
    """Obtém coletor de métricas."""
    global _collector
    if _collector is None:
        _collector = MetricCollector()
        create_default_metrics(_collector)
    return _collector

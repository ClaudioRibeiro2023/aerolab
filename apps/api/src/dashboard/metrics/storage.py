"""
Metric Storage - Armazenamento de métricas time-series.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredPoint:
    """Ponto armazenado."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class RetentionPolicy:
    """Política de retenção."""
    name: str
    duration: timedelta
    resolution: timedelta
    
    @classmethod
    def raw(cls) -> "RetentionPolicy":
        """Raw data: 24h, full resolution."""
        return cls("raw", timedelta(hours=24), timedelta(seconds=0))
    
    @classmethod
    def hourly(cls) -> "RetentionPolicy":
        """Hourly: 7 days."""
        return cls("hourly", timedelta(days=7), timedelta(hours=1))
    
    @classmethod
    def daily(cls) -> "RetentionPolicy":
        """Daily: 90 days."""
        return cls("daily", timedelta(days=90), timedelta(days=1))
    
    @classmethod
    def monthly(cls) -> "RetentionPolicy":
        """Monthly: 2 years."""
        return cls("monthly", timedelta(days=730), timedelta(days=30))


class MetricStorage:
    """
    Armazenamento de métricas.
    
    Suporta:
    - Múltiplas políticas de retenção
    - Compactação automática
    - Query por time range
    - Labels indexados
    """
    
    def __init__(
        self,
        policies: Optional[List[RetentionPolicy]] = None
    ):
        self._data: Dict[str, Dict[str, List[StoredPoint]]] = defaultdict(
            lambda: defaultdict(list)
        )  # metric -> tier -> points
        
        self._policies = policies or [
            RetentionPolicy.raw(),
            RetentionPolicy.hourly(),
            RetentionPolicy.daily()
        ]
        
        self._label_index: Dict[str, Dict[str, set]] = defaultdict(
            lambda: defaultdict(set)
        )  # label_key -> label_value -> set of metric names
        
        self._lock = threading.RLock()
        self._max_points_per_tier = 100000
    
    def write(
        self,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Escreve um ponto."""
        with self._lock:
            point = StoredPoint(
                timestamp=timestamp or datetime.now(),
                value=value,
                labels=labels or {}
            )
            
            # Adicionar ao tier raw
            self._data[metric]["raw"].append(point)
            
            # Indexar labels
            for key, value in (labels or {}).items():
                self._label_index[key][value].add(metric)
            
            # Aplicar limites
            if len(self._data[metric]["raw"]) > self._max_points_per_tier:
                self._compact_tier(metric, "raw")
    
    def write_batch(
        self,
        metric: str,
        points: List[Dict]
    ) -> int:
        """Escreve múltiplos pontos."""
        count = 0
        for point in points:
            self.write(
                metric=metric,
                value=point.get("value", 0),
                timestamp=point.get("timestamp"),
                labels=point.get("labels")
            )
            count += 1
        return count
    
    def read(
        self,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        limit: int = 10000
    ) -> List[StoredPoint]:
        """Lê pontos de uma métrica."""
        with self._lock:
            # Determinar melhor tier baseado no range
            tier = self._select_tier(start, end)
            points = self._data[metric].get(tier, [])
            
            # Filtrar por time range
            if start:
                points = [p for p in points if p.timestamp >= start]
            if end:
                points = [p for p in points if p.timestamp <= end]
            
            # Filtrar por labels
            if labels:
                points = [
                    p for p in points
                    if all(p.labels.get(k) == v for k, v in labels.items())
                ]
            
            # Limitar
            return points[-limit:]
    
    def read_latest(
        self,
        metric: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[StoredPoint]:
        """Lê ponto mais recente."""
        points = self.read(metric, labels=labels, limit=1)
        return points[-1] if points else None
    
    def _select_tier(
        self,
        start: Optional[datetime],
        end: Optional[datetime]
    ) -> str:
        """Seleciona melhor tier para o range."""
        if not start:
            return "raw"
        
        now = datetime.now()
        range_duration = (end or now) - start
        
        # Usar tier com resolução apropriada
        for policy in self._policies:
            if range_duration <= policy.duration:
                return policy.name
        
        return self._policies[-1].name
    
    def _compact_tier(self, metric: str, tier: str) -> None:
        """Compacta tier removendo dados antigos."""
        policy = next((p for p in self._policies if p.name == tier), None)
        if not policy:
            return
        
        cutoff = datetime.now() - policy.duration
        self._data[metric][tier] = [
            p for p in self._data[metric][tier]
            if p.timestamp >= cutoff
        ]
    
    def aggregate(
        self,
        metric: str,
        function: str = "avg",
        interval: str = "1h",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict]:
        """Agrega pontos por intervalo."""
        from .aggregator import get_aggregator, AggregationFunction
        
        points = self.read(metric, start, end)
        if not points:
            return []
        
        aggregator = get_aggregator()
        
        # Converter para formato do agregador
        data_points = [(p.timestamp, p.value) for p in points]
        
        # Mapear função
        func_map = {
            "sum": AggregationFunction.SUM,
            "avg": AggregationFunction.AVG,
            "min": AggregationFunction.MIN,
            "max": AggregationFunction.MAX,
            "count": AggregationFunction.COUNT,
            "p95": AggregationFunction.P95,
            "p99": AggregationFunction.P99,
        }
        
        agg_func = func_map.get(function, AggregationFunction.AVG)
        result = aggregator.aggregate(data_points, interval, agg_func)
        
        return [p.to_dict() for p in result]
    
    def list_metrics(self) -> List[str]:
        """Lista todas as métricas."""
        return list(self._data.keys())
    
    def list_label_values(
        self,
        label_key: str,
        metric: Optional[str] = None
    ) -> List[str]:
        """Lista valores de um label."""
        if metric:
            points = self._data[metric].get("raw", [])
            values = set()
            for p in points:
                if label_key in p.labels:
                    values.add(p.labels[label_key])
            return list(values)
        
        return list(self._label_index.get(label_key, {}).keys())
    
    def delete(
        self,
        metric: str,
        before: Optional[datetime] = None
    ) -> int:
        """Deleta pontos de uma métrica."""
        with self._lock:
            if metric not in self._data:
                return 0
            
            if before is None:
                # Deletar tudo
                count = sum(len(v) for v in self._data[metric].values())
                del self._data[metric]
                return count
            
            # Deletar antes de uma data
            count = 0
            for tier in self._data[metric]:
                original_len = len(self._data[metric][tier])
                self._data[metric][tier] = [
                    p for p in self._data[metric][tier]
                    if p.timestamp >= before
                ]
                count += original_len - len(self._data[metric][tier])
            
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do storage."""
        total_points = 0
        metrics_count = len(self._data)
        
        for metric_data in self._data.values():
            for tier_data in metric_data.values():
                total_points += len(tier_data)
        
        return {
            "metrics": metrics_count,
            "totalPoints": total_points,
            "policies": [p.name for p in self._policies],
        }


# Singleton
_storage: Optional[MetricStorage] = None


def get_metric_storage() -> MetricStorage:
    """Obtém storage de métricas."""
    global _storage
    if _storage is None:
        _storage = MetricStorage()
    return _storage

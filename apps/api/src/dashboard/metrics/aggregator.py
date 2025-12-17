"""
Time Series Aggregator - Agregação de séries temporais.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class AggregationFunction(str, Enum):
    """Funções de agregação."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    LAST = "last"
    FIRST = "first"
    
    # Percentiles
    P50 = "p50"
    P90 = "p90"
    P95 = "p95"
    P99 = "p99"
    
    # Rate
    RATE = "rate"
    IRATE = "irate"
    
    # Comparison
    DELTA = "delta"
    INCREASE = "increase"


class TimeInterval(str, Enum):
    """Intervalos de tempo."""
    SECOND = "1s"
    SECONDS_5 = "5s"
    SECONDS_15 = "15s"
    SECONDS_30 = "30s"
    MINUTE = "1m"
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOUR = "1h"
    HOURS_3 = "3h"
    HOURS_6 = "6h"
    HOURS_12 = "12h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


@dataclass
class AggregatedPoint:
    """Ponto agregado."""
    timestamp: datetime
    value: float
    count: int = 1
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
        }


@dataclass
class TimeSeries:
    """Série temporal agregada."""
    metric_name: str
    labels: Dict[str, str]
    points: List[AggregatedPoint]
    interval: TimeInterval
    aggregation: AggregationFunction
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric_name,
            "labels": self.labels,
            "points": [p.to_dict() for p in self.points],
            "interval": self.interval.value,
            "aggregation": self.aggregation.value,
        }


class TimeSeriesAggregator:
    """
    Agregador de séries temporais.
    
    Suporta:
    - Múltiplas funções de agregação
    - Downsampling
    - Fill gaps
    - Comparações temporais
    """
    
    @staticmethod
    def parse_interval(interval: str) -> timedelta:
        """Converte string de intervalo para timedelta."""
        unit = interval[-1]
        value = int(interval[:-1])
        
        if unit == 's':
            return timedelta(seconds=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        elif unit == 'M':
            return timedelta(days=value * 30)
        
        return timedelta(minutes=1)
    
    @staticmethod
    def get_bucket_key(timestamp: datetime, interval: timedelta) -> datetime:
        """Obtém chave do bucket para timestamp."""
        epoch = datetime(1970, 1, 1)
        seconds = (timestamp - epoch).total_seconds()
        bucket_seconds = (seconds // interval.total_seconds()) * interval.total_seconds()
        return epoch + timedelta(seconds=bucket_seconds)
    
    def aggregate(
        self,
        points: List[Tuple[datetime, float]],
        interval: str,
        function: AggregationFunction = AggregationFunction.AVG,
        fill_gaps: bool = False,
        fill_value: float = 0
    ) -> List[AggregatedPoint]:
        """
        Agrega pontos por intervalo.
        
        Args:
            points: Lista de (timestamp, value)
            interval: Intervalo de agregação (1m, 5m, 1h, etc.)
            function: Função de agregação
            fill_gaps: Preencher gaps com fill_value
            fill_value: Valor para gaps
            
        Returns:
            Lista de pontos agregados
        """
        if not points:
            return []
        
        delta = self.parse_interval(interval)
        
        # Agrupar por bucket
        buckets: Dict[datetime, List[float]] = {}
        
        for ts, value in points:
            key = self.get_bucket_key(ts, delta)
            if key not in buckets:
                buckets[key] = []
            buckets[key].append(value)
        
        # Agregar cada bucket
        result = []
        
        for bucket_ts in sorted(buckets.keys()):
            values = buckets[bucket_ts]
            aggregated_value = self._apply_function(values, function)
            
            result.append(AggregatedPoint(
                timestamp=bucket_ts,
                value=aggregated_value,
                count=len(values),
                min_value=min(values),
                max_value=max(values)
            ))
        
        # Preencher gaps
        if fill_gaps and len(result) >= 2:
            result = self._fill_gaps(result, delta, fill_value)
        
        return result
    
    def _apply_function(
        self,
        values: List[float],
        function: AggregationFunction
    ) -> float:
        """Aplica função de agregação."""
        if not values:
            return 0
        
        if function == AggregationFunction.SUM:
            return sum(values)
        elif function == AggregationFunction.AVG:
            return statistics.mean(values)
        elif function == AggregationFunction.MIN:
            return min(values)
        elif function == AggregationFunction.MAX:
            return max(values)
        elif function == AggregationFunction.COUNT:
            return len(values)
        elif function == AggregationFunction.LAST:
            return values[-1]
        elif function == AggregationFunction.FIRST:
            return values[0]
        elif function == AggregationFunction.P50:
            return self._percentile(values, 50)
        elif function == AggregationFunction.P90:
            return self._percentile(values, 90)
        elif function == AggregationFunction.P95:
            return self._percentile(values, 95)
        elif function == AggregationFunction.P99:
            return self._percentile(values, 99)
        elif function == AggregationFunction.DELTA:
            return values[-1] - values[0] if len(values) > 1 else 0
        elif function == AggregationFunction.INCREASE:
            return max(0, values[-1] - values[0]) if len(values) > 1 else 0
        
        return statistics.mean(values)
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calcula percentil."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * percentile / 100)
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]
    
    def _fill_gaps(
        self,
        points: List[AggregatedPoint],
        interval: timedelta,
        fill_value: float
    ) -> List[AggregatedPoint]:
        """Preenche gaps na série."""
        if len(points) < 2:
            return points
        
        filled = []
        
        for i, point in enumerate(points):
            filled.append(point)
            
            if i < len(points) - 1:
                next_point = points[i + 1]
                expected_next = point.timestamp + interval
                
                # Adicionar pontos faltantes
                while expected_next < next_point.timestamp:
                    filled.append(AggregatedPoint(
                        timestamp=expected_next,
                        value=fill_value,
                        count=0
                    ))
                    expected_next += interval
        
        return filled
    
    def compare_periods(
        self,
        current: List[Tuple[datetime, float]],
        previous: List[Tuple[datetime, float]],
        interval: str,
        function: AggregationFunction = AggregationFunction.AVG
    ) -> Dict[str, Any]:
        """Compara dois períodos."""
        current_agg = self.aggregate(current, interval, function)
        previous_agg = self.aggregate(previous, interval, function)
        
        current_total = sum(p.value for p in current_agg) if current_agg else 0
        previous_total = sum(p.value for p in previous_agg) if previous_agg else 0
        
        if previous_total > 0:
            change_percent = ((current_total - previous_total) / previous_total) * 100
        else:
            change_percent = 100 if current_total > 0 else 0
        
        return {
            "current": current_total,
            "previous": previous_total,
            "change": current_total - previous_total,
            "changePercent": round(change_percent, 2),
            "trend": "up" if change_percent > 0 else "down" if change_percent < 0 else "stable"
        }
    
    def downsample(
        self,
        points: List[AggregatedPoint],
        target_points: int = 100
    ) -> List[AggregatedPoint]:
        """Reduz número de pontos mantendo forma."""
        if len(points) <= target_points:
            return points
        
        step = len(points) / target_points
        result = []
        
        i = 0
        while i < len(points):
            result.append(points[int(i)])
            i += step
        
        return result


# Singleton
_aggregator: Optional[TimeSeriesAggregator] = None


def get_aggregator() -> TimeSeriesAggregator:
    """Obtém agregador."""
    global _aggregator
    if _aggregator is None:
        _aggregator = TimeSeriesAggregator()
    return _aggregator

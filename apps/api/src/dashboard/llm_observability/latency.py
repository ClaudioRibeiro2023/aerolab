"""
Latency Tracker - Rastreamento de latência de LLMs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import statistics
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class LatencyPercentiles:
    """Percentis de latência."""
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0
    count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "p50": round(self.p50, 2),
            "p75": round(self.p75, 2),
            "p90": round(self.p90, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
            "min": round(self.min, 2),
            "max": round(self.max, 2),
            "avg": round(self.avg, 2),
            "count": self.count,
        }
    
    @classmethod
    def from_values(cls, values: List[float]) -> "LatencyPercentiles":
        """Calcula percentis de lista de valores."""
        if not values:
            return cls()
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        def percentile(p: int) -> float:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            return sorted_values[idx]
        
        return cls(
            p50=percentile(50),
            p75=percentile(75),
            p90=percentile(90),
            p95=percentile(95),
            p99=percentile(99),
            min=sorted_values[0],
            max=sorted_values[-1],
            avg=statistics.mean(values),
            count=n
        )


@dataclass
class LatencyEntry:
    """Entrada de latência."""
    timestamp: datetime
    model: str
    provider: str
    
    # Latências
    total_ms: float
    time_to_first_token_ms: Optional[float] = None
    
    # Performance
    tokens_per_second: Optional[float] = None
    output_tokens: int = 0
    
    # Context
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "totalMs": self.total_ms,
            "timeToFirstTokenMs": self.time_to_first_token_ms,
            "tokensPerSecond": self.tokens_per_second,
        }


class LatencyTracker:
    """
    Rastreador de latência.
    
    Monitora:
    - Latência total
    - Time to first token (TTFT)
    - Tokens por segundo
    - Percentis por modelo
    """
    
    def __init__(self, max_entries: int = 100000):
        self._entries: List[LatencyEntry] = []
        self._by_model: Dict[str, List[LatencyEntry]] = defaultdict(list)
        self._max_entries = max_entries
        self._lock = threading.RLock()
    
    def track(
        self,
        model: str,
        total_ms: float,
        time_to_first_token_ms: Optional[float] = None,
        output_tokens: int = 0,
        provider: str = "",
        user_id: Optional[str] = None
    ) -> LatencyEntry:
        """Registra latência."""
        # Calcular tokens por segundo
        tokens_per_second = None
        if output_tokens > 0 and total_ms > 0:
            tokens_per_second = (output_tokens / total_ms) * 1000
        
        entry = LatencyEntry(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            total_ms=total_ms,
            time_to_first_token_ms=time_to_first_token_ms,
            tokens_per_second=tokens_per_second,
            output_tokens=output_tokens,
            user_id=user_id
        )
        
        with self._lock:
            self._entries.append(entry)
            self._by_model[model].append(entry)
            
            # Limitar tamanho
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
        
        return entry
    
    def get_percentiles(
        self,
        model: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> LatencyPercentiles:
        """Obtém percentis de latência."""
        if model:
            entries = self._by_model.get(model, [])
        else:
            entries = self._entries
        
        entries = self._filter_by_time(entries, start, end)
        
        if not entries:
            return LatencyPercentiles()
        
        values = [e.total_ms for e in entries]
        return LatencyPercentiles.from_values(values)
    
    def get_ttft_percentiles(
        self,
        model: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> LatencyPercentiles:
        """Obtém percentis de TTFT."""
        if model:
            entries = self._by_model.get(model, [])
        else:
            entries = self._entries
        
        entries = self._filter_by_time(entries, start, end)
        entries = [e for e in entries if e.time_to_first_token_ms is not None]
        
        if not entries:
            return LatencyPercentiles()
        
        values = [e.time_to_first_token_ms for e in entries]
        return LatencyPercentiles.from_values(values)
    
    def get_percentiles_by_model(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, LatencyPercentiles]:
        """Obtém percentis por modelo."""
        result = {}
        
        for model in self._by_model.keys():
            result[model] = self.get_percentiles(model, start, end)
        
        return result
    
    def get_avg_tokens_per_second(
        self,
        model: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> float:
        """Obtém média de tokens por segundo."""
        if model:
            entries = self._by_model.get(model, [])
        else:
            entries = self._entries
        
        entries = self._filter_by_time(entries, start, end)
        entries = [e for e in entries if e.tokens_per_second is not None]
        
        if not entries:
            return 0
        
        return statistics.mean(e.tokens_per_second for e in entries)
    
    def get_time_series(
        self,
        model: Optional[str] = None,
        interval: str = "1h",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[Dict]:
        """Obtém série temporal de latência."""
        if model:
            entries = self._by_model.get(model, [])
        else:
            entries = self._entries
        
        entries = self._filter_by_time(entries, start, end)
        
        if not entries:
            return []
        
        # Parse interval
        unit = interval[-1]
        value = int(interval[:-1])
        
        if unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        else:
            delta = timedelta(hours=1)
        
        # Agrupar por bucket
        buckets: Dict[datetime, List[float]] = defaultdict(list)
        
        for entry in entries:
            bucket_ts = self._get_bucket(entry.timestamp, delta)
            buckets[bucket_ts].append(entry.total_ms)
        
        # Calcular stats por bucket
        result = []
        for bucket_ts in sorted(buckets.keys()):
            values = buckets[bucket_ts]
            percentiles = LatencyPercentiles.from_values(values)
            
            result.append({
                "timestamp": bucket_ts.isoformat(),
                "p50": percentiles.p50,
                "p95": percentiles.p95,
                "p99": percentiles.p99,
                "avg": percentiles.avg,
                "count": len(values),
            })
        
        return result
    
    def compare_models(
        self,
        models: List[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """Compara latência entre modelos."""
        result = {}
        
        for model in models:
            percentiles = self.get_percentiles(model, start, end)
            ttft = self.get_ttft_percentiles(model, start, end)
            tps = self.get_avg_tokens_per_second(model, start, end)
            
            result[model] = {
                "latency": percentiles.to_dict(),
                "ttft": ttft.to_dict(),
                "tokensPerSecond": round(tps, 2),
            }
        
        return result
    
    def get_summary(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtém resumo de latência."""
        entries = self._filter_by_time(self._entries, start, end)
        
        if not entries:
            return {
                "totalRequests": 0,
                "avgLatencyMs": 0,
            }
        
        percentiles = LatencyPercentiles.from_values([e.total_ms for e in entries])
        
        return {
            "totalRequests": len(entries),
            "avgLatencyMs": percentiles.avg,
            "p50LatencyMs": percentiles.p50,
            "p95LatencyMs": percentiles.p95,
            "p99LatencyMs": percentiles.p99,
            "modelCount": len(self._by_model),
            "byModel": self.get_percentiles_by_model(start, end),
        }
    
    def _filter_by_time(
        self,
        entries: List[LatencyEntry],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[LatencyEntry]:
        """Filtra por tempo."""
        if start:
            entries = [e for e in entries if e.timestamp >= start]
        if end:
            entries = [e for e in entries if e.timestamp <= end]
        return entries
    
    def _get_bucket(self, ts: datetime, delta: timedelta) -> datetime:
        """Obtém bucket de tempo."""
        epoch = datetime(1970, 1, 1)
        seconds = (ts - epoch).total_seconds()
        bucket_seconds = (seconds // delta.total_seconds()) * delta.total_seconds()
        return epoch + timedelta(seconds=bucket_seconds)


# Singleton
_tracker: Optional[LatencyTracker] = None


def get_latency_tracker() -> LatencyTracker:
    """Obtém latency tracker."""
    global _tracker
    if _tracker is None:
        _tracker = LatencyTracker()
    return _tracker

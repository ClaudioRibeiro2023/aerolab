"""
Query Engine - Motor de queries para métricas.

Suporta sintaxe similar a PromQL.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Resultado de uma query."""
    data: List[Dict] = field(default_factory=list)
    metric: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    execution_time_ms: float = 0
    points_scanned: int = 0
    
    # Scalar result
    scalar: Optional[float] = None
    
    # Error
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "data": self.data,
            "metric": self.metric,
            "labels": self.labels,
            "executionTimeMs": self.execution_time_ms,
            "pointsScanned": self.points_scanned,
            "scalar": self.scalar,
            "error": self.error,
        }


@dataclass
class TimeRange:
    """Range de tempo para query."""
    start: datetime
    end: datetime
    step: Optional[str] = None  # 1m, 5m, 1h, etc.
    
    @classmethod
    def last(cls, duration: str) -> "TimeRange":
        """Cria range dos últimos N tempo."""
        now = datetime.now()
        
        # Parse duration
        unit = duration[-1]
        value = int(duration[:-1])
        
        if unit == 's':
            delta = timedelta(seconds=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'w':
            delta = timedelta(weeks=value)
        else:
            delta = timedelta(hours=1)
        
        return cls(start=now - delta, end=now)
    
    @classmethod
    def today(cls) -> "TimeRange":
        """Cria range de hoje."""
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return cls(start=start, end=now)
    
    @classmethod
    def yesterday(cls) -> "TimeRange":
        """Cria range de ontem."""
        now = datetime.now()
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
        return cls(start=start, end=end)


class QueryParser:
    """Parser de queries."""
    
    # Padrões regex
    METRIC_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)')
    LABELS_PATTERN = re.compile(r'\{([^}]*)\}')
    FUNCTION_PATTERN = re.compile(r'(\w+)\((.*)\)')
    RANGE_PATTERN = re.compile(r'\[(\d+[smhdw])\]')
    
    def parse(self, query: str) -> Dict[str, Any]:
        """Faz parse de uma query."""
        query = query.strip()
        
        result = {
            "metric": None,
            "labels": {},
            "function": None,
            "args": [],
            "range": None,
            "raw": query,
        }
        
        # Verificar se é função
        func_match = self.FUNCTION_PATTERN.match(query)
        if func_match:
            result["function"] = func_match.group(1)
            inner = func_match.group(2)
            
            # Parse argumentos
            args = self._parse_args(inner)
            if args:
                result["args"] = args
                # Primeiro argumento geralmente é a métrica
                if args:
                    inner_parsed = self.parse(args[0])
                    result["metric"] = inner_parsed.get("metric")
                    result["labels"] = inner_parsed.get("labels", {})
        else:
            # Parse métrica simples
            metric_match = self.METRIC_PATTERN.match(query)
            if metric_match:
                result["metric"] = metric_match.group(1)
            
            # Parse labels
            labels_match = self.LABELS_PATTERN.search(query)
            if labels_match:
                labels_str = labels_match.group(1)
                result["labels"] = self._parse_labels(labels_str)
            
            # Parse range
            range_match = self.RANGE_PATTERN.search(query)
            if range_match:
                result["range"] = range_match.group(1)
        
        return result
    
    def _parse_labels(self, labels_str: str) -> Dict[str, str]:
        """Parse string de labels."""
        labels = {}
        
        # Suporta: key="value", key=value, key=~"regex"
        parts = labels_str.split(',')
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                labels[key] = value
        
        return labels
    
    def _parse_args(self, args_str: str) -> List[str]:
        """Parse argumentos de função."""
        args = []
        current = ""
        depth = 0
        
        for char in args_str:
            if char == ',' and depth == 0:
                args.append(current.strip())
                current = ""
            else:
                if char in '([{':
                    depth += 1
                elif char in ')]}':
                    depth -= 1
                current += char
        
        if current.strip():
            args.append(current.strip())
        
        return args


class QueryEngine:
    """
    Motor de queries.
    
    Executa queries em métricas armazenadas.
    """
    
    def __init__(self):
        self._parser = QueryParser()
        self._functions = {
            "sum": self._func_sum,
            "avg": self._func_avg,
            "min": self._func_min,
            "max": self._func_max,
            "count": self._func_count,
            "rate": self._func_rate,
            "increase": self._func_increase,
            "histogram_quantile": self._func_histogram_quantile,
            "delta": self._func_delta,
            "absent": self._func_absent,
            "label_values": self._func_label_values,
        }
    
    async def execute(
        self,
        query: str,
        time_range: Optional[TimeRange] = None,
        step: Optional[str] = None
    ) -> QueryResult:
        """Executa uma query."""
        import time
        start_time = time.time()
        
        try:
            parsed = self._parser.parse(query)
            
            if not parsed.get("metric"):
                return QueryResult(error="No metric specified")
            
            # Obter storage
            from .storage import get_metric_storage
            storage = get_metric_storage()
            
            # Definir time range
            if not time_range:
                time_range = TimeRange.last("1h")
            
            # Buscar dados
            points = storage.read(
                parsed["metric"],
                start=time_range.start,
                end=time_range.end,
                labels=parsed.get("labels")
            )
            
            # Aplicar função se presente
            if parsed.get("function"):
                func = self._functions.get(parsed["function"])
                if func:
                    result = await func(points, parsed.get("args", []), time_range)
                else:
                    return QueryResult(error=f"Unknown function: {parsed['function']}")
            else:
                # Retornar série raw
                result = QueryResult(
                    data=[
                        {"timestamp": p.timestamp.isoformat(), "value": p.value}
                        for p in points
                    ],
                    metric=parsed["metric"],
                    labels=parsed.get("labels", {}),
                    points_scanned=len(points)
                )
            
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return QueryResult(error=str(e))
    
    # Funções de agregação
    async def _func_sum(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Soma todos os valores."""
        if not points:
            return QueryResult(scalar=0)
        
        total = sum(p.value for p in points)
        return QueryResult(
            scalar=total,
            points_scanned=len(points)
        )
    
    async def _func_avg(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Média dos valores."""
        if not points:
            return QueryResult(scalar=0)
        
        avg = sum(p.value for p in points) / len(points)
        return QueryResult(
            scalar=avg,
            points_scanned=len(points)
        )
    
    async def _func_min(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Valor mínimo."""
        if not points:
            return QueryResult(scalar=0)
        
        return QueryResult(
            scalar=min(p.value for p in points),
            points_scanned=len(points)
        )
    
    async def _func_max(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Valor máximo."""
        if not points:
            return QueryResult(scalar=0)
        
        return QueryResult(
            scalar=max(p.value for p in points),
            points_scanned=len(points)
        )
    
    async def _func_count(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Contagem de pontos."""
        return QueryResult(
            scalar=len(points),
            points_scanned=len(points)
        )
    
    async def _func_rate(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Taxa de mudança por segundo."""
        if len(points) < 2:
            return QueryResult(scalar=0)
        
        first = points[0]
        last = points[-1]
        
        value_diff = last.value - first.value
        time_diff = (last.timestamp - first.timestamp).total_seconds()
        
        rate = value_diff / time_diff if time_diff > 0 else 0
        
        return QueryResult(
            scalar=rate,
            points_scanned=len(points)
        )
    
    async def _func_increase(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Aumento total no período."""
        if len(points) < 2:
            return QueryResult(scalar=0)
        
        increase = max(0, points[-1].value - points[0].value)
        
        return QueryResult(
            scalar=increase,
            points_scanned=len(points)
        )
    
    async def _func_delta(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Diferença entre primeiro e último."""
        if len(points) < 2:
            return QueryResult(scalar=0)
        
        delta = points[-1].value - points[0].value
        
        return QueryResult(
            scalar=delta,
            points_scanned=len(points)
        )
    
    async def _func_histogram_quantile(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Calcula quantil de histograma."""
        if not args or not points:
            return QueryResult(scalar=0)
        
        try:
            quantile = float(args[0])
        except:
            quantile = 0.95
        
        values = sorted(p.value for p in points)
        idx = int(len(values) * quantile)
        idx = min(idx, len(values) - 1)
        
        return QueryResult(
            scalar=values[idx] if values else 0,
            points_scanned=len(points)
        )
    
    async def _func_absent(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Retorna 1 se métrica ausente, 0 se presente."""
        return QueryResult(scalar=0 if points else 1)
    
    async def _func_label_values(
        self,
        points: List,
        args: List[str],
        time_range: TimeRange
    ) -> QueryResult:
        """Lista valores únicos de um label."""
        if not args:
            return QueryResult(data=[])
        
        label_key = args[0].strip('"\'')
        values = set()
        
        for p in points:
            if label_key in p.labels:
                values.add(p.labels[label_key])
        
        return QueryResult(
            data=list(values),
            points_scanned=len(points)
        )


# Singleton
_query_engine: Optional[QueryEngine] = None


def get_query_engine() -> QueryEngine:
    """Obtém query engine."""
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine()
    return _query_engine

"""
Widget Config Builder - Construtor de configurações de widgets.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Tipos de gráfico."""
    LINE = "line_chart"
    AREA = "area_chart"
    BAR = "bar_chart"
    PIE = "pie_chart"
    DONUT = "donut_chart"
    SCATTER = "scatter_chart"
    HEATMAP = "heatmap"


class AggregationType(str, Enum):
    """Tipos de agregação."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    RATE = "rate"
    INCREASE = "increase"
    HISTOGRAM = "histogram_quantile"


@dataclass
class QueryCondition:
    """Condição de filtro para query."""
    field: str
    operator: str  # =, !=, =~, !~, >, <, >=, <=
    value: Union[str, int, float]
    
    def to_promql(self) -> str:
        """Converte para formato PromQL."""
        if self.operator in ["=", "!="]:
            return f'{self.field}{self.operator}"{self.value}"'
        elif self.operator in ["=~", "!~"]:
            return f'{self.field}{self.operator}"{self.value}"'
        else:
            return f'{self.field}{self.operator}{self.value}'


class QueryBuilder:
    """
    Construtor de queries PromQL-like.
    
    Exemplo:
        query = (QueryBuilder()
            .metric("llm_requests_total")
            .filter("model", "=", "gpt-4")
            .filter("status", "=", "success")
            .rate("5m")
            .sum_by(["agent_name"])
            .build())
    """
    
    def __init__(self):
        self._metric_name: str = ""
        self._conditions: List[QueryCondition] = []
        self._aggregation: Optional[AggregationType] = None
        self._aggregation_args: List[str] = []
        self._group_by: List[str] = []
        self._range: Optional[str] = None
        self._functions: List[tuple] = []  # (func_name, args)
    
    def metric(self, name: str) -> "QueryBuilder":
        """Define a métrica base."""
        self._metric_name = name
        return self
    
    def filter(
        self,
        field: str,
        operator: str,
        value: Union[str, int, float]
    ) -> "QueryBuilder":
        """Adiciona filtro."""
        self._conditions.append(QueryCondition(field, operator, value))
        return self
    
    def label_eq(self, label: str, value: str) -> "QueryBuilder":
        """Shortcut para filtro de igualdade."""
        return self.filter(label, "=", value)
    
    def label_neq(self, label: str, value: str) -> "QueryBuilder":
        """Shortcut para filtro de diferença."""
        return self.filter(label, "!=", value)
    
    def label_regex(self, label: str, pattern: str) -> "QueryBuilder":
        """Shortcut para filtro regex."""
        return self.filter(label, "=~", pattern)
    
    def rate(self, interval: str = "5m") -> "QueryBuilder":
        """Aplica rate()."""
        self._functions.append(("rate", [interval]))
        return self
    
    def increase(self, interval: str = "5m") -> "QueryBuilder":
        """Aplica increase()."""
        self._functions.append(("increase", [interval]))
        return self
    
    def sum(self) -> "QueryBuilder":
        """Aplica sum()."""
        self._aggregation = AggregationType.SUM
        return self
    
    def avg(self) -> "QueryBuilder":
        """Aplica avg()."""
        self._aggregation = AggregationType.AVG
        return self
    
    def min(self) -> "QueryBuilder":
        """Aplica min()."""
        self._aggregation = AggregationType.MIN
        return self
    
    def max(self) -> "QueryBuilder":
        """Aplica max()."""
        self._aggregation = AggregationType.MAX
        return self
    
    def count(self) -> "QueryBuilder":
        """Aplica count()."""
        self._aggregation = AggregationType.COUNT
        return self
    
    def histogram_quantile(self, quantile: float) -> "QueryBuilder":
        """Aplica histogram_quantile()."""
        self._aggregation = AggregationType.HISTOGRAM
        self._aggregation_args = [str(quantile)]
        return self
    
    def by(self, labels: List[str]) -> "QueryBuilder":
        """Define agrupamento."""
        self._group_by = labels
        return self
    
    def sum_by(self, labels: List[str]) -> "QueryBuilder":
        """Shortcut para sum() by()."""
        return self.sum().by(labels)
    
    def avg_by(self, labels: List[str]) -> "QueryBuilder":
        """Shortcut para avg() by()."""
        return self.avg().by(labels)
    
    def range(self, interval: str) -> "QueryBuilder":
        """Define range de tempo."""
        self._range = interval
        return self
    
    def build(self) -> str:
        """Constrói query final."""
        # Base metric com labels
        labels_str = ""
        if self._conditions:
            labels = [c.to_promql() for c in self._conditions]
            labels_str = "{" + ", ".join(labels) + "}"
        
        query = f"{self._metric_name}{labels_str}"
        
        # Range
        if self._range:
            query = f"{query}[{self._range}]"
        
        # Funções internas (rate, increase, etc)
        for func_name, args in self._functions:
            if func_name in ["rate", "increase"]:
                if not self._range:
                    query = f"{query}[{args[0]}]"
                query = f"{func_name}({query})"
        
        # Agregação
        if self._aggregation:
            if self._aggregation == AggregationType.HISTOGRAM:
                quantile = self._aggregation_args[0] if self._aggregation_args else "0.95"
                query = f"histogram_quantile({quantile}, {query})"
            else:
                agg_func = self._aggregation.value
                if self._group_by:
                    by_clause = f" by ({', '.join(self._group_by)})"
                    query = f"{agg_func}({query}){by_clause}"
                else:
                    query = f"{agg_func}({query})"
        
        return query
    
    def __str__(self) -> str:
        return self.build()


class WidgetConfigBuilder:
    """
    Construtor de configurações de widgets.
    
    Exemplo:
        config = (WidgetConfigBuilder()
            .title("Request Rate")
            .type("line_chart")
            .query(
                QueryBuilder()
                    .metric("requests_total")
                    .rate("5m")
                    .sum_by(["method"])
                    .build()
            )
            .chart_smooth()
            .chart_legend()
            .build())
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {
            "title": "New Widget",
            "type": "metric_card",
            "query": "",
            "config": {},
        }
    
    def title(self, title: str) -> "WidgetConfigBuilder":
        """Define título."""
        self._config["title"] = title
        return self
    
    def description(self, description: str) -> "WidgetConfigBuilder":
        """Define descrição."""
        self._config["description"] = description
        return self
    
    def type(self, widget_type: str) -> "WidgetConfigBuilder":
        """Define tipo do widget."""
        self._config["type"] = widget_type
        return self
    
    def query(self, query: Union[str, QueryBuilder]) -> "WidgetConfigBuilder":
        """Define query."""
        if isinstance(query, QueryBuilder):
            self._config["query"] = query.build()
        else:
            self._config["query"] = query
        return self
    
    def data_source(self, source_id: str) -> "WidgetConfigBuilder":
        """Define data source."""
        self._config["dataSourceId"] = source_id
        return self
    
    def refresh_interval(self, seconds: int) -> "WidgetConfigBuilder":
        """Define intervalo de refresh."""
        self._config["refreshIntervalSeconds"] = seconds
        return self
    
    # Configurações de métrica
    def metric_format(self, format: str) -> "WidgetConfigBuilder":
        """Define formato de métrica (number, currency, percent, duration, bytes)."""
        if "metric" not in self._config["config"]:
            self._config["config"]["metric"] = {}
        self._config["config"]["metric"]["format"] = format
        return self
    
    def metric_precision(self, precision: int) -> "WidgetConfigBuilder":
        """Define precisão decimal."""
        if "metric" not in self._config["config"]:
            self._config["config"]["metric"] = {}
        self._config["config"]["metric"]["precision"] = precision
        return self
    
    def metric_show_trend(self, show: bool = True) -> "WidgetConfigBuilder":
        """Mostra tendência."""
        if "metric" not in self._config["config"]:
            self._config["config"]["metric"] = {}
        self._config["config"]["metric"]["showTrend"] = show
        return self
    
    def metric_sparkline(self, show: bool = True) -> "WidgetConfigBuilder":
        """Mostra sparkline."""
        if "metric" not in self._config["config"]:
            self._config["config"]["metric"] = {}
        self._config["config"]["metric"]["sparkline"] = show
        return self
    
    # Configurações de chart
    def chart_legend(self, show: bool = True) -> "WidgetConfigBuilder":
        """Mostra legenda."""
        if "chart" not in self._config["config"]:
            self._config["config"]["chart"] = {}
        self._config["config"]["chart"]["showLegend"] = show
        return self
    
    def chart_grid(self, show: bool = True) -> "WidgetConfigBuilder":
        """Mostra grid."""
        if "chart" not in self._config["config"]:
            self._config["config"]["chart"] = {}
        self._config["config"]["chart"]["showGrid"] = show
        return self
    
    def chart_smooth(self, smooth: bool = True) -> "WidgetConfigBuilder":
        """Linhas suaves."""
        if "chart" not in self._config["config"]:
            self._config["config"]["chart"] = {}
        self._config["config"]["chart"]["smooth"] = smooth
        return self
    
    def chart_stacked(self, stacked: bool = True) -> "WidgetConfigBuilder":
        """Empilhado."""
        if "chart" not in self._config["config"]:
            self._config["config"]["chart"] = {}
        self._config["config"]["chart"]["stacked"] = stacked
        return self
    
    def chart_colors(self, colors: List[str]) -> "WidgetConfigBuilder":
        """Define cores."""
        if "chart" not in self._config["config"]:
            self._config["config"]["chart"] = {}
        self._config["config"]["chart"]["colorScheme"] = colors
        return self
    
    # Configurações de gauge
    def gauge_range(self, min_val: float, max_val: float) -> "WidgetConfigBuilder":
        """Define range do gauge."""
        if "gauge" not in self._config["config"]:
            self._config["config"]["gauge"] = {}
        self._config["config"]["gauge"]["min"] = min_val
        self._config["config"]["gauge"]["max"] = max_val
        return self
    
    def gauge_thresholds(self, thresholds: List[Dict]) -> "WidgetConfigBuilder":
        """Define thresholds do gauge."""
        if "gauge" not in self._config["config"]:
            self._config["config"]["gauge"] = {}
        self._config["config"]["gauge"]["thresholds"] = thresholds
        return self
    
    def gauge_unit(self, unit: str) -> "WidgetConfigBuilder":
        """Define unidade do gauge."""
        if "gauge" not in self._config["config"]:
            self._config["config"]["gauge"] = {}
        self._config["config"]["gauge"]["unit"] = unit
        return self
    
    # Configurações de tabela
    def table_columns(self, columns: List[Dict]) -> "WidgetConfigBuilder":
        """Define colunas da tabela."""
        if "table" not in self._config["config"]:
            self._config["config"]["table"] = {}
        self._config["config"]["table"]["columns"] = columns
        return self
    
    def table_sortable(self, sortable: bool = True) -> "WidgetConfigBuilder":
        """Tabela ordenável."""
        if "table" not in self._config["config"]:
            self._config["config"]["table"] = {}
        self._config["config"]["table"]["sortable"] = sortable
        return self
    
    def table_pagination(self, page_size: int = 10) -> "WidgetConfigBuilder":
        """Paginação da tabela."""
        if "table" not in self._config["config"]:
            self._config["config"]["table"] = {}
        self._config["config"]["table"]["pagination"] = True
        self._config["config"]["table"]["pageSize"] = page_size
        return self
    
    # Posição
    def position(self, x: int, y: int, w: int, h: int) -> "WidgetConfigBuilder":
        """Define posição no grid."""
        self._config["position"] = {"x": x, "y": y, "w": w, "h": h}
        return self
    
    def size(self, width: int, height: int) -> "WidgetConfigBuilder":
        """Define tamanho."""
        if "position" not in self._config:
            self._config["position"] = {"x": 0, "y": 0}
        self._config["position"]["w"] = width
        self._config["position"]["h"] = height
        return self
    
    def tags(self, tags: List[str]) -> "WidgetConfigBuilder":
        """Define tags."""
        self._config["tags"] = tags
        return self
    
    def build(self) -> Dict[str, Any]:
        """Constrói configuração final."""
        return self._config.copy()

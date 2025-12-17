"""
Widgets - Sistema de componentes visuais para dashboards.

Suporta 25+ tipos de widgets configuráveis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import uuid


class WidgetType(str, Enum):
    """Tipos de widgets disponíveis."""
    # KPIs
    METRIC_CARD = "metric_card"
    STAT_CARD = "stat_card"
    GAUGE = "gauge"
    PROGRESS = "progress"
    
    # Charts - Time Series
    LINE_CHART = "line_chart"
    AREA_CHART = "area_chart"
    BAR_CHART = "bar_chart"
    SPARKLINE = "sparkline"
    
    # Charts - Distribution
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    HISTOGRAM = "histogram"
    SCATTER = "scatter"
    
    # Charts - Advanced
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    SANKEY = "sankey"
    FUNNEL = "funnel"
    
    # Geographic
    MAP = "map"
    CHOROPLETH = "choropleth"
    
    # Data
    TABLE = "table"
    LOG_VIEWER = "log_viewer"
    TIMELINE = "timeline"
    
    # Traces
    TRACE_VIEWER = "trace_viewer"
    SPAN_TIMELINE = "span_timeline"
    
    # Status
    STATUS_GRID = "status_grid"
    ALERT_LIST = "alert_list"
    
    # Comparison
    COMPARISON = "comparison"
    DIFF_VIEWER = "diff_viewer"
    
    # Content
    MARKDOWN = "markdown"
    IMAGE = "image"
    VIDEO = "video"
    IFRAME = "iframe"
    
    # Custom
    CUSTOM = "custom"


class WidgetSize(str, Enum):
    """Tamanhos predefinidos."""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    WIDE = "wide"        # 4x1
    TALL = "tall"        # 1x2
    FULL = "full"        # 4x2


class RefreshInterval(str, Enum):
    """Intervalos de refresh."""
    OFF = "off"
    REALTIME = "realtime"  # WebSocket
    SECONDS_5 = "5s"
    SECONDS_15 = "15s"
    SECONDS_30 = "30s"
    MINUTE_1 = "1m"
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"


@dataclass
class ChartConfig:
    """Configuração de gráficos."""
    # Axes
    x_axis_label: str = ""
    y_axis_label: str = ""
    x_axis_type: str = "category"  # category, time, linear
    y_axis_type: str = "linear"
    
    # Display
    show_legend: bool = True
    legend_position: str = "bottom"  # top, bottom, left, right
    show_grid: bool = True
    show_tooltip: bool = True
    
    # Animation
    animate: bool = True
    animation_duration: int = 300
    
    # Colors
    colors: List[str] = field(default_factory=list)
    gradient: bool = False
    
    # Stacking
    stacked: bool = False
    
    # Line specific
    line_type: str = "linear"  # linear, smooth, step
    show_dots: bool = True
    dot_size: int = 4
    line_width: int = 2
    
    # Bar specific
    bar_width: float = 0.8
    horizontal: bool = False
    
    # Pie specific
    inner_radius: float = 0  # 0 = pie, >0 = donut
    
    def to_dict(self) -> Dict:
        return {
            "xAxisLabel": self.x_axis_label,
            "yAxisLabel": self.y_axis_label,
            "xAxisType": self.x_axis_type,
            "yAxisType": self.y_axis_type,
            "showLegend": self.show_legend,
            "legendPosition": self.legend_position,
            "showGrid": self.show_grid,
            "showTooltip": self.show_tooltip,
            "animate": self.animate,
            "colors": self.colors,
            "stacked": self.stacked,
            "lineType": self.line_type,
            "showDots": self.show_dots,
            "horizontal": self.horizontal,
            "innerRadius": self.inner_radius,
        }


@dataclass
class TableConfig:
    """Configuração de tabelas."""
    columns: List[Dict[str, Any]] = field(default_factory=list)
    sortable: bool = True
    filterable: bool = True
    paginated: bool = True
    page_size: int = 10
    selectable: bool = False
    row_click_action: Optional[str] = None  # drill-down, modal, link
    
    # Conditional formatting
    conditional_formatting: List[Dict] = field(default_factory=list)
    
    # Export
    exportable: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["csv", "excel"])
    
    def to_dict(self) -> Dict:
        return {
            "columns": self.columns,
            "sortable": self.sortable,
            "filterable": self.filterable,
            "paginated": self.paginated,
            "pageSize": self.page_size,
            "selectable": self.selectable,
            "exportable": self.exportable,
        }


@dataclass
class MetricConfig:
    """Configuração de metric cards."""
    format: str = "number"  # number, percent, currency, duration, bytes
    precision: int = 2
    prefix: str = ""
    suffix: str = ""
    
    # Comparison
    show_comparison: bool = True
    comparison_period: str = "previous"  # previous, week_ago, month_ago
    comparison_format: str = "percent"
    
    # Sparkline
    show_sparkline: bool = True
    sparkline_period: str = "7d"
    
    # Thresholds
    thresholds: List[Dict[str, Any]] = field(default_factory=list)
    # [{"value": 90, "color": "green"}, {"value": 70, "color": "yellow"}]
    
    def to_dict(self) -> Dict:
        return {
            "format": self.format,
            "precision": self.precision,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "showComparison": self.show_comparison,
            "comparisonPeriod": self.comparison_period,
            "showSparkline": self.show_sparkline,
            "thresholds": self.thresholds,
        }


@dataclass
class GaugeConfig:
    """Configuração de gauges."""
    min_value: float = 0
    max_value: float = 100
    thresholds: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"value": 70, "color": "#22c55e"},
        {"value": 90, "color": "#eab308"},
        {"value": 100, "color": "#ef4444"}
    ])
    show_value: bool = True
    show_min_max: bool = True
    arc_width: int = 20
    
    def to_dict(self) -> Dict:
        return {
            "minValue": self.min_value,
            "maxValue": self.max_value,
            "thresholds": self.thresholds,
            "showValue": self.show_value,
            "showMinMax": self.show_min_max,
            "arcWidth": self.arc_width,
        }


@dataclass
class WidgetConfig:
    """Configuração completa de um widget."""
    # Tipo específico
    chart: Optional[ChartConfig] = None
    table: Optional[TableConfig] = None
    metric: Optional[MetricConfig] = None
    gauge: Optional[GaugeConfig] = None
    
    # Content (para markdown, iframe, etc)
    content: str = ""
    url: str = ""
    
    # Filters
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Time range (pode sobrescrever dashboard)
    time_range: Optional[str] = None
    
    # Drill-down
    drill_down_enabled: bool = False
    drill_down_dashboard_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "filters": self.filters,
            "drillDownEnabled": self.drill_down_enabled,
        }
        
        if self.chart:
            result["chart"] = self.chart.to_dict()
        if self.table:
            result["table"] = self.table.to_dict()
        if self.metric:
            result["metric"] = self.metric.to_dict()
        if self.gauge:
            result["gauge"] = self.gauge.to_dict()
        if self.content:
            result["content"] = self.content
        if self.url:
            result["url"] = self.url
        
        return result


@dataclass
class WidgetState:
    """Estado runtime de um widget."""
    loading: bool = False
    error: Optional[str] = None
    last_updated: Optional[datetime] = None
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict:
        return {
            "loading": self.loading,
            "error": self.error,
            "lastUpdated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class Widget:
    """
    Widget de dashboard.
    
    Unidade visual configurável que exibe dados de uma fonte.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificação
    title: str = "Untitled Widget"
    description: str = ""
    type: WidgetType = WidgetType.METRIC_CARD
    
    # Data
    data_source_id: str = ""
    query: str = ""  # Query para data source
    
    # Layout
    position: Optional["GridPosition"] = None
    size: WidgetSize = WidgetSize.MEDIUM
    
    # Config
    config: WidgetConfig = field(default_factory=WidgetConfig)
    
    # Refresh
    refresh_interval: RefreshInterval = RefreshInterval.MINUTE_1
    
    # State
    state: WidgetState = field(default_factory=WidgetState)
    
    # Visibility
    visible: bool = True
    collapsed: bool = False
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "dataSourceId": self.data_source_id,
            "query": self.query,
            "position": self.position.to_dict() if self.position else None,
            "size": self.size.value,
            "config": self.config.to_dict(),
            "refreshInterval": self.refresh_interval.value,
            "state": self.state.to_dict(),
            "visible": self.visible,
            "collapsed": self.collapsed,
            "tags": self.tags,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
    
    @classmethod
    def metric_card(
        cls,
        title: str,
        query: str,
        data_source_id: str,
        **kwargs
    ) -> "Widget":
        """Cria widget de metric card."""
        return cls(
            title=title,
            type=WidgetType.METRIC_CARD,
            query=query,
            data_source_id=data_source_id,
            config=WidgetConfig(metric=MetricConfig()),
            **kwargs
        )
    
    @classmethod
    def line_chart(
        cls,
        title: str,
        query: str,
        data_source_id: str,
        **kwargs
    ) -> "Widget":
        """Cria widget de line chart."""
        return cls(
            title=title,
            type=WidgetType.LINE_CHART,
            query=query,
            data_source_id=data_source_id,
            size=WidgetSize.LARGE,
            config=WidgetConfig(chart=ChartConfig()),
            **kwargs
        )
    
    @classmethod
    def table(
        cls,
        title: str,
        query: str,
        data_source_id: str,
        columns: List[Dict],
        **kwargs
    ) -> "Widget":
        """Cria widget de tabela."""
        return cls(
            title=title,
            type=WidgetType.TABLE,
            query=query,
            data_source_id=data_source_id,
            size=WidgetSize.LARGE,
            config=WidgetConfig(table=TableConfig(columns=columns)),
            **kwargs
        )


# Importar GridPosition depois para evitar circular
from .layouts import GridPosition

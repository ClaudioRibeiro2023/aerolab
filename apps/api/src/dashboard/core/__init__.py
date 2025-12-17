"""
Dashboard Core - Entidades fundamentais.
"""

from .widgets import Widget, WidgetType, WidgetConfig, WidgetState
from .layouts import Layout, LayoutType, GridPosition, LayoutItem
from .datasources import DataSource, DataSourceType, DataSourceConfig
from .themes import Theme, ThemeConfig
from .permissions import DashboardPermission, WidgetPermission

__all__ = [
    "Widget",
    "WidgetType",
    "WidgetConfig",
    "WidgetState",
    "Layout",
    "LayoutType",
    "GridPosition",
    "LayoutItem",
    "DataSource",
    "DataSourceType",
    "DataSourceConfig",
    "Theme",
    "ThemeConfig",
    "DashboardPermission",
    "WidgetPermission",
]

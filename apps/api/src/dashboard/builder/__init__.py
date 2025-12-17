"""
Dashboard Builder - Construtor visual de dashboards.

Features:
- Drag & drop de widgets
- Configuração visual de queries
- Templates pré-definidos
- Exportação/Importação
"""

from .templates import DashboardTemplate, TemplateManager, get_template_manager
from .config import WidgetConfigBuilder, QueryBuilder
from .export import DashboardExporter, DashboardImporter

__all__ = [
    "DashboardTemplate",
    "TemplateManager",
    "get_template_manager",
    "WidgetConfigBuilder",
    "QueryBuilder",
    "DashboardExporter",
    "DashboardImporter",
]

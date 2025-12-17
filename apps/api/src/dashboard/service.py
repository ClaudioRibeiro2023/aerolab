"""
Dashboard Service - Serviço principal do módulo de dashboards.

Orquestra todas as operações de dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import logging

from .core.widgets import Widget, WidgetType, WidgetConfig
from .core.layouts import Layout, LayoutType, GridPosition
from .core.datasources import DataSource, get_datasource_registry
from .core.themes import Theme, get_theme
from .core.permissions import DashboardPermission, get_permission_manager

logger = logging.getLogger(__name__)


@dataclass
class Dashboard:
    """
    Dashboard completo.
    
    Contém widgets, layout e configurações.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificação
    name: str = "Untitled Dashboard"
    description: str = ""
    slug: str = ""
    
    # Conteúdo
    widgets: List[Widget] = field(default_factory=list)
    layout: Layout = field(default_factory=Layout)
    
    # Tema
    theme_id: Optional[str] = None
    
    # Time range
    default_time_range: str = "24h"
    time_zone: str = "America/Sao_Paulo"
    
    # Refresh
    auto_refresh: bool = True
    refresh_interval_seconds: int = 60
    
    # Filters
    global_filters: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Organization
    folder_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    # Status
    is_favorite: bool = False
    is_template: bool = False
    is_published: bool = False
    
    def add_widget(self, widget: Widget) -> None:
        """Adiciona widget ao dashboard."""
        self.widgets.append(widget)
        self.layout.add_widget(widget.id)
        self.updated_at = datetime.now()
        self.version += 1
    
    def remove_widget(self, widget_id: str) -> bool:
        """Remove widget do dashboard."""
        initial_len = len(self.widgets)
        self.widgets = [w for w in self.widgets if w.id != widget_id]
        
        if len(self.widgets) < initial_len:
            self.layout.remove_widget(widget_id)
            self.updated_at = datetime.now()
            self.version += 1
            return True
        return False
    
    def get_widget(self, widget_id: str) -> Optional[Widget]:
        """Obtém widget por ID."""
        for widget in self.widgets:
            if widget.id == widget_id:
                return widget
        return None
    
    def update_widget(self, widget_id: str, **kwargs) -> Optional[Widget]:
        """Atualiza widget."""
        widget = self.get_widget(widget_id)
        if widget:
            for key, value in kwargs.items():
                if hasattr(widget, key):
                    setattr(widget, key, value)
            widget.updated_at = datetime.now()
            self.updated_at = datetime.now()
            self.version += 1
        return widget
    
    def duplicate_widget(self, widget_id: str) -> Optional[Widget]:
        """Duplica widget."""
        original = self.get_widget(widget_id)
        if not original:
            return None
        
        # Criar cópia
        new_widget = Widget(
            title=f"{original.title} (Copy)",
            description=original.description,
            type=original.type,
            data_source_id=original.data_source_id,
            query=original.query,
            config=original.config,
            refresh_interval=original.refresh_interval,
            tags=original.tags.copy()
        )
        
        self.add_widget(new_widget)
        return new_widget
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "widgets": [w.to_dict() for w in self.widgets],
            "layout": self.layout.to_dict(),
            "themeId": self.theme_id,
            "defaultTimeRange": self.default_time_range,
            "timeZone": self.time_zone,
            "autoRefresh": self.auto_refresh,
            "refreshIntervalSeconds": self.refresh_interval_seconds,
            "globalFilters": self.global_filters,
            "variables": self.variables,
            "folderId": self.folder_id,
            "tags": self.tags,
            "version": self.version,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "createdBy": self.created_by,
            "isFavorite": self.is_favorite,
            "isTemplate": self.is_template,
            "isPublished": self.is_published,
        }
    
    @classmethod
    def from_template(cls, template: "Dashboard", name: str, created_by: str) -> "Dashboard":
        """Cria dashboard a partir de template."""
        return cls(
            name=name,
            description=f"Created from template: {template.name}",
            widgets=[
                Widget(
                    title=w.title,
                    type=w.type,
                    data_source_id=w.data_source_id,
                    query=w.query,
                    config=w.config
                )
                for w in template.widgets
            ],
            layout=Layout(
                type=template.layout.type,
                config=template.layout.config
            ),
            theme_id=template.theme_id,
            default_time_range=template.default_time_range,
            created_by=created_by
        )


@dataclass
class DashboardFolder:
    """Pasta para organizar dashboards."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Folder"
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "parentId": self.parent_id,
            "createdAt": self.created_at.isoformat(),
        }


class DashboardService:
    """
    Serviço principal de dashboards.
    
    Gerencia CRUD de dashboards, widgets e configurações.
    """
    
    def __init__(self):
        self._dashboards: Dict[str, Dashboard] = {}
        self._folders: Dict[str, DashboardFolder] = {}
        self._favorites: Dict[str, List[str]] = {}  # user_id -> dashboard_ids
        self._initialized = False
    
    async def initialize(self) -> None:
        """Inicializa o serviço."""
        if self._initialized:
            return
        
        # Criar dashboards padrão
        await self._create_default_dashboards()
        
        self._initialized = True
        logger.info("Dashboard service initialized")
    
    async def _create_default_dashboards(self) -> None:
        """Cria dashboards padrão."""
        # Overview Dashboard
        overview = Dashboard(
            name="Overview",
            slug="overview",
            description="Visão geral do sistema",
            is_published=True
        )
        
        # Adicionar widgets
        overview.add_widget(Widget.metric_card(
            title="Total Executions",
            query="sum(agent_executions_total)",
            data_source_id="system"
        ))
        
        overview.add_widget(Widget.metric_card(
            title="Success Rate",
            query="avg(agent_success_rate)",
            data_source_id="system"
        ))
        
        overview.add_widget(Widget.metric_card(
            title="Active Agents",
            query="count(active_agents)",
            data_source_id="system"
        ))
        
        overview.add_widget(Widget.metric_card(
            title="Total Cost",
            query="sum(total_cost_usd)",
            data_source_id="system"
        ))
        
        self._dashboards[overview.id] = overview
    
    # Dashboard CRUD
    async def create_dashboard(
        self,
        name: str,
        description: str = "",
        created_by: str = "",
        template_id: Optional[str] = None
    ) -> Dashboard:
        """Cria novo dashboard."""
        if template_id:
            template = self._dashboards.get(template_id)
            if template and template.is_template:
                dashboard = Dashboard.from_template(template, name, created_by)
            else:
                dashboard = Dashboard(name=name, description=description, created_by=created_by)
        else:
            dashboard = Dashboard(name=name, description=description, created_by=created_by)
        
        # Gerar slug
        dashboard.slug = name.lower().replace(" ", "-")
        
        self._dashboards[dashboard.id] = dashboard
        logger.info(f"Created dashboard: {dashboard.name}")
        
        return dashboard
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Obtém dashboard por ID."""
        return self._dashboards.get(dashboard_id)
    
    async def get_dashboard_by_slug(self, slug: str) -> Optional[Dashboard]:
        """Obtém dashboard por slug."""
        for dashboard in self._dashboards.values():
            if dashboard.slug == slug:
                return dashboard
        return None
    
    async def update_dashboard(
        self,
        dashboard_id: str,
        **kwargs
    ) -> Optional[Dashboard]:
        """Atualiza dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        for key, value in kwargs.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)
        
        dashboard.updated_at = datetime.now()
        dashboard.version += 1
        
        return dashboard
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Deleta dashboard."""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            logger.info(f"Deleted dashboard: {dashboard_id}")
            return True
        return False
    
    async def list_dashboards(
        self,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_templates: bool = False
    ) -> List[Dashboard]:
        """Lista dashboards."""
        dashboards = list(self._dashboards.values())
        
        # Filtrar por pasta
        if folder_id:
            dashboards = [d for d in dashboards if d.folder_id == folder_id]
        
        # Filtrar templates
        if not include_templates:
            dashboards = [d for d in dashboards if not d.is_template]
        
        # Filtrar por tags
        if tags:
            dashboards = [
                d for d in dashboards
                if any(tag in d.tags for tag in tags)
            ]
        
        # Ordenar por favorito e nome
        if user_id:
            user_favorites = self._favorites.get(user_id, [])
            dashboards.sort(key=lambda d: (d.id not in user_favorites, d.name))
        else:
            dashboards.sort(key=lambda d: d.name)
        
        return dashboards
    
    # Widget operations
    async def add_widget(
        self,
        dashboard_id: str,
        widget: Widget
    ) -> Optional[Dashboard]:
        """Adiciona widget a dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard:
            dashboard.add_widget(widget)
        return dashboard
    
    async def remove_widget(
        self,
        dashboard_id: str,
        widget_id: str
    ) -> Optional[Dashboard]:
        """Remove widget de dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard:
            dashboard.remove_widget(widget_id)
        return dashboard
    
    async def update_widget(
        self,
        dashboard_id: str,
        widget_id: str,
        **kwargs
    ) -> Optional[Widget]:
        """Atualiza widget."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard:
            return dashboard.update_widget(widget_id, **kwargs)
        return None
    
    # Layout operations
    async def update_layout(
        self,
        dashboard_id: str,
        layout_items: List[Dict]
    ) -> Optional[Dashboard]:
        """Atualiza layout de dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        for item in layout_items:
            widget_id = item.get("widgetId")
            position = item.get("position", {})
            
            if widget_id:
                dashboard.layout.move_widget(
                    widget_id,
                    position.get("x", 0),
                    position.get("y", 0)
                )
                dashboard.layout.resize_widget(
                    widget_id,
                    position.get("w", 2),
                    position.get("h", 1)
                )
        
        dashboard.updated_at = datetime.now()
        dashboard.version += 1
        
        return dashboard
    
    # Query execution
    async def execute_widget_query(
        self,
        dashboard_id: str,
        widget_id: str,
        time_range: Optional[Dict] = None
    ) -> Dict:
        """Executa query de um widget."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return {"error": "Dashboard not found"}
        
        widget = dashboard.get_widget(widget_id)
        if not widget:
            return {"error": "Widget not found"}
        
        # Obter data source
        registry = get_datasource_registry()
        data_source = registry.get(widget.data_source_id)
        
        if not data_source:
            # Usar data source padrão
            data_source = registry.get_by_type(
                DataSource.DataSourceType.AGENT_METRICS
            )[0] if registry.get_by_type(DataSource.DataSourceType.AGENT_METRICS) else None
        
        if not data_source:
            return {"error": "Data source not found"}
        
        # Executar query
        result = await data_source.query(
            widget.query,
            params=widget.config.filters,
            time_range=time_range or {"range": dashboard.default_time_range}
        )
        
        return result.to_dict()
    
    async def execute_all_queries(
        self,
        dashboard_id: str,
        time_range: Optional[Dict] = None
    ) -> Dict[str, Dict]:
        """Executa queries de todos os widgets."""
        dashboard = self._dashboards.get(dashboard_id)
        if not dashboard:
            return {}
        
        results = {}
        for widget in dashboard.widgets:
            results[widget.id] = await self.execute_widget_query(
                dashboard_id,
                widget.id,
                time_range
            )
        
        return results
    
    # Favorites
    async def toggle_favorite(
        self,
        user_id: str,
        dashboard_id: str
    ) -> bool:
        """Toggle favorito."""
        if user_id not in self._favorites:
            self._favorites[user_id] = []
        
        if dashboard_id in self._favorites[user_id]:
            self._favorites[user_id].remove(dashboard_id)
            return False
        else:
            self._favorites[user_id].append(dashboard_id)
            return True
    
    # Folders
    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        created_by: str = ""
    ) -> DashboardFolder:
        """Cria pasta."""
        folder = DashboardFolder(
            name=name,
            parent_id=parent_id,
            created_by=created_by
        )
        self._folders[folder.id] = folder
        return folder
    
    async def list_folders(self) -> List[DashboardFolder]:
        """Lista pastas."""
        return list(self._folders.values())
    
    # Templates
    async def list_templates(self) -> List[Dashboard]:
        """Lista templates disponíveis."""
        return [d for d in self._dashboards.values() if d.is_template]
    
    async def create_from_template(
        self,
        template_id: str,
        name: str,
        created_by: str
    ) -> Optional[Dashboard]:
        """Cria dashboard a partir de template."""
        return await self.create_dashboard(
            name=name,
            created_by=created_by,
            template_id=template_id
        )
    
    # Export/Import
    async def export_dashboard(self, dashboard_id: str) -> Optional[Dict]:
        """Exporta dashboard como JSON."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard:
            return dashboard.to_dict()
        return None
    
    async def import_dashboard(
        self,
        data: Dict,
        created_by: str
    ) -> Dashboard:
        """Importa dashboard de JSON."""
        dashboard = Dashboard(
            name=data.get("name", "Imported Dashboard"),
            description=data.get("description", ""),
            created_by=created_by
        )
        
        # Reconstruir widgets
        for widget_data in data.get("widgets", []):
            widget = Widget(
                title=widget_data.get("title", ""),
                type=WidgetType(widget_data.get("type", "metric_card")),
                query=widget_data.get("query", ""),
                data_source_id=widget_data.get("dataSourceId", "")
            )
            dashboard.add_widget(widget)
        
        self._dashboards[dashboard.id] = dashboard
        return dashboard


# Singleton
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Obtém serviço de dashboards."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service

"""
Permissions - Controle de acesso para dashboards.

Suporta RBAC granular para dashboards e widgets.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import uuid


class PermissionLevel(str, Enum):
    """Níveis de permissão."""
    NONE = "none"
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"
    OWNER = "owner"


class ResourceType(str, Enum):
    """Tipos de recursos."""
    DASHBOARD = "dashboard"
    WIDGET = "widget"
    DATA_SOURCE = "data_source"
    ALERT = "alert"
    REPORT = "report"


@dataclass
class Permission:
    """Permissão individual."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Subject (quem)
    user_id: Optional[str] = None
    role: Optional[str] = None  # admin, analyst, viewer
    team_id: Optional[str] = None
    
    # Resource (o quê)
    resource_type: ResourceType = ResourceType.DASHBOARD
    resource_id: str = ""
    
    # Permission level
    level: PermissionLevel = PermissionLevel.VIEW
    
    # Specific permissions
    can_view: bool = True
    can_edit: bool = False
    can_delete: bool = False
    can_share: bool = False
    can_export: bool = True
    
    # Timestamps
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: str = ""
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Verifica se permissão expirou."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def has_permission(self, action: str) -> bool:
        """Verifica se tem permissão para ação."""
        if self.is_expired():
            return False
        
        action_map = {
            "view": self.can_view,
            "edit": self.can_edit,
            "delete": self.can_delete,
            "share": self.can_share,
            "export": self.can_export,
        }
        
        return action_map.get(action, False)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "role": self.role,
            "teamId": self.team_id,
            "resourceType": self.resource_type.value,
            "resourceId": self.resource_id,
            "level": self.level.value,
            "canView": self.can_view,
            "canEdit": self.can_edit,
            "canDelete": self.can_delete,
            "canShare": self.can_share,
            "canExport": self.can_export,
            "grantedAt": self.granted_at.isoformat(),
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class DashboardPermission:
    """Permissões de um dashboard."""
    dashboard_id: str = ""
    owner_id: str = ""
    
    # Visibility
    is_public: bool = False
    is_organization_wide: bool = False
    
    # Permissions
    permissions: List[Permission] = field(default_factory=list)
    
    # Default for new viewers
    default_level: PermissionLevel = PermissionLevel.VIEW
    
    def add_permission(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        team_id: Optional[str] = None,
        level: PermissionLevel = PermissionLevel.VIEW,
        granted_by: str = ""
    ) -> Permission:
        """Adiciona permissão."""
        permission = Permission(
            user_id=user_id,
            role=role,
            team_id=team_id,
            resource_type=ResourceType.DASHBOARD,
            resource_id=self.dashboard_id,
            level=level,
            can_view=level in (PermissionLevel.VIEW, PermissionLevel.EDIT, PermissionLevel.ADMIN, PermissionLevel.OWNER),
            can_edit=level in (PermissionLevel.EDIT, PermissionLevel.ADMIN, PermissionLevel.OWNER),
            can_delete=level in (PermissionLevel.ADMIN, PermissionLevel.OWNER),
            can_share=level in (PermissionLevel.ADMIN, PermissionLevel.OWNER),
            granted_by=granted_by
        )
        
        self.permissions.append(permission)
        return permission
    
    def remove_permission(self, permission_id: str) -> bool:
        """Remove permissão."""
        initial_len = len(self.permissions)
        self.permissions = [p for p in self.permissions if p.id != permission_id]
        return len(self.permissions) < initial_len
    
    def check_access(
        self,
        user_id: str,
        user_roles: List[str],
        user_teams: List[str],
        action: str = "view"
    ) -> bool:
        """Verifica se usuário tem acesso."""
        # Owner sempre tem acesso
        if user_id == self.owner_id:
            return True
        
        # Público
        if self.is_public and action == "view":
            return True
        
        # Verificar permissões
        for perm in self.permissions:
            if perm.is_expired():
                continue
            
            # Por user
            if perm.user_id and perm.user_id == user_id:
                if perm.has_permission(action):
                    return True
            
            # Por role
            if perm.role and perm.role in user_roles:
                if perm.has_permission(action):
                    return True
            
            # Por team
            if perm.team_id and perm.team_id in user_teams:
                if perm.has_permission(action):
                    return True
        
        return False
    
    def get_effective_level(
        self,
        user_id: str,
        user_roles: List[str],
        user_teams: List[str]
    ) -> PermissionLevel:
        """Obtém nível efetivo de permissão."""
        if user_id == self.owner_id:
            return PermissionLevel.OWNER
        
        highest_level = PermissionLevel.NONE
        level_order = [
            PermissionLevel.NONE,
            PermissionLevel.VIEW,
            PermissionLevel.EDIT,
            PermissionLevel.ADMIN,
            PermissionLevel.OWNER
        ]
        
        for perm in self.permissions:
            if perm.is_expired():
                continue
            
            matches = False
            if perm.user_id and perm.user_id == user_id:
                matches = True
            elif perm.role and perm.role in user_roles:
                matches = True
            elif perm.team_id and perm.team_id in user_teams:
                matches = True
            
            if matches:
                if level_order.index(perm.level) > level_order.index(highest_level):
                    highest_level = perm.level
        
        return highest_level
    
    def to_dict(self) -> Dict:
        return {
            "dashboardId": self.dashboard_id,
            "ownerId": self.owner_id,
            "isPublic": self.is_public,
            "isOrganizationWide": self.is_organization_wide,
            "permissions": [p.to_dict() for p in self.permissions],
            "defaultLevel": self.default_level.value,
        }


@dataclass
class WidgetPermission:
    """Permissões de um widget individual."""
    widget_id: str = ""
    
    # Inherit from dashboard
    inherit_from_dashboard: bool = True
    
    # Override permissions
    override_permissions: List[Permission] = field(default_factory=list)
    
    # Specific restrictions
    hidden_for_roles: List[str] = field(default_factory=list)
    hidden_for_users: List[str] = field(default_factory=list)
    
    def is_visible(
        self,
        user_id: str,
        user_roles: List[str]
    ) -> bool:
        """Verifica se widget é visível."""
        if user_id in self.hidden_for_users:
            return False
        
        for role in user_roles:
            if role in self.hidden_for_roles:
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        return {
            "widgetId": self.widget_id,
            "inheritFromDashboard": self.inherit_from_dashboard,
            "hiddenForRoles": self.hidden_for_roles,
            "hiddenForUsers": self.hidden_for_users,
        }


class PermissionManager:
    """Gerenciador de permissões."""
    
    def __init__(self):
        self._dashboard_permissions: Dict[str, DashboardPermission] = {}
        self._widget_permissions: Dict[str, WidgetPermission] = {}
    
    def get_dashboard_permission(
        self,
        dashboard_id: str
    ) -> Optional[DashboardPermission]:
        """Obtém permissões de dashboard."""
        return self._dashboard_permissions.get(dashboard_id)
    
    def set_dashboard_permission(
        self,
        permission: DashboardPermission
    ) -> None:
        """Define permissões de dashboard."""
        self._dashboard_permissions[permission.dashboard_id] = permission
    
    def check_dashboard_access(
        self,
        dashboard_id: str,
        user_id: str,
        user_roles: List[str] = None,
        user_teams: List[str] = None,
        action: str = "view"
    ) -> bool:
        """Verifica acesso a dashboard."""
        perm = self._dashboard_permissions.get(dashboard_id)
        if not perm:
            return True  # Sem permissão definida = acesso permitido
        
        return perm.check_access(
            user_id=user_id,
            user_roles=user_roles or [],
            user_teams=user_teams or [],
            action=action
        )
    
    def list_accessible_dashboards(
        self,
        user_id: str,
        user_roles: List[str] = None,
        user_teams: List[str] = None,
        all_dashboard_ids: List[str] = None
    ) -> List[str]:
        """Lista dashboards acessíveis."""
        if all_dashboard_ids is None:
            all_dashboard_ids = list(self._dashboard_permissions.keys())
        
        accessible = []
        for dash_id in all_dashboard_ids:
            if self.check_dashboard_access(
                dash_id,
                user_id,
                user_roles,
                user_teams
            ):
                accessible.append(dash_id)
        
        return accessible


# Singleton
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Obtém gerenciador de permissões."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager

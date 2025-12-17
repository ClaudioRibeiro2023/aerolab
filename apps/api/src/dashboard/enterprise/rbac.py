"""
RBAC - Role-Based Access Control para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Tipos de recursos."""
    DASHBOARD = "dashboard"
    WIDGET = "widget"
    DATASOURCE = "datasource"
    ALERT = "alert"
    FOLDER = "folder"
    TEMPLATE = "template"
    REPORT = "report"


class Action(str, Enum):
    """Ações sobre recursos."""
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"
    EXPORT = "export"
    ADMIN = "admin"


@dataclass
class Permission:
    """Permissão de acesso."""
    resource_type: ResourceType
    action: Action
    resource_id: Optional[str] = None  # None = todos os recursos do tipo
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def matches(
        self,
        resource_type: ResourceType,
        action: Action,
        resource_id: Optional[str] = None,
    ) -> bool:
        """Verifica se permissão aplica."""
        if self.resource_type != resource_type:
            return False
        
        if self.action != action and self.action != Action.ADMIN:
            return False
        
        if self.resource_id and resource_id and self.resource_id != resource_id:
            return False
        
        return True
    
    def to_dict(self) -> Dict:
        return {
            "resourceType": self.resource_type.value,
            "action": self.action.value,
            "resourceId": self.resource_id,
            "conditions": self.conditions,
        }


@dataclass
class Role:
    """Role com conjunto de permissões."""
    id: str
    name: str
    description: str = ""
    
    # Permissões
    permissions: List[Permission] = field(default_factory=list)
    
    # Hierarquia
    parent_role_id: Optional[str] = None
    
    # Metadata
    is_system: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(
        self,
        resource_type: ResourceType,
        action: Action,
        resource_id: Optional[str] = None,
    ) -> bool:
        """Verifica se role tem permissão."""
        return any(
            p.matches(resource_type, action, resource_id)
            for p in self.permissions
        )
    
    def add_permission(self, permission: Permission):
        """Adiciona permissão."""
        self.permissions.append(permission)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "parentRoleId": self.parent_role_id,
            "isSystem": self.is_system,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass
class UserRoleAssignment:
    """Atribuição de role a usuário."""
    user_id: str
    role_id: str
    tenant_id: Optional[str] = None
    scope: Optional[str] = None  # folder_id, dashboard_id, etc
    assigned_at: datetime = field(default_factory=datetime.now)
    assigned_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class RBACManager:
    """
    Gerenciador de RBAC.
    
    Controla permissões baseadas em roles para recursos de dashboard.
    """
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._assignments: List[UserRoleAssignment] = []
        self._user_cache: Dict[str, Set[str]] = {}  # user_id -> role_ids
        
        self._load_system_roles()
    
    def _load_system_roles(self):
        """Carrega roles padrão do sistema."""
        # Viewer - apenas visualização
        viewer = Role(
            id="viewer",
            name="Viewer",
            description="Can view dashboards and widgets",
            is_system=True,
            permissions=[
                Permission(ResourceType.DASHBOARD, Action.VIEW),
                Permission(ResourceType.WIDGET, Action.VIEW),
                Permission(ResourceType.FOLDER, Action.VIEW),
            ]
        )
        self._roles["viewer"] = viewer
        
        # Editor - pode editar
        editor = Role(
            id="editor",
            name="Editor",
            description="Can create and edit dashboards",
            is_system=True,
            parent_role_id="viewer",
            permissions=[
                Permission(ResourceType.DASHBOARD, Action.VIEW),
                Permission(ResourceType.DASHBOARD, Action.CREATE),
                Permission(ResourceType.DASHBOARD, Action.EDIT),
                Permission(ResourceType.WIDGET, Action.VIEW),
                Permission(ResourceType.WIDGET, Action.CREATE),
                Permission(ResourceType.WIDGET, Action.EDIT),
                Permission(ResourceType.FOLDER, Action.VIEW),
                Permission(ResourceType.FOLDER, Action.CREATE),
                Permission(ResourceType.ALERT, Action.VIEW),
                Permission(ResourceType.ALERT, Action.CREATE),
            ]
        )
        self._roles["editor"] = editor
        
        # Admin - acesso total
        admin = Role(
            id="admin",
            name="Admin",
            description="Full access to all resources",
            is_system=True,
            parent_role_id="editor",
            permissions=[
                Permission(ResourceType.DASHBOARD, Action.ADMIN),
                Permission(ResourceType.WIDGET, Action.ADMIN),
                Permission(ResourceType.DATASOURCE, Action.ADMIN),
                Permission(ResourceType.FOLDER, Action.ADMIN),
                Permission(ResourceType.ALERT, Action.ADMIN),
                Permission(ResourceType.TEMPLATE, Action.ADMIN),
                Permission(ResourceType.REPORT, Action.ADMIN),
            ]
        )
        self._roles["admin"] = admin
    
    def create_role(
        self,
        role_id: str,
        name: str,
        description: str = "",
        permissions: Optional[List[Permission]] = None,
        parent_role_id: Optional[str] = None,
    ) -> Role:
        """Cria nova role."""
        if role_id in self._roles:
            raise ValueError(f"Role {role_id} already exists")
        
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions or [],
            parent_role_id=parent_role_id,
        )
        
        self._roles[role_id] = role
        logger.info(f"Created role: {role_id}")
        return role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Obtém role por ID."""
        return self._roles.get(role_id)
    
    def list_roles(self) -> List[Role]:
        """Lista todas as roles."""
        return list(self._roles.values())
    
    def assign_role(
        self,
        user_id: str,
        role_id: str,
        tenant_id: Optional[str] = None,
        scope: Optional[str] = None,
        assigned_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserRoleAssignment:
        """Atribui role a usuário."""
        if role_id not in self._roles:
            raise ValueError(f"Role {role_id} not found")
        
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            scope=scope,
            assigned_by=assigned_by,
            expires_at=expires_at,
        )
        
        self._assignments.append(assignment)
        self._invalidate_cache(user_id)
        
        logger.info(f"Assigned role {role_id} to user {user_id}")
        return assignment
    
    def revoke_role(
        self,
        user_id: str,
        role_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Revoga role de usuário."""
        initial_count = len(self._assignments)
        
        self._assignments = [
            a for a in self._assignments
            if not (
                a.user_id == user_id and
                a.role_id == role_id and
                (tenant_id is None or a.tenant_id == tenant_id)
            )
        ]
        
        self._invalidate_cache(user_id)
        
        revoked = len(self._assignments) < initial_count
        if revoked:
            logger.info(f"Revoked role {role_id} from user {user_id}")
        
        return revoked
    
    def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Role]:
        """Obtém roles de um usuário."""
        role_ids = self._get_user_role_ids(user_id, tenant_id)
        return [self._roles[rid] for rid in role_ids if rid in self._roles]
    
    def _get_user_role_ids(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> Set[str]:
        """Obtém IDs de roles de um usuário."""
        cache_key = f"{user_id}:{tenant_id or 'global'}"
        
        if cache_key in self._user_cache:
            return self._user_cache[cache_key]
        
        now = datetime.now()
        role_ids = set()
        
        for assignment in self._assignments:
            if assignment.user_id != user_id:
                continue
            
            if tenant_id and assignment.tenant_id and assignment.tenant_id != tenant_id:
                continue
            
            if assignment.expires_at and assignment.expires_at < now:
                continue
            
            role_ids.add(assignment.role_id)
            
            # Adicionar roles pai
            role = self._roles.get(assignment.role_id)
            while role and role.parent_role_id:
                role_ids.add(role.parent_role_id)
                role = self._roles.get(role.parent_role_id)
        
        self._user_cache[cache_key] = role_ids
        return role_ids
    
    def check_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        action: Action,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Verifica se usuário tem permissão."""
        roles = self.get_user_roles(user_id, tenant_id)
        
        for role in roles:
            if role.has_permission(resource_type, action, resource_id):
                return True
        
        return False
    
    def get_user_permissions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Permission]:
        """Obtém todas as permissões de um usuário."""
        roles = self.get_user_roles(user_id, tenant_id)
        
        permissions = []
        for role in roles:
            permissions.extend(role.permissions)
        
        return permissions
    
    def _invalidate_cache(self, user_id: str):
        """Invalida cache de usuário."""
        keys_to_remove = [k for k in self._user_cache if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._user_cache[key]


# Singleton
_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Obtém gerenciador de RBAC."""
    global _manager
    if _manager is None:
        _manager = RBACManager()
    return _manager

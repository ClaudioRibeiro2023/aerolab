"""
Sistema Multi-tenancy para isolamento de dados entre organizações.

Features:
- Isolamento de dados por tenant
- Configurações por organização
- Quotas e limites
- Custom branding
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json


class TenantPlan(Enum):
    """Planos disponíveis."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class TenantQuotas:
    """Quotas por plano."""
    max_agents: int = 5
    max_teams: int = 2
    max_workflows: int = 5
    max_executions_day: int = 100
    max_tokens_month: int = 100000
    max_users: int = 3
    max_storage_mb: int = 100
    
    @classmethod
    def for_plan(cls, plan: TenantPlan) -> "TenantQuotas":
        """Retorna quotas para um plano."""
        quotas = {
            TenantPlan.FREE: cls(
                max_agents=3,
                max_teams=1,
                max_workflows=2,
                max_executions_day=50,
                max_tokens_month=50000,
                max_users=2,
                max_storage_mb=50
            ),
            TenantPlan.STARTER: cls(
                max_agents=10,
                max_teams=5,
                max_workflows=10,
                max_executions_day=500,
                max_tokens_month=500000,
                max_users=10,
                max_storage_mb=500
            ),
            TenantPlan.PRO: cls(
                max_agents=50,
                max_teams=20,
                max_workflows=50,
                max_executions_day=5000,
                max_tokens_month=5000000,
                max_users=50,
                max_storage_mb=5000
            ),
            TenantPlan.ENTERPRISE: cls(
                max_agents=-1,  # Ilimitado
                max_teams=-1,
                max_workflows=-1,
                max_executions_day=-1,
                max_tokens_month=-1,
                max_users=-1,
                max_storage_mb=-1
            ),
        }
        return quotas.get(plan, cls())


@dataclass
class TenantBranding:
    """Configurações de branding."""
    logo_url: Optional[str] = None
    primary_color: str = "#3b82f6"
    secondary_color: str = "#1e40af"
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None
    email_header: Optional[str] = None
    email_footer: Optional[str] = None


@dataclass
class Tenant:
    """Representa uma organização/tenant."""
    id: str
    name: str
    slug: str
    plan: TenantPlan
    owner_id: str
    created_at: datetime
    settings: Dict[str, Any] = field(default_factory=dict)
    branding: TenantBranding = field(default_factory=TenantBranding)
    quotas: TenantQuotas = field(default_factory=TenantQuotas)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "plan": self.plan.value,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "settings": self.settings,
            "branding": asdict(self.branding),
            "quotas": asdict(self.quotas),
            "is_active": self.is_active,
        }


@dataclass
class TenantUser:
    """Usuário em um tenant."""
    user_id: str
    tenant_id: str
    role: str  # owner, admin, member, viewer
    permissions: List[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=datetime.utcnow)


class TenantManager:
    """
    Gerenciador de multi-tenancy.
    
    Features:
    - Criação e gestão de tenants
    - Associação de usuários
    - Verificação de quotas
    - Isolamento de contexto
    
    Configuração:
        MULTI_TENANT_ENABLED: Ativa multi-tenancy
        DEFAULT_TENANT_ID: Tenant padrão (single-tenant mode)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.enabled = os.getenv("MULTI_TENANT_ENABLED", "false").lower() == "true"
        self.default_tenant_id = os.getenv("DEFAULT_TENANT_ID", "default")
        self.storage_path = storage_path or os.getenv("TENANT_STORAGE_PATH", "./data/tenants")
        
        # Cache em memória
        self._tenants: Dict[str, Tenant] = {}
        self._user_tenants: Dict[str, List[str]] = {}  # user_id -> [tenant_ids]
        
        # Carregar dados
        self._load_data()
    
    def _load_data(self):
        """Carrega dados persistidos."""
        import os
        from pathlib import Path
        
        storage = Path(self.storage_path)
        if not storage.exists():
            storage.mkdir(parents=True, exist_ok=True)
            # Criar tenant padrão
            self._create_default_tenant()
            return
        
        tenants_file = storage / "tenants.json"
        if tenants_file.exists():
            data = json.loads(tenants_file.read_text())
            for t_data in data.get("tenants", []):
                tenant = Tenant(
                    id=t_data["id"],
                    name=t_data["name"],
                    slug=t_data["slug"],
                    plan=TenantPlan(t_data["plan"]),
                    owner_id=t_data["owner_id"],
                    created_at=datetime.fromisoformat(t_data["created_at"]),
                    settings=t_data.get("settings", {}),
                    branding=TenantBranding(**t_data.get("branding", {})),
                    quotas=TenantQuotas(**t_data.get("quotas", {})),
                    is_active=t_data.get("is_active", True),
                )
                self._tenants[tenant.id] = tenant
        else:
            self._create_default_tenant()
    
    def _create_default_tenant(self):
        """Cria tenant padrão."""
        default = Tenant(
            id=self.default_tenant_id,
            name="Default Organization",
            slug="default",
            plan=TenantPlan.PRO,
            owner_id="system",
            created_at=datetime.utcnow(),
            quotas=TenantQuotas.for_plan(TenantPlan.PRO),
        )
        self._tenants[default.id] = default
        self._save_data()
    
    def _save_data(self):
        """Persiste dados."""
        from pathlib import Path
        
        storage = Path(self.storage_path)
        storage.mkdir(parents=True, exist_ok=True)
        
        tenants_file = storage / "tenants.json"
        data = {
            "tenants": [t.to_dict() for t in self._tenants.values()]
        }
        tenants_file.write_text(json.dumps(data, indent=2))
    
    def create_tenant(
        self,
        name: str,
        owner_id: str,
        plan: TenantPlan = TenantPlan.FREE,
        slug: Optional[str] = None
    ) -> Tenant:
        """
        Cria um novo tenant.
        
        Args:
            name: Nome da organização
            owner_id: ID do usuário dono
            plan: Plano inicial
            slug: URL slug (gerado se não fornecido)
        """
        import re
        import uuid
        
        # Gerar slug
        if not slug:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        
        # Verificar unicidade
        existing_slugs = [t.slug for t in self._tenants.values()]
        if slug in existing_slugs:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            plan=plan,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            quotas=TenantQuotas.for_plan(plan),
        )
        
        self._tenants[tenant.id] = tenant
        
        # Associar owner
        if owner_id not in self._user_tenants:
            self._user_tenants[owner_id] = []
        self._user_tenants[owner_id].append(tenant.id)
        
        self._save_data()
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Obtém tenant por ID."""
        return self._tenants.get(tenant_id)
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Obtém tenant por slug."""
        for tenant in self._tenants.values():
            if tenant.slug == slug:
                return tenant
        return None
    
    def list_tenants(self, user_id: Optional[str] = None) -> List[Tenant]:
        """Lista tenants (opcionalmente filtrado por usuário)."""
        if user_id:
            tenant_ids = self._user_tenants.get(user_id, [])
            return [self._tenants[tid] for tid in tenant_ids if tid in self._tenants]
        return list(self._tenants.values())
    
    def update_tenant(
        self,
        tenant_id: str,
        **updates
    ) -> Optional[Tenant]:
        """Atualiza tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        self._save_data()
        return tenant
    
    def update_branding(
        self,
        tenant_id: str,
        branding: Dict[str, Any]
    ) -> Optional[Tenant]:
        """Atualiza branding do tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        tenant.branding = TenantBranding(**branding)
        self._save_data()
        return tenant
    
    def check_quota(
        self,
        tenant_id: str,
        resource: str,
        current_count: int
    ) -> bool:
        """
        Verifica se está dentro da quota.
        
        Args:
            tenant_id: ID do tenant
            resource: Nome do recurso (agents, teams, etc.)
            current_count: Contagem atual
        
        Returns:
            True se dentro da quota
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        quota_map = {
            "agents": tenant.quotas.max_agents,
            "teams": tenant.quotas.max_teams,
            "workflows": tenant.quotas.max_workflows,
            "users": tenant.quotas.max_users,
        }
        
        max_allowed = quota_map.get(resource, -1)
        if max_allowed == -1:  # Ilimitado
            return True
        
        return current_count < max_allowed
    
    def get_context_tenant_id(self, user_id: Optional[str] = None) -> str:
        """
        Obtém tenant ID para contexto atual.
        
        Em single-tenant mode, sempre retorna o default.
        Em multi-tenant, retorna baseado no usuário.
        """
        if not self.enabled:
            return self.default_tenant_id
        
        if user_id:
            user_tenants = self._user_tenants.get(user_id, [])
            if user_tenants:
                return user_tenants[0]  # Primeiro tenant do usuário
        
        return self.default_tenant_id


# Singleton
_tenant_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Obtém instância singleton do Tenant Manager."""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager

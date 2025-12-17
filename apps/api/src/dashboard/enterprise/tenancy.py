"""
Multi-Tenancy - Suporte multi-tenant para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TenantStatus(str, Enum):
    """Status do tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class TenantPlan(str, Enum):
    """Planos de tenant."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantLimits:
    """Limites do tenant."""
    max_dashboards: int = 10
    max_widgets_per_dashboard: int = 20
    max_users: int = 5
    max_datasources: int = 3
    max_alerts: int = 10
    retention_days: int = 30
    api_rate_limit: int = 1000  # requests/hour
    
    def to_dict(self) -> Dict:
        return {
            "maxDashboards": self.max_dashboards,
            "maxWidgetsPerDashboard": self.max_widgets_per_dashboard,
            "maxUsers": self.max_users,
            "maxDatasources": self.max_datasources,
            "maxAlerts": self.max_alerts,
            "retentionDays": self.retention_days,
            "apiRateLimit": self.api_rate_limit,
        }


@dataclass
class TenantUsage:
    """Uso atual do tenant."""
    dashboards_count: int = 0
    widgets_count: int = 0
    users_count: int = 0
    datasources_count: int = 0
    alerts_count: int = 0
    api_calls_today: int = 0
    storage_bytes: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "dashboardsCount": self.dashboards_count,
            "widgetsCount": self.widgets_count,
            "usersCount": self.users_count,
            "datasourcesCount": self.datasources_count,
            "alertsCount": self.alerts_count,
            "apiCallsToday": self.api_calls_today,
            "storageBytes": self.storage_bytes,
        }


@dataclass
class Tenant:
    """Tenant (organização/conta)."""
    id: str
    name: str
    slug: str
    
    # Status
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    
    # Configurações
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Limites e uso
    limits: TenantLimits = field(default_factory=TenantLimits)
    usage: TenantUsage = field(default_factory=TenantUsage)
    
    # Billing
    billing_email: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner_id: Optional[str] = None
    
    # Customização
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    
    def is_active(self) -> bool:
        """Verifica se tenant está ativo."""
        return self.status == TenantStatus.ACTIVE
    
    def check_limit(self, resource: str, amount: int = 1) -> bool:
        """Verifica se operação está dentro dos limites."""
        if resource == "dashboards":
            return self.usage.dashboards_count + amount <= self.limits.max_dashboards
        elif resource == "users":
            return self.usage.users_count + amount <= self.limits.max_users
        elif resource == "datasources":
            return self.usage.datasources_count + amount <= self.limits.max_datasources
        elif resource == "alerts":
            return self.usage.alerts_count + amount <= self.limits.max_alerts
        elif resource == "api_calls":
            return self.usage.api_calls_today + amount <= self.limits.api_rate_limit
        return True
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "plan": self.plan.value,
            "settings": self.settings,
            "limits": self.limits.to_dict(),
            "usage": self.usage.to_dict(),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "ownerId": self.owner_id,
            "logoUrl": self.logo_url,
            "primaryColor": self.primary_color,
            "customDomain": self.custom_domain,
        }


# Limites por plano
PLAN_LIMITS = {
    TenantPlan.FREE: TenantLimits(
        max_dashboards=5,
        max_widgets_per_dashboard=10,
        max_users=2,
        max_datasources=1,
        max_alerts=5,
        retention_days=7,
        api_rate_limit=100,
    ),
    TenantPlan.STARTER: TenantLimits(
        max_dashboards=20,
        max_widgets_per_dashboard=30,
        max_users=10,
        max_datasources=5,
        max_alerts=25,
        retention_days=30,
        api_rate_limit=1000,
    ),
    TenantPlan.PROFESSIONAL: TenantLimits(
        max_dashboards=100,
        max_widgets_per_dashboard=50,
        max_users=50,
        max_datasources=20,
        max_alerts=100,
        retention_days=90,
        api_rate_limit=10000,
    ),
    TenantPlan.ENTERPRISE: TenantLimits(
        max_dashboards=999999,
        max_widgets_per_dashboard=100,
        max_users=999999,
        max_datasources=100,
        max_alerts=1000,
        retention_days=365,
        api_rate_limit=999999,
    ),
}


class TenantManager:
    """Gerenciador de tenants."""
    
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._user_tenants: Dict[str, List[str]] = {}  # user_id -> tenant_ids
    
    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        slug: str,
        owner_id: str,
        plan: TenantPlan = TenantPlan.FREE,
    ) -> Tenant:
        """Cria novo tenant."""
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant {tenant_id} already exists")
        
        # Verificar slug único
        if any(t.slug == slug for t in self._tenants.values()):
            raise ValueError(f"Slug {slug} already in use")
        
        tenant = Tenant(
            id=tenant_id,
            name=name,
            slug=slug,
            owner_id=owner_id,
            plan=plan,
            limits=PLAN_LIMITS.get(plan, PLAN_LIMITS[TenantPlan.FREE]),
        )
        
        self._tenants[tenant_id] = tenant
        
        # Associar owner ao tenant
        self.add_user_to_tenant(owner_id, tenant_id)
        
        logger.info(f"Created tenant: {tenant_id}")
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
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
    ) -> List[Tenant]:
        """Lista tenants com filtros."""
        tenants = list(self._tenants.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        if plan:
            tenants = [t for t in tenants if t.plan == plan]
        
        return tenants
    
    def update_tenant(
        self,
        tenant_id: str,
        **kwargs
    ) -> Optional[Tenant]:
        """Atualiza tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.now()
        return tenant
    
    def change_plan(self, tenant_id: str, new_plan: TenantPlan) -> Optional[Tenant]:
        """Altera plano do tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        tenant.plan = new_plan
        tenant.limits = PLAN_LIMITS.get(new_plan, tenant.limits)
        tenant.updated_at = datetime.now()
        
        logger.info(f"Changed tenant {tenant_id} plan to {new_plan.value}")
        return tenant
    
    def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspende tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.status = TenantStatus.SUSPENDED
        tenant.settings["suspension_reason"] = reason
        tenant.updated_at = datetime.now()
        
        logger.warning(f"Suspended tenant {tenant_id}: {reason}")
        return True
    
    def activate_tenant(self, tenant_id: str) -> bool:
        """Ativa tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.status = TenantStatus.ACTIVE
        tenant.settings.pop("suspension_reason", None)
        tenant.updated_at = datetime.now()
        
        logger.info(f"Activated tenant {tenant_id}")
        return True
    
    def add_user_to_tenant(self, user_id: str, tenant_id: str):
        """Adiciona usuário ao tenant."""
        if user_id not in self._user_tenants:
            self._user_tenants[user_id] = []
        
        if tenant_id not in self._user_tenants[user_id]:
            self._user_tenants[user_id].append(tenant_id)
            
            # Atualizar contagem
            tenant = self._tenants.get(tenant_id)
            if tenant:
                tenant.usage.users_count += 1
    
    def remove_user_from_tenant(self, user_id: str, tenant_id: str):
        """Remove usuário do tenant."""
        if user_id in self._user_tenants:
            if tenant_id in self._user_tenants[user_id]:
                self._user_tenants[user_id].remove(tenant_id)
                
                # Atualizar contagem
                tenant = self._tenants.get(tenant_id)
                if tenant:
                    tenant.usage.users_count = max(0, tenant.usage.users_count - 1)
    
    def get_user_tenants(self, user_id: str) -> List[Tenant]:
        """Obtém tenants de um usuário."""
        tenant_ids = self._user_tenants.get(user_id, [])
        return [
            self._tenants[tid]
            for tid in tenant_ids
            if tid in self._tenants
        ]
    
    def update_usage(
        self,
        tenant_id: str,
        resource: str,
        delta: int = 1,
    ):
        """Atualiza uso do tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return
        
        usage = tenant.usage
        
        if resource == "dashboards":
            usage.dashboards_count = max(0, usage.dashboards_count + delta)
        elif resource == "widgets":
            usage.widgets_count = max(0, usage.widgets_count + delta)
        elif resource == "datasources":
            usage.datasources_count = max(0, usage.datasources_count + delta)
        elif resource == "alerts":
            usage.alerts_count = max(0, usage.alerts_count + delta)
        elif resource == "api_calls":
            usage.api_calls_today += delta
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas de tenants."""
        tenants = list(self._tenants.values())
        
        return {
            "totalTenants": len(tenants),
            "activeTenants": len([t for t in tenants if t.status == TenantStatus.ACTIVE]),
            "byPlan": {
                plan.value: len([t for t in tenants if t.plan == plan])
                for plan in TenantPlan
            },
            "byStatus": {
                status.value: len([t for t in tenants if t.status == status])
                for status in TenantStatus
            },
        }


# Singleton
_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Obtém gerenciador de tenants."""
    global _manager
    if _manager is None:
        _manager = TenantManager()
    return _manager

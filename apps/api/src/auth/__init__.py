"""
Módulo de Autenticação e Autorização.
"""

from .deps import get_current_user, is_auth_enabled  # noqa: F401
from .jwt import create_access_token, decode_token  # noqa: F401
from .sso import SSOManager, SSOUser, OAuthProvider, get_sso_manager
from .multitenancy import TenantManager, Tenant, TenantPlan, get_tenant_manager

__all__ = [
    # JWT
    "get_current_user",
    "is_auth_enabled",
    "create_access_token",
    "decode_token",
    # SSO
    "SSOManager",
    "SSOUser",
    "OAuthProvider",
    "get_sso_manager",
    # Multi-tenancy
    "TenantManager",
    "Tenant",
    "TenantPlan",
    "get_tenant_manager",
]

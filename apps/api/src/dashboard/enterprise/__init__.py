"""
Enterprise Module - Features enterprise para dashboards.

Features:
- Multi-tenancy
- RBAC (Role-Based Access Control)
- Audit logging
- Governance
"""

from .rbac import RBACManager, Permission, Role, get_rbac_manager
from .tenancy import TenantManager, Tenant, get_tenant_manager
from .audit import AuditLogger, AuditEvent, get_audit_logger
from .governance import GovernanceManager, Policy, get_governance_manager

__all__ = [
    "RBACManager",
    "Permission",
    "Role",
    "get_rbac_manager",
    "TenantManager",
    "Tenant",
    "get_tenant_manager",
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
    "GovernanceManager",
    "Policy",
    "get_governance_manager",
]

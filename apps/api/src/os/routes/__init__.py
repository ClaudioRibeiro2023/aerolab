"""
Routers modulares do AgentOS.

Cada módulo expõe uma função `create_router(app)` que retorna um APIRouter configurado.
"""

from .agents import create_router as create_agents_router
from .teams import create_router as create_teams_router
from .workflows import create_router as create_workflows_router
from .rag import create_router as create_rag_router
from .hitl import create_router as create_hitl_router
from .storage import create_router as create_storage_router
from .auth import create_router as create_auth_router
from .memory import create_router as create_memory_router
from .metrics import create_router as create_metrics_router
from .admin import create_router as create_admin_router
from .audit import create_router as create_audit_router

__all__ = [
    "create_agents_router",
    "create_teams_router",
    "create_workflows_router",
    "create_rag_router",
    "create_hitl_router",
    "create_storage_router",
    "create_auth_router",
    "create_memory_router",
    "create_metrics_router",
    "create_admin_router",
    "create_audit_router",
]

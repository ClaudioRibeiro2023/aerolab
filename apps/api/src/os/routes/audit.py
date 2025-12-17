"""
Router de Audit - Logs de auditoria.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.auth.deps import get_current_user, is_auth_enabled
from src.audit import get_audit_logger, EventType
from src.os.middleware import setup_security


class AuditQueryParams(BaseModel):
    """Parâmetros de consulta de audit logs."""

    event_type: Optional[str] = None
    user: Optional[str] = None
    resource: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de audit.

    Args:
        app: Instância do FastAPI app.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/audit", tags=["audit"])

    # Aplicar middlewares
    setup_security(router)

    @router.get("/logs")
    async def audit_list(
        event_type: Optional[str] = Query(None),
        user: Optional[str] = Query(None),
        resource: Optional[str] = Query(None),
        domain: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(100, le=1000),
        offset: int = Query(0),
        current_user=Depends(get_current_user),
    ):
        """Lista logs de auditoria (apenas admin)."""
        if is_auth_enabled():
            role = (current_user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        audit = get_audit_logger()

        # Converter event_type string para enum se fornecido
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")

        logs = audit.query(
            event_type=event_type_enum,
            user=user,
            resource=resource,
            domain=domain,
            status=status,
            limit=limit,
            offset=offset,
        )

        return {"logs": logs, "count": len(logs)}

    @router.get("/logs/stats")
    async def audit_stats(current_user=Depends(get_current_user)):
        """Estatísticas de auditoria (apenas admin)."""
        if is_auth_enabled():
            role = (current_user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        audit = get_audit_logger()
        return audit.get_stats()

    @router.get("/logs/user/{username}")
    async def audit_user_activity(
        username: str,
        limit: int = Query(50, le=500),
        current_user=Depends(get_current_user),
    ):
        """Atividade de um usuário específico (apenas admin ou próprio usuário)."""
        if is_auth_enabled():
            role = (current_user or {}).get("role", "user")
            current_username = (current_user or {}).get("sub")
            if role != "admin" and current_username != username:
                raise HTTPException(status_code=403, detail="Forbidden")

        audit = get_audit_logger()
        logs = audit.get_user_activity(user=username, limit=limit)

        return {"user": username, "logs": logs, "count": len(logs)}

    @router.get("/logs/security")
    async def audit_security_events(
        limit: int = Query(100, le=500),
        current_user=Depends(get_current_user),
    ):
        """Eventos de segurança recentes (apenas admin)."""
        if is_auth_enabled():
            role = (current_user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        audit = get_audit_logger()
        logs = audit.get_security_events(limit=limit)

        return {"logs": logs, "count": len(logs)}

    @router.get("/event-types")
    async def audit_event_types():
        """Lista tipos de eventos disponíveis."""
        return {"event_types": [e.value for e in EventType]}

    return router

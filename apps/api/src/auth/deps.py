from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from src.config import get_settings
from .jwt import decode_token, create_access_token  # re-export for convenience
from .rbac import Resource, Action, Domain, check_permission, get_user_domains

_CREATE_ACCESS_TOKEN_REF = create_access_token


def is_auth_enabled() -> bool:
    """Verifica se autenticação está habilitada."""
    s = get_settings()
    return bool(s.JWT_SECRET)


def get_current_user(request: Request) -> Dict[str, Any]:
    """Obtém usuário atual do token JWT."""
    s = get_settings()
    if not s.JWT_SECRET:
        # Auth desabilitada
        return {"sub": "anonymous", "role": "admin"}
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token, secret=s.JWT_SECRET)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def require_role(*roles: str):
    """Dependência que requer um dos papéis especificados."""
    def _dep(user: Dict[str, Any] = Depends(get_current_user)):
        role = user.get("role", "user")
        if roles and role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


def require_permission(resource: Resource, action: Action, domain: Optional[Domain] = None):
    """
    Dependência que verifica permissão granular via RBAC.

    Args:
        resource: Recurso sendo acessado
        action: Ação sendo executada
        domain: Domínio (opcional)

    Returns:
        Dependência FastAPI
    """
    def _dep(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "user")

        if not check_permission(user_role, resource, action, domain):
            # Log de acesso negado
            try:
                from src.audit import get_audit_logger, AuditEvent, EventType
                audit = get_audit_logger()
                audit.log(AuditEvent(
                    event_type=EventType.ACCESS_DENIED,
                    user=user.get("sub"),
                    user_role=user_role,
                    resource=resource.value,
                    action=action.value,
                    domain=domain.value if domain else None,
                    ip_address=request.client.host if request.client else None,
                    status="denied",
                ))
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource.value}:{action.value}"
            )
        return user

    return _dep


def get_user_allowed_domains(user: Dict[str, Any]) -> set:
    """Retorna os domínios permitidos para o usuário."""
    user_role = user.get("role", "user")
    return get_user_domains(user_role)

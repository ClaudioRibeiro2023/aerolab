"""
Router de Auth - Autenticação JWT.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.config import get_settings
from src.auth.deps import get_current_user
from src.auth.jwt import create_access_token


class LoginRequest(BaseModel):
    """Request de login."""

    username: str


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de auth.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/login")
    async def login(req: LoginRequest):
        """Realiza login e retorna token JWT."""
        settings = get_settings()

        if not settings.JWT_SECRET:
            raise HTTPException(status_code=400, detail="JWT not configured")

        admins = {u.strip() for u in (settings.ADMIN_USERS or "").split(",") if u.strip()}
        role = "admin" if req.username in admins else "user"

        token = create_access_token(
            subject=req.username,
            role=role,
            secret=settings.JWT_SECRET,
            expires_minutes=settings.JWT_EXPIRES_MIN,
        )

        return {"access_token": token, "token_type": "bearer", "role": role}

    @router.get("/me")
    async def me(user=Depends(get_current_user)):
        """Retorna informações do usuário autenticado."""
        return user

    return router

"""
Router de Admin - Configuração e health checks.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.config import get_settings
from src.auth.deps import get_current_user, is_auth_enabled


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de admin.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(tags=["admin"])

    @router.get("/admin/health")
    async def health():
        """Health check da aplicação."""
        now = time.time()
        started = getattr(app.state, "started_at", None)
        uptime = (now - started) if started else None

        return {
            "status": "ok",
            "uptime_s": round(uptime, 2) if uptime else None,
        }

    @router.get("/admin/config")
    async def admin_config(user=Depends(get_current_user)):
        """Retorna configurações da aplicação (apenas admin)."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        settings = get_settings()

        return {
            "DEFAULT_MODEL_PROVIDER": settings.DEFAULT_MODEL_PROVIDER,
            "DEFAULT_MODEL_ID": settings.DEFAULT_MODEL_ID,
            "CORS_ALLOW_ORIGINS": settings.CORS_ALLOW_ORIGINS,
            "RATE_LIMIT_ENABLED": getattr(settings, "RATE_LIMIT_ENABLED", False),
            "RATE_LIMIT_WINDOW_SECONDS": getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60),
            "RATE_LIMIT_RAG_QUERY": getattr(settings, "RATE_LIMIT_RAG_QUERY", None),
            "RATE_LIMIT_RAG_INGEST": getattr(settings, "RATE_LIMIT_RAG_INGEST", None),
            "RATE_LIMIT_AUTH": getattr(settings, "RATE_LIMIT_AUTH", None),
            "RATE_LIMIT_AGENTICS": getattr(settings, "RATE_LIMIT_AGENTICS", None),
            "RATE_LIMIT_DEFAULT": getattr(settings, "RATE_LIMIT_DEFAULT", None),
            "DEBUG": settings.DEBUG,
            "LOG_LEVEL": settings.LOG_LEVEL,
        }

    @router.get("/admin/rate-limit/status")
    async def admin_rate_limit_status(user=Depends(get_current_user)):
        """Retorna status do rate limiting (apenas admin)."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        settings = get_settings()

        return {
            "enabled": getattr(settings, "RATE_LIMIT_ENABLED", False),
            "window_seconds": getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60),
            "limits": {
                "rag_query": getattr(settings, "RATE_LIMIT_RAG_QUERY", None),
                "rag_ingest": getattr(settings, "RATE_LIMIT_RAG_INGEST", None),
                "auth": getattr(settings, "RATE_LIMIT_AUTH", None),
                "agentics": getattr(settings, "RATE_LIMIT_AGENTICS", None),
                "default": getattr(settings, "RATE_LIMIT_DEFAULT", None),
            },
            "counters_hint": "Use /metrics para contadores por rota e status.",
        }

    return router

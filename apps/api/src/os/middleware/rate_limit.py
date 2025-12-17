"""
Rate limiting middleware e utilitários.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from src.config import get_settings


def _route_group(path: str) -> str:
    """Determina o grupo de rate limit baseado no path."""
    if path.startswith("/rag/query"):
        return "rag_query"
    if path.startswith("/rag/ingest"):
        return "rag_ingest"
    if path.startswith("/auth/"):
        return "auth"
    if path.startswith("/teams/"):
        return "teams"
    if path.startswith("/workflows/"):
        return "workflows"
    return "default"


def _limit_for(group: str) -> int:
    """Retorna o limite de requisições para um grupo."""
    settings = get_settings()
    limits = {
        "rag_query": getattr(settings, "RATE_LIMIT_RAG_QUERY", 60),
        "rag_ingest": getattr(settings, "RATE_LIMIT_RAG_INGEST", 10),
        "auth": getattr(settings, "RATE_LIMIT_AUTH", 30),
        "teams": getattr(settings, "RATE_LIMIT_AGENTICS", 30),
        "workflows": getattr(settings, "RATE_LIMIT_AGENTICS", 30),
    }
    return limits.get(group, getattr(settings, "RATE_LIMIT_DEFAULT", 120))


class RateLimiter:
    """Rate limiter baseado em sliding window."""

    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.buckets: Dict[str, deque] = {}

    def check(self, key: str, group: str) -> bool:
        """
        Verifica se a requisição deve ser permitida.
        Retorna True se permitida, False se bloqueada.
        """
        now = time.time()
        limit = _limit_for(group)
        bucket_key = f"{group}:{key}"

        dq = self.buckets.setdefault(bucket_key, deque())

        # Remove entradas fora da janela
        while dq and (now - dq[0]) > self.window:
            dq.popleft()

        if len(dq) >= limit:
            return False

        dq.append(now)
        return True

    def get_retry_after(self, key: str, group: str) -> int:
        """Retorna segundos até poder tentar novamente."""
        bucket_key = f"{group}:{key}"
        dq = self.buckets.get(bucket_key)
        if not dq:
            return 0
        now = time.time()
        return max(1, int(self.window - (now - dq[0])))


# Instância global do rate limiter
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Retorna a instância global do rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        window = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
        _rate_limiter = RateLimiter(window_seconds=window)
    return _rate_limiter


def create_rate_limiter() -> RateLimiter:
    """Cria uma nova instância do rate limiter."""
    settings = get_settings()
    window = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    return RateLimiter(window_seconds=window)


def create_rate_limit_dependency() -> Callable:
    """Cria uma dependência de rate limiting para FastAPI."""

    def _rate_limit(request: Request):
        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED:
            return True

        limiter = get_rate_limiter()
        path = request.url.path
        group = _route_group(path)

        # Extrair chave do usuário (token ou IP)
        auth = request.headers.get("authorization", "")
        key = None
        if auth.lower().startswith("bearer "):
            key = auth.split(" ", 1)[1].strip()
        if not key:
            key = request.client.host if request.client else "unknown"

        if not limiter.check(key, group):
            retry_after = limiter.get_retry_after(key, group)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        return True

    return _rate_limit


def setup_rate_limit(router: APIRouter) -> None:
    """Configura rate limiting em um router."""
    settings = get_settings()
    if settings.RATE_LIMIT_ENABLED:
        router.dependencies.append(Depends(create_rate_limit_dependency()))

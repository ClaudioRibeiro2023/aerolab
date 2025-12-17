"""
Security middleware e utilitários.
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.config import get_settings


def create_basic_auth_dependency() -> Callable:
    """Cria uma dependência de Basic Auth para FastAPI."""
    security = HTTPBasic()
    settings = get_settings()

    def _basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
        if not (
            credentials.username == settings.BASIC_AUTH_USERNAME
            and credentials.password == settings.BASIC_AUTH_PASSWORD
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"},
            )
        return True

    return _basic_auth


def setup_security(router: APIRouter) -> None:
    """Configura segurança (Basic Auth) em um router se habilitado."""
    settings = get_settings()

    if settings.BASIC_AUTH_USERNAME and settings.BASIC_AUTH_PASSWORD:
        router.dependencies.append(Depends(create_basic_auth_dependency()))

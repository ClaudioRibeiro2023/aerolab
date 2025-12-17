"""
Router de Storage - Upload e gestão de arquivos.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.deps import get_current_user, is_auth_enabled
from src.storage.service import get_storage
from src.os.middleware import setup_rate_limit, setup_security


class UploadTextRequest(BaseModel):
    """Request para upload de texto."""

    name: str
    content: str


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de storage.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/storage", tags=["storage"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    # RBAC opcional
    if is_auth_enabled():
        router.dependencies.append(Depends(get_current_user))

    @router.post("/upload-text")
    async def storage_upload_text(req: UploadTextRequest, user=Depends(get_current_user)):
        """Faz upload de um arquivo de texto."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        storage = get_storage()
        path = storage.save_text(req.name, req.content)

        return {"path": path}

    @router.get("/list")
    async def storage_list():
        """Lista todos os arquivos."""
        storage = get_storage()
        return {"files": storage.list_files()}

    @router.delete("/{name}")
    async def storage_delete(name: str, user=Depends(get_current_user)):
        """Remove um arquivo."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        storage = get_storage()
        ok = storage.delete_file(name)

        if not ok:
            raise HTTPException(status_code=404, detail="File not found")

        return {"deleted": name}

    return router

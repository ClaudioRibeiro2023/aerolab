"""
Router de RAG - Ingestão e consulta de conhecimento.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.auth.deps import get_current_user, is_auth_enabled
from src.os.middleware import setup_rate_limit, setup_security


class IngestTextsRequest(BaseModel):
    """Request para ingerir textos."""

    collection: str
    texts: List[str]
    metadatas: Optional[List[Dict]] = None


class QueryRequest(BaseModel):
    """Request para consultar conhecimento."""

    collection: str
    query_text: str
    top_k: Optional[int] = 5


class IngestUrlsRequest(BaseModel):
    """Request para ingerir URLs."""

    collection: str
    urls: List[str]


def _get_rag_service():
    """Obtém o serviço RAG com lazy import."""
    try:
        from src.rag.service import get_rag_service

        return get_rag_service()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="RAG não habilitado. Instale o extra: pip install -e .[rag]",
        )


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de RAG.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/rag", tags=["rag"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    # Nota: autenticação é verificada individualmente nas rotas que precisam (ingest, delete)

    @router.post("/ingest-texts")
    async def rag_ingest_texts(req: IngestTextsRequest, user=Depends(get_current_user)):
        """Ingere textos em uma coleção."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        rag = _get_rag_service()
        result = rag.add_texts(
            collection=req.collection, texts=req.texts, metadatas=req.metadatas
        )
        return result

    @router.post("/query")
    async def rag_query(req: QueryRequest):
        """Consulta conhecimento em uma coleção."""
        rag = _get_rag_service()
        results = rag.query(
            collection=req.collection, query_text=req.query_text, top_k=req.top_k or 5
        )
        return {"results": results}

    @router.post("/ingest-urls")
    async def rag_ingest_urls(req: IngestUrlsRequest, user=Depends(get_current_user)):
        """Ingere conteúdo de URLs em uma coleção."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        rag = _get_rag_service()
        result = await rag.ingest_urls(collection=req.collection, urls=req.urls)
        return result

    @router.post("/ingest-files")
    async def rag_ingest_files(
        collection: str = Form(...),
        files: List[UploadFile] = File(...),
        user=Depends(get_current_user),
    ):
        """Ingere arquivos (PDF, MD, TXT) em uma coleção."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        rag = _get_rag_service()
        payload: List[tuple[str, bytes]] = []

        for f in files:
            data = await f.read()
            payload.append((f.filename, data))

        if not payload:
            return {"added": 0}

        result = rag.ingest_files(collection=collection, files=payload)
        return result

    @router.get("/collections")
    async def rag_collections():
        """Lista todas as coleções."""
        rag = _get_rag_service()

        if hasattr(rag, "list_collections"):
            return {"collections": rag.list_collections()}

        raise HTTPException(
            status_code=501, detail="Operação não suportada pelo backend RAG"
        )

    @router.get("/collections/{collection}/docs")
    async def rag_list_docs(collection: str):
        """Lista documentos de uma coleção."""
        rag = _get_rag_service()

        if hasattr(rag, "list_docs"):
            return {"docs": rag.list_docs(collection=collection)}

        raise HTTPException(
            status_code=501, detail="Operação não suportada pelo backend RAG"
        )

    @router.delete("/collections/{collection}")
    async def rag_delete_collection(collection: str, user=Depends(get_current_user)):
        """Remove uma coleção."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        rag = _get_rag_service()

        if hasattr(rag, "delete_collection"):
            ok = rag.delete_collection(collection=collection)
            if not ok:
                raise HTTPException(status_code=404, detail="Collection not found")
            return {"deleted": collection}

        raise HTTPException(
            status_code=501, detail="Operação não suportada pelo backend RAG"
        )

    @router.delete("/collections/{collection}/docs/{doc_id}")
    async def rag_delete_doc(
        collection: str, doc_id: str, user=Depends(get_current_user)
    ):
        """Remove um documento de uma coleção."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        rag = _get_rag_service()

        if hasattr(rag, "delete_doc"):
            ok = rag.delete_doc(collection=collection, doc_id=doc_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Document not found")
            return {"deleted": doc_id}

        raise HTTPException(
            status_code=501, detail="Operação não suportada pelo backend RAG"
        )

    return router

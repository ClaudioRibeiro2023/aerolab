"""
Router de Metrics - Observabilidade e métricas.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from src.observability.metrics import get_metrics_text, track_request


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de metrics.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/metrics", tags=["metrics"])

    @router.get("")
    async def metrics_get():
        """Retorna métricas da aplicação em JSON."""
        metrics = getattr(app.state, "metrics", {})

        per_route = {}
        for path, data in metrics.get("per_route", {}).items():
            avg = (data["total_ms"] / data["count"]) if data["count"] else 0.0
            per_route[path] = {"count": data["count"], "avg_ms": round(avg, 2)}

        return {
            "requests": metrics.get("requests", 0),
            "per_route": per_route,
            "per_status": metrics.get("per_status", {}),
            "per_route_status": metrics.get("per_route_status", {}),
        }

    @router.get("/prometheus")
    async def metrics_prometheus():
        """
        Retorna métricas em formato Prometheus.
        
        Compatível com Prometheus scraper e Grafana.
        """
        return PlainTextResponse(
            content=get_metrics_text(),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    return router


def setup_metrics_middleware(app: Any) -> None:
    """
    Configura o middleware de métricas.

    Args:
        app: Instância do FastAPI app.
    """
    # Inicializar métricas
    if not hasattr(app.state, "metrics"):
        app.state.metrics = {
            "requests": 0,
            "per_route": {},
            "per_status": {},
            "per_route_status": {},
        }

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.time()
        req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        auth_present = bool(request.headers.get("authorization"))

        response = None
        try:
            # Interceptar GET /workflows/registry
            normalized_path = request.url.path.rstrip("/")
            if method == "GET" and normalized_path == "/workflows/registry":
                registry = getattr(app.state, "workflows_registry", {})
                response = JSONResponse(list(registry.values()))
                return response

            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.time() - start) * 1000.0
            status_code = getattr(response, "status_code", 500) if response else 500

            try:
                if response is not None:
                    response.headers["x-request-id"] = req_id
            except Exception:
                pass

            # Atualizar métricas
            metrics = app.state.metrics
            metrics["requests"] += 1

            pr = metrics["per_route"].setdefault(path, {"count": 0, "total_ms": 0.0})
            pr["count"] += 1
            pr["total_ms"] += duration_ms

            metrics["per_status"][status_code] = metrics["per_status"].get(status_code, 0) + 1

            prs = metrics["per_route_status"].setdefault(path, {})
            prs[status_code] = prs.get(status_code, 0) + 1

            # Log estruturado
            logger = getattr(app.state, "logger", None)
            if logger:
                try:
                    logger.info(
                        f"event=request id={req_id} method={method} path={path} "
                        f"status={status_code} duration_ms={round(duration_ms, 2)} "
                        f"ip={ip} auth={auth_present}"
                    )
                except Exception:
                    pass

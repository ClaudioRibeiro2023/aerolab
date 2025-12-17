"""API routes para o Núcleo Licitações."""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import uuid
import logging

from ..models import (
    LicitacaoItem,
    TriageScore,
    AnalysisPack,
    FlowConfig,
    FlowResult,
    Prioridade,
    StatusFluxo,
)
from ..tools import PNCPClient
from ..services import dedup_strong

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/licitacoes", tags=["Licitações"])


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class MonitorRequest(BaseModel):
    config: FlowConfig | None = None


class MonitorResponse(BaseModel):
    run_id: str
    items_count: int
    items: list[LicitacaoItem]
    result: FlowResult


class AnalyzeRequest(BaseModel):
    licitacao_id: str | None = None
    url: str | None = None
    text: str | None = None


class AnalyzeResponse(BaseModel):
    run_id: str
    licitacao: LicitacaoItem | None
    analysis: AnalysisPack | None
    result: FlowResult


class DigestResponse(BaseModel):
    date: str
    total_items: int
    p0_count: int
    p1_count: int
    items: list[LicitacaoItem]
    scores: list[TriageScore]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica saúde do módulo de licitações."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/monitor", response_model=MonitorResponse)
async def run_monitor(request: MonitorRequest):
    """
    Executa monitoramento de licitações (debug/desenvolvimento).

    Este endpoint executa o fluxo daily_monitor de forma síncrona
    para fins de debug. Em produção, use o scheduler.
    """
    run_id = f"monitor-{uuid.uuid4().hex[:8]}"
    result = FlowResult.init_result(run_id)

    config = request.config or FlowConfig()

    try:
        async with PNCPClient() as client:
            items = await client.search(
                keywords=config.keywords,
                ufs=config.ufs if config.ufs else None,
                modalidades=config.modalidades if config.modalidades else None,
            )

        items = dedup_strong(items)

        result.items_processed = len(items)
        result.mark_success()
        result.payload_json = f'{{"items_count": {len(items)}}}'

        return MonitorResponse(
            run_id=run_id,
            items_count=len(items),
            items=items[:config.limite_itens],
            result=result,
        )

    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        result.mark_error(str(e))
        return MonitorResponse(
            run_id=run_id,
            items_count=0,
            items=[],
            result=result,
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def run_analyze(request: AnalyzeRequest):
    """
    Executa análise de licitação sob demanda (debug/desenvolvimento).

    Forneça um licitacao_id, url ou text para análise.
    """
    run_id = f"analyze-{uuid.uuid4().hex[:8]}"
    result = FlowResult.init_result(run_id)

    if not any([request.licitacao_id, request.url, request.text]):
        raise HTTPException(
            status_code=400,
            detail="Forneça licitacao_id, url ou text para análise",
        )

    try:
        licitacao: LicitacaoItem | None = None

        if request.licitacao_id:
            async with PNCPClient() as client:
                licitacao = await client.get_detail(request.licitacao_id)

            if not licitacao:
                result.mark_error(f"Licitação não encontrada: {request.licitacao_id}")
                return AnalyzeResponse(
                    run_id=run_id,
                    licitacao=None,
                    analysis=None,
                    result=result,
                )

        analysis = AnalysisPack(
            licitacao_id=request.licitacao_id or "manual",
            resumo_executivo="Análise em desenvolvimento. Agente Analyst será implementado na próxima fase.",
            pontos_atencao=["Implementação pendente"],
            recomendacao="analisar mais",
        )

        result.mark_success()

        return AnalyzeResponse(
            run_id=run_id,
            licitacao=licitacao,
            analysis=analysis,
            result=result,
        )

    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        result.mark_error(str(e))
        return AnalyzeResponse(
            run_id=run_id,
            licitacao=None,
            analysis=None,
            result=result,
        )


@router.get("/digest/{date}", response_model=DigestResponse)
async def get_digest(
    date: str,
    priority: Prioridade | None = Query(default=None, description="Filtrar por prioridade"),
):
    """
    Retorna o digest de licitações para uma data específica.

    Formato da data: YYYY-MM-DD
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD",
        )

    return DigestResponse(
        date=date,
        total_items=0,
        p0_count=0,
        p1_count=0,
        items=[],
        scores=[],
    )


@router.get("/search")
async def search_licitacoes(
    q: str = Query(..., min_length=3, description="Termo de busca"),
    uf: str | None = Query(default=None, max_length=2),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Busca licitações por palavra-chave."""
    run_id = f"search-{uuid.uuid4().hex[:8]}"

    try:
        async with PNCPClient() as client:
            items = await client.search(
                keywords=[q],
                ufs=[uf] if uf else None,
            )

        items = dedup_strong(items)[:limit]

        return {
            "run_id": run_id,
            "query": q,
            "uf": uf,
            "count": len(items),
            "items": items,
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

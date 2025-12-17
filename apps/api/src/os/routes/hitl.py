"""
Router de HITL - Human-in-the-Loop workflows.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agno.agent import Agent

from src.os.middleware import setup_rate_limit, setup_security


class HITLStartRequest(BaseModel):
    """Request para iniciar sessão HITL."""

    topic: str
    style: Optional[str] = None


class HITLCompleteRequest(BaseModel):
    """Request para completar sessão HITL."""

    session_id: str
    approve: bool = True
    feedback: Optional[str] = None


class HITLCancelRequest(BaseModel):
    """Request para cancelar sessão HITL."""

    session_id: str
    reason: Optional[str] = None


def _get_output(agent: Agent) -> str:
    """Extrai output de um agente de forma segura."""
    try:
        out = agent.get_last_run_output()
    except Exception:
        out = None

    if isinstance(out, dict):
        return out.get("content", "")
    return getattr(out, "content", "") or ""


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de HITL.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/hitl", tags=["hitl"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    @router.post("/start")
    async def hitl_start(req: HITLStartRequest):
        """Inicia uma sessão HITL com pesquisa inicial."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")

        if not researcher:
            raise HTTPException(status_code=500, detail="Researcher agent not available")

        # Executar pesquisa
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        research = _get_output(researcher)

        # Fallback se vazio
        if not research:
            researcher.run(f"Liste 5 pontos objetivos sobre: {req.topic} com 1-2 fontes.")
            research = _get_output(researcher)

        if not research:
            tmpl = agents_map.get("Template Agent")
            if tmpl:
                tmpl.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
                research = _get_output(tmpl)

        if not research:
            research = f"Não foi possível gerar pesquisa automática sobre: {req.topic}."

        # Persistir sessão
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        sess = repo.create_session(topic=req.topic, style=req.style, research=research)

        return {"session_id": sess.id, "topic": sess.topic, "research": sess.research}

    @router.post("/complete")
    async def hitl_complete(req: HITLCompleteRequest):
        """Completa uma sessão HITL (aprova ou rejeita)."""
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        sess = repo.get(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Invalid session_id")

        if not req.approve:
            sess = repo.reject(req.session_id)
            return {"status": sess.status, "session_id": sess.id}

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        writer = agents_map.get("Writer")

        if not writer:
            raise HTTPException(status_code=500, detail="Writer agent not available")

        style = sess.style or "neutro"
        research = sess.research or ""
        feedback = req.feedback or ""

        writer.run(
            f"Escreva um texto claro e bem estruturado em Markdown.\n\n"
            f"Pesquisa:\n{research}\n\n"
            f"Estilo: {style}\n"
            f"Observações do revisor: {feedback}"
        )
        content = _get_output(writer)

        # Fallback
        if not content:
            tmpl = agents_map.get("Template Agent")
            if tmpl:
                tmpl.run(
                    f"Escreva um texto claro sobre: {sess.topic}\n"
                    f"Estilo: {style}"
                )
                content = _get_output(tmpl)

        if not content:
            content = f"Conteúdo gerado para: {sess.topic}"

        sess = repo.approve(req.session_id, final_text=content, feedback=feedback)

        return {"status": sess.status, "session_id": sess.id, "content": content}

    @router.get("/{session_id}")
    async def hitl_get(session_id: str):
        """Retorna detalhes de uma sessão HITL."""
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        sess = repo.get(session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": sess.id,
            "topic": sess.topic,
            "style": sess.style,
            "status": sess.status,
            "research": sess.research,
            "final_text": sess.final_text,
        }

    @router.get("/")
    async def hitl_list(status: Optional[str] = None, limit: int = 50):
        """Lista sessões HITL."""
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        sessions = repo.list(status=status, limit=limit)
        
        items = [
            {
                "session_id": s.id,
                "topic": s.topic,
                "status": s.status,
            }
            for s in sessions
        ]

        return {"items": items, "count": len(items)}

    @router.post("/cancel")
    async def hitl_cancel(req: HITLCancelRequest):
        """Cancela uma sessão HITL."""
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        try:
            sess = repo.cancel(req.session_id, reason=req.reason)
        except ValueError:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"status": sess.status, "session_id": sess.id}

    return router

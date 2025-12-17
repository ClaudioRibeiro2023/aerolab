"""
Router de Memory - Gestão de histórico e memória de agentes.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agno.agent import Agent

from src.os.middleware import setup_rate_limit, setup_security


class MemoryPruneRequest(BaseModel):
    """Request para podar memória."""

    max_messages: Optional[int] = None
    max_tokens: Optional[int] = None


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
    Cria o router de memory.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/memory", tags=["memory"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    @router.get("/agent/{agent_name}/history")
    async def memory_history(agent_name: str):
        """Retorna histórico de chat de um agente."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            history = agent.get_chat_history()
        except Exception:
            history = []

        return {"agent": agent_name, "history": history}

    @router.get("/agent/{agent_name}/summary")
    async def memory_summary(agent_name: str):
        """Retorna resumo da sessão de um agente."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            summary = agent.get_session_summary()
        except Exception:
            summary = None

        return {"agent": agent_name, "summary": summary}

    @router.post("/agent/{agent_name}/reset")
    async def memory_reset(agent_name: str):
        """Reseta a sessão de um agente."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            agent.delete_session()
        except Exception:
            pass

        return {"agent": agent_name, "status": "reset"}

    @router.post("/agent/{agent_name}/prune")
    async def memory_prune(agent_name: str, req: MemoryPruneRequest):
        """Poda memória de um agente baseado em limites."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(agent_name)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        try:
            history = agent.get_chat_history() or []
        except Exception:
            history = []

        count = len(history)

        # Calcular tokens aproximados
        content_len = 0
        try:
            for msg in history:
                content = getattr(msg, "content", "")
                if isinstance(content, str):
                    content_len += len(content)
        except Exception:
            pass

        approx_tokens = max(1, content_len // 4) if content_len > 0 else 0

        # Verificar se precisa podar
        should_prune = False
        if req.max_messages is not None and count > req.max_messages:
            should_prune = True
        if req.max_tokens is not None and approx_tokens > req.max_tokens:
            should_prune = True

        if should_prune:
            # Gerar resumo antes de resetar
            summary_text = None
            try:
                summary_text = agent.get_session_summary()
            except Exception:
                pass

            if not summary_text:
                try:
                    preview = history[-10:] if len(history) > 10 else history
                    joined = "\n\n".join(
                        [str(getattr(m, "content", ""))[:500] for m in preview]
                    )
                    prompt = (
                        "Resuma a conversa em no máximo 8 bullets, "
                        "mantendo fatos essenciais e decisões.\n\n"
                        f"Contexto:\n{joined}"
                    )
                    agent.run(prompt)
                    summary_text = _get_output(agent)
                except Exception:
                    summary_text = ""

            # Persistir resumo
            summary_path = None
            try:
                from src.storage.service import get_storage

                storage = get_storage()
                sid = getattr(agent, "session_id", None) or str(uuid.uuid4())
                fname = f"summary_{agent_name}_{sid}.md"
                content = f"# Resumo da sessão ({agent_name})\n\n{summary_text or 'Sem resumo.'}"
                summary_path = storage.save_text(fname, content)
            except Exception:
                pass

            # Resetar sessão
            try:
                sid = getattr(agent, "session_id", None)
                if sid:
                    agent.delete_session(sid)
                else:
                    agent.delete_session()
            except Exception:
                pass

            return {
                "agent": agent_name,
                "pruned": True,
                "prev_messages": count,
                "approx_tokens": approx_tokens,
                "summary_path": summary_path,
            }

        return {
            "agent": agent_name,
            "pruned": False,
            "messages": count,
            "approx_tokens": approx_tokens,
        }

    return router

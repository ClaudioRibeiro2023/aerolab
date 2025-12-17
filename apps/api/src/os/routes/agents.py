"""
Router de Agents - CRUD e execução de agentes.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agno.agent import Agent

from src.agents import BaseAgent
from src.config import get_settings
from src.auth.deps import get_current_user, is_auth_enabled
from src.os.middleware import setup_rate_limit, setup_security


class AgentCreateRequest(BaseModel):
    """Request para criar um novo agente."""

    name: str
    role: Optional[str] = None
    model_provider: Optional[str] = None
    model_id: Optional[str] = None
    use_database: Optional[bool] = False
    instructions: Optional[List[str]] = None
    markdown: Optional[bool] = True
    add_history_to_context: Optional[bool] = True
    debug_mode: Optional[bool] = False


class AgentUpdateRequest(BaseModel):
    """Request para atualizar um agente."""

    role: Optional[str] = None
    model_provider: Optional[str] = None
    model_id: Optional[str] = None
    use_database: Optional[bool] = None
    instructions: Optional[List[str]] = None
    markdown: Optional[bool] = None
    add_history_to_context: Optional[bool] = None
    debug_mode: Optional[bool] = None


class AgentRunRequest(BaseModel):
    """Request para executar um agente."""

    prompt: str


def _get_agent_output(agent: Agent) -> str:
    """Extrai o output de um agente de forma segura."""
    try:
        out = agent.get_last_run_output()
    except Exception:
        out = None

    if isinstance(out, dict):
        return out.get("content", "")
    return getattr(out, "content", "") or ""


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de agents.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/agents", tags=["agents"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    @router.post("")
    async def agents_create(req: AgentCreateRequest, user=Depends(get_current_user)):
        """Cria um novo agente."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        if req.name in agents_map:
            raise HTTPException(status_code=409, detail="Agent already exists")

        settings = get_settings()
        agent = BaseAgent.create(
            name=req.name,
            role=req.role,
            instructions=req.instructions or [],
            model_provider=req.model_provider or settings.DEFAULT_MODEL_PROVIDER,
            model_id=req.model_id or settings.DEFAULT_MODEL_ID,
            use_database=bool(req.use_database),
            add_history_to_context=bool(req.add_history_to_context),
            markdown=bool(req.markdown),
            debug_mode=bool(req.debug_mode),
        )

        agents_map[req.name] = agent
        app.state.agents = agents_map

        return {"name": req.name, "role": getattr(agent, "role", None)}

    @router.get("")
    async def agents_list():
        """Lista todos os agentes disponíveis."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        return [
            {"name": k, "role": getattr(v, "role", None)}
            for k, v in agents_map.items()
        ]

    @router.get("/{name}")
    async def agents_get(name: str):
        """Retorna detalhes de um agente específico."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Extrair configurações do agente
        return {
            "name": name,
            "role": getattr(agent, "role", None),
            "model_provider": getattr(agent, "model_provider", None) or getattr(getattr(agent, "model", None), "id", "").split("/")[0] if hasattr(agent, "model") else None,
            "model_id": getattr(agent, "model_id", None) or getattr(getattr(agent, "model", None), "id", None),
            "instructions": getattr(agent, "instructions", []),
            "use_database": getattr(agent, "storage", None) is not None,
            "add_history_to_context": getattr(agent, "add_history_to_messages", False),
            "markdown": getattr(agent, "markdown", True),
            "debug_mode": getattr(agent, "debug_mode", False),
        }

    @router.put("/{name}")
    async def agents_update(name: str, req: AgentUpdateRequest, user=Depends(get_current_user)):
        """Atualiza um agente existente."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        old_agent = agents_map.get(name)
        if not old_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Preservar valores existentes se não fornecidos
        settings = get_settings()
        new_role = req.role if req.role is not None else getattr(old_agent, "role", None)
        new_instructions = req.instructions if req.instructions is not None else getattr(old_agent, "instructions", [])
        new_provider = req.model_provider if req.model_provider is not None else settings.DEFAULT_MODEL_PROVIDER
        new_model = req.model_id if req.model_id is not None else settings.DEFAULT_MODEL_ID
        new_db = req.use_database if req.use_database is not None else (getattr(old_agent, "storage", None) is not None)
        new_history = req.add_history_to_context if req.add_history_to_context is not None else getattr(old_agent, "add_history_to_messages", True)
        new_md = req.markdown if req.markdown is not None else getattr(old_agent, "markdown", True)
        new_debug = req.debug_mode if req.debug_mode is not None else getattr(old_agent, "debug_mode", False)

        # Recriar agente com novas configurações
        new_agent = BaseAgent.create(
            name=name,
            role=new_role,
            instructions=new_instructions,
            model_provider=new_provider,
            model_id=new_model,
            use_database=bool(new_db),
            add_history_to_context=bool(new_history),
            markdown=bool(new_md),
            debug_mode=bool(new_debug),
        )

        agents_map[name] = new_agent
        app.state.agents = agents_map

        return {"name": name, "role": new_role, "updated": True}

    @router.post("/{name}/run")
    async def agents_run(name: str, req: AgentRunRequest):
        """Executa um agente com o prompt fornecido."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent.run(req.prompt)
        output = _get_agent_output(agent)

        return {"agent": name, "output": output}

    @router.post("/{name}/stream")
    async def agents_stream(name: str, req: AgentRunRequest):
        """
        Executa um agente com streaming SSE.
        
        Retorna chunks de resposta em tempo real via Server-Sent Events.
        """
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        async def generate():
            try:
                # Executar agente
                agent.run(req.prompt)
                output = _get_agent_output(agent)
                
                # Simular streaming dividindo a resposta em chunks
                # Em produção, usar run_stream do Agno se disponível
                chunk_size = 50
                for i in range(0, len(output), chunk_size):
                    chunk = output[i:i + chunk_size]
                    yield f"data: {chunk}\n\n"
                    await asyncio.sleep(0.05)  # Pequeno delay para efeito visual
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    @router.delete("/{name}")
    async def agents_delete(name: str, user=Depends(get_current_user)):
        """Remove um agente."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        if name not in agents_map:
            raise HTTPException(status_code=404, detail="Agent not found")

        agents_map.pop(name, None)
        app.state.agents = agents_map

        return {"deleted": name}

    return router

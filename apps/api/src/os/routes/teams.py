"""
Router de Teams - CRUD e execução de times multi-agente.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agno.agent import Agent
from agno.team import Team

from src.auth.deps import get_current_user, is_auth_enabled
from src.os.middleware import setup_rate_limit, setup_security


class TeamCreateRequest(BaseModel):
    """Request para criar um novo time."""

    name: str
    members: Optional[List[str]] = None
    description: Optional[str] = None


class TeamRunRequest(BaseModel):
    """Request para executar um time."""

    prompt: str
    style: Optional[str] = None


class TeamMemberAddRequest(BaseModel):
    """Request para adicionar membro a um time."""

    agent: str


class TeamUpdateRequest(BaseModel):
    """Request para atualizar um time."""

    name: Optional[str] = None
    members: Optional[List[str]] = None
    description: Optional[str] = None


def _get_output(obj: Any) -> str:
    """Extrai output de um agente ou time de forma segura."""
    try:
        out = obj.get_last_run_output()
    except Exception:
        out = None

    if isinstance(out, dict):
        return out.get("content", "")
    return getattr(out, "content", "") or ""


def _run_pipeline(agents: List[Agent], prompts: List[str]) -> str:
    """
    Executa um pipeline sequencial de agentes.

    Args:
        agents: Lista de agentes a executar em sequência.
        prompts: Lista de prompts (um por agente).

    Returns:
        Output do último agente.
    """
    context = ""
    for agent, prompt in zip(agents, prompts):
        full_prompt = prompt.format(context=context) if "{context}" in prompt else prompt
        if context and "{context}" not in prompt:
            full_prompt = f"{prompt}\n\nContexto anterior:\n{context}"
        agent.run(full_prompt)
        context = _get_output(agent)
    return context


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de teams.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/teams", tags=["teams"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    # === Pipelines pré-definidos ===

    @router.post("/content/run")
    async def team_content_run(req: TeamRunRequest):
        """Executa pipeline de conteúdo: Researcher -> Writer."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")

        if not researcher or not writer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pipeline: Pesquisar -> Escrever
        researcher.run(f"Pesquise sobre: {req.prompt}. Forneça pontos objetivos e fontes.")
        research = _get_output(researcher)

        writer.run(
            f"Escreva um texto claro e bem estruturado em Markdown.\n\n"
            f"Pesquisa:\n{research}\n\n"
            f"Estilo: {req.style or 'neutro'}"
        )
        output = _get_output(writer)

        return {"team": "content", "output": output}

    @router.post("/review/run")
    async def team_review_run(req: TeamRunRequest):
        """Executa revisão de texto com o Reviewer."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        reviewer = agents_map.get("Reviewer")

        if not reviewer:
            raise HTTPException(status_code=500, detail="Reviewer agent not available")

        reviewer.run(
            f"Revise o texto a seguir, melhorando clareza, coesão e gramática.\n"
            f"Entregue uma seção com Comentários e outra com Versão Revisada.\n\n"
            f"Texto:\n{req.prompt}"
        )
        output = _get_output(reviewer)

        return {"team": "review", "output": output}

    @router.post("/content-pro/run")
    async def team_content_pro_run(req: TeamRunRequest):
        """Executa pipeline completo: Researcher -> Writer -> Reviewer."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")
        reviewer = agents_map.get("Reviewer")

        if not researcher or not writer or not reviewer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pesquisar
        researcher.run(f"Pesquise sobre: {req.prompt}. Forneça pontos objetivos e fontes.")
        research = _get_output(researcher)

        # Escrever
        writer.run(
            f"Escreva um texto claro e bem estruturado em Markdown.\n\n"
            f"Pesquisa:\n{research}\n\n"
            f"Estilo: {req.style or 'neutro'}"
        )
        draft = _get_output(writer)

        # Revisar
        reviewer.run(
            f"Revise e melhore o texto abaixo, mantendo o estilo indicado.\n"
            f"Entregue a versão final revisada.\n\n"
            f"Estilo: {req.style or 'neutro'}\n\n"
            f"Texto:\n{draft}"
        )
        final = _get_output(reviewer)

        return {"team": "content-pro", "output": final}

    # === CRUD de Times ===

    @router.post("")
    async def teams_create(req: TeamCreateRequest, user=Depends(get_current_user)):
        """Cria um novo time."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        key = req.name.lower()

        if key in teams_map:
            raise HTTPException(status_code=409, detail="Team already exists")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        members: List[Agent] = []

        if req.members:
            for m in req.members:
                agent = agents_map.get(m)
                if not agent:
                    raise HTTPException(status_code=400, detail=f"Unknown agent: {m}")
                members.append(agent)

        team = Team(
            members=members,
            name=req.name,
            description=req.description or "",
            markdown=True,
        )

        teams_map[key] = team
        app.state.teams = teams_map

        return {"name": req.name, "members": [getattr(a, "name", None) for a in members]}

    @router.get("")
    async def teams_list():
        """Lista todos os times."""
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        items = []

        for name, team in teams_map.items():
            try:
                mems = [getattr(a, "name", None) for a in getattr(team, "members", [])]
            except Exception:
                mems = []
            items.append({"name": name, "members": mems})

        return items

    @router.get("/{team_name}")
    async def teams_get(team_name: str):
        """Retorna detalhes de um time."""
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())

        if not team:
            # Nomes reservados para pipelines
            if team_name.lower() in ("content", "review", "content-pro"):
                return {"name": team_name.lower(), "members": [], "type": "pipeline"}
            raise HTTPException(status_code=404, detail="Team not found")

        try:
            mems = [getattr(a, "name", None) for a in getattr(team, "members", [])]
        except Exception:
            mems = []

        return {"name": team_name, "members": mems}

    @router.post("/{team_name}/members")
    async def teams_add_member(
        team_name: str, req: TeamMemberAddRequest, user=Depends(get_current_user)
    ):
        """Adiciona um membro a um time."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        agent = agents_map.get(req.agent)

        if not agent:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

        try:
            getattr(team, "members", []).append(agent)
        except Exception:
            raise HTTPException(status_code=500, detail="Unable to add member")

        return {"name": team_name, "added": req.agent}

    @router.delete("/{team_name}/members/{agent_name}")
    async def teams_remove_member(
        team_name: str, agent_name: str, user=Depends(get_current_user)
    ):
        """Remove um membro de um time."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        try:
            mems = getattr(team, "members", [])
            idx = None
            for i, m in enumerate(mems):
                if getattr(m, "name", None) == agent_name:
                    idx = i
                    break
            if idx is None:
                raise HTTPException(status_code=404, detail="Agent not in team")
            mems.pop(idx)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Unable to remove member")

        return {"name": team_name, "removed": agent_name}

    @router.put("/{team_name}")
    async def teams_update(
        team_name: str, req: TeamUpdateRequest, user=Depends(get_current_user)
    ):
        """Atualiza um time existente."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        key = team_name.lower()
        team = teams_map.get(key)

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})

        # Atualizar membros se fornecido
        if req.members is not None:
            new_members: List[Agent] = []
            for m in req.members:
                agent = agents_map.get(m)
                if not agent:
                    raise HTTPException(status_code=400, detail=f"Unknown agent: {m}")
                new_members.append(agent)
            team.members = new_members

        # Atualizar descrição se fornecida
        if req.description is not None:
            team.description = req.description

        # Atualizar nome se fornecido (recriar com novo nome)
        new_name = req.name or team_name
        if req.name and req.name.lower() != key:
            # Verificar se novo nome já existe
            if req.name.lower() in teams_map:
                raise HTTPException(status_code=409, detail="Team name already exists")
            # Remover time antigo e adicionar com novo nome
            teams_map.pop(key, None)
            team.name = req.name
            teams_map[req.name.lower()] = team

        app.state.teams = teams_map

        try:
            mems = [getattr(a, "name", None) for a in getattr(team, "members", [])]
        except Exception:
            mems = []

        return {
            "name": new_name,
            "members": mems,
            "description": getattr(team, "description", ""),
        }

    @router.delete("/{team_name}")
    async def teams_delete(team_name: str, user=Depends(get_current_user)):
        """Remove um time."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        key = team_name.lower()

        if key not in teams_map:
            raise HTTPException(status_code=404, detail="Team not found")

        teams_map.pop(key, None)
        app.state.teams = teams_map

        return {"deleted": team_name}

    @router.post("/{team_name}/run")
    async def team_run(team_name: str, req: TeamRunRequest):
        """Executa um time customizado."""
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        team.run(req.prompt)
        output = _get_output(team)

        return {"team": team_name, "output": output}

    return router

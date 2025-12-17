"""
Builder do AgentOS - Versão Modular.

Este módulo monta a aplicação FastAPI usando routers modulares,
mantendo compatibilidade com a API existente.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from agno.agent import Agent
from agno.os import AgentOS
from agno.team import Team

from src.agents import BaseAgent
from src.config import get_settings
from src.hitl.repo import get_repo
from src.utils.logger import get_logger

# Importar routers modulares
from src.os.routes import (
    create_agents_router,
    create_teams_router,
    create_workflows_router,
    create_rag_router,
    create_hitl_router,
    create_storage_router,
    create_auth_router,
    create_memory_router,
    create_metrics_router,
    create_admin_router,
    create_audit_router,
)
from src.os.routes.metrics import setup_metrics_middleware


def build_agents() -> List[Agent]:
    """
    Constrói os agentes padrão do sistema.

    Returns:
        Lista de agentes configurados
    """
    settings = get_settings()

    # Agente padrão (genérico)
    default_agent = BaseAgent.create(
        name=(settings.AGENTOS_AGENT_NAME or "Template Agent"),
        role=(settings.AGENTOS_AGENT_ROLE or "Você é um assistente útil do template"),
        instructions=[
            "Responda em português",
            "Seja conciso e claro",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    # Agente especializado: Pesquisador
    researcher = BaseAgent.create(
        name="Researcher",
        role="Pesquisador que busca informações confiáveis e organiza insights",
        instructions=[
            "Cite fontes quando possível",
            "Organize em tópicos",
            "Seja objetivo",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    # Agente especializado: Escritor
    writer = BaseAgent.create(
        name="Writer",
        role="Escritor que produz conteúdo claro e bem estruturado a partir de pesquisa fornecida",
        instructions=[
            "Escreva em Markdown",
            "Use títulos e seções",
            "Seja didático e conciso",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    # Agente especializado: Revisor
    reviewer = BaseAgent.create(
        name="Reviewer",
        role="Revisor que avalia clareza, coesão, gramática e consistência; sugere melhorias",
        instructions=[
            "Aponte problemas de clareza e consistência",
            "Sugira melhorias objetivas",
            "Quando solicitado, entregue versão revisada",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    return [default_agent, researcher, writer, reviewer]


def build_teams(agents_map: Dict[str, Agent]) -> Dict[str, Team]:
    """
    Constrói os times padrão do sistema.

    Args:
        agents_map: Mapa de agentes disponíveis

    Returns:
        Dicionário de times
    """
    teams: Dict[str, Team] = {}

    researcher = agents_map.get("Researcher")
    writer = agents_map.get("Writer")

    if researcher and writer:
        content_team = Team(
            members=[researcher, writer],
            name="ContentTeam",
            description="Time que pesquisa e escreve conteúdos",
            markdown=True,
        )
        teams["content"] = content_team

    return teams


def build_agent_os(agents: Optional[List[Agent]] = None) -> AgentOS:
    """
    Constrói o AgentOS com os agentes fornecidos.

    Args:
        agents: Lista de agentes (usa padrão se não fornecido)

    Returns:
        AgentOS configurado
    """
    agents = agents or build_agents()
    return AgentOS(agents=agents)


def get_app():
    """
    Constrói e retorna a aplicação FastAPI completa.

    Esta função:
    1. Cria os agentes padrão
    2. Monta o AgentOS
    3. Configura state da aplicação
    4. Registra todos os routers modulares
    5. Configura middlewares

    Returns:
        FastAPI app configurado
    """
    # Construir agentes e AgentOS
    agents = build_agents()
    agent_os = build_agent_os(agents)
    app = agent_os.get_app()

    # Configurar state da aplicação
    try:
        app.state.agents = {a.name: a for a in agents}
    except Exception:
        app.state.agents = {}

    # Configurar times
    try:
        app.state.teams = build_teams(app.state.agents)
    except Exception:
        app.state.teams = {}

    # Configurar logger
    try:
        app.state.logger = get_logger("api")
    except Exception:
        app.state.logger = None

    # Configurar HITL repository
    try:
        app.state.hitl_repo = get_repo()
    except Exception:
        app.state.hitl_repo = None

    # Inicializar workflows registry
    if not hasattr(app.state, "workflows_registry"):
        app.state.workflows_registry = {}

    # Marcar tempo de início
    if not hasattr(app.state, "started_at"):
        app.state.started_at = time.time()

    # Registrar routers modulares
    app.include_router(create_agents_router(app))
    app.include_router(create_teams_router(app))
    app.include_router(create_workflows_router(app))
    app.include_router(create_rag_router(app))
    app.include_router(create_hitl_router(app))
    app.include_router(create_storage_router(app))
    app.include_router(create_auth_router(app))
    app.include_router(create_memory_router(app))
    app.include_router(create_metrics_router(app))
    app.include_router(create_admin_router(app))
    app.include_router(create_audit_router(app))

    # Configurar middleware de métricas
    setup_metrics_middleware(app)

    return app

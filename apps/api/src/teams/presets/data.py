"""
Time de análise de dados.
"""

from __future__ import annotations

from typing import Dict, Optional

from agno.agent import Agent
from agno.team import Team

from src.teams import BaseTeam
from src.agents.domains import DataAgent


def create_data_team(
    agents_map: Optional[Dict[str, Agent]] = None,
    model_provider: Optional[str] = None,
) -> Team:
    """
    Cria time de análise de dados.

    Membros:
    - DataEngineer: ETL e preparação de dados
    - DataAnalyst: Análise e insights
    - DataReporter: Relatórios e visualizações

    Args:
        agents_map: Mapa de agentes existentes (opcional)
        model_provider: Provider do modelo

    Returns:
        Team configurado
    """
    from src.agents import BaseAgent

    data_engineer = BaseAgent.create(
        name="DataEngineer",
        role="Especialista em engenharia de dados",
        instructions=[
            "Prepare e transforme dados para análise",
            "Garanta qualidade e integridade dos dados",
            "Otimize queries e pipelines",
            "Responda em português",
        ],
        model_provider=model_provider,
    )

    data_analyst = DataAgent.create(
        name="DataAnalyst",
        model_provider=model_provider,
    )

    data_reporter = BaseAgent.create(
        name="DataReporter",
        role="Especialista em relatórios de dados",
        instructions=[
            "Gere relatórios claros e visuais",
            "Destaque insights principais",
            "Use gráficos apropriados",
            "Responda em português",
        ],
        model_provider=model_provider,
    )

    return BaseTeam.create(
        name="DataAnalysisTeam",
        members=[data_engineer, data_analyst, data_reporter],
        description="Time de análise de dados completa",
    )

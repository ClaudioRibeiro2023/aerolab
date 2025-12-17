"""
Time de análise geoespacial.
"""

from __future__ import annotations

from typing import Dict, Optional

from agno.agent import Agent
from agno.team import Team

from src.teams import BaseTeam
from src.agents.domains import GeoAgent, DataAgent


def create_geo_team(
    agents_map: Optional[Dict[str, Agent]] = None,
    model_provider: Optional[str] = None,
) -> Team:
    """
    Cria time de análise geoespacial.

    Membros:
    - GeoAnalyst: Análise espacial e mapas
    - DataAnalyst: Análise de dados
    - Reporter: Geração de relatórios

    Args:
        agents_map: Mapa de agentes existentes (opcional)
        model_provider: Provider do modelo

    Returns:
        Team configurado
    """
    from src.agents import BaseAgent

    # Criar agentes especializados
    geo_analyst = GeoAgent.create(
        name="GeoAnalyst",
        model_provider=model_provider,
    )

    data_analyst = DataAgent.create(
        name="DataAnalyst",
        model_provider=model_provider,
    )

    reporter = BaseAgent.create(
        name="GeoReporter",
        role="Especialista em relatórios geoespaciais",
        instructions=[
            "Gere relatórios claros sobre análises geoespaciais",
            "Use visualizações e mapas quando possível",
            "Forneça conclusões acionáveis",
            "Responda em português",
        ],
        model_provider=model_provider,
    )

    return BaseTeam.create(
        name="GeoAnalysisTeam",
        members=[geo_analyst, data_analyst, reporter],
        description="Time de análise geoespacial completa",
    )

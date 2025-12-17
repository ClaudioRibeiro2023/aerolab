"""
Times de criação de conteúdo.
"""

from __future__ import annotations

from typing import Dict, Optional

from agno.agent import Agent
from agno.team import Team

from src.teams import BaseTeam


def create_content_team(agents_map: Dict[str, Agent]) -> Optional[Team]:
    """
    Cria time de conteúdo: Researcher -> Writer.

    Args:
        agents_map: Mapa de agentes disponíveis

    Returns:
        Team ou None se agentes não disponíveis
    """
    researcher = agents_map.get("Researcher")
    writer = agents_map.get("Writer")

    if not researcher or not writer:
        return None

    return BaseTeam.create(
        name="ContentTeam",
        members=[researcher, writer],
        description="Time que pesquisa e escreve conteúdos",
    )


def create_content_pro_team(agents_map: Dict[str, Agent]) -> Optional[Team]:
    """
    Cria time de conteúdo completo: Researcher -> Writer -> Reviewer.

    Args:
        agents_map: Mapa de agentes disponíveis

    Returns:
        Team ou None se agentes não disponíveis
    """
    researcher = agents_map.get("Researcher")
    writer = agents_map.get("Writer")
    reviewer = agents_map.get("Reviewer")

    if not researcher or not writer or not reviewer:
        return None

    return BaseTeam.create(
        name="ContentProTeam",
        members=[researcher, writer, reviewer],
        description="Time completo de criação de conteúdo com revisão",
    )

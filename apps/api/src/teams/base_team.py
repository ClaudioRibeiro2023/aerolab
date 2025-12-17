"""
Classe base para times multi-agente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agno.agent import Agent
from agno.team import Team


@dataclass
class TeamConfig:
    """Configuração de um time."""

    name: str
    description: str = ""
    members: List[str] = field(default_factory=list)
    markdown: bool = True
    mode: str = "sequential"  # sequential, parallel, router


class BaseTeam:
    """
    Factory base para criar times multi-agente.

    Uso:
        team = BaseTeam.create(
            name="ContentTeam",
            members=[researcher, writer],
            description="Time de criação de conteúdo"
        )
    """

    @classmethod
    def create(
        cls,
        name: str,
        members: List[Agent],
        description: Optional[str] = None,
        markdown: bool = True,
        **kwargs,
    ) -> Team:
        """
        Cria um time de agentes.

        Args:
            name: Nome do time
            members: Lista de agentes membros
            description: Descrição do time
            markdown: Usar formatação markdown
            **kwargs: Argumentos adicionais para Team

        Returns:
            Team configurado
        """
        return Team(
            name=name,
            members=members,
            description=description or f"Time {name}",
            markdown=markdown,
            **kwargs,
        )

    @classmethod
    def from_config(cls, config: TeamConfig, agents_map: Dict[str, Agent]) -> Team:
        """
        Cria um time a partir de configuração.

        Args:
            config: Configuração do time
            agents_map: Mapa de agentes disponíveis {nome: agent}

        Returns:
            Team configurado

        Raises:
            ValueError: Se algum agente não for encontrado
        """
        members = []
        for member_name in config.members:
            agent = agents_map.get(member_name)
            if not agent:
                raise ValueError(f"Agente não encontrado: {member_name}")
            members.append(agent)

        return cls.create(
            name=config.name,
            members=members,
            description=config.description,
            markdown=config.markdown,
        )


class TeamRegistry:
    """Registry de times disponíveis."""

    def __init__(self):
        self._teams: Dict[str, Team] = {}
        self._configs: Dict[str, TeamConfig] = {}

    def register(self, team: Team) -> None:
        """Registra um time."""
        self._teams[team.name.lower()] = team

    def register_config(self, config: TeamConfig) -> None:
        """Registra uma configuração de time."""
        self._configs[config.name.lower()] = config

    def get(self, name: str) -> Optional[Team]:
        """Obtém um time pelo nome."""
        return self._teams.get(name.lower())

    def get_config(self, name: str) -> Optional[TeamConfig]:
        """Obtém uma configuração pelo nome."""
        return self._configs.get(name.lower())

    def list_teams(self) -> List[str]:
        """Lista nomes dos times registrados."""
        return list(self._teams.keys())

    def list_configs(self) -> List[str]:
        """Lista nomes das configurações registradas."""
        return list(self._configs.keys())


# Registry global
_registry = TeamRegistry()


def get_team_registry() -> TeamRegistry:
    """Retorna o registry global de times."""
    return _registry

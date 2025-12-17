"""
Módulo de times multi-agente.

Estrutura:
- base_team.py: Factory base para criar times
- presets/: Times pré-configurados por domínio
"""

from .base_team import BaseTeam, TeamConfig

__all__ = [
    "BaseTeam",
    "TeamConfig",
]

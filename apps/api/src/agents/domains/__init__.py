"""
Agentes especializados por domínio.

Cada agente é pré-configurado com ferramentas e instruções
específicas para seu domínio de atuação.
"""

from .geo import GeoAgent
from .data import DataAgent
from .dev import DevAgent
from .finance import FinanceAgent
from .legal import LegalAgent
from .corporate import CorporateAgent
from .testing import PlatformTesterAgent, get_platform_tester

__all__ = [
    "GeoAgent",
    "DataAgent",
    "DevAgent",
    "FinanceAgent",
    "LegalAgent",
    "CorporateAgent",
    "PlatformTesterAgent",
    "get_platform_tester",
]

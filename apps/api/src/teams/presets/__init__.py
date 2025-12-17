"""
Times pré-configurados por domínio.
"""

from .content import create_content_team, create_content_pro_team
from .geo import create_geo_team
from .data import create_data_team
from .finance import create_finance_team

__all__ = [
    "create_content_team",
    "create_content_pro_team",
    "create_geo_team",
    "create_data_team",
    "create_finance_team",
]

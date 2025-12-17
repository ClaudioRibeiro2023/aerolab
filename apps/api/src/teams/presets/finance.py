"""
Time de análise financeira.
"""

from __future__ import annotations

from typing import Dict, Optional

from agno.agent import Agent
from agno.team import Team

from src.teams import BaseTeam
from src.agents.domains import FinanceAgent


def create_finance_team(
    agents_map: Optional[Dict[str, Agent]] = None,
    model_provider: Optional[str] = None,
) -> Team:
    """
    Cria time de análise financeira.

    Membros:
    - MarketAnalyst: Análise de mercado
    - RiskAnalyst: Análise de risco
    - FinanceReporter: Relatórios financeiros

    Args:
        agents_map: Mapa de agentes existentes (opcional)
        model_provider: Provider do modelo

    Returns:
        Team configurado
    """
    from src.agents import BaseAgent

    market_analyst = FinanceAgent.create(
        name="MarketAnalyst",
        role="Especialista em análise de mercado",
        model_provider=model_provider,
    )

    risk_analyst = BaseAgent.create(
        name="RiskAnalyst",
        role="Especialista em análise de risco",
        instructions=[
            "Avalie riscos financeiros de forma conservadora",
            "Identifique fatores de risco e mitigações",
            "Use métricas quantitativas quando possível",
            "Responda em português",
        ],
        model_provider=model_provider,
    )

    finance_reporter = BaseAgent.create(
        name="FinanceReporter",
        role="Especialista em relatórios financeiros",
        instructions=[
            "Gere relatórios financeiros claros",
            "Use gráficos e tabelas apropriados",
            "Destaque métricas-chave",
            "Responda em português",
        ],
        model_provider=model_provider,
    )

    return BaseTeam.create(
        name="FinanceAnalysisTeam",
        members=[market_analyst, risk_analyst, finance_reporter],
        description="Time de análise financeira completa",
    )

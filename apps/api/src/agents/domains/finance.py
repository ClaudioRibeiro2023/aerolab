"""
Agente especializado em Análise Financeira.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class FinanceAgent:
    """
    Factory para criar agentes financeiros.

    Especialidades:
    - Análise de mercado
    - Valuation e DCF
    - Análise de risco
    - Indicadores financeiros
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em análise financeira",
        "Analise dados de mercado com rigor técnico",
        "Calcule indicadores financeiros corretamente",
        "Avalie riscos de forma conservadora",
        "Cite fontes de dados financeiros",
        "Não forneça recomendações de investimento diretas",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "FinancialAnalyst",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """Cria um agente financeiro."""
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        tools = []
        try:
            from src.tools.finance.market import MarketTool
            tools.append(MarketTool())
        except Exception:
            pass

        try:
            from src.tools.finance.analysis import FinancialAnalysisTool
            tools.append(FinancialAnalysisTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em análise financeira",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

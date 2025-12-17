"""
Agente especializado em Análise Corporativa.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class CorporateAgent:
    """
    Factory para criar agentes corporativos.

    Especialidades:
    - Análise estratégica (SWOT, Porter, PESTEL)
    - Planejamento empresarial
    - Análise de mercado
    - Gestão de projetos
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em estratégia corporativa",
        "Use frameworks estratégicos apropriados (SWOT, Porter, PESTEL)",
        "Analise cenários de forma estruturada",
        "Forneça recomendações acionáveis",
        "Considere aspectos financeiros, operacionais e de mercado",
        "Documente premissas e limitações das análises",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "StrategyConsultant",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """Cria um agente corporativo."""
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        tools = []
        try:
            from src.tools.corporate.strategy import StrategyTool
            tools.append(StrategyTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em estratégia corporativa",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

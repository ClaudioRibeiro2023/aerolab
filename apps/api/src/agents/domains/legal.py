"""
Agente especializado em Consultoria Jurídica.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class LegalAgent:
    """
    Factory para criar agentes jurídicos.

    Especialidades:
    - Análise de contratos
    - Pesquisa de legislação
    - Compliance
    - Due diligence
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em análise jurídica",
        "Analise documentos legais com precisão técnica",
        "Cite legislação e jurisprudência relevantes",
        "Identifique riscos e cláusulas problemáticas",
        "Não forneça aconselhamento jurídico definitivo",
        "Recomende consulta a advogado para decisões importantes",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "LegalAnalyst",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """Cria um agente jurídico."""
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        tools = []
        try:
            from src.tools.legal.search import LegalSearchTool
            tools.append(LegalSearchTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em análise jurídica",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

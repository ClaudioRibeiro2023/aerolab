"""
Agente especializado em Dados e Analytics.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class DataAgent:
    """
    Factory para criar agentes de dados e analytics.

    Especialidades:
    - Consultas SQL
    - Análise de dados
    - Visualização de dados
    - ETL e pipelines
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em dados e analytics",
        "Escreva queries SQL otimizadas e seguras",
        "Analise dados com rigor estatístico",
        "Forneça insights acionáveis baseados em dados",
        "Use visualizações apropriadas para cada tipo de dado",
        "Documente suas análises de forma clara",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "DataAnalyst",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """
        Cria um agente de dados.

        Args:
            name: Nome do agente
            role: Papel customizado
            instructions: Instruções adicionais
            model_provider: Provider do modelo
            model_id: ID do modelo
            use_database: Usar persistência
            **kwargs: Argumentos adicionais

        Returns:
            Agent configurado para dados
        """
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        tools = []
        try:
            from src.tools.database.sql import SQLTool
            tools.append(SQLTool())
        except Exception:
            pass

        try:
            from src.tools.database.analytics import AnalyticsTool
            tools.append(AnalyticsTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em dados e analytics",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

"""
Agente especializado em Geolocalização.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class GeoAgent:
    """
    Factory para criar agentes de geolocalização.

    Especialidades:
    - Análise espacial
    - Geocoding e rotas
    - Visualização de mapas
    - Análise de mobilidade urbana
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em análise geoespacial e localização",
        "Analise dados geográficos com precisão técnica",
        "Use coordenadas no formato (latitude, longitude)",
        "Forneça visualizações e mapas quando possível",
        "Considere aspectos de mobilidade urbana e acessibilidade",
        "Cite fontes de dados geográficos quando relevante",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "GeoAnalyst",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """
        Cria um agente de geolocalização.

        Args:
            name: Nome do agente
            role: Papel customizado (usa padrão se não fornecido)
            instructions: Instruções adicionais
            model_provider: Provider do modelo
            model_id: ID do modelo
            use_database: Usar persistência
            **kwargs: Argumentos adicionais para BaseAgent

        Returns:
            Agent configurado para geolocalização
        """
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        # Carregar ferramentas de geo se disponíveis
        tools = []
        try:
            from src.tools.geo.mapbox import MapboxTool
            tools.append(MapboxTool())
        except Exception:
            pass

        try:
            from src.tools.geo.spatial import SpatialTool
            tools.append(SpatialTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em análise geoespacial e localização",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

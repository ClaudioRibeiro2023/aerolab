"""
Agente especializado em Desenvolvimento e DevOps.
"""

from __future__ import annotations

from typing import List, Optional

from agno.agent import Agent

from src.agents import BaseAgent


class DevAgent:
    """
    Factory para criar agentes de desenvolvimento.

    Especialidades:
    - Gestão de repositórios GitHub
    - Deploy e CI/CD
    - Integração com Supabase
    - Arquitetura de sistemas
    """

    DEFAULT_INSTRUCTIONS = [
        "Você é um especialista em desenvolvimento e DevOps",
        "Siga boas práticas de código e arquitetura",
        "Priorize segurança em todas as operações",
        "Documente decisões técnicas importantes",
        "Use Git flow e versionamento semântico",
        "Automatize processos repetitivos",
        "Responda em português",
    ]

    @classmethod
    def create(
        cls,
        name: str = "DevOpsEngineer",
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = True,
        **kwargs,
    ) -> Agent:
        """
        Cria um agente de desenvolvimento.

        Args:
            name: Nome do agente
            role: Papel customizado
            instructions: Instruções adicionais
            model_provider: Provider do modelo
            model_id: ID do modelo
            use_database: Usar persistência
            **kwargs: Argumentos adicionais

        Returns:
            Agent configurado para desenvolvimento
        """
        final_instructions = cls.DEFAULT_INSTRUCTIONS.copy()
        if instructions:
            final_instructions.extend(instructions)

        tools = []
        try:
            from src.tools.devops.github import GitHubTool
            tools.append(GitHubTool())
        except Exception:
            pass

        try:
            from src.tools.devops.netlify import NetlifyTool
            tools.append(NetlifyTool())
        except Exception:
            pass

        try:
            from src.tools.devops.supabase import SupabaseTool
            tools.append(SupabaseTool())
        except Exception:
            pass

        return BaseAgent.create(
            name=name,
            role=role or "Especialista em desenvolvimento e DevOps",
            instructions=final_instructions,
            tools=tools if tools else None,
            model_provider=model_provider,
            model_id=model_id,
            use_database=use_database,
            **kwargs,
        )

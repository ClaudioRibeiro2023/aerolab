"""
Ferramenta de pesquisa com IA via Perplexity.

Perplexity combina pesquisa web com LLM para respostas
atualizadas e com citações.

Requer: PERPLEXITY_API_KEY no .env
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="llm")
class PerplexityTool(BaseTool):
    """
    Ferramenta para pesquisa com IA via Perplexity API.

    Funcionalidades:
    - ask: Pergunta com pesquisa integrada
    - research: Pesquisa aprofundada
    """

    name = "perplexity"
    description = "Pesquisa com IA via Perplexity"
    version = "1.0.0"
    requires_auth = True

    BASE_URL = "https://api.perplexity.ai"

    # Modelos disponíveis (atualizado Nov 2025)
    MODELS = {
        "sonar": "sonar",
        "sonar-pro": "sonar-pro",
        "sonar-reasoning": "sonar-reasoning",
        # Aliases para compatibilidade
        "sonar-large": "sonar-pro",
        "sonar-huge": "sonar-pro",
    }

    def _setup(self) -> None:
        """Configura cliente Perplexity."""
        self.api_key = self.config.get("api_key") or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ToolError("PERPLEXITY_API_KEY não configurada", tool_name=self.name)
        self._initialized = True

    def _headers(self) -> Dict[str, str]:
        """Headers para requisições."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação Perplexity."""
        actions = {
            "ask": self._ask,
            "research": self._research,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _ask(
        self,
        question: str,
        model: str = "sonar",
        system_prompt: Optional[str] = None,
    ) -> ToolResult:
        """
        Faz uma pergunta com pesquisa integrada.

        Args:
            question: Pergunta
            model: Modelo (sonar, sonar-large, sonar-huge)
            system_prompt: Prompt de sistema opcional

        Returns:
            ToolResult com resposta e citações
        """
        try:
            import requests

            model_id = self.MODELS.get(model, model)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": question})

            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model_id,
                    "messages": messages,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            return ToolResult.ok({
                "question": question,
                "answer": message.get("content"),
                "citations": data.get("citations", []),
                "model": model_id,
                "usage": data.get("usage", {}),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na pergunta: {str(e)}")

    def _research(
        self,
        topic: str,
        depth: str = "basic",
    ) -> ToolResult:
        """
        Pesquisa aprofundada sobre um tópico.

        Args:
            topic: Tópico de pesquisa
            depth: basic ou deep

        Returns:
            ToolResult com análise completa
        """
        model = "sonar-large" if depth == "deep" else "sonar"

        system_prompt = """Você é um pesquisador especializado. 
Forneça uma análise completa e estruturada do tópico, incluindo:
1. Visão geral
2. Pontos principais
3. Dados e estatísticas relevantes
4. Perspectivas diferentes
5. Conclusão

Cite suas fontes."""

        return self._ask(
            question=f"Faça uma pesquisa completa sobre: {topic}",
            model=model,
            system_prompt=system_prompt,
        )

"""
Ferramenta de busca jurídica.
"""

from __future__ import annotations

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="legal")
class LegalSearchTool(BaseTool):
    """
    Ferramenta para busca em bases jurídicas.

    Funcionalidades:
    - search_legislation: Buscar leis
    - search_jurisprudence: Buscar jurisprudência
    """

    name = "legal_search"
    description = "Busca em bases jurídicas"
    version = "1.0.0"

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa busca jurídica."""
        actions = {
            "search_legislation": self._search_legislation,
            "search_jurisprudence": self._search_jurisprudence,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _search_legislation(self, query: str, limit: int = 10) -> ToolResult:
        """Busca legislação (stub para integração futura)."""
        return ToolResult.ok({
            "query": query,
            "results": [],
            "message": "Integração com base de legislação pendente",
        })

    def _search_jurisprudence(self, query: str, limit: int = 10) -> ToolResult:
        """Busca jurisprudência (stub para integração futura)."""
        return ToolResult.ok({
            "query": query,
            "results": [],
            "message": "Integração com base de jurisprudência pendente",
        })

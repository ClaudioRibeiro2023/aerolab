"""
Ferramenta de pesquisa web via Tavily.

Requer: TAVILY_API_KEY no .env
"""

from __future__ import annotations

import os

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="research")
class TavilyTool(BaseTool):
    """
    Ferramenta para pesquisa web via Tavily API.

    Funcionalidades:
    - search: Pesquisa web
    - search_news: Pesquisa de notícias
    - search_context: Pesquisa com contexto para RAG
    """

    name = "tavily"
    description = "Pesquisa web via Tavily API"
    version = "1.0.0"
    requires_auth = True

    def _setup(self) -> None:
        """Configura cliente Tavily."""
        self.api_key = self.config.get("api_key") or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ToolError("TAVILY_API_KEY não configurada", tool_name=self.name)

        self._client = None
        self._initialized = True

    def _get_client(self):
        """Obtém cliente Tavily."""
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                raise ToolError(
                    "tavily-python não instalado. Use: pip install tavily-python",
                    tool_name=self.name,
                )
        return self._client

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa pesquisa."""
        actions = {
            "search": self._search,
            "search_news": self._search_news,
            "search_context": self._search_context,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        search_depth: str = "basic",
    ) -> ToolResult:
        """
        Pesquisa web.

        Args:
            query: Termo de pesquisa
            max_results: Máximo de resultados
            include_answer: Incluir resposta gerada
            search_depth: basic ou advanced

        Returns:
            ToolResult com resultados
        """
        try:
            client = self._get_client()

            response = client.search(
                query=query,
                max_results=max_results,
                include_answer=include_answer,
                search_depth=search_depth,
            )

            return ToolResult.ok({
                "query": query,
                "answer": response.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content"),
                        "score": r.get("score"),
                    }
                    for r in response.get("results", [])
                ],
                "count": len(response.get("results", [])),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na pesquisa: {str(e)}")

    def _search_news(self, query: str, max_results: int = 5) -> ToolResult:
        """Pesquisa notícias recentes."""
        try:
            client = self._get_client()

            response = client.search(
                query=query,
                max_results=max_results,
                topic="news",
            )

            return ToolResult.ok({
                "query": query,
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content"),
                        "published_date": r.get("published_date"),
                    }
                    for r in response.get("results", [])
                ],
                "count": len(response.get("results", [])),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na pesquisa de notícias: {str(e)}")

    def _search_context(self, query: str, max_tokens: int = 4000) -> ToolResult:
        """Pesquisa com contexto otimizado para RAG."""
        try:
            client = self._get_client()

            context = client.get_search_context(
                query=query,
                max_tokens=max_tokens,
            )

            return ToolResult.ok({
                "query": query,
                "context": context,
                "tokens": len(context.split()),  # Aproximado
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na pesquisa de contexto: {str(e)}")

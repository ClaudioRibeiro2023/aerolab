"""
Ferramenta de busca na Wikipedia.

API pública, não requer autenticação.
"""

from __future__ import annotations

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="research")
class WikipediaTool(BaseTool):
    """
    Ferramenta para busca na Wikipedia.

    Funcionalidades:
    - search: Buscar artigos
    - summary: Resumo de um artigo
    - content: Conteúdo completo de um artigo
    """

    name = "wikipedia"
    description = "Busca na Wikipedia (API pública)"
    version = "1.0.0"
    requires_auth = False

    BASE_URL = "https://pt.wikipedia.org/api/rest_v1"
    SEARCH_URL = "https://pt.wikipedia.org/w/api.php"
    USER_AGENT = "AgnoTemplate/1.0 (https://github.com/agno-agi/agno; contact@example.com)"

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa busca."""
        actions = {
            "search": self._search,
            "summary": self._summary,
            "content": self._content,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _search(self, query: str, limit: int = 10) -> ToolResult:
        """
        Busca artigos na Wikipedia.

        Args:
            query: Termo de busca
            limit: Máximo de resultados

        Returns:
            ToolResult com títulos encontrados
        """
        try:
            import requests

            response = requests.get(
                self.SEARCH_URL,
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": limit,
                    "format": "json",
                },
                headers={"User-Agent": self.USER_AGENT},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # opensearch retorna [query, [títulos], [descrições], [urls]]
            titles = data[1] if len(data) > 1 else []
            descriptions = data[2] if len(data) > 2 else []
            urls = data[3] if len(data) > 3 else []

            results = []
            for i, title in enumerate(titles):
                results.append({
                    "title": title,
                    "description": descriptions[i] if i < len(descriptions) else "",
                    "url": urls[i] if i < len(urls) else "",
                })

            return ToolResult.ok({
                "query": query,
                "results": results,
                "count": len(results),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na busca: {str(e)}")

    def _summary(self, title: str) -> ToolResult:
        """
        Obtém resumo de um artigo.

        Args:
            title: Título do artigo

        Returns:
            ToolResult com resumo
        """
        try:
            import requests

            # Usar API REST para resumo
            response = requests.get(
                f"{self.BASE_URL}/page/summary/{title}",
                headers={"Accept": "application/json", "User-Agent": self.USER_AGENT},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult.ok({
                "title": data.get("title"),
                "extract": data.get("extract"),
                "description": data.get("description"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                "thumbnail": data.get("thumbnail", {}).get("source"),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter resumo: {str(e)}")

    def _content(self, title: str, sections: bool = False) -> ToolResult:
        """
        Obtém conteúdo de um artigo.

        Args:
            title: Título do artigo
            sections: Se deve incluir lista de seções

        Returns:
            ToolResult com conteúdo
        """
        try:
            import requests

            # Usar API de parse para conteúdo em texto
            response = requests.get(
                self.SEARCH_URL,
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts|sections" if sections else "extracts",
                    "explaintext": True,
                    "format": "json",
                },
                headers={"User-Agent": self.USER_AGENT},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            page = list(pages.values())[0] if pages else {}

            result = {
                "title": page.get("title"),
                "content": page.get("extract", "")[:10000],  # Limitar tamanho
                "pageid": page.get("pageid"),
            }

            if sections and "sections" in page:
                result["sections"] = [
                    {"title": s.get("line"), "level": s.get("level")}
                    for s in page.get("sections", [])
                ]

            return ToolResult.ok(result)
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter conteúdo: {str(e)}")

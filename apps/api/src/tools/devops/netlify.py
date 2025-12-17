"""
Ferramenta de integração com Netlify.

Requer:
- NETLIFY_AUTH_TOKEN no .env
"""

from __future__ import annotations

import os
from typing import Dict

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="devops")
class NetlifyTool(BaseTool):
    """
    Ferramenta para operações no Netlify.

    Funcionalidades:
    - sites: Listar sites
    - deploys: Listar deploys
    - deploy_status: Status de um deploy
    """

    name = "netlify"
    description = "Integração com Netlify API"
    version = "1.0.0"
    requires_auth = True

    BASE_URL = "https://api.netlify.com/api/v1"

    def _setup(self) -> None:
        """Configura autenticação."""
        self.token = self.config.get("token") or os.getenv("NETLIFY_AUTH_TOKEN")
        if not self.token:
            raise ToolError("NETLIFY_AUTH_TOKEN não configurado", tool_name=self.name)
        self._initialized = True

    def _headers(self) -> Dict[str, str]:
        """Headers para requisições."""
        return {"Authorization": f"Bearer {self.token}"}

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação do Netlify."""
        actions = {
            "sites": self._list_sites,
            "deploys": self._list_deploys,
            "deploy_status": self._deploy_status,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _list_sites(self) -> ToolResult:
        """Lista todos os sites."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/sites",
                headers=self._headers(),
                timeout=15,
            )
            response.raise_for_status()
            sites = response.json()

            return ToolResult.ok({
                "sites": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "url": s["url"],
                        "ssl_url": s.get("ssl_url"),
                        "state": s.get("state"),
                    }
                    for s in sites
                ],
                "count": len(sites),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar sites: {str(e)}")

    def _list_deploys(self, site_id: str, limit: int = 10) -> ToolResult:
        """Lista deploys de um site."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/sites/{site_id}/deploys",
                headers=self._headers(),
                params={"per_page": limit},
                timeout=15,
            )
            response.raise_for_status()
            deploys = response.json()

            return ToolResult.ok({
                "deploys": [
                    {
                        "id": d["id"],
                        "state": d["state"],
                        "created_at": d.get("created_at"),
                        "deploy_url": d.get("deploy_url"),
                        "branch": d.get("branch"),
                    }
                    for d in deploys
                ],
                "site_id": site_id,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar deploys: {str(e)}")

    def _deploy_status(self, deploy_id: str) -> ToolResult:
        """Obtém status de um deploy."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/deploys/{deploy_id}",
                headers=self._headers(),
                timeout=15,
            )
            response.raise_for_status()
            deploy = response.json()

            return ToolResult.ok({
                "id": deploy["id"],
                "state": deploy["state"],
                "created_at": deploy.get("created_at"),
                "published_at": deploy.get("published_at"),
                "deploy_url": deploy.get("deploy_url"),
                "ssl_url": deploy.get("ssl_url"),
                "error_message": deploy.get("error_message"),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter status: {str(e)}")

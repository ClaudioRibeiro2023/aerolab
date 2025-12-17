"""
Ferramenta de integração com GitHub.

Requer:
- GITHUB_TOKEN no .env
- pip install PyGithub (opcional, usa requests se não disponível)
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="devops")
class GitHubTool(BaseTool):
    """
    Ferramenta para operações no GitHub.

    Funcionalidades:
    - repos: Listar repositórios
    - create_repo: Criar repositório
    - issues: Listar/criar issues
    - pulls: Listar pull requests
    - workflows: Listar GitHub Actions
    """

    name = "github"
    description = "Integração com GitHub API"
    version = "1.0.0"
    requires_auth = True

    BASE_URL = "https://api.github.com"

    def _setup(self) -> None:
        """Configura autenticação."""
        self.token = self.config.get("token") or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ToolError("GITHUB_TOKEN não configurado", tool_name=self.name)
        self._initialized = True

    def _headers(self) -> Dict[str, str]:
        """Headers para requisições."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação do GitHub."""
        actions = {
            "repos": self._list_repos,
            "create_repo": self._create_repo,
            "issues": self._list_issues,
            "create_issue": self._create_issue,
            "pulls": self._list_pulls,
            "workflows": self._list_workflows,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _list_repos(self, user: Optional[str] = None, limit: int = 30) -> ToolResult:
        """Lista repositórios."""
        try:
            import requests

            if user:
                url = f"{self.BASE_URL}/users/{user}/repos"
            else:
                url = f"{self.BASE_URL}/user/repos"

            response = requests.get(
                url,
                headers=self._headers(),
                params={"per_page": limit, "sort": "updated"},
                timeout=15,
            )
            response.raise_for_status()
            repos = response.json()

            return ToolResult.ok({
                "repos": [
                    {
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "private": r["private"],
                        "url": r["html_url"],
                        "description": r.get("description"),
                    }
                    for r in repos
                ],
                "count": len(repos),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar repos: {str(e)}")

    def _create_repo(
        self,
        name: str,
        description: Optional[str] = None,
        private: bool = True,
    ) -> ToolResult:
        """Cria um repositório."""
        try:
            import requests

            response = requests.post(
                f"{self.BASE_URL}/user/repos",
                headers=self._headers(),
                json={
                    "name": name,
                    "description": description,
                    "private": private,
                    "auto_init": True,
                },
                timeout=15,
            )
            response.raise_for_status()
            repo = response.json()

            return ToolResult.ok({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "url": repo["html_url"],
                "clone_url": repo["clone_url"],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao criar repo: {str(e)}")

    def _list_issues(self, repo: str, state: str = "open", limit: int = 30) -> ToolResult:
        """Lista issues de um repositório."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/repos/{repo}/issues",
                headers=self._headers(),
                params={"state": state, "per_page": limit},
                timeout=15,
            )
            response.raise_for_status()
            issues = response.json()

            return ToolResult.ok({
                "issues": [
                    {
                        "number": i["number"],
                        "title": i["title"],
                        "state": i["state"],
                        "url": i["html_url"],
                        "labels": [label["name"] for label in i.get("labels", [])],
                    }
                    for i in issues
                    if "pull_request" not in i  # Excluir PRs
                ],
                "repo": repo,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar issues: {str(e)}")

    def _create_issue(
        self,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> ToolResult:
        """Cria uma issue."""
        try:
            import requests

            response = requests.post(
                f"{self.BASE_URL}/repos/{repo}/issues",
                headers=self._headers(),
                json={
                    "title": title,
                    "body": body,
                    "labels": labels or [],
                },
                timeout=15,
            )
            response.raise_for_status()
            issue = response.json()

            return ToolResult.ok({
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao criar issue: {str(e)}")

    def _list_pulls(self, repo: str, state: str = "open", limit: int = 30) -> ToolResult:
        """Lista pull requests."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/repos/{repo}/pulls",
                headers=self._headers(),
                params={"state": state, "per_page": limit},
                timeout=15,
            )
            response.raise_for_status()
            pulls = response.json()

            return ToolResult.ok({
                "pulls": [
                    {
                        "number": p["number"],
                        "title": p["title"],
                        "state": p["state"],
                        "url": p["html_url"],
                        "head": p["head"]["ref"],
                        "base": p["base"]["ref"],
                    }
                    for p in pulls
                ],
                "repo": repo,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar PRs: {str(e)}")

    def _list_workflows(self, repo: str) -> ToolResult:
        """Lista GitHub Actions workflows."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/repos/{repo}/actions/workflows",
                headers=self._headers(),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult.ok({
                "workflows": [
                    {
                        "id": w["id"],
                        "name": w["name"],
                        "path": w["path"],
                        "state": w["state"],
                    }
                    for w in data.get("workflows", [])
                ],
                "repo": repo,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar workflows: {str(e)}")

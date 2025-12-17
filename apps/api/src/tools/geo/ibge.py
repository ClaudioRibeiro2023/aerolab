"""
Ferramenta de integração com API do IBGE.

API pública, não requer autenticação.
"""

from __future__ import annotations

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="geo")
class IBGETool(BaseTool):
    """
    Ferramenta para dados geográficos do IBGE.

    Funcionalidades:
    - estados: Listar estados brasileiros
    - municipios: Listar municípios de um estado
    - localidade: Buscar localidade por nome
    - regioes: Listar regiões do Brasil
    """

    name = "ibge"
    description = "Dados geográficos do IBGE (API pública)"
    version = "1.0.0"
    requires_auth = False

    BASE_URL = "https://servicodados.ibge.gov.br/api/v1"

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação do IBGE."""
        actions = {
            "estados": self._estados,
            "municipios": self._municipios,
            "localidade": self._localidade,
            "regioes": self._regioes,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _estados(self) -> ToolResult:
        """Lista todos os estados brasileiros."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/localidades/estados",
                timeout=10,
            )
            response.raise_for_status()
            estados = response.json()

            return ToolResult.ok({
                "estados": [
                    {
                        "id": e["id"],
                        "sigla": e["sigla"],
                        "nome": e["nome"],
                        "regiao": e["regiao"]["nome"],
                    }
                    for e in estados
                ],
                "count": len(estados),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar estados: {str(e)}")

    def _municipios(self, uf: str) -> ToolResult:
        """
        Lista municípios de um estado.

        Args:
            uf: Sigla do estado (ex: SP, RJ)
        """
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/localidades/estados/{uf}/municipios",
                timeout=10,
            )
            response.raise_for_status()
            municipios = response.json()

            return ToolResult.ok({
                "uf": uf.upper(),
                "municipios": [
                    {
                        "id": m["id"],
                        "nome": m["nome"],
                    }
                    for m in municipios
                ],
                "count": len(municipios),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar municípios: {str(e)}")

    def _localidade(self, nome: str, tipo: str = "municipios") -> ToolResult:
        """
        Busca localidade por nome.

        Args:
            nome: Nome da localidade
            tipo: Tipo (municipios, estados)
        """
        try:
            import requests

            # API não tem busca direta, vamos filtrar
            if tipo == "estados":
                response = requests.get(
                    f"{self.BASE_URL}/localidades/estados",
                    timeout=10,
                )
            else:
                response = requests.get(
                    f"{self.BASE_URL}/localidades/municipios",
                    timeout=15,
                )

            response.raise_for_status()
            dados = response.json()

            # Filtrar por nome (case-insensitive)
            nome_lower = nome.lower()
            resultados = [
                d for d in dados
                if nome_lower in d["nome"].lower()
            ]

            return ToolResult.ok({
                "query": nome,
                "tipo": tipo,
                "resultados": resultados[:20],  # Limitar a 20
                "count": len(resultados),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na busca: {str(e)}")

    def _regioes(self) -> ToolResult:
        """Lista regiões do Brasil."""
        try:
            import requests

            response = requests.get(
                f"{self.BASE_URL}/localidades/regioes",
                timeout=10,
            )
            response.raise_for_status()
            regioes = response.json()

            return ToolResult.ok({
                "regioes": [
                    {
                        "id": r["id"],
                        "sigla": r["sigla"],
                        "nome": r["nome"],
                    }
                    for r in regioes
                ],
                "count": len(regioes),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar regiões: {str(e)}")

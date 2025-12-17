"""
Ferramenta de integração com Supabase.

Requer:
- SUPABASE_URL e SUPABASE_KEY no .env
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="devops")
class SupabaseTool(BaseTool):
    """
    Ferramenta para operações no Supabase.

    Funcionalidades:
    - select: Consultar dados
    - insert: Inserir dados
    - update: Atualizar dados
    - delete: Remover dados
    - rpc: Chamar função RPC
    """

    name = "supabase"
    description = "Integração com Supabase"
    version = "1.0.0"
    requires_auth = True

    def _setup(self) -> None:
        """Configura cliente Supabase."""
        self.url = self.config.get("url") or os.getenv("SUPABASE_URL")
        self.key = self.config.get("key") or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ToolError(
                "SUPABASE_URL e SUPABASE_KEY não configurados",
                tool_name=self.name,
            )

        self._client = None
        self._initialized = True

    def _get_client(self):
        """Obtém cliente Supabase."""
        if self._client is None:
            try:
                from supabase import create_client

                self._client = create_client(self.url, self.key)
            except ImportError:
                raise ToolError(
                    "supabase-py não instalado. Use: pip install supabase",
                    tool_name=self.name,
                )
        return self._client

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação do Supabase."""
        actions = {
            "select": self._select,
            "insert": self._insert,
            "update": self._update,
            "delete": self._delete,
            "rpc": self._rpc,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> ToolResult:
        """
        Consulta dados de uma tabela.

        Args:
            table: Nome da tabela
            columns: Colunas a retornar
            filters: Filtros {coluna: valor}
            limit: Limite de resultados

        Returns:
            ToolResult com dados
        """
        try:
            client = self._get_client()
            query = client.table(table).select(columns)

            if filters:
                for col, val in filters.items():
                    query = query.eq(col, val)

            query = query.limit(limit)
            result = query.execute()

            return ToolResult.ok({
                "data": result.data,
                "count": len(result.data),
                "table": table,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no select: {str(e)}")

    def _insert(self, table: str, data: Dict[str, Any]) -> ToolResult:
        """
        Insere dados em uma tabela.

        Args:
            table: Nome da tabela
            data: Dados a inserir

        Returns:
            ToolResult com registro inserido
        """
        try:
            client = self._get_client()
            result = client.table(table).insert(data).execute()

            return ToolResult.ok({
                "data": result.data,
                "table": table,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no insert: {str(e)}")

    def _update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> ToolResult:
        """
        Atualiza dados em uma tabela.

        Args:
            table: Nome da tabela
            data: Dados a atualizar
            filters: Filtros para identificar registros

        Returns:
            ToolResult com registros atualizados
        """
        try:
            client = self._get_client()
            query = client.table(table).update(data)

            for col, val in filters.items():
                query = query.eq(col, val)

            result = query.execute()

            return ToolResult.ok({
                "data": result.data,
                "count": len(result.data),
                "table": table,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no update: {str(e)}")

    def _delete(self, table: str, filters: Dict[str, Any]) -> ToolResult:
        """
        Remove dados de uma tabela.

        Args:
            table: Nome da tabela
            filters: Filtros para identificar registros

        Returns:
            ToolResult com registros removidos
        """
        try:
            client = self._get_client()
            query = client.table(table).delete()

            for col, val in filters.items():
                query = query.eq(col, val)

            result = query.execute()

            return ToolResult.ok({
                "data": result.data,
                "count": len(result.data),
                "table": table,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no delete: {str(e)}")

    def _rpc(self, function: str, params: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Chama uma função RPC.

        Args:
            function: Nome da função
            params: Parâmetros da função

        Returns:
            ToolResult com resultado
        """
        try:
            client = self._get_client()
            result = client.rpc(function, params or {}).execute()

            return ToolResult.ok({
                "data": result.data,
                "function": function,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no RPC: {str(e)}")

"""
Ferramenta de execução SQL segura.

Suporta:
- SQLite (padrão)
- PostgreSQL (via psycopg2)
- DuckDB (para analytics)
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="database")
class SQLTool(BaseTool):
    """
    Ferramenta para execução segura de queries SQL.

    Funcionalidades:
    - query: Executar SELECT
    - schema: Obter schema de tabela
    - tables: Listar tabelas
    - explain: Explicar query
    """

    name = "sql"
    description = "Execução segura de queries SQL"
    version = "1.0.0"

    # Palavras-chave bloqueadas para segurança
    BLOCKED_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]

    def _setup(self) -> None:
        """Configura conexão."""
        self.db_url = self.config.get("db_url") or os.getenv("DATABASE_URL")
        self.read_only = self.config.get("read_only", True)
        self._engine = None
        self._initialized = True

    def _get_engine(self):
        """Obtém engine SQLAlchemy."""
        if self._engine is None:
            from sqlalchemy import create_engine

            url = self.db_url or "sqlite:///data/databases/agents.db"
            self._engine = create_engine(url)
        return self._engine

    def _validate_query(self, sql: str) -> Optional[str]:
        """Valida query para segurança."""
        if not self.read_only:
            return None

        sql_upper = sql.upper().strip()
        for keyword in self.BLOCKED_KEYWORDS:
            if keyword in sql_upper:
                return f"Operação bloqueada: {keyword}"
        return None

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma ação SQL.

        Args:
            action: Ação (query, schema, tables, explain)
            **kwargs: Parâmetros

        Returns:
            ToolResult
        """
        actions = {
            "query": self._query,
            "schema": self._schema,
            "tables": self._tables,
            "explain": self._explain,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _query(self, sql: str, params: Optional[Dict] = None, limit: int = 100) -> ToolResult:
        """
        Executa uma query SELECT.

        Args:
            sql: Query SQL
            params: Parâmetros para bind
            limit: Limite de resultados

        Returns:
            ToolResult com resultados
        """
        error = self._validate_query(sql)
        if error:
            return ToolResult.fail(error)

        try:
            from sqlalchemy import text

            engine = self._get_engine()

            # Adicionar LIMIT se não presente
            sql_upper = sql.upper().strip()
            if "LIMIT" not in sql_upper and sql_upper.startswith("SELECT"):
                sql = f"{sql.rstrip(';')} LIMIT {limit}"

            with engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                rows = [dict(row._mapping) for row in result.fetchall()]

            return ToolResult.ok({
                "rows": rows,
                "count": len(rows),
                "sql": sql,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na query: {str(e)}")

    def _schema(self, table: str) -> ToolResult:
        """
        Obtém schema de uma tabela.

        Args:
            table: Nome da tabela

        Returns:
            ToolResult com colunas e tipos
        """
        try:
            from sqlalchemy import inspect

            engine = self._get_engine()
            inspector = inspect(engine)

            columns = inspector.get_columns(table)
            pk = inspector.get_pk_constraint(table)
            fks = inspector.get_foreign_keys(table)

            return ToolResult.ok({
                "table": table,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                    }
                    for col in columns
                ],
                "primary_key": pk.get("constrained_columns", []),
                "foreign_keys": [
                    {
                        "columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                    }
                    for fk in fks
                ],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter schema: {str(e)}")

    def _tables(self) -> ToolResult:
        """Lista todas as tabelas."""
        try:
            from sqlalchemy import inspect

            engine = self._get_engine()
            inspector = inspect(engine)

            tables = inspector.get_table_names()

            return ToolResult.ok({
                "tables": tables,
                "count": len(tables),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar tabelas: {str(e)}")

    def _explain(self, sql: str) -> ToolResult:
        """
        Explica plano de execução de uma query.

        Args:
            sql: Query SQL

        Returns:
            ToolResult com plano de execução
        """
        error = self._validate_query(sql)
        if error:
            return ToolResult.fail(error)

        try:
            from sqlalchemy import text

            engine = self._get_engine()

            with engine.connect() as conn:
                result = conn.execute(text(f"EXPLAIN {sql}"))
                plan = [str(row) for row in result.fetchall()]

            return ToolResult.ok({
                "sql": sql,
                "plan": plan,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no EXPLAIN: {str(e)}")

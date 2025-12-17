"""
Ferramenta de analytics com DuckDB.

DuckDB é um banco de dados analítico embutido,
ideal para análise de dados em memória.

Requer: pip install duckdb
"""

from __future__ import annotations

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="database")
class DuckDBTool(BaseTool):
    """
    Ferramenta para análise de dados com DuckDB.

    Funcionalidades:
    - query: Executar SQL analítico
    - load_csv: Carregar dados de CSV
    - load_parquet: Carregar dados de Parquet
    - describe: Descrever tabela
    - export: Exportar resultados
    """

    name = "duckdb"
    description = "Analytics com DuckDB"
    version = "1.0.0"

    def _setup(self) -> None:
        """Configura DuckDB."""
        self._has_duckdb = False
        self._conn = None
        try:
            import duckdb
            self._has_duckdb = True
            # Conexão em memória por padrão
            db_path = self.config.get("db_path", ":memory:")
            self._conn = duckdb.connect(db_path)
        except ImportError:
            pass
        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação DuckDB."""
        if not self._has_duckdb:
            return ToolResult.fail("DuckDB não instalado. Use: pip install duckdb")

        actions = {
            "query": self._query,
            "load_csv": self._load_csv,
            "load_parquet": self._load_parquet,
            "describe": self._describe,
            "export": self._export,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _query(self, sql: str, limit: int = 100) -> ToolResult:
        """
        Executa query SQL.

        Args:
            sql: Query SQL
            limit: Limite de resultados

        Returns:
            ToolResult com dados
        """
        try:
            # Adicionar LIMIT se não presente
            sql_upper = sql.upper().strip()
            if "LIMIT" not in sql_upper and sql_upper.startswith("SELECT"):
                sql = f"{sql.rstrip(';')} LIMIT {limit}"

            result = self._conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()

            data = [dict(zip(columns, row)) for row in rows]

            return ToolResult.ok({
                "data": data,
                "columns": columns,
                "count": len(data),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na query: {str(e)}")

    def _load_csv(self, path: str, table_name: str) -> ToolResult:
        """
        Carrega CSV em tabela.

        Args:
            path: Caminho do arquivo CSV
            table_name: Nome da tabela

        Returns:
            ToolResult
        """
        try:
            self._conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{path}')
            """)

            count = self._conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            return ToolResult.ok({
                "table": table_name,
                "path": path,
                "rows": count,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao carregar CSV: {str(e)}")

    def _load_parquet(self, path: str, table_name: str) -> ToolResult:
        """Carrega Parquet em tabela."""
        try:
            self._conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_parquet('{path}')
            """)

            count = self._conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            return ToolResult.ok({
                "table": table_name,
                "path": path,
                "rows": count,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao carregar Parquet: {str(e)}")

    def _describe(self, table: str) -> ToolResult:
        """Descreve uma tabela."""
        try:
            result = self._conn.execute(f"DESCRIBE {table}")
            columns = result.fetchall()

            return ToolResult.ok({
                "table": table,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES",
                    }
                    for col in columns
                ],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao descrever tabela: {str(e)}")

    def _export(self, sql: str, path: str, format: str = "csv") -> ToolResult:
        """Exporta resultados de query."""
        try:
            if format == "csv":
                self._conn.execute(f"COPY ({sql}) TO '{path}' (HEADER, DELIMITER ',')")
            elif format == "parquet":
                self._conn.execute(f"COPY ({sql}) TO '{path}' (FORMAT PARQUET)")
            elif format == "json":
                self._conn.execute(f"COPY ({sql}) TO '{path}' (FORMAT JSON)")
            else:
                return ToolResult.fail(f"Formato não suportado: {format}")

            return ToolResult.ok({
                "path": path,
                "format": format,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao exportar: {str(e)}")

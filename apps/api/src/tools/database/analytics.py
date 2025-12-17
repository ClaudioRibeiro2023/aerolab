"""
Ferramenta de análise de dados.

Requer:
- pip install pandas numpy
"""

from __future__ import annotations

import importlib.util
from typing import Any, Dict, List, Optional, Union

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="database")
class AnalyticsTool(BaseTool):
    """
    Ferramenta para análise de dados com Pandas.

    Funcionalidades:
    - describe: Estatísticas descritivas
    - correlate: Matriz de correlação
    - pivot: Tabela pivot
    - aggregate: Agregações customizadas
    - filter: Filtrar dados
    """

    name = "analytics"
    description = "Análise de dados com Pandas"
    version = "1.0.0"

    def _setup(self) -> None:
        """Verifica dependências."""
        self._has_pandas = importlib.util.find_spec("pandas") is not None
        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma ação de analytics.

        Args:
            action: Ação (describe, correlate, pivot, aggregate, filter)
            **kwargs: Parâmetros

        Returns:
            ToolResult
        """
        if not self._has_pandas:
            return ToolResult.fail("Pandas não instalado. Use: pip install pandas")

        actions = {
            "describe": self._describe,
            "correlate": self._correlate,
            "pivot": self._pivot,
            "aggregate": self._aggregate,
            "filter": self._filter,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _to_dataframe(self, data: Union[List[Dict], Dict]) -> Any:
        """Converte dados para DataFrame."""
        import pandas as pd

        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        else:
            raise ValueError("Dados devem ser lista de dicts ou dict de listas")

    def _describe(self, data: Union[List[Dict], Dict]) -> ToolResult:
        """
        Gera estatísticas descritivas.

        Args:
            data: Dados para análise

        Returns:
            ToolResult com estatísticas
        """
        try:
            df = self._to_dataframe(data)
            desc = df.describe(include="all").to_dict()

            return ToolResult.ok({
                "statistics": desc,
                "columns": list(df.columns),
                "rows": len(df),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no describe: {str(e)}")

    def _correlate(
        self,
        data: Union[List[Dict], Dict],
        columns: Optional[List[str]] = None,
    ) -> ToolResult:
        """
        Calcula matriz de correlação.

        Args:
            data: Dados para análise
            columns: Colunas a correlacionar (opcional)

        Returns:
            ToolResult com matriz de correlação
        """
        try:
            df = self._to_dataframe(data)

            if columns:
                df = df[columns]

            # Selecionar apenas colunas numéricas
            numeric_df = df.select_dtypes(include=["number"])

            if numeric_df.empty:
                return ToolResult.fail("Nenhuma coluna numérica encontrada")

            corr = numeric_df.corr().to_dict()

            return ToolResult.ok({
                "correlation": corr,
                "columns": list(numeric_df.columns),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na correlação: {str(e)}")

    def _pivot(
        self,
        data: Union[List[Dict], Dict],
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "mean",
    ) -> ToolResult:
        """
        Cria tabela pivot.

        Args:
            data: Dados
            index: Coluna para índice
            columns: Coluna para colunas
            values: Coluna para valores
            aggfunc: Função de agregação (mean, sum, count, etc)

        Returns:
            ToolResult com tabela pivot
        """
        try:
            import pandas as pd

            df = self._to_dataframe(data)

            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc,
            )

            return ToolResult.ok({
                "pivot": pivot.to_dict(),
                "index": index,
                "columns": columns,
                "values": values,
                "aggfunc": aggfunc,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no pivot: {str(e)}")

    def _aggregate(
        self,
        data: Union[List[Dict], Dict],
        group_by: List[str],
        aggregations: Dict[str, str],
    ) -> ToolResult:
        """
        Agrega dados por grupos.

        Args:
            data: Dados
            group_by: Colunas para agrupar
            aggregations: Dict de {coluna: função} (sum, mean, count, etc)

        Returns:
            ToolResult com dados agregados
        """
        try:
            df = self._to_dataframe(data)

            result = df.groupby(group_by).agg(aggregations).reset_index()

            return ToolResult.ok({
                "data": result.to_dict(orient="records"),
                "group_by": group_by,
                "aggregations": aggregations,
                "rows": len(result),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na agregação: {str(e)}")

    def _filter(
        self,
        data: Union[List[Dict], Dict],
        conditions: Dict[str, Any],
    ) -> ToolResult:
        """
        Filtra dados por condições.

        Args:
            data: Dados
            conditions: Dict de {coluna: valor} ou {coluna: {op: valor}}

        Returns:
            ToolResult com dados filtrados
        """
        try:
            df = self._to_dataframe(data)

            for col, cond in conditions.items():
                if isinstance(cond, dict):
                    op = list(cond.keys())[0]
                    val = cond[op]
                    if op == "gt":
                        df = df[df[col] > val]
                    elif op == "gte":
                        df = df[df[col] >= val]
                    elif op == "lt":
                        df = df[df[col] < val]
                    elif op == "lte":
                        df = df[df[col] <= val]
                    elif op == "ne":
                        df = df[df[col] != val]
                    elif op == "in":
                        df = df[df[col].isin(val)]
                    elif op == "contains":
                        df = df[df[col].str.contains(val, na=False)]
                else:
                    df = df[df[col] == cond]

            return ToolResult.ok({
                "data": df.to_dict(orient="records"),
                "rows": len(df),
                "conditions": conditions,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no filtro: {str(e)}")

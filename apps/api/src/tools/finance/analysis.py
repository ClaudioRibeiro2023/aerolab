"""
Ferramenta de análise financeira.
"""

from __future__ import annotations

from typing import Dict, List

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="finance")
class FinancialAnalysisTool(BaseTool):
    """
    Ferramenta para análise financeira.

    Funcionalidades:
    - ratios: Calcular indicadores financeiros
    - dcf: Valuation por DCF
    - risk: Métricas de risco
    """

    name = "financial_analysis"
    description = "Análise financeira e valuation"
    version = "1.0.0"

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação de análise."""
        actions = {
            "ratios": self._ratios,
            "dcf": self._dcf,
            "risk": self._risk,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _ratios(self, financials: Dict[str, float]) -> ToolResult:
        """Calcula indicadores financeiros."""
        try:
            revenue = financials.get("revenue", 0)
            net_income = financials.get("net_income", 0)
            total_assets = financials.get("total_assets", 1)
            total_equity = financials.get("total_equity", 1)
            current_assets = financials.get("current_assets", 0)
            current_liabilities = financials.get("current_liabilities", 1)

            return ToolResult.ok({
                "profit_margin": round(net_income / revenue, 4) if revenue else 0,
                "roa": round(net_income / total_assets, 4),
                "roe": round(net_income / total_equity, 4),
                "current_ratio": round(current_assets / current_liabilities, 2),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no cálculo: {str(e)}")

    def _dcf(self, cash_flows: List[float], discount_rate: float = 0.10) -> ToolResult:
        """Calcula valor presente via DCF."""
        try:
            pv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
            return ToolResult.ok({
                "present_value": round(pv, 2),
                "discount_rate": discount_rate,
                "periods": len(cash_flows),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no DCF: {str(e)}")

    def _risk(self, returns: List[float]) -> ToolResult:
        """Calcula métricas de risco."""
        try:
            import statistics
            
            mean = statistics.mean(returns)
            std = statistics.stdev(returns) if len(returns) > 1 else 0
            sharpe = mean / std if std > 0 else 0

            return ToolResult.ok({
                "mean_return": round(mean, 4),
                "volatility": round(std, 4),
                "sharpe_ratio": round(sharpe, 4),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no cálculo de risco: {str(e)}")

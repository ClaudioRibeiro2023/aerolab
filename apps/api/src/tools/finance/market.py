"""
Ferramenta de dados de mercado.

Requer:
- pip install yfinance
"""

from __future__ import annotations

import importlib.util

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="finance")
class MarketTool(BaseTool):
    """
    Ferramenta para dados de mercado financeiro.

    Funcionalidades:
    - quote: Cotação atual
    - history: Histórico de preços
    - fundamentals: Dados fundamentalistas
    - news: Notícias do ativo
    """

    name = "market"
    description = "Dados de mercado via yfinance"
    version = "1.0.0"

    def _setup(self) -> None:
        """Verifica dependências."""
        self._has_yfinance = importlib.util.find_spec("yfinance") is not None
        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação de mercado."""
        if not self._has_yfinance:
            return ToolResult.fail("yfinance não instalado. Use: pip install yfinance")

        actions = {
            "quote": self._quote,
            "history": self._history,
            "fundamentals": self._fundamentals,
            "news": self._news,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _quote(self, symbol: str) -> ToolResult:
        """
        Obtém cotação atual.

        Args:
            symbol: Símbolo do ativo (ex: PETR4.SA, AAPL)

        Returns:
            ToolResult com cotação
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return ToolResult.ok({
                "symbol": symbol,
                "name": info.get("shortName") or info.get("longName"),
                "price": info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter cotação: {str(e)}")

    def _history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
    ) -> ToolResult:
        """
        Obtém histórico de preços.

        Args:
            symbol: Símbolo do ativo
            period: Período (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalo (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            ToolResult com histórico
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                })

            return ToolResult.ok({
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data,
                "count": len(data),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter histórico: {str(e)}")

    def _fundamentals(self, symbol: str) -> ToolResult:
        """
        Obtém dados fundamentalistas.

        Args:
            symbol: Símbolo do ativo

        Returns:
            ToolResult com fundamentals
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            return ToolResult.ok({
                "symbol": symbol,
                "name": info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "profit_margin": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue": info.get("totalRevenue"),
                "earnings": info.get("netIncomeToCommon"),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter fundamentals: {str(e)}")

    def _news(self, symbol: str) -> ToolResult:
        """
        Obtém notícias do ativo.

        Args:
            symbol: Símbolo do ativo

        Returns:
            ToolResult com notícias
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            news = ticker.news

            return ToolResult.ok({
                "symbol": symbol,
                "news": [
                    {
                        "title": n.get("title"),
                        "publisher": n.get("publisher"),
                        "link": n.get("link"),
                        "published": n.get("providerPublishTime"),
                    }
                    for n in (news or [])[:10]
                ],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro ao obter notícias: {str(e)}")

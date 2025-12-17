"""
Testes de integração com APIs externas.

Testes com APIs públicas rodam sempre.
Testes com APIs privadas só rodam se as keys estiverem configuradas.
"""

import os
import pytest


# ==================== TESTES DE APIS PÚBLICAS ====================

class TestIBGEIntegration:
    """Testes de integração com API do IBGE (pública)."""

    def test_ibge_estados(self):
        """Deve listar estados brasileiros."""
        from src.tools.geo.ibge import IBGETool

        tool = IBGETool()
        result = tool.run(action="estados")

        assert result.success is True
        assert result.data["count"] == 27  # 26 estados + DF
        
        # Verificar se SP está na lista
        siglas = [e["sigla"] for e in result.data["estados"]]
        assert "SP" in siglas
        assert "RJ" in siglas

    def test_ibge_municipios_sp(self):
        """Deve listar municípios de São Paulo."""
        from src.tools.geo.ibge import IBGETool

        tool = IBGETool()
        result = tool.run(action="municipios", uf="SP")

        assert result.success is True
        assert result.data["count"] > 600  # SP tem 645 municípios

    def test_ibge_regioes(self):
        """Deve listar regiões do Brasil."""
        from src.tools.geo.ibge import IBGETool

        tool = IBGETool()
        result = tool.run(action="regioes")

        assert result.success is True
        assert result.data["count"] == 5  # 5 regiões


class TestWikipediaIntegration:
    """Testes de integração com API da Wikipedia (pública)."""

    def test_wikipedia_search(self):
        """Deve buscar artigos."""
        from src.tools.research.wikipedia import WikipediaTool

        tool = WikipediaTool()
        result = tool.run(action="search", query="Brasil")

        assert result.success is True
        assert result.data["count"] > 0
        assert len(result.data["results"]) > 0

    def test_wikipedia_summary(self):
        """Deve obter resumo de artigo."""
        from src.tools.research.wikipedia import WikipediaTool

        tool = WikipediaTool()
        result = tool.run(action="summary", title="São Paulo")

        assert result.success is True
        assert result.data["title"] is not None
        assert len(result.data["extract"]) > 100


# ==================== TESTES DE APIS PRIVADAS (SKIP SE NÃO CONFIGURADAS) ====================

class TestTavilyIntegration:
    """Testes de integração com Tavily API."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Pula se TAVILY_API_KEY não estiver configurada."""
        if not os.getenv("TAVILY_API_KEY"):
            pytest.skip("TAVILY_API_KEY não configurada")

    @pytest.mark.skip(reason="Requires valid TAVILY_API_KEY - external service")
    def test_tavily_search(self):
        """Deve realizar pesquisa web."""
        from src.tools.research.tavily import TavilyTool

        tool = TavilyTool()
        result = tool.run(action="search", query="Python programming", max_results=3)

        assert result.success is True
        assert result.data["count"] > 0


class TestGitHubIntegration:
    """Testes de integração com GitHub API."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Pula se GITHUB_TOKEN não estiver configurado."""
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN não configurado")

    def test_github_list_repos(self):
        """Deve listar repositórios."""
        from src.tools.devops.github import GitHubTool

        tool = GitHubTool()
        result = tool.run(action="repos", limit=5)

        assert result.success is True
        assert "repos" in result.data


class TestPerplexityIntegration:
    """Testes de integração com Perplexity API."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Pula se PERPLEXITY_API_KEY não estiver configurada."""
        if not os.getenv("PERPLEXITY_API_KEY"):
            pytest.skip("PERPLEXITY_API_KEY não configurada")

    def test_perplexity_ask(self):
        """Deve responder pergunta."""
        from src.tools.llm.perplexity import PerplexityTool

        tool = PerplexityTool()
        result = tool.run(action="ask", question="What is Python?")

        assert result.success is True
        assert result.data["answer"] is not None


class TestMapboxIntegration:
    """Testes de integração com Mapbox API."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Pula se MAPBOX_API_KEY não estiver configurada."""
        if not os.getenv("MAPBOX_API_KEY"):
            pytest.skip("MAPBOX_API_KEY não configurada")

    def test_mapbox_geocode(self):
        """Deve geocodificar endereço."""
        from src.tools.geo.mapbox import MapboxTool

        tool = MapboxTool()
        result = tool.run(action="geocode", address="Av. Paulista, São Paulo")

        assert result.success is True
        assert "lat" in result.data
        assert "lon" in result.data


# ==================== TESTES DE FERRAMENTAS LOCAIS ====================

class TestOllamaIntegration:
    """Testes de integração com Ollama (local)."""

    @pytest.fixture(autouse=True)
    def check_ollama_running(self):
        """Pula se Ollama não estiver rodando."""
        import requests
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
        except Exception:
            pytest.skip("Ollama não está rodando")

    def test_ollama_list_models(self):
        """Deve listar modelos."""
        from src.tools.llm.ollama import OllamaTool

        tool = OllamaTool()
        result = tool.run(action="list_models")

        assert result.success is True
        assert "models" in result.data


# ==================== TESTES DE FERRAMENTAS SEM API ====================

class TestSpatialToolIntegration:
    """Testes do SpatialTool (requer shapely)."""

    @pytest.fixture(autouse=True)
    def check_shapely(self):
        """Pula se shapely não estiver instalado."""
        pytest.importorskip("shapely")

    def test_spatial_distance(self):
        """Deve calcular distância entre pontos."""
        from src.tools.geo.spatial import SpatialTool

        tool = SpatialTool()
        # São Paulo -> Rio de Janeiro
        result = tool.run(
            action="distance",
            point1=(-23.5505, -46.6333),
            point2=(-22.9068, -43.1729),
        )

        assert result.success is True
        # Distância deve ser aproximadamente 360km
        assert 350 < result.data["distance_km"] < 400

    def test_spatial_buffer(self):
        """Deve criar buffer ao redor de ponto."""
        pytest.importorskip("pyproj")
        from src.tools.geo.spatial import SpatialTool

        tool = SpatialTool()
        result = tool.run(
            action="buffer",
            point=(-23.5505, -46.6333),  # lat, lon
            distance_km=1.0,
        )

        assert result.success is True
        assert result.data["geometry"]["type"] == "Polygon"


class TestAnalyticsToolIntegration:
    """Testes do AnalyticsTool (não requer API)."""

    def test_analytics_describe(self):
        """Deve gerar estatísticas descritivas."""
        pytest.importorskip("pandas")
        from src.tools.database.analytics import AnalyticsTool

        tool = AnalyticsTool()
        data = [
            {"name": "A", "value": 10, "category": "X"},
            {"name": "B", "value": 20, "category": "X"},
            {"name": "C", "value": 30, "category": "Y"},
            {"name": "D", "value": 40, "category": "Y"},
        ]

        result = tool.run(action="describe", data=data)

        assert result.success is True
        assert result.data["rows"] == 4

    def test_analytics_aggregate(self):
        """Deve agregar dados."""
        pytest.importorskip("pandas")
        from src.tools.database.analytics import AnalyticsTool

        tool = AnalyticsTool()
        data = [
            {"category": "X", "value": 10},
            {"category": "X", "value": 20},
            {"category": "Y", "value": 30},
        ]

        result = tool.run(
            action="aggregate",
            data=data,
            group_by=["category"],
            aggregations={"value": "sum"},
        )

        assert result.success is True
        assert result.data["rows"] == 2

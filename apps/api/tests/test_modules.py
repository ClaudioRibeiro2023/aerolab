"""
Module validation tests for Agno Platform.

Converted from scripts/validate_*.py to pytest format.
Tests core module initialization and functionality.
"""

import pytest


# =============================================================================
# Flow Studio Module Tests
# =============================================================================


class TestFlowStudio:
    """Tests for Flow Studio module."""

    def test_engine_initialization(self):
        """Test Flow Studio engine initialization."""
        from src.flow_studio.engine import get_workflow_engine

        engine = get_workflow_engine()
        assert engine is not None

    def test_executor_registration(self):
        """Test executor registration."""
        from src.flow_studio.engine import get_workflow_engine
        from src.flow_studio.executor import register_default_executors

        engine = get_workflow_engine()
        register_default_executors(engine)

    def test_api_routes(self):
        """Test Flow Studio API routes."""
        from src.flow_studio.api import router

        routes = [r.path for r in router.routes]
        assert len(routes) >= 5, f"Expected 5+ routes, got {len(routes)}"


# =============================================================================
# Team Orchestrator Module Tests
# =============================================================================


class TestTeamOrchestrator:
    """Tests for Team Orchestrator module."""

    def test_engine_initialization(self):
        """Test Team Orchestrator engine initialization."""
        from src.team_orchestrator.engine import get_orchestration_engine

        engine = get_orchestration_engine()
        assert engine is not None

    def test_api_routes(self):
        """Test Team Orchestrator API routes."""
        from src.team_orchestrator.api import router

        routes = [r.path for r in router.routes]
        assert len(routes) >= 5, f"Expected 5+ routes, got {len(routes)}"


# =============================================================================
# Domain Studio Module Tests
# =============================================================================


class TestDomainStudio:
    """Tests for Domain Studio module."""

    def test_registry(self):
        """Test domain registry."""
        from src.domain_studio.core.registry import get_domain_registry

        registry = get_domain_registry()
        domains = registry.list_domains()
        assert len(domains) >= 15, f"Expected 15+ domains, got {len(domains)}"

    def test_agentic_rag_engine(self):
        """Test Agentic RAG Engine initialization."""
        from src.domain_studio.engines.agentic_rag import AgenticRAGEngine
        from src.domain_studio.core.types import DomainType

        engine = AgenticRAGEngine(domain=DomainType.LEGAL)
        assert engine is not None

    def test_graph_rag_engine(self):
        """Test GraphRAG Engine initialization."""
        from src.domain_studio.engines.graph_rag import GraphRAGEngine
        from src.domain_studio.core.types import DomainType

        engine = GraphRAGEngine(domain=DomainType.LEGAL)
        assert engine is not None

    def test_compliance_engine(self):
        """Test Compliance Engine initialization."""
        from src.domain_studio.engines.compliance import ComplianceEngine

        engine = ComplianceEngine()
        stats = engine.get_stats()
        assert stats["total_rules"] >= 10, f"Expected 10+ rules, got {stats['total_rules']}"

    def test_multimodal_engine(self):
        """Test MultiModal Engine initialization."""
        from src.domain_studio.engines.multimodal import MultiModalEngine

        engine = MultiModalEngine()
        assert engine is not None

    def test_api_routes(self):
        """Test Domain Studio API routes."""
        from src.domain_studio.api import router

        routes = [r.path for r in router.routes]
        assert len(routes) >= 5, f"Expected 5+ routes, got {len(routes)}"


# =============================================================================
# Dashboard Module Tests
# =============================================================================


class TestDashboard:
    """Tests for Dashboard module."""

    def test_api_routes(self):
        """Test Dashboard API routes."""
        from src.dashboard.api import router

        routes = [r.path for r in router.routes]
        assert len(routes) >= 3, f"Expected 3+ routes, got {len(routes)}"


# =============================================================================
# RAG System Tests (requires chromadb)
# =============================================================================


class TestRAGSystem:
    """Tests for RAG System."""

    def test_rag_service_import(self):
        """Test RAG service can be imported."""
        from src.rag.service import RagService

        assert RagService is not None

    def test_rag_service_methods(self):
        """Test RAG service has expected methods."""
        from src.rag.service import RagService

        assert hasattr(RagService, "add_texts")
        assert hasattr(RagService, "query")
        assert hasattr(RagService, "get_collection")


# =============================================================================
# Agents Module Tests (requires groq)
# =============================================================================


@pytest.mark.skipif(True, reason="Agents module requires groq SDK which may not be installed")
class TestAgentsModule:
    """Tests for Agents module - requires groq SDK."""

    def test_base_agent_import(self):
        """Test BaseAgent can be imported."""
        from src.agents.base_agent import BaseAgent

        assert BaseAgent is not None


# =============================================================================
# Server Integration Tests
# =============================================================================


class TestServerIntegration:
    """Tests for server integration."""

    def test_fastapi_app_import(self):
        """Test FastAPI app imports correctly."""
        from server import app

        assert app is not None

    def test_expected_routers_loaded(self):
        """Test expected module routers are loaded."""
        from server import app

        router_tags = set()
        for route in app.routes:
            if hasattr(route, "tags") and route.tags:
                router_tags.update(route.tags)

        expected_modules = ["Flow Studio", "Dashboard", "Team Orchestrator", "Domain Studio"]
        for module in expected_modules:
            assert module in router_tags, f"Missing router: {module}"

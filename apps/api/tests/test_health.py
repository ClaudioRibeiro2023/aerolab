"""
Smoke tests for API health endpoints.

These tests verify that the API is running and responding correctly.
"""

import pytest


class TestHealthEndpoints:
    """Test suite for health and status endpoints."""

    def test_health_returns_200(self, client):
        """GET /health should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """GET /health should return status=healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_contains_service_name(self, client):
        """GET /health should contain service name."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data
        assert len(data["service"]) > 0

    def test_health_contains_version(self, client):
        """GET /health should contain version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data

    def test_health_contains_modules(self, client):
        """GET /health should list active modules."""
        response = client.get("/health")
        data = response.json()
        assert "modules" in data
        assert isinstance(data["modules"], dict)


class TestDocsEndpoint:
    """Test suite for API documentation endpoints."""

    def test_docs_returns_200(self, client):
        """GET /docs should return 200 OK (Swagger UI)."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_returns_200(self, client):
        """GET /openapi.json should return 200 OK."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_json_contains_paths(self, client):
        """GET /openapi.json should contain API paths."""
        response = client.get("/openapi.json")
        data = response.json()
        assert "paths" in data
        assert len(data["paths"]) > 0

    def test_openapi_json_contains_info(self, client):
        """GET /openapi.json should contain API info."""
        response = client.get("/openapi.json")
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_returns_redirect_or_200(self, client):
        """GET / should return 200 or redirect."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [200, 307, 308]

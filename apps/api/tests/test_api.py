"""
API tests for Agno Multi-Agent Platform.

Testes básicos que validam endpoints core da API.
Para testes completos dos routers modulares, use pytest com Python 3.14.
"""


def test_health(client):
    """Test health endpoint."""
    r = client.get("/health")
    assert r.status_code == 200
    js = r.json()
    assert js.get("status") == "healthy"


def test_health_detailed(client):
    """Test detailed health endpoint."""
    r = client.get("/health/detailed")
    assert r.status_code == 200


def test_health_liveness(client):
    """Test liveness probe."""
    r = client.get("/health/live")
    assert r.status_code == 200


def test_health_readiness(client):
    """Test readiness probe."""
    r = client.get("/health/ready")
    assert r.status_code == 200


def test_metrics(client):
    """Test Prometheus metrics endpoint."""
    r = client.get("/metrics")
    assert r.status_code == 200


def test_api_status(client):
    """Test API status endpoint."""
    r = client.get("/api/status")
    assert r.status_code == 200
    js = r.json()
    assert js.get("status") == "online"
    assert "endpoints" in js
    assert "features" in js


def test_root_redirects_to_docs(client):
    """Test root endpoint redirects to docs."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307  # Redirect


def test_docs_endpoint(client):
    """Test OpenAPI docs endpoint."""
    r = client.get("/docs")
    assert r.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI schema endpoint."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    js = r.json()
    assert "openapi" in js
    assert "paths" in js


# Flow Studio API tests
def test_flow_studio_health(client):
    """Test Flow Studio health endpoint."""
    r = client.get("/api/flow-studio/health")
    assert r.status_code == 200


def test_flow_studio_stats(client):
    """Test Flow Studio stats endpoint."""
    r = client.get("/api/flow-studio/stats")
    assert r.status_code == 200


# Dashboard API tests
def test_dashboard_health(client):
    """Test Dashboard health endpoint."""
    r = client.get("/api/dashboard/health")
    assert r.status_code == 200


def test_dashboard_stats(client):
    """Test Dashboard stats endpoint."""
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    js = r.json()
    assert "dashboards" in js
    assert "timestamp" in js


# Domain Studio API tests
def test_domain_studio_health(client):
    """Test Domain Studio health endpoint."""
    r = client.get("/domain-studio/health")
    assert r.status_code == 200


def test_domain_studio_domains_list(client):
    """Test Domain Studio domains list."""
    r = client.get("/domain-studio/domains")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# Team Orchestrator API tests
def test_team_orchestrator_health(client):
    """Test Team Orchestrator health endpoint."""
    r = client.get("/api/teams/health")
    assert r.status_code == 200


def test_team_orchestrator_modes(client):
    """Test Team Orchestrator modes endpoint."""
    r = client.get("/api/teams/modes")
    assert r.status_code == 200

# Testes

> Como escrever e executar testes no projeto Agno.

---

## Stack de Testes

| Ferramenta | Uso |
|------------|-----|
| **pytest** | Framework de testes Python |
| **pytest-cov** | Cobertura de código |
| **pytest-asyncio** | Testes assíncronos |

---

## Executar Testes

### Todos os testes

```bash
pytest tests/ -v
```

### Com cobertura

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Testes específicos

```bash
# Por arquivo
pytest tests/test_api.py -v

# Por classe
pytest tests/test_modules.py::TestFlowStudio -v

# Por nome
pytest tests/ -k "test_health" -v
```

---

## Estrutura de Testes

```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_api.py          # Testes de API (endpoints)
├── test_modules.py      # Testes de módulos
└── integration/         # Testes de integração
    └── test_e2e.py
```

---

## Fixtures

### Configuração (`conftest.py`)

```python
import pytest
from fastapi.testclient import TestClient
from server import app

@pytest.fixture(scope="session")
def app():
    """Get the FastAPI app instance."""
    return app

@pytest.fixture(scope="function")
def client(app):
    """Get a TestClient for the app."""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get headers with valid auth token."""
    response = client.post("/auth/login", json={
        "email": "admin@local",
        "password": "admin"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## Padrões de Teste

### Teste de Endpoint

```python
def test_health(client):
    """Test health endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_agents_requires_auth(client):
    """Test agents endpoint requires authentication."""
    response = client.get("/agents")

    assert response.status_code == 401

def test_create_agent(client, auth_headers):
    """Test creating a new agent."""
    response = client.post("/agents",
        headers=auth_headers,
        json={
            "name": "test-agent",
            "model": "groq:llama-3.3-70b-versatile"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "test-agent"
```

### Teste de Módulo

```python
class TestFlowStudio:
    """Tests for Flow Studio module."""

    def test_engine_initialization(self):
        """Test workflow engine can be initialized."""
        from src.flow_studio.engine import get_workflow_engine

        engine = get_workflow_engine()
        assert engine is not None

    def test_executor_registration(self):
        """Test default executors are registered."""
        from src.flow_studio.engine import get_workflow_engine
        from src.flow_studio.executor import register_default_executors

        engine = get_workflow_engine()
        register_default_executors(engine)

        assert len(engine.executors) > 0
```

### Teste Assíncrono

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation."""
    from src.rag.service import RagService

    service = RagService()
    result = await service.query("test", "What is X?")

    assert result is not None
```

---

## Mocking

### Mock de LLM

```python
from unittest.mock import patch, MagicMock

def test_agent_run_with_mock():
    """Test agent run with mocked LLM."""
    mock_response = MagicMock()
    mock_response.content = "Mocked response"

    with patch('src.agents.base_agent.Agent.run') as mock_run:
        mock_run.return_value = mock_response

        # Test code that uses the agent
        ...
```

### Mock de External Service

```python
import respx
import httpx

@respx.mock
def test_external_api():
    """Test with mocked external API."""
    respx.get("https://api.external.com/data").mock(
        return_value=httpx.Response(200, json={"data": "test"})
    )

    # Test code that calls external API
    ...
```

---

## Convenções

### Naming

- Arquivos: `test_<module>.py`
- Funções: `test_<what_is_being_tested>`
- Classes: `Test<Module>`

### Docstrings

Cada teste deve ter docstring explicando o que testa:

```python
def test_login_with_invalid_credentials():
    """Test that login with invalid credentials returns 401."""
    ...
```

### Arrange-Act-Assert

```python
def test_example():
    # Arrange - Setup
    agent = create_test_agent()

    # Act - Execute
    result = agent.run("test input")

    # Assert - Verify
    assert result.status == "success"
```

---

## CI/CD

Testes rodam automaticamente no GitHub Actions:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=src
```

---

## Referências

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

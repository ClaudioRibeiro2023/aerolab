"""
Pytest configuration for API tests.

Este arquivo é executado ANTES de qualquer teste.
Configura variáveis de ambiente e carrega os routers do AgentOS.
"""

import os
import sys

# 1. Adicionar diretório raiz ao PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 2. Configurar variáveis de ambiente ANTES de qualquer import do projeto
os.environ["TESTING"] = "1"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["ADMIN_USERS"] = "admin@local,admin"
os.environ["GROQ_API_KEY"] = "test-key"

# 3. Importar e configurar o app com routers IMEDIATAMENTE
# Isso acontece no nível do módulo, antes de qualquer teste
from server import app as _server_app  # noqa: E402

# 4. Carregar routers do AgentOS se não estiverem carregados
_routes = [r.path for r in _server_app.routes]
if "/teams/content/run" not in _routes:
    print("[conftest] Loading AgentOS routers...")
    try:
        from src.os.routes import (
            create_agents_router,
            create_teams_router,
            create_workflows_router,
            create_rag_router,
            create_hitl_router,
            create_storage_router,
            create_auth_router,
            create_memory_router,
            create_admin_router,
            create_audit_router,
        )

        _server_app.include_router(create_auth_router(_server_app), tags=["Auth"])
        _server_app.include_router(create_agents_router(_server_app), tags=["Agents"])
        _server_app.include_router(create_teams_router(_server_app), tags=["Teams"])
        _server_app.include_router(create_workflows_router(_server_app), tags=["Workflows"])
        _server_app.include_router(create_rag_router(_server_app), tags=["RAG"])
        _server_app.include_router(create_hitl_router(_server_app), tags=["HITL"])
        _server_app.include_router(create_storage_router(_server_app), tags=["Storage"])
        _server_app.include_router(create_memory_router(_server_app), tags=["Memory"])
        _server_app.include_router(create_admin_router(_server_app), tags=["Admin"])
        _server_app.include_router(create_audit_router(_server_app), tags=["Audit"])
        print(f"[conftest] AgentOS routers loaded. Total routes: {len(_server_app.routes)}")
    except Exception as e:
        import traceback

        print(f"[conftest] Failed to load AgentOS routers: {e}")
        traceback.print_exc()
else:
    print(f"[conftest] AgentOS routers already loaded. Total routes: {len(_routes)}")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def app():
    """Get the FastAPI app instance with all routers."""
    return _server_app


@pytest.fixture(scope="function")
def client():
    """Get a TestClient for the app."""
    return TestClient(_server_app)

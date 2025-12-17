"""
Agno Multi-Agent Platform - Main Server

Unified API server integrating all modules:
- Flow Studio (Visual Workflow Builder)
- Team Orchestrator (Multi-Agent Teams)
- Dashboard (Observability & Analytics)
- Agents API
- Chat API
- RAG API

Run with: python server.py
Or: uvicorn server:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse
import logging
import uvicorn
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured JSON logging
from src.observability.logging import setup_logging, get_logger, set_request_id
from src.observability.health import get_health_checker
from src.observability.metrics import get_metrics_text, track_request

# Setup logging (JSON in production, readable in dev)
LOG_FORMAT_JSON = os.getenv("LOG_FORMAT", "json").lower() == "json"
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=LOG_FORMAT_JSON
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Agno Multi-Agent Platform...")

    # Detectar ambiente de teste para não falhar em validação
    is_testing = os.getenv("TESTING", "").lower() in ("1", "true", "yes")

    # Validar variáveis de ambiente críticas
    try:
        from src.config.env_validator import validate_environment
        validate_environment(fail_fast=not is_testing)
        logger.info("[OK] Variaveis de ambiente validadas")
    except Exception as e:
        if is_testing:
            logger.warning(f"[WARN] Validacao de ambiente ignorada em teste: {e}")
        else:
            logger.error(f"[ERROR] Falha na validacao de ambiente: {e}")
            raise

    # Inicializar app.state para routers modulares
    app.state.agents = getattr(app.state, "agents", {})
    app.state.teams = getattr(app.state, "teams", {})
    app.state.workflows_registry = getattr(app.state, "workflows_registry", {})
    app.state.logger = logger
    app.state.started_at = datetime.now()

    # Inicializar HITL repository
    try:
        from src.hitl.repo import HITLRepository
        app.state.hitl_repo = HITLRepository()
        logger.info("[OK] HITL Repository initialized")
    except Exception as e:
        logger.warning(f"[WARN] HITL Repository initialization: {e}")
        app.state.hitl_repo = None

    # Inicializar métricas
    app.state.metrics = {
        "requests": 0,
        "latency_sum": 0.0,
        "by_route": {},
        "by_status": {},
    }

    # Startup
    try:
        # Initialize Flow Studio executors
        from src.flow_studio.engine import get_workflow_engine
        from src.flow_studio.executor import register_default_executors
        engine = get_workflow_engine()
        register_default_executors(engine)
        logger.info("[OK] Flow Studio engine initialized")
    except Exception as e:
        logger.warning(f"[WARN] Flow Studio initialization: {e}")

    try:
        # Initialize Team Orchestrator
        from src.team_orchestrator.engine import get_orchestration_engine
        team_engine = get_orchestration_engine()
        logger.info("[OK] Team Orchestrator engine initialized")
    except Exception as e:
        logger.warning(f"[WARN] Team Orchestrator initialization: {e}")

    logger.info("[OK] Server started successfully")
    logger.info("API Docs: http://localhost:8000/docs")
    logger.info("Flow Studio: http://localhost:3000/flow-studio")

    yield

    # Shutdown
    logger.info("Shutting down server...")


# Create FastAPI app
app = FastAPI(
    title="AeroLab Platform",
    description="""
    🤖 **AeroLab - AI Platform API**

    Complete AI agent orchestration and workflow automation platform.

    ## Modules

    - **Flow Studio** - Visual workflow builder with 60+ node types
    - **Agents** - AI agent management and execution
    - **Teams** - Multi-agent team orchestration
    - **Chat** - Conversational AI with memory
    - **RAG** - Retrieval-augmented generation
    - **Dashboard** - Real-time observability
    - **Domain Studio** - Vertical AI with 15 specialized domains

    ## Quick Links

    - [Flow Studio API](/api/flow-studio/health)
    - [Dashboard API](/api/dashboard/health)
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware - allow local development and Docker
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:4001",  # Docker frontend
    "http://localhost:9000",  # Studio production
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:4001",  # Docker frontend
    "http://127.0.0.1:9000",  # Studio production
    "https://aerolab.netlify.app",
]
# Add custom origins from environment
custom_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
if custom_origins:
    cors_origins.extend([o.strip() for o in custom_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar app.state imediatamente (necessário para routers e testes)
# Valores serão atualizados no lifespan se necessário
app.state.agents = {}
app.state.teams = {}
app.state.workflows_registry = {}
app.state.logger = logger
app.state.started_at = datetime.now()
app.state.hitl_repo = None
app.state.metrics = {
    "requests": 0,
    "latency_sum": 0.0,
    "by_route": {},
    "by_status": {},
}


# ============================================================
# Include Routers
# ============================================================

# Flow Studio API
try:
    from src.flow_studio.api import router as flow_studio_router
    from src.flow_studio.api import websocket_router as flow_studio_ws
    app.include_router(flow_studio_router, tags=["Flow Studio"])
    app.include_router(flow_studio_ws, tags=["Flow Studio WebSocket"])
    logger.info("[OK] Flow Studio API loaded")
except Exception as e:
    logger.warning(f"[WARN] Flow Studio API not loaded: {e}")

# Dashboard API
try:
    from src.dashboard.api import router as dashboard_router
    from src.dashboard.api import websocket_router as dashboard_ws
    app.include_router(dashboard_router, tags=["Dashboard"])
    app.include_router(dashboard_ws, tags=["Dashboard WebSocket"])
    logger.info("[OK] Dashboard API loaded")
except Exception as e:
    logger.warning(f"[WARN] Dashboard API not loaded: {e}")

# Team Orchestrator API
try:
    from src.team_orchestrator.api import router as teams_router
    from src.team_orchestrator.api import websocket_router as teams_ws
    app.include_router(teams_router, tags=["Team Orchestrator"])
    app.include_router(teams_ws, tags=["Team Orchestrator WebSocket"])
    logger.info("[OK] Team Orchestrator API loaded")
except Exception as e:
    logger.warning(f"[WARN] Team Orchestrator API not loaded: {e}")

# Domain Studio API
try:
    from src.domain_studio.api import router as domain_studio_router
    app.include_router(domain_studio_router, tags=["Domain Studio"])
    logger.info("[OK] Domain Studio API loaded")
except Exception as e:
    logger.warning(f"[WARN] Domain Studio API not loaded: {e}")


# ============================================================
# AgentOS Modular Routers
# ============================================================

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
        create_metrics_router,
        create_admin_router,
        create_audit_router,
    )

    # Auth router
    app.include_router(create_auth_router(app), tags=["Auth"])
    logger.info("[OK] Auth router loaded")

    # Agents router
    app.include_router(create_agents_router(app), tags=["Agents"])
    logger.info("[OK] Agents router loaded")

    # Teams router
    app.include_router(create_teams_router(app), tags=["Teams"])
    logger.info("[OK] Teams router loaded")

    # Workflows router
    app.include_router(create_workflows_router(app), tags=["Workflows"])
    logger.info("[OK] Workflows router loaded")

    # RAG router
    app.include_router(create_rag_router(app), tags=["RAG"])
    logger.info("[OK] RAG router loaded")

    # HITL router (primary at /hitl)
    hitl_router = create_hitl_router(app)
    app.include_router(hitl_router, tags=["HITL"])
    logger.info("[OK] HITL router loaded")

    # HITL alias at /workflows/hitl for backward compatibility
    from fastapi import APIRouter
    hitl_alias = APIRouter(prefix="/workflows/hitl", tags=["HITL"])

    @hitl_alias.post("/start")
    async def hitl_start_alias(task: str = ""):
        """Alias for /hitl/start."""
        from src.os.routes.hitl import HITLStartRequest
        if hasattr(app.state, "hitl_repo") and app.state.hitl_repo:
            session = app.state.hitl_repo.create_session(task=task)
            return {"id": session.id, "task": task, "status": session.status}
        return {"id": 1, "task": task, "status": "pending"}

    @hitl_alias.post("/complete")
    async def hitl_complete_alias(session_id: int, result: str = ""):
        """Alias for /hitl/complete."""
        if hasattr(app.state, "hitl_repo") and app.state.hitl_repo:
            session = app.state.hitl_repo.approve(session_id, result=result)
            if session:
                return {"id": session.id, "status": session.status, "result": result}
        return {"id": session_id, "status": "completed", "result": result}

    app.include_router(hitl_alias)
    logger.info("[OK] HITL alias at /workflows/hitl loaded")

    # Storage router
    app.include_router(create_storage_router(app), tags=["Storage"])
    logger.info("[OK] Storage router loaded")

    # Memory router
    app.include_router(create_memory_router(app), tags=["Memory"])
    logger.info("[OK] Memory router loaded")

    # Admin router
    app.include_router(create_admin_router(app), tags=["Admin"])
    logger.info("[OK] Admin router loaded")

    # Audit router
    app.include_router(create_audit_router(app), tags=["Audit"])
    logger.info("[OK] Audit router loaded")

except Exception as e:
    import traceback
    import sys
    # Use print para garantir que o erro seja visível mesmo se o logger falhar
    print(f"[SERVER ERROR] AgentOS routers not loaded: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    try:
        logger.error(f"[ERROR] AgentOS routers not loaded: {e}")
    except:
        pass


# ============================================================
# Auth Endpoints (fallback if AgentOS routers fail)
# ============================================================

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str

@app.post("/auth/login", tags=["Auth"])
async def auth_login(req: LoginRequest):
    """Login endpoint - returns JWT token."""
    from src.config import get_settings
    from src.auth.jwt import create_access_token
    
    settings = get_settings()
    
    # Se JWT não configurado, retornar token mock para desenvolvimento
    if not settings.JWT_SECRET:
        return {
            "access_token": "dev-token-no-auth",
            "token_type": "bearer",
            "role": "admin",
            "message": "Auth disabled - development mode"
        }
    
    admins = {u.strip() for u in (settings.ADMIN_USERS or "admin").split(",") if u.strip()}
    role = "admin" if req.username in admins else "user"
    
    token = create_access_token(
        subject=req.username,
        role=role,
        secret=settings.JWT_SECRET,
        expires_minutes=settings.JWT_EXPIRES_MIN or 60,
    )
    
    return {"access_token": token, "token_type": "bearer", "role": role}

@app.get("/auth/me", tags=["Auth"])
async def auth_me(request: Request):
    """Get current user info."""
    from src.auth.deps import get_current_user
    try:
        user = get_current_user(request)
        return user
    except Exception:
        return {"sub": "anonymous", "role": "guest"}

# ============================================================
# Root Endpoints
# ============================================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint (simple)."""
    return {
        "status": "healthy",
        "service": "aerolab-platform",
        "version": "3.0.0",
        "modules": {
            "flow_studio": "active",
            "team_orchestrator": "active",
            "dashboard": "active",
            "domain_studio": "active",
            "agents": "active",
        }
    }


@app.get("/health/detailed")
async def health_detailed():
    """
    Detailed health check endpoint.

    Returns status of all system components:
    - Database connection
    - Redis (if configured)
    - Filesystem
    - Memory usage
    - Uptime
    """
    checker = get_health_checker()
    checker.version = "3.0.0"
    health_status = await checker.check_all()
    return health_status.to_dict()


@app.get("/health/live")
async def health_liveness():
    """Kubernetes liveness probe."""
    checker = get_health_checker()
    return await checker.check_liveness()


@app.get("/health/ready")
async def health_readiness():
    """Kubernetes readiness probe."""
    checker = get_health_checker()
    return await checker.check_readiness()


# ============================================================
# Fallback CRUD Endpoints (when AgentOS routers fail to load)
# ============================================================

# In-memory agents store (fallback when DB not available)
_agents_store = {
    "Assistant": {"id": "1", "name": "Assistant", "model": "gpt-4", "status": "active", "role": "Agente genérico", "model_provider": "openai", "model_id": "gpt-4"},
    "Coder": {"id": "2", "name": "Coder", "model": "gpt-4", "status": "active", "role": "Agente genérico", "model_provider": "openai", "model_id": "gpt-4"},
    "Researcher": {"id": "3", "name": "Researcher", "model": "claude-3", "status": "active", "role": "Agente genérico", "model_provider": "anthropic", "model_id": "claude-3"},
}


class CreateAgentRequest(BaseModel):
    name: str
    role: str = None
    model_provider: str = "openai"
    model_id: str = "gpt-4"
    instructions: list = None
    use_database: bool = False
    add_history_to_context: bool = True
    markdown: bool = True
    debug_mode: bool = False


@app.get("/agents", tags=["Agents"])
async def list_agents():
    """List all agents (fallback)."""
    return list(_agents_store.values())


@app.post("/agents", tags=["Agents"])
async def create_agent(request: CreateAgentRequest):
    """Create a new agent."""
    if request.name in _agents_store:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Agent already exists")
    
    new_id = str(len(_agents_store) + 1)
    agent = {
        "id": new_id,
        "name": request.name,
        "role": request.role or "Agente personalizado",
        "model": request.model_id,
        "model_provider": request.model_provider,
        "model_id": request.model_id,
        "status": "active",
        "instructions": request.instructions or [],
        "use_database": request.use_database,
        "add_history_to_context": request.add_history_to_context,
        "markdown": request.markdown,
        "debug_mode": request.debug_mode,
    }
    _agents_store[request.name] = agent
    return agent


@app.delete("/agents/{agent_name}", tags=["Agents"])
async def delete_agent(agent_name: str):
    """Delete an agent."""
    if agent_name in _agents_store:
        del _agents_store[agent_name]
        return {"deleted": agent_name}
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Agent not found")


@app.get("/teams", tags=["Teams"])
async def list_teams():
    """List all teams (fallback)."""
    return [
        {"id": "1", "name": "Research Team", "members": 3, "status": "active"},
        {"id": "2", "name": "Development Team", "members": 2, "status": "active"},
    ]


@app.get("/workflows", tags=["Workflows"])
async def list_workflows():
    """List all workflows (fallback)."""
    return [
        {"id": "1", "name": "Data Pipeline", "nodes": 5, "status": "active"},
        {"id": "2", "name": "Content Generation", "nodes": 3, "status": "active"},
    ]


@app.get("/workflows/registry", tags=["Workflows"])
async def workflows_registry():
    """Get workflow node registry (fallback)."""
    return {"nodes": [], "categories": []}


@app.get("/rag/collections", tags=["RAG"])
async def list_rag_collections():
    """List RAG collections (fallback)."""
    return {
        "collections": ["Documentation", "Knowledge Base", "FAQ"],
        "items": [
            {"id": "1", "name": "Documentation", "documents": 10, "status": "active"},
            {"id": "2", "name": "Knowledge Base", "documents": 25, "status": "active"},
        ]
    }


@app.post("/rag/ingest-texts", tags=["RAG"])
async def rag_ingest_texts(collection: str = "", texts: list = []):
    """Ingest texts into RAG collection."""
    return {"added": len(texts) if texts else 0, "collection": collection}


@app.post("/rag/ingest-urls", tags=["RAG"])
async def rag_ingest_urls(collection: str = "", urls: list = []):
    """Ingest URLs into RAG collection."""
    return {"added": len(urls) if urls else 0, "collection": collection}


@app.post("/rag/ingest-files", tags=["RAG"])
async def rag_ingest_files(collection: str = ""):
    """Ingest files into RAG collection."""
    return {"added": 0, "collection": collection}


@app.post("/rag/query", tags=["RAG"])
async def rag_query(collection: str = "", query_text: str = "", top_k: int = 5):
    """Query RAG collection."""
    return {"results": [{"text": "Demo result for: " + query_text, "metadata": {}}]}


@app.get("/rag/collections/{collection}/docs", tags=["RAG"])
async def rag_list_docs(collection: str):
    """List documents in RAG collection."""
    return {"docs": [{"id": "doc1", "name": "Sample Document", "collection": collection}]}


@app.delete("/rag/collections/{collection}", tags=["RAG"])
async def rag_delete_collection(collection: str):
    """Delete RAG collection."""
    return {"deleted": collection}


@app.delete("/rag/collections/{collection}/docs/{doc_id}", tags=["RAG"])
async def rag_delete_doc(collection: str, doc_id: str):
    """Delete document from RAG collection."""
    return {"deleted": doc_id}


# HITL Endpoints
@app.post("/hitl/start", tags=["HITL"])
async def hitl_start_endpoint(topic: str = "", style: str = None):
    """Start HITL session."""
    return {"session_id": "hitl-001", "topic": topic, "research": "Demo research content"}


@app.post("/hitl/complete", tags=["HITL"])
async def hitl_complete_endpoint(session_id: str = "", approve: bool = True, feedback: str = None):
    """Complete HITL session."""
    return {"status": "completed", "session_id": session_id, "content": "Demo completed content"}


@app.get("/hitl/{session_id}", tags=["HITL"])
async def hitl_get_session(session_id: str):
    """Get HITL session."""
    return {"session": {"id": session_id, "status": "pending"}, "actions": []}


@app.get("/hitl", tags=["HITL"])
async def hitl_list_sessions(status: str = None, limit: int = 50, offset: int = 0):
    """List HITL sessions."""
    return {"items": [], "count": 0}


@app.post("/hitl/cancel", tags=["HITL"])
async def hitl_cancel_endpoint(session_id: str = "", reason: str = None):
    """Cancel HITL session."""
    return {"status": "cancelled", "session_id": session_id}


# ============================================================
# Chat & Agent Execution Endpoints
# ============================================================

class ChatMessage(BaseModel):
    message: str
    model: str = "gpt-4"
    agent_id: str = "Assistant"


class AgentRunRequest(BaseModel):
    message: str = None
    prompt: str = None
    model: str = "gpt-4"
    stream: bool = False


@app.post("/agents/{agent_name}/run", tags=["Agents"])
async def run_agent(agent_name: str, request: AgentRunRequest):
    """Execute an agent with a message."""
    # Accept both 'message' and 'prompt' fields
    user_input = request.prompt or request.message or ""
    truncated = user_input[:50] if len(user_input) > 50 else user_input
    
    return {
        "id": f"run-{agent_name}-001",
        "agent": agent_name,
        "message": user_input,
        "result": f"[{agent_name}] Esta é uma resposta de demonstração. O agente '{agent_name}' processou sua mensagem: '{truncated}'. Configure uma API key de LLM (OpenAI, Anthropic, Groq) para respostas reais.",
        "response": f"[{agent_name}] Resposta de demonstração para: '{truncated}'. Configure uma API key de LLM para respostas reais.",
        "model": request.model,
        "status": "completed",
        "tokens": {"input": len(user_input.split()), "output": 50}
    }


@app.get("/agents/{agent_name}", tags=["Agents"])
async def get_agent(agent_name: str):
    """Get agent details by name."""
    if agent_name in _agents_store:
        return _agents_store[agent_name]
    # Return dynamic agent if not found
    return {"id": "0", "name": agent_name, "model": "gpt-4", "status": "active", "role": "Dynamic agent"}


@app.post("/chat", tags=["Chat"])
async def chat_endpoint(request: ChatMessage):
    """Simple chat endpoint."""
    return {
        "id": "chat-001",
        "message": request.message,
        "response": f"Resposta de demonstração para: '{request.message[:100]}'. Configure uma API key de LLM para respostas reais.",
        "agent": request.agent_id,
        "model": request.model,
        "status": "completed"
    }


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatMessage):
    """Streaming chat endpoint (returns full response for now)."""
    return {
        "id": "chat-stream-001",
        "message": request.message,
        "response": f"[Streaming] Resposta de demonstração. Configure LLM para streaming real.",
        "agent": request.agent_id,
        "done": True
    }


@app.get("/chat/history", tags=["Chat"])
async def chat_history():
    """Get chat history."""
    return []


@app.get("/logs", tags=["Logs"])
async def get_logs():
    """Get system logs."""
    return {
        "logs": [
            {"timestamp": "2025-01-01T00:00:00Z", "level": "INFO", "message": "System started"},
            {"timestamp": "2025-01-01T00:00:01Z", "level": "INFO", "message": "API ready"},
        ],
        "total": 2
    }


@app.get("/domains", tags=["Domains"])
async def list_domains():
    """List available domains."""
    return [
        {"id": "legal", "name": "Legal", "description": "Legal domain expertise"},
        {"id": "finance", "name": "Finance", "description": "Financial analysis"},
        {"id": "devops", "name": "DevOps", "description": "DevOps automation"},
        {"id": "data-science", "name": "Data Science", "description": "Data analysis and ML"},
    ]


@app.get("/models", tags=["Models"])
async def list_models():
    """List available LLM models."""
    return [
        {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI", "available": True},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI", "available": True},
        {"id": "claude-3", "name": "Claude 3", "provider": "Anthropic", "available": True},
        {"id": "llama-3.3-70b", "name": "Llama 3.3 70B", "provider": "Groq", "available": True},
    ]


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes:
    - Request counts and latency
    - Agent execution metrics
    - Token usage
    - Cache hits/misses
    - Error counts
    """
    return get_metrics_text()


@app.get("/api/status")
async def api_status():
    """API status and available endpoints."""
    return {
        "status": "online",
        "version": "3.0.0",
        "endpoints": {
            "flow_studio": "/api/flow-studio",
            "team_orchestrator": "/api/teams",
            "dashboard": "/api/dashboard",
            "domain_studio": "/domain-studio",
            "docs": "/docs",
            "health": "/health",
        },
        "features": [
            "Visual Workflow Builder",
            "60+ Node Types",
            "Natural Language to Workflow",
            "AI Optimization",
            "Cost/Time Prediction",
            "Real-time Execution",
            "Debug Mode",
            "Team Orchestrator v2.0",
            "15+ Orchestration Modes",
            "20+ Agent Personas",
            "NL Team Builder",
            "Agent Learning System",
            "Conflict Resolution",
            "Domain Studio v3.5",
            "15 Specialized Domains",
            "Agentic RAG",
            "GraphRAG + Neo4j",
            "30+ Compliance Rules",
            "MultiModal Processing",
        ]
    }


# ============================================================
# Middleware for Metrics
# ============================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics."""
    # Set request ID for structured logging
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    set_request_id(request_id)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Track metrics (skip health/metrics endpoints)
    if not request.url.path.startswith(("/health", "/metrics")):
        track_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

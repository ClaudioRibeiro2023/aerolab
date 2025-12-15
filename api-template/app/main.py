"""
Template API - FastAPI
"""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os

from .logging_config import get_logger
from .middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from .rate_limit import setup_rate_limiting, limiter, rate_limit_health, rate_limit_api

# ============================================================================
# Logging
# ============================================================================
logger = get_logger(__name__)

# ============================================================================
# App Configuration
# ============================================================================
API_VERSION = "0.1.0"

app = FastAPI(
    title="Template API",
    description="API Template with authentication and basic endpoints",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# Middleware (order matters - last added = first executed)
# ============================================================================

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Request logging with request_id
app.add_middleware(RequestLoggingMiddleware)

# CORS (should be one of the last to ensure headers are added)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:13000",
        os.getenv("FRONTEND_URL", "http://localhost:13000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Rate limiting
setup_rate_limiting(app)

# ============================================================================
# Models
# ============================================================================
class HealthResponse(BaseModel):
    status: str
    version: str

class LivenessResponse(BaseModel):
    """Liveness probe response - just checks if API is running"""
    status: str
    timestamp: str

class ReadinessResponse(BaseModel):
    """Readiness probe response - checks all dependencies"""
    status: str
    version: str
    timestamp: str
    checks: dict[str, dict]

class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    roles: list[str]

# ============================================================================
# Health Check Utilities
# ============================================================================
async def check_database() -> dict:
    """Check database connectivity"""
    # TODO: Implement actual database check
    # Example: await db.execute("SELECT 1")
    return {"status": "ok", "latency_ms": 1}

async def check_redis() -> dict:
    """Check Redis connectivity"""
    # TODO: Implement actual Redis check
    # Example: await redis.ping()
    return {"status": "ok", "latency_ms": 1}

async def check_keycloak() -> dict:
    """Check Keycloak connectivity"""
    # TODO: Implement actual Keycloak check
    return {"status": "ok"}

# ============================================================================
# Health Check Routes
# ============================================================================
@app.get("/", response_model=HealthResponse)
async def root():
    """Root health check endpoint"""
    return HealthResponse(status="ok", version=API_VERSION)

@app.get("/health", response_model=HealthResponse)
async def health():
    """Basic health check"""
    return HealthResponse(status="healthy", version=API_VERSION)

@app.get("/health/live", response_model=LivenessResponse)
async def liveness():
    """
    Liveness probe - Kubernetes uses this to know when to restart a container.
    Should only check if the application is running, not dependencies.
    """
    return LivenessResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/health/ready", response_model=ReadinessResponse)
async def readiness():
    """
    Readiness probe - Kubernetes uses this to know when the container is ready
    to start accepting traffic. Checks all dependencies.
    """
    checks = {}
    overall_status = "ready"
    
    # Check database
    try:
        checks["database"] = await check_database()
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}
        overall_status = "not_ready"
    
    # Check Redis
    try:
        checks["redis"] = await check_redis()
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)}
        overall_status = "not_ready"
    
    # Check Keycloak
    try:
        checks["keycloak"] = await check_keycloak()
    except Exception as e:
        checks["keycloak"] = {"status": "error", "message": str(e)}
        # Keycloak is optional, don't mark as not_ready
        
    response = ReadinessResponse(
        status=overall_status,
        version=API_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )
    
    if overall_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump()
        )
    
    return response

@app.get("/api/me", response_model=UserInfo)
async def get_current_user():
    """Get current user info (placeholder)"""
    # In production, extract from JWT token
    return UserInfo(
        id="demo-user",
        email="demo@template.com",
        name="Demo User",
        roles=["ADMIN", "GESTOR", "OPERADOR", "VIEWER"]
    )

@app.get("/api/config")
async def get_config():
    """Get frontend configuration"""
    return {
        "appName": "Template Platform",
        "version": "0.1.0",
        "features": {
            "darkMode": True,
            "notifications": True,
        }
    }

# ============================================================================
# Startup / Shutdown Events
# ============================================================================
@app.on_event("startup")
async def startup():
    logger.info(
        "api_started",
        version=API_VERSION,
        environment=os.getenv("ENVIRONMENT", "development"),
    )

@app.on_event("shutdown")
async def shutdown():
    logger.info("api_shutdown")

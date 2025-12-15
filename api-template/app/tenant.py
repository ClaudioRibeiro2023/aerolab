"""
Multi-Tenancy Support

Provides tenant identification and context management for multi-tenant applications.
"""
from fastapi import FastAPI, Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar
from typing import Optional
from pydantic import BaseModel
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

TENANT_HEADER = os.getenv("TENANT_HEADER", "X-Tenant-ID")
TENANT_SUBDOMAIN_MODE = os.getenv("TENANT_SUBDOMAIN_MODE", "false").lower() == "true"
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "default")

# ============================================================================
# Tenant Context
# ============================================================================

# Context variable for current tenant (thread-safe)
_current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)


def get_current_tenant() -> Optional[str]:
    """Get the current tenant ID from context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: Optional[str]) -> None:
    """Set the current tenant ID in context."""
    _current_tenant.set(tenant_id)


# ============================================================================
# Tenant Model
# ============================================================================

class Tenant(BaseModel):
    """Tenant model for API responses."""
    id: str
    name: str
    slug: str
    is_active: bool = True
    settings: dict = {}


class TenantConfig(BaseModel):
    """Tenant-specific configuration."""
    tenant_id: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    app_name: Optional[str] = None
    features: dict = {}


# ============================================================================
# Tenant Store (Mock implementation - replace with database)
# ============================================================================

class TenantStore:
    """
    Tenant store interface.
    Replace this with actual database implementation.
    """
    
    def __init__(self):
        # Mock tenants for development
        self._tenants = {
            "default": Tenant(
                id="default",
                name="Default Organization",
                slug="default",
                is_active=True,
                settings={"max_users": 100},
            ),
            "acme": Tenant(
                id="acme",
                name="ACME Corporation",
                slug="acme",
                is_active=True,
                settings={"max_users": 500, "custom_domain": "acme.example.com"},
            ),
            "demo": Tenant(
                id="demo",
                name="Demo Company",
                slug="demo",
                is_active=True,
                settings={"max_users": 10, "is_trial": True},
            ),
        }
        
        self._configs = {
            "default": TenantConfig(
                tenant_id="default",
                app_name="Template Platform",
                primary_color="#0087A8",
            ),
            "acme": TenantConfig(
                tenant_id="acme",
                app_name="ACME Portal",
                logo_url="/tenants/acme/logo.png",
                primary_color="#FF5722",
            ),
            "demo": TenantConfig(
                tenant_id="demo",
                app_name="Demo Platform",
                primary_color="#4CAF50",
            ),
        }
    
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug (for subdomain matching)."""
        for tenant in self._tenants.values():
            if tenant.slug == slug:
                return tenant
        return None
    
    async def get_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration."""
        return self._configs.get(tenant_id)
    
    async def list_all(self) -> list[Tenant]:
        """List all active tenants."""
        return [t for t in self._tenants.values() if t.is_active]


# Global tenant store instance
tenant_store = TenantStore()


# ============================================================================
# Tenant Middleware
# ============================================================================

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to identify tenant from request.
    
    Supports multiple identification methods:
    1. X-Tenant-ID header
    2. Subdomain (e.g., acme.example.com)
    3. Default tenant fallback
    """
    
    async def dispatch(self, request: Request, call_next):
        tenant_id = None
        
        # Method 1: Check header
        tenant_id = request.headers.get(TENANT_HEADER)
        
        # Method 2: Check subdomain (if enabled)
        if not tenant_id and TENANT_SUBDOMAIN_MODE:
            host = request.headers.get("host", "")
            parts = host.split(".")
            if len(parts) >= 3:
                subdomain = parts[0]
                tenant = await tenant_store.get_by_slug(subdomain)
                if tenant:
                    tenant_id = tenant.id
        
        # Method 3: Default tenant
        if not tenant_id:
            tenant_id = DEFAULT_TENANT_ID
        
        # Validate tenant exists and is active
        tenant = await tenant_store.get_by_id(tenant_id)
        if not tenant:
            logger.warning("tenant_not_found", tenant_id=tenant_id)
            tenant_id = DEFAULT_TENANT_ID
        elif not tenant.is_active:
            logger.warning("tenant_inactive", tenant_id=tenant_id)
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "tenant_inactive", "message": "This organization is currently inactive."},
            )
        
        # Set tenant in context
        set_current_tenant(tenant_id)
        
        # Add tenant to request state for easy access
        request.state.tenant_id = tenant_id
        
        # Log with tenant context
        logger.debug("tenant_identified", tenant_id=tenant_id, method=request.method, path=request.url.path)
        
        response = await call_next(request)
        
        # Add tenant header to response
        response.headers["X-Tenant-ID"] = tenant_id
        
        return response


# ============================================================================
# Dependencies
# ============================================================================

async def get_tenant(request: Request) -> Tenant:
    """
    FastAPI dependency to get current tenant.
    
    Usage:
        @app.get("/api/resource")
        async def get_resource(tenant: Tenant = Depends(get_tenant)):
            return {"tenant": tenant.name}
    """
    tenant_id = getattr(request.state, "tenant_id", None) or get_current_tenant()
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not identified",
        )
    
    tenant = await tenant_store.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_id}",
        )
    
    return tenant


async def get_tenant_config(request: Request) -> TenantConfig:
    """
    FastAPI dependency to get current tenant configuration.
    """
    tenant_id = getattr(request.state, "tenant_id", None) or get_current_tenant()
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not identified",
        )
    
    config = await tenant_store.get_config(tenant_id)
    if not config:
        # Return default config
        return TenantConfig(tenant_id=tenant_id)
    
    return config


# ============================================================================
# Setup Function
# ============================================================================

def setup_multi_tenancy(app: FastAPI) -> None:
    """
    Configure multi-tenancy for the FastAPI application.
    
    Usage:
        from app.tenant import setup_multi_tenancy, get_tenant
        
        setup_multi_tenancy(app)
        
        @app.get("/api/resource")
        async def get_resource(tenant: Tenant = Depends(get_tenant)):
            return {"tenant": tenant.name}
    """
    from fastapi.responses import JSONResponse
    
    app.add_middleware(TenantMiddleware)
    
    logger.info(
        "multi_tenancy_configured",
        header=TENANT_HEADER,
        subdomain_mode=TENANT_SUBDOMAIN_MODE,
        default_tenant=DEFAULT_TENANT_ID,
    )


# ============================================================================
# API Endpoints
# ============================================================================

def add_tenant_endpoints(app: FastAPI) -> None:
    """Add tenant-related API endpoints."""
    
    @app.get("/api/tenant", response_model=Tenant)
    async def get_current_tenant_info(tenant: Tenant = Depends(get_tenant)):
        """Get current tenant information."""
        return tenant
    
    @app.get("/api/tenant/config", response_model=TenantConfig)
    async def get_current_tenant_config(config: TenantConfig = Depends(get_tenant_config)):
        """Get current tenant configuration (branding, features, etc.)."""
        return config


# Import for JSONResponse
from fastapi.responses import JSONResponse

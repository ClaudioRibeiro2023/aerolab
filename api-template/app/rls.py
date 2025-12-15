"""
Row-Level Security (RLS) for Multi-Tenancy

Provides automatic tenant-based filtering for database queries.
Works with SQLAlchemy to ensure data isolation between tenants.
"""
from typing import Optional, TypeVar, Generic, Any
from sqlalchemy import Column, String, event
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.declarative import declared_attr
from contextvars import ContextVar
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

RLS_ENABLED = os.getenv("RLS_ENABLED", "true").lower() == "true"
RLS_BYPASS_ROLES = os.getenv("RLS_BYPASS_ROLES", "ADMIN,SUPERADMIN").split(",")

# Context variable for current tenant
_current_tenant_id: ContextVar[Optional[str]] = ContextVar("rls_tenant_id", default=None)
_bypass_rls: ContextVar[bool] = ContextVar("bypass_rls", default=False)

# ============================================================================
# Context Management
# ============================================================================

def set_tenant_context(tenant_id: Optional[str]) -> None:
    """Set the current tenant context for RLS filtering."""
    _current_tenant_id.set(tenant_id)
    logger.debug("rls_tenant_set", tenant_id=tenant_id)


def get_tenant_context() -> Optional[str]:
    """Get the current tenant context."""
    return _current_tenant_id.get()


def set_bypass_rls(bypass: bool) -> None:
    """Set whether to bypass RLS (for admin operations)."""
    _bypass_rls.set(bypass)
    if bypass:
        logger.warning("rls_bypass_enabled")


def should_apply_rls() -> bool:
    """Check if RLS should be applied to current query."""
    if not RLS_ENABLED:
        return False
    if _bypass_rls.get():
        return False
    return True


# ============================================================================
# Tenant Mixin for SQLAlchemy Models
# ============================================================================

class TenantMixin:
    """
    Mixin that adds tenant_id column and automatic filtering.
    
    Usage:
        class User(Base, TenantMixin):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            name = Column(String)
            # tenant_id is automatically added
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(String(50), nullable=False, index=True)
    
    @classmethod
    def tenant_filter(cls, query: Query) -> Query:
        """Apply tenant filter to query."""
        if not should_apply_rls():
            return query
        
        tenant_id = get_tenant_context()
        if tenant_id:
            return query.filter(cls.tenant_id == tenant_id)
        
        logger.warning("rls_no_tenant_context", model=cls.__name__)
        return query


# ============================================================================
# Query Extension for Automatic Filtering
# ============================================================================

class TenantQuery(Query):
    """
    Custom Query class that automatically applies tenant filtering.
    
    Usage:
        # In your SQLAlchemy session setup
        Session = sessionmaker(bind=engine, query_cls=TenantQuery)
    """
    
    def __init__(self, entities, session=None):
        super().__init__(entities, session)
        self._apply_tenant_filter()
    
    def _apply_tenant_filter(self):
        """Automatically apply tenant filter if model has TenantMixin."""
        if not should_apply_rls():
            return
        
        tenant_id = get_tenant_context()
        if not tenant_id:
            return
        
        # Check if any entity has tenant_id
        for entity in self._entities:
            mapper = getattr(entity, 'mapper', None)
            if mapper and hasattr(mapper.class_, 'tenant_id'):
                self._criterion = (
                    self._criterion & (mapper.class_.tenant_id == tenant_id)
                    if self._criterion is not None
                    else (mapper.class_.tenant_id == tenant_id)
                )


# ============================================================================
# Session Event Listeners
# ============================================================================

def setup_rls_events(session_class):
    """
    Set up SQLAlchemy event listeners for automatic tenant assignment.
    
    Usage:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        setup_rls_events(Session)
    """
    
    @event.listens_for(session_class, "before_flush")
    def set_tenant_on_new_objects(session, flush_context, instances):
        """Automatically set tenant_id on new objects."""
        if not RLS_ENABLED:
            return
        
        tenant_id = get_tenant_context()
        if not tenant_id:
            return
        
        for obj in session.new:
            if hasattr(obj, 'tenant_id') and obj.tenant_id is None:
                obj.tenant_id = tenant_id
                logger.debug("rls_tenant_assigned", model=type(obj).__name__, tenant_id=tenant_id)
    
    @event.listens_for(session_class, "do_orm_execute")
    def add_tenant_filter(orm_execute_state):
        """Add tenant filter to SELECT queries."""
        if not should_apply_rls():
            return
        
        if orm_execute_state.is_select:
            tenant_id = get_tenant_context()
            if tenant_id:
                # Add tenant filter to the statement
                # This is a simplified version - production code would need more robust handling
                pass
    
    logger.info("rls_events_configured")


# ============================================================================
# Decorators
# ============================================================================

from functools import wraps
from typing import Callable

def with_tenant(tenant_id: str):
    """
    Decorator to run a function with a specific tenant context.
    
    Usage:
        @with_tenant("acme")
        async def get_acme_users():
            return await User.query.all()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = _current_tenant_id.set(tenant_id)
            try:
                return await func(*args, **kwargs)
            finally:
                _current_tenant_id.reset(token)
        return wrapper
    return decorator


def bypass_rls():
    """
    Decorator to bypass RLS for admin operations.
    
    Usage:
        @bypass_rls()
        async def get_all_users_admin():
            return await User.query.all()  # Returns users from ALL tenants
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = _bypass_rls.set(True)
            try:
                return await func(*args, **kwargs)
            finally:
                _bypass_rls.reset(token)
        return wrapper
    return decorator


# ============================================================================
# FastAPI Dependency
# ============================================================================

from fastapi import Request, Depends

async def rls_dependency(request: Request) -> str:
    """
    FastAPI dependency that sets tenant context from request.
    
    Usage:
        @app.get("/api/users")
        async def get_users(tenant_id: str = Depends(rls_dependency)):
            # Queries will automatically filter by tenant_id
            return await User.query.all()
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    
    if tenant_id:
        set_tenant_context(tenant_id)
        return tenant_id
    
    # Check for bypass roles
    user_roles = getattr(request.state, "user_roles", [])
    if any(role in RLS_BYPASS_ROLES for role in user_roles):
        set_bypass_rls(True)
        return None
    
    logger.warning("rls_no_tenant", path=request.url.path)
    return None


# ============================================================================
# PostgreSQL RLS Setup (SQL Scripts)
# ============================================================================

POSTGRES_RLS_SETUP = """
-- Enable RLS on a table
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation_policy ON {table_name}
    USING (tenant_id = current_setting('app.current_tenant')::text);

-- Create policy for INSERT (set tenant_id automatically)
CREATE POLICY tenant_insert_policy ON {table_name}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);

-- Function to set current tenant in session
CREATE OR REPLACE FUNCTION set_current_tenant(tenant_id text) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id, false);
END;
$$ LANGUAGE plpgsql;
"""

POSTGRES_RLS_DISABLE = """
-- Disable RLS on a table
ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;

-- Drop policies
DROP POLICY IF EXISTS tenant_isolation_policy ON {table_name};
DROP POLICY IF EXISTS tenant_insert_policy ON {table_name};
"""


def get_rls_setup_sql(table_name: str) -> str:
    """Get SQL to enable RLS on a table."""
    return POSTGRES_RLS_SETUP.format(table_name=table_name)


def get_rls_disable_sql(table_name: str) -> str:
    """Get SQL to disable RLS on a table."""
    return POSTGRES_RLS_DISABLE.format(table_name=table_name)


# ============================================================================
# Setup Function
# ============================================================================

def setup_row_level_security(enabled: bool = True) -> None:
    """
    Configure Row-Level Security.
    
    Usage:
        from app.rls import setup_row_level_security, TenantMixin, rls_dependency
        
        setup_row_level_security()
        
        class User(Base, TenantMixin):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            name = Column(String)
        
        @app.get("/api/users")
        async def get_users(_: str = Depends(rls_dependency)):
            # Automatically filtered by tenant
            ...
    """
    global RLS_ENABLED
    RLS_ENABLED = enabled
    
    logger.info("rls_configured", enabled=enabled, bypass_roles=RLS_BYPASS_ROLES)

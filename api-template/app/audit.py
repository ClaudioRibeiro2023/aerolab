"""
Audit Logging System

Provides comprehensive audit logging for security-sensitive operations.
Logs are structured for easy querying and compliance reporting.
"""
from fastapi import FastAPI, Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel
import json
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "logs/audit.jsonl")
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"

# ============================================================================
# Audit Event Types
# ============================================================================

class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGE = "auth.password_change"
    TOKEN_REFRESH = "auth.token_refresh"
    
    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"
    
    # Data Access
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    
    # Configuration
    CONFIG_READ = "config.read"
    CONFIG_UPDATE = "config.update"
    
    # Security
    PERMISSION_DENIED = "security.permission_denied"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    
    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class AuditOutcome(str, Enum):
    """Outcome of an audited action."""
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    ERROR = "error"


# ============================================================================
# Audit Log Entry Model
# ============================================================================

class AuditLogEntry(BaseModel):
    """Structured audit log entry."""
    timestamp: str
    action: AuditAction
    outcome: AuditOutcome
    
    # Actor information
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_roles: Optional[list[str]] = None
    
    # Request context
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Tenant context (for multi-tenant apps)
    tenant_id: Optional[str] = None
    
    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Additional details
    details: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Compliance fields
    data_classification: Optional[str] = None  # e.g., "public", "internal", "confidential", "restricted"
    retention_days: int = 365


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """
    Audit logger for security-sensitive operations.
    
    Usage:
        audit = AuditLogger()
        
        audit.log(
            action=AuditAction.USER_CREATE,
            outcome=AuditOutcome.SUCCESS,
            user_id="user123",
            resource_type="user",
            resource_id="new-user-456",
            details={"email": "new@example.com"}
        )
    """
    
    def __init__(self, log_file: Optional[str] = None, enabled: bool = True):
        self.log_file = log_file or AUDIT_LOG_FILE
        self.enabled = enabled and AUDIT_ENABLED
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
    
    def log(
        self,
        action: AuditAction,
        outcome: AuditOutcome,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_roles: Optional[list[str]] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
        data_classification: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an audit event."""
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            action=action,
            outcome=outcome,
            user_id=user_id,
            user_email=user_email,
            user_roles=user_roles,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            error_message=error_message,
            data_classification=data_classification,
        )
        
        if self.enabled:
            self._write_entry(entry)
            self._log_to_structured(entry)
        
        return entry
    
    def _write_entry(self, entry: AuditLogEntry) -> None:
        """Write entry to audit log file (JSONL format)."""
        try:
            with open(self.log_file, "a") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error("audit_write_error", error=str(e))
    
    def _log_to_structured(self, entry: AuditLogEntry) -> None:
        """Also log to structured logger for aggregation."""
        log_data = {
            "action": entry.action.value,
            "outcome": entry.outcome.value,
            "user_id": entry.user_id,
            "resource": f"{entry.resource_type}:{entry.resource_id}" if entry.resource_type else None,
            "ip": entry.ip_address,
        }
        
        if entry.outcome == AuditOutcome.SUCCESS:
            logger.info("audit_event", **{k: v for k, v in log_data.items() if v})
        elif entry.outcome == AuditOutcome.FAILURE:
            logger.warning("audit_event", **{k: v for k, v in log_data.items() if v})
        else:
            logger.error("audit_event", **{k: v for k, v in log_data.items() if v}, error=entry.error_message)
    
    def log_from_request(
        self,
        request: Request,
        action: AuditAction,
        outcome: AuditOutcome,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an audit event with context from the request."""
        # Extract user info from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)
        user_roles = getattr(request.state, "user_roles", None)
        tenant_id = getattr(request.state, "tenant_id", None)
        request_id = getattr(request.state, "request_id", None)
        
        # Get IP address
        ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip_address:
            ip_address = request.headers.get("X-Real-IP", request.client.host if request.client else None)
        
        return self.log(
            action=action,
            outcome=outcome,
            user_id=user_id,
            user_email=user_email,
            user_roles=user_roles,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=request.headers.get("User-Agent"),
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            error_message=error_message,
        )


# Global audit logger instance
audit_logger = AuditLogger()


# ============================================================================
# Audit Middleware (Optional - for automatic request logging)
# ============================================================================

class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log all requests.
    Use with caution - can generate large volumes of logs.
    """
    
    # Paths to exclude from automatic logging
    EXCLUDE_PATHS = {
        "/health",
        "/health/live",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)
        
        # Determine action based on method
        method_to_action = {
            "GET": AuditAction.DATA_READ,
            "POST": AuditAction.DATA_CREATE,
            "PUT": AuditAction.DATA_UPDATE,
            "PATCH": AuditAction.DATA_UPDATE,
            "DELETE": AuditAction.DATA_DELETE,
        }
        action = method_to_action.get(request.method, AuditAction.DATA_READ)
        
        # Execute request
        response = await call_next(request)
        
        # Determine outcome
        if response.status_code < 400:
            outcome = AuditOutcome.SUCCESS
        elif response.status_code == 403:
            outcome = AuditOutcome.DENIED
        elif response.status_code < 500:
            outcome = AuditOutcome.FAILURE
        else:
            outcome = AuditOutcome.ERROR
        
        # Log the request
        audit_logger.log_from_request(
            request=request,
            action=action,
            outcome=outcome,
            resource_type="api",
            resource_id=request.url.path,
            details={
                "method": request.method,
                "status_code": response.status_code,
            },
        )
        
        return response


# ============================================================================
# Setup Function
# ============================================================================

def setup_audit_logging(app: FastAPI, auto_log_requests: bool = False) -> None:
    """
    Configure audit logging for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        auto_log_requests: If True, automatically log all requests (high volume)
    
    Usage:
        from app.audit import setup_audit_logging, audit_logger, AuditAction, AuditOutcome
        
        setup_audit_logging(app)
        
        # Manual logging in routes
        @app.post("/api/users")
        async def create_user(request: Request, user: UserCreate):
            # ... create user ...
            audit_logger.log_from_request(
                request=request,
                action=AuditAction.USER_CREATE,
                outcome=AuditOutcome.SUCCESS,
                resource_type="user",
                resource_id=new_user.id,
            )
    """
    if auto_log_requests:
        app.add_middleware(AuditMiddleware)
        logger.info("audit_middleware_enabled")
    
    # Log system startup
    audit_logger.log(
        action=AuditAction.SYSTEM_STARTUP,
        outcome=AuditOutcome.SUCCESS,
        details={"version": os.getenv("API_VERSION", "unknown")},
    )
    
    logger.info("audit_logging_configured", log_file=AUDIT_LOG_FILE)


# ============================================================================
# Convenience Functions
# ============================================================================

def log_login(
    user_id: str,
    user_email: str,
    ip_address: str,
    success: bool,
    error_message: Optional[str] = None,
) -> AuditLogEntry:
    """Log a login attempt."""
    return audit_logger.log(
        action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
        outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        error_message=error_message,
    )


def log_data_access(
    request: Request,
    resource_type: str,
    resource_id: str,
    action: AuditAction = AuditAction.DATA_READ,
    details: Optional[dict] = None,
) -> AuditLogEntry:
    """Log data access."""
    return audit_logger.log_from_request(
        request=request,
        action=action,
        outcome=AuditOutcome.SUCCESS,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )


def log_permission_denied(
    request: Request,
    resource_type: str,
    resource_id: str,
    required_permission: str,
) -> AuditLogEntry:
    """Log a permission denied event."""
    return audit_logger.log_from_request(
        request=request,
        action=AuditAction.PERMISSION_DENIED,
        outcome=AuditOutcome.DENIED,
        resource_type=resource_type,
        resource_id=resource_id,
        details={"required_permission": required_permission},
    )

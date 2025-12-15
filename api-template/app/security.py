"""
Security Headers and Content Security Policy

Provides CSP headers and other security configurations for production deployments.
"""
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Environment
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# CSP Directives
CSP_REPORT_URI = os.getenv("CSP_REPORT_URI", "/api/csp-report")
CSP_REPORT_ONLY = os.getenv("CSP_REPORT_ONLY", "false").lower() == "true"

# Trusted domains (customize per environment)
TRUSTED_DOMAINS = [
    "'self'",
    os.getenv("FRONTEND_URL", "http://localhost:13000"),
    os.getenv("API_URL", "http://localhost:8000"),
    os.getenv("KEYCLOAK_URL", "http://localhost:8080"),
]

# CDN domains (for assets)
CDN_DOMAINS = [
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "https://cdn.jsdelivr.net",
]

# ============================================================================
# Content Security Policy Builder
# ============================================================================

class CSPBuilder:
    """
    Builder for Content Security Policy headers.
    
    Usage:
        csp = CSPBuilder()
        csp.add_directive("script-src", "'self'", "https://cdn.example.com")
        header_value = csp.build()
    """
    
    def __init__(self):
        self.directives: dict[str, list[str]] = {}
    
    def add_directive(self, directive: str, *sources: str) -> "CSPBuilder":
        """Add or append to a CSP directive."""
        if directive not in self.directives:
            self.directives[directive] = []
        self.directives[directive].extend(sources)
        return self
    
    def build(self) -> str:
        """Build the CSP header value."""
        parts = []
        for directive, sources in self.directives.items():
            unique_sources = list(dict.fromkeys(sources))  # Remove duplicates, preserve order
            parts.append(f"{directive} {' '.join(unique_sources)}")
        return "; ".join(parts)
    
    @classmethod
    def default(cls) -> "CSPBuilder":
        """Create a CSP builder with sensible defaults."""
        builder = cls()
        
        # Default source
        builder.add_directive("default-src", "'self'")
        
        # Scripts - allow self and inline for React
        builder.add_directive("script-src", "'self'", "'unsafe-inline'", "'unsafe-eval'")
        for domain in CDN_DOMAINS:
            builder.add_directive("script-src", domain)
        
        # Styles - allow self, inline, and Google Fonts
        builder.add_directive("style-src", "'self'", "'unsafe-inline'")
        for domain in CDN_DOMAINS:
            builder.add_directive("style-src", domain)
        
        # Images
        builder.add_directive("img-src", "'self'", "data:", "blob:", "https:")
        
        # Fonts
        builder.add_directive("font-src", "'self'", "data:")
        for domain in CDN_DOMAINS:
            builder.add_directive("font-src", domain)
        
        # Connect (API calls, WebSockets)
        builder.add_directive("connect-src", "'self'")
        for domain in TRUSTED_DOMAINS:
            builder.add_directive("connect-src", domain)
        # Allow WebSocket connections
        builder.add_directive("connect-src", "ws:", "wss:")
        
        # Frame ancestors (clickjacking protection)
        builder.add_directive("frame-ancestors", "'self'")
        
        # Form actions
        builder.add_directive("form-action", "'self'")
        for domain in TRUSTED_DOMAINS:
            builder.add_directive("form-action", domain)
        
        # Base URI
        builder.add_directive("base-uri", "'self'")
        
        # Object sources (Flash, etc.)
        builder.add_directive("object-src", "'none'")
        
        # Report URI
        if CSP_REPORT_URI:
            builder.add_directive("report-uri", CSP_REPORT_URI)
        
        return builder


# Default CSP
DEFAULT_CSP = CSPBuilder.default().build()


# ============================================================================
# Security Headers Middleware
# ============================================================================

class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add Content Security Policy and other security headers.
    """
    
    def __init__(self, app, csp: Optional[str] = None, report_only: bool = False):
        super().__init__(app)
        self.csp = csp or DEFAULT_CSP
        self.report_only = report_only or CSP_REPORT_ONLY
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        header_name = "Content-Security-Policy-Report-Only" if self.report_only else "Content-Security-Policy"
        response.headers[header_name] = self.csp
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options (backup for browsers that don't support CSP frame-ancestors)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # X-XSS-Protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        # HSTS (only in production with HTTPS)
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# ============================================================================
# CSP Report Endpoint
# ============================================================================

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

csp_router = APIRouter(tags=["Security"])


class CSPViolationReport(BaseModel):
    """CSP violation report from browser."""
    document_uri: Optional[str] = None
    referrer: Optional[str] = None
    violated_directive: Optional[str] = None
    effective_directive: Optional[str] = None
    original_policy: Optional[str] = None
    blocked_uri: Optional[str] = None
    status_code: Optional[int] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None


@csp_router.post("/api/csp-report")
async def receive_csp_report(request: Request):
    """
    Receive CSP violation reports from browsers.
    
    Browsers send reports in format: {"csp-report": {...}}
    """
    try:
        body = await request.json()
        report = body.get("csp-report", body)
        
        logger.warning(
            "csp_violation",
            document_uri=report.get("document-uri"),
            blocked_uri=report.get("blocked-uri"),
            violated_directive=report.get("violated-directive"),
            source_file=report.get("source-file"),
            line_number=report.get("line-number"),
        )
        
        return {"status": "received"}
    except Exception as e:
        logger.error("csp_report_error", error=str(e))
        return {"status": "error", "message": str(e)}


# ============================================================================
# Setup Function
# ============================================================================

def setup_content_security_policy(
    app: FastAPI,
    csp: Optional[str] = None,
    report_only: bool = False,
    include_report_endpoint: bool = True,
) -> None:
    """
    Configure Content Security Policy for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        csp: Custom CSP string (uses default if not provided)
        report_only: If True, uses Report-Only header (won't block, just report)
        include_report_endpoint: If True, adds the /api/csp-report endpoint
    
    Usage:
        from app.security import setup_content_security_policy
        
        setup_content_security_policy(app)
    """
    app.add_middleware(
        ContentSecurityPolicyMiddleware,
        csp=csp,
        report_only=report_only,
    )
    
    if include_report_endpoint:
        app.include_router(csp_router)
    
    logger.info(
        "csp_configured",
        report_only=report_only,
        report_endpoint=include_report_endpoint,
    )

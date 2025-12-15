"""
CSRF Protection Middleware

Implements Cross-Site Request Forgery protection using double-submit cookie pattern.
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from typing import Optional
import secrets
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Secret key for signing tokens (should be set via environment variable in production)
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", secrets.token_hex(32))
CSRF_TOKEN_EXPIRY = int(os.getenv("CSRF_TOKEN_EXPIRY", "3600"))  # 1 hour default
CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
CSRF_HEADER_NAME = os.getenv("CSRF_HEADER_NAME", "X-CSRF-Token")
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "false").lower() == "true"
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "strict")

# Methods that require CSRF protection
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that are exempt from CSRF protection (e.g., login, webhooks)
CSRF_EXEMPT_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/health/live",
    "/health/ready",
}

# ============================================================================
# Token Serializer
# ============================================================================

serializer = URLSafeTimedSerializer(CSRF_SECRET_KEY)


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    token_data = secrets.token_hex(32)
    return serializer.dumps(token_data)


def validate_csrf_token(token: str, max_age: int = CSRF_TOKEN_EXPIRY) -> bool:
    """Validate a CSRF token."""
    try:
        serializer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


# ============================================================================
# CSRF Middleware
# ============================================================================

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using double-submit cookie pattern.
    
    How it works:
    1. For safe methods (GET, HEAD, OPTIONS), set a CSRF cookie if not present
    2. For unsafe methods (POST, PUT, PATCH, DELETE), validate that:
       - The CSRF cookie is present
       - The X-CSRF-Token header matches the cookie value
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for exempt paths
        if request.url.path in CSRF_EXEMPT_PATHS:
            return await call_next(request)
        
        # Skip CSRF for safe methods but set cookie
        if request.method not in CSRF_PROTECTED_METHODS:
            response = await call_next(request)
            
            # Set CSRF cookie if not present
            if CSRF_COOKIE_NAME not in request.cookies:
                csrf_token = generate_csrf_token()
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=csrf_token,
                    httponly=False,  # Must be readable by JavaScript
                    secure=CSRF_COOKIE_SECURE,
                    samesite=CSRF_COOKIE_SAMESITE,
                    max_age=CSRF_TOKEN_EXPIRY,
                )
            
            return response
        
        # For unsafe methods, validate CSRF token
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)
        
        # Check if tokens are present
        if not cookie_token:
            logger.warning(
                "csrf_missing_cookie",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "csrf_token_missing",
                    "message": "CSRF cookie not found. Please refresh the page.",
                },
            )
        
        if not header_token:
            logger.warning(
                "csrf_missing_header",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "csrf_header_missing",
                    "message": "CSRF header not found. Include X-CSRF-Token header.",
                },
            )
        
        # Validate tokens match
        if cookie_token != header_token:
            logger.warning(
                "csrf_token_mismatch",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "csrf_token_mismatch",
                    "message": "CSRF token validation failed.",
                },
            )
        
        # Validate token is not expired
        if not validate_csrf_token(cookie_token):
            logger.warning(
                "csrf_token_invalid",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "csrf_token_invalid",
                    "message": "CSRF token is invalid or expired. Please refresh the page.",
                },
            )
        
        return await call_next(request)


# ============================================================================
# Setup Function
# ============================================================================

def setup_csrf_protection(app: FastAPI, enabled: bool = True) -> None:
    """
    Configure CSRF protection for the FastAPI application.
    
    Usage:
        from app.csrf import setup_csrf_protection
        
        setup_csrf_protection(app)
    
    Frontend usage:
        // Read CSRF token from cookie
        const csrfToken = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrf_token='))
            ?.split('=')[1];
        
        // Include in requests
        fetch('/api/resource', {
            method: 'POST',
            headers: {
                'X-CSRF-Token': csrfToken,
            },
            ...
        });
    """
    if not enabled:
        logger.info("csrf_protection_disabled")
        return
    
    app.add_middleware(CSRFMiddleware)
    
    logger.info(
        "csrf_protection_configured",
        cookie_name=CSRF_COOKIE_NAME,
        header_name=CSRF_HEADER_NAME,
        expiry=CSRF_TOKEN_EXPIRY,
    )


# ============================================================================
# Utility Endpoint
# ============================================================================

def add_csrf_endpoint(app: FastAPI) -> None:
    """Add an endpoint to get a fresh CSRF token."""
    
    @app.get("/api/csrf-token")
    async def get_csrf_token(request: Request):
        """
        Get a fresh CSRF token.
        The token is also set as a cookie.
        """
        csrf_token = generate_csrf_token()
        
        response = JSONResponse(content={"csrf_token": csrf_token})
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,
            secure=CSRF_COOKIE_SECURE,
            samesite=CSRF_COOKIE_SAMESITE,
            max_age=CSRF_TOKEN_EXPIRY,
        )
        
        return response

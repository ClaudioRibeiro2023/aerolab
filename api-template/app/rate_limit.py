"""
Rate Limiting Middleware

Implements request throttling using slowapi to prevent abuse and ensure fair usage.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from functools import wraps
from typing import Callable
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Default rate limits (can be overridden via environment variables)
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
AUTH_RATE_LIMIT = os.getenv("RATE_LIMIT_AUTH", "10/minute")
API_RATE_LIMIT = os.getenv("RATE_LIMIT_API", "60/minute")
HEALTH_RATE_LIMIT = os.getenv("RATE_LIMIT_HEALTH", "300/minute")

# Redis URL for distributed rate limiting (optional)
REDIS_URL = os.getenv("REDIS_URL")

# ============================================================================
# Limiter Setup
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Get client IP address, considering proxy headers.
    """
    # Check for X-Forwarded-For header (when behind a proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return get_remote_address(request)


# Create limiter instance
# Use Redis for distributed rate limiting if available, otherwise in-memory
if REDIS_URL:
    limiter = Limiter(
        key_func=get_client_ip,
        storage_uri=REDIS_URL,
        default_limits=[DEFAULT_RATE_LIMIT],
    )
    logger.info("rate_limiter_initialized", storage="redis", url=REDIS_URL)
else:
    limiter = Limiter(
        key_func=get_client_ip,
        default_limits=[DEFAULT_RATE_LIMIT],
    )
    logger.info("rate_limiter_initialized", storage="memory")

# ============================================================================
# Rate Limit Decorators
# ============================================================================

def rate_limit_auth(func: Callable) -> Callable:
    """Rate limit decorator for authentication endpoints (stricter)."""
    return limiter.limit(AUTH_RATE_LIMIT)(func)


def rate_limit_api(func: Callable) -> Callable:
    """Rate limit decorator for general API endpoints."""
    return limiter.limit(API_RATE_LIMIT)(func)


def rate_limit_health(func: Callable) -> Callable:
    """Rate limit decorator for health check endpoints (more lenient)."""
    return limiter.limit(HEALTH_RATE_LIMIT)(func)


# ============================================================================
# Custom Rate Limit Exceeded Handler
# ============================================================================

async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    Returns a JSON response with details about the limit.
    """
    logger.warning(
        "rate_limit_exceeded",
        client_ip=get_client_ip(request),
        path=request.url.path,
        limit=str(exc.detail),
    )
    
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", 60),
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60)),
            "X-RateLimit-Limit": str(exc.detail).split("/")[0] if "/" in str(exc.detail) else "unknown",
        },
    )


# ============================================================================
# Setup Function
# ============================================================================

def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.
    
    Usage:
        from app.rate_limit import setup_rate_limiting, limiter
        
        setup_rate_limiting(app)
        
        @app.get("/api/resource")
        @limiter.limit("10/minute")
        async def get_resource(request: Request):
            ...
    """
    # Store limiter in app state for access in routes
    app.state.limiter = limiter
    
    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    
    # Add SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info(
        "rate_limiting_configured",
        default_limit=DEFAULT_RATE_LIMIT,
        auth_limit=AUTH_RATE_LIMIT,
        api_limit=API_RATE_LIMIT,
    )


# ============================================================================
# Utility Functions
# ============================================================================

def get_rate_limit_headers(request: Request) -> dict:
    """
    Get current rate limit status for the request.
    Useful for including in API responses.
    """
    # Note: This requires the request to have been processed by the limiter
    return {
        "X-RateLimit-Limit": request.state.view_rate_limit if hasattr(request.state, "view_rate_limit") else "unknown",
        "X-RateLimit-Remaining": request.state.view_rate_limit_remaining if hasattr(request.state, "view_rate_limit_remaining") else "unknown",
        "X-RateLimit-Reset": request.state.view_rate_limit_reset if hasattr(request.state, "view_rate_limit_reset") else "unknown",
    }

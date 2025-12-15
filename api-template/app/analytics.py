"""
Event Tracking and Analytics

Provides privacy-first event tracking for user behavior analysis.
Supports multiple analytics backends (GA4, Mixpanel, custom).
"""
from fastapi import FastAPI, Request, APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime
from enum import Enum
import json
import os
import hashlib

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

ANALYTICS_ENABLED = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
ANALYTICS_BACKEND = os.getenv("ANALYTICS_BACKEND", "internal")  # internal, ga4, mixpanel
ANALYTICS_LOG_FILE = os.getenv("ANALYTICS_LOG_FILE", "logs/analytics.jsonl")

# Privacy settings
ANONYMIZE_IP = os.getenv("ANALYTICS_ANONYMIZE_IP", "true").lower() == "true"
HASH_USER_ID = os.getenv("ANALYTICS_HASH_USER_ID", "true").lower() == "true"
EXCLUDE_PII = os.getenv("ANALYTICS_EXCLUDE_PII", "true").lower() == "true"

# PII fields to exclude
PII_FIELDS = {"email", "phone", "name", "address", "ssn", "credit_card", "password"}

# ============================================================================
# Event Categories
# ============================================================================

class EventCategory(str, Enum):
    """Categories for analytics events."""
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    NAVIGATION = "navigation"
    FORM = "form"
    ERROR = "error"
    PERFORMANCE = "performance"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"


class StandardEvent(str, Enum):
    """Standard event types for consistency."""
    # Page events
    PAGE_VIEW = "page_view"
    PAGE_LEAVE = "page_leave"
    
    # User events
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    
    # Navigation
    CLICK = "click"
    SCROLL = "scroll"
    SEARCH = "search"
    
    # Forms
    FORM_START = "form_start"
    FORM_SUBMIT = "form_submit"
    FORM_ERROR = "form_error"
    FORM_ABANDON = "form_abandon"
    
    # Errors
    ERROR = "error"
    EXCEPTION = "exception"
    
    # Performance
    PAGE_LOAD = "page_load"
    API_CALL = "api_call"
    
    # Engagement
    FEATURE_USE = "feature_use"
    SHARE = "share"
    DOWNLOAD = "download"
    
    # Conversion
    CONVERSION = "conversion"
    PURCHASE = "purchase"


# ============================================================================
# Event Models
# ============================================================================

class AnalyticsEvent(BaseModel):
    """Analytics event model."""
    event_name: str
    category: EventCategory
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # User context (anonymized)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # Request context
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Event data
    properties: dict[str, Any] = {}
    
    # Performance metrics
    duration_ms: Optional[int] = None
    
    class Config:
        use_enum_values = True


class EventTrackRequest(BaseModel):
    """Request model for tracking events from frontend."""
    event_name: str
    category: Optional[EventCategory] = EventCategory.USER_ACTION
    properties: dict[str, Any] = {}
    duration_ms: Optional[int] = None


# ============================================================================
# Privacy Utilities
# ============================================================================

def anonymize_ip_address(ip: str) -> str:
    """Anonymize IP address by zeroing last octet (IPv4) or last 80 bits (IPv6)."""
    if not ip or not ANONYMIZE_IP:
        return ip
    
    if ":" in ip:  # IPv6
        parts = ip.split(":")
        return ":".join(parts[:3]) + ":0:0:0:0:0"
    else:  # IPv4
        parts = ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + ".0"
    
    return ip


def hash_identifier(identifier: str) -> str:
    """Hash user identifier for privacy."""
    if not identifier or not HASH_USER_ID:
        return identifier
    
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def sanitize_properties(properties: dict) -> dict:
    """Remove PII from event properties."""
    if not EXCLUDE_PII:
        return properties
    
    sanitized = {}
    for key, value in properties.items():
        key_lower = key.lower()
        if any(pii in key_lower for pii in PII_FIELDS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_properties(value)
        else:
            sanitized[key] = value
    
    return sanitized


# ============================================================================
# Analytics Tracker
# ============================================================================

class AnalyticsTracker:
    """
    Privacy-first analytics tracker.
    
    Usage:
        tracker = AnalyticsTracker()
        
        tracker.track(
            event_name="button_click",
            category=EventCategory.USER_ACTION,
            properties={"button_id": "submit-form"}
        )
    """
    
    def __init__(self, enabled: bool = True, log_file: Optional[str] = None):
        self.enabled = enabled and ANALYTICS_ENABLED
        self.log_file = log_file or ANALYTICS_LOG_FILE
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
    
    def track(
        self,
        event_name: str,
        category: EventCategory = EventCategory.USER_ACTION,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        page_url: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        properties: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[AnalyticsEvent]:
        """Track an analytics event."""
        if not self.enabled:
            return None
        
        # Apply privacy transformations
        event = AnalyticsEvent(
            event_name=event_name,
            category=category,
            user_id=hash_identifier(user_id) if user_id else None,
            session_id=session_id,
            tenant_id=tenant_id,
            page_url=page_url,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=anonymize_ip_address(ip_address) if ip_address else None,
            properties=sanitize_properties(properties or {}),
            duration_ms=duration_ms,
        )
        
        # Write to log file
        self._write_event(event)
        
        # Send to external analytics (if configured)
        self._send_to_backend(event)
        
        logger.debug("event_tracked", event=event_name, category=category.value)
        return event
    
    def track_from_request(
        self,
        request: Request,
        event_name: str,
        category: EventCategory = EventCategory.USER_ACTION,
        properties: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[AnalyticsEvent]:
        """Track event with context from HTTP request."""
        user_id = getattr(request.state, "user_id", None)
        session_id = request.cookies.get("session_id")
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # Get IP address
        ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip_address:
            ip_address = request.headers.get("X-Real-IP", request.client.host if request.client else None)
        
        return self.track(
            event_name=event_name,
            category=category,
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            page_url=str(request.url),
            referrer=request.headers.get("Referer"),
            user_agent=request.headers.get("User-Agent"),
            ip_address=ip_address,
            properties=properties,
            duration_ms=duration_ms,
        )
    
    def _write_event(self, event: AnalyticsEvent) -> None:
        """Write event to log file."""
        try:
            with open(self.log_file, "a") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error("analytics_write_error", error=str(e))
    
    def _send_to_backend(self, event: AnalyticsEvent) -> None:
        """Send event to external analytics backend."""
        if ANALYTICS_BACKEND == "internal":
            return  # Already logged to file
        
        # TODO: Implement GA4, Mixpanel, etc.
        # This is a placeholder for external integrations
        pass
    
    # Convenience methods for standard events
    def page_view(self, request: Request, page_title: Optional[str] = None) -> Optional[AnalyticsEvent]:
        """Track a page view."""
        return self.track_from_request(
            request=request,
            event_name=StandardEvent.PAGE_VIEW.value,
            category=EventCategory.PAGE_VIEW,
            properties={"page_title": page_title} if page_title else {},
        )
    
    def user_login(self, request: Request, method: str = "password") -> Optional[AnalyticsEvent]:
        """Track user login."""
        return self.track_from_request(
            request=request,
            event_name=StandardEvent.LOGIN.value,
            category=EventCategory.USER_ACTION,
            properties={"method": method},
        )
    
    def feature_use(self, request: Request, feature_name: str) -> Optional[AnalyticsEvent]:
        """Track feature usage."""
        return self.track_from_request(
            request=request,
            event_name=StandardEvent.FEATURE_USE.value,
            category=EventCategory.ENGAGEMENT,
            properties={"feature": feature_name},
        )
    
    def error(self, request: Request, error_type: str, error_message: str) -> Optional[AnalyticsEvent]:
        """Track an error."""
        return self.track_from_request(
            request=request,
            event_name=StandardEvent.ERROR.value,
            category=EventCategory.ERROR,
            properties={"error_type": error_type, "error_message": error_message},
        )


# Global tracker instance
analytics = AnalyticsTracker()


# ============================================================================
# API Router
# ============================================================================

analytics_router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@analytics_router.post("/track")
async def track_event(request: Request, event: EventTrackRequest):
    """
    Track an analytics event from the frontend.
    
    Example:
        POST /api/analytics/track
        {
            "event_name": "button_click",
            "category": "user_action",
            "properties": {"button_id": "submit-form"}
        }
    """
    tracked = analytics.track_from_request(
        request=request,
        event_name=event.event_name,
        category=event.category or EventCategory.USER_ACTION,
        properties=event.properties,
        duration_ms=event.duration_ms,
    )
    
    return {"status": "tracked" if tracked else "disabled"}


@analytics_router.post("/page-view")
async def track_page_view(request: Request, page_title: Optional[str] = None):
    """Track a page view."""
    analytics.page_view(request, page_title)
    return {"status": "tracked"}


@analytics_router.get("/status")
async def analytics_status():
    """Get analytics configuration status."""
    return {
        "enabled": ANALYTICS_ENABLED,
        "backend": ANALYTICS_BACKEND,
        "privacy": {
            "anonymize_ip": ANONYMIZE_IP,
            "hash_user_id": HASH_USER_ID,
            "exclude_pii": EXCLUDE_PII,
        },
    }


# ============================================================================
# Setup Function
# ============================================================================

def setup_analytics(app: FastAPI, enabled: bool = True) -> None:
    """
    Configure analytics tracking for the FastAPI application.
    
    Usage:
        from app.analytics import setup_analytics, analytics
        
        setup_analytics(app)
        
        # Track events in routes
        @app.post("/api/action")
        async def do_action(request: Request):
            analytics.feature_use(request, "my_feature")
            ...
    """
    global ANALYTICS_ENABLED
    ANALYTICS_ENABLED = enabled
    
    app.include_router(analytics_router)
    
    logger.info(
        "analytics_configured",
        enabled=enabled,
        backend=ANALYTICS_BACKEND,
        anonymize_ip=ANONYMIZE_IP,
    )

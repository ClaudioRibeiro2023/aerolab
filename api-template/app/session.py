"""
Redis Session Store

Provides distributed session management using Redis for multi-instance deployments.
"""
from typing import Optional, Any
from datetime import datetime, timedelta
import json
import secrets
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_PREFIX = os.getenv("SESSION_PREFIX", "session:")
SESSION_TTL = int(os.getenv("SESSION_TTL", "3600"))  # 1 hour default
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session_id")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax")

# ============================================================================
# Session Data Model
# ============================================================================

class SessionData:
    """Session data container."""
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        data: Optional[dict] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.data = data or {}
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(seconds=SESSION_TTL))
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            data=data.get("data", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def delete(self, key: str) -> None:
        self.data.pop(key, None)


# ============================================================================
# Session Store Interface
# ============================================================================

class SessionStore:
    """Abstract session store interface."""
    
    async def create(self, user_id: Optional[str] = None, data: Optional[dict] = None) -> SessionData:
        raise NotImplementedError
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        raise NotImplementedError
    
    async def update(self, session: SessionData) -> bool:
        raise NotImplementedError
    
    async def delete(self, session_id: str) -> bool:
        raise NotImplementedError
    
    async def refresh(self, session_id: str) -> Optional[SessionData]:
        raise NotImplementedError


# ============================================================================
# Redis Session Store Implementation
# ============================================================================

class RedisSessionStore(SessionStore):
    """Redis-backed session store for distributed deployments."""
    
    def __init__(self, redis_url: str = REDIS_URL, prefix: str = SESSION_PREFIX, ttl: int = SESSION_TTL):
        self.redis_url = redis_url
        self.prefix = prefix
        self.ttl = ttl
        self._redis = None
    
    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
                logger.info("redis_session_store_connected", url=self.redis_url)
            except Exception as e:
                logger.error("redis_session_store_connection_failed", error=str(e))
                raise
        return self._redis
    
    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.prefix}{session_id}"
    
    async def create(self, user_id: Optional[str] = None, data: Optional[dict] = None) -> SessionData:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            data=data,
        )
        
        redis = await self._get_redis()
        await redis.setex(
            self._key(session_id),
            self.ttl,
            json.dumps(session.to_dict()),
        )
        
        logger.info("session_created", session_id=session_id, user_id=user_id)
        return session
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID."""
        redis = await self._get_redis()
        data = await redis.get(self._key(session_id))
        
        if not data:
            return None
        
        session = SessionData.from_dict(json.loads(data))
        
        if session.is_expired():
            await self.delete(session_id)
            return None
        
        return session
    
    async def update(self, session: SessionData) -> bool:
        """Update session data."""
        redis = await self._get_redis()
        
        # Calculate remaining TTL
        remaining_ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
        if remaining_ttl <= 0:
            await self.delete(session.session_id)
            return False
        
        await redis.setex(
            self._key(session.session_id),
            remaining_ttl,
            json.dumps(session.to_dict()),
        )
        
        logger.debug("session_updated", session_id=session.session_id)
        return True
    
    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        redis = await self._get_redis()
        result = await redis.delete(self._key(session_id))
        
        if result:
            logger.info("session_deleted", session_id=session_id)
        
        return bool(result)
    
    async def refresh(self, session_id: str) -> Optional[SessionData]:
        """Refresh session TTL."""
        session = await self.get(session_id)
        if not session:
            return None
        
        session.expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)
        await self.update(session)
        
        logger.debug("session_refreshed", session_id=session_id)
        return session
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# ============================================================================
# In-Memory Session Store (for development/testing)
# ============================================================================

class MemorySessionStore(SessionStore):
    """In-memory session store for development and testing."""
    
    def __init__(self, ttl: int = SESSION_TTL):
        self.ttl = ttl
        self._sessions: dict[str, SessionData] = {}
    
    async def create(self, user_id: Optional[str] = None, data: Optional[dict] = None) -> SessionData:
        session_id = secrets.token_urlsafe(32)
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            data=data,
        )
        self._sessions[session_id] = session
        logger.info("session_created", session_id=session_id, user_id=user_id, store="memory")
        return session
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            await self.delete(session_id)
            return None
        return session
    
    async def update(self, session: SessionData) -> bool:
        if session.session_id not in self._sessions:
            return False
        self._sessions[session.session_id] = session
        return True
    
    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("session_deleted", session_id=session_id, store="memory")
            return True
        return False
    
    async def refresh(self, session_id: str) -> Optional[SessionData]:
        session = await self.get(session_id)
        if not session:
            return None
        session.expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)
        return session


# ============================================================================
# Factory Function
# ============================================================================

def create_session_store(use_redis: bool = True) -> SessionStore:
    """
    Create appropriate session store based on configuration.
    
    Usage:
        session_store = create_session_store()
        
        # Create session
        session = await session_store.create(user_id="user123")
        
        # Get session
        session = await session_store.get(session_id)
        
        # Update session data
        session.set("key", "value")
        await session_store.update(session)
        
        # Delete session
        await session_store.delete(session_id)
    """
    if use_redis and REDIS_URL:
        logger.info("using_redis_session_store", url=REDIS_URL)
        return RedisSessionStore()
    else:
        logger.info("using_memory_session_store")
        return MemorySessionStore()


# Global session store instance
session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get the global session store instance."""
    global session_store
    if session_store is None:
        session_store = create_session_store()
    return session_store

"""
Rate Limiting distribuído com Redis.

Protege a API contra abuso com limites por usuário/IP.
"""

import os
import time
import hashlib
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RateLimitStrategy(Enum):
    """Estratégias de rate limiting."""
    FIXED_WINDOW = "fixed_window"       # Janela fixa
    SLIDING_WINDOW = "sliding_window"   # Janela deslizante
    TOKEN_BUCKET = "token_bucket"       # Token bucket
    LEAKY_BUCKET = "leaky_bucket"       # Leaky bucket


@dataclass
class RateLimitResult:
    """Resultado de verificação de rate limit."""
    allowed: bool
    remaining: int
    reset_at: datetime
    limit: int
    retry_after: Optional[int] = None
    
    def to_headers(self) -> Dict[str, str]:
        """Retorna headers HTTP padrão."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


@dataclass
class RateLimitConfig:
    """Configuração de rate limit."""
    requests: int = 100          # Requisições permitidas
    window_seconds: int = 60     # Janela de tempo
    burst: int = 10              # Burst permitido
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW


class RateLimiter:
    """
    Rate limiter distribuído.
    
    Features:
    - Múltiplas estratégias
    - Suporte a Redis para distribuição
    - Fallback para memória
    - Limites por usuário, IP ou endpoint
    - Headers HTTP padrão
    
    Configuração:
        RATE_LIMIT_ENABLED: Ativar rate limiting
        RATE_LIMIT_REQUESTS: Requisições por janela
        RATE_LIMIT_WINDOW: Tamanho da janela em segundos
    """
    
    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        redis_client = None,
        prefix: str = "ratelimit:"
    ):
        self.config = config or RateLimitConfig(
            requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        )
        self.redis = redis_client
        self.prefix = prefix
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        
        # Fallback para memória se Redis não disponível
        self._memory_store: Dict[str, Dict[str, Any]] = {}
    
    def _get_key(self, identifier: str, scope: str = "default") -> str:
        """Gera chave para o rate limit."""
        return f"{self.prefix}{scope}:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    async def check(
        self,
        identifier: str,
        scope: str = "default",
        cost: int = 1
    ) -> RateLimitResult:
        """
        Verifica rate limit.
        
        Args:
            identifier: Identificador único (user_id, IP, etc.)
            scope: Escopo do limite (endpoint, global, etc.)
            cost: Custo da requisição (1 por padrão)
        
        Returns:
            Resultado com status e informações
        """
        if not self.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=self.config.requests,
                reset_at=datetime.utcnow(),
                limit=self.config.requests
            )
        
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window(identifier, scope, cost)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket(identifier, scope, cost)
        else:
            return await self._fixed_window(identifier, scope, cost)
    
    async def _fixed_window(
        self,
        identifier: str,
        scope: str,
        cost: int
    ) -> RateLimitResult:
        """Rate limit com janela fixa."""
        key = self._get_key(identifier, scope)
        now = time.time()
        window_start = int(now // self.config.window_seconds) * self.config.window_seconds
        window_end = window_start + self.config.window_seconds
        
        if self.redis:
            # Usar Redis
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.config.window_seconds)
            results = await pipe.execute()
            current = results[0]
        else:
            # Usar memória
            if key not in self._memory_store or self._memory_store[key].get("window") != window_start:
                self._memory_store[key] = {"count": 0, "window": window_start}
            
            self._memory_store[key]["count"] += cost
            current = self._memory_store[key]["count"]
        
        remaining = max(0, self.config.requests - current)
        allowed = current <= self.config.requests
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=datetime.fromtimestamp(window_end),
            limit=self.config.requests,
            retry_after=int(window_end - now) if not allowed else None
        )
    
    async def _sliding_window(
        self,
        identifier: str,
        scope: str,
        cost: int
    ) -> RateLimitResult:
        """Rate limit com janela deslizante."""
        key = self._get_key(identifier, scope)
        now = time.time()
        window_start = now - self.config.window_seconds
        
        if self.redis:
            # Usar Redis sorted set
            pipe = self.redis.pipeline()
            # Remover entradas antigas
            pipe.zremrangebyscore(key, 0, window_start)
            # Adicionar nova entrada
            pipe.zadd(key, {str(now): now})
            # Contar entradas
            pipe.zcard(key)
            # Definir expiração
            pipe.expire(key, self.config.window_seconds)
            results = await pipe.execute()
            current = results[2]
        else:
            # Usar memória
            if key not in self._memory_store:
                self._memory_store[key] = {"timestamps": []}
            
            # Limpar antigos
            self._memory_store[key]["timestamps"] = [
                ts for ts in self._memory_store[key]["timestamps"]
                if ts > window_start
            ]
            
            # Adicionar novo
            self._memory_store[key]["timestamps"].append(now)
            current = len(self._memory_store[key]["timestamps"])
        
        remaining = max(0, self.config.requests - current)
        allowed = current <= self.config.requests
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=datetime.fromtimestamp(now + self.config.window_seconds),
            limit=self.config.requests,
            retry_after=self.config.window_seconds if not allowed else None
        )
    
    async def _token_bucket(
        self,
        identifier: str,
        scope: str,
        cost: int
    ) -> RateLimitResult:
        """Rate limit com token bucket."""
        key = self._get_key(identifier, scope)
        now = time.time()
        
        # Recuperar estado
        if self.redis:
            data = await self.redis.hgetall(key)
            tokens = float(data.get(b"tokens", self.config.requests))
            last_update = float(data.get(b"last_update", now))
        else:
            if key not in self._memory_store:
                self._memory_store[key] = {
                    "tokens": float(self.config.requests),
                    "last_update": now
                }
            tokens = self._memory_store[key]["tokens"]
            last_update = self._memory_store[key]["last_update"]
        
        # Calcular tokens adicionados
        elapsed = now - last_update
        refill_rate = self.config.requests / self.config.window_seconds
        tokens = min(self.config.requests, tokens + elapsed * refill_rate)
        
        # Verificar se pode consumir
        allowed = tokens >= cost
        if allowed:
            tokens -= cost
        
        # Salvar estado
        if self.redis:
            await self.redis.hmset(key, {"tokens": tokens, "last_update": now})
            await self.redis.expire(key, self.config.window_seconds * 2)
        else:
            self._memory_store[key] = {"tokens": tokens, "last_update": now}
        
        remaining = int(tokens)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=datetime.fromtimestamp(now + self.config.window_seconds),
            limit=self.config.requests,
            retry_after=int((cost - tokens) / refill_rate) if not allowed else None
        )
    
    async def reset(self, identifier: str, scope: str = "default"):
        """Reseta rate limit para um identificador."""
        key = self._get_key(identifier, scope)
        if self.redis:
            await self.redis.delete(key)
        elif key in self._memory_store:
            del self._memory_store[key]
    
    def get_middleware(self):
        """Retorna middleware FastAPI."""
        from fastapi import Request, HTTPException
        from starlette.middleware.base import BaseHTTPMiddleware
        
        limiter = self
        
        class RateLimitMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Identificar por IP ou user
                identifier = request.client.host if request.client else "unknown"
                
                # Usar user_id se autenticado
                if hasattr(request.state, "user"):
                    identifier = str(request.state.user.get("sub", identifier))
                
                result = await limiter.check(identifier, scope=request.url.path)
                
                if not result.allowed:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers=result.to_headers()
                    )
                
                response = await call_next(request)
                
                # Adicionar headers
                for key, value in result.to_headers().items():
                    response.headers[key] = value
                
                return response
        
        return RateLimitMiddleware


# Configurações por tier
RATE_LIMIT_TIERS = {
    "free": RateLimitConfig(requests=60, window_seconds=60),
    "starter": RateLimitConfig(requests=300, window_seconds=60),
    "pro": RateLimitConfig(requests=1000, window_seconds=60),
    "enterprise": RateLimitConfig(requests=10000, window_seconds=60),
}


# Singleton
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Obtém instância singleton do RateLimiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

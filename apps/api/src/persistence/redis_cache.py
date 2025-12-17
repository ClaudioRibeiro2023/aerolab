"""
Cache distribuído com Redis.

Gerencia cache de respostas, sessões e dados temporários.
"""

import os
import json
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisCache:
    """
    Cache distribuído com Redis.
    
    Features:
    - Cache de respostas de agentes
    - Sessões de usuário
    - Rate limiting distribuído
    - Pub/Sub para eventos
    - TTL automático
    
    Configuração:
        REDIS_URL ou variáveis individuais:
        REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB
    """
    
    DEFAULT_TTL = 3600  # 1 hora
    
    def __init__(
        self,
        url: Optional[str] = None,
        prefix: str = "agentos:"
    ):
        if not HAS_REDIS:
            raise ImportError(
                "redis não instalado. Instale com: pip install redis"
            )
        
        self.url = url or self._build_url()
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None
    
    def _build_url(self) -> str:
        """Constrói URL do Redis a partir de variáveis de ambiente."""
        url = os.getenv("REDIS_URL")
        if url:
            return url
        
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        password = os.getenv("REDIS_PASSWORD", "")
        db = os.getenv("REDIS_DB", "0")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    async def connect(self):
        """Inicializa conexão com Redis."""
        if self._client is None:
            self._client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect(self):
        """Fecha conexão."""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def _ensure_connected(self):
        """Garante que está conectado."""
        if not self._client:
            await self.connect()
    
    def _key(self, key: str) -> str:
        """Adiciona prefix à chave."""
        return f"{self.prefix}{key}"
    
    # Operações básicas
    async def get(self, key: str) -> Optional[str]:
        """Obtém valor do cache."""
        await self._ensure_connected()
        return await self._client.get(self._key(key))
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Define valor no cache."""
        await self._ensure_connected()
        return await self._client.set(
            self._key(key),
            value,
            ex=ttl or self.DEFAULT_TTL
        )
    
    async def delete(self, key: str) -> int:
        """Remove valor do cache."""
        await self._ensure_connected()
        return await self._client.delete(self._key(key))
    
    async def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        await self._ensure_connected()
        return await self._client.exists(self._key(key)) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Define TTL para chave existente."""
        await self._ensure_connected()
        return await self._client.expire(self._key(key), ttl)
    
    async def ttl(self, key: str) -> int:
        """Retorna TTL restante."""
        await self._ensure_connected()
        return await self._client.ttl(self._key(key))
    
    # JSON helpers
    async def get_json(self, key: str) -> Optional[Any]:
        """Obtém valor JSON do cache."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Define valor JSON no cache."""
        return await self.set(key, json.dumps(value, default=str), ttl)
    
    # Cache de respostas de agentes
    async def cache_response(
        self,
        agent_name: str,
        prompt_hash: str,
        response: str,
        ttl: int = 3600
    ) -> bool:
        """Cacheia resposta de agente."""
        key = f"response:{agent_name}:{prompt_hash}"
        return await self.set(key, response, ttl)
    
    async def get_cached_response(
        self,
        agent_name: str,
        prompt_hash: str
    ) -> Optional[str]:
        """Obtém resposta cacheada."""
        key = f"response:{agent_name}:{prompt_hash}"
        return await self.get(key)
    
    # Sessões
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 86400  # 24h
    ) -> bool:
        """Define sessão de usuário."""
        return await self.set_json(f"session:{session_id}", data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém sessão de usuário."""
        return await self.get_json(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> int:
        """Remove sessão."""
        return await self.delete(f"session:{session_id}")
    
    # Rate Limiting
    async def rate_limit_check(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Verifica rate limit.
        
        Args:
            identifier: ID único (IP, user_id, etc.)
            limit: Máximo de requisições
            window_seconds: Janela de tempo
        
        Returns:
            (allowed, remaining)
        """
        await self._ensure_connected()
        key = self._key(f"ratelimit:{identifier}")
        
        # Incrementa contador
        current = await self._client.incr(key)
        
        # Define TTL na primeira requisição
        if current == 1:
            await self._client.expire(key, window_seconds)
        
        allowed = current <= limit
        remaining = max(0, limit - current)
        
        return allowed, remaining
    
    async def rate_limit_reset(self, identifier: str) -> int:
        """Reseta rate limit."""
        return await self.delete(f"ratelimit:{identifier}")
    
    # Pub/Sub
    async def publish(self, channel: str, message: Any) -> int:
        """Publica mensagem em canal."""
        await self._ensure_connected()
        if not isinstance(message, str):
            message = json.dumps(message, default=str)
        return await self._client.publish(self._key(channel), message)
    
    async def subscribe(self, *channels: str):
        """Inscreve em canais."""
        await self._ensure_connected()
        pubsub = self._client.pubsub()
        await pubsub.subscribe(*[self._key(c) for c in channels])
        return pubsub
    
    # Listas (filas)
    async def lpush(self, key: str, *values: str) -> int:
        """Adiciona ao início da lista."""
        await self._ensure_connected()
        return await self._client.lpush(self._key(key), *values)
    
    async def rpush(self, key: str, *values: str) -> int:
        """Adiciona ao fim da lista."""
        await self._ensure_connected()
        return await self._client.rpush(self._key(key), *values)
    
    async def lpop(self, key: str) -> Optional[str]:
        """Remove e retorna primeiro elemento."""
        await self._ensure_connected()
        return await self._client.lpop(self._key(key))
    
    async def rpop(self, key: str) -> Optional[str]:
        """Remove e retorna último elemento."""
        await self._ensure_connected()
        return await self._client.rpop(self._key(key))
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Retorna range da lista."""
        await self._ensure_connected()
        return await self._client.lrange(self._key(key), start, end)
    
    async def llen(self, key: str) -> int:
        """Retorna tamanho da lista."""
        await self._ensure_connected()
        return await self._client.llen(self._key(key))
    
    # Hash (objetos)
    async def hset(self, key: str, field: str, value: str) -> int:
        """Define campo em hash."""
        await self._ensure_connected()
        return await self._client.hset(self._key(key), field, value)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Obtém campo de hash."""
        await self._ensure_connected()
        return await self._client.hget(self._key(key), field)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Obtém todos os campos de hash."""
        await self._ensure_connected()
        return await self._client.hgetall(self._key(key))
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Remove campos de hash."""
        await self._ensure_connected()
        return await self._client.hdel(self._key(key), *fields)
    
    # Utilitários
    async def keys(self, pattern: str = "*") -> List[str]:
        """Lista chaves que correspondem ao padrão."""
        await self._ensure_connected()
        keys = await self._client.keys(self._key(pattern))
        # Remove prefix
        return [k.replace(self.prefix, "", 1) for k in keys]
    
    async def flush_prefix(self) -> int:
        """Remove todas as chaves com o prefix."""
        await self._ensure_connected()
        keys = await self._client.keys(self._key("*"))
        if keys:
            return await self._client.delete(*keys)
        return 0
    
    async def info(self) -> Dict[str, Any]:
        """Retorna informações do Redis."""
        await self._ensure_connected()
        return await self._client.info()
    
    async def ping(self) -> bool:
        """Verifica conexão."""
        await self._ensure_connected()
        return await self._client.ping()


# Singleton
_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Obtém instância singleton do cache."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache

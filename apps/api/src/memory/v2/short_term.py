"""
Memory v2 - Short-Term Memory

Memória de curto prazo usando Redis.
Mantém contexto de sessão e mensagens recentes.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
import logging

import redis.asyncio as redis

from .config import MemoryConfig, get_memory_config
from .types import Memory, MemoryType, MemoryPriority, ConversationContext


logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    Short-Term Memory com Redis.
    
    Features:
    - Armazenamento de contexto de sessão
    - Histórico de mensagens
    - TTL automático
    - Promoção para long-term baseada em uso
    """
    
    # Prefixos de chaves
    MEMORY_PREFIX = "stm:mem:"
    SESSION_PREFIX = "stm:session:"
    CONTEXT_PREFIX = "stm:ctx:"
    INDEX_PREFIX = "stm:idx:"
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        self.stm_config = self.config.short_term
        self._redis: Optional[redis.Redis] = None
        
        # Métricas
        self.total_stored = 0
        self.total_retrieved = 0
        self.promotions = 0
    
    async def _get_redis(self) -> redis.Redis:
        """Retorna conexão Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.config.redis.url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    def _memory_key(self, memory_id: str) -> str:
        """Gera chave para uma memória."""
        return f"{self.MEMORY_PREFIX}{memory_id}"
    
    def _session_key(self, session_id: str) -> str:
        """Gera chave para índice de sessão."""
        return f"{self.SESSION_PREFIX}{session_id}"
    
    def _context_key(self, session_id: str) -> str:
        """Gera chave para contexto de conversa."""
        return f"{self.CONTEXT_PREFIX}{session_id}"
    
    async def store(
        self,
        memory: Memory,
        ttl: Optional[int] = None
    ) -> str:
        """
        Armazena uma memória.
        
        Args:
            memory: Memória a armazenar
            ttl: TTL em segundos (usa padrão se não especificado)
            
        Returns:
            ID da memória
        """
        r = await self._get_redis()
        
        # Garantir tipo correto
        memory.memory_type = MemoryType.SHORT_TERM
        memory.updated_at = datetime.now()
        
        # Calcular TTL
        if ttl is None:
            ttl = self.stm_config.default_ttl
        ttl = min(ttl, self.stm_config.max_ttl)
        
        # Calcular expiração
        memory.expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Serializar e armazenar
        key = self._memory_key(memory.id)
        await r.setex(key, ttl, json.dumps(memory.to_dict()))
        
        # Indexar por sessão
        if memory.session_id:
            session_key = self._session_key(memory.session_id)
            await r.sadd(session_key, memory.id)
            await r.expire(session_key, ttl)
        
        self.total_stored += 1
        logger.debug(f"Memória {memory.id} armazenada com TTL {ttl}s")
        
        return memory.id
    
    async def get(self, memory_id: str) -> Optional[Memory]:
        """
        Recupera uma memória por ID.
        
        Args:
            memory_id: ID da memória
            
        Returns:
            Memory ou None se não encontrada
        """
        r = await self._get_redis()
        
        key = self._memory_key(memory_id)
        data = await r.get(key)
        
        if not data:
            return None
        
        memory = Memory.from_dict(json.loads(data))
        
        # Atualizar acesso
        memory.access_count += 1
        memory.last_accessed = datetime.now()
        
        # Salvar atualização
        ttl = await r.ttl(key)
        if ttl > 0:
            await r.setex(key, ttl, json.dumps(memory.to_dict()))
        
        self.total_retrieved += 1
        
        return memory
    
    async def get_by_session(self, session_id: str) -> list[Memory]:
        """
        Recupera todas as memórias de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de memórias
        """
        r = await self._get_redis()
        
        session_key = self._session_key(session_id)
        memory_ids = await r.smembers(session_key)
        
        memories = []
        for mid in memory_ids:
            memory = await self.get(mid)
            if memory:
                memories.append(memory)
        
        # Ordenar por criação
        memories.sort(key=lambda m: m.created_at, reverse=True)
        
        return memories
    
    async def delete(self, memory_id: str) -> bool:
        """
        Remove uma memória.
        
        Args:
            memory_id: ID da memória
            
        Returns:
            True se removida
        """
        r = await self._get_redis()
        
        key = self._memory_key(memory_id)
        result = await r.delete(key)
        
        return result > 0
    
    async def clear_session(self, session_id: str) -> int:
        """
        Limpa todas as memórias de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Número de memórias removidas
        """
        r = await self._get_redis()
        
        session_key = self._session_key(session_id)
        memory_ids = await r.smembers(session_key)
        
        count = 0
        for mid in memory_ids:
            if await self.delete(mid):
                count += 1
        
        await r.delete(session_key)
        await r.delete(self._context_key(session_id))
        
        return count
    
    async def save_context(self, context: ConversationContext) -> None:
        """
        Salva contexto de conversa.
        
        Args:
            context: Contexto a salvar
        """
        r = await self._get_redis()
        
        key = self._context_key(context.session_id)
        
        data = {
            "session_id": context.session_id,
            "agent_id": context.agent_id,
            "user_id": context.user_id,
            "messages": context.messages[-self.stm_config.max_context_messages:],
            "variables": context.variables,
            "started_at": context.started_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "message_count": context.message_count,
            "token_count": context.token_count
        }
        
        await r.setex(key, self.stm_config.default_ttl, json.dumps(data))
    
    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Recupera contexto de conversa.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            ConversationContext ou None
        """
        r = await self._get_redis()
        
        key = self._context_key(session_id)
        data = await r.get(key)
        
        if not data:
            return None
        
        parsed = json.loads(data)
        
        context = ConversationContext(
            session_id=parsed["session_id"],
            agent_id=parsed["agent_id"],
            user_id=parsed.get("user_id"),
            messages=parsed.get("messages", []),
            variables=parsed.get("variables", {}),
            message_count=parsed.get("message_count", 0),
            token_count=parsed.get("token_count", 0)
        )
        
        if parsed.get("started_at"):
            context.started_at = datetime.fromisoformat(parsed["started_at"])
        if parsed.get("last_activity"):
            context.last_activity = datetime.fromisoformat(parsed["last_activity"])
        
        return context
    
    async def get_or_create_context(
        self,
        session_id: str,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> ConversationContext:
        """
        Recupera ou cria contexto de conversa.
        
        Args:
            session_id: ID da sessão
            agent_id: ID do agente
            user_id: ID do usuário (opcional)
            
        Returns:
            ConversationContext
        """
        context = await self.get_context(session_id)
        
        if context is None:
            context = ConversationContext(
                session_id=session_id,
                agent_id=agent_id,
                user_id=user_id
            )
            await self.save_context(context)
        
        return context
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> ConversationContext:
        """
        Adiciona mensagem ao contexto.
        
        Args:
            session_id: ID da sessão
            role: Papel (user, assistant, system)
            content: Conteúdo da mensagem
            metadata: Metadados opcionais
            
        Returns:
            Contexto atualizado
        """
        context = await self.get_context(session_id)
        
        if context is None:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        context.add_message(role, content, metadata)
        await self.save_context(context)
        
        return context
    
    async def check_for_promotion(self, memory: Memory) -> bool:
        """
        Verifica se memória deve ser promovida para long-term.
        
        Args:
            memory: Memória a verificar
            
        Returns:
            True se deve ser promovida
        """
        # Critérios de promoção
        if memory.access_count >= self.stm_config.promotion_access_count:
            return True
        
        if memory.importance_score >= self.stm_config.promotion_importance_threshold:
            return True
        
        if memory.priority in [MemoryPriority.HIGH, MemoryPriority.CRITICAL]:
            return True
        
        return False
    
    async def get_promotion_candidates(self, session_id: str) -> list[Memory]:
        """
        Retorna memórias candidatas a promoção.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de memórias a promover
        """
        memories = await self.get_by_session(session_id)
        
        candidates = []
        for memory in memories:
            if await self.check_for_promotion(memory):
                candidates.append(memory)
        
        return candidates
    
    async def extend_ttl(self, memory_id: str, additional_seconds: int) -> bool:
        """
        Estende o TTL de uma memória.
        
        Args:
            memory_id: ID da memória
            additional_seconds: Segundos adicionais
            
        Returns:
            True se estendido com sucesso
        """
        r = await self._get_redis()
        
        key = self._memory_key(memory_id)
        current_ttl = await r.ttl(key)
        
        if current_ttl < 0:
            return False
        
        new_ttl = min(current_ttl + additional_seconds, self.stm_config.max_ttl)
        await r.expire(key, new_ttl)
        
        return True
    
    def get_metrics(self) -> dict:
        """Retorna métricas."""
        return {
            "total_stored": self.total_stored,
            "total_retrieved": self.total_retrieved,
            "promotions": self.promotions
        }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._redis:
            await self._redis.close()


# Singleton
_short_term_memory: Optional[ShortTermMemory] = None


def get_short_term_memory(config: Optional[MemoryConfig] = None) -> ShortTermMemory:
    """Retorna o short-term memory singleton."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory(config)
    return _short_term_memory

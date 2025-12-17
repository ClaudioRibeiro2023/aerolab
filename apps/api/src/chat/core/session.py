"""
Session - Gerenciamento de sessões de chat.

Mantém estado temporário:
- Conversa ativa
- Mensagens em cache
- Typing indicators
- Presence
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class TypingIndicator:
    """Indicador de digitação."""
    user_id: str
    conversation_id: str
    started_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() - self.started_at > timedelta(seconds=5)


@dataclass
class Session:
    """
    Sessão de chat ativa.
    
    Mantém estado temporário para uma sessão de usuário.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Conversa ativa
    active_conversation_id: Optional[str] = None
    active_agent_id: Optional[str] = None
    
    # Estado
    is_typing: bool = False
    is_processing: bool = False
    
    # Contexto
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Histórico recente (cache)
    recent_message_ids: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Configurações de sessão
    max_cache_messages: int = 100
    session_timeout_minutes: int = 60
    
    def __post_init__(self):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(minutes=self.session_timeout_minutes)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def is_active(self) -> bool:
        return not self.is_expired
    
    def touch(self) -> None:
        """Atualiza última atividade e estende expiração."""
        self.last_activity = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=self.session_timeout_minutes)
    
    def set_active_conversation(self, conversation_id: str) -> None:
        """Define conversa ativa."""
        self.active_conversation_id = conversation_id
        self.touch()
    
    def set_active_agent(self, agent_id: str) -> None:
        """Define agente ativo."""
        self.active_agent_id = agent_id
        self.touch()
    
    def add_message_to_cache(self, message_id: str) -> None:
        """Adiciona mensagem ao cache."""
        self.recent_message_ids.append(message_id)
        # Limitar tamanho
        if len(self.recent_message_ids) > self.max_cache_messages:
            self.recent_message_ids = self.recent_message_ids[-self.max_cache_messages:]
        self.touch()
    
    def set_context(self, key: str, value: Any) -> None:
        """Define valor no contexto."""
        self.context[key] = value
        self.touch()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Obtém valor do contexto."""
        return self.context.get(key, default)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Define variável."""
        self.variables[key] = value
        self.touch()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Obtém variável."""
        return self.variables.get(key, default)
    
    def start_typing(self) -> None:
        """Inicia indicador de digitação."""
        self.is_typing = True
        self.touch()
    
    def stop_typing(self) -> None:
        """Para indicador de digitação."""
        self.is_typing = False
        self.touch()
    
    def start_processing(self) -> None:
        """Marca como processando."""
        self.is_processing = True
        self.touch()
    
    def stop_processing(self) -> None:
        """Para processamento."""
        self.is_processing = False
        self.touch()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "active_conversation_id": self.active_conversation_id,
            "active_agent_id": self.active_agent_id,
            "is_typing": self.is_typing,
            "is_processing": self.is_processing,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class SessionManager:
    """
    Gerenciador de sessões.
    
    Mantém sessões ativas em memória com suporte a Redis.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self._typing_indicators: Dict[str, TypingIndicator] = {}
        self._redis_url = redis_url
        self._redis = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Inicializa o gerenciador."""
        # Conectar Redis se configurado
        if self._redis_url:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self._redis_url)
                logger.info("SessionManager connected to Redis")
            except ImportError:
                logger.warning("redis package not installed, using in-memory sessions")
        
        # Iniciar tarefa de limpeza
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def shutdown(self) -> None:
        """Encerra o gerenciador."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
    
    async def _cleanup_loop(self) -> None:
        """Loop de limpeza de sessões expiradas."""
        while True:
            try:
                await asyncio.sleep(60)  # A cada minuto
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired(self) -> None:
        """Remove sessões expiradas."""
        expired = [
            session_id for session_id, session in self._sessions.items()
            if session.is_expired
        ]
        
        for session_id in expired:
            session = self._sessions.pop(session_id, None)
            if session:
                self._user_sessions.pop(session.user_id, None)
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")
    
    async def create_session(self, user_id: str) -> Session:
        """Cria uma nova sessão."""
        # Verificar se já existe sessão para o usuário
        existing = await self.get_session_by_user(user_id)
        if existing:
            return existing
        
        session = Session(user_id=user_id)
        self._sessions[session.id] = session
        self._user_sessions[user_id] = session.id
        
        # Persistir no Redis se disponível
        if self._redis:
            await self._redis.setex(
                f"session:{session.id}",
                session.session_timeout_minutes * 60,
                session.to_dict().__str__()
            )
        
        logger.debug(f"Created session {session.id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Obtém uma sessão por ID."""
        session = self._sessions.get(session_id)
        
        if session and session.is_expired:
            await self.delete_session(session_id)
            return None
        
        return session
    
    async def get_session_by_user(self, user_id: str) -> Optional[Session]:
        """Obtém sessão por user_id."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return await self.get_session(session_id)
        return None
    
    async def get_or_create_session(self, user_id: str) -> Session:
        """Obtém ou cria sessão para usuário."""
        session = await self.get_session_by_user(user_id)
        if session:
            session.touch()
            return session
        return await self.create_session(user_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Deleta uma sessão."""
        session = self._sessions.pop(session_id, None)
        if session:
            self._user_sessions.pop(session.user_id, None)
            
            if self._redis:
                await self._redis.delete(f"session:{session_id}")
            
            return True
        return False
    
    async def set_typing(self, user_id: str, conversation_id: str) -> None:
        """Marca usuário como digitando."""
        key = f"{user_id}:{conversation_id}"
        self._typing_indicators[key] = TypingIndicator(
            user_id=user_id,
            conversation_id=conversation_id
        )
    
    async def clear_typing(self, user_id: str, conversation_id: str) -> None:
        """Remove indicador de digitação."""
        key = f"{user_id}:{conversation_id}"
        self._typing_indicators.pop(key, None)
    
    async def get_typing_users(self, conversation_id: str) -> List[str]:
        """Retorna usuários digitando em uma conversa."""
        typing = []
        expired = []
        
        for key, indicator in self._typing_indicators.items():
            if indicator.conversation_id == conversation_id:
                if indicator.is_expired:
                    expired.append(key)
                else:
                    typing.append(indicator.user_id)
        
        # Limpar expirados
        for key in expired:
            self._typing_indicators.pop(key, None)
        
        return typing
    
    def get_active_session_count(self) -> int:
        """Retorna número de sessões ativas."""
        return len([s for s in self._sessions.values() if s.is_active])


# Singleton
_session_manager: Optional[SessionManager] = None


def get_session_manager(redis_url: Optional[str] = None) -> SessionManager:
    """Obtém o gerenciador de sessões singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(redis_url)
    return _session_manager

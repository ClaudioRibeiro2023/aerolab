"""
WebSocket Manager - Gerenciamento de conexões WebSocket.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Set
from enum import Enum
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipos de mensagem WebSocket."""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    DATA = "data"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"


@dataclass
class WebSocketMessage:
    """Mensagem WebSocket."""
    type: MessageType
    channel: Optional[str] = None
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: Optional[str] = None
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "channel": self.channel,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "id": self.id,
        })
    
    @classmethod
    def from_json(cls, data: str) -> "WebSocketMessage":
        parsed = json.loads(data)
        return cls(
            type=MessageType(parsed.get("type", "data")),
            channel=parsed.get("channel"),
            data=parsed.get("data"),
            id=parsed.get("id"),
        )


@dataclass
class WebSocketConnection:
    """Conexão WebSocket individual."""
    id: str
    user_id: Optional[str] = None
    
    # Subscriptions
    subscribed_channels: Set[str] = field(default_factory=set)
    
    # Status
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_authenticated: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Callbacks (set by manager)
    _send_callback: Optional[Callable] = None
    
    def subscribe(self, channel: str):
        """Inscreve em um canal."""
        self.subscribed_channels.add(channel)
    
    def unsubscribe(self, channel: str):
        """Cancela inscrição de um canal."""
        self.subscribed_channels.discard(channel)
    
    async def send(self, message: WebSocketMessage):
        """Envia mensagem para o cliente."""
        if self._send_callback:
            await self._send_callback(message.to_json())
    
    def touch(self):
        """Atualiza última atividade."""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "subscribedChannels": list(self.subscribed_channels),
            "connectedAt": self.connected_at.isoformat(),
            "lastActivity": self.last_activity.isoformat(),
            "isAuthenticated": self.is_authenticated,
        }


class WebSocketManager:
    """
    Gerenciador de conexões WebSocket.
    
    Gerencia conexões, autenticação e roteamento de mensagens.
    """
    
    def __init__(
        self,
        ping_interval: int = 30,
        ping_timeout: int = 10,
        max_connections_per_user: int = 5,
    ):
        self._connections: Dict[str, WebSocketConnection] = {}
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._channel_subscribers: Dict[str, Set[str]] = {}  # channel -> connection_ids
        
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._max_connections_per_user = max_connections_per_user
        
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        self._auth_handler: Optional[Callable] = None
        
        self._running = False
        self._ping_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Inicia o gerenciador."""
        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Para o gerenciador."""
        self._running = False
        if self._ping_task:
            self._ping_task.cancel()
        
        # Fechar todas conexões
        for conn_id in list(self._connections.keys()):
            await self.disconnect(conn_id)
        
        logger.info("WebSocket manager stopped")
    
    async def connect(
        self,
        connection_id: str,
        send_callback: Callable,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> WebSocketConnection:
        """Registra nova conexão."""
        # Verificar limite de conexões por usuário
        if user_id:
            user_conns = self._user_connections.get(user_id, set())
            if len(user_conns) >= self._max_connections_per_user:
                # Remover conexão mais antiga
                oldest_id = next(iter(user_conns))
                await self.disconnect(oldest_id)
        
        conn = WebSocketConnection(
            id=connection_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        conn._send_callback = send_callback
        
        self._connections[connection_id] = conn
        
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id}")
        return conn
    
    async def disconnect(self, connection_id: str):
        """Remove conexão."""
        conn = self._connections.pop(connection_id, None)
        if not conn:
            return
        
        # Remover de user_connections
        if conn.user_id and conn.user_id in self._user_connections:
            self._user_connections[conn.user_id].discard(connection_id)
            if not self._user_connections[conn.user_id]:
                del self._user_connections[conn.user_id]
        
        # Remover de todos os canais
        for channel in conn.subscribed_channels:
            if channel in self._channel_subscribers:
                self._channel_subscribers[channel].discard(connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def handle_message(self, connection_id: str, raw_message: str):
        """Processa mensagem recebida."""
        conn = self._connections.get(connection_id)
        if not conn:
            return
        
        conn.touch()
        
        try:
            message = WebSocketMessage.from_json(raw_message)
        except Exception as e:
            await self._send_error(conn, f"Invalid message format: {e}")
            return
        
        # Processar por tipo
        if message.type == MessageType.AUTH:
            await self._handle_auth(conn, message)
        elif message.type == MessageType.SUBSCRIBE:
            await self._handle_subscribe(conn, message)
        elif message.type == MessageType.UNSUBSCRIBE:
            await self._handle_unsubscribe(conn, message)
        elif message.type == MessageType.PING:
            await conn.send(WebSocketMessage(type=MessageType.PONG))
        else:
            # Chamar handlers registrados
            handlers = self._message_handlers.get(message.type, [])
            for handler in handlers:
                try:
                    await handler(conn, message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
    
    async def _handle_auth(self, conn: WebSocketConnection, message: WebSocketMessage):
        """Processa autenticação."""
        if not self._auth_handler:
            conn.is_authenticated = True
            await conn.send(WebSocketMessage(type=MessageType.AUTH_SUCCESS))
            return
        
        try:
            user_id = await self._auth_handler(message.data)
            if user_id:
                conn.user_id = user_id
                conn.is_authenticated = True
                
                # Adicionar ao mapeamento de usuário
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(conn.id)
                
                await conn.send(WebSocketMessage(
                    type=MessageType.AUTH_SUCCESS,
                    data={"userId": user_id}
                ))
            else:
                await conn.send(WebSocketMessage(
                    type=MessageType.AUTH_FAILURE,
                    data={"error": "Authentication failed"}
                ))
        except Exception as e:
            await conn.send(WebSocketMessage(
                type=MessageType.AUTH_FAILURE,
                data={"error": str(e)}
            ))
    
    async def _handle_subscribe(self, conn: WebSocketConnection, message: WebSocketMessage):
        """Processa inscrição em canal."""
        channel = message.channel
        if not channel:
            await self._send_error(conn, "Channel required for subscription")
            return
        
        conn.subscribe(channel)
        
        if channel not in self._channel_subscribers:
            self._channel_subscribers[channel] = set()
        self._channel_subscribers[channel].add(conn.id)
        
        logger.debug(f"Connection {conn.id} subscribed to {channel}")
    
    async def _handle_unsubscribe(self, conn: WebSocketConnection, message: WebSocketMessage):
        """Processa cancelamento de inscrição."""
        channel = message.channel
        if not channel:
            return
        
        conn.unsubscribe(channel)
        
        if channel in self._channel_subscribers:
            self._channel_subscribers[channel].discard(conn.id)
    
    async def _send_error(self, conn: WebSocketConnection, error: str):
        """Envia mensagem de erro."""
        await conn.send(WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error}
        ))
    
    async def broadcast(self, channel: str, data: Any):
        """Envia dados para todos inscritos em um canal."""
        subscriber_ids = self._channel_subscribers.get(channel, set())
        
        message = WebSocketMessage(
            type=MessageType.DATA,
            channel=channel,
            data=data,
        )
        
        for conn_id in subscriber_ids:
            conn = self._connections.get(conn_id)
            if conn:
                try:
                    await conn.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {conn_id}: {e}")
    
    async def send_to_user(self, user_id: str, data: Any, channel: Optional[str] = None):
        """Envia dados para todas conexões de um usuário."""
        conn_ids = self._user_connections.get(user_id, set())
        
        message = WebSocketMessage(
            type=MessageType.DATA,
            channel=channel,
            data=data,
        )
        
        for conn_id in conn_ids:
            conn = self._connections.get(conn_id)
            if conn:
                try:
                    await conn.send(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
    
    async def _ping_loop(self):
        """Loop de ping para manter conexões ativas."""
        while self._running:
            try:
                await asyncio.sleep(self._ping_interval)
                
                # Enviar ping para todas conexões
                for conn in self._connections.values():
                    try:
                        await conn.send(WebSocketMessage(type=MessageType.PING))
                    except Exception:
                        pass
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
    
    def set_auth_handler(self, handler: Callable):
        """Define handler de autenticação."""
        self._auth_handler = handler
    
    def on_message(self, message_type: MessageType, handler: Callable):
        """Registra handler para tipo de mensagem."""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
    
    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Obtém conexão por ID."""
        return self._connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Obtém conexões de um usuário."""
        conn_ids = self._user_connections.get(user_id, set())
        return [
            self._connections[cid]
            for cid in conn_ids
            if cid in self._connections
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas do gerenciador."""
        return {
            "totalConnections": len(self._connections),
            "uniqueUsers": len(self._user_connections),
            "totalChannels": len(self._channel_subscribers),
            "authenticatedConnections": len([
                c for c in self._connections.values()
                if c.is_authenticated
            ]),
        }


# Singleton
_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Obtém gerenciador de WebSocket."""
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager

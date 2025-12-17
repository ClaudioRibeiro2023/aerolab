"""
Agno Chat Module v2 - Sistema de Chat Avançado

Features:
- Streaming real-time (SSE/WebSocket)
- Persistência de conversas
- Branching e versionamento
- Multi-modal (texto, imagem, voz, arquivos)
- Workbench (Artifacts/Canvas)
- Multi-agent collaboration
- Personalization e memória
- Enterprise compliance

Uso:
```python
from src.chat import ChatService, Conversation, Message

# Criar serviço
chat = ChatService()

# Iniciar conversa
conversation = await chat.create_conversation(
    agent_id="assistant",
    user_id="user_123"
)

# Enviar mensagem com streaming
async for chunk in chat.send_message_stream(
    conversation_id=conversation.id,
    content="Hello!",
    agent_id="assistant"
):
    print(chunk.delta, end="")

# Obter histórico
messages = await chat.get_messages(conversation.id)
```
"""

__all__ = [
    # Core
    "Conversation",
    "Message",
    "MessageRole",
    "MessageType",
    "ConversationStatus",
    # Session
    "Session",
    "SessionManager",
    # Streaming
    "StreamChunk",
    "StreamEvent",
    "ChatStreamer",
    # Service
    "ChatService",
    # Context
    "ContextBuilder",
    "ChatContext",
]

# Core
from .core.conversation import Conversation, ConversationStatus
from .core.message import Message, MessageRole, MessageType
from .core.session import Session, SessionManager
from .core.context import ContextBuilder, ChatContext

# Streaming
from .streaming.events import StreamChunk, StreamEvent
from .streaming.streamer import ChatStreamer

# Service
from .service import ChatService

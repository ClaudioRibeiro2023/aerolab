"""
Chat Core - Entidades fundamentais do sistema de chat.
"""

from .conversation import Conversation, ConversationStatus
from .message import Message, MessageRole, MessageType
from .session import Session, SessionManager
from .context import ContextBuilder, ChatContext

__all__ = [
    "Conversation",
    "ConversationStatus",
    "Message",
    "MessageRole", 
    "MessageType",
    "Session",
    "SessionManager",
    "ContextBuilder",
    "ChatContext",
]

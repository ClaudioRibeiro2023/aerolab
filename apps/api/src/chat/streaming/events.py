"""
Streaming Events - Tipos de eventos para streaming.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class StreamEventType(str, Enum):
    """Tipos de eventos de streaming."""
    # Mensagem
    MESSAGE_START = "message_start"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_DONE = "message_done"
    MESSAGE_ERROR = "message_error"
    
    # Reasoning/Thinking
    THINKING_START = "thinking_start"
    THINKING_DELTA = "thinking_delta"
    THINKING_DONE = "thinking_done"
    
    # Tool calls
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_ARGS = "tool_call_args"
    TOOL_CALL_DONE = "tool_call_done"
    TOOL_RESULT = "tool_result"
    
    # Artifacts
    ARTIFACT_START = "artifact_start"
    ARTIFACT_DELTA = "artifact_delta"
    ARTIFACT_DONE = "artifact_done"
    
    # Citations
    CITATION_ADDED = "citation_added"
    
    # Status
    TYPING = "typing"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"
    
    # Presence
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_TYPING = "user_typing"


@dataclass
class StreamChunk:
    """
    Chunk de streaming de conteúdo.
    """
    content: str = ""
    delta: str = ""
    finish_reason: Optional[str] = None
    
    # Metadata
    message_id: Optional[str] = None
    model: Optional[str] = None
    
    # Tokens (se disponível)
    tokens: int = 0
    
    def __str__(self) -> str:
        return self.delta or self.content
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "delta": self.delta,
            "finish_reason": self.finish_reason,
            "message_id": self.message_id,
            "model": self.model,
            "tokens": self.tokens
        }


@dataclass
class StreamEvent:
    """
    Evento de streaming completo.
    
    Pode representar diferentes tipos de eventos durante
    o streaming de uma resposta.
    """
    type: StreamEventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Identificadores
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # Para deltas de texto
    content: str = ""
    delta: str = ""
    
    # Para tool calls
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict] = None
    tool_result: Optional[str] = None
    
    # Para artifacts
    artifact_id: Optional[str] = None
    artifact_type: Optional[str] = None
    artifact_content: str = ""
    
    # Para citations
    citation: Optional[Dict] = None
    
    # Para erros
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Finish reason
    finish_reason: Optional[str] = None
    
    def to_sse(self) -> str:
        """Formata para Server-Sent Events."""
        data = self.to_dict()
        return f"event: {self.type.value}\ndata: {json.dumps(data)}\n\n"
    
    def to_dict(self) -> Dict:
        result = {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "conversation_id": self.conversation_id
        }
        
        # Adicionar campos específicos por tipo
        if self.type in (StreamEventType.MESSAGE_DELTA, StreamEventType.MESSAGE_START, StreamEventType.MESSAGE_DONE):
            result["content"] = self.content
            result["delta"] = self.delta
            if self.finish_reason:
                result["finish_reason"] = self.finish_reason
        
        elif self.type in (StreamEventType.THINKING_START, StreamEventType.THINKING_DELTA, StreamEventType.THINKING_DONE):
            result["content"] = self.content
            result["delta"] = self.delta
        
        elif self.type in (StreamEventType.TOOL_CALL_START, StreamEventType.TOOL_CALL_ARGS, StreamEventType.TOOL_CALL_DONE):
            result["tool_call_id"] = self.tool_call_id
            result["tool_name"] = self.tool_name
            result["arguments"] = self.tool_arguments
        
        elif self.type == StreamEventType.TOOL_RESULT:
            result["tool_call_id"] = self.tool_call_id
            result["result"] = self.tool_result
        
        elif self.type in (StreamEventType.ARTIFACT_START, StreamEventType.ARTIFACT_DELTA, StreamEventType.ARTIFACT_DONE):
            result["artifact_id"] = self.artifact_id
            result["artifact_type"] = self.artifact_type
            result["content"] = self.artifact_content
        
        elif self.type == StreamEventType.CITATION_ADDED:
            result["citation"] = self.citation
        
        elif self.type == StreamEventType.ERROR:
            result["error"] = self.error
            result["error_code"] = self.error_code
        
        # Adicionar data extra
        result["data"] = self.data
        
        return result
    
    @classmethod
    def message_start(cls, message_id: str, conversation_id: str) -> "StreamEvent":
        """Cria evento de início de mensagem."""
        return cls(
            type=StreamEventType.MESSAGE_START,
            message_id=message_id,
            conversation_id=conversation_id
        )
    
    @classmethod
    def message_delta(cls, delta: str, content: str, message_id: str) -> "StreamEvent":
        """Cria evento de delta de mensagem."""
        return cls(
            type=StreamEventType.MESSAGE_DELTA,
            delta=delta,
            content=content,
            message_id=message_id
        )
    
    @classmethod
    def message_done(
        cls, 
        content: str, 
        message_id: str,
        finish_reason: str = "stop"
    ) -> "StreamEvent":
        """Cria evento de fim de mensagem."""
        return cls(
            type=StreamEventType.MESSAGE_DONE,
            content=content,
            message_id=message_id,
            finish_reason=finish_reason
        )
    
    @classmethod
    def message_error(cls, error: str, message_id: str, code: str = "error") -> "StreamEvent":
        """Cria evento de erro."""
        return cls(
            type=StreamEventType.MESSAGE_ERROR,
            error=error,
            error_code=code,
            message_id=message_id
        )
    
    @classmethod
    def thinking_start(cls, message_id: str) -> "StreamEvent":
        """Cria evento de início de thinking."""
        return cls(
            type=StreamEventType.THINKING_START,
            message_id=message_id
        )
    
    @classmethod
    def thinking_delta(cls, delta: str, content: str, message_id: str) -> "StreamEvent":
        """Cria evento de delta de thinking."""
        return cls(
            type=StreamEventType.THINKING_DELTA,
            delta=delta,
            content=content,
            message_id=message_id
        )
    
    @classmethod
    def tool_call_start(cls, tool_call_id: str, tool_name: str, message_id: str) -> "StreamEvent":
        """Cria evento de início de tool call."""
        return cls(
            type=StreamEventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            message_id=message_id
        )
    
    @classmethod
    def tool_result(cls, tool_call_id: str, result: str, message_id: str) -> "StreamEvent":
        """Cria evento de resultado de tool."""
        return cls(
            type=StreamEventType.TOOL_RESULT,
            tool_call_id=tool_call_id,
            tool_result=result,
            message_id=message_id
        )
    
    @classmethod
    def artifact_delta(
        cls, 
        artifact_id: str, 
        artifact_type: str,
        content: str,
        message_id: str
    ) -> "StreamEvent":
        """Cria evento de delta de artifact."""
        return cls(
            type=StreamEventType.ARTIFACT_DELTA,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            artifact_content=content,
            message_id=message_id
        )
    
    @classmethod
    def citation_added(cls, citation: Dict, message_id: str) -> "StreamEvent":
        """Cria evento de citação adicionada."""
        return cls(
            type=StreamEventType.CITATION_ADDED,
            citation=citation,
            message_id=message_id
        )
    
    @classmethod
    def user_typing(cls, user_id: str, conversation_id: str) -> "StreamEvent":
        """Cria evento de usuário digitando."""
        return cls(
            type=StreamEventType.USER_TYPING,
            conversation_id=conversation_id,
            data={"user_id": user_id}
        )

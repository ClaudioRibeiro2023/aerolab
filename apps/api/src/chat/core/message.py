"""
Message - Representação de mensagens no chat.

Suporta múltiplos tipos de conteúdo:
- Texto/Markdown
- Código
- Imagens
- Áudio
- Arquivos
- Artifacts
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Papel do autor da mensagem."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(str, Enum):
    """Tipo de conteúdo da mensagem."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    ARTIFACT = "artifact"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class MessageStatus(str, Enum):
    """Status da mensagem."""
    PENDING = "pending"
    SENDING = "sending"
    STREAMING = "streaming"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class Attachment:
    """Anexo de mensagem."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    url: Optional[str] = None
    content: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "url": self.url,
            "metadata": self.metadata
        }


@dataclass
class Citation:
    """Citação/fonte referenciada."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    url: Optional[str] = None
    snippet: str = ""
    source_type: str = "web"  # web, document, rag
    relevance_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_type": self.source_type,
            "relevance_score": self.relevance_score
        }


@dataclass
class ToolCall:
    """Chamada de ferramenta."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    status: str = "pending"  # pending, running, success, error
    duration_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "status": self.status,
            "duration_ms": self.duration_ms
        }


@dataclass
class ReasoningStep:
    """Passo de raciocínio (thinking mode)."""
    step_number: int = 0
    content: str = ""
    step_type: str = "thinking"  # thinking, planning, evaluating, concluding
    duration_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "step_number": self.step_number,
            "content": self.content,
            "step_type": self.step_type,
            "duration_ms": self.duration_ms
        }


@dataclass
class Reaction:
    """Reação a uma mensagem."""
    user_id: str = ""
    emoji: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """
    Mensagem de chat.
    
    Suporta conteúdo rico incluindo:
    - Texto formatado (Markdown)
    - Código com syntax highlighting
    - Imagens e arquivos
    - Citações e fontes
    - Tool calls
    - Raciocínio (thinking mode)
    - Artifacts (canvas items)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    branch_id: str = "main"
    parent_id: Optional[str] = None  # Para threading
    
    # Autor
    role: MessageRole = MessageRole.USER
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Conteúdo
    content: str = ""
    content_type: MessageType = MessageType.TEXT
    
    # Rich content
    attachments: List[Attachment] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    artifact_ids: List[str] = field(default_factory=list)
    
    # Metadata
    model: Optional[str] = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latency_ms: float = 0
    
    # Status
    status: MessageStatus = MessageStatus.PENDING
    error: Optional[str] = None
    
    # Interações
    reactions: List[Reaction] = field(default_factory=list)
    feedback: Optional[str] = None  # good, bad
    regenerated_from: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    
    # Metadata extra
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        return self.tokens_prompt + self.tokens_completion
    
    @property
    def is_user(self) -> bool:
        return self.role == MessageRole.USER
    
    @property
    def is_assistant(self) -> bool:
        return self.role == MessageRole.ASSISTANT
    
    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0
    
    @property
    def has_citations(self) -> bool:
        return len(self.citations) > 0
    
    @property
    def has_reasoning(self) -> bool:
        return len(self.reasoning_steps) > 0
    
    def add_attachment(self, attachment: Attachment) -> None:
        """Adiciona um anexo."""
        self.attachments.append(attachment)
        self.updated_at = datetime.now()
    
    def add_citation(self, citation: Citation) -> None:
        """Adiciona uma citação."""
        self.citations.append(citation)
        self.updated_at = datetime.now()
    
    def add_tool_call(self, tool_call: ToolCall) -> None:
        """Adiciona uma chamada de ferramenta."""
        self.tool_calls.append(tool_call)
        self.updated_at = datetime.now()
    
    def add_reasoning_step(self, step: ReasoningStep) -> None:
        """Adiciona um passo de raciocínio."""
        self.reasoning_steps.append(step)
        self.updated_at = datetime.now()
    
    def add_reaction(self, user_id: str, emoji: str) -> None:
        """Adiciona uma reação."""
        # Remover reação anterior do mesmo usuário
        self.reactions = [r for r in self.reactions if r.user_id != user_id]
        self.reactions.append(Reaction(user_id=user_id, emoji=emoji))
        self.updated_at = datetime.now()
    
    def set_feedback(self, feedback: str) -> None:
        """Define feedback (good/bad)."""
        if feedback in ("good", "bad"):
            self.feedback = feedback
            self.updated_at = datetime.now()
    
    def mark_as_streaming(self) -> None:
        """Marca como streaming."""
        self.status = MessageStatus.STREAMING
        self.updated_at = datetime.now()
    
    def mark_as_done(self) -> None:
        """Marca como concluída."""
        self.status = MessageStatus.DONE
        self.updated_at = datetime.now()
    
    def mark_as_error(self, error: str) -> None:
        """Marca como erro."""
        self.status = MessageStatus.ERROR
        self.error = error
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "branch_id": self.branch_id,
            "parent_id": self.parent_id,
            "role": self.role.value,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "content": self.content,
            "content_type": self.content_type.value,
            "attachments": [a.to_dict() for a in self.attachments],
            "citations": [c.to_dict() for c in self.citations],
            "tool_calls": [t.to_dict() for t in self.tool_calls],
            "reasoning_steps": [r.to_dict() for r in self.reasoning_steps],
            "artifact_ids": self.artifact_ids,
            "model": self.model,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "latency_ms": self.latency_ms,
            "status": self.status.value,
            "error": self.error,
            "feedback": self.feedback,
            "regenerated_from": self.regenerated_from,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "metadata": self.metadata
        }
    
    def to_api_format(self) -> Dict:
        """Converte para formato de API (OpenAI-compatible)."""
        msg = {
            "role": self.role.value,
            "content": self.content
        }
        
        if self.role == MessageRole.TOOL:
            msg["tool_call_id"] = self.metadata.get("tool_call_id", "")
        
        return msg
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """Cria a partir de dicionário."""
        msg = cls(
            id=data.get("id", str(uuid.uuid4())),
            conversation_id=data.get("conversation_id", ""),
            branch_id=data.get("branch_id", "main"),
            parent_id=data.get("parent_id"),
            role=MessageRole(data.get("role", "user")),
            agent_id=data.get("agent_id"),
            user_id=data.get("user_id"),
            content=data.get("content", ""),
            content_type=MessageType(data.get("content_type", "text")),
            model=data.get("model"),
            tokens_prompt=data.get("tokens_prompt", 0),
            tokens_completion=data.get("tokens_completion", 0),
            latency_ms=data.get("latency_ms", 0),
            status=MessageStatus(data.get("status", "done")),
            error=data.get("error"),
            feedback=data.get("feedback"),
            regenerated_from=data.get("regenerated_from"),
            metadata=data.get("metadata", {})
        )
        
        # Parse timestamps
        if "created_at" in data:
            msg.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            msg.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("edited_at"):
            msg.edited_at = datetime.fromisoformat(data["edited_at"])
        
        return msg
    
    @classmethod
    def user(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem de usuário."""
        return cls(
            role=MessageRole.USER,
            content=content,
            status=MessageStatus.DONE,
            **kwargs
        )
    
    @classmethod
    def assistant(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem de assistente."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=content,
            status=MessageStatus.DONE,
            **kwargs
        )
    
    @classmethod
    def system(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem de sistema."""
        return cls(
            role=MessageRole.SYSTEM,
            content=content,
            status=MessageStatus.DONE,
            **kwargs
        )

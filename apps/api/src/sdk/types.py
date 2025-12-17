"""
Agno SDK - Tipos e Estruturas de Dados

Define todas as estruturas de dados utilizadas pelo SDK.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union, Literal
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Papéis de mensagens."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentState(str, Enum):
    """Estado do agente."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class ResponseStatus(str, Enum):
    """Status da resposta."""
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Message:
    """
    Representa uma mensagem na conversa.
    
    Attributes:
        role: Papel da mensagem (user, assistant, system, tool)
        content: Conteúdo textual da mensagem
        name: Nome opcional (para tool messages)
        tool_calls: Chamadas de ferramentas
        tool_call_id: ID da chamada de ferramenta (para respostas)
        metadata: Metadados adicionais
    """
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Converte para dicionário compatível com APIs de LLM."""
        msg = {
            "role": self.role.value,
            "content": self.content
        }
        
        if self.name:
            msg["name"] = self.name
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        
        return msg
    
    @classmethod
    def user(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem do usuário."""
        return cls(role=MessageRole.USER, content=content, **kwargs)
    
    @classmethod
    def assistant(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem do assistente."""
        return cls(role=MessageRole.ASSISTANT, content=content, **kwargs)
    
    @classmethod
    def system(cls, content: str, **kwargs) -> "Message":
        """Cria mensagem de sistema."""
        return cls(role=MessageRole.SYSTEM, content=content, **kwargs)
    
    @classmethod
    def tool(cls, content: str, tool_call_id: str, name: str, **kwargs) -> "Message":
        """Cria mensagem de ferramenta."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            **kwargs
        )


@dataclass
class ToolCall:
    """
    Representa uma chamada de ferramenta.
    
    Attributes:
        id: ID único da chamada
        name: Nome da ferramenta
        arguments: Argumentos da chamada
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    arguments: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments
            }
        }


@dataclass
class Usage:
    """
    Uso de tokens.
    
    Attributes:
        prompt_tokens: Tokens no prompt
        completion_tokens: Tokens na resposta
        total_tokens: Total de tokens
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __add__(self, other: "Usage") -> "Usage":
        """Soma dois Usage."""
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens
        )


@dataclass
class Response:
    """
    Resposta de uma execução de agente.
    
    Attributes:
        content: Conteúdo textual da resposta
        messages: Histórico de mensagens
        tool_calls: Chamadas de ferramentas feitas
        usage: Uso de tokens
        status: Status da resposta
        error: Mensagem de erro se houver
        metadata: Metadados adicionais
    """
    content: str = ""
    messages: list[Message] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    status: ResponseStatus = ResponseStatus.SUCCESS
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "content": self.content,
            "status": self.status.value,
            "error": self.error,
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens
            },
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


@dataclass
class StreamChunk:
    """
    Chunk de streaming.
    
    Attributes:
        content: Conteúdo do chunk
        delta: Delta de conteúdo (para streaming incremental)
        tool_calls: Chamadas de ferramentas parciais
        finish_reason: Razão de término
    """
    content: str = ""
    delta: str = ""
    tool_calls: Optional[list[dict]] = None
    finish_reason: Optional[str] = None
    
    def __str__(self) -> str:
        return self.delta or self.content


@dataclass
class Context:
    """
    Contexto de execução.
    
    Permite passar informações adicionais para o agente.
    
    Attributes:
        user_id: ID do usuário
        session_id: ID da sessão
        project_id: ID do projeto
        variables: Variáveis customizadas
        metadata: Metadados adicionais
    """
    user_id: Optional[str] = None
    session_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[int] = None
    variables: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    
    # Memórias carregadas
    memories: list[dict] = field(default_factory=list)
    
    # Documentos de contexto
    documents: list[dict] = field(default_factory=list)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém variável do contexto."""
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Define variável no contexto."""
        self.variables[key] = value
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "variables": self.variables,
            "metadata": self.metadata
        }


@dataclass
class AgentRun:
    """
    Representa uma execução de agente.
    
    Attributes:
        id: ID único da execução
        agent_name: Nome do agente
        input: Input do usuário
        output: Output gerado
        context: Contexto da execução
        status: Status atual
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    input: str = ""
    output: str = ""
    context: Context = field(default_factory=Context)
    status: AgentState = AgentState.IDLE
    
    # Histórico
    messages: list[Message] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    
    # Métricas
    usage: Usage = field(default_factory=Usage)
    duration_ms: float = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Erro
    error: Optional[str] = None


@dataclass
class TeamRun:
    """
    Representa uma execução de equipe multi-agent.
    
    Attributes:
        id: ID único da execução
        team_name: Nome da equipe
        agent_runs: Execuções dos agentes individuais
        workflow: Tipo de workflow usado
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str = ""
    input: str = ""
    output: str = ""
    agent_runs: list[AgentRun] = field(default_factory=list)
    workflow: str = "sequential"
    
    # Métricas agregadas
    total_usage: Usage = field(default_factory=Usage)
    total_duration_ms: float = 0
    
    # Status
    status: AgentState = AgentState.IDLE
    error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


# Type aliases
MessageLike = Union[str, Message, dict]
ToolLike = Union["Tool", callable, dict]

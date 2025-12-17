"""
Memory v2 - Tipos e Estruturas de Dados

Define todas as estruturas de dados utilizadas pelo sistema de memória.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum
import uuid


class MemoryType(str, Enum):
    """Tipos de memória."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"


class MemoryPriority(str, Enum):
    """Prioridade de memória."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryStatus(str, Enum):
    """Status da memória."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_CONSOLIDATION = "pending_consolidation"
    CONSOLIDATED = "consolidated"
    EXPIRED = "expired"


@dataclass
class Memory:
    """
    Representa uma unidade de memória.
    
    Pode ser armazenada em qualquer um dos três níveis:
    - Short-term: contexto temporário
    - Long-term: conhecimento persistente
    - Episodic: registro de eventos
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Conteúdo
    content: str = ""
    summary: Optional[str] = None
    
    # Metadados
    memory_type: MemoryType = MemoryType.SHORT_TERM
    priority: MemoryPriority = MemoryPriority.MEDIUM
    status: MemoryStatus = MemoryStatus.ACTIVE
    
    # Contexto
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    
    # Embedding
    embedding: Optional[list[float]] = None
    
    # Relevância
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Tags e metadados
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    # Relacionamentos
    parent_id: Optional[str] = None
    related_ids: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "content": self.content,
            "summary": self.summary,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "related_ids": self.related_ids
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        """Cria Memory a partir de dicionário."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            summary=data.get("summary"),
            memory_type=MemoryType(data.get("memory_type", "short_term")),
            priority=MemoryPriority(data.get("priority", "medium")),
            status=MemoryStatus(data.get("status", "active")),
            agent_id=data.get("agent_id"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            project_id=data.get("project_id"),
            importance_score=data.get("importance_score", 0.5),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            parent_id=data.get("parent_id"),
            related_ids=data.get("related_ids", [])
        )
    
    def is_expired(self) -> bool:
        """Verifica se a memória expirou."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def calculate_decay(self, decay_rate: float = 0.1) -> float:
        """
        Calcula o fator de decay temporal.
        
        Memórias mais antigas têm menor relevância.
        """
        if self.last_accessed:
            hours_since_access = (datetime.now() - self.last_accessed).total_seconds() / 3600
        else:
            hours_since_access = (datetime.now() - self.created_at).total_seconds() / 3600
        
        import math
        decay = math.exp(-decay_rate * hours_since_access)
        return max(0.1, decay)  # Mínimo de 10%
    
    def effective_score(self, decay_rate: float = 0.1) -> float:
        """Calcula score efetivo considerando decay."""
        return self.importance_score * self.calculate_decay(decay_rate)


@dataclass
class MemoryQuery:
    """Query para busca de memórias."""
    query: str = ""
    
    # Filtros
    memory_types: list[MemoryType] = field(default_factory=list)
    priorities: list[MemoryPriority] = field(default_factory=list)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    
    # Período
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Paginação
    limit: int = 10
    offset: int = 0
    
    # Ordenação
    order_by: str = "relevance"  # relevance, created_at, importance_score
    order_desc: bool = True


@dataclass
class MemorySearchResult:
    """Resultado de busca de memória."""
    memory: Memory
    score: float
    match_type: str  # semantic, keyword, exact
    highlights: list[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """
    Contexto de uma conversa (sessão).
    
    Mantém o estado da conversa atual incluindo
    histórico de mensagens e memórias relevantes.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    user_id: Optional[str] = None
    
    # Histórico
    messages: list[dict] = field(default_factory=list)
    
    # Memórias carregadas
    active_memories: list[Memory] = field(default_factory=list)
    
    # Estado
    variables: dict = field(default_factory=dict)
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Métricas
    message_count: int = 0
    token_count: int = 0
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """Adiciona mensagem ao histórico."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self.message_count += 1
        self.token_count += len(content) // 4  # Estimativa
        self.last_activity = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> list[dict]:
        """Retorna mensagens recentes."""
        return self.messages[-limit:]
    
    def to_prompt_messages(self, limit: int = 20) -> list[dict]:
        """Converte para formato de mensagens de prompt."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.messages[-limit:]
        ]
    
    def get_context_summary(self) -> str:
        """Gera resumo do contexto."""
        memory_summary = "\n".join([
            f"- {m.summary or m.content[:100]}"
            for m in self.active_memories[:5]
        ])
        
        return f"""Session: {self.session_id}
Messages: {self.message_count}
Active Memories:
{memory_summary}
Variables: {list(self.variables.keys())}"""


@dataclass
class Episode:
    """
    Representa um episódio (execução completa de uma tarefa).
    
    Usado para aprendizado e replay de experiências.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Contexto
    agent_id: str = ""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    
    # Tarefa
    task_description: str = ""
    task_type: Optional[str] = None
    
    # Execução
    steps: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    
    # Resultado
    outcome: Optional[str] = None  # success, failure, partial
    result: Optional[str] = None
    error: Optional[str] = None
    
    # Métricas
    duration_ms: float = 0
    token_count: int = 0
    tool_call_count: int = 0
    
    # Avaliação
    user_feedback: Optional[str] = None
    rating: Optional[float] = None
    lessons_learned: list[str] = field(default_factory=list)
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def add_step(self, action: str, result: Any, reasoning: Optional[str] = None) -> None:
        """Adiciona um passo ao episódio."""
        self.steps.append({
            "action": action,
            "result": str(result)[:1000],
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tool_call(self, tool_name: str, args: dict, result: Any) -> None:
        """Registra uma chamada de ferramenta."""
        self.tool_calls.append({
            "tool": tool_name,
            "args": args,
            "result": str(result)[:500],
            "timestamp": datetime.now().isoformat()
        })
        self.tool_call_count += 1
    
    def add_decision(self, decision: str, options: list[str], reasoning: str) -> None:
        """Registra uma decisão tomada."""
        self.decisions.append({
            "decision": decision,
            "options": options,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })
    
    def complete(self, outcome: str, result: Optional[str] = None, error: Optional[str] = None) -> None:
        """Marca o episódio como completo."""
        self.outcome = outcome
        self.result = result
        self.error = error
        self.completed_at = datetime.now()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "task_description": self.task_description,
            "task_type": self.task_type,
            "steps": self.steps,
            "tool_calls": self.tool_calls,
            "decisions": self.decisions,
            "outcome": self.outcome,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "token_count": self.token_count,
            "tool_call_count": self.tool_call_count,
            "user_feedback": self.user_feedback,
            "rating": self.rating,
            "lessons_learned": self.lessons_learned,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        """Cria Episode a partir de dicionário."""
        episode = cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_id=data.get("agent_id", ""),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            project_id=data.get("project_id"),
            task_description=data.get("task_description", ""),
            task_type=data.get("task_type"),
            steps=data.get("steps", []),
            tool_calls=data.get("tool_calls", []),
            decisions=data.get("decisions", []),
            outcome=data.get("outcome"),
            result=data.get("result"),
            error=data.get("error"),
            duration_ms=data.get("duration_ms", 0),
            token_count=data.get("token_count", 0),
            tool_call_count=data.get("tool_call_count", 0),
            user_feedback=data.get("user_feedback"),
            rating=data.get("rating"),
            lessons_learned=data.get("lessons_learned", []),
            metadata=data.get("metadata", {})
        )
        
        if data.get("started_at"):
            episode.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            episode.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return episode

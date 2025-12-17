"""
Conversation - Representa uma conversa completa.

Features:
- Múltiplos branches (árvore de versões)
- Múltiplos agentes
- Projects/Workspaces
- Configurações personalizadas
- Colaboração em tempo real
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

from .message import Message


class ConversationStatus(str, Enum):
    """Status da conversa."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ReasoningMode(str, Enum):
    """Modo de raciocínio."""
    OFF = "off"
    BASIC = "basic"
    EXTENDED = "extended"


@dataclass
class Branch:
    """Branch de conversa (para edit/regenerate)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "main"
    parent_id: Optional[str] = None
    parent_message_id: Optional[str] = None  # Ponto de bifurcação
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "parent_message_id": self.parent_message_id,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Collaborator:
    """Colaborador em uma conversa."""
    user_id: str = ""
    role: str = "viewer"  # owner, editor, viewer
    joined_at: datetime = field(default_factory=datetime.now)
    cursor_position: Optional[int] = None  # Para real-time
    is_online: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
            "is_online": self.is_online
        }


@dataclass
class ConversationSettings:
    """Configurações da conversa."""
    # Modelo
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Instruções
    custom_instructions: Optional[str] = None
    system_prompt: Optional[str] = None
    
    # Features
    reasoning_mode: ReasoningMode = ReasoningMode.OFF
    web_search_enabled: bool = False
    code_execution_enabled: bool = False
    voice_mode_enabled: bool = False
    
    # Contexto
    max_context_messages: int = 50
    include_system_prompt: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "custom_instructions": self.custom_instructions,
            "system_prompt": self.system_prompt,
            "reasoning_mode": self.reasoning_mode.value,
            "web_search_enabled": self.web_search_enabled,
            "code_execution_enabled": self.code_execution_enabled,
            "voice_mode_enabled": self.voice_mode_enabled,
            "max_context_messages": self.max_context_messages,
            "include_system_prompt": self.include_system_prompt
        }


@dataclass
class Conversation:
    """
    Conversa completa.
    
    Suporta:
    - Múltiplos branches (árvore de versões)
    - Múltiplos agentes
    - Colaboração em tempo real
    - Configurações personalizadas
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Organização
    project_id: Optional[str] = None
    title: str = "Nova Conversa"
    auto_title: bool = True
    
    # Owner
    user_id: str = ""
    organization_id: Optional[str] = None
    
    # Status
    status: ConversationStatus = ConversationStatus.ACTIVE
    pinned: bool = False
    
    # Branches
    branches: List[Branch] = field(default_factory=lambda: [Branch(name="main")])
    active_branch_id: str = ""
    
    # Mensagens (carregadas sob demanda)
    messages: List[Message] = field(default_factory=list)
    message_count: int = 0
    
    # Agentes
    agent_ids: List[str] = field(default_factory=list)
    primary_agent_id: Optional[str] = None
    
    # Colaboradores
    collaborators: List[Collaborator] = field(default_factory=list)
    
    # Settings
    settings: ConversationSettings = field(default_factory=ConversationSettings)
    
    # Métricas
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.active_branch_id and self.branches:
            self.active_branch_id = self.branches[0].id
    
    @property
    def is_active(self) -> bool:
        return self.status == ConversationStatus.ACTIVE
    
    @property
    def is_archived(self) -> bool:
        return self.status == ConversationStatus.ARCHIVED
    
    @property
    def active_branch(self) -> Optional[Branch]:
        for branch in self.branches:
            if branch.id == self.active_branch_id:
                return branch
        return self.branches[0] if self.branches else None
    
    def add_message(self, message: Message) -> None:
        """Adiciona uma mensagem."""
        message.conversation_id = self.id
        message.branch_id = self.active_branch_id
        self.messages.append(message)
        self.message_count += 1
        self.total_tokens += message.total_tokens
        self.updated_at = datetime.now()
        self.last_message_at = datetime.now()
    
    def get_messages(self, branch_id: Optional[str] = None) -> List[Message]:
        """Retorna mensagens de um branch."""
        branch = branch_id or self.active_branch_id
        return [m for m in self.messages if m.branch_id == branch]
    
    def create_branch(self, name: str, from_message_id: str) -> Branch:
        """Cria um novo branch a partir de uma mensagem."""
        branch = Branch(
            name=name,
            parent_id=self.active_branch_id,
            parent_message_id=from_message_id
        )
        self.branches.append(branch)
        self.updated_at = datetime.now()
        return branch
    
    def switch_branch(self, branch_id: str) -> bool:
        """Muda para outro branch."""
        if any(b.id == branch_id for b in self.branches):
            self.active_branch_id = branch_id
            self.updated_at = datetime.now()
            return True
        return False
    
    def add_agent(self, agent_id: str) -> None:
        """Adiciona um agente à conversa."""
        if agent_id not in self.agent_ids:
            self.agent_ids.append(agent_id)
            if not self.primary_agent_id:
                self.primary_agent_id = agent_id
            self.updated_at = datetime.now()
    
    def add_collaborator(self, user_id: str, role: str = "viewer") -> Collaborator:
        """Adiciona um colaborador."""
        collab = Collaborator(user_id=user_id, role=role)
        self.collaborators.append(collab)
        self.updated_at = datetime.now()
        return collab
    
    def archive(self) -> None:
        """Arquiva a conversa."""
        self.status = ConversationStatus.ARCHIVED
        self.archived_at = datetime.now()
        self.updated_at = datetime.now()
    
    def unarchive(self) -> None:
        """Desarquiva a conversa."""
        self.status = ConversationStatus.ACTIVE
        self.archived_at = None
        self.updated_at = datetime.now()
    
    def update_title(self, title: str) -> None:
        """Atualiza o título."""
        self.title = title
        self.auto_title = False
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "auto_title": self.auto_title,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "status": self.status.value,
            "pinned": self.pinned,
            "branches": [b.to_dict() for b in self.branches],
            "active_branch_id": self.active_branch_id,
            "message_count": self.message_count,
            "agent_ids": self.agent_ids,
            "primary_agent_id": self.primary_agent_id,
            "collaborators": [c.to_dict() for c in self.collaborators],
            "settings": self.settings.to_dict(),
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "metadata": self.metadata,
            "tags": self.tags
        }
    
    def to_list_item(self) -> Dict:
        """Retorna versão resumida para listagem."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "pinned": self.pinned,
            "message_count": self.message_count,
            "primary_agent_id": self.primary_agent_id,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conversation":
        """Cria a partir de dicionário."""
        conv = cls(
            id=data.get("id", str(uuid.uuid4())),
            project_id=data.get("project_id"),
            title=data.get("title", "Nova Conversa"),
            auto_title=data.get("auto_title", True),
            user_id=data.get("user_id", ""),
            organization_id=data.get("organization_id"),
            status=ConversationStatus(data.get("status", "active")),
            pinned=data.get("pinned", False),
            active_branch_id=data.get("active_branch_id", ""),
            message_count=data.get("message_count", 0),
            agent_ids=data.get("agent_ids", []),
            primary_agent_id=data.get("primary_agent_id"),
            total_tokens=data.get("total_tokens", 0),
            estimated_cost_usd=data.get("estimated_cost_usd", 0.0),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )
        
        # Parse branches
        if "branches" in data:
            conv.branches = []
            for b in data["branches"]:
                branch = Branch(
                    id=b.get("id"),
                    name=b.get("name", "main"),
                    parent_id=b.get("parent_id"),
                    parent_message_id=b.get("parent_message_id")
                )
                conv.branches.append(branch)
        
        # Parse timestamps
        if "created_at" in data:
            conv.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            conv.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("last_message_at"):
            conv.last_message_at = datetime.fromisoformat(data["last_message_at"])
        if data.get("archived_at"):
            conv.archived_at = datetime.fromisoformat(data["archived_at"])
        
        return conv

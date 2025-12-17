"""
Sistema de Memória para Agentes.

Implementa diferentes tipos de memória para agentes:
- ShortTermMemory: Contexto da sessão atual
- LongTermMemory: Persistente entre sessões
- EpisodicMemory: Eventos e experiências específicas
- SemanticMemory: Conhecimento indexado (integra com RAG)

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Memory Manager                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Short-Term   │  │ Long-Term    │  │ Episodic     │      │
│  │ Memory       │  │ Memory       │  │ Memory       │      │
│  │              │  │              │  │              │      │
│  │ - Messages   │  │ - Facts      │  │ - Events     │      │
│  │ - Context    │  │ - Preferences│  │ - Outcomes   │      │
│  │ - Session    │  │ - History    │  │ - Lessons    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │ Semantic  │                            │
│                    │ Memory    │                            │
│                    │ (RAG)     │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum
import sqlite3
import threading


class MemoryType(Enum):
    """Tipos de memória."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MessageRole(Enum):
    """Roles de mensagem."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class MemoryItem:
    """Item de memória genérico."""
    id: str
    content: str
    memory_type: MemoryType
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0-1
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


@dataclass
class Message:
    """Mensagem de conversa."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Episode:
    """Episódio de memória episódica."""
    id: str
    description: str
    outcome: str
    lesson: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "outcome": self.outcome,
            "lesson": self.lesson,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance
        }


class BaseMemory(ABC):
    """Interface base para memórias."""
    
    @abstractmethod
    def add(self, item: Any) -> str:
        """Adiciona item à memória."""
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[Any]:
        """Recupera item por ID."""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Any]:
        """Busca itens relevantes."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Limpa a memória."""
        pass


class ShortTermMemory(BaseMemory):
    """
    Memória de curto prazo (sessão).
    
    Armazena mensagens da conversa atual e contexto temporário.
    Perdida ao fim da sessão.
    """
    
    def __init__(self, max_messages: int = 50, max_tokens: int = 8000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._messages: List[Message] = []
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def add(self, message: Message) -> str:
        """Adiciona mensagem à memória."""
        with self._lock:
            self._messages.append(message)
            
            # Trim se exceder limite
            while len(self._messages) > self.max_messages:
                self._messages.pop(0)
            
            return f"msg_{len(self._messages)}"
    
    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Adiciona mensagem do usuário."""
        return self.add(Message(
            role=MessageRole.USER,
            content=content,
            metadata=metadata or {}
        ))
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Adiciona mensagem do assistente."""
        return self.add(Message(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata=metadata or {}
        ))
    
    def get(self, item_id: str) -> Optional[Message]:
        """Recupera mensagem por índice."""
        try:
            idx = int(item_id.replace("msg_", "")) - 1
            return self._messages[idx] if 0 <= idx < len(self._messages) else None
        except (ValueError, IndexError):
            return None
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Retorna últimas mensagens."""
        with self._lock:
            if limit:
                return self._messages[-limit:]
            return self._messages.copy()
    
    def get_context_window(self, max_tokens: Optional[int] = None) -> List[Dict]:
        """
        Retorna mensagens formatadas para contexto do LLM.
        
        Respeita limite de tokens estimado.
        """
        max_tokens = max_tokens or self.max_tokens
        result = []
        total_tokens = 0
        
        for msg in reversed(self._messages):
            # Estimativa: 4 chars = 1 token
            msg_tokens = len(msg.content) // 4 + 10
            
            if total_tokens + msg_tokens > max_tokens:
                break
            
            result.insert(0, {"role": msg.role.value, "content": msg.content})
            total_tokens += msg_tokens
        
        return result
    
    def search(self, query: str, limit: int = 10) -> List[Message]:
        """Busca mensagens por texto."""
        query_lower = query.lower()
        matches = [
            msg for msg in self._messages
            if query_lower in msg.content.lower()
        ]
        return matches[-limit:]
    
    def set_context(self, key: str, value: Any) -> None:
        """Define contexto temporário."""
        self._context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Recupera contexto."""
        return self._context.get(key, default)
    
    def clear(self) -> None:
        """Limpa toda a memória de sessão."""
        with self._lock:
            self._messages.clear()
            self._context.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo da memória."""
        return {
            "message_count": len(self._messages),
            "context_keys": list(self._context.keys()),
            "estimated_tokens": sum(len(m.content) // 4 for m in self._messages)
        }


class LongTermMemory(BaseMemory):
    """
    Memória de longo prazo (persistente).
    
    Armazena fatos, preferências e histórico entre sessões.
    Persistida em SQLite.
    """
    
    def __init__(self, db_path: str = "./data/memory/long_term.db", agent_id: str = "default"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.agent_id = agent_id
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    importance REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON memories(category)")
    
    def _generate_id(self, content: str) -> str:
        """Gera ID único para conteúdo."""
        hash_input = f"{self.agent_id}:{content}:{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def add(self, item: MemoryItem) -> str:
        """Adiciona item à memória persistente."""
        item_id = item.id or self._generate_id(item.content)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories 
                (id, agent_id, content, category, importance, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                self.agent_id,
                item.content,
                item.metadata.get("category", "general"),
                item.importance,
                item.created_at.isoformat(),
                json.dumps(item.metadata)
            ))
        
        return item_id
    
    def remember(
        self, 
        content: str, 
        category: str = "general",
        importance: float = 0.5,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Memoriza um fato ou informação.
        
        Args:
            content: Conteúdo a memorizar
            category: Categoria (fact, preference, instruction, etc.)
            importance: Importância (0-1)
            metadata: Metadados adicionais
        """
        item = MemoryItem(
            id=self._generate_id(content),
            content=content,
            memory_type=MemoryType.LONG_TERM,
            importance=importance,
            metadata={"category": category, **(metadata or {})}
        )
        return self.add(item)
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Recupera item por ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ? AND agent_id = ?",
                (item_id, self.agent_id)
            ).fetchone()
            
            if row:
                # Atualizar contador de acesso
                conn.execute(
                    "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                    (item_id,)
                )
                
                return MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    memory_type=MemoryType.LONG_TERM,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    importance=row["importance"],
                    access_count=row["access_count"],
                    metadata=json.loads(row["metadata"])
                )
        
        return None
    
    def search(self, query: str, limit: int = 10, category: Optional[str] = None) -> List[MemoryItem]:
        """Busca memórias por texto."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = """
                SELECT * FROM memories 
                WHERE agent_id = ? AND content LIKE ?
            """
            params = [self.agent_id, f"%{query}%"]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            sql += " ORDER BY importance DESC, access_count DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            
            return [
                MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    memory_type=MemoryType.LONG_TERM,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    importance=row["importance"],
                    access_count=row["access_count"],
                    metadata=json.loads(row["metadata"])
                )
                for row in rows
            ]
    
    def get_by_category(self, category: str, limit: int = 20) -> List[MemoryItem]:
        """Recupera memórias por categoria."""
        return self.search("", limit=limit, category=category)
    
    def forget(self, item_id: str) -> bool:
        """Remove uma memória."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "DELETE FROM memories WHERE id = ? AND agent_id = ?",
                (item_id, self.agent_id)
            )
            return result.rowcount > 0
    
    def clear(self) -> None:
        """Limpa todas as memórias do agente."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories WHERE agent_id = ?", (self.agent_id,))
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo da memória."""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE agent_id = ?",
                (self.agent_id,)
            ).fetchone()[0]
            
            categories = conn.execute(
                "SELECT category, COUNT(*) FROM memories WHERE agent_id = ? GROUP BY category",
                (self.agent_id,)
            ).fetchall()
            
            return {
                "total_memories": count,
                "categories": {c[0]: c[1] for c in categories}
            }


class EpisodicMemory(BaseMemory):
    """
    Memória episódica.
    
    Armazena experiências, eventos e lições aprendidas.
    Útil para agentes que precisam aprender com experiências passadas.
    """
    
    def __init__(self, db_path: str = "./data/memory/episodic.db", agent_id: str = "default"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.agent_id = agent_id
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    lesson TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp TEXT NOT NULL,
                    context TEXT DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON episodes(agent_id)")
    
    def _generate_id(self, description: str) -> str:
        """Gera ID único."""
        hash_input = f"{self.agent_id}:{description}:{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def add(self, episode: Episode) -> str:
        """Adiciona episódio."""
        episode_id = episode.id or self._generate_id(episode.description)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO episodes 
                (id, agent_id, description, outcome, lesson, importance, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                episode_id,
                self.agent_id,
                episode.description,
                episode.outcome,
                episode.lesson,
                episode.importance,
                episode.timestamp.isoformat(),
                json.dumps(episode.context)
            ))
        
        return episode_id
    
    def record(
        self,
        description: str,
        outcome: str,
        lesson: Optional[str] = None,
        importance: float = 0.5,
        context: Optional[Dict] = None
    ) -> str:
        """
        Registra um episódio.
        
        Args:
            description: O que aconteceu
            outcome: Resultado (success, failure, partial)
            lesson: Lição aprendida
            importance: Importância (0-1)
            context: Contexto adicional
        """
        episode = Episode(
            id=self._generate_id(description),
            description=description,
            outcome=outcome,
            lesson=lesson,
            importance=importance,
            context=context or {}
        )
        return self.add(episode)
    
    def get(self, item_id: str) -> Optional[Episode]:
        """Recupera episódio por ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM episodes WHERE id = ? AND agent_id = ?",
                (item_id, self.agent_id)
            ).fetchone()
            
            if row:
                return Episode(
                    id=row["id"],
                    description=row["description"],
                    outcome=row["outcome"],
                    lesson=row["lesson"],
                    importance=row["importance"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    context=json.loads(row["context"])
                )
        
        return None
    
    def search(self, query: str, limit: int = 10) -> List[Episode]:
        """Busca episódios relevantes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute("""
                SELECT * FROM episodes 
                WHERE agent_id = ? AND (description LIKE ? OR lesson LIKE ?)
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            """, (self.agent_id, f"%{query}%", f"%{query}%", limit)).fetchall()
            
            return [
                Episode(
                    id=row["id"],
                    description=row["description"],
                    outcome=row["outcome"],
                    lesson=row["lesson"],
                    importance=row["importance"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    context=json.loads(row["context"])
                )
                for row in rows
            ]
    
    def get_lessons(self, limit: int = 10) -> List[str]:
        """Retorna lições aprendidas."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT lesson FROM episodes 
                WHERE agent_id = ? AND lesson IS NOT NULL
                ORDER BY importance DESC
                LIMIT ?
            """, (self.agent_id, limit)).fetchall()
            
            return [row[0] for row in rows]
    
    def get_similar_situations(self, description: str, limit: int = 5) -> List[Episode]:
        """Encontra situações similares passadas."""
        return self.search(description, limit)
    
    def clear(self) -> None:
        """Limpa todos os episódios."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM episodes WHERE agent_id = ?", (self.agent_id,))


class MemoryManager:
    """
    Gerenciador unificado de memórias.
    
    Coordena todos os tipos de memória e fornece interface unificada.
    
    Exemplo:
        memory = MemoryManager(agent_id="researcher")
        
        # Memória de curto prazo
        memory.short_term.add_user_message("Hello")
        
        # Memória de longo prazo
        memory.long_term.remember("User prefers formal language", category="preference")
        
        # Memória episódica
        memory.episodic.record(
            "User asked about AI trends",
            outcome="success",
            lesson="User is interested in technology"
        )
        
        # Obter contexto completo
        context = memory.get_context_for_prompt()
    """
    
    def __init__(
        self,
        agent_id: str = "default",
        enable_short_term: bool = True,
        enable_long_term: bool = True,
        enable_episodic: bool = False,
        db_path: str = "./data/memory"
    ):
        self.agent_id = agent_id
        self.db_path = Path(db_path)
        
        self.short_term: Optional[ShortTermMemory] = None
        self.long_term: Optional[LongTermMemory] = None
        self.episodic: Optional[EpisodicMemory] = None
        
        if enable_short_term:
            self.short_term = ShortTermMemory()
        
        if enable_long_term:
            self.long_term = LongTermMemory(
                db_path=str(self.db_path / "long_term.db"),
                agent_id=agent_id
            )
        
        if enable_episodic:
            self.episodic = EpisodicMemory(
                db_path=str(self.db_path / "episodic.db"),
                agent_id=agent_id
            )
    
    def get_context_for_prompt(
        self,
        include_long_term: bool = True,
        include_episodic: bool = True,
        max_tokens: int = 2000
    ) -> str:
        """
        Gera contexto de memória para incluir no prompt.
        
        Returns:
            String formatada com memórias relevantes
        """
        parts = []
        
        # Memórias de longo prazo
        if include_long_term and self.long_term:
            memories = self.long_term.search("", limit=10)
            if memories:
                parts.append("## Conhecimento Prévio:")
                for mem in memories:
                    parts.append(f"- {mem.content}")
        
        # Lições da memória episódica
        if include_episodic and self.episodic:
            lessons = self.episodic.get_lessons(limit=5)
            if lessons:
                parts.append("\n## Lições Aprendidas:")
                for lesson in lessons:
                    parts.append(f"- {lesson}")
        
        context = "\n".join(parts)
        
        # Truncar se exceder limite
        if len(context) > max_tokens * 4:  # ~4 chars per token
            context = context[:max_tokens * 4] + "..."
        
        return context
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Retorna histórico de conversa formatado para LLM."""
        if self.short_term:
            return self.short_term.get_context_window()
        return []
    
    def clear_session(self) -> None:
        """Limpa memória de sessão (short-term)."""
        if self.short_term:
            self.short_term.clear()
    
    def clear_all(self) -> None:
        """Limpa todas as memórias."""
        if self.short_term:
            self.short_term.clear()
        if self.long_term:
            self.long_term.clear()
        if self.episodic:
            self.episodic.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo de todas as memórias."""
        summary = {"agent_id": self.agent_id}
        
        if self.short_term:
            summary["short_term"] = self.short_term.get_summary()
        if self.long_term:
            summary["long_term"] = self.long_term.get_summary()
        if self.episodic:
            summary["episodic"] = {"enabled": True}
        
        return summary


# Factory function
def create_memory_manager(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None
) -> MemoryManager:
    """
    Cria MemoryManager com configuração.
    
    Args:
        agent_id: ID do agente
        config: Configuração opcional
    """
    config = config or {}
    
    return MemoryManager(
        agent_id=agent_id,
        enable_short_term=config.get("short_term", True),
        enable_long_term=config.get("long_term", False),
        enable_episodic=config.get("episodic", False),
        db_path=config.get("db_path", "./data/memory")
    )

"""
User Memory - Memória persistente por usuário.

Armazena informações importantes sobre o usuário
que persistem entre sessões.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Item de memória."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    category: str = "general"  # general, preference, fact, context
    importance: float = 0.5
    
    # Source
    source_conversation_id: Optional[str] = None
    source_message_id: Optional[str] = None
    
    # Status
    is_pinned: bool = False
    is_verified: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat()
        }


class UserMemory:
    """
    Memória persistente do usuário.
    
    Armazena fatos, preferências e contexto
    que o assistente deve lembrar.
    """
    
    def __init__(self):
        self._memories: Dict[str, List[MemoryItem]] = {}  # user_id -> memories
    
    async def add(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        source_conversation_id: Optional[str] = None
    ) -> MemoryItem:
        """Adiciona item à memória."""
        item = MemoryItem(
            content=content,
            category=category,
            importance=importance,
            source_conversation_id=source_conversation_id
        )
        
        if user_id not in self._memories:
            self._memories[user_id] = []
        
        self._memories[user_id].append(item)
        logger.debug(f"Added memory for user {user_id}: {content[:50]}")
        
        return item
    
    async def get(
        self,
        user_id: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[MemoryItem]:
        """Obtém memórias do usuário."""
        if user_id not in self._memories:
            return []
        
        memories = self._memories[user_id]
        
        if category:
            memories = [m for m in memories if m.category == category]
        
        # Ordenar por importância e pinned
        memories = sorted(
            memories,
            key=lambda m: (m.is_pinned, m.importance),
            reverse=True
        )
        
        # Atualizar last_accessed
        for m in memories[:limit]:
            m.last_accessed = datetime.now()
        
        return memories[:limit]
    
    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[MemoryItem]:
        """Busca memórias por texto."""
        if user_id not in self._memories:
            return []
        
        query_lower = query.lower()
        matches = [
            m for m in self._memories[user_id]
            if query_lower in m.content.lower()
        ]
        
        return sorted(matches, key=lambda m: m.importance, reverse=True)[:limit]
    
    async def update(
        self,
        user_id: str,
        memory_id: str,
        **kwargs
    ) -> Optional[MemoryItem]:
        """Atualiza uma memória."""
        if user_id not in self._memories:
            return None
        
        for memory in self._memories[user_id]:
            if memory.id == memory_id:
                for key, value in kwargs.items():
                    if hasattr(memory, key):
                        setattr(memory, key, value)
                return memory
        
        return None
    
    async def delete(
        self,
        user_id: str,
        memory_id: str
    ) -> bool:
        """Deleta uma memória."""
        if user_id not in self._memories:
            return False
        
        initial_len = len(self._memories[user_id])
        self._memories[user_id] = [
            m for m in self._memories[user_id]
            if m.id != memory_id
        ]
        
        return len(self._memories[user_id]) < initial_len
    
    async def clear(self, user_id: str) -> int:
        """Limpa todas as memórias do usuário."""
        if user_id not in self._memories:
            return 0
        
        count = len(self._memories[user_id])
        self._memories[user_id] = []
        return count
    
    async def pin(self, user_id: str, memory_id: str) -> bool:
        """Fixa uma memória."""
        memory = await self.update(user_id, memory_id, is_pinned=True)
        return memory is not None
    
    async def unpin(self, user_id: str, memory_id: str) -> bool:
        """Desfixa uma memória."""
        memory = await self.update(user_id, memory_id, is_pinned=False)
        return memory is not None
    
    async def get_context_string(
        self,
        user_id: str,
        max_items: int = 5
    ) -> str:
        """Obtém string de contexto para LLM."""
        memories = await self.get(user_id, max_items)
        
        if not memories:
            return ""
        
        parts = ["User memories:"]
        for m in memories:
            parts.append(f"- {m.content}")
        
        return "\n".join(parts)
    
    async def auto_extract(
        self,
        user_id: str,
        message: str,
        response: str
    ) -> List[MemoryItem]:
        """
        Extrai automaticamente memórias de uma conversa.
        
        Em produção: usar LLM para extrair fatos importantes.
        """
        # Placeholder: detectar padrões simples
        extracted = []
        
        # Detectar preferências
        if "prefer" in message.lower() or "like" in message.lower():
            item = await self.add(
                user_id,
                f"User expressed preference: {message[:100]}",
                category="preference",
                importance=0.7
            )
            extracted.append(item)
        
        # Detectar fatos
        if "i am" in message.lower() or "my name" in message.lower():
            item = await self.add(
                user_id,
                f"User stated: {message[:100]}",
                category="fact",
                importance=0.8
            )
            extracted.append(item)
        
        return extracted


# Singleton
_user_memory: Optional[UserMemory] = None


def get_user_memory() -> UserMemory:
    global _user_memory
    if _user_memory is None:
        _user_memory = UserMemory()
    return _user_memory

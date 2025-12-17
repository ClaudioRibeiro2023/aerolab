"""
Agno SDK - Memory

Sistema de memória para agentes no SDK.
Integra com o Memory Manager v2.

Uso:
```python
from agno import Agent, Memory

# Memória de curto prazo (sessão)
agent = Agent(
    name="assistant",
    memory=Memory(type="short_term")
)

# Memória de longo prazo
agent = Agent(
    name="researcher",
    memory=Memory(type="long_term", agent_id="researcher_1")
)

# Memória customizada
memory = Memory(
    type="long_term",
    search_limit=10,
    importance_threshold=0.5
)
agent = Agent(name="custom", memory=memory)
```
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union
import asyncio
import logging


logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """
    Configuração de memória.
    
    Attributes:
        type: Tipo de memória (short_term, long_term, episodic)
        agent_id: ID do agente para memória persistente
        search_limit: Limite de resultados em buscas
        importance_threshold: Threshold mínimo de importância
        auto_store: Armazenar automaticamente mensagens importantes
    """
    type: str = "short_term"  # short_term, long_term, episodic, all
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    
    # Busca
    search_limit: int = 10
    importance_threshold: float = 0.3
    
    # Comportamento
    auto_store: bool = True
    auto_retrieve: bool = True
    
    # Decay
    enable_decay: bool = True
    decay_rate: float = 0.01


@dataclass
class MemoryEntry:
    """
    Entrada de memória.
    
    Attributes:
        content: Conteúdo da memória
        importance: Score de importância (0-1)
        tags: Tags para categorização
    """
    content: str
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Contexto
    session_id: Optional[str] = None
    agent_id: Optional[str] = None


class Memory:
    """
    Sistema de memória para agentes.
    
    Integra com o Memory Manager v2 para fornecer:
    - Short-term: Contexto de sessão em Redis
    - Long-term: Conhecimento persistente em pgvector
    - Episodic: Histórico de execuções
    
    Uso:
    ```python
    memory = Memory(type="long_term")
    
    # Armazenar
    await memory.store("Important information")
    
    # Buscar
    results = await memory.search("query")
    
    # Obter contexto
    context = await memory.get_context(session_id)
    ```
    """
    
    def __init__(
        self,
        type: str = "short_term",
        config: Optional[MemoryConfig] = None,
        **kwargs
    ):
        if config:
            self.config = config
        else:
            self.config = MemoryConfig(type=type, **kwargs)
        
        self._manager = None
        self._initialized = False
    
    async def _get_manager(self):
        """Obtém o Memory Manager."""
        if self._manager is None:
            from ..memory.v2.manager import get_memory_manager
            self._manager = get_memory_manager()
            
            if not self._initialized:
                await self._manager.initialize()
                self._initialized = True
        
        return self._manager
    
    async def store(
        self,
        content: str,
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Armazena uma memória.
        
        Args:
            content: Conteúdo a armazenar
            importance: Score de importância (0-1)
            tags: Tags opcionais
            metadata: Metadados opcionais
            session_id: ID da sessão (para short-term)
            
        Returns:
            ID da memória criada
        """
        manager = await self._get_manager()
        
        if self.config.type == "short_term":
            if not session_id:
                raise ValueError("session_id required for short_term memory")
            
            memory = await manager.store_short_term(
                content=content,
                session_id=session_id,
                agent_id=self.config.agent_id,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
        else:
            memory = await manager.store_long_term(
                content=content,
                agent_id=self.config.agent_id,
                user_id=self.config.user_id,
                project_id=self.config.project_id,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
        
        return memory.id
    
    async def search(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Busca memórias por similaridade.
        
        Args:
            query: Query de busca
            limit: Limite de resultados
            
        Returns:
            Lista de memórias encontradas
        """
        manager = await self._get_manager()
        
        results = await manager.search_memories(
            query=query,
            agent_id=self.config.agent_id,
            user_id=self.config.user_id,
            project_id=self.config.project_id,
            limit=limit or self.config.search_limit
        )
        
        return [
            {
                "id": r.memory.id,
                "content": r.memory.content,
                "score": r.score,
                "importance": r.memory.importance_score,
                "created_at": r.memory.created_at.isoformat()
            }
            for r in results
            if r.score >= self.config.importance_threshold
        ]
    
    async def get_context(
        self,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> dict:
        """
        Obtém contexto completo para um agente.
        
        Combina memórias de curto e longo prazo.
        
        Args:
            session_id: ID da sessão
            agent_id: ID do agente
            
        Returns:
            Dicionário com contexto
        """
        manager = await self._get_manager()
        
        return await manager.build_agent_context(
            agent_id=agent_id or self.config.agent_id or "default",
            session_id=session_id,
            max_memories=self.config.search_limit
        )
    
    async def get_conversation(self, session_id: str) -> Optional[dict]:
        """
        Obtém contexto de conversa.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Contexto de conversa ou None
        """
        manager = await self._get_manager()
        context = await manager.get_context(session_id)
        
        if context:
            return {
                "session_id": context.session_id,
                "messages": context.messages,
                "variables": context.variables,
                "message_count": context.message_count
            }
        
        return None
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Adiciona mensagem ao histórico.
        
        Args:
            session_id: ID da sessão
            role: Papel (user, assistant, system)
            content: Conteúdo da mensagem
        """
        manager = await self._get_manager()
        await manager.add_message(session_id, role, content)
    
    async def start_session(
        self,
        session_id: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Inicia uma nova sessão.
        
        Args:
            session_id: ID da sessão
            agent_id: ID do agente
            user_id: ID do usuário
            
        Returns:
            Contexto da sessão
        """
        manager = await self._get_manager()
        
        context = await manager.get_or_create_context(
            session_id=session_id,
            agent_id=agent_id or self.config.agent_id or "default",
            user_id=user_id or self.config.user_id
        )
        
        return {
            "session_id": context.session_id,
            "agent_id": context.agent_id,
            "user_id": context.user_id
        }
    
    async def get_similar_episodes(
        self,
        task_description: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Busca episódios similares.
        
        Útil para aprendizado e reutilização de experiências.
        
        Args:
            task_description: Descrição da tarefa
            limit: Limite de resultados
            
        Returns:
            Lista de episódios similares
        """
        manager = await self._get_manager()
        
        episodes = await manager.get_similar_episodes(
            task_description=task_description,
            agent_id=self.config.agent_id,
            limit=limit
        )
        
        return [e.to_dict() for e in episodes]
    
    async def start_episode(
        self,
        task_description: str,
        task_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Inicia um novo episódio.
        
        Args:
            task_description: Descrição da tarefa
            task_type: Tipo da tarefa
            session_id: ID da sessão
            
        Returns:
            ID do episódio
        """
        manager = await self._get_manager()
        
        episode = await manager.start_episode(
            agent_id=self.config.agent_id or "default",
            task_description=task_description,
            task_type=task_type,
            session_id=session_id,
            user_id=self.config.user_id,
            project_id=self.config.project_id
        )
        
        return episode.id
    
    async def clear_session(self, session_id: str) -> int:
        """
        Limpa memórias de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Número de memórias removidas
        """
        manager = await self._get_manager()
        stm = await manager._get_short_term()
        return await stm.clear_session(session_id)
    
    # Métodos síncronos para conveniência
    
    def store_sync(self, content: str, **kwargs) -> str:
        """Versão síncrona de store."""
        return asyncio.run(self.store(content, **kwargs))
    
    def search_sync(self, query: str, **kwargs) -> list[dict]:
        """Versão síncrona de search."""
        return asyncio.run(self.search(query, **kwargs))
    
    def get_context_sync(self, session_id: str, **kwargs) -> dict:
        """Versão síncrona de get_context."""
        return asyncio.run(self.get_context(session_id, **kwargs))


# Factory functions

def create_short_term_memory(**kwargs) -> Memory:
    """Cria memória de curto prazo."""
    return Memory(type="short_term", **kwargs)


def create_long_term_memory(**kwargs) -> Memory:
    """Cria memória de longo prazo."""
    return Memory(type="long_term", **kwargs)


def create_episodic_memory(**kwargs) -> Memory:
    """Cria memória episódica."""
    return Memory(type="episodic", **kwargs)

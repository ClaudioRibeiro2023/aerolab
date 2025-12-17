"""
Memory v2 - Memory Manager

Gerenciador unificado que orquestra os três níveis de memória:
- Short-term (Redis)
- Long-term (PostgreSQL + pgvector)
- Episodic (PostgreSQL)
"""

import asyncio
from datetime import datetime
from typing import Optional
import logging

from .config import MemoryConfig, get_memory_config
from .types import (
    Memory, MemoryType, MemoryPriority, MemoryQuery, 
    MemorySearchResult, ConversationContext, Episode
)
from .short_term import ShortTermMemory, get_short_term_memory
from .long_term import LongTermMemory, get_long_term_memory
from .episodic import EpisodicMemory, get_episodic_memory


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Gerenciador unificado de memória.
    
    Features:
    - Interface unificada para todos os níveis
    - Promoção automática de short-term para long-term
    - Busca híbrida em múltiplos níveis
    - Consolidação periódica
    - Métricas e observabilidade
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        
        # Stores
        self._short_term: Optional[ShortTermMemory] = None
        self._long_term: Optional[LongTermMemory] = None
        self._episodic: Optional[EpisodicMemory] = None
        
        # Estado
        self._initialized = False
        
        # Métricas
        self.total_operations = 0
        self.promotions = 0
        self.searches = 0
    
    async def _get_short_term(self) -> ShortTermMemory:
        """Retorna short-term memory."""
        if self._short_term is None:
            self._short_term = get_short_term_memory(self.config)
        return self._short_term
    
    async def _get_long_term(self) -> LongTermMemory:
        """Retorna long-term memory."""
        if self._long_term is None:
            self._long_term = get_long_term_memory(self.config)
        return self._long_term
    
    async def _get_episodic(self) -> EpisodicMemory:
        """Retorna episodic memory."""
        if self._episodic is None:
            self._episodic = get_episodic_memory(self.config)
        return self._episodic
    
    async def initialize(self) -> None:
        """Inicializa todos os stores."""
        if self._initialized:
            return
        
        long_term = await self._get_long_term()
        episodic = await self._get_episodic()
        
        await asyncio.gather(
            long_term.initialize(),
            episodic.initialize()
        )
        
        self._initialized = True
        logger.info("Memory Manager inicializado")
    
    # ==================== Short-Term Operations ====================
    
    async def store_short_term(
        self,
        content: str,
        session_id: str,
        agent_id: Optional[str] = None,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        importance: float = 0.5,
        ttl: Optional[int] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None
    ) -> Memory:
        """
        Armazena memória de curto prazo.
        
        Args:
            content: Conteúdo da memória
            session_id: ID da sessão
            agent_id: ID do agente
            priority: Prioridade
            importance: Score de importância (0-1)
            ttl: TTL em segundos
            tags: Tags para categorização
            metadata: Metadados adicionais
            
        Returns:
            Memory criada
        """
        self.total_operations += 1
        
        memory = Memory(
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            priority=priority,
            importance_score=importance,
            session_id=session_id,
            agent_id=agent_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        stm = await self._get_short_term()
        await stm.store(memory, ttl)
        
        return memory
    
    async def get_session_memories(self, session_id: str) -> list[Memory]:
        """Recupera todas as memórias de uma sessão."""
        stm = await self._get_short_term()
        return await stm.get_by_session(session_id)
    
    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Recupera contexto de conversa."""
        stm = await self._get_short_term()
        return await stm.get_context(session_id)
    
    async def get_or_create_context(
        self,
        session_id: str,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> ConversationContext:
        """Recupera ou cria contexto de conversa."""
        stm = await self._get_short_term()
        return await stm.get_or_create_context(session_id, agent_id, user_id)
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> ConversationContext:
        """Adiciona mensagem ao contexto."""
        stm = await self._get_short_term()
        return await stm.add_message(session_id, role, content, metadata)
    
    # ==================== Long-Term Operations ====================
    
    async def store_long_term(
        self,
        content: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None,
        importance: float = 0.5,
        summary: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None
    ) -> Memory:
        """
        Armazena memória de longo prazo.
        
        Args:
            content: Conteúdo da memória
            agent_id: ID do agente
            user_id: ID do usuário
            project_id: ID do projeto
            importance: Score de importância
            summary: Resumo opcional
            tags: Tags para categorização
            metadata: Metadados adicionais
            
        Returns:
            Memory criada
        """
        self.total_operations += 1
        
        memory = Memory(
            content=content,
            summary=summary,
            memory_type=MemoryType.LONG_TERM,
            importance_score=importance,
            agent_id=agent_id,
            user_id=user_id,
            project_id=project_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        ltm = await self._get_long_term()
        await ltm.store(memory)
        
        return memory
    
    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None,
        include_short_term: bool = False,
        limit: int = 10
    ) -> list[MemorySearchResult]:
        """
        Busca memórias por similaridade semântica.
        
        Args:
            query: Query de busca
            agent_id: Filtrar por agente
            user_id: Filtrar por usuário
            project_id: Filtrar por projeto
            include_short_term: Incluir memórias de curto prazo
            limit: Número máximo de resultados
            
        Returns:
            Lista de resultados ordenados por relevância
        """
        self.searches += 1
        
        results: list[MemorySearchResult] = []
        
        # Buscar no long-term
        ltm = await self._get_long_term()
        lt_results = await ltm.search(
            query=query,
            agent_id=agent_id,
            user_id=user_id,
            project_id=project_id,
            limit=limit
        )
        results.extend(lt_results)
        
        # Buscar no short-term se solicitado
        if include_short_term and (agent_id or user_id):
            stm = await self._get_short_term()
            # Short-term não tem busca semântica, fazer match simples
            # Isso é uma limitação - em produção, indexaríamos no Redis Search
            
        # Ordenar por score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def search_by_query(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Busca usando MemoryQuery estruturada."""
        return await self.search_memories(
            query=query.query,
            agent_id=query.agent_id,
            user_id=query.user_id,
            project_id=query.project_id,
            limit=query.limit
        )
    
    # ==================== Episodic Operations ====================
    
    async def start_episode(
        self,
        agent_id: str,
        task_description: str,
        task_type: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> Episode:
        """Inicia um novo episódio."""
        episodic = await self._get_episodic()
        return await episodic.start_episode(
            agent_id=agent_id,
            task_description=task_description,
            task_type=task_type,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id
        )
    
    async def update_episode(self, episode: Episode) -> None:
        """Atualiza um episódio em andamento."""
        episodic = await self._get_episodic()
        await episodic.update_episode(episode)
    
    async def complete_episode(
        self,
        episode: Episode,
        outcome: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Finaliza um episódio."""
        episodic = await self._get_episodic()
        await episodic.complete_episode(episode, outcome, result, error)
    
    async def get_similar_episodes(
        self,
        task_description: str,
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> list[Episode]:
        """Busca episódios com tarefas similares."""
        episodic = await self._get_episodic()
        return await episodic.search_similar_tasks(
            task_description=task_description,
            agent_id=agent_id,
            successful_only=True,
            limit=limit
        )
    
    async def get_best_approach(
        self,
        task_type: str,
        agent_id: str
    ) -> Optional[dict]:
        """Retorna melhor abordagem para um tipo de tarefa."""
        episodic = await self._get_episodic()
        return await episodic.get_best_approach(task_type, agent_id)
    
    # ==================== Promotion & Consolidation ====================
    
    async def promote_to_long_term(self, memory_id: str) -> Optional[Memory]:
        """
        Promove memória de short-term para long-term.
        
        Args:
            memory_id: ID da memória a promover
            
        Returns:
            Memory promovida ou None se não encontrada
        """
        stm = await self._get_short_term()
        memory = await stm.get(memory_id)
        
        if not memory:
            return None
        
        # Mudar tipo
        memory.memory_type = MemoryType.LONG_TERM
        
        # Armazenar no long-term
        ltm = await self._get_long_term()
        await ltm.store(memory)
        
        # Remover do short-term
        await stm.delete(memory_id)
        
        self.promotions += 1
        logger.info(f"Memória {memory_id} promovida para long-term")
        
        return memory
    
    async def auto_promote_session(self, session_id: str) -> int:
        """
        Promove automaticamente memórias elegíveis de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Número de memórias promovidas
        """
        if not self.config.enable_auto_promotion:
            return 0
        
        stm = await self._get_short_term()
        candidates = await stm.get_promotion_candidates(session_id)
        
        count = 0
        for memory in candidates:
            if await self.promote_to_long_term(memory.id):
                count += 1
        
        return count
    
    async def consolidate_memories(
        self,
        threshold: float = 0.9,
        max_consolidations: int = 10
    ) -> int:
        """
        Consolida memórias similares no long-term.
        
        Args:
            threshold: Threshold de similaridade
            max_consolidations: Máximo de consolidações
            
        Returns:
            Número de consolidações realizadas
        """
        if not self.config.enable_auto_consolidation:
            return 0
        
        ltm = await self._get_long_term()
        return await ltm.consolidate_similar(threshold, max_consolidations)
    
    # ==================== Context Building ====================
    
    async def build_agent_context(
        self,
        agent_id: str,
        session_id: str,
        current_task: Optional[str] = None,
        max_memories: int = 10
    ) -> dict:
        """
        Constrói contexto completo para um agente.
        
        Combina:
        - Contexto de conversa (short-term)
        - Memórias relevantes (long-term)
        - Episódios similares (episodic)
        
        Args:
            agent_id: ID do agente
            session_id: ID da sessão
            current_task: Tarefa atual (para buscar similares)
            max_memories: Número máximo de memórias
            
        Returns:
            Dicionário com contexto completo
        """
        # Buscar contexto de conversa
        context = await self.get_context(session_id)
        
        # Buscar memórias de sessão
        session_memories = await self.get_session_memories(session_id)
        
        # Buscar memórias de longo prazo relevantes
        long_term_memories = []
        if current_task:
            results = await self.search_memories(
                query=current_task,
                agent_id=agent_id,
                limit=max_memories
            )
            long_term_memories = [r.memory for r in results]
        
        # Buscar episódios similares
        similar_episodes = []
        best_approach = None
        if current_task:
            similar_episodes = await self.get_similar_episodes(
                task_description=current_task,
                agent_id=agent_id,
                limit=3
            )
            
            # Tentar obter melhor abordagem
            if similar_episodes and similar_episodes[0].task_type:
                best_approach = await self.get_best_approach(
                    task_type=similar_episodes[0].task_type,
                    agent_id=agent_id
                )
        
        return {
            "conversation": {
                "session_id": session_id,
                "messages": context.to_prompt_messages() if context else [],
                "variables": context.variables if context else {}
            },
            "session_memories": [m.to_dict() for m in session_memories],
            "long_term_memories": [m.to_dict() for m in long_term_memories],
            "similar_episodes": [e.to_dict() for e in similar_episodes],
            "best_approach": best_approach
        }
    
    # ==================== Maintenance ====================
    
    async def cleanup(self) -> dict:
        """
        Executa limpeza e manutenção.
        
        Returns:
            Estatísticas de limpeza
        """
        stats = {
            "promotions": 0,
            "consolidations": 0,
            "episodes_cleaned": 0
        }
        
        # Consolidar memórias
        if self.config.enable_auto_consolidation:
            ltm = await self._get_long_term()
            stats["consolidations"] = await ltm.consolidate_similar()
        
        # Limpar episódios antigos
        episodic = await self._get_episodic()
        stats["episodes_cleaned"] = await episodic.cleanup_old_episodes()
        
        return stats
    
    async def get_stats(self, agent_id: Optional[str] = None) -> dict:
        """Retorna estatísticas de todos os stores."""
        ltm = await self._get_long_term()
        episodic = await self._get_episodic()
        
        lt_stats, ep_stats = await asyncio.gather(
            ltm.get_stats(agent_id),
            episodic.get_stats(agent_id)
        )
        
        return {
            "short_term": (await self._get_short_term()).get_metrics(),
            "long_term": lt_stats,
            "episodic": ep_stats,
            "manager": {
                "total_operations": self.total_operations,
                "promotions": self.promotions,
                "searches": self.searches
            }
        }
    
    def get_metrics(self) -> dict:
        """Retorna métricas do manager."""
        return {
            "total_operations": self.total_operations,
            "promotions": self.promotions,
            "searches": self.searches
        }
    
    async def close(self) -> None:
        """Fecha todas as conexões."""
        tasks = []
        
        if self._short_term:
            tasks.append(self._short_term.close())
        if self._long_term:
            tasks.append(self._long_term.close())
        if self._episodic:
            tasks.append(self._episodic.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Singleton
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(config: Optional[MemoryConfig] = None) -> MemoryManager:
    """Retorna o memory manager singleton."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(config)
    return _memory_manager

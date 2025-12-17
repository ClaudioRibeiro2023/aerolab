"""
Agno Team Orchestrator v2.0 - Shared Memory Space

Team memory management with multiple scopes.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

from .types import MemoryItem, MemoryScope

logger = logging.getLogger(__name__)


# ============================================================
# TEAM MEMORY SPACE
# ============================================================

class TeamMemorySpace:
    """
    Shared memory space for team agents.
    
    Scopes:
    - WORKING: Current execution context (ephemeral)
    - EPISODIC: History of past executions
    - SEMANTIC: Permanent knowledge (RAG)
    - PROCEDURAL: How to do tasks
    """
    
    def __init__(self, team_id: str):
        self.team_id = team_id
        self._working: Dict[str, MemoryItem] = {}
        self._episodic: List[MemoryItem] = []
        self._semantic: Dict[str, MemoryItem] = {}
        self._procedural: Dict[str, MemoryItem] = {}
        self._agent_views: Dict[str, set] = defaultdict(set)
    
    async def store(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.WORKING,
        agent_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> MemoryItem:
        """Store item in memory."""
        item = MemoryItem(
            key=key,
            value=value,
            scope=scope,
            agent_id=agent_id,
            team_id=self.team_id,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        )
        
        storage = self._get_storage(scope)
        
        if scope == MemoryScope.EPISODIC:
            storage.append(item)
        else:
            storage[key] = item
        
        # Track agent access
        if agent_id:
            self._agent_views[agent_id].add(key)
        
        logger.debug(f"Stored memory: {key} in {scope.value}")
        return item
    
    async def retrieve(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.WORKING
    ) -> Optional[Any]:
        """Retrieve item from memory."""
        storage = self._get_storage(scope)
        
        if scope == MemoryScope.EPISODIC:
            # Search episodic memory
            for item in reversed(storage):
                if item.key == key:
                    if not self._is_expired(item):
                        item.access_count += 1
                        return item.value
            return None
        
        item = storage.get(key)
        if item and not self._is_expired(item):
            item.access_count += 1
            return item.value
        
        return None
    
    async def search(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """Search memory by query (simple text match)."""
        results = []
        
        scopes_to_search = [scope] if scope else [
            MemoryScope.WORKING,
            MemoryScope.SEMANTIC,
            MemoryScope.PROCEDURAL
        ]
        
        for s in scopes_to_search:
            storage = self._get_storage(s)
            
            if isinstance(storage, list):
                items = storage
            else:
                items = storage.values()
            
            for item in items:
                if self._is_expired(item):
                    continue
                
                # Simple relevance scoring
                score = self._calculate_relevance(query, item)
                if score > 0:
                    item.relevance_score = score
                    results.append(item)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]
    
    async def forget(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.WORKING
    ) -> bool:
        """Remove item from memory."""
        storage = self._get_storage(scope)
        
        if scope == MemoryScope.EPISODIC:
            for i, item in enumerate(storage):
                if item.key == key:
                    storage.pop(i)
                    return True
            return False
        
        if key in storage:
            del storage[key]
            return True
        return False
    
    async def clear_scope(self, scope: MemoryScope):
        """Clear all items in a scope."""
        if scope == MemoryScope.WORKING:
            self._working.clear()
        elif scope == MemoryScope.EPISODIC:
            self._episodic.clear()
        elif scope == MemoryScope.SEMANTIC:
            self._semantic.clear()
        elif scope == MemoryScope.PROCEDURAL:
            self._procedural.clear()
    
    def get_shared_context(self, max_tokens: int = 2000) -> str:
        """Get shared context as string for prompts."""
        context_parts = []
        char_count = 0
        
        # Add working memory
        for key, item in self._working.items():
            if self._is_expired(item):
                continue
            
            entry = f"[{key}]: {item.value}"
            if char_count + len(entry) > max_tokens * 4:  # Rough char estimate
                break
            
            context_parts.append(entry)
            char_count += len(entry)
        
        return "\n".join(context_parts)
    
    def get_agent_view(self, agent_id: str) -> Dict[str, Any]:
        """Get memory items visible to specific agent."""
        visible_keys = self._agent_views.get(agent_id, set())
        view = {}
        
        for key in visible_keys:
            for scope in [MemoryScope.WORKING, MemoryScope.SEMANTIC]:
                value = asyncio.get_event_loop().run_until_complete(
                    self.retrieve(key, scope)
                )
                if value is not None:
                    view[key] = value
                    break
        
        return view
    
    async def sync_to_agent(self, agent_id: str, keys: List[str]):
        """Sync specific keys to agent's view."""
        for key in keys:
            self._agent_views[agent_id].add(key)
    
    async def broadcast_update(self, key: str, value: Any):
        """Broadcast memory update to all agents."""
        await self.store(key, value, MemoryScope.WORKING)
        # In production, would notify all agents
    
    async def consolidate(self):
        """Consolidate working memory to long-term."""
        # Move frequently accessed items to semantic memory
        for key, item in list(self._working.items()):
            if item.access_count >= 3:
                await self.store(
                    key=key,
                    value=item.value,
                    scope=MemoryScope.SEMANTIC
                )
                logger.info(f"Consolidated {key} to semantic memory")
    
    async def cleanup_expired(self):
        """Remove expired items."""
        # Working memory
        expired_keys = [
            k for k, v in self._working.items() 
            if self._is_expired(v)
        ]
        for key in expired_keys:
            del self._working[key]
        
        # Episodic memory
        self._episodic = [
            item for item in self._episodic 
            if not self._is_expired(item)
        ]
    
    def _get_storage(self, scope: MemoryScope):
        """Get storage for scope."""
        if scope == MemoryScope.WORKING:
            return self._working
        elif scope == MemoryScope.EPISODIC:
            return self._episodic
        elif scope == MemoryScope.SEMANTIC:
            return self._semantic
        elif scope == MemoryScope.PROCEDURAL:
            return self._procedural
        else:
            return self._working
    
    def _is_expired(self, item: MemoryItem) -> bool:
        """Check if item is expired."""
        if item.expires_at is None:
            return False
        return datetime.now() > item.expires_at
    
    def _calculate_relevance(self, query: str, item: MemoryItem) -> float:
        """Calculate relevance score (simple implementation)."""
        query_lower = query.lower()
        key_lower = item.key.lower()
        value_str = str(item.value).lower()
        
        score = 0.0
        
        # Key match
        if query_lower in key_lower:
            score += 0.5
        
        # Value match
        if query_lower in value_str:
            score += 0.3
        
        # Recency bonus
        age = (datetime.now() - item.created_at).total_seconds()
        recency_score = max(0, 1 - age / 3600)  # Decay over 1 hour
        score += 0.2 * recency_score
        
        return score
    
    def to_dict(self) -> Dict:
        """Serialize memory state."""
        return {
            "team_id": self.team_id,
            "working": {k: v.to_dict() for k, v in self._working.items()},
            "episodic_count": len(self._episodic),
            "semantic_count": len(self._semantic),
            "procedural_count": len(self._procedural),
        }


# ============================================================
# MEMORY MANAGER
# ============================================================

class MemoryManager:
    """Manages memory spaces for multiple teams."""
    
    def __init__(self):
        self._team_memories: Dict[str, TeamMemorySpace] = {}
    
    def get_or_create(self, team_id: str) -> TeamMemorySpace:
        """Get or create memory space for team."""
        if team_id not in self._team_memories:
            self._team_memories[team_id] = TeamMemorySpace(team_id)
        return self._team_memories[team_id]
    
    def delete(self, team_id: str) -> bool:
        """Delete team memory space."""
        if team_id in self._team_memories:
            del self._team_memories[team_id]
            return True
        return False
    
    async def cleanup_all(self):
        """Cleanup expired items in all team memories."""
        for memory in self._team_memories.values():
            await memory.cleanup_expired()
    
    async def consolidate_all(self):
        """Consolidate all team memories."""
        for memory in self._team_memories.values():
            await memory.consolidate()


# Singleton
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

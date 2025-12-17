"""
Memory v2 - Sistema de Memória Avançado para Agentes

Implementa arquitetura de memória em três níveis:
- Short-term: Contexto de sessão (Redis)
- Long-term: Conhecimento persistente (pgvector)
- Episodic: Histórico de execuções (PostgreSQL)

Features:
- Promoção/demoção automática entre níveis
- Decay temporal para relevância
- Consolidação de memórias
- Busca semântica
"""

from .config import MemoryConfig, get_memory_config
from .short_term import ShortTermMemory, get_short_term_memory
from .long_term import LongTermMemory, get_long_term_memory
from .episodic import EpisodicMemory, get_episodic_memory
from .manager import MemoryManager, get_memory_manager
from .types import (
    Memory,
    MemoryType,
    MemoryPriority,
    MemoryQuery,
    MemorySearchResult,
    ConversationContext,
    Episode
)

__all__ = [
    # Config
    "MemoryConfig",
    "get_memory_config",
    # Stores
    "ShortTermMemory",
    "get_short_term_memory",
    "LongTermMemory",
    "get_long_term_memory",
    "EpisodicMemory",
    "get_episodic_memory",
    # Manager
    "MemoryManager",
    "get_memory_manager",
    # Types
    "Memory",
    "MemoryType",
    "MemoryPriority",
    "MemoryQuery",
    "MemorySearchResult",
    "ConversationContext",
    "Episode"
]

__version__ = "2.0.0"

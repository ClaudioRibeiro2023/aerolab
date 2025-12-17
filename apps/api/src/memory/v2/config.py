"""
Memory v2 - Configuração

Configuração centralizada para o sistema de memória.
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class RedisConfig:
    """Configuração do Redis para short-term memory."""
    host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    db: int = field(default_factory=lambda: int(os.getenv("REDIS_MEMORY_DB", "1")))
    
    @property
    def url(self) -> str:
        """URL de conexão Redis."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class PostgresConfig:
    """Configuração do PostgreSQL para long-term e episodic memory."""
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_MEMORY_DB", "agno_memory"))
    
    @property
    def url(self) -> str:
        """URL de conexão PostgreSQL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """URL de conexão PostgreSQL assíncrona."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ShortTermConfig:
    """Configuração de short-term memory."""
    
    # TTL padrão em segundos (30 minutos)
    default_ttl: int = 1800
    
    # TTL máximo (24 horas)
    max_ttl: int = 86400
    
    # Número máximo de memórias por sessão
    max_per_session: int = 100
    
    # Tamanho máximo do contexto de conversa
    max_context_messages: int = 50
    
    # Threshold para promoção para long-term
    promotion_access_count: int = 3
    promotion_importance_threshold: float = 0.7


@dataclass
class LongTermConfig:
    """Configuração de long-term memory."""
    
    # Dimensões do embedding
    embedding_dimensions: int = 3072
    
    # Modelo de embedding
    embedding_model: str = "text-embedding-3-large"
    
    # Número máximo de memórias a retornar em busca
    max_search_results: int = 20
    
    # Threshold de similaridade para busca
    similarity_threshold: float = 0.5
    
    # Taxa de decay temporal (por hora)
    decay_rate: float = 0.01
    
    # Intervalo de consolidação (em horas)
    consolidation_interval_hours: int = 24
    
    # Threshold para consolidação
    consolidation_similarity_threshold: float = 0.9


@dataclass
class EpisodicConfig:
    """Configuração de episodic memory."""
    
    # Número máximo de episódios por agente
    max_episodes_per_agent: int = 1000
    
    # Dias para manter episódios
    retention_days: int = 90
    
    # Número de episódios similares a buscar
    similar_episodes_count: int = 5
    
    # Threshold para episódios similares
    similarity_threshold: float = 0.7
    
    # Habilitar aprendizado de padrões
    enable_pattern_learning: bool = True


@dataclass
class EmbeddingConfig:
    """Configuração de embeddings."""
    
    # API Key do OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    # Modelo
    model: str = "text-embedding-3-large"
    
    # Dimensões
    dimensions: int = 3072
    
    # Batch size
    batch_size: int = 100
    
    # Cache de embeddings
    cache_embeddings: bool = True
    cache_ttl: int = 86400


@dataclass
class MemoryConfig:
    """Configuração principal do sistema de memória."""
    
    # Databases
    redis: RedisConfig = field(default_factory=RedisConfig)
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    
    # Memory stores
    short_term: ShortTermConfig = field(default_factory=ShortTermConfig)
    long_term: LongTermConfig = field(default_factory=LongTermConfig)
    episodic: EpisodicConfig = field(default_factory=EpisodicConfig)
    
    # Embedding
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Comportamento global
    enable_auto_promotion: bool = True
    enable_auto_consolidation: bool = True
    enable_decay: bool = True
    
    # Logging
    log_memory_operations: bool = True


# Singleton
_memory_config: Optional[MemoryConfig] = None


def get_memory_config() -> MemoryConfig:
    """Retorna a configuração de memória global."""
    global _memory_config
    if _memory_config is None:
        _memory_config = MemoryConfig()
    return _memory_config


def set_memory_config(config: MemoryConfig) -> None:
    """Define a configuração de memória global."""
    global _memory_config
    _memory_config = config

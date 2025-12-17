"""
RAG v2 Configuration

Configuração centralizada para o sistema RAG avançado.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from enum import Enum
import os


class EmbeddingModel(str, Enum):
    """Modelos de embedding disponíveis."""
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class RetrievalMethod(str, Enum):
    """Métodos de retrieval disponíveis."""
    VECTOR = "vector"
    GRAPH = "graph"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class RerankModel(str, Enum):
    """Modelos de reranking disponíveis."""
    COHERE_RERANK_V3 = "rerank-english-v3.0"
    COHERE_RERANK_MULTILINGUAL = "rerank-multilingual-v3.0"
    BGE_RERANKER = "bge-reranker-large"


@dataclass
class DatabaseConfig:
    """Configuração de banco de dados."""
    
    # PostgreSQL
    postgres_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    postgres_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    postgres_db: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "agno_rag"))
    
    # Neo4j
    neo4j_uri: str = field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))
    
    # Redis
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    
    @property
    def postgres_url(self) -> str:
        """URL de conexão PostgreSQL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_async_url(self) -> str:
        """URL de conexão PostgreSQL assíncrona."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """URL de conexão Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@dataclass
class EmbeddingConfig:
    """Configuração de embeddings."""
    
    model: EmbeddingModel = EmbeddingModel.TEXT_EMBEDDING_3_LARGE
    dimensions: int = 3072  # 3072 para large, 1536 para small
    batch_size: int = 100
    max_retries: int = 3
    timeout: int = 30
    
    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    def __post_init__(self):
        """Ajusta dimensões baseado no modelo."""
        if self.model == EmbeddingModel.TEXT_EMBEDDING_3_SMALL:
            self.dimensions = 1536
        elif self.model == EmbeddingModel.TEXT_EMBEDDING_3_LARGE:
            self.dimensions = 3072
        elif self.model == EmbeddingModel.TEXT_EMBEDDING_ADA_002:
            self.dimensions = 1536


@dataclass
class ChunkingConfig:
    """Configuração de chunking de documentos."""
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    
    # Separadores para chunking semântico
    separators: list[str] = field(default_factory=lambda: [
        "\n\n",
        "\n",
        ". ",
        "! ",
        "? ",
        "; ",
        ", ",
        " ",
        ""
    ])
    
    # Chunking semântico
    use_semantic_chunking: bool = True
    semantic_threshold: float = 0.7


@dataclass
class RetrievalConfig:
    """Configuração de retrieval."""
    
    method: RetrievalMethod = RetrievalMethod.HYBRID
    top_k: int = 20  # Documentos iniciais
    top_n: int = 5   # Documentos após reranking
    
    # Pesos para hybrid search
    vector_weight: float = 0.5
    graph_weight: float = 0.3
    keyword_weight: float = 0.2
    
    # Threshold de similaridade
    similarity_threshold: float = 0.5
    
    # Reciprocal Rank Fusion
    rrf_k: int = 60


@dataclass
class RerankConfig:
    """Configuração de reranking."""
    
    enabled: bool = True
    model: RerankModel = RerankModel.COHERE_RERANK_V3
    top_n: int = 5
    
    # Cohere
    cohere_api_key: str = field(default_factory=lambda: os.getenv("COHERE_API_KEY", ""))
    
    # Fallback local
    use_fallback: bool = True
    fallback_model: str = "BAAI/bge-reranker-large"


@dataclass
class QueryConfig:
    """Configuração de processamento de queries."""
    
    # Query expansion
    enable_expansion: bool = True
    expansion_count: int = 3
    
    # HyDE (Hypothetical Document Embeddings)
    enable_hyde: bool = True
    hyde_model: str = "gpt-4o-mini"
    
    # Step-back prompting
    enable_step_back: bool = True
    
    # Query decomposition
    enable_decomposition: bool = True
    max_sub_queries: int = 3


@dataclass
class CacheConfig:
    """Configuração de cache."""
    
    enabled: bool = True
    ttl: int = 3600  # 1 hora
    max_size: int = 10000
    
    # Cache de embeddings
    cache_embeddings: bool = True
    embedding_ttl: int = 86400  # 24 horas
    
    # Cache de queries
    cache_queries: bool = True
    query_ttl: int = 3600


@dataclass
class RAGConfig:
    """Configuração principal do RAG v2."""
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    query: QueryConfig = field(default_factory=QueryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # LLM para geração
    llm_model: str = field(default_factory=lambda: os.getenv("RAG_LLM_MODEL", "gpt-4o-mini"))
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    
    # Contexto
    max_context_tokens: int = 8000
    include_sources: bool = True


# Singleton global
_rag_config: Optional[RAGConfig] = None


def get_rag_config() -> RAGConfig:
    """Retorna a configuração RAG global."""
    global _rag_config
    if _rag_config is None:
        _rag_config = RAGConfig()
    return _rag_config


def set_rag_config(config: RAGConfig) -> None:
    """Define a configuração RAG global."""
    global _rag_config
    _rag_config = config

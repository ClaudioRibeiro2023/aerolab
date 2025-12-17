"""
RAG v2 - Sistema de Retrieval-Augmented Generation Avançado

Este módulo implementa um sistema RAG completo com:
- Hybrid Search (Vector + Graph + Keyword)
- Reranking com Cohere
- Query Processing avançado
- Contextual Compression

Arquitetura:
    Query → Decomposition → Hybrid Search → Reranking → Generation
             (Vector + Graph + Keyword)    (Cohere)
"""

from .config import RAGConfig, get_rag_config
from .embeddings import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, get_vector_store
from .graph_store import GraphStore, get_graph_store
from .reranker import Reranker, get_reranker
from .query_processor import QueryProcessor, get_query_processor
from .pipeline import RAGPipeline, get_rag_pipeline
from .ingestion import IngestionPipeline, get_ingestion_pipeline

__all__ = [
    # Config
    "RAGConfig",
    "get_rag_config",
    # Embeddings
    "EmbeddingService",
    "get_embedding_service",
    # Stores
    "VectorStore",
    "get_vector_store",
    "GraphStore",
    "get_graph_store",
    # Reranker
    "Reranker",
    "get_reranker",
    # Query Processing
    "QueryProcessor",
    "get_query_processor",
    # Pipeline
    "RAGPipeline",
    "get_rag_pipeline",
    # Ingestion
    "IngestionPipeline",
    "get_ingestion_pipeline",
]

__version__ = "2.0.0"

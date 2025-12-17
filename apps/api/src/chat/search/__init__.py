"""
Search - Busca web e RAG para chat.

Features:
- Web search em tempo real
- RAG com knowledge base
- Citations automáticas
- Fact checking
"""

from .web_search import WebSearcher, SearchResult
from .rag_search import RAGSearcher
from .citations import CitationManager

__all__ = [
    "WebSearcher",
    "SearchResult",
    "RAGSearcher",
    "CitationManager",
]

"""
Citations - Gerenciamento de citações e fontes.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citação/fonte."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    url: Optional[str] = None
    snippet: str = ""
    source_type: str = "web"  # web, rag, file
    relevance_score: float = 0.0
    
    # Para inline citations
    marker: str = ""  # [1], [2], etc.
    start_pos: int = 0
    end_pos: int = 0
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_type": self.source_type,
            "relevance_score": self.relevance_score,
            "marker": self.marker
        }


class CitationManager:
    """
    Gerenciador de citações.
    
    Responsável por:
    - Extrair citações de respostas
    - Formatar citações inline
    - Gerar lista de referências
    """
    
    def __init__(self):
        self._citations: Dict[str, List[Citation]] = {}  # message_id -> citations
    
    def extract_citations(
        self,
        content: str,
        sources: List[Dict]
    ) -> tuple[str, List[Citation]]:
        """
        Extrai e formata citações em um texto.
        
        Args:
            content: Conteúdo com marcadores de citação
            sources: Fontes disponíveis
            
        Returns:
            (content formatado, lista de citações)
        """
        citations = []
        
        # Criar citações das fontes
        for i, source in enumerate(sources, 1):
            citation = Citation(
                title=source.get("title", ""),
                url=source.get("url"),
                snippet=source.get("snippet", "")[:200],
                source_type=source.get("source_type", "web"),
                relevance_score=source.get("relevance_score", 0.0),
                marker=f"[{i}]"
            )
            citations.append(citation)
        
        return content, citations
    
    def add_inline_citations(
        self,
        content: str,
        citations: List[Citation]
    ) -> str:
        """
        Adiciona marcadores de citação inline.
        
        Formato: "texto citado[1] mais texto[2]"
        """
        # Em produção: usar NLP para identificar claims e adicionar citações
        # Por agora, retorna conteúdo original
        return content
    
    def format_references(
        self,
        citations: List[Citation],
        format: str = "markdown"
    ) -> str:
        """
        Formata lista de referências.
        
        Args:
            citations: Lista de citações
            format: Formato (markdown, html, plain)
            
        Returns:
            String formatada
        """
        if not citations:
            return ""
        
        if format == "markdown":
            lines = ["\n---\n**Sources:**\n"]
            for c in citations:
                if c.url:
                    lines.append(f"{c.marker} [{c.title}]({c.url})")
                else:
                    lines.append(f"{c.marker} {c.title}")
            return "\n".join(lines)
        
        elif format == "html":
            items = []
            for c in citations:
                if c.url:
                    items.append(f'<li><a href="{c.url}">{c.title}</a></li>')
                else:
                    items.append(f'<li>{c.title}</li>')
            return f'<h4>Sources</h4><ol>{"".join(items)}</ol>'
        
        else:  # plain
            lines = ["\nSources:"]
            for c in citations:
                lines.append(f"{c.marker} {c.title}: {c.url or 'N/A'}")
            return "\n".join(lines)
    
    def store_citations(
        self,
        message_id: str,
        citations: List[Citation]
    ) -> None:
        """Armazena citações de uma mensagem."""
        self._citations[message_id] = citations
    
    def get_citations(self, message_id: str) -> List[Citation]:
        """Obtém citações de uma mensagem."""
        return self._citations.get(message_id, [])
    
    def merge_citations(
        self,
        citations_a: List[Citation],
        citations_b: List[Citation]
    ) -> List[Citation]:
        """Combina listas de citações removendo duplicatas."""
        seen_urls = set()
        merged = []
        
        for c in citations_a + citations_b:
            key = c.url or c.title
            if key not in seen_urls:
                seen_urls.add(key)
                merged.append(c)
        
        # Renumerar markers
        for i, c in enumerate(merged, 1):
            c.marker = f"[{i}]"
        
        return merged


# Singleton
_citation_manager: Optional[CitationManager] = None


def get_citation_manager() -> CitationManager:
    global _citation_manager
    if _citation_manager is None:
        _citation_manager = CitationManager()
    return _citation_manager

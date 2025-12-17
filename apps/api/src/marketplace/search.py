"""
Marketplace Search - Busca no Marketplace

Sistema de busca com ranking e filtros.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from collections import defaultdict
import re

from .types import Listing, ListingType, ListingCategory, ListingStatus


@dataclass
class SearchResult:
    """Resultado de busca."""
    listing: Listing
    score: float
    highlights: Dict[str, List[str]] = field(default_factory=dict)


class MarketplaceSearch:
    """
    Motor de busca do marketplace.
    
    Features:
    - Busca por texto
    - Filtros por tipo, categoria, preço
    - Ranking por relevância
    - Highlights de matches
    """
    
    def __init__(self, marketplace=None):
        """
        Args:
            marketplace: Instância do Marketplace
        """
        from .marketplace import get_marketplace
        self._marketplace = marketplace or get_marketplace()
    
    def search(
        self,
        query: str,
        type: Optional[ListingType] = None,
        category: Optional[ListingCategory] = None,
        is_free: Optional[bool] = None,
        min_rating: Optional[float] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "relevance",  # relevance, downloads, rating, newest
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Busca no marketplace.
        
        Args:
            query: Texto de busca
            type: Filtrar por tipo
            category: Filtrar por categoria
            is_free: Filtrar por gratuito
            min_rating: Rating mínimo
            tags: Filtrar por tags
            sort_by: Ordenação
            limit: Número máximo
            offset: Offset para paginação
            
        Returns:
            Resultados da busca
        """
        results: List[SearchResult] = []
        
        # Normalizar query
        query_lower = query.lower().strip()
        query_terms = query_lower.split()
        
        for listing in self._marketplace._listings.values():
            # Apenas publicados
            if listing.status != ListingStatus.PUBLISHED:
                continue
            
            # Aplicar filtros
            if type and listing.type != type:
                continue
            if category and listing.category != category:
                continue
            if is_free is not None and listing.is_free != is_free:
                continue
            if min_rating and listing.rating < min_rating:
                continue
            if tags and not any(t in listing.tags for t in tags):
                continue
            
            # Calcular score
            score, highlights = self._calculate_score(listing, query_terms)
            
            if score > 0 or not query:
                results.append(SearchResult(
                    listing=listing,
                    score=score,
                    highlights=highlights
                ))
        
        # Ordenar resultados
        results = self._sort_results(results, sort_by, bool(query))
        
        # Paginar
        total = len(results)
        results = results[offset:offset + limit]
        
        return {
            "query": query,
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": [
                {
                    **r.listing.to_summary(),
                    "score": r.score,
                    "highlights": r.highlights
                }
                for r in results
            ],
            "filters_applied": {
                "type": type.value if type else None,
                "category": category.value if category else None,
                "is_free": is_free,
                "min_rating": min_rating,
                "tags": tags
            }
        }
    
    def _calculate_score(
        self,
        listing: Listing,
        query_terms: List[str]
    ) -> tuple:
        """
        Calcula score de relevância.
        
        Args:
            listing: Listing a avaliar
            query_terms: Termos da busca
            
        Returns:
            (score, highlights)
        """
        score = 0
        highlights = defaultdict(list)
        
        if not query_terms:
            # Sem query, usar popularidade como score
            return listing.downloads / 1000, {}
        
        name_lower = listing.name.lower()
        desc_lower = listing.description.lower()
        short_desc_lower = listing.short_description.lower()
        tags_lower = [t.lower() for t in listing.tags]
        
        for term in query_terms:
            # Match no nome (peso alto)
            if term in name_lower:
                score += 10
                highlights["name"].append(term)
            
            # Match exato no nome
            if term == name_lower.replace(" ", "-"):
                score += 20
            
            # Match na descrição curta
            if term in short_desc_lower:
                score += 5
                highlights["short_description"].append(term)
            
            # Match na descrição
            if term in desc_lower:
                score += 2
                highlights["description"].append(term)
            
            # Match em tags
            for tag in tags_lower:
                if term in tag:
                    score += 8
                    highlights["tags"].append(term)
        
        # Bonus por popularidade
        score += min(listing.downloads / 1000, 5)
        
        # Bonus por rating
        score += listing.rating
        
        # Bonus por verificado
        if listing.is_verified:
            score += 2
        
        # Bonus por featured
        if listing.is_featured:
            score += 3
        
        return score, dict(highlights)
    
    def _sort_results(
        self,
        results: List[SearchResult],
        sort_by: str,
        has_query: bool
    ) -> List[SearchResult]:
        """
        Ordena resultados.
        
        Args:
            results: Lista de resultados
            sort_by: Critério de ordenação
            has_query: Se tem query de busca
            
        Returns:
            Lista ordenada
        """
        if sort_by == "relevance" and has_query:
            results.sort(key=lambda r: r.score, reverse=True)
        elif sort_by == "downloads":
            results.sort(key=lambda r: r.listing.downloads, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda r: (r.listing.rating, r.listing.review_count), reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda r: r.listing.created_at, reverse=True)
        elif sort_by == "price_low":
            results.sort(key=lambda r: r.listing.price)
        elif sort_by == "price_high":
            results.sort(key=lambda r: r.listing.price, reverse=True)
        else:
            # Default: combinar score e downloads
            results.sort(key=lambda r: r.score + r.listing.downloads/100, reverse=True)
        
        return results
    
    def suggest(self, query: str, limit: int = 5) -> List[str]:
        """
        Sugere termos de busca.
        
        Args:
            query: Query parcial
            limit: Número máximo de sugestões
            
        Returns:
            Lista de sugestões
        """
        query_lower = query.lower().strip()
        if len(query_lower) < 2:
            return []
        
        suggestions = set()
        
        for listing in self._marketplace._listings.values():
            if listing.status != ListingStatus.PUBLISHED:
                continue
            
            # Sugerir nomes
            if query_lower in listing.name.lower():
                suggestions.add(listing.name)
            
            # Sugerir tags
            for tag in listing.tags:
                if query_lower in tag.lower():
                    suggestions.add(tag)
        
        return list(suggestions)[:limit]
    
    def get_trending(self, days: int = 7, limit: int = 10) -> List[Listing]:
        """
        Obtém listings em alta.
        
        Args:
            days: Período em dias
            limit: Número máximo
            
        Returns:
            Lista de listings trending
        """
        # Simplificado: usar downloads como proxy
        listings = [
            l for l in self._marketplace._listings.values()
            if l.status == ListingStatus.PUBLISHED
        ]
        
        listings.sort(key=lambda l: l.downloads, reverse=True)
        return listings[:limit]
    
    def get_related(
        self,
        listing_id: str,
        limit: int = 5
    ) -> List[Listing]:
        """
        Obtém listings relacionados.
        
        Args:
            listing_id: ID do listing base
            limit: Número máximo
            
        Returns:
            Lista de listings relacionados
        """
        base = self._marketplace.get_listing(listing_id)
        if not base:
            return []
        
        related = []
        
        for listing in self._marketplace._listings.values():
            if listing.id == listing_id:
                continue
            if listing.status != ListingStatus.PUBLISHED:
                continue
            
            # Calcular similaridade
            similarity = 0
            
            # Mesmo tipo
            if listing.type == base.type:
                similarity += 5
            
            # Mesma categoria
            if listing.category == base.category:
                similarity += 3
            
            # Tags em comum
            common_tags = set(listing.tags) & set(base.tags)
            similarity += len(common_tags) * 2
            
            if similarity > 0:
                related.append((listing, similarity))
        
        # Ordenar por similaridade
        related.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in related[:limit]]
    
    def get_filters(self) -> Dict[str, Any]:
        """
        Obtém opções de filtros disponíveis.
        
        Returns:
            Opções de filtros
        """
        types = defaultdict(int)
        categories = defaultdict(int)
        tags = defaultdict(int)
        price_ranges = {"free": 0, "paid": 0}
        
        for listing in self._marketplace._listings.values():
            if listing.status != ListingStatus.PUBLISHED:
                continue
            
            types[listing.type.value] += 1
            categories[listing.category.value] += 1
            
            for tag in listing.tags:
                tags[tag] += 1
            
            if listing.is_free:
                price_ranges["free"] += 1
            else:
                price_ranges["paid"] += 1
        
        # Top tags
        top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "types": dict(types),
            "categories": dict(categories),
            "tags": [{"name": t[0], "count": t[1]} for t in top_tags],
            "price_ranges": price_ranges
        }

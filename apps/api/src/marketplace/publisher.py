"""
Publisher - Publicação no Marketplace

Gerencia publicação de itens no marketplace.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .types import (
    Listing, ListingType, ListingStatus, ListingCategory,
    ListingVersion
)


class Publisher:
    """
    Serviço para publicação no marketplace.
    
    Features:
    - Criação e edição de listings
    - Gerenciamento de versões
    - Submissão para review
    - Analytics de publisher
    """
    
    def __init__(self, marketplace=None):
        """
        Args:
            marketplace: Instância do Marketplace
        """
        from .marketplace import get_marketplace
        self._marketplace = marketplace or get_marketplace()
        self._pending_reviews: Dict[str, Listing] = {}
    
    def create_listing(
        self,
        author_id: str,
        author_name: str,
        name: str,
        description: str,
        type: ListingType,
        category: ListingCategory,
        short_description: str = "",
        tags: List[str] = None,
        price: int = 0,
        icon_url: Optional[str] = None,
        documentation_url: Optional[str] = None,
        repository_url: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Listing:
        """
        Cria novo listing (draft).
        
        Args:
            author_id: ID do autor
            author_name: Nome do autor
            name: Nome do listing
            description: Descrição completa
            type: Tipo do listing
            category: Categoria
            short_description: Descrição curta
            tags: Tags
            price: Preço em centavos
            icon_url: URL do ícone
            documentation_url: URL da documentação
            repository_url: URL do repositório
            organization_id: ID da organização
            
        Returns:
            Listing criado (draft)
        """
        listing = Listing(
            name=name,
            description=description,
            short_description=short_description or description[:100],
            type=type,
            category=category,
            tags=tags or [],
            author_id=author_id,
            author_name=author_name,
            organization_id=organization_id,
            price=price,
            icon_url=icon_url,
            documentation_url=documentation_url,
            repository_url=repository_url,
            status=ListingStatus.DRAFT
        )
        
        # Salvar no marketplace
        self._marketplace._listings[listing.id] = listing
        
        return listing
    
    def update_listing(
        self,
        listing_id: str,
        author_id: str,
        **updates
    ) -> Optional[Listing]:
        """
        Atualiza um listing existente.
        
        Args:
            listing_id: ID do listing
            author_id: ID do autor (para verificação)
            **updates: Campos a atualizar
            
        Returns:
            Listing atualizado ou None
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing:
            return None
        
        # Verificar autoria
        if listing.author_id != author_id:
            return None
        
        # Campos que podem ser atualizados
        allowed_fields = {
            "name", "description", "short_description", "tags",
            "price", "icon_url", "banner_url", "documentation_url",
            "repository_url", "requirements", "dependencies", "category"
        }
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(listing, field):
                setattr(listing, field, value)
        
        listing.updated_at = datetime.now()
        
        return listing
    
    def add_version(
        self,
        listing_id: str,
        author_id: str,
        version: str,
        changelog: str,
        config: Optional[dict] = None,
        download_url: Optional[str] = None
    ) -> Optional[ListingVersion]:
        """
        Adiciona nova versão a um listing.
        
        Args:
            listing_id: ID do listing
            author_id: ID do autor
            version: Número da versão (semver)
            changelog: Descrição das mudanças
            config: Configuração da versão
            download_url: URL para download
            
        Returns:
            ListingVersion criada
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing or listing.author_id != author_id:
            return None
        
        # Criar versão
        version_obj = ListingVersion(
            version=version,
            changelog=changelog,
            config=config or {},
            download_url=download_url
        )
        
        listing.add_version(version_obj)
        
        return version_obj
    
    def submit_for_review(
        self,
        listing_id: str,
        author_id: str
    ) -> bool:
        """
        Submete listing para review.
        
        Args:
            listing_id: ID do listing
            author_id: ID do autor
            
        Returns:
            True se submetido com sucesso
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing or listing.author_id != author_id:
            return False
        
        if listing.status not in [ListingStatus.DRAFT, ListingStatus.SUSPENDED]:
            return False
        
        # Validar listing
        validation = self.validate_listing(listing)
        if not validation["valid"]:
            return False
        
        listing.status = ListingStatus.PENDING_REVIEW
        self._pending_reviews[listing_id] = listing
        
        return True
    
    def validate_listing(self, listing: Listing) -> Dict[str, Any]:
        """
        Valida listing antes da publicação.
        
        Args:
            listing: Listing a validar
            
        Returns:
            Resultado da validação
        """
        errors = []
        warnings = []
        
        # Campos obrigatórios
        if not listing.name or len(listing.name) < 3:
            errors.append("Name must be at least 3 characters")
        
        if not listing.description or len(listing.description) < 50:
            errors.append("Description must be at least 50 characters")
        
        if not listing.short_description:
            warnings.append("Short description is recommended")
        
        if not listing.tags:
            warnings.append("Tags help users find your listing")
        
        if not listing.versions:
            errors.append("At least one version is required")
        
        if not listing.icon_url:
            warnings.append("An icon improves visibility")
        
        # Verificar slug único
        existing = self._marketplace.get_listing_by_slug(listing.slug)
        if existing and existing.id != listing.id:
            errors.append("Slug already exists")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def publish(
        self,
        listing_id: str,
        reviewer_id: str = "system"
    ) -> bool:
        """
        Publica um listing (após review).
        
        Args:
            listing_id: ID do listing
            reviewer_id: ID do reviewer
            
        Returns:
            True se publicado com sucesso
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing:
            return False
        
        if listing.status != ListingStatus.PENDING_REVIEW:
            return False
        
        listing.status = ListingStatus.PUBLISHED
        listing.published_at = datetime.now()
        
        if listing_id in self._pending_reviews:
            del self._pending_reviews[listing_id]
        
        return True
    
    def unpublish(
        self,
        listing_id: str,
        author_id: str,
        reason: str = ""
    ) -> bool:
        """
        Remove listing do marketplace.
        
        Args:
            listing_id: ID do listing
            author_id: ID do autor
            reason: Motivo
            
        Returns:
            True se removido com sucesso
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing or listing.author_id != author_id:
            return False
        
        listing.status = ListingStatus.DRAFT
        listing.metadata["unpublish_reason"] = reason
        listing.metadata["unpublished_at"] = datetime.now().isoformat()
        
        return True
    
    def deprecate(
        self,
        listing_id: str,
        author_id: str,
        replacement_id: Optional[str] = None,
        message: str = ""
    ) -> bool:
        """
        Marca listing como deprecado.
        
        Args:
            listing_id: ID do listing
            author_id: ID do autor
            replacement_id: ID do substituto
            message: Mensagem de deprecação
            
        Returns:
            True se deprecado com sucesso
        """
        listing = self._marketplace.get_listing(listing_id)
        if not listing or listing.author_id != author_id:
            return False
        
        listing.status = ListingStatus.DEPRECATED
        listing.metadata["deprecated_at"] = datetime.now().isoformat()
        listing.metadata["deprecation_message"] = message
        if replacement_id:
            listing.metadata["replacement_id"] = replacement_id
        
        return True
    
    def get_author_listings(
        self,
        author_id: str,
        include_drafts: bool = True
    ) -> List[Listing]:
        """
        Lista todos os listings de um autor.
        
        Args:
            author_id: ID do autor
            include_drafts: Incluir drafts
            
        Returns:
            Lista de listings
        """
        results = []
        
        for listing in self._marketplace._listings.values():
            if listing.author_id != author_id:
                continue
            
            if not include_drafts and listing.status == ListingStatus.DRAFT:
                continue
            
            results.append(listing)
        
        return results
    
    def get_publisher_stats(self, author_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas do publisher.
        
        Args:
            author_id: ID do autor
            
        Returns:
            Estatísticas
        """
        listings = self.get_author_listings(author_id)
        
        total_downloads = sum(l.downloads for l in listings)
        total_installs = sum(l.installs for l in listings)
        total_reviews = sum(l.review_count for l in listings)
        
        avg_rating = 0
        rated_count = len([l for l in listings if l.review_count > 0])
        if rated_count > 0:
            avg_rating = sum(l.rating for l in listings if l.review_count > 0) / rated_count
        
        # Revenue (simplificado)
        total_revenue = sum(
            l.price * l.installs 
            for l in listings 
            if not l.is_free
        )
        
        return {
            "author_id": author_id,
            "total_listings": len(listings),
            "published": len([l for l in listings if l.status == ListingStatus.PUBLISHED]),
            "drafts": len([l for l in listings if l.status == ListingStatus.DRAFT]),
            "total_downloads": total_downloads,
            "total_installs": total_installs,
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 2),
            "estimated_revenue": total_revenue / 100  # Em dólares
        }


# Singleton instance
_publisher: Optional[Publisher] = None


def get_publisher() -> Publisher:
    """Obtém instância singleton do Publisher."""
    global _publisher
    if _publisher is None:
        _publisher = Publisher()
    return _publisher

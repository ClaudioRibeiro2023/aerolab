"""
Marketplace - Serviço Principal

Gerencia operações do marketplace.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from .types import (
    Listing, ListingType, ListingStatus, ListingCategory,
    ListingVersion, Review, Installation
)


class Marketplace:
    """
    Serviço principal do marketplace.
    
    Features:
    - Listagem e busca de itens
    - Instalação e gerenciamento
    - Reviews e ratings
    - Analytics
    """
    
    def __init__(self):
        """Inicializa marketplace."""
        self._listings: Dict[str, Listing] = {}
        self._reviews: Dict[str, List[Review]] = defaultdict(list)
        self._installations: Dict[str, List[Installation]] = defaultdict(list)
        self._user_installations: Dict[str, List[str]] = defaultdict(list)
        
        # Carregar itens de exemplo
        self._load_sample_listings()
    
    def _load_sample_listings(self) -> None:
        """Carrega listings de exemplo."""
        
        # Customer Support Agent
        self._listings["cs-agent-001"] = Listing(
            id="cs-agent-001",
            name="Customer Support Agent",
            slug="customer-support-agent",
            description="AI-powered customer support agent with multi-language support, sentiment analysis, and automatic ticket routing.",
            short_description="Intelligent customer support automation",
            type=ListingType.AGENT,
            category=ListingCategory.CUSTOMER_SERVICE,
            tags=["support", "customer-service", "multilingual", "sentiment"],
            author_id="official",
            author_name="Agno Team",
            price=0,
            downloads=5420,
            installs=3210,
            rating=4.8,
            review_count=128,
            status=ListingStatus.PUBLISHED,
            is_featured=True,
            is_verified=True,
            current_version="2.1.0",
            versions=[
                ListingVersion(version="2.1.0", changelog="Added multilingual support"),
                ListingVersion(version="2.0.0", changelog="Complete rewrite with new AI model"),
                ListingVersion(version="1.0.0", changelog="Initial release")
            ],
            icon_url="/icons/customer-support.png",
            documentation_url="https://docs.agno.ai/agents/customer-support"
        )
        
        # RAG Q&A Template
        self._listings["rag-qa-001"] = Listing(
            id="rag-qa-001",
            name="RAG Q&A System",
            slug="rag-qa-system",
            description="Complete RAG-based question answering system with document ingestion, vector search, and contextual responses.",
            short_description="Document-based Q&A with RAG",
            type=ListingType.TEMPLATE,
            category=ListingCategory.PRODUCTIVITY,
            tags=["rag", "qa", "documents", "knowledge-base"],
            author_id="official",
            author_name="Agno Team",
            price=0,
            downloads=3890,
            installs=2450,
            rating=4.9,
            review_count=89,
            status=ListingStatus.PUBLISHED,
            is_featured=True,
            is_verified=True,
            current_version="1.2.0"
        )
        
        # Slack Integration
        self._listings["slack-int-001"] = Listing(
            id="slack-int-001",
            name="Slack Integration",
            slug="slack-integration",
            description="Connect your agents to Slack channels. Receive messages, respond automatically, and manage conversations.",
            short_description="Connect agents to Slack",
            type=ListingType.INTEGRATION,
            category=ListingCategory.PRODUCTIVITY,
            tags=["slack", "chat", "messaging", "integration"],
            author_id="official",
            author_name="Agno Team",
            price=0,
            downloads=8920,
            installs=6780,
            rating=4.7,
            review_count=234,
            status=ListingStatus.PUBLISHED,
            is_verified=True,
            current_version="3.0.1"
        )
        
        # Sales Assistant Agent
        self._listings["sales-agent-001"] = Listing(
            id="sales-agent-001",
            name="Sales Assistant Pro",
            slug="sales-assistant-pro",
            description="AI sales assistant that qualifies leads, schedules demos, and provides product information to prospects.",
            short_description="AI-powered sales qualification",
            type=ListingType.AGENT,
            category=ListingCategory.SALES,
            tags=["sales", "leads", "qualification", "demos"],
            author_id="partner-001",
            author_name="SalesAI Inc.",
            price=2999,  # $29.99
            downloads=1250,
            installs=890,
            rating=4.6,
            review_count=45,
            status=ListingStatus.PUBLISHED,
            is_verified=True,
            current_version="1.5.0"
        )
        
        # Code Review Tool
        self._listings["code-review-001"] = Listing(
            id="code-review-001",
            name="AI Code Reviewer",
            slug="ai-code-reviewer",
            description="Automated code review tool that analyzes code quality, suggests improvements, and identifies bugs.",
            short_description="AI-powered code review",
            type=ListingType.TOOL,
            category=ListingCategory.DEVELOPMENT,
            tags=["code", "review", "quality", "bugs", "development"],
            author_id="partner-002",
            author_name="DevTools Co.",
            price=1999,  # $19.99
            downloads=2340,
            installs=1560,
            rating=4.5,
            review_count=67,
            status=ListingStatus.PUBLISHED,
            current_version="2.0.0"
        )
    
    # === Listing Operations ===
    
    def get_listing(self, listing_id: str) -> Optional[Listing]:
        """Obtém listing pelo ID."""
        return self._listings.get(listing_id)
    
    def get_listing_by_slug(self, slug: str) -> Optional[Listing]:
        """Obtém listing pelo slug."""
        for listing in self._listings.values():
            if listing.slug == slug:
                return listing
        return None
    
    def list_all(
        self,
        type: Optional[ListingType] = None,
        category: Optional[ListingCategory] = None,
        is_free: Optional[bool] = None,
        is_featured: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Listing]:
        """
        Lista itens do marketplace.
        
        Args:
            type: Filtrar por tipo
            category: Filtrar por categoria
            is_free: Filtrar por gratuito
            is_featured: Apenas destacados
            limit: Número máximo
            offset: Offset para paginação
            
        Returns:
            Lista de listings
        """
        results = []
        
        for listing in self._listings.values():
            # Apenas publicados
            if listing.status != ListingStatus.PUBLISHED:
                continue
            
            # Filtros
            if type and listing.type != type:
                continue
            if category and listing.category != category:
                continue
            if is_free is not None and listing.is_free != is_free:
                continue
            if is_featured and not listing.is_featured:
                continue
            
            results.append(listing)
        
        # Ordenar por downloads
        results.sort(key=lambda x: x.downloads, reverse=True)
        
        return results[offset:offset + limit]
    
    def get_featured(self, limit: int = 6) -> List[Listing]:
        """Obtém listings em destaque."""
        return self.list_all(is_featured=True, limit=limit)
    
    def get_popular(self, type: Optional[ListingType] = None, limit: int = 10) -> List[Listing]:
        """Obtém listings mais populares."""
        listings = self.list_all(type=type, limit=100)
        listings.sort(key=lambda x: x.downloads, reverse=True)
        return listings[:limit]
    
    def get_top_rated(self, type: Optional[ListingType] = None, limit: int = 10) -> List[Listing]:
        """Obtém listings melhor avaliados."""
        listings = self.list_all(type=type, limit=100)
        listings.sort(key=lambda x: (x.rating, x.review_count), reverse=True)
        return listings[:limit]
    
    def get_categories(self) -> Dict[str, int]:
        """Obtém contagem por categoria."""
        counts = defaultdict(int)
        for listing in self._listings.values():
            if listing.status == ListingStatus.PUBLISHED:
                counts[listing.category.value] += 1
        return dict(counts)
    
    # === Installation Operations ===
    
    def install(
        self,
        listing_id: str,
        user_id: str,
        version: Optional[str] = None
    ) -> Optional[Installation]:
        """
        Instala um listing para um usuário.
        
        Args:
            listing_id: ID do listing
            user_id: ID do usuário
            version: Versão específica (default: atual)
            
        Returns:
            Installation criada
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return None
        
        # Verificar se já instalado
        for inst in self._installations[listing_id]:
            if inst.user_id == user_id and inst.is_active:
                return inst  # Já instalado
        
        # Criar instalação
        installation = Installation(
            listing_id=listing_id,
            user_id=user_id,
            version=version or listing.current_version
        )
        
        # Salvar
        self._installations[listing_id].append(installation)
        self._user_installations[user_id].append(listing_id)
        
        # Atualizar contadores
        listing.installs += 1
        listing.downloads += 1
        
        return installation
    
    def uninstall(self, listing_id: str, user_id: str) -> bool:
        """
        Desinstala um listing.
        
        Args:
            listing_id: ID do listing
            user_id: ID do usuário
            
        Returns:
            True se desinstalado com sucesso
        """
        for inst in self._installations[listing_id]:
            if inst.user_id == user_id and inst.is_active:
                inst.is_active = False
                inst.uninstalled_at = datetime.now()
                
                if listing_id in self._user_installations[user_id]:
                    self._user_installations[user_id].remove(listing_id)
                
                return True
        
        return False
    
    def get_user_installations(self, user_id: str) -> List[Listing]:
        """Obtém listings instalados por um usuário."""
        listing_ids = self._user_installations.get(user_id, [])
        return [self._listings[lid] for lid in listing_ids if lid in self._listings]
    
    def is_installed(self, listing_id: str, user_id: str) -> bool:
        """Verifica se listing está instalado."""
        return listing_id in self._user_installations.get(user_id, [])
    
    # === Review Operations ===
    
    def add_review(
        self,
        listing_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        title: str,
        content: str
    ) -> Optional[Review]:
        """
        Adiciona review a um listing.
        
        Args:
            listing_id: ID do listing
            user_id: ID do usuário
            user_name: Nome do usuário
            rating: Nota (1-5)
            title: Título
            content: Conteúdo
            
        Returns:
            Review criada
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return None
        
        # Verificar se é compra verificada
        is_verified = self.is_installed(listing_id, user_id)
        
        review = Review(
            listing_id=listing_id,
            user_id=user_id,
            user_name=user_name,
            rating=min(5, max(1, rating)),
            title=title,
            content=content,
            is_verified_purchase=is_verified
        )
        
        # Salvar
        self._reviews[listing_id].append(review)
        
        # Atualizar rating médio
        all_ratings = [r.rating for r in self._reviews[listing_id]]
        listing.rating = sum(all_ratings) / len(all_ratings)
        listing.review_count = len(all_ratings)
        
        return review
    
    def get_reviews(
        self,
        listing_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Review]:
        """Obtém reviews de um listing."""
        reviews = self._reviews.get(listing_id, [])
        reviews.sort(key=lambda x: x.created_at, reverse=True)
        return reviews[offset:offset + limit]
    
    # === Analytics ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do marketplace."""
        total_listings = len([l for l in self._listings.values() 
                            if l.status == ListingStatus.PUBLISHED])
        total_downloads = sum(l.downloads for l in self._listings.values())
        total_installs = sum(l.installs for l in self._listings.values())
        
        by_type = defaultdict(int)
        for listing in self._listings.values():
            if listing.status == ListingStatus.PUBLISHED:
                by_type[listing.type.value] += 1
        
        return {
            "total_listings": total_listings,
            "total_downloads": total_downloads,
            "total_installs": total_installs,
            "by_type": dict(by_type),
            "categories": self.get_categories()
        }


# Singleton instance
_marketplace: Optional[Marketplace] = None


def get_marketplace() -> Marketplace:
    """Obtém instância singleton do Marketplace."""
    global _marketplace
    if _marketplace is None:
        _marketplace = Marketplace()
    return _marketplace

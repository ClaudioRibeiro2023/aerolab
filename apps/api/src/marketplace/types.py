"""
Marketplace - Tipos e Estruturas de Dados

Define estruturas para o marketplace.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ListingType(str, Enum):
    """Tipo de item no marketplace."""
    AGENT = "agent"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    INTEGRATION = "integration"
    TOOL = "tool"
    PROMPT = "prompt"
    DATASET = "dataset"


class ListingStatus(str, Enum):
    """Status do listing."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class ListingCategory(str, Enum):
    """Categoria do listing."""
    PRODUCTIVITY = "productivity"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    MARKETING = "marketing"
    DEVELOPMENT = "development"
    DATA_ANALYSIS = "data_analysis"
    CONTENT = "content"
    RESEARCH = "research"
    EDUCATION = "education"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    OTHER = "other"


@dataclass
class ListingVersion:
    """
    Versão de um listing.
    """
    version: str
    changelog: str = ""
    download_url: Optional[str] = None
    
    # Compatibilidade
    min_platform_version: str = "1.0.0"
    
    # Conteúdo
    config: dict = field(default_factory=dict)
    
    # Timestamps
    published_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "changelog": self.changelog,
            "download_url": self.download_url,
            "min_platform_version": self.min_platform_version,
            "published_at": self.published_at.isoformat()
        }


@dataclass
class Listing:
    """
    Item listado no marketplace.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificação
    name: str = ""
    slug: str = ""
    description: str = ""
    short_description: str = ""
    
    # Tipo e categoria
    type: ListingType = ListingType.AGENT
    category: ListingCategory = ListingCategory.OTHER
    tags: List[str] = field(default_factory=list)
    
    # Autor
    author_id: str = ""
    author_name: str = ""
    organization_id: Optional[str] = None
    
    # Preço (em centavos, 0 = grátis)
    price: int = 0
    currency: str = "USD"
    is_free: bool = True
    
    # Métricas
    downloads: int = 0
    installs: int = 0
    rating: float = 0.0
    review_count: int = 0
    
    # Status
    status: ListingStatus = ListingStatus.DRAFT
    is_featured: bool = False
    is_verified: bool = False
    
    # Versões
    current_version: str = "1.0.0"
    versions: List[ListingVersion] = field(default_factory=list)
    
    # URLs
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    
    # Requisitos
    requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(" ", "-")
        self.is_free = self.price == 0
    
    def add_version(self, version: ListingVersion) -> None:
        """Adiciona nova versão."""
        self.versions.append(version)
        self.current_version = version.version
        self.updated_at = datetime.now()
    
    def get_version(self, version: str) -> Optional[ListingVersion]:
        """Obtém versão específica."""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "type": self.type.value,
            "category": self.category.value,
            "tags": self.tags,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "price": self.price,
            "is_free": self.is_free,
            "downloads": self.downloads,
            "installs": self.installs,
            "rating": self.rating,
            "review_count": self.review_count,
            "status": self.status.value,
            "is_featured": self.is_featured,
            "is_verified": self.is_verified,
            "current_version": self.current_version,
            "icon_url": self.icon_url,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_summary(self) -> dict:
        """Retorna resumo para listagens."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "short_description": self.short_description,
            "type": self.type.value,
            "category": self.category.value,
            "price": self.price,
            "is_free": self.is_free,
            "rating": self.rating,
            "downloads": self.downloads,
            "icon_url": self.icon_url,
            "is_featured": self.is_featured,
            "is_verified": self.is_verified
        }


@dataclass
class Review:
    """
    Review de um listing.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    listing_id: str = ""
    user_id: str = ""
    user_name: str = ""
    
    # Avaliação
    rating: int = 5  # 1-5
    title: str = ""
    content: str = ""
    
    # Resposta do autor
    author_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    # Status
    is_verified_purchase: bool = False
    is_helpful_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "author_response": self.author_response,
            "is_verified_purchase": self.is_verified_purchase,
            "is_helpful_count": self.is_helpful_count,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Installation:
    """
    Registro de instalação de um listing.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    listing_id: str = ""
    user_id: str = ""
    
    # Versão instalada
    version: str = ""
    
    # Status
    is_active: bool = True
    
    # Configuração do usuário
    user_config: dict = field(default_factory=dict)
    
    # Timestamps
    installed_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    uninstalled_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "user_id": self.user_id,
            "version": self.version,
            "is_active": self.is_active,
            "installed_at": self.installed_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }

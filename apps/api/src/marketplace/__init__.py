"""
Marketplace - Loja de Agentes, Templates e Integrações

Sistema de marketplace para compartilhar e monetizar componentes.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                      Marketplace                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Agents    │  │  Templates  │  │ Integrations│         │
│  │             │  │             │  │             │         │
│  │ - Publish   │  │ - Workflow  │  │ - Connectors│         │
│  │ - Search    │  │   Templates │  │ - APIs      │         │
│  │ - Install   │  │ - Prompts   │  │ - Tools     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                    ┌─────┴─────┐                            │
│                    │  Reviews  │                            │
│                    │ Ratings   │                            │
│                    │ Analytics │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘

Uso:
```python
from marketplace import Marketplace, ListingType

marketplace = Marketplace()

# Publicar agente
listing = marketplace.publish(
    type=ListingType.AGENT,
    name="Customer Support Bot",
    description="AI-powered support agent",
    price=999  # $9.99
)

# Buscar itens
results = marketplace.search("support", type=ListingType.AGENT)

# Instalar item
marketplace.install(listing_id, user_id)
```
"""

from .types import (
    ListingType,
    ListingStatus,
    ListingCategory,
    Listing,
    ListingVersion,
    Review,
    Installation
)
from .marketplace import Marketplace, get_marketplace
from .publisher import Publisher, get_publisher
from .search import MarketplaceSearch

__all__ = [
    # Types
    "ListingType",
    "ListingStatus",
    "ListingCategory",
    "Listing",
    "ListingVersion",
    "Review",
    "Installation",
    # Services
    "Marketplace",
    "get_marketplace",
    "Publisher",
    "get_publisher",
    "MarketplaceSearch"
]

__version__ = "2.0.0"

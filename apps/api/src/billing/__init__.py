"""
Billing System - Sistema de Cobrança e Metering

Implementa controle de uso, pricing e billing para a plataforma.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                     Billing System                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Metering    │  │ Pricing     │  │ Billing     │         │
│  │             │  │             │  │             │         │
│  │ - Tokens    │→│ - Calculate │→│ - Invoice   │         │
│  │ - API Calls │  │ - Discount  │  │ - Payment   │         │
│  │ - Storage   │  │ - Markup    │  │ - History   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │   Plans   │                            │
│                    │  - Free   │                            │
│                    │  - Pro    │                            │
│                    │  - Team   │                            │
│                    │  - Entpr  │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘

Uso:
```python
from billing import BillingManager, MeteringService, PricingEngine

# Metering
metering = MeteringService()
metering.track_tokens(user_id, tokens=1000, model="gpt-4o")
metering.track_api_call(user_id, endpoint="/api/agents/run")

# Pricing
pricing = PricingEngine()
cost = pricing.calculate_cost(usage)

# Billing
billing = BillingManager()
invoice = billing.generate_invoice(user_id, period="monthly")
```
"""

from .types import (
    UsageType,
    UsageRecord,
    UsageSummary,
    PriceTier,
    Plan,
    PlanFeatures,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus
)
from .metering import MeteringService, get_metering_service
from .pricing import PricingEngine, get_pricing_engine
from .plans import PlanManager, get_plan_manager
from .billing import BillingManager, get_billing_manager

__all__ = [
    # Types
    "UsageType",
    "UsageRecord",
    "UsageSummary",
    "PriceTier",
    "Plan",
    "PlanFeatures",
    "Invoice",
    "InvoiceStatus",
    "Payment",
    "PaymentStatus",
    # Services
    "MeteringService",
    "get_metering_service",
    "PricingEngine",
    "get_pricing_engine",
    "PlanManager",
    "get_plan_manager",
    "BillingManager",
    "get_billing_manager"
]

__version__ = "2.0.0"

"""
Billing System - Tipos e Estruturas de Dados

Define estruturas para metering, pricing e billing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum
import uuid


class UsageType(str, Enum):
    """Tipos de uso rastreado."""
    TOKENS_INPUT = "tokens_input"
    TOKENS_OUTPUT = "tokens_output"
    API_CALLS = "api_calls"
    STORAGE_MB = "storage_mb"
    AGENT_EXECUTIONS = "agent_executions"
    WORKFLOW_RUNS = "workflow_runs"
    RAG_QUERIES = "rag_queries"
    EMBEDDINGS = "embeddings"


class InvoiceStatus(str, Enum):
    """Status de fatura."""
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Status de pagamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class UsageRecord:
    """
    Registro individual de uso.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    tenant_id: Optional[str] = None
    
    # Tipo e quantidade
    usage_type: UsageType = UsageType.API_CALLS
    quantity: float = 0
    
    # Detalhes
    model: Optional[str] = None
    endpoint: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    # Custo calculado
    unit_cost: float = 0
    total_cost: float = 0
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "usage_type": self.usage_type.value,
            "quantity": self.quantity,
            "model": self.model,
            "endpoint": self.endpoint,
            "unit_cost": self.unit_cost,
            "total_cost": self.total_cost,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UsageSummary:
    """
    Resumo de uso por período.
    """
    user_id: str
    period_start: datetime
    period_end: datetime
    
    # Totais por tipo
    tokens_input: int = 0
    tokens_output: int = 0
    api_calls: int = 0
    storage_mb: float = 0
    agent_executions: int = 0
    workflow_runs: int = 0
    rag_queries: int = 0
    embeddings: int = 0
    
    # Custos
    total_cost: float = 0
    
    # Por modelo
    cost_by_model: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "api_calls": self.api_calls,
            "storage_mb": self.storage_mb,
            "agent_executions": self.agent_executions,
            "workflow_runs": self.workflow_runs,
            "total_cost": self.total_cost,
            "cost_by_model": self.cost_by_model
        }


@dataclass
class PriceTier:
    """
    Tier de preço para um tipo de uso.
    """
    usage_type: UsageType
    model: Optional[str] = None
    
    # Preço por unidade (em centavos)
    price_per_unit: float = 0  # Em centavos
    
    # Volume discount
    volume_tiers: list = field(default_factory=list)  # [(limit, price), ...]
    
    # Markup/discount
    markup_percent: float = 0  # Percentual de markup
    discount_percent: float = 0  # Percentual de desconto
    
    def get_price(self, quantity: float) -> float:
        """Calcula preço baseado em volume tiers."""
        if not self.volume_tiers:
            base_price = quantity * self.price_per_unit
        else:
            base_price = 0
            remaining = quantity
            
            for limit, tier_price in sorted(self.volume_tiers):
                if remaining <= 0:
                    break
                    
                tier_quantity = min(remaining, limit)
                base_price += tier_quantity * tier_price
                remaining -= tier_quantity
            
            if remaining > 0:
                base_price += remaining * self.price_per_unit
        
        # Aplicar markup
        if self.markup_percent > 0:
            base_price *= (1 + self.markup_percent / 100)
        
        # Aplicar desconto
        if self.discount_percent > 0:
            base_price *= (1 - self.discount_percent / 100)
        
        return base_price


@dataclass
class PlanFeatures:
    """
    Features incluídas em um plano.
    """
    # Limites de uso
    max_agents: int = 3
    max_workflows: int = 5
    max_api_calls_per_day: int = 1000
    max_tokens_per_month: int = 100000
    max_storage_mb: int = 100
    
    # Features
    custom_models: bool = False
    priority_support: bool = False
    sso_enabled: bool = False
    audit_logs: bool = False
    custom_domain: bool = False
    api_access: bool = True
    webhooks: bool = False
    dedicated_support: bool = False
    
    # Colaboração
    max_team_members: int = 1
    
    def to_dict(self) -> dict:
        return {
            "max_agents": self.max_agents,
            "max_workflows": self.max_workflows,
            "max_api_calls_per_day": self.max_api_calls_per_day,
            "max_tokens_per_month": self.max_tokens_per_month,
            "max_storage_mb": self.max_storage_mb,
            "custom_models": self.custom_models,
            "priority_support": self.priority_support,
            "sso_enabled": self.sso_enabled,
            "audit_logs": self.audit_logs,
            "api_access": self.api_access,
            "max_team_members": self.max_team_members
        }


@dataclass
class Plan:
    """
    Plano de assinatura.
    """
    id: str
    name: str
    description: str
    
    # Preço
    price_monthly: float = 0  # Em centavos
    price_yearly: float = 0  # Em centavos (com desconto)
    
    # Features
    features: PlanFeatures = field(default_factory=PlanFeatures)
    
    # Status
    is_active: bool = True
    is_public: bool = True
    
    # Trial
    trial_days: int = 0
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "features": self.features.to_dict(),
            "is_active": self.is_active,
            "trial_days": self.trial_days
        }


@dataclass
class InvoiceItem:
    """Item de uma fatura."""
    description: str
    quantity: float
    unit_price: float
    total: float
    usage_type: Optional[UsageType] = None


@dataclass
class Invoice:
    """
    Fatura de cobrança.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    tenant_id: Optional[str] = None
    
    # Período
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # Valores
    subtotal: float = 0
    tax: float = 0
    discount: float = 0
    total: float = 0
    currency: str = "USD"
    
    # Items
    items: list = field(default_factory=list)
    
    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    # Datas
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    # Referências
    payment_id: Optional[str] = None
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def add_item(self, item: InvoiceItem) -> None:
        """Adiciona item à fatura."""
        self.items.append(item)
        self.subtotal += item.total
        self.total = self.subtotal + self.tax - self.discount
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "subtotal": self.subtotal,
            "tax": self.tax,
            "discount": self.discount,
            "total": self.total,
            "currency": self.currency,
            "items": [
                {
                    "description": i.description,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total": i.total
                } for i in self.items
            ],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None
        }


@dataclass
class Payment:
    """
    Registro de pagamento.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str = ""
    user_id: str = ""
    
    # Valores
    amount: float = 0
    currency: str = "USD"
    
    # Método
    payment_method: str = ""  # stripe, paypal, etc
    payment_provider_id: Optional[str] = None  # ID no provider
    
    # Status
    status: PaymentStatus = PaymentStatus.PENDING
    
    # Datas
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Erro (se houver)
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

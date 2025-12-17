"""
Pricing Engine - Motor de Precificação

Calcula custos baseado em uso e planos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

from .types import UsageType, UsageSummary, PriceTier


class PricingEngine:
    """
    Motor de precificação para calcular custos.
    
    Features:
    - Preços base por tipo de uso
    - Volume discounts
    - Markup configurável
    - Suporte a múltiplas moedas
    """
    
    # Preços base (em centavos USD)
    DEFAULT_PRICES: Dict[UsageType, Dict[str, Any]] = {
        UsageType.TOKENS_INPUT: {
            "base_price": 0.015,  # Por 1K tokens
            "unit": 1000,
            "description": "Input tokens"
        },
        UsageType.TOKENS_OUTPUT: {
            "base_price": 0.06,  # Por 1K tokens
            "unit": 1000,
            "description": "Output tokens"
        },
        UsageType.API_CALLS: {
            "base_price": 0,  # Geralmente free
            "unit": 1,
            "description": "API calls"
        },
        UsageType.STORAGE_MB: {
            "base_price": 0.02,  # Por GB/mês
            "unit": 1024,  # Cobrado por GB
            "description": "Storage"
        },
        UsageType.AGENT_EXECUTIONS: {
            "base_price": 0.01,
            "unit": 1,
            "description": "Agent executions"
        },
        UsageType.WORKFLOW_RUNS: {
            "base_price": 0.05,
            "unit": 1,
            "description": "Workflow runs"
        },
        UsageType.RAG_QUERIES: {
            "base_price": 0.001,
            "unit": 1,
            "description": "RAG queries"
        },
        UsageType.EMBEDDINGS: {
            "base_price": 0.002,  # Por 1K tokens
            "unit": 1000,
            "description": "Embedding tokens"
        }
    }
    
    # Volume discounts (quantidade, desconto %)
    VOLUME_DISCOUNTS: Dict[UsageType, List[tuple]] = {
        UsageType.TOKENS_INPUT: [
            (100000, 5),     # >100K tokens: 5% desconto
            (1000000, 10),   # >1M tokens: 10% desconto
            (10000000, 20),  # >10M tokens: 20% desconto
        ],
        UsageType.TOKENS_OUTPUT: [
            (100000, 5),
            (1000000, 10),
            (10000000, 20),
        ],
        UsageType.API_CALLS: [
            (10000, 0),
            (100000, 0),
        ],
    }
    
    def __init__(
        self,
        markup_percent: float = 20.0,
        currency: str = "USD"
    ):
        """
        Args:
            markup_percent: Percentual de markup sobre preços base
            currency: Moeda padrão
        """
        self._markup = markup_percent
        self._currency = currency
        self._custom_prices: Dict[UsageType, float] = {}
        self._price_tiers: Dict[str, PriceTier] = {}
    
    def set_custom_price(
        self,
        usage_type: UsageType,
        price: float,
        model: Optional[str] = None
    ) -> None:
        """Define preço customizado."""
        key = f"{usage_type.value}_{model}" if model else usage_type.value
        self._custom_prices[key] = price
    
    def add_price_tier(self, tier: PriceTier) -> None:
        """Adiciona tier de preço."""
        key = f"{tier.usage_type.value}_{tier.model}" if tier.model else tier.usage_type.value
        self._price_tiers[key] = tier
    
    def get_base_price(
        self,
        usage_type: UsageType,
        model: Optional[str] = None
    ) -> float:
        """
        Obtém preço base para um tipo de uso.
        
        Args:
            usage_type: Tipo de uso
            model: Modelo específico (opcional)
            
        Returns:
            Preço base por unidade
        """
        # Verificar preço customizado
        key = f"{usage_type.value}_{model}" if model else usage_type.value
        if key in self._custom_prices:
            return self._custom_prices[key]
        
        # Verificar tier
        if key in self._price_tiers:
            return self._price_tiers[key].price_per_unit
        
        # Preço padrão
        price_info = self.DEFAULT_PRICES.get(usage_type, {"base_price": 0, "unit": 1})
        return price_info["base_price"]
    
    def get_volume_discount(
        self,
        usage_type: UsageType,
        quantity: float
    ) -> float:
        """
        Calcula desconto por volume.
        
        Args:
            usage_type: Tipo de uso
            quantity: Quantidade total
            
        Returns:
            Percentual de desconto
        """
        discounts = self.VOLUME_DISCOUNTS.get(usage_type, [])
        
        applicable_discount = 0
        for threshold, discount in discounts:
            if quantity >= threshold:
                applicable_discount = discount
        
        return applicable_discount
    
    def calculate_cost(
        self,
        usage_type: UsageType,
        quantity: float,
        model: Optional[str] = None,
        apply_markup: bool = True,
        apply_volume_discount: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula custo para um uso específico.
        
        Args:
            usage_type: Tipo de uso
            quantity: Quantidade
            model: Modelo (opcional)
            apply_markup: Aplicar markup
            apply_volume_discount: Aplicar desconto por volume
            
        Returns:
            Dict com detalhes do cálculo
        """
        base_price = self.get_base_price(usage_type, model)
        price_info = self.DEFAULT_PRICES.get(usage_type, {"unit": 1})
        unit = price_info.get("unit", 1)
        
        # Normalizar quantidade para unidade
        normalized_quantity = quantity / unit
        
        # Custo base
        base_cost = normalized_quantity * base_price
        
        # Desconto por volume
        volume_discount = 0
        if apply_volume_discount:
            discount_percent = self.get_volume_discount(usage_type, quantity)
            volume_discount = base_cost * (discount_percent / 100)
        
        # Markup
        markup_amount = 0
        if apply_markup:
            markup_amount = (base_cost - volume_discount) * (self._markup / 100)
        
        # Total
        total = base_cost - volume_discount + markup_amount
        
        return {
            "usage_type": usage_type.value,
            "quantity": quantity,
            "unit": unit,
            "base_price": base_price,
            "base_cost": round(base_cost, 6),
            "volume_discount": round(volume_discount, 6),
            "markup": round(markup_amount, 6),
            "total": round(total, 6),
            "currency": self._currency
        }
    
    def calculate_summary_cost(
        self,
        summary: UsageSummary,
        include_breakdown: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula custo total de um UsageSummary.
        
        Args:
            summary: Resumo de uso
            include_breakdown: Incluir breakdown por tipo
            
        Returns:
            Dict com custo total e breakdown
        """
        breakdown = []
        total_cost = 0
        
        # Tokens input
        if summary.tokens_input > 0:
            cost = self.calculate_cost(UsageType.TOKENS_INPUT, summary.tokens_input)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # Tokens output
        if summary.tokens_output > 0:
            cost = self.calculate_cost(UsageType.TOKENS_OUTPUT, summary.tokens_output)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # API calls
        if summary.api_calls > 0:
            cost = self.calculate_cost(UsageType.API_CALLS, summary.api_calls)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # Storage
        if summary.storage_mb > 0:
            cost = self.calculate_cost(UsageType.STORAGE_MB, summary.storage_mb)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # Agent executions
        if summary.agent_executions > 0:
            cost = self.calculate_cost(UsageType.AGENT_EXECUTIONS, summary.agent_executions)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # Workflow runs
        if summary.workflow_runs > 0:
            cost = self.calculate_cost(UsageType.WORKFLOW_RUNS, summary.workflow_runs)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # RAG queries
        if summary.rag_queries > 0:
            cost = self.calculate_cost(UsageType.RAG_QUERIES, summary.rag_queries)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        # Embeddings
        if summary.embeddings > 0:
            cost = self.calculate_cost(UsageType.EMBEDDINGS, summary.embeddings)
            total_cost += cost["total"]
            if include_breakdown:
                breakdown.append(cost)
        
        return {
            "user_id": summary.user_id,
            "period_start": summary.period_start.isoformat(),
            "period_end": summary.period_end.isoformat(),
            "total_cost": round(total_cost, 2),
            "currency": self._currency,
            "breakdown": breakdown if include_breakdown else None
        }
    
    def estimate_monthly_cost(
        self,
        tokens_per_day: int = 0,
        api_calls_per_day: int = 0,
        storage_mb: float = 0,
        agents: int = 0,
        workflows: int = 0
    ) -> Dict[str, Any]:
        """
        Estima custo mensal baseado em uso projetado.
        
        Args:
            tokens_per_day: Tokens por dia
            api_calls_per_day: API calls por dia
            storage_mb: Storage em MB
            agents: Número de agentes
            workflows: Número de workflows
            
        Returns:
            Estimativa de custo mensal
        """
        days_in_month = 30
        
        # Projetar uso mensal
        monthly_tokens = tokens_per_day * days_in_month
        monthly_api_calls = api_calls_per_day * days_in_month
        monthly_agent_executions = agents * 100  # Estimativa
        monthly_workflow_runs = workflows * 50   # Estimativa
        
        # Calcular custos
        token_cost = self.calculate_cost(
            UsageType.TOKENS_INPUT,
            monthly_tokens * 0.3  # 30% input
        )["total"]
        token_cost += self.calculate_cost(
            UsageType.TOKENS_OUTPUT,
            monthly_tokens * 0.7  # 70% output
        )["total"]
        
        api_cost = self.calculate_cost(
            UsageType.API_CALLS,
            monthly_api_calls
        )["total"]
        
        storage_cost = self.calculate_cost(
            UsageType.STORAGE_MB,
            storage_mb
        )["total"]
        
        agent_cost = self.calculate_cost(
            UsageType.AGENT_EXECUTIONS,
            monthly_agent_executions
        )["total"]
        
        workflow_cost = self.calculate_cost(
            UsageType.WORKFLOW_RUNS,
            monthly_workflow_runs
        )["total"]
        
        total = token_cost + api_cost + storage_cost + agent_cost + workflow_cost
        
        return {
            "estimated_monthly_cost": round(total, 2),
            "currency": self._currency,
            "breakdown": {
                "tokens": round(token_cost, 2),
                "api_calls": round(api_cost, 2),
                "storage": round(storage_cost, 2),
                "agents": round(agent_cost, 2),
                "workflows": round(workflow_cost, 2)
            },
            "assumptions": {
                "days_in_month": days_in_month,
                "tokens_per_day": tokens_per_day,
                "api_calls_per_day": api_calls_per_day
            }
        }


# Singleton instance
_pricing_engine: Optional[PricingEngine] = None


def get_pricing_engine() -> PricingEngine:
    """Obtém instância singleton do PricingEngine."""
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = PricingEngine()
    return _pricing_engine

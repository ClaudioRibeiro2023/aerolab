"""
LLM Cost Tracker - Rastreamento de custos de LLM.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Preços de um modelo."""
    model: str
    provider: str
    input_cost_per_1m: float  # USD per 1M tokens
    output_cost_per_1m: float
    
    # Cache pricing (se aplicável)
    cached_input_cost_per_1m: Optional[float] = None
    
    # Limites
    context_window: int = 128000
    max_output: int = 4096
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> float:
        """Calcula custo de uma chamada."""
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_1m
        
        if cached_tokens > 0 and self.cached_input_cost_per_1m:
            cached_cost = (cached_tokens / 1_000_000) * self.cached_input_cost_per_1m
            input_cost -= cached_cost
        
        return input_cost + output_cost
    
    def to_dict(self) -> Dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "inputCostPer1M": self.input_cost_per_1m,
            "outputCostPer1M": self.output_cost_per_1m,
            "contextWindow": self.context_window,
        }


# Pricing database
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": ModelPricing("gpt-4o", "openai", 2.50, 10.00, context_window=128000),
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", "openai", 0.15, 0.60, context_window=128000),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", "openai", 10.00, 30.00, context_window=128000),
    "gpt-4": ModelPricing("gpt-4", "openai", 30.00, 60.00, context_window=8192),
    "gpt-3.5-turbo": ModelPricing("gpt-3.5-turbo", "openai", 0.50, 1.50, context_window=16385),
    "o1": ModelPricing("o1", "openai", 15.00, 60.00, context_window=200000),
    "o1-mini": ModelPricing("o1-mini", "openai", 3.00, 12.00, context_window=128000),
    
    # Anthropic
    "claude-3-5-sonnet-20241022": ModelPricing("claude-3-5-sonnet-20241022", "anthropic", 3.00, 15.00, context_window=200000),
    "claude-3-opus-20240229": ModelPricing("claude-3-opus-20240229", "anthropic", 15.00, 75.00, context_window=200000),
    "claude-3-sonnet-20240229": ModelPricing("claude-3-sonnet-20240229", "anthropic", 3.00, 15.00, context_window=200000),
    "claude-3-haiku-20240307": ModelPricing("claude-3-haiku-20240307", "anthropic", 0.25, 1.25, context_window=200000),
    
    # Google
    "gemini-1.5-pro": ModelPricing("gemini-1.5-pro", "google", 1.25, 5.00, context_window=2000000),
    "gemini-1.5-flash": ModelPricing("gemini-1.5-flash", "google", 0.075, 0.30, context_window=1000000),
    
    # Groq
    "llama-3.3-70b-versatile": ModelPricing("llama-3.3-70b-versatile", "groq", 0.59, 0.79, context_window=128000),
    "llama-3.1-8b-instant": ModelPricing("llama-3.1-8b-instant", "groq", 0.05, 0.08, context_window=128000),
    "mixtral-8x7b-32768": ModelPricing("mixtral-8x7b-32768", "groq", 0.24, 0.24, context_window=32768),
}


@dataclass
class CostEntry:
    """Entrada de custo."""
    timestamp: datetime
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    
    # Context
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "provider": self.provider,
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "costUsd": self.cost_usd,
            "userId": self.user_id,
            "agentId": self.agent_id,
            "projectId": self.project_id,
        }


class LLMCostTracker:
    """
    Rastreador de custos LLM.
    
    Monitora custos por:
    - Modelo
    - Usuário
    - Agente
    - Projeto
    - Tempo
    """
    
    def __init__(self):
        self._entries: List[CostEntry] = []
        self._lock = threading.RLock()
        
        # Indexes
        self._by_model: Dict[str, List[CostEntry]] = defaultdict(list)
        self._by_user: Dict[str, List[CostEntry]] = defaultdict(list)
        self._by_agent: Dict[str, List[CostEntry]] = defaultdict(list)
        self._by_project: Dict[str, List[CostEntry]] = defaultdict(list)
    
    def track(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> CostEntry:
        """Registra uso e calcula custo."""
        pricing = MODEL_PRICING.get(model)
        
        if pricing:
            cost = pricing.calculate_cost(input_tokens, output_tokens)
            provider = pricing.provider
        else:
            # Fallback pricing
            cost = ((input_tokens + output_tokens) / 1_000_000) * 2.0
            provider = "unknown"
        
        entry = CostEntry(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            user_id=user_id,
            agent_id=agent_id,
            project_id=project_id
        )
        
        with self._lock:
            self._entries.append(entry)
            self._by_model[model].append(entry)
            
            if user_id:
                self._by_user[user_id].append(entry)
            if agent_id:
                self._by_agent[agent_id].append(entry)
            if project_id:
                self._by_project[project_id].append(entry)
        
        return entry
    
    def get_total_cost(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> float:
        """Obtém custo total."""
        entries = self._filter_by_time(self._entries, start, end)
        return sum(e.cost_usd for e in entries)
    
    def get_cost_by_model(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Obtém custo por modelo."""
        result = {}
        
        for model, entries in self._by_model.items():
            filtered = self._filter_by_time(entries, start, end)
            result[model] = sum(e.cost_usd for e in filtered)
        
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def get_cost_by_user(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Obtém custo por usuário."""
        result = {}
        
        for user_id, entries in self._by_user.items():
            filtered = self._filter_by_time(entries, start, end)
            result[user_id] = sum(e.cost_usd for e in filtered)
        
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def get_cost_by_agent(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Obtém custo por agente."""
        result = {}
        
        for agent_id, entries in self._by_agent.items():
            filtered = self._filter_by_time(entries, start, end)
            result[agent_id] = sum(e.cost_usd for e in filtered)
        
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def get_daily_costs(
        self,
        days: int = 30
    ) -> List[Dict]:
        """Obtém custos diários."""
        start = datetime.now() - timedelta(days=days)
        entries = self._filter_by_time(self._entries, start)
        
        # Agrupar por dia
        by_day: Dict[str, float] = defaultdict(float)
        
        for entry in entries:
            day = entry.timestamp.strftime("%Y-%m-%d")
            by_day[day] += entry.cost_usd
        
        return [
            {"date": day, "cost": cost}
            for day, cost in sorted(by_day.items())
        ]
    
    def get_summary(
        self,
        user_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtém resumo de custos."""
        if user_id:
            entries = self._by_user.get(user_id, [])
        else:
            entries = self._entries
        
        entries = self._filter_by_time(entries, start, end)
        
        if not entries:
            return {
                "totalCost": 0,
                "totalTokens": 0,
                "requestCount": 0,
                "avgCostPerRequest": 0,
            }
        
        total_cost = sum(e.cost_usd for e in entries)
        total_input = sum(e.input_tokens for e in entries)
        total_output = sum(e.output_tokens for e in entries)
        
        return {
            "totalCost": round(total_cost, 4),
            "totalTokens": total_input + total_output,
            "inputTokens": total_input,
            "outputTokens": total_output,
            "requestCount": len(entries),
            "avgCostPerRequest": round(total_cost / len(entries), 6),
            "topModels": self.get_cost_by_model(start, end),
        }
    
    def estimate_monthly_cost(
        self,
        daily_requests: int,
        avg_input_tokens: int = 500,
        avg_output_tokens: int = 1000,
        model: str = "gpt-4o"
    ) -> float:
        """Estima custo mensal."""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0
        
        cost_per_request = pricing.calculate_cost(avg_input_tokens, avg_output_tokens)
        return cost_per_request * daily_requests * 30
    
    def _filter_by_time(
        self,
        entries: List[CostEntry],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[CostEntry]:
        """Filtra entries por tempo."""
        if start:
            entries = [e for e in entries if e.timestamp >= start]
        if end:
            entries = [e for e in entries if e.timestamp <= end]
        return entries
    
    def get_pricing(self, model: str) -> Optional[ModelPricing]:
        """Obtém pricing de um modelo."""
        return MODEL_PRICING.get(model)
    
    def list_models(self) -> List[Dict]:
        """Lista modelos com pricing."""
        return [p.to_dict() for p in MODEL_PRICING.values()]


# Singleton
_cost_tracker: Optional[LLMCostTracker] = None


def get_cost_tracker() -> LLMCostTracker:
    """Obtém cost tracker."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = LLMCostTracker()
    return _cost_tracker

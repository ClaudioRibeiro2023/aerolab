"""
Cost Calculator - Cálculo de custos.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Preços por 1M tokens (em USD)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    
    # Google
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    
    # Groq (muito barato)
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}


@dataclass
class CostBreakdown:
    """Detalhamento de custos."""
    total_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    model: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "total_usd": round(self.total_usd, 6),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "input_cost_usd": round(self.input_cost_usd, 6),
            "output_cost_usd": round(self.output_cost_usd, 6),
            "model": self.model
        }


class CostCalculator:
    """
    Calculador de custos.
    """
    
    def __init__(self, custom_pricing: Optional[Dict] = None):
        self._pricing = MODEL_PRICING.copy()
        if custom_pricing:
            self._pricing.update(custom_pricing)
    
    def calculate(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> CostBreakdown:
        """Calcula custo de uma request."""
        pricing = self._pricing.get(model)
        
        if not pricing:
            # Fallback: usar preço médio
            pricing = {"input": 1.0, "output": 3.0}
            logger.warning(f"Unknown model pricing: {model}, using default")
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return CostBreakdown(
            total_usd=input_cost + output_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            model=model
        )
    
    def estimate_monthly(
        self,
        daily_messages: int,
        avg_input_tokens: int = 500,
        avg_output_tokens: int = 1000,
        model: str = "gpt-4o"
    ) -> float:
        """Estima custo mensal."""
        daily_cost = self.calculate(
            model,
            daily_messages * avg_input_tokens,
            daily_messages * avg_output_tokens
        )
        
        return daily_cost.total_usd * 30
    
    def compare_models(
        self,
        input_tokens: int,
        output_tokens: int,
        models: Optional[list] = None
    ) -> Dict[str, CostBreakdown]:
        """Compara custos entre modelos."""
        if models is None:
            models = list(self._pricing.keys())
        
        return {
            model: self.calculate(model, input_tokens, output_tokens)
            for model in models
            if model in self._pricing
        }
    
    def get_pricing(self, model: str) -> Optional[Dict]:
        """Obtém pricing de um modelo."""
        return self._pricing.get(model)
    
    def set_pricing(self, model: str, input_price: float, output_price: float) -> None:
        """Define pricing customizado."""
        self._pricing[model] = {"input": input_price, "output": output_price}


# Singleton
_cost_calculator: Optional[CostCalculator] = None


def get_cost_calculator() -> CostCalculator:
    global _cost_calculator
    if _cost_calculator is None:
        _cost_calculator = CostCalculator()
    return _cost_calculator

"""
AeroLab Platform - LLM Models Configuration
============================================
Central configuration for all LLM providers and models.
Update this file when new models are released.

Last Updated: 2024-12-17
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ModelTier(Enum):
    """Model performance/cost tiers"""
    FREE = "free"           # Free tier models
    BUDGET = "budget"       # Low cost, good for simple tasks
    BALANCED = "balanced"   # Good balance of cost/performance
    PREMIUM = "premium"     # Best performance, higher cost
    FLAGSHIP = "flagship"   # Latest flagship models


@dataclass
class LLMModel:
    """LLM Model configuration"""
    id: str                          # Model identifier for API calls
    name: str                        # Human-readable name
    provider: str                    # Provider name
    tier: ModelTier                  # Performance/cost tier
    context_window: int              # Max context tokens
    input_cost_per_1m: float         # Cost per 1M input tokens (USD)
    output_cost_per_1m: float        # Cost per 1M output tokens (USD)
    supports_vision: bool = False    # Supports image input
    supports_tools: bool = True      # Supports function calling
    supports_json: bool = True       # Supports JSON mode
    release_date: str = ""           # Model release date
    notes: str = ""                  # Additional notes


# =============================================================================
# GROQ MODELS (Updated: Dec 2024)
# https://console.groq.com/docs/models
# =============================================================================
GROQ_MODELS = {
    # Flagship - Llama 3.3 (Latest)
    "llama-3.3-70b-versatile": LLMModel(
        id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B Versatile",
        provider="groq",
        tier=ModelTier.FREE,
        context_window=128000,
        input_cost_per_1m=0.59,
        output_cost_per_1m=0.79,
        release_date="2024-12",
        notes="Best free option. Excellent for most tasks."
    ),
    # Llama 3.1 models
    "llama-3.1-70b-versatile": LLMModel(
        id="llama-3.1-70b-versatile",
        name="Llama 3.1 70B",
        provider="groq",
        tier=ModelTier.FREE,
        context_window=128000,
        input_cost_per_1m=0.59,
        output_cost_per_1m=0.79,
        release_date="2024-07",
        notes="Previous generation, still excellent."
    ),
    "llama-3.1-8b-instant": LLMModel(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant",
        provider="groq",
        tier=ModelTier.FREE,
        context_window=128000,
        input_cost_per_1m=0.05,
        output_cost_per_1m=0.08,
        release_date="2024-07",
        notes="Fastest, best for simple tasks."
    ),
    # Mixtral
    "mixtral-8x7b-32768": LLMModel(
        id="mixtral-8x7b-32768",
        name="Mixtral 8x7B",
        provider="groq",
        tier=ModelTier.FREE,
        context_window=32768,
        input_cost_per_1m=0.24,
        output_cost_per_1m=0.24,
        release_date="2024-01",
        notes="Good for coding tasks."
    ),
    # Gemma 2
    "gemma2-9b-it": LLMModel(
        id="gemma2-9b-it",
        name="Gemma 2 9B",
        provider="groq",
        tier=ModelTier.FREE,
        context_window=8192,
        input_cost_per_1m=0.20,
        output_cost_per_1m=0.20,
        release_date="2024-06",
        notes="Google's efficient model."
    ),
}


# =============================================================================
# OPENAI MODELS (Updated: Dec 2024)
# https://platform.openai.com/docs/models
# =============================================================================
OPENAI_MODELS = {
    # GPT-4o series (Latest)
    "gpt-4o": LLMModel(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        tier=ModelTier.FLAGSHIP,
        context_window=128000,
        input_cost_per_1m=2.50,
        output_cost_per_1m=10.00,
        supports_vision=True,
        release_date="2024-05",
        notes="Best overall. Vision + reasoning."
    ),
    "gpt-4o-mini": LLMModel(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        tier=ModelTier.BUDGET,
        context_window=128000,
        input_cost_per_1m=0.15,
        output_cost_per_1m=0.60,
        supports_vision=True,
        release_date="2024-07",
        notes="Best value. Recommended for most use cases."
    ),
    # O1 series (Reasoning)
    "o1": LLMModel(
        id="o1",
        name="O1",
        provider="openai",
        tier=ModelTier.FLAGSHIP,
        context_window=200000,
        input_cost_per_1m=15.00,
        output_cost_per_1m=60.00,
        release_date="2024-12",
        notes="Best reasoning. Complex problem solving."
    ),
    "o1-mini": LLMModel(
        id="o1-mini",
        name="O1 Mini",
        provider="openai",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        input_cost_per_1m=3.00,
        output_cost_per_1m=12.00,
        release_date="2024-09",
        notes="Faster reasoning model."
    ),
    # GPT-4 Turbo
    "gpt-4-turbo": LLMModel(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        input_cost_per_1m=10.00,
        output_cost_per_1m=30.00,
        supports_vision=True,
        release_date="2024-04",
        notes="Previous flagship. Still excellent."
    ),
}


# =============================================================================
# ANTHROPIC MODELS (Updated: Dec 2024)
# https://docs.anthropic.com/claude/docs/models-overview
# =============================================================================
ANTHROPIC_MODELS = {
    # Claude 3.5 series (Latest)
    "claude-3-5-sonnet-20241022": LLMModel(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        tier=ModelTier.BALANCED,
        context_window=200000,
        input_cost_per_1m=3.00,
        output_cost_per_1m=15.00,
        supports_vision=True,
        release_date="2024-10",
        notes="Best Claude model. Excellent for coding."
    ),
    "claude-3-5-haiku-20241022": LLMModel(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        tier=ModelTier.BUDGET,
        context_window=200000,
        input_cost_per_1m=0.80,
        output_cost_per_1m=4.00,
        supports_vision=True,
        release_date="2024-10",
        notes="Fast and affordable. Great for simple tasks."
    ),
    # Claude 3 series
    "claude-3-opus-20240229": LLMModel(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="anthropic",
        tier=ModelTier.FLAGSHIP,
        context_window=200000,
        input_cost_per_1m=15.00,
        output_cost_per_1m=75.00,
        supports_vision=True,
        release_date="2024-02",
        notes="Most capable Claude 3. Complex reasoning."
    ),
    "claude-3-haiku-20240307": LLMModel(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku",
        provider="anthropic",
        tier=ModelTier.BUDGET,
        context_window=200000,
        input_cost_per_1m=0.25,
        output_cost_per_1m=1.25,
        supports_vision=True,
        release_date="2024-03",
        notes="Cheapest Claude. Good for high volume."
    ),
}


# =============================================================================
# MISTRAL MODELS (Updated: Dec 2024)
# https://docs.mistral.ai/getting-started/models/
# =============================================================================
MISTRAL_MODELS = {
    # Latest models
    "mistral-large-latest": LLMModel(
        id="mistral-large-latest",
        name="Mistral Large",
        provider="mistral",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        input_cost_per_1m=2.00,
        output_cost_per_1m=6.00,
        release_date="2024-11",
        notes="Best Mistral. Multilingual excellence."
    ),
    "mistral-small-latest": LLMModel(
        id="mistral-small-latest",
        name="Mistral Small",
        provider="mistral",
        tier=ModelTier.BUDGET,
        context_window=32000,
        input_cost_per_1m=0.10,
        output_cost_per_1m=0.30,
        release_date="2024-09",
        notes="Cost-effective. Good for simple tasks."
    ),
    "codestral-latest": LLMModel(
        id="codestral-latest",
        name="Codestral",
        provider="mistral",
        tier=ModelTier.BALANCED,
        context_window=32000,
        input_cost_per_1m=0.30,
        output_cost_per_1m=0.90,
        release_date="2024-05",
        notes="Specialized for code generation."
    ),
    "pixtral-large-latest": LLMModel(
        id="pixtral-large-latest",
        name="Pixtral Large",
        provider="mistral",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        input_cost_per_1m=2.00,
        output_cost_per_1m=6.00,
        supports_vision=True,
        release_date="2024-11",
        notes="Vision model. Image understanding."
    ),
}


# =============================================================================
# GOOGLE MODELS (Updated: Dec 2024)
# https://ai.google.dev/gemini-api/docs/models/gemini
# =============================================================================
GOOGLE_MODELS = {
    "gemini-2.0-flash-exp": LLMModel(
        id="gemini-2.0-flash-exp",
        name="Gemini 2.0 Flash",
        provider="google",
        tier=ModelTier.BALANCED,
        context_window=1000000,
        input_cost_per_1m=0.075,
        output_cost_per_1m=0.30,
        supports_vision=True,
        release_date="2024-12",
        notes="Latest Gemini. 1M context window."
    ),
    "gemini-1.5-pro": LLMModel(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        tier=ModelTier.PREMIUM,
        context_window=2000000,
        input_cost_per_1m=1.25,
        output_cost_per_1m=5.00,
        supports_vision=True,
        release_date="2024-02",
        notes="2M context. Best for long documents."
    ),
    "gemini-1.5-flash": LLMModel(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        tier=ModelTier.BUDGET,
        context_window=1000000,
        input_cost_per_1m=0.075,
        output_cost_per_1m=0.30,
        supports_vision=True,
        release_date="2024-05",
        notes="Fast and cheap. 1M context."
    ),
}


# =============================================================================
# RECOMMENDED MODELS BY USE CASE
# =============================================================================
RECOMMENDED_MODELS = {
    # Default model for general use (best value)
    "default": "llama-3.3-70b-versatile",
    
    # By use case
    "chat": "llama-3.3-70b-versatile",      # General chat
    "coding": "claude-3-5-sonnet-20241022",  # Code generation
    "reasoning": "o1-mini",                   # Complex reasoning
    "vision": "gpt-4o",                       # Image analysis
    "fast": "llama-3.1-8b-instant",          # Quick responses
    "cheap": "gpt-4o-mini",                   # Budget-friendly
    "long_context": "gemini-1.5-pro",         # Very long documents
    
    # By provider (best model from each)
    "best_groq": "llama-3.3-70b-versatile",
    "best_openai": "gpt-4o-mini",
    "best_anthropic": "claude-3-5-sonnet-20241022",
    "best_mistral": "mistral-small-latest",
    "best_google": "gemini-2.0-flash-exp",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_models() -> dict:
    """Get all available models from all providers"""
    return {
        **GROQ_MODELS,
        **OPENAI_MODELS,
        **ANTHROPIC_MODELS,
        **MISTRAL_MODELS,
        **GOOGLE_MODELS,
    }


def get_models_by_provider(provider: str) -> dict:
    """Get models for a specific provider"""
    providers = {
        "groq": GROQ_MODELS,
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "mistral": MISTRAL_MODELS,
        "google": GOOGLE_MODELS,
    }
    return providers.get(provider.lower(), {})


def get_models_by_tier(tier: ModelTier) -> list:
    """Get all models of a specific tier"""
    all_models = get_all_models()
    return [m for m in all_models.values() if m.tier == tier]


def get_cheapest_model(provider: str = None) -> LLMModel:
    """Get the cheapest model (optionally by provider)"""
    if provider:
        models = get_models_by_provider(provider)
    else:
        models = get_all_models()
    
    return min(models.values(), key=lambda m: m.input_cost_per_1m + m.output_cost_per_1m)


def get_recommended_model(use_case: str = "default") -> str:
    """Get recommended model ID for a use case"""
    return RECOMMENDED_MODELS.get(use_case, RECOMMENDED_MODELS["default"])


def get_model_info(model_id: str) -> Optional[LLMModel]:
    """Get model info by ID"""
    all_models = get_all_models()
    return all_models.get(model_id)


def list_models_for_frontend() -> list:
    """Get models formatted for frontend dropdown"""
    all_models = get_all_models()
    result = []
    
    for model_id, model in all_models.items():
        result.append({
            "id": model_id,
            "name": model.name,
            "provider": model.provider,
            "tier": model.tier.value,
            "context_window": model.context_window,
            "cost_input": model.input_cost_per_1m,
            "cost_output": model.output_cost_per_1m,
            "supports_vision": model.supports_vision,
            "notes": model.notes,
        })
    
    # Sort by provider, then by tier
    result.sort(key=lambda x: (x["provider"], x["tier"]))
    return result

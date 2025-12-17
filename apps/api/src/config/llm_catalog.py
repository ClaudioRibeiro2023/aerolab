from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


class LLMCatalogError(Exception):
    """Erro ao carregar ou consultar o catálogo de LLMs."""


_BASE_DIR = Path(__file__).parent
_CATALOG_PATH = _BASE_DIR / "llm_catalog.json"


@lru_cache(maxsize=1)
def load_llm_catalog() -> Dict[str, Any]:
    """Carrega o catálogo de LLMs a partir do arquivo JSON.

    O resultado é cacheado em memória para evitar I/O repetido.
    """
    if not _CATALOG_PATH.exists():
        raise LLMCatalogError(f"Catálogo de LLMs não encontrado em {_CATALOG_PATH}")

    try:
        with _CATALOG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise LLMCatalogError(f"Erro ao fazer parse de {_CATALOG_PATH}: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMCatalogError("Conteúdo de llm_catalog.json deve ser um objeto JSON na raiz")

    return data


def get_model_config(model_key: str) -> Dict[str, Any]:
    """Retorna a configuração completa de um modelo, ex: "openai:gpt-5.1"."""
    catalog = load_llm_catalog()
    models = catalog.get("models", {})
    if model_key not in models:
        raise LLMCatalogError(f"Modelo não encontrado no catálogo: {model_key}")
    cfg = models[model_key]
    if not isinstance(cfg, dict):
        raise LLMCatalogError(f"Configuração inválida para modelo: {model_key}")
    return cfg


def list_models() -> List[str]:
    """Lista todas as chaves de modelos disponíveis no catálogo."""
    catalog = load_llm_catalog()
    models = catalog.get("models", {})
    if not isinstance(models, dict):
        raise LLMCatalogError("Campo 'models' deve ser um objeto JSON")
    return list(models.keys())


def list_models_by_provider(provider: str) -> List[str]:
    """Lista modelos pertencentes a um provider específico (ex: "openai")."""
    catalog = load_llm_catalog()
    models = catalog.get("models", {})
    if not isinstance(models, dict):
        raise LLMCatalogError("Campo 'models' deve ser um objeto JSON")

    result: List[str] = []
    for key, cfg in models.items():
        if isinstance(cfg, dict) and cfg.get("provider") == provider:
            result.append(key)
    return result


def get_profile_models(profile_name: str) -> List[str]:
    """Retorna a lista de modelos em ordem de prioridade para um profile."""
    catalog = load_llm_catalog()
    profiles = catalog.get("profiles", {})
    if not isinstance(profiles, dict):
        raise LLMCatalogError("Campo 'profiles' deve ser um objeto JSON")

    profile_cfg = profiles.get(profile_name)
    if not isinstance(profile_cfg, dict):
        raise LLMCatalogError(f"Profile não encontrado no catálogo: {profile_name}")

    order = profile_cfg.get("priority_order", [])
    if not isinstance(order, list):
        raise LLMCatalogError(f"Campo 'priority_order' inválido para profile: {profile_name}")

    return [m for m in order if isinstance(m, str)]


def get_pricing(model_key: str) -> Optional[Dict[str, Any]]:
    """Retorna o bloco de pricing de um modelo, se existir.

    Estrutura esperada (a ser preenchida manualmente no JSON):

    "pricing": {
        "unit": "1K_tokens" | "1M_tokens",
        "input_usd": 0.0,
        "output_usd": 0.0
    }
    """
    cfg = get_model_config(model_key)
    pricing = cfg.get("pricing")
    if pricing is None:
        return None
    if not isinstance(pricing, dict):
        raise LLMCatalogError(f"Campo 'pricing' inválido para modelo: {model_key}")
    return pricing


def resolve_profile(
    profile_name: str,
    available_api_keys: Optional[Dict[str, bool]] = None
) -> tuple[str, str]:
    """Resolve um profile para (provider, model_id) baseado na prioridade e API keys disponíveis.

    Args:
        profile_name: Nome do profile (ex: "agent_frontier", "agent_coding_max")
        available_api_keys: Dict indicando quais API keys estão configuradas.
            Ex: {"openai": True, "anthropic": False, "google_gemini": True, "mistral": False}
            Se None, assume todas disponíveis.

    Returns:
        Tuple (provider, model_id) do primeiro modelo disponível no profile.

    Raises:
        LLMCatalogError: Se o profile não existir ou nenhum modelo estiver disponível.

    Exemplo:
        >>> provider, model_id = resolve_profile("agent_frontier", {"openai": True})
        >>> # Retorna ("openai", "gpt-5.1") se OPENAI_API_KEY estiver configurada
    """
    model_keys = get_profile_models(profile_name)
    if not model_keys:
        raise LLMCatalogError(f"Profile '{profile_name}' está vazio ou não existe")

    for model_key in model_keys:
        cfg = get_model_config(model_key)
        provider = cfg.get("provider")
        model_id = cfg.get("model_id")

        if not provider or not model_id:
            continue

        # Se não temos info de API keys, assume disponível
        if available_api_keys is None:
            return (provider, model_id)

        # Checa se a API key do provider está disponível
        if available_api_keys.get(provider, False):
            return (provider, model_id)

    raise LLMCatalogError(
        f"Nenhum modelo disponível para profile '{profile_name}'. "
        f"Verifique se as API keys dos providers estão configuradas."
    )


def get_available_api_keys() -> Dict[str, bool]:
    """Retorna um dict indicando quais API keys de LLM estão configuradas.

    Útil para passar ao resolve_profile().
    """
    import os
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "google_gemini": bool(os.getenv("GOOGLE_GEMINI_API_KEY")),
        "mistral": bool(os.getenv("MISTRAL_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
    }


def get_models_for_frontend() -> List[Dict[str, Any]]:
    """Retorna lista de modelos formatada para o frontend.

    Cada item contém:
    - key: chave única (ex: "openai:gpt-5.1")
    - provider: nome do provider
    - model_id: id do modelo
    - capabilities: lista de capacidades
    - role: papel recomendado
    - display_name: nome amigável para exibir
    """
    catalog = load_llm_catalog()
    models = catalog.get("models", {})
    result = []

    for key, cfg in models.items():
        if not isinstance(cfg, dict):
            continue

        provider = cfg.get("provider", "")
        model_id = cfg.get("model_id", "")
        capabilities = cfg.get("capabilities", [])
        recommended = cfg.get("recommended", {})
        role = recommended.get("role", "general")

        # Gerar nome amigável
        display_name = model_id.replace("-", " ").title()

        result.append({
            "key": key,
            "provider": provider,
            "model_id": model_id,
            "capabilities": capabilities,
            "role": role,
            "display_name": display_name,
        })

    return result

"""
CLI simples: python -m src
Mostra um resumo das configurações ativas (valores sensíveis mascarados).
"""
from typing import Optional
from src.config import get_settings


def _mask(v: Optional[str]) -> str:
    if not v:
        return "MISSING"
    return f"***{v[-4:]}"


def main() -> None:
    s = get_settings()
    s.ensure_directories()
    print("🔧 Settings - Resumo (CLI)")
    print(f"DEFAULT_MODEL_PROVIDER={s.DEFAULT_MODEL_PROVIDER}")
    print(f"DEFAULT_MODEL_ID={s.DEFAULT_MODEL_ID}")
    print(f"AGENTOS_HOST={s.AGENTOS_HOST}")
    print(f"AGENTOS_PORT={s.AGENTOS_PORT}")
    print(f"DEFAULT_DB_FILE={s.DEFAULT_DB_FILE}")
    print("API keys:")
    print(f"  OPENAI_API_KEY={_mask(s.OPENAI_API_KEY)}")
    print(f"  ANTHROPIC_API_KEY={_mask(s.ANTHROPIC_API_KEY)}")
    print(f"  GROQ_API_KEY={_mask(s.GROQ_API_KEY)}")
    print(f"  TAVILY_API_KEY={_mask(s.TAVILY_API_KEY)}")
    print(f"VALID={s.validate()}")


if __name__ == "__main__":
    main()

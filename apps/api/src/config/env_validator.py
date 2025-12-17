"""
Validador de variáveis de ambiente com fail-fast.

Este módulo valida variáveis de ambiente críticas na inicialização
da aplicação, falhando imediatamente se configurações essenciais
estiverem ausentes.

Uso:
    from src.config.env_validator import validate_environment
    validate_environment()  # Levanta exceção se faltar variável crítica
"""

import os
import sys
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Resultado da validação de ambiente."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class EnvironmentValidationError(Exception):
    """Exceção levantada quando variáveis críticas estão ausentes."""

    pass


def _get_env(key: str) -> Optional[str]:
    """Obtém variável de ambiente, retorna None se vazia."""
    value = os.getenv(key, "").strip()
    return value if value else None


def validate_environment(fail_fast: bool = True) -> ValidationResult:
    """
    Valida variáveis de ambiente críticas.

    Args:
        fail_fast: Se True, levanta exceção imediatamente ao encontrar erro crítico.
                   Se False, coleta todos os erros e retorna resultado.

    Returns:
        ValidationResult com status e lista de erros/warnings.

    Raises:
        EnvironmentValidationError: Se fail_fast=True e variável crítica ausente.
    """
    result = ValidationResult()

    # ========== VARIÁVEIS CRÍTICAS (P0) ==========
    # Pelo menos uma API key de LLM deve estar configurada
    llm_keys = {
        "GROQ_API_KEY": _get_env("GROQ_API_KEY"),
        "OPENAI_API_KEY": _get_env("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": _get_env("ANTHROPIC_API_KEY"),
    }

    if not any(llm_keys.values()):
        error = (
            "❌ CRÍTICO: Nenhuma API key de LLM configurada. "
            "Configure pelo menos uma: GROQ_API_KEY, OPENAI_API_KEY ou ANTHROPIC_API_KEY"
        )
        result.errors.append(error)
        result.is_valid = False

    # JWT_SECRET é obrigatório para autenticação
    if not _get_env("JWT_SECRET"):
        error = "❌ CRÍTICO: JWT_SECRET não configurado. Necessário para autenticação."
        result.errors.append(error)
        result.is_valid = False

    # ========== VARIÁVEIS IMPORTANTES (P1) ==========
    # ADMIN_USERS recomendado
    if not _get_env("ADMIN_USERS"):
        result.warnings.append(
            "⚠️ ADMIN_USERS não configurado. Nenhum usuário terá permissões de admin."
        )

    # CORS para produção
    cors_origins = _get_env("CORS_ALLOW_ORIGINS")
    if not cors_origins:
        result.warnings.append(
            "⚠️ CORS_ALLOW_ORIGINS não configurado. Usando padrão permissivo (localhost)."
        )

    # ========== VARIÁVEIS OPCIONAIS (P2) ==========
    # Apenas log informativo se configuradas
    optional_services = {
        "TAVILY_API_KEY": "Busca web (Tavily)",
        "CHROMA_HOST": "Vector store remoto (ChromaDB)",
        "REDIS_URL": "Cache (Redis)",
        "SENTRY_DSN": "Error tracking (Sentry)",
    }

    configured_services = []
    for key, description in optional_services.items():
        if _get_env(key):
            configured_services.append(description)

    # ========== FAIL FAST ==========
    if fail_fast and not result.is_valid:
        print("\n" + "=" * 60)
        print("🚨 FALHA NA VALIDAÇÃO DE AMBIENTE")
        print("=" * 60)
        for error in result.errors:
            print(f"\n{error}")
        print("\n" + "-" * 60)
        print("📝 Configure as variáveis no arquivo .env ou como variáveis de ambiente.")
        print("   Consulte .env.example para referência.")
        print("=" * 60 + "\n")
        raise EnvironmentValidationError(
            f"Variáveis de ambiente críticas ausentes: {len(result.errors)} erro(s)"
        )

    return result


def print_environment_summary():
    """Imprime resumo das configurações de ambiente."""
    result = validate_environment(fail_fast=False)

    print("\n" + "=" * 60)
    print("📋 RESUMO DE CONFIGURAÇÃO DE AMBIENTE")
    print("=" * 60)

    # Status geral
    if result.is_valid:
        print("\n✅ Status: VÁLIDO")
    else:
        print("\n❌ Status: INVÁLIDO")

    # Erros críticos
    if result.errors:
        print("\n🚨 Erros Críticos:")
        for error in result.errors:
            print(f"   {error}")

    # Warnings
    if result.warnings:
        print("\n⚠️ Avisos:")
        for warning in result.warnings:
            print(f"   {warning}")

    # LLM Keys configuradas
    print("\n🤖 LLM Providers:")
    for provider, key in [
        ("Groq", "GROQ_API_KEY"),
        ("OpenAI", "OPENAI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
    ]:
        status = "✅" if _get_env(key) else "❌"
        print(f"   {status} {provider}")

    # Serviços opcionais
    print("\n🔌 Serviços Opcionais:")
    for key, description in [
        ("TAVILY_API_KEY", "Busca web (Tavily)"),
        ("CHROMA_HOST", "Vector store remoto"),
        ("REDIS_URL", "Cache (Redis)"),
        ("SENTRY_DSN", "Error tracking (Sentry)"),
    ]:
        status = "✅" if _get_env(key) else "⬚"
        print(f"   {status} {description}")

    print("\n" + "=" * 60)

    return result


if __name__ == "__main__":
    """Executa validação standalone."""
    from dotenv import load_dotenv

    load_dotenv()

    try:
        result = print_environment_summary()
        sys.exit(0 if result.is_valid else 1)
    except EnvironmentValidationError:
        sys.exit(1)

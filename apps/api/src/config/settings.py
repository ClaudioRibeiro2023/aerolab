"""
Configurações centralizadas do projeto usando python-dotenv
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Configurações da aplicação"""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASES_DIR: Path = DATA_DIR / "databases"
    KNOWLEDGE_DIR: Path = DATA_DIR / "knowledge"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    GOOGLE_GEMINI_API_KEY: Optional[str] = os.getenv("GOOGLE_GEMINI_API_KEY")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    
    # Modelos padrão
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", "openai")
    DEFAULT_MODEL_ID: str = os.getenv("DEFAULT_MODEL_ID", "gpt-4.1")
    
    # AgentOS
    AGENTOS_HOST: str = os.getenv("AGENTOS_HOST", "0.0.0.0")
    AGENTOS_PORT: int = int(os.getenv("AGENTOS_PORT", "8000"))
    AGENTOS_AGENT_NAME: Optional[str] = os.getenv("AGENTOS_AGENT_NAME")
    AGENTOS_AGENT_ROLE: Optional[str] = os.getenv("AGENTOS_AGENT_ROLE")
    CORS_ALLOW_ORIGINS: Optional[str] = os.getenv("CORS_ALLOW_ORIGINS")
    # Segurança opcional
    BASIC_AUTH_USERNAME: Optional[str] = os.getenv("BASIC_AUTH_USERNAME")
    BASIC_AUTH_PASSWORD: Optional[str] = os.getenv("BASIC_AUTH_PASSWORD")
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
    # Rate limit específicos por grupo de rota (opcionais)
    RATE_LIMIT_RAG_QUERY: int = int(os.getenv("RATE_LIMIT_RAG_QUERY", "60"))
    RATE_LIMIT_RAG_INGEST: int = int(os.getenv("RATE_LIMIT_RAG_INGEST", "10"))
    RATE_LIMIT_AUTH: int = int(os.getenv("RATE_LIMIT_AUTH", "30"))
    RATE_LIMIT_AGENTICS: int = int(os.getenv("RATE_LIMIT_AGENTICS", "30"))  # teams/workflows
    RATE_LIMIT_DEFAULT: int = int(os.getenv("RATE_LIMIT_DEFAULT", "120"))
    # JWT opcional
    JWT_SECRET: Optional[str] = os.getenv("JWT_SECRET")
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    ADMIN_USERS: Optional[str] = os.getenv("ADMIN_USERS")  # lista separada por vírgula
    
    # RAG / Embeddings / Vector store
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "data/vectorstore")
    CHROMA_HOST: Optional[str] = os.getenv("CHROMA_HOST")  # Ex: http://chromadb:8000
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "openai")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
    
    # Database
    DEFAULT_DB_FILE: str = os.getenv("DEFAULT_DB_FILE", "data/databases/agents.db")
    
    # Configurações gerais
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se as configurações críticas estão presentes"""
        critical_keys = []
        
        # Verificar se pelo menos uma API key de LLM está configurada
        if not any([cls.OPENAI_API_KEY, cls.ANTHROPIC_API_KEY, cls.GROQ_API_KEY]):
            critical_keys.append("Nenhuma API key de LLM configurada (OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY)")
        
        if critical_keys:
            print("⚠️  Configurações faltando:")
            for key in critical_keys:
                print(f"   - {key}")
            return False
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """Garante que os diretórios necessários existem"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.DATABASES_DIR.mkdir(exist_ok=True)
        cls.KNOWLEDGE_DIR.mkdir(exist_ok=True)


# Instância global de configurações
_settings = Settings()

def get_settings() -> Settings:
    """Retorna a instância de configurações"""
    return _settings


if __name__ == "__main__":
    s = get_settings()
    s.ensure_directories()
    print("🔧 Settings - Resumo")
    print(f"DEFAULT_MODEL_PROVIDER={s.DEFAULT_MODEL_PROVIDER}")
    print(f"DEFAULT_MODEL_ID={s.DEFAULT_MODEL_ID}")
    print(f"AGENTOS_HOST={s.AGENTOS_HOST}")
    print(f"AGENTOS_PORT={s.AGENTOS_PORT}")
    print(f"DEFAULT_DB_FILE={s.DEFAULT_DB_FILE}")

    def _mask(v: Optional[str]) -> str:
        if not v:
            return "MISSING"
        return f"***{v[-4:]}"

    print("API keys:")
    print(f"  OPENAI_API_KEY={_mask(s.OPENAI_API_KEY)}")
    print(f"  ANTHROPIC_API_KEY={_mask(s.ANTHROPIC_API_KEY)}")
    print(f"  GROQ_API_KEY={_mask(s.GROQ_API_KEY)}")
    print(f"  MISTRAL_API_KEY={_mask(s.MISTRAL_API_KEY)}")
    print(f"  GOOGLE_GEMINI_API_KEY={_mask(s.GOOGLE_GEMINI_API_KEY)}")
    print(f"  TAVILY_API_KEY={_mask(s.TAVILY_API_KEY)}")

    ok = s.validate()
    print(f"VALID={ok}")

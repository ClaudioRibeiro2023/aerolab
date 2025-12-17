"""
Classe base para agentes reutilizáveis
"""

from typing import Optional, List, Any
from agno.agent import Agent
from agno.models.base import Model
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb

from ..config import get_settings

# Importação condicional do MistralChat (evita erro se mistralai não estiver instalado)
MistralChat = None
try:
    from agno.models.mistral.mistral import MistralChat
except ImportError:
    pass


class BaseAgent:
    """
    Classe base para criar agentes com configurações padrão

    Uso:
        agent = BaseAgent.create(
            name="Meu Agente",
            role="Assistente",
            instructions=["Seja educado"]
        )
    """

    @staticmethod
    def get_model(
        provider: Optional[str] = None, model_id: Optional[str] = None, **kwargs
    ) -> Model:
        """
        Retorna um modelo LLM configurado

        Args:
            provider: Provider do modelo (groq, openai, anthropic)
            model_id: ID do modelo específico
            **kwargs: Argumentos adicionais para o modelo
        """
        settings = get_settings()
        provider = provider or settings.DEFAULT_MODEL_PROVIDER
        model_id = model_id or settings.DEFAULT_MODEL_ID

        if provider == "groq":
            return Groq(id=model_id, api_key=settings.GROQ_API_KEY, **kwargs)
        elif provider == "openai":
            return OpenAIChat(id=model_id or "gpt-4o", api_key=settings.OPENAI_API_KEY, **kwargs)
        elif provider == "anthropic":
            try:
                from agno.models.anthropic import Claude  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "O provider 'anthropic' foi selecionado, mas o pacote 'anthropic' não está instalado. "
                    "Instale com 'pip install anthropic' ou defina DEFAULT_MODEL_PROVIDER para 'groq' ou 'openai'."
                ) from e
            return Claude(
                id=model_id or "claude-sonnet-4-5", api_key=settings.ANTHROPIC_API_KEY, **kwargs
            )
        elif provider in ("google", "google_gemini"):
            return Gemini(id=model_id, api_key=settings.GOOGLE_GEMINI_API_KEY, **kwargs)
        elif provider == "mistral":
            if MistralChat is None:
                raise ImportError(
                    "O provider 'mistral' foi selecionado, mas o pacote 'mistralai' não está instalado. "
                    "Instale com 'pip install mistralai' ou defina DEFAULT_MODEL_PROVIDER para 'groq' ou 'openai'."
                )
            return MistralChat(id=model_id, api_key=settings.MISTRAL_API_KEY, **kwargs)
        else:
            raise ValueError(f"Provider não suportado: {provider}")

    @staticmethod
    def get_database(db_file: Optional[str] = None) -> SqliteDb:
        """
        Retorna um banco de dados SQLite configurado

        Args:
            db_file: Caminho para o arquivo do banco de dados
        """
        settings = get_settings()
        settings.ensure_directories()

        db_path = db_file or settings.DEFAULT_DB_FILE
        return SqliteDb(db_file=db_path)

    @classmethod
    def create(
        cls,
        name: str,
        role: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        tools: Optional[List[Any]] = None,
        model_provider: Optional[str] = None,
        model_id: Optional[str] = None,
        use_database: bool = False,
        db_file: Optional[str] = None,
        add_history_to_context: bool = True,
        markdown: bool = True,
        debug_mode: bool = False,
        **kwargs,
    ) -> Agent:
        """
        Cria um agente Agno com configurações padrão

        Args:
            name: Nome do agente
            role: Papel/função do agente
            instructions: Lista de instruções para o agente
            tools: Lista de ferramentas do agente
            model_provider: Provider do modelo (groq, openai, anthropic)
            model_id: ID específico do modelo
            use_database: Se deve usar banco de dados para persistência
            db_file: Caminho customizado para o banco de dados
            add_history_to_context: Adicionar histórico ao contexto
            markdown: Usar formatação markdown
            debug_mode: Ativar modo debug
            **kwargs: Argumentos adicionais para o Agent

        Returns:
            Agent configurado

        Exemplo:
            >>> agent = BaseAgent.create(
            ...     name="Assistente",
            ...     role="Você é um assistente útil",
            ...     instructions=["Seja educado", "Seja conciso"],
            ...     model_provider="groq"
            ... )
        """
        settings = get_settings()

        # Configurar modelo
        model = cls.get_model(provider=model_provider, model_id=model_id)

        # Configurar banco de dados se solicitado
        db = None
        if use_database:
            db = cls.get_database(db_file)

        # Criar agente
        agent = Agent(
            name=name,
            model=model,
            role=role,
            instructions=instructions or [],
            tools=tools or [],
            db=db,
            add_history_to_context=add_history_to_context,
            markdown=markdown,
            debug_mode=debug_mode or settings.DEBUG,
            **kwargs,
        )

        return agent

"""
AgentBuilder - Padrão Fluent para criação de agentes avançados.

Permite criar agentes com configurações complexas de forma intuitiva:

    agent = AgentBuilder("Researcher") \
        .with_profile("agent_frontier") \
        .with_tools([TavilyTool(), GitHubTool()]) \
        .with_rag(collection="docs", strategy="semantic") \
        .with_self_healing(max_retries=3) \
        .with_planning(strategy="react") \
        .with_memory(long_term=True) \
        .with_guardrails(max_tokens=4000) \
        .build()
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent

from .base_agent import BaseAgent
from ..config.llm_catalog import resolve_profile, get_model_config


class AgentComplexity(Enum):
    """Níveis de complexidade de agente."""
    SIMPLE = "simple"           # Só responde
    TOOLS = "tools"             # Usa ferramentas
    RAG = "rag"                 # Usa retrieval
    PLANNING = "planning"       # Planeja antes de agir
    AUTONOMOUS = "autonomous"   # Multi-step autônomo


@dataclass
class GuardrailsConfig:
    """Configuração de guardrails."""
    max_input_tokens: int = 8000
    max_output_tokens: int = 4000
    max_tool_calls: int = 10
    allowed_tools: Optional[List[str]] = None
    blocked_patterns: List[str] = field(default_factory=list)
    require_confirmation_for: List[str] = field(default_factory=list)


@dataclass
class MemoryConfig:
    """Configuração de memória."""
    short_term: bool = True
    long_term: bool = False
    episodic: bool = False
    semantic: bool = False  # RAG-based
    max_history_messages: int = 20
    persistence_backend: str = "sqlite"  # sqlite, redis, supabase


@dataclass
class TelemetryConfig:
    """Configuração de telemetria."""
    enabled: bool = True
    log_inputs: bool = False  # PII concerns
    log_outputs: bool = False
    track_latency: bool = True
    track_tokens: bool = True
    track_costs: bool = True
    export_to: Optional[str] = None  # prometheus, datadog, etc.


@dataclass
class AgentConfig:
    """Configuração completa de um agente."""
    name: str
    role: Optional[str] = None
    instructions: List[str] = field(default_factory=list)
    
    # Model
    provider: Optional[str] = None
    model_id: Optional[str] = None
    profile: Optional[str] = None
    temperature: float = 0.7
    
    # Tools
    tools: List[Any] = field(default_factory=list)
    tool_choice: str = "auto"  # auto, required, none
    
    # RAG
    rag_enabled: bool = False
    rag_collection: Optional[str] = None
    rag_strategy: str = "semantic"  # semantic, keyword, hybrid
    rag_top_k: int = 5
    
    # Planning
    planning_enabled: bool = False
    planning_strategy: str = "react"  # react, decompose, tot
    
    # Self-healing
    self_healing_enabled: bool = False
    max_retries: int = 3
    fallback_models: List[str] = field(default_factory=list)
    
    # Memory
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Guardrails
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    
    # Telemetry
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    
    # Database
    use_database: bool = False
    db_file: Optional[str] = None
    
    # Output
    markdown: bool = True
    debug_mode: bool = False


class AgentBuilder:
    """
    Builder fluent para criação de agentes avançados.
    
    Exemplo:
        agent = AgentBuilder("Pesquisador") \
            .with_role("Especialista em pesquisa de mercado") \
            .with_profile("balanced") \
            .with_instructions([
                "Pesquise informações atualizadas",
                "Cite fontes confiáveis"
            ]) \
            .with_tools([TavilyTool()]) \
            .with_rag("docs_collection") \
            .with_self_healing() \
            .with_memory(long_term=True) \
            .build()
    """
    
    def __init__(self, name: str):
        """
        Inicia o builder com o nome do agente.
        
        Args:
            name: Nome identificador do agente
        """
        self._config = AgentConfig(name=name)
    
    def with_role(self, role: str) -> "AgentBuilder":
        """Define o papel/função do agente."""
        self._config.role = role
        return self
    
    def with_instructions(self, instructions: List[str]) -> "AgentBuilder":
        """Define as instruções do agente."""
        self._config.instructions = instructions
        return self
    
    def add_instruction(self, instruction: str) -> "AgentBuilder":
        """Adiciona uma instrução."""
        self._config.instructions.append(instruction)
        return self
    
    def with_profile(self, profile: str) -> "AgentBuilder":
        """
        Define o profile do agente.
        
        Profiles disponíveis:
        - fast: Rápido e econômico (Gemini Flash)
        - balanced: Equilibrado (GPT-5.1)
        - powerful: Máxima qualidade (Claude Opus)
        - coding: Especialista em código (GPT-5.1 Codex)
        - reasoning: Raciocínio profundo (O3 Pro)
        
        Args:
            profile: ID do profile
        """
        self._config.profile = profile
        
        # Mapear profiles simplificados para profiles do catálogo
        profile_mapping = {
            "fast": "agent_fast_low_cost",
            "balanced": "agent_frontier",
            "powerful": "agent_deep_reasoning",
            "coding": "agent_coding_max",
            "reasoning": "agent_deep_reasoning",
        }
        
        catalog_profile = profile_mapping.get(profile, profile)
        
        try:
            provider, model_id = resolve_profile(catalog_profile)
            self._config.provider = provider
            self._config.model_id = model_id
        except Exception:
            # Fallback para GPT-5.1
            self._config.provider = "openai"
            self._config.model_id = "gpt-5.1"
        
        return self
    
    def with_model(
        self, 
        provider: str, 
        model_id: str,
        temperature: float = 0.7
    ) -> "AgentBuilder":
        """
        Define o modelo manualmente.
        
        Args:
            provider: Provider (openai, anthropic, google_gemini, mistral)
            model_id: ID do modelo
            temperature: Temperatura (0-2)
        """
        self._config.provider = provider
        self._config.model_id = model_id
        self._config.temperature = temperature
        return self
    
    def with_tools(self, tools: List[Any]) -> "AgentBuilder":
        """
        Define as ferramentas do agente.
        
        Args:
            tools: Lista de instâncias de ferramentas
        """
        self._config.tools = tools
        return self
    
    def add_tool(self, tool: Any) -> "AgentBuilder":
        """Adiciona uma ferramenta."""
        self._config.tools.append(tool)
        return self
    
    def with_rag(
        self,
        collection: str,
        strategy: str = "semantic",
        top_k: int = 5
    ) -> "AgentBuilder":
        """
        Habilita RAG (Retrieval Augmented Generation).
        
        Args:
            collection: Nome da collection/index
            strategy: Estratégia de busca (semantic, keyword, hybrid)
            top_k: Número de documentos a recuperar
        """
        self._config.rag_enabled = True
        self._config.rag_collection = collection
        self._config.rag_strategy = strategy
        self._config.rag_top_k = top_k
        return self
    
    def with_planning(self, strategy: str = "react") -> "AgentBuilder":
        """
        Habilita planejamento antes de agir.
        
        Args:
            strategy: Estratégia de planejamento (react, decompose, tot)
        """
        self._config.planning_enabled = True
        self._config.planning_strategy = strategy
        return self
    
    def with_self_healing(
        self,
        max_retries: int = 3,
        fallback_models: Optional[List[str]] = None
    ) -> "AgentBuilder":
        """
        Habilita auto-recuperação de erros.
        
        Args:
            max_retries: Máximo de tentativas
            fallback_models: Modelos de fallback
        """
        self._config.self_healing_enabled = True
        self._config.max_retries = max_retries
        self._config.fallback_models = fallback_models or [
            "gpt-5.1",
            "claude-sonnet-4.5",
            "gemini-2.5-pro"
        ]
        return self
    
    def with_memory(
        self,
        short_term: bool = True,
        long_term: bool = False,
        episodic: bool = False,
        semantic: bool = False,
        max_history: int = 20
    ) -> "AgentBuilder":
        """
        Configura sistema de memória.
        
        Args:
            short_term: Memória de sessão
            long_term: Memória persistente
            episodic: Memória de eventos
            semantic: Memória semântica (RAG)
            max_history: Máximo de mensagens no histórico
        """
        self._config.memory = MemoryConfig(
            short_term=short_term,
            long_term=long_term,
            episodic=episodic,
            semantic=semantic,
            max_history_messages=max_history
        )
        return self
    
    def with_guardrails(
        self,
        max_input_tokens: int = 8000,
        max_output_tokens: int = 4000,
        max_tool_calls: int = 10,
        blocked_patterns: Optional[List[str]] = None
    ) -> "AgentBuilder":
        """
        Configura guardrails de segurança.
        
        Args:
            max_input_tokens: Limite de tokens de entrada
            max_output_tokens: Limite de tokens de saída
            max_tool_calls: Limite de chamadas de ferramentas
            blocked_patterns: Padrões bloqueados no output
        """
        self._config.guardrails = GuardrailsConfig(
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_tool_calls=max_tool_calls,
            blocked_patterns=blocked_patterns or []
        )
        return self
    
    def with_telemetry(
        self,
        enabled: bool = True,
        track_costs: bool = True,
        export_to: Optional[str] = None
    ) -> "AgentBuilder":
        """
        Configura telemetria.
        
        Args:
            enabled: Habilitar telemetria
            track_costs: Rastrear custos
            export_to: Destino de exportação (prometheus, datadog)
        """
        self._config.telemetry = TelemetryConfig(
            enabled=enabled,
            track_costs=track_costs,
            export_to=export_to
        )
        return self
    
    def with_database(self, db_file: Optional[str] = None) -> "AgentBuilder":
        """Habilita persistência em banco de dados."""
        self._config.use_database = True
        self._config.db_file = db_file
        return self
    
    def with_markdown(self, enabled: bool = True) -> "AgentBuilder":
        """Configura output em Markdown."""
        self._config.markdown = enabled
        return self
    
    def with_debug(self, enabled: bool = True) -> "AgentBuilder":
        """Habilita modo debug."""
        self._config.debug_mode = enabled
        return self
    
    def get_config(self) -> AgentConfig:
        """Retorna a configuração atual."""
        return self._config
    
    def build(self) -> Agent:
        """
        Constrói o agente com todas as configurações.
        
        Returns:
            Agent configurado
        """
        config = self._config
        
        # Criar agente base
        agent = BaseAgent.create(
            name=config.name,
            role=config.role,
            instructions=config.instructions,
            tools=config.tools if config.tools else None,
            model_provider=config.provider,
            model_id=config.model_id,
            use_database=config.use_database,
            db_file=config.db_file,
            add_history_to_context=config.memory.short_term,
            markdown=config.markdown,
            debug_mode=config.debug_mode
        )
        
        # Wrap com SelfHealingAgent se habilitado
        if config.self_healing_enabled:
            from .self_healing import SelfHealingAgent
            agent = SelfHealingAgent(
                agent=agent,
                max_retries=config.max_retries,
                enable_circuit_breaker=True
            )
        
        return agent
    
    def build_async(self) -> "AsyncAgentBuilder":
        """Retorna um builder para agente assíncrono."""
        return AsyncAgentBuilder(self._config)


class AsyncAgentBuilder:
    """Builder para criação assíncrona de agentes."""
    
    def __init__(self, config: AgentConfig):
        self._config = config
    
    async def build(self) -> Agent:
        """Constrói o agente de forma assíncrona."""
        # Para expansão futura com inicialização assíncrona
        return AgentBuilder(self._config.name) \
            .with_role(self._config.role or "") \
            .with_instructions(self._config.instructions) \
            .build()


# Factory functions
def quick_agent(
    name: str,
    profile: str = "balanced",
    instructions: Optional[List[str]] = None
) -> Agent:
    """
    Cria um agente rapidamente com defaults sensatos.
    
    Args:
        name: Nome do agente
        profile: Profile (fast, balanced, powerful, coding, reasoning)
        instructions: Instruções opcionais
    
    Returns:
        Agent configurado
    """
    builder = AgentBuilder(name).with_profile(profile)
    
    if instructions:
        builder.with_instructions(instructions)
    
    return builder.build()


def research_agent(name: str = "Researcher") -> Agent:
    """Cria um agente de pesquisa pré-configurado."""
    return AgentBuilder(name) \
        .with_role("Especialista em pesquisa e análise de informações") \
        .with_profile("balanced") \
        .with_instructions([
            "Pesquise informações atualizadas e relevantes",
            "Cite fontes confiáveis sempre que possível",
            "Organize findings de forma clara e estruturada",
            "Identifique insights acionáveis"
        ]) \
        .with_self_healing() \
        .build()


def coding_agent(name: str = "CodeAssistant") -> Agent:
    """Cria um agente de código pré-configurado."""
    return AgentBuilder(name) \
        .with_role("Especialista em desenvolvimento de software") \
        .with_profile("coding") \
        .with_instructions([
            "Escreva código limpo, bem documentado e testável",
            "Siga as melhores práticas da linguagem",
            "Explique suas decisões de design",
            "Considere edge cases e error handling"
        ]) \
        .with_self_healing() \
        .build()


def support_agent(name: str = "SupportBot") -> Agent:
    """Cria um agente de suporte pré-configurado."""
    return AgentBuilder(name) \
        .with_role("Agente de suporte ao cliente") \
        .with_profile("fast") \
        .with_instructions([
            "Seja empático e profissional",
            "Resolva problemas de forma eficiente",
            "Escale para humano quando necessário",
            "Sempre confirme se o problema foi resolvido"
        ]) \
        .with_memory(short_term=True, long_term=True) \
        .build()

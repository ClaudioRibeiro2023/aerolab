"""
Domain Studio Core Types - 100+ tipos avançados para domínios especializados.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union


# ============================================================
# DOMAIN TYPES
# ============================================================

class DomainType(str, Enum):
    """15 domínios especializados."""
    LEGAL = "legal"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    GEO = "geo"
    DATA = "data"
    DEVOPS = "devops"
    CORPORATE = "corporate"
    HR = "hr"
    MARKETING = "marketing"
    SALES = "sales"
    SUPPLY_CHAIN = "supply_chain"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    INSURANCE = "insurance"
    GOVERNMENT = "government"
    ENERGY = "energy"


class DomainCapability(str, Enum):
    """Capacidades disponíveis por domínio."""
    RAG = "rag"
    AGENTIC_RAG = "agentic_rag"
    GRAPH_RAG = "graph_rag"
    MULTIMODAL = "multimodal"
    VOICE = "voice"
    WORKFLOWS = "workflows"
    COMPLIANCE = "compliance"
    REAL_TIME = "real_time"
    ANALYTICS = "analytics"
    INTEGRATIONS = "integrations"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    FINE_TUNED = "fine_tuned"
    XAI = "xai"
    COMPUTER_USE = "computer_use"
    MCP = "mcp"


class ComplianceLevel(str, Enum):
    """Níveis de compliance."""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CRITICAL = "critical"


class RegulationType(str, Enum):
    """Tipos de regulamentação."""
    # Brasil
    LGPD = "lgpd"
    CVM = "cvm"
    BACEN = "bacen"
    ANVISA = "anvisa"
    CFM = "cfm"
    OAB = "oab"
    CLT = "clt"
    CONAR = "conar"
    B3 = "b3"
    SUSEP = "susep"
    ANS = "ans"
    ANATEL = "anatel"
    # Internacional
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    SOX = "sox"
    CCPA = "ccpa"


class AgentCapability(str, Enum):
    """Capacidades de agentes."""
    REASONING = "reasoning"
    PLANNING = "planning"
    TOOL_USE = "tool_use"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    DOCUMENT_ANALYSIS = "document_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_ANALYSIS = "audio_analysis"
    DATA_ANALYSIS = "data_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"


class WorkflowStepType(str, Enum):
    """Tipos de steps em workflows."""
    AGENT = "agent"
    TOOL = "tool"
    HUMAN = "human"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SUBWORKFLOW = "subworkflow"
    API_CALL = "api_call"
    WAIT = "wait"
    TRANSFORM = "transform"


class RAGMode(str, Enum):
    """Modos de RAG."""
    SIMPLE = "simple"
    HYBRID = "hybrid"
    AGENTIC = "agentic"
    GRAPH = "graph"
    MULTI_HOP = "multi_hop"


class ExplainMethod(str, Enum):
    """Métodos de explicabilidade."""
    SHAP = "shap"
    LIME = "lime"
    ATTENTION = "attention"
    COUNTERFACTUAL = "counterfactual"
    FEATURE_IMPORTANCE = "feature_importance"


# ============================================================
# DATA CLASSES - DOMAIN
# ============================================================

@dataclass
class DomainConfiguration:
    """Configuração completa de um domínio."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: DomainType = DomainType.CORPORATE
    description: str = ""
    icon: str = "📁"
    color: str = "#3B82F6"
    gradient: str = "from-blue-500 to-cyan-600"
    
    # Capabilities
    capabilities: List[DomainCapability] = field(default_factory=list)
    
    # Compliance
    compliance_level: ComplianceLevel = ComplianceLevel.STANDARD
    regulations: List[RegulationType] = field(default_factory=list)
    
    # Models
    default_model: str = "gpt-4o"
    fine_tuned_model: Optional[str] = None
    embedding_model: str = "text-embedding-3-large"
    
    # Languages
    supported_languages: List[str] = field(default_factory=lambda: ["pt-BR", "en-US"])
    
    # Resources
    agents: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    knowledge_sources: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"


@dataclass
class DomainAgent:
    """Agente especializado de domínio."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: DomainType = DomainType.CORPORATE
    role: str = ""
    description: str = ""
    
    # Capabilities
    capabilities: List[AgentCapability] = field(default_factory=list)
    
    # Instructions
    system_prompt: str = ""
    instructions: List[str] = field(default_factory=list)
    
    # Model
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Tools
    tools: List[str] = field(default_factory=list)
    
    # Knowledge
    knowledge_sources: List[str] = field(default_factory=list)
    rag_mode: RAGMode = RAGMode.HYBRID
    
    # Compliance
    compliance_rules: List[str] = field(default_factory=list)
    
    # Performance
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    
    # Metadata
    icon: str = "🤖"
    color: str = "#3B82F6"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DomainWorkflow:
    """Workflow automatizado de domínio."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: DomainType = DomainType.CORPORATE
    description: str = ""
    
    # Steps
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Triggers
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    
    # Human checkpoints
    human_checkpoints: List[str] = field(default_factory=list)
    
    # Configuration
    timeout_minutes: int = 60
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    icon: str = "⚙️"
    is_active: bool = True
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowStep:
    """Step de workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: WorkflowStepType = WorkflowStepType.AGENT
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    
    # Error handling
    on_error: str = "fail"  # fail, skip, retry
    max_retries: int = 3
    
    # Timeout
    timeout_seconds: int = 300


@dataclass
class WorkflowTrigger:
    """Trigger de workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "manual"  # manual, schedule, event, webhook
    config: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class DomainKnowledge:
    """Base de conhecimento do domínio."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: DomainType = DomainType.CORPORATE
    name: str = ""
    description: str = ""
    
    # Sources
    document_count: int = 0
    total_chunks: int = 0
    
    # Ontology
    entity_types: List[str] = field(default_factory=list)
    relationship_types: List[str] = field(default_factory=list)
    
    # Embeddings
    embedding_model: str = "text-embedding-3-large"
    vector_dimensions: int = 3072
    
    # Graph
    has_knowledge_graph: bool = False
    graph_node_count: int = 0
    graph_edge_count: int = 0
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


# ============================================================
# DATA CLASSES - RAG
# ============================================================

@dataclass
class RAGQuery:
    """Query para RAG."""
    query: str
    domain: DomainType
    mode: RAGMode = RAGMode.HYBRID
    top_k: int = 10
    rerank: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    include_graph: bool = False


@dataclass
class RAGResult:
    """Resultado de RAG."""
    query: str
    answer: str
    sources: List[RAGSource] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    tokens_used: int = 0
    graph_context: Optional[Dict] = None


@dataclass
class RAGSource:
    """Fonte de RAG."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: str = "document"


# ============================================================
# DATA CLASSES - COMPLIANCE
# ============================================================

@dataclass
class ComplianceCheck:
    """Resultado de verificação de compliance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    regulations_checked: List[RegulationType] = field(default_factory=list)
    
    # Results
    is_compliant: bool = True
    score: float = 100.0
    
    # Issues
    violations: List[ComplianceViolation] = field(default_factory=list)
    warnings: List[ComplianceWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceViolation:
    """Violação de compliance."""
    regulation: RegulationType
    rule: str
    description: str
    severity: str  # critical, high, medium, low
    location: Optional[str] = None


@dataclass
class ComplianceWarning:
    """Warning de compliance."""
    regulation: RegulationType
    rule: str
    description: str
    recommendation: str


# ============================================================
# DATA CLASSES - XAI
# ============================================================

@dataclass
class Explanation:
    """Explicação de resposta."""
    response_id: str
    method: ExplainMethod
    
    # Explanation data
    feature_importance: Dict[str, float] = field(default_factory=dict)
    attention_weights: Optional[List[float]] = None
    shap_values: Optional[List[float]] = None
    
    # Natural language
    summary: str = ""
    key_factors: List[str] = field(default_factory=list)
    
    # Sources
    sources_used: List[str] = field(default_factory=list)
    
    # Confidence
    confidence_score: float = 0.0
    uncertainty_factors: List[str] = field(default_factory=list)


@dataclass
class BiasReport:
    """Relatório de detecção de viés."""
    content_id: str
    
    # Scores
    overall_bias_score: float = 0.0
    
    # By category
    gender_bias: float = 0.0
    racial_bias: float = 0.0
    age_bias: float = 0.0
    
    # Details
    flagged_phrases: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Fairness metrics
    fairness_metrics: Dict[str, float] = field(default_factory=dict)


# ============================================================
# DATA CLASSES - GAMIFICATION
# ============================================================

@dataclass
class Achievement:
    """Conquista do sistema de gamificação."""
    id: str
    name: str
    description: str
    icon: str
    tier: str  # bronze, silver, gold, platinum
    domain: Optional[DomainType] = None
    
    # Criteria
    metric: str = ""
    target: int = 1
    
    # Reward
    xp_reward: int = 0
    badge_url: Optional[str] = None
    
    # Status
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    progress: float = 0.0


@dataclass
class UserProgress:
    """Progresso do usuário no sistema."""
    user_id: str
    
    # XP
    total_xp: int = 0
    level: int = 1
    
    # Achievements
    achievements: List[str] = field(default_factory=list)
    
    # By domain
    domain_xp: Dict[str, int] = field(default_factory=dict)
    domain_level: Dict[str, int] = field(default_factory=dict)
    
    # Stats
    messages_sent: int = 0
    workflows_run: int = 0
    documents_analyzed: int = 0
    
    # Streak
    current_streak: int = 0
    longest_streak: int = 0
    last_active: datetime = field(default_factory=datetime.now)


# ============================================================
# PROTOCOL TYPES
# ============================================================

@dataclass
class MCPTool:
    """Ferramenta MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable] = None


@dataclass
class MCPResource:
    """Recurso MCP."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


@dataclass
class A2AMessage:
    """Mensagem A2A entre agentes."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    type: str = "request"  # request, response, proposal, counter
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================
# DOMAIN THEMES
# ============================================================

DOMAIN_THEMES: Dict[DomainType, Dict[str, str]] = {
    DomainType.LEGAL: {
        "name": "Jurídico",
        "icon": "⚖️",
        "color": "#DC2626",
        "gradient": "from-red-500 to-rose-600",
    },
    DomainType.FINANCE: {
        "name": "Financeiro",
        "icon": "💰",
        "color": "#F59E0B",
        "gradient": "from-amber-500 to-orange-600",
    },
    DomainType.HEALTHCARE: {
        "name": "Saúde",
        "icon": "🏥",
        "color": "#10B981",
        "gradient": "from-emerald-500 to-teal-600",
    },
    DomainType.GEO: {
        "name": "Geolocalização",
        "icon": "🗺️",
        "color": "#22C55E",
        "gradient": "from-green-500 to-emerald-600",
    },
    DomainType.DATA: {
        "name": "Dados & Analytics",
        "icon": "📊",
        "color": "#3B82F6",
        "gradient": "from-blue-500 to-cyan-600",
    },
    DomainType.DEVOPS: {
        "name": "DevOps",
        "icon": "⚙️",
        "color": "#8B5CF6",
        "gradient": "from-purple-500 to-indigo-600",
    },
    DomainType.CORPORATE: {
        "name": "Corporativo",
        "icon": "🏢",
        "color": "#6B7280",
        "gradient": "from-slate-500 to-gray-600",
    },
    DomainType.HR: {
        "name": "Recursos Humanos",
        "icon": "👥",
        "color": "#EC4899",
        "gradient": "from-pink-500 to-rose-600",
    },
    DomainType.MARKETING: {
        "name": "Marketing",
        "icon": "📢",
        "color": "#F97316",
        "gradient": "from-orange-500 to-amber-600",
    },
    DomainType.SALES: {
        "name": "Vendas",
        "icon": "💼",
        "color": "#14B8A6",
        "gradient": "from-teal-500 to-cyan-600",
    },
    DomainType.SUPPLY_CHAIN: {
        "name": "Supply Chain",
        "icon": "📦",
        "color": "#84CC16",
        "gradient": "from-lime-500 to-green-600",
    },
    DomainType.EDUCATION: {
        "name": "Educação",
        "icon": "🎓",
        "color": "#6366F1",
        "gradient": "from-indigo-500 to-purple-600",
    },
    DomainType.REAL_ESTATE: {
        "name": "Imobiliário",
        "icon": "🏠",
        "color": "#78716C",
        "gradient": "from-stone-500 to-neutral-600",
    },
    DomainType.INSURANCE: {
        "name": "Seguros",
        "icon": "🛡️",
        "color": "#0EA5E9",
        "gradient": "from-sky-500 to-blue-600",
    },
    DomainType.GOVERNMENT: {
        "name": "Governo",
        "icon": "🏛️",
        "color": "#1D4ED8",
        "gradient": "from-blue-700 to-indigo-800",
    },
    DomainType.ENERGY: {
        "name": "Energia",
        "icon": "⚡",
        "color": "#FACC15",
        "gradient": "from-yellow-500 to-amber-600",
    },
}


# ============================================================
# REGULATIONS BY DOMAIN
# ============================================================

DOMAIN_REGULATIONS: Dict[DomainType, List[RegulationType]] = {
    DomainType.LEGAL: [
        RegulationType.OAB,
        RegulationType.LGPD,
    ],
    DomainType.FINANCE: [
        RegulationType.CVM,
        RegulationType.BACEN,
        RegulationType.B3,
        RegulationType.LGPD,
        RegulationType.SOX,
    ],
    DomainType.HEALTHCARE: [
        RegulationType.ANVISA,
        RegulationType.CFM,
        RegulationType.ANS,
        RegulationType.LGPD,
        RegulationType.HIPAA,
    ],
    DomainType.DATA: [
        RegulationType.LGPD,
        RegulationType.GDPR,
        RegulationType.SOC2,
    ],
    DomainType.DEVOPS: [
        RegulationType.SOC2,
        RegulationType.ISO_27001,
        RegulationType.PCI_DSS,
    ],
    DomainType.HR: [
        RegulationType.CLT,
        RegulationType.LGPD,
    ],
    DomainType.MARKETING: [
        RegulationType.CONAR,
        RegulationType.LGPD,
    ],
    DomainType.INSURANCE: [
        RegulationType.SUSEP,
        RegulationType.LGPD,
    ],
}

"""
Legal Domain Agents - Agentes especializados do domínio jurídico.
"""

from ...core.types import DomainAgent, AgentCapability, RAGMode, DomainType


# Agent configurations (exported for reference)
ContractAnalystAgent = DomainAgent(
    name="ContractAnalyst",
    domain=DomainType.LEGAL,
    role="Analista de Contratos",
    description="Especialista em análise e revisão de contratos",
    capabilities=[
        AgentCapability.DOCUMENT_ANALYSIS,
        AgentCapability.REASONING,
        AgentCapability.COMPLIANCE_CHECK,
    ],
    icon="📋",
)

LegalResearcherAgent = DomainAgent(
    name="LegalResearcher",
    domain=DomainType.LEGAL,
    role="Pesquisador Jurídico",
    description="Especialista em pesquisa de jurisprudência e legislação",
    capabilities=[
        AgentCapability.KNOWLEDGE_RETRIEVAL,
        AgentCapability.WEB_SEARCH,
        AgentCapability.REASONING,
    ],
    icon="🔍",
)

DocumentDrafterAgent = DomainAgent(
    name="DocumentDrafter",
    domain=DomainType.LEGAL,
    role="Redator de Documentos",
    description="Especialista em redação de documentos jurídicos",
    capabilities=[
        AgentCapability.REASONING,
        AgentCapability.PLANNING,
    ],
    icon="✍️",
)

ComplianceOfficerAgent = DomainAgent(
    name="ComplianceOfficer",
    domain=DomainType.LEGAL,
    role="Oficial de Compliance",
    description="Especialista em compliance e conformidade regulatória",
    capabilities=[
        AgentCapability.COMPLIANCE_CHECK,
        AgentCapability.REASONING,
    ],
    icon="🛡️",
)

DueDiligenceAgent = DomainAgent(
    name="DueDiligenceExpert",
    domain=DomainType.LEGAL,
    role="Especialista em Due Diligence",
    description="Especialista em processos de due diligence",
    capabilities=[
        AgentCapability.DOCUMENT_ANALYSIS,
        AgentCapability.REASONING,
        AgentCapability.PLANNING,
    ],
    icon="📊",
)

LitigationSupportAgent = DomainAgent(
    name="LitigationSupport",
    domain=DomainType.LEGAL,
    role="Suporte a Litígios",
    description="Especialista em suporte a processos judiciais",
    capabilities=[
        AgentCapability.KNOWLEDGE_RETRIEVAL,
        AgentCapability.DOCUMENT_ANALYSIS,
        AgentCapability.REASONING,
    ],
    icon="⚔️",
)

# All legal agents
LEGAL_AGENTS = [
    ContractAnalystAgent,
    LegalResearcherAgent,
    DocumentDrafterAgent,
    ComplianceOfficerAgent,
    DueDiligenceAgent,
    LitigationSupportAgent,
]

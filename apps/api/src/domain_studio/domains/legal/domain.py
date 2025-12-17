"""
Legal Domain Implementation - Domínio Jurídico Completo.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ...core.types import (
    DomainType,
    DomainConfiguration,
    DomainCapability,
    RegulationType,
    DomainAgent,
    DomainWorkflow,
    WorkflowStep,
    WorkflowStepType,
    AgentCapability,
    RAGMode,
)
from ...core.domain_base import BaseDomain
from ...engines.agentic_rag import AgenticRAGEngine
from ...engines.graph_rag import GraphRAGEngine
from ...engines.compliance import ComplianceEngine
from ...engines.workflow import WorkflowEngine, WorkflowDefinition, get_workflow_engine

logger = logging.getLogger(__name__)


class LegalDomain(BaseDomain):
    """
    Domínio Jurídico Especializado.
    
    Features:
    - 6 Agentes Especializados
    - Contract Analysis
    - Legal Research (jurisprudência + legislação)
    - Document Drafting
    - Due Diligence
    - Compliance OAB/LGPD
    """
    
    @property
    def domain_type(self) -> DomainType:
        return DomainType.LEGAL
    
    def _get_default_config(self) -> DomainConfiguration:
        """Get default configuration for Legal domain."""
        return DomainConfiguration(
            type=DomainType.LEGAL,
            name="Jurídico",
            description="Domínio especializado em análise jurídica, contratos, compliance e pesquisa legal.",
            icon="⚖️",
            color="#DC2626",
            gradient="from-red-500 to-rose-600",
            capabilities=[
                DomainCapability.RAG,
                DomainCapability.AGENTIC_RAG,
                DomainCapability.GRAPH_RAG,
                DomainCapability.COMPLIANCE,
                DomainCapability.WORKFLOWS,
                DomainCapability.MULTIMODAL,
                DomainCapability.XAI,
                DomainCapability.MCP,
            ],
            regulations=[
                RegulationType.OAB,
                RegulationType.LGPD,
            ],
            default_model="gpt-4o",
            supported_languages=["pt-BR", "en-US"],
        )
    
    def _register_agents(self) -> None:
        """Register Legal domain agents."""
        # Contract Analyst
        self.add_agent(DomainAgent(
            name="ContractAnalyst",
            role="Analista de Contratos",
            description="Especialista em análise e revisão de contratos",
            capabilities=[
                AgentCapability.DOCUMENT_ANALYSIS,
                AgentCapability.REASONING,
                AgentCapability.COMPLIANCE_CHECK,
            ],
            system_prompt="""Você é um especialista em análise de contratos jurídicos.
Analise contratos identificando:
- Cláusulas de risco
- Obrigações das partes
- Prazos e penalidades
- Conformidade com legislação
Sempre cite as cláusulas específicas em suas análises.""",
            instructions=[
                "Analise contratos de forma estruturada",
                "Identifique riscos e oportunidades",
                "Sugira melhorias nas cláusulas",
                "Verifique conformidade com LGPD",
            ],
            tools=["contract_parser", "clause_analyzer", "risk_scorer"],
            rag_mode=RAGMode.AGENTIC,
            icon="📋",
            color="#DC2626",
        ))
        
        # Legal Researcher
        self.add_agent(DomainAgent(
            name="LegalResearcher",
            role="Pesquisador Jurídico",
            description="Especialista em pesquisa de jurisprudência e legislação",
            capabilities=[
                AgentCapability.KNOWLEDGE_RETRIEVAL,
                AgentCapability.WEB_SEARCH,
                AgentCapability.REASONING,
            ],
            system_prompt="""Você é um pesquisador jurídico especializado.
Pesquise e analise:
- Jurisprudência de tribunais superiores (STF, STJ, TST)
- Legislação federal, estadual e municipal
- Doutrina e pareceres
Sempre cite as fontes com números de processos e artigos de lei.""",
            instructions=[
                "Pesquise jurisprudência relevante",
                "Cite número de processos e datas",
                "Analise entendimentos majoritários",
                "Identifique tendências jurisprudenciais",
            ],
            tools=["jurisprudence_search", "legislation_lookup", "doctrine_search"],
            rag_mode=RAGMode.GRAPH,
            icon="🔍",
            color="#B91C1C",
        ))
        
        # Document Drafter
        self.add_agent(DomainAgent(
            name="DocumentDrafter",
            role="Redator de Documentos",
            description="Especialista em redação de documentos jurídicos",
            capabilities=[
                AgentCapability.REASONING,
                AgentCapability.PLANNING,
            ],
            system_prompt="""Você é um redator jurídico experiente.
Elabore documentos jurídicos como:
- Petições e recursos
- Contratos e aditivos
- Pareceres jurídicos
- Notificações e ofícios
Use linguagem técnica apropriada e siga as normas processuais.""",
            instructions=[
                "Siga o formato técnico adequado",
                "Use fundamentação legal sólida",
                "Mantenha clareza e objetividade",
                "Revise ortografia e formatação",
            ],
            tools=["document_templates", "legal_formatter"],
            icon="✍️",
            color="#991B1B",
        ))
        
        # Compliance Officer
        self.add_agent(DomainAgent(
            name="ComplianceOfficer",
            role="Oficial de Compliance",
            description="Especialista em compliance e conformidade regulatória",
            capabilities=[
                AgentCapability.COMPLIANCE_CHECK,
                AgentCapability.REASONING,
            ],
            system_prompt="""Você é um oficial de compliance jurídico.
Verifique conformidade com:
- Código de Ética da OAB
- LGPD e proteção de dados
- Normas anticorrupção
- Regulamentações setoriais
Identifique riscos e proponha mitigações.""",
            instructions=[
                "Verifique conformidade regulatória",
                "Identifique riscos de compliance",
                "Proponha ações corretivas",
                "Monitore prazos e obrigações",
            ],
            tools=["compliance_checker", "risk_assessor"],
            compliance_rules=["oab_ethics", "lgpd_data_protection"],
            icon="🛡️",
            color="#7F1D1D",
        ))
        
        # Due Diligence Expert
        self.add_agent(DomainAgent(
            name="DueDiligenceExpert",
            role="Especialista em Due Diligence",
            description="Especialista em processos de due diligence",
            capabilities=[
                AgentCapability.DOCUMENT_ANALYSIS,
                AgentCapability.REASONING,
                AgentCapability.PLANNING,
            ],
            system_prompt="""Você é um especialista em due diligence jurídica.
Conduza análises abrangentes de:
- Situação societária
- Passivos trabalhistas e tributários
- Contratos relevantes
- Litígios em andamento
Produza relatórios estruturados com classificação de riscos.""",
            instructions=[
                "Analise documentação corporativa",
                "Identifique contingências",
                "Classifique riscos por severidade",
                "Produza relatório executivo",
            ],
            tools=["corporate_search", "litigation_tracker", "risk_matrix"],
            icon="📊",
            color="#DC2626",
        ))
        
        # Litigation Support
        self.add_agent(DomainAgent(
            name="LitigationSupport",
            role="Suporte a Litígios",
            description="Especialista em suporte a processos judiciais",
            capabilities=[
                AgentCapability.KNOWLEDGE_RETRIEVAL,
                AgentCapability.DOCUMENT_ANALYSIS,
                AgentCapability.REASONING,
            ],
            system_prompt="""Você é um especialista em suporte a litígios.
Auxilie em:
- Análise de peças processuais
- Pesquisa de precedentes
- Elaboração de estratégias
- Cálculos de contingências
Mantenha registro da linha do tempo processual.""",
            instructions=[
                "Analise histórico processual",
                "Identifique argumentos relevantes",
                "Sugira estratégias processuais",
                "Monitore prazos",
            ],
            tools=["case_analyzer", "timeline_builder", "precedent_finder"],
            icon="⚔️",
            color="#EF4444",
        ))
    
    def _register_workflows(self) -> None:
        """Register Legal domain workflows."""
        # Contract Review Workflow
        contract_review = DomainWorkflow(
            name="Contract Review",
            description="Análise completa de contrato com verificação de compliance",
            steps=[
                WorkflowStep(
                    id="extract",
                    name="Extract Contract Data",
                    type=WorkflowStepType.TOOL,
                    config={"tool": "contract_parser"}
                ),
                WorkflowStep(
                    id="analyze",
                    name="Analyze Clauses",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "ContractAnalyst"},
                    depends_on=["extract"]
                ),
                WorkflowStep(
                    id="compliance",
                    name="Check Compliance",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "ComplianceOfficer"},
                    depends_on=["analyze"]
                ),
                WorkflowStep(
                    id="review",
                    name="Human Review",
                    type=WorkflowStepType.HUMAN,
                    config={"message": "Revise a análise do contrato"},
                    depends_on=["compliance"]
                ),
                WorkflowStep(
                    id="report",
                    name="Generate Report",
                    type=WorkflowStepType.TRANSFORM,
                    config={"transform": "generate_report"},
                    depends_on=["review"]
                ),
            ],
            human_checkpoints=["review"],
            icon="📋",
        )
        self.add_workflow(contract_review)
        
        # Due Diligence Workflow
        due_diligence = DomainWorkflow(
            name="Due Diligence",
            description="Processo completo de due diligence jurídica",
            steps=[
                WorkflowStep(
                    id="corporate",
                    name="Corporate Analysis",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "DueDiligenceExpert", "focus": "corporate"}
                ),
                WorkflowStep(
                    id="litigation",
                    name="Litigation Check",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "LitigationSupport"},
                ),
                WorkflowStep(
                    id="contracts",
                    name="Contract Review",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "ContractAnalyst"},
                ),
                WorkflowStep(
                    id="compliance",
                    name="Compliance Check",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "ComplianceOfficer"},
                    depends_on=["corporate", "litigation", "contracts"]
                ),
                WorkflowStep(
                    id="risk_matrix",
                    name="Generate Risk Matrix",
                    type=WorkflowStepType.TRANSFORM,
                    config={"transform": "risk_matrix"},
                    depends_on=["compliance"]
                ),
                WorkflowStep(
                    id="partner_review",
                    name="Partner Review",
                    type=WorkflowStepType.HUMAN,
                    config={"message": "Revisão do sócio responsável"},
                    depends_on=["risk_matrix"]
                ),
            ],
            human_checkpoints=["partner_review"],
            icon="📊",
        )
        self.add_workflow(due_diligence)
        
        # Legal Research Workflow
        legal_research = DomainWorkflow(
            name="Legal Research",
            description="Pesquisa jurídica completa com jurisprudência e doutrina",
            steps=[
                WorkflowStep(
                    id="jurisprudence",
                    name="Search Jurisprudence",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "LegalResearcher", "focus": "jurisprudence"}
                ),
                WorkflowStep(
                    id="legislation",
                    name="Search Legislation",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "LegalResearcher", "focus": "legislation"}
                ),
                WorkflowStep(
                    id="synthesize",
                    name="Synthesize Findings",
                    type=WorkflowStepType.AGENT,
                    config={"agent": "DocumentDrafter"},
                    depends_on=["jurisprudence", "legislation"]
                ),
            ],
            icon="🔍",
        )
        self.add_workflow(legal_research)
    
    async def analyze_contract(
        self,
        contract_text: str,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """Analyze a contract."""
        logger.info("Analyzing contract (%s analysis)", analysis_type)
        
        # Use ContractAnalyst agent
        agent = self.get_agent_by_name("ContractAnalyst")
        
        # Get RAG context
        rag_context = await self.query_knowledge(
            f"Análise de contrato: {contract_text[:200]}..."
        )
        
        # Check compliance
        compliance = await self.check_compliance(contract_text)
        
        return {
            "analysis_type": analysis_type,
            "agent": agent.name if agent else "default",
            "clauses_found": self._extract_clauses(contract_text),
            "risks": self._identify_risks(contract_text),
            "compliance": {
                "is_compliant": compliance.is_compliant,
                "score": compliance.score,
                "violations": len(compliance.violations),
            },
            "rag_sources": len(rag_context.sources) if rag_context else 0,
        }
    
    def _extract_clauses(self, text: str) -> List[Dict]:
        """Extract clauses from contract text."""
        clauses = []
        
        # Simple clause detection
        clause_markers = ["CLÁUSULA", "Cláusula", "Art.", "Artigo", "§"]
        for marker in clause_markers:
            if marker in text:
                clauses.append({
                    "type": "identified",
                    "marker": marker,
                    "count": text.count(marker)
                })
        
        return clauses
    
    def _identify_risks(self, text: str) -> List[Dict]:
        """Identify risks in contract."""
        risks = []
        
        risk_keywords = {
            "high": ["rescisão imediata", "multa", "penalidade", "inadimplemento"],
            "medium": ["prazo", "renovação automática", "reajuste"],
            "low": ["notificação", "comunicação"]
        }
        
        for severity, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    risks.append({
                        "keyword": keyword,
                        "severity": severity
                    })
        
        return risks
    
    async def search_jurisprudence(
        self,
        query: str,
        courts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search legal jurisprudence."""
        logger.info("Searching jurisprudence: %s", query[:50])
        
        # Use GraphRAG for relationship-aware search
        rag = GraphRAGEngine(domain=self.domain_type)
        result = await rag.query(query, depth=2)
        
        return {
            "query": query,
            "courts": courts or ["STF", "STJ", "TST"],
            "results_count": len(result.entities_found),
            "answer": result.answer,
            "confidence": result.confidence,
        }


# Factory function
def create_legal_domain() -> LegalDomain:
    """Create Legal domain instance."""
    return LegalDomain()

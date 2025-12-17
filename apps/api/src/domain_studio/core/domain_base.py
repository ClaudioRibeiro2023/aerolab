"""
Base Domain Class - Classe base para todos os domínios especializados.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .types import (
    DomainType,
    DomainConfiguration,
    DomainAgent,
    DomainWorkflow,
    DomainCapability,
    RAGMode,
    RAGQuery,
    RAGResult,
    ComplianceCheck,
    RegulationType,
)

logger = logging.getLogger(__name__)


class BaseDomain(ABC):
    """
    Classe base abstrata para domínios especializados.
    
    Cada domínio deve implementar:
    - Agentes especializados
    - Workflows automatizados
    - Base de conhecimento
    - Regras de compliance
    """
    
    def __init__(self, config: Optional[DomainConfiguration] = None):
        self.config = config or self._get_default_config()
        self._agents: Dict[str, DomainAgent] = {}
        self._workflows: Dict[str, DomainWorkflow] = {}
        self._initialized = False
        
        logger.info("Initializing domain: %s", self.domain_type.value)
    
    @property
    @abstractmethod
    def domain_type(self) -> DomainType:
        """Return the domain type."""
        pass
    
    @abstractmethod
    def _get_default_config(self) -> DomainConfiguration:
        """Get default configuration for this domain."""
        pass
    
    @abstractmethod
    def _register_agents(self) -> None:
        """Register domain-specific agents."""
        pass
    
    @abstractmethod
    def _register_workflows(self) -> None:
        """Register domain-specific workflows."""
        pass
    
    # ============================================================
    # INITIALIZATION
    # ============================================================
    
    async def initialize(self) -> None:
        """Initialize the domain."""
        if self._initialized:
            return
        
        logger.info("Initializing domain: %s", self.domain_type.value)
        
        # Register agents
        self._register_agents()
        logger.info("Registered %d agents", len(self._agents))
        
        # Register workflows
        self._register_workflows()
        logger.info("Registered %d workflows", len(self._workflows))
        
        # Initialize knowledge base
        await self._initialize_knowledge()
        
        self._initialized = True
        logger.info("Domain %s initialized successfully", self.domain_type.value)
    
    async def _initialize_knowledge(self) -> None:
        """Initialize domain knowledge base."""
        # Override in subclasses
        pass
    
    # ============================================================
    # AGENT MANAGEMENT
    # ============================================================
    
    def add_agent(self, agent: DomainAgent) -> None:
        """Add an agent to this domain."""
        agent.domain = self.domain_type
        self._agents[agent.id] = agent
        logger.debug("Added agent: %s", agent.name)
    
    def get_agent(self, agent_id: str) -> Optional[DomainAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agent_by_name(self, name: str) -> Optional[DomainAgent]:
        """Get agent by name."""
        for agent in self._agents.values():
            if agent.name == name:
                return agent
        return None
    
    def list_agents(self) -> List[DomainAgent]:
        """List all agents in this domain."""
        return list(self._agents.values())
    
    # ============================================================
    # WORKFLOW MANAGEMENT
    # ============================================================
    
    def add_workflow(self, workflow: DomainWorkflow) -> None:
        """Add a workflow to this domain."""
        workflow.domain = self.domain_type
        self._workflows[workflow.id] = workflow
        logger.debug("Added workflow: %s", workflow.name)
    
    def get_workflow(self, workflow_id: str) -> Optional[DomainWorkflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self) -> List[DomainWorkflow]:
        """List all workflows in this domain."""
        return list(self._workflows.values())
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        logger.info("Executing workflow: %s", workflow.name)
        
        # Execute workflow steps
        results = {}
        for step in workflow.steps:
            try:
                step_result = await self._execute_step(step, inputs, results, context)
                results[step.id] = step_result
            except Exception as e:
                logger.error("Error in step %s: %s", step.name, str(e))
                if step.on_error == "fail":
                    raise
                elif step.on_error == "skip":
                    continue
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "status": "completed",
            "results": results,
        }
    
    async def _execute_step(
        self,
        step,
        inputs: Dict,
        previous_results: Dict,
        context: Optional[Dict]
    ) -> Any:
        """Execute a single workflow step."""
        # Override in subclasses for custom step execution
        return {"step": step.name, "status": "executed"}
    
    # ============================================================
    # RAG / KNOWLEDGE
    # ============================================================
    
    async def query_knowledge(
        self,
        query: str,
        mode: RAGMode = RAGMode.HYBRID,
        top_k: int = 10,
        **kwargs
    ) -> RAGResult:
        """Query the domain knowledge base."""
        rag_query = RAGQuery(
            query=query,
            domain=self.domain_type,
            mode=mode,
            top_k=top_k,
            **kwargs
        )
        
        # Override in subclasses with actual RAG implementation
        return RAGResult(
            query=query,
            answer="Knowledge query not implemented for this domain.",
            sources=[],
            confidence=0.0,
        )
    
    # ============================================================
    # COMPLIANCE
    # ============================================================
    
    async def check_compliance(
        self,
        content: str,
        regulations: Optional[List[RegulationType]] = None
    ) -> ComplianceCheck:
        """Check content for compliance with domain regulations."""
        regs = regulations or self.config.regulations
        
        # Override in subclasses with actual compliance logic
        return ComplianceCheck(
            content=content,
            regulations_checked=regs,
            is_compliant=True,
            score=100.0,
        )
    
    # ============================================================
    # CHAT
    # ============================================================
    
    async def chat(
        self,
        message: str,
        agent_name: Optional[str] = None,
        context: Optional[Dict] = None,
        use_rag: bool = True,
        check_compliance: bool = True
    ) -> Dict[str, Any]:
        """Chat with the domain."""
        # Select agent
        agent = None
        if agent_name:
            agent = self.get_agent_by_name(agent_name)
        
        if not agent and self._agents:
            # Use first available agent
            agent = list(self._agents.values())[0]
        
        # Get RAG context if enabled
        rag_context = None
        if use_rag and DomainCapability.RAG in self.config.capabilities:
            rag_result = await self.query_knowledge(message)
            rag_context = rag_result
        
        # Generate response (override in subclasses)
        response = await self._generate_response(
            message=message,
            agent=agent,
            rag_context=rag_context,
            context=context
        )
        
        # Check compliance if enabled
        compliance = None
        if check_compliance and DomainCapability.COMPLIANCE in self.config.capabilities:
            compliance = await self.check_compliance(response.get("content", ""))
        
        return {
            "domain": self.domain_type.value,
            "agent": agent.name if agent else None,
            "response": response,
            "rag_context": rag_context,
            "compliance": compliance,
        }
    
    async def _generate_response(
        self,
        message: str,
        agent: Optional[DomainAgent],
        rag_context: Optional[RAGResult],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate a response. Override in subclasses."""
        return {
            "content": f"Response from {self.domain_type.value} domain.",
            "agent": agent.name if agent else "default",
        }
    
    # ============================================================
    # UTILITIES
    # ============================================================
    
    def get_capabilities(self) -> List[DomainCapability]:
        """Get domain capabilities."""
        return self.config.capabilities
    
    def has_capability(self, capability: DomainCapability) -> bool:
        """Check if domain has a capability."""
        return capability in self.config.capabilities
    
    def get_info(self) -> Dict[str, Any]:
        """Get domain information."""
        return {
            "type": self.domain_type.value,
            "name": self.config.name,
            "description": self.config.description,
            "icon": self.config.icon,
            "color": self.config.color,
            "capabilities": [c.value for c in self.config.capabilities],
            "agents_count": len(self._agents),
            "workflows_count": len(self._workflows),
            "regulations": [r.value for r in self.config.regulations],
            "is_initialized": self._initialized,
        }

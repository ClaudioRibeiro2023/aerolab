"""
Domain Registry - Registro dinâmico de domínios e seus componentes.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from .types import (
    DomainType,
    DomainConfiguration,
    DomainAgent,
    DomainWorkflow,
    DomainKnowledge,
    DOMAIN_THEMES,
    DOMAIN_REGULATIONS,
)

logger = logging.getLogger(__name__)


class DomainRegistry:
    """
    Registry central para todos os domínios.
    
    Gerencia:
    - Configurações de domínios
    - Agentes por domínio
    - Workflows por domínio
    - Bases de conhecimento
    """
    
    _instance: Optional[DomainRegistry] = None
    
    def __new__(cls) -> DomainRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._domains: Dict[DomainType, DomainConfiguration] = {}
        self._agents: Dict[DomainType, Dict[str, DomainAgent]] = {}
        self._workflows: Dict[DomainType, Dict[str, DomainWorkflow]] = {}
        self._knowledge: Dict[DomainType, DomainKnowledge] = {}
        self._domain_classes: Dict[DomainType, Type] = {}
        
        # Initialize default domains
        self._initialize_default_domains()
        
        self._initialized = True
        logger.info("DomainRegistry initialized with %d domains", len(self._domains))
    
    def _initialize_default_domains(self) -> None:
        """Initialize all 15 default domains."""
        for domain_type in DomainType:
            theme = DOMAIN_THEMES.get(domain_type, {})
            regulations = DOMAIN_REGULATIONS.get(domain_type, [])
            
            config = DomainConfiguration(
                type=domain_type,
                name=theme.get("name", domain_type.value.title()),
                description=f"Domínio especializado em {theme.get('name', domain_type.value)}",
                icon=theme.get("icon", "📁"),
                color=theme.get("color", "#3B82F6"),
                gradient=theme.get("gradient", "from-blue-500 to-cyan-600"),
                regulations=regulations,
            )
            
            self._domains[domain_type] = config
            self._agents[domain_type] = {}
            self._workflows[domain_type] = {}
    
    # ============================================================
    # DOMAIN MANAGEMENT
    # ============================================================
    
    def get_domain(self, domain_type: DomainType) -> Optional[DomainConfiguration]:
        """Get domain configuration."""
        return self._domains.get(domain_type)
    
    def list_domains(self) -> List[DomainConfiguration]:
        """List all registered domains."""
        return list(self._domains.values())
    
    def update_domain(
        self,
        domain_type: DomainType,
        config: DomainConfiguration
    ) -> None:
        """Update domain configuration."""
        self._domains[domain_type] = config
        logger.info("Updated domain: %s", domain_type.value)
    
    def register_domain_class(
        self,
        domain_type: DomainType,
        domain_class: Type
    ) -> None:
        """Register a domain implementation class."""
        self._domain_classes[domain_type] = domain_class
        logger.info("Registered domain class: %s -> %s", 
                   domain_type.value, domain_class.__name__)
    
    def get_domain_class(self, domain_type: DomainType) -> Optional[Type]:
        """Get registered domain class."""
        return self._domain_classes.get(domain_type)
    
    # ============================================================
    # AGENT MANAGEMENT
    # ============================================================
    
    def register_agent(
        self,
        domain_type: DomainType,
        agent: DomainAgent
    ) -> None:
        """Register an agent for a domain."""
        if domain_type not in self._agents:
            self._agents[domain_type] = {}
        
        self._agents[domain_type][agent.id] = agent
        
        # Update domain config
        if domain_type in self._domains:
            if agent.name not in self._domains[domain_type].agents:
                self._domains[domain_type].agents.append(agent.name)
        
        logger.info("Registered agent: %s for domain %s", 
                   agent.name, domain_type.value)
    
    def get_agent(
        self,
        domain_type: DomainType,
        agent_id: str
    ) -> Optional[DomainAgent]:
        """Get agent by ID."""
        return self._agents.get(domain_type, {}).get(agent_id)
    
    def get_agent_by_name(
        self,
        domain_type: DomainType,
        name: str
    ) -> Optional[DomainAgent]:
        """Get agent by name."""
        agents = self._agents.get(domain_type, {})
        for agent in agents.values():
            if agent.name == name:
                return agent
        return None
    
    def list_agents(
        self,
        domain_type: Optional[DomainType] = None
    ) -> List[DomainAgent]:
        """List agents, optionally filtered by domain."""
        if domain_type:
            return list(self._agents.get(domain_type, {}).values())
        
        all_agents = []
        for agents in self._agents.values():
            all_agents.extend(agents.values())
        return all_agents
    
    # ============================================================
    # WORKFLOW MANAGEMENT
    # ============================================================
    
    def register_workflow(
        self,
        domain_type: DomainType,
        workflow: DomainWorkflow
    ) -> None:
        """Register a workflow for a domain."""
        if domain_type not in self._workflows:
            self._workflows[domain_type] = {}
        
        self._workflows[domain_type][workflow.id] = workflow
        
        # Update domain config
        if domain_type in self._domains:
            if workflow.name not in self._domains[domain_type].workflows:
                self._domains[domain_type].workflows.append(workflow.name)
        
        logger.info("Registered workflow: %s for domain %s", 
                   workflow.name, domain_type.value)
    
    def get_workflow(
        self,
        domain_type: DomainType,
        workflow_id: str
    ) -> Optional[DomainWorkflow]:
        """Get workflow by ID."""
        return self._workflows.get(domain_type, {}).get(workflow_id)
    
    def list_workflows(
        self,
        domain_type: Optional[DomainType] = None
    ) -> List[DomainWorkflow]:
        """List workflows, optionally filtered by domain."""
        if domain_type:
            return list(self._workflows.get(domain_type, {}).values())
        
        all_workflows = []
        for workflows in self._workflows.values():
            all_workflows.extend(workflows.values())
        return all_workflows
    
    # ============================================================
    # KNOWLEDGE MANAGEMENT
    # ============================================================
    
    def set_knowledge(
        self,
        domain_type: DomainType,
        knowledge: DomainKnowledge
    ) -> None:
        """Set knowledge base for a domain."""
        self._knowledge[domain_type] = knowledge
        logger.info("Set knowledge base for domain: %s", domain_type.value)
    
    def get_knowledge(
        self,
        domain_type: DomainType
    ) -> Optional[DomainKnowledge]:
        """Get knowledge base for a domain."""
        return self._knowledge.get(domain_type)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        total_agents = sum(len(agents) for agents in self._agents.values())
        total_workflows = sum(len(wf) for wf in self._workflows.values())
        
        return {
            "total_domains": len(self._domains),
            "total_agents": total_agents,
            "total_workflows": total_workflows,
            "domains_with_knowledge": len(self._knowledge),
            "domains": {
                dt.value: {
                    "agents": len(self._agents.get(dt, {})),
                    "workflows": len(self._workflows.get(dt, {})),
                    "has_knowledge": dt in self._knowledge,
                }
                for dt in DomainType
            }
        }


# Singleton accessor
_registry: Optional[DomainRegistry] = None


def get_domain_registry() -> DomainRegistry:
    """Get the singleton domain registry instance."""
    global _registry
    if _registry is None:
        _registry = DomainRegistry()
    return _registry

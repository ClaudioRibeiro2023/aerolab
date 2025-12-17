"""
Agno Flow Studio v3.0 - Workflow Optimizer

AI-powered workflow optimization suggestions.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from ..types import Workflow, Node, NodeType


class OptimizationType(str, Enum):
    """Types of optimization suggestions."""
    PERFORMANCE = "performance"
    COST = "cost"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"


class OptimizationPriority(str, Enum):
    """Priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationSuggestion:
    """A single optimization suggestion."""
    type: OptimizationType
    priority: OptimizationPriority
    title: str
    description: str
    impact: str
    node_ids: List[str] = field(default_factory=list)
    auto_fixable: bool = False
    fix_action: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "nodeIds": self.node_ids,
            "autoFixable": self.auto_fixable,
            "fixAction": self.fix_action,
        }


class WorkflowOptimizer:
    """
    Workflow Optimizer.
    
    Analyzes workflows and provides optimization suggestions.
    
    Categories:
    - Performance: Parallel execution, caching
    - Cost: Model selection, token optimization
    - Reliability: Error handling, retries
    - Security: PII detection, secret management
    - Maintainability: Simplification, documentation
    """
    
    def analyze(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze workflow and return optimization suggestions."""
        suggestions = []
        
        # Performance optimizations
        suggestions.extend(self._analyze_performance(workflow))
        
        # Cost optimizations
        suggestions.extend(self._analyze_cost(workflow))
        
        # Reliability optimizations
        suggestions.extend(self._analyze_reliability(workflow))
        
        # Security optimizations
        suggestions.extend(self._analyze_security(workflow))
        
        # Maintainability optimizations
        suggestions.extend(self._analyze_maintainability(workflow))
        
        # Sort by priority
        priority_order = {OptimizationPriority.HIGH: 0, OptimizationPriority.MEDIUM: 1, OptimizationPriority.LOW: 2}
        suggestions.sort(key=lambda s: priority_order[s.priority])
        
        return suggestions
    
    def _analyze_performance(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze performance optimizations."""
        suggestions = []
        
        # Check for parallelization opportunities
        parallel_candidates = self._find_parallel_candidates(workflow)
        if len(parallel_candidates) >= 2:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                priority=OptimizationPriority.MEDIUM,
                title="Parallelization Opportunity",
                description=f"Found {len(parallel_candidates)} nodes that could run in parallel",
                impact="Could reduce execution time by up to 50%",
                node_ids=parallel_candidates,
                auto_fixable=True,
                fix_action="add_parallel_node",
            ))
        
        # Check for missing cache
        agent_nodes = [n for n in workflow.nodes if n.node_type == NodeType.AGENT]
        has_cache = any(n.node_type == NodeType.CACHE for n in workflow.nodes)
        
        if len(agent_nodes) > 1 and not has_cache:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                priority=OptimizationPriority.LOW,
                title="Add Caching",
                description="Multiple agent nodes detected without caching",
                impact="Could reduce API calls and costs for repeated inputs",
                node_ids=[n.id for n in agent_nodes],
                auto_fixable=True,
                fix_action="add_cache_node",
            ))
        
        return suggestions
    
    def _analyze_cost(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze cost optimizations."""
        suggestions = []
        
        # Check for expensive models
        expensive_models = ["gpt-4o", "gpt-4", "claude-3-opus"]
        cheaper_alternatives = {"gpt-4o": "gpt-4o-mini", "gpt-4": "gpt-4o-mini", "claude-3-opus": "claude-3-5-sonnet"}
        
        for node in workflow.nodes:
            if node.node_type == NodeType.AGENT:
                model = node.config.get("model", "")
                if model in expensive_models:
                    suggestions.append(OptimizationSuggestion(
                        type=OptimizationType.COST,
                        priority=OptimizationPriority.MEDIUM,
                        title=f"Consider Cheaper Model for '{node.label}'",
                        description=f"Using {model} which is expensive. Consider {cheaper_alternatives.get(model, 'a smaller model')}",
                        impact="Could reduce costs by 50-90%",
                        node_ids=[node.id],
                        auto_fixable=True,
                        fix_action=f"change_model:{cheaper_alternatives.get(model, 'gpt-4o-mini')}",
                    ))
        
        # Check for cost guard
        has_cost_guard = any(n.node_type == NodeType.COST_GUARD for n in workflow.nodes)
        if not has_cost_guard and len(workflow.nodes) > 5:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.COST,
                priority=OptimizationPriority.LOW,
                title="Add Cost Guard",
                description="No cost limit set for this workflow",
                impact="Prevents runaway costs from loops or errors",
                auto_fixable=True,
                fix_action="add_cost_guard",
            ))
        
        return suggestions
    
    def _analyze_reliability(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze reliability optimizations."""
        suggestions = []
        
        # Check for error handling
        has_retry = any(n.node_type == NodeType.RETRY for n in workflow.nodes)
        has_circuit_breaker = any(n.node_type == NodeType.CIRCUIT_BREAKER for n in workflow.nodes)
        
        http_nodes = [n for n in workflow.nodes if n.node_type == NodeType.HTTP]
        if http_nodes and not has_retry:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.RELIABILITY,
                priority=OptimizationPriority.HIGH,
                title="Add Retry Logic for HTTP Calls",
                description="HTTP requests can fail. Add retry logic for resilience.",
                impact="Improves success rate by handling transient failures",
                node_ids=[n.id for n in http_nodes],
                auto_fixable=True,
                fix_action="wrap_with_retry",
            ))
        
        agent_nodes = [n for n in workflow.nodes if n.node_type == NodeType.AGENT]
        if len(agent_nodes) > 3 and not has_circuit_breaker:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.RELIABILITY,
                priority=OptimizationPriority.MEDIUM,
                title="Add Circuit Breaker",
                description="Multiple agent calls without circuit breaker",
                impact="Prevents cascade failures when API is down",
                auto_fixable=True,
                fix_action="add_circuit_breaker",
            ))
        
        return suggestions
    
    def _analyze_security(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze security optimizations."""
        suggestions = []
        
        # Check for PII detection
        has_pii_detector = any(n.node_type == NodeType.PII_DETECTOR for n in workflow.nodes)
        input_nodes = workflow.get_input_nodes()
        
        if input_nodes and not has_pii_detector:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.SECURITY,
                priority=OptimizationPriority.MEDIUM,
                title="Consider PII Detection",
                description="Input data may contain PII. Consider adding PII detection.",
                impact="Helps comply with privacy regulations",
                auto_fixable=True,
                fix_action="add_pii_detector",
            ))
        
        # Check for hardcoded secrets
        for node in workflow.nodes:
            config_str = str(node.config).lower()
            if any(kw in config_str for kw in ["api_key", "password", "secret", "token"]):
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.SECURITY,
                    priority=OptimizationPriority.HIGH,
                    title=f"Possible Hardcoded Secret in '{node.label}'",
                    description="Configuration may contain hardcoded secrets",
                    impact="Security risk - use Secret Fetch node instead",
                    node_ids=[node.id],
                    auto_fixable=False,
                ))
        
        return suggestions
    
    def _analyze_maintainability(self, workflow: Workflow) -> List[OptimizationSuggestion]:
        """Analyze maintainability optimizations."""
        suggestions = []
        
        # Check for very long workflows
        if len(workflow.nodes) > 15:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MAINTAINABILITY,
                priority=OptimizationPriority.LOW,
                title="Consider Breaking Down Workflow",
                description=f"Workflow has {len(workflow.nodes)} nodes. Consider sub-workflows.",
                impact="Improves maintainability and reusability",
                auto_fixable=False,
            ))
        
        # Check for missing descriptions
        nodes_without_desc = [n for n in workflow.nodes if not n.description]
        if len(nodes_without_desc) > len(workflow.nodes) / 2:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.MAINTAINABILITY,
                priority=OptimizationPriority.LOW,
                title="Add Node Descriptions",
                description=f"{len(nodes_without_desc)} nodes have no description",
                impact="Improves understanding and documentation",
                node_ids=[n.id for n in nodes_without_desc],
                auto_fixable=False,
            ))
        
        return suggestions
    
    def _find_parallel_candidates(self, workflow: Workflow) -> List[str]:
        """Find nodes that could run in parallel."""
        candidates = []
        
        # Simple heuristic: nodes with same parent and no dependencies between them
        for node in workflow.nodes:
            incoming = workflow.get_incoming_edges(node.id)
            if len(incoming) == 1:
                parent_id = incoming[0].source
                siblings = [
                    n for n in workflow.nodes
                    if n.id != node.id and
                    len(workflow.get_incoming_edges(n.id)) == 1 and
                    workflow.get_incoming_edges(n.id)[0].source == parent_id
                ]
                if siblings:
                    candidates.append(node.id)
        
        return list(set(candidates))
    
    def apply_fix(self, workflow: Workflow, fix_action: str) -> Workflow:
        """Apply an auto-fix to the workflow."""
        if fix_action.startswith("change_model:"):
            new_model = fix_action.split(":")[1]
            for node in workflow.nodes:
                if node.node_type == NodeType.AGENT:
                    node.config["model"] = new_model
        
        # Other fix actions would be implemented here
        
        return workflow

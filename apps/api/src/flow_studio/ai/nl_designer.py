"""
Agno Flow Studio v3.0 - Natural Language Designer

Convert natural language descriptions to workflows.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from ..types import Workflow, Node, Connection, NodeType, NodeCategory, Port, Position, DataType, PortType

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Detected workflow intent types."""
    AUTOMATION = "automation"
    DATA_PROCESSING = "data_processing"
    AI_AGENT = "ai_agent"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    CUSTOMER_SERVICE = "customer_service"
    CONTENT_GENERATION = "content_generation"
    RESEARCH = "research"
    UNKNOWN = "unknown"


@dataclass
class WorkflowSuggestion:
    """A suggested workflow from natural language."""
    workflow: Workflow
    confidence: float
    intent: IntentType
    explanation: str
    alternatives: List["WorkflowSuggestion"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "workflow": self.workflow.to_dict(),
            "confidence": self.confidence,
            "intent": self.intent.value,
            "explanation": self.explanation,
            "alternatives": [a.to_dict() for a in self.alternatives],
        }


class NLWorkflowDesigner:
    """
    Natural Language to Workflow Designer.
    
    Converts natural language descriptions into executable workflows.
    Uses LLM to understand intent and generate workflow structure.
    
    Features:
    - Intent detection
    - Template matching
    - Step-by-step refinement
    - Multi-language support
    """
    
    # Workflow templates for common intents
    TEMPLATES = {
        IntentType.AI_AGENT: {
            "name": "AI Agent Workflow",
            "nodes": [
                {"type": "input", "label": "User Input"},
                {"type": "agent", "label": "AI Agent"},
                {"type": "output", "label": "Response"},
            ],
            "connections": [(0, 1), (1, 2)],
        },
        IntentType.DATA_PROCESSING: {
            "name": "Data Processing Pipeline",
            "nodes": [
                {"type": "input", "label": "Data Input"},
                {"type": "transform", "label": "Transform"},
                {"type": "filter", "label": "Filter"},
                {"type": "output", "label": "Processed Data"},
            ],
            "connections": [(0, 1), (1, 2), (2, 3)],
        },
        IntentType.CUSTOMER_SERVICE: {
            "name": "Customer Service Bot",
            "nodes": [
                {"type": "input", "label": "Customer Message"},
                {"type": "agent", "label": "Intent Classifier"},
                {"type": "condition", "label": "Route by Intent"},
                {"type": "agent", "label": "Support Agent"},
                {"type": "agent", "label": "Sales Agent"},
                {"type": "output", "label": "Response"},
            ],
            "connections": [(0, 1), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)],
        },
        IntentType.CONTENT_GENERATION: {
            "name": "Content Generation Pipeline",
            "nodes": [
                {"type": "input", "label": "Topic/Brief"},
                {"type": "agent", "label": "Researcher"},
                {"type": "agent", "label": "Writer"},
                {"type": "agent", "label": "Editor"},
                {"type": "output", "label": "Final Content"},
            ],
            "connections": [(0, 1), (1, 2), (2, 3), (3, 4)],
        },
        IntentType.RESEARCH: {
            "name": "Research Assistant",
            "nodes": [
                {"type": "input", "label": "Research Query"},
                {"type": "rag-search", "label": "Knowledge Search"},
                {"type": "agent", "label": "Analyst"},
                {"type": "output", "label": "Research Summary"},
            ],
            "connections": [(0, 1), (1, 2), (2, 3)],
        },
    }
    
    # Keywords for intent detection
    INTENT_KEYWORDS = {
        IntentType.AI_AGENT: ["agent", "ai", "llm", "chatbot", "assistant", "gpt", "claude"],
        IntentType.DATA_PROCESSING: ["data", "transform", "etl", "pipeline", "process", "convert"],
        IntentType.CUSTOMER_SERVICE: ["customer", "support", "service", "help", "ticket", "inquiry"],
        IntentType.CONTENT_GENERATION: ["content", "write", "generate", "article", "blog", "copy"],
        IntentType.RESEARCH: ["research", "search", "find", "analyze", "investigate", "study"],
        IntentType.INTEGRATION: ["integrate", "connect", "api", "webhook", "sync"],
        IntentType.AUTOMATION: ["automate", "schedule", "trigger", "workflow", "routine"],
        IntentType.MONITORING: ["monitor", "alert", "watch", "track", "notify"],
    }
    
    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm_model = llm_model
    
    async def design_workflow(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> WorkflowSuggestion:
        """
        Generate a workflow from natural language description.
        
        Args:
            description: Natural language description of desired workflow
            context: Additional context (existing nodes, variables, etc.)
            language: Language of the description
            
        Returns:
            WorkflowSuggestion with generated workflow
        """
        # Detect intent
        intent = self._detect_intent(description)
        
        # Get base template
        template = self.TEMPLATES.get(intent, self.TEMPLATES[IntentType.AI_AGENT])
        
        # Generate workflow from template
        workflow = self._generate_from_template(template, description, intent)
        
        # Enhance with LLM if available
        try:
            workflow = await self._enhance_with_llm(workflow, description, context)
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
        
        # Calculate confidence
        confidence = self._calculate_confidence(description, intent, workflow)
        
        # Generate explanation
        explanation = self._generate_explanation(description, intent, workflow)
        
        return WorkflowSuggestion(
            workflow=workflow,
            confidence=confidence,
            intent=intent,
            explanation=explanation,
        )
    
    def _detect_intent(self, description: str) -> IntentType:
        """Detect the primary intent from description."""
        description_lower = description.lower()
        
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in description_lower)
            scores[intent] = score
        
        if not scores or max(scores.values()) == 0:
            return IntentType.UNKNOWN
        
        return max(scores, key=scores.get)
    
    def _generate_from_template(
        self,
        template: Dict,
        description: str,
        intent: IntentType
    ) -> Workflow:
        """Generate workflow from template."""
        workflow = Workflow(
            name=template.get("name", "Generated Workflow"),
            description=description,
        )
        
        # Create nodes
        node_map = {}
        x, y = 100, 100
        
        for i, node_def in enumerate(template.get("nodes", [])):
            node_type = NodeType(node_def["type"]) if node_def["type"] in [e.value for e in NodeType] else NodeType.AGENT
            category = self._get_category_for_type(node_type)
            
            node = Node(
                type="custom",
                position=Position(x=x, y=y),
                label=node_def.get("label", f"Node {i+1}"),
                node_type=node_type,
                category=category,
                inputs=self._get_default_inputs(node_type),
                outputs=self._get_default_outputs(node_type),
                config=node_def.get("config", {}),
            )
            
            workflow.nodes.append(node)
            node_map[i] = node.id
            
            x += 250
            if (i + 1) % 4 == 0:
                x = 100
                y += 150
        
        # Create connections
        for source_idx, target_idx in template.get("connections", []):
            if source_idx in node_map and target_idx in node_map:
                conn = Connection(
                    source=node_map[source_idx],
                    target=node_map[target_idx],
                )
                workflow.edges.append(conn)
        
        return workflow
    
    def _get_category_for_type(self, node_type: NodeType) -> NodeCategory:
        """Get category for a node type."""
        type_to_category = {
            NodeType.AGENT: NodeCategory.AGENTS,
            NodeType.TEAM: NodeCategory.AGENTS,
            NodeType.CONDITION: NodeCategory.LOGIC,
            NodeType.LOOP: NodeCategory.LOGIC,
            NodeType.TRANSFORM: NodeCategory.DATA,
            NodeType.FILTER: NodeCategory.DATA,
            NodeType.MEMORY_READ: NodeCategory.MEMORY,
            NodeType.RAG_SEARCH: NodeCategory.MEMORY,
            NodeType.HTTP: NodeCategory.INTEGRATIONS,
            NodeType.HUMAN_APPROVAL: NodeCategory.GOVERNANCE,
            NodeType.INPUT: NodeCategory.INPUT,
            NodeType.OUTPUT: NodeCategory.OUTPUT,
        }
        return type_to_category.get(node_type, NodeCategory.AGENTS)
    
    def _get_default_inputs(self, node_type: NodeType) -> List[Port]:
        """Get default input ports for a node type."""
        if node_type == NodeType.INPUT:
            return []
        return [Port(name="input", type=PortType.INPUT, data_type=DataType.ANY, required=True)]
    
    def _get_default_outputs(self, node_type: NodeType) -> List[Port]:
        """Get default output ports for a node type."""
        if node_type == NodeType.OUTPUT:
            return []
        return [Port(name="output", type=PortType.OUTPUT, data_type=DataType.ANY)]
    
    async def _enhance_with_llm(
        self,
        workflow: Workflow,
        description: str,
        context: Optional[Dict]
    ) -> Workflow:
        """Enhance workflow using LLM."""
        # In a real implementation, this would call the LLM to:
        # 1. Add appropriate instructions to agent nodes
        # 2. Configure conditions based on description
        # 3. Add missing nodes
        # 4. Optimize the workflow structure
        
        # For now, add basic configurations
        for node in workflow.nodes:
            if node.node_type == NodeType.AGENT:
                node.config["model"] = self.llm_model
                node.config["instructions"] = f"You are part of a workflow to: {description}"
            elif node.node_type == NodeType.CONDITION:
                node.config["condition"] = "value != None"
        
        return workflow
    
    def _calculate_confidence(
        self,
        description: str,
        intent: IntentType,
        workflow: Workflow
    ) -> float:
        """Calculate confidence score for the suggestion."""
        base_confidence = 0.5
        
        # Boost for matching intent
        if intent != IntentType.UNKNOWN:
            base_confidence += 0.2
        
        # Boost for more specific description
        word_count = len(description.split())
        if word_count > 10:
            base_confidence += 0.1
        if word_count > 20:
            base_confidence += 0.1
        
        # Cap at 0.95
        return min(base_confidence, 0.95)
    
    def _generate_explanation(
        self,
        description: str,
        intent: IntentType,
        workflow: Workflow
    ) -> str:
        """Generate explanation of the workflow."""
        node_names = [n.label for n in workflow.nodes]
        
        return f"""Based on your description, I detected a '{intent.value}' workflow pattern.

I've created a workflow with {len(workflow.nodes)} nodes:
{', '.join(node_names)}

The workflow will:
1. Receive input through the '{workflow.nodes[0].label if workflow.nodes else 'Input'}' node
2. Process it through the intermediate steps
3. Return the result through the output node

You can customize each node's configuration by clicking on it."""
    
    def suggest_next_node(
        self,
        current_nodes: List[Node],
        last_node: Node
    ) -> List[Dict]:
        """Suggest next nodes based on context."""
        suggestions = []
        
        # Common follow-ups based on node type
        follow_ups = {
            NodeType.INPUT: [NodeType.AGENT, NodeType.TRANSFORM, NodeType.RAG_SEARCH],
            NodeType.AGENT: [NodeType.AGENT, NodeType.CONDITION, NodeType.OUTPUT, NodeType.TRANSFORM],
            NodeType.CONDITION: [NodeType.AGENT, NodeType.OUTPUT],
            NodeType.TRANSFORM: [NodeType.AGENT, NodeType.OUTPUT, NodeType.HTTP],
            NodeType.RAG_SEARCH: [NodeType.AGENT],
            NodeType.HTTP: [NodeType.TRANSFORM, NodeType.OUTPUT],
        }
        
        suggested_types = follow_ups.get(last_node.node_type, [NodeType.OUTPUT])
        
        for node_type in suggested_types:
            suggestions.append({
                "type": node_type.value,
                "label": f"Add {node_type.value.replace('-', ' ').title()}",
                "reason": f"Common follow-up for {last_node.node_type.value}",
            })
        
        return suggestions

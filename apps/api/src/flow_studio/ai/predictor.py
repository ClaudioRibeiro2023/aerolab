"""
Agno Flow Studio v3.0 - Cost and Execution Predictor

Predict execution time, cost, and resource usage.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from ..types import Workflow, Node, NodeType


@dataclass
class CostPrediction:
    """Cost prediction result."""
    total_cost: float
    cost_breakdown: Dict[str, float]
    confidence: float
    assumptions: List[str]
    
    def to_dict(self) -> dict:
        return {
            "totalCost": self.total_cost,
            "costBreakdown": self.cost_breakdown,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
        }


@dataclass
class ExecutionPrediction:
    """Execution time prediction."""
    estimated_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    bottleneck_node: Optional[str]
    parallel_opportunities: int
    
    def to_dict(self) -> dict:
        return {
            "estimatedDurationMs": self.estimated_duration_ms,
            "minDurationMs": self.min_duration_ms,
            "maxDurationMs": self.max_duration_ms,
            "bottleneckNode": self.bottleneck_node,
            "parallelOpportunities": self.parallel_opportunities,
        }


@dataclass
class ResourcePrediction:
    """Resource usage prediction."""
    estimated_tokens: int
    estimated_api_calls: int
    estimated_memory_mb: float
    
    def to_dict(self) -> dict:
        return {
            "estimatedTokens": self.estimated_tokens,
            "estimatedApiCalls": self.estimated_api_calls,
            "estimatedMemoryMb": self.estimated_memory_mb,
        }


class CostPredictor:
    """
    Predicts workflow execution cost.
    
    Based on:
    - Model pricing
    - Estimated token usage
    - API call counts
    - Historical data (when available)
    """
    
    # Model costs per 1K tokens (input/output averaged)
    MODEL_COSTS = {
        "gpt-4o": 0.015,
        "gpt-4o-mini": 0.0003,
        "gpt-4": 0.045,
        "gpt-3.5-turbo": 0.002,
        "claude-3-5-sonnet": 0.009,
        "claude-3-opus": 0.045,
        "claude-3-haiku": 0.00075,
    }
    
    # Average tokens per node type
    AVG_TOKENS = {
        NodeType.AGENT: 2000,
        NodeType.RAG_SEARCH: 500,
        NodeType.TRANSFORM: 100,
        NodeType.HTTP: 0,
        NodeType.CONDITION: 0,
    }
    
    def predict(
        self,
        workflow: Workflow,
        input_size: int = 500,
        iterations: int = 1
    ) -> CostPrediction:
        """Predict workflow execution cost."""
        cost_breakdown = {}
        assumptions = []
        
        total_cost = 0.0
        
        for node in workflow.nodes:
            node_cost = self._estimate_node_cost(node, input_size)
            if node_cost > 0:
                cost_breakdown[node.label] = node_cost * iterations
                total_cost += node_cost * iterations
        
        # Add assumptions
        assumptions.append(f"Assuming {input_size} input tokens")
        assumptions.append(f"Assuming {iterations} iteration(s)")
        
        # Calculate confidence based on how many unknowns
        unknown_models = sum(1 for n in workflow.nodes 
                           if n.node_type == NodeType.AGENT 
                           and n.config.get("model", "") not in self.MODEL_COSTS)
        confidence = 0.9 - (unknown_models * 0.1)
        
        return CostPrediction(
            total_cost=round(total_cost, 6),
            cost_breakdown=cost_breakdown,
            confidence=max(0.5, confidence),
            assumptions=assumptions,
        )
    
    def _estimate_node_cost(self, node: Node, input_size: int) -> float:
        """Estimate cost for a single node."""
        if node.node_type != NodeType.AGENT:
            return 0.0
        
        model = node.config.get("model", "gpt-4o-mini")
        cost_per_1k = self.MODEL_COSTS.get(model, 0.01)
        
        # Estimate tokens: input + avg output
        avg_output = self.AVG_TOKENS.get(node.node_type, 1000)
        estimated_tokens = input_size + avg_output
        
        return (estimated_tokens / 1000) * cost_per_1k


class ExecutionPredictor:
    """
    Predicts workflow execution time.
    
    Based on:
    - Node type latencies
    - Parallel vs sequential execution
    - Historical data (when available)
    """
    
    # Average latency per node type (ms)
    NODE_LATENCIES = {
        NodeType.INPUT: 10,
        NodeType.OUTPUT: 10,
        NodeType.AGENT: 3000,  # 3 seconds average
        NodeType.TEAM: 10000,  # 10 seconds average
        NodeType.CONDITION: 5,
        NodeType.LOOP: 10,
        NodeType.PARALLEL: 10,
        NodeType.JOIN: 10,
        NodeType.TRANSFORM: 50,
        NodeType.HTTP: 500,
        NodeType.DATABASE: 200,
        NodeType.RAG_SEARCH: 1000,
        NodeType.MEMORY_READ: 100,
        NodeType.MEMORY_WRITE: 100,
        NodeType.DELAY: 1000,  # Default 1 second
        NodeType.CACHE: 10,
        NodeType.HUMAN_APPROVAL: 60000,  # 1 minute average
    }
    
    def predict(
        self,
        workflow: Workflow,
        include_human_nodes: bool = True
    ) -> ExecutionPrediction:
        """Predict workflow execution time."""
        
        # Calculate critical path (longest path through workflow)
        critical_path = self._calculate_critical_path(workflow)
        
        # Sum latencies along critical path
        total_latency = 0.0
        bottleneck_node = None
        max_node_latency = 0
        
        for node_id in critical_path:
            node = workflow.get_node(node_id)
            if not node:
                continue
            
            if not include_human_nodes and node.node_type == NodeType.HUMAN_APPROVAL:
                continue
            
            latency = self._get_node_latency(node)
            total_latency += latency
            
            if latency > max_node_latency:
                max_node_latency = latency
                bottleneck_node = node.label
        
        # Find parallel opportunities
        parallel_opps = self._count_parallel_opportunities(workflow)
        
        # Calculate min/max with variance
        variance = 0.3  # 30% variance
        
        return ExecutionPrediction(
            estimated_duration_ms=total_latency,
            min_duration_ms=total_latency * (1 - variance),
            max_duration_ms=total_latency * (1 + variance),
            bottleneck_node=bottleneck_node,
            parallel_opportunities=parallel_opps,
        )
    
    def _get_node_latency(self, node: Node) -> float:
        """Get estimated latency for a node."""
        base_latency = self.NODE_LATENCIES.get(node.node_type, 100)
        
        # Adjust for specific configurations
        if node.node_type == NodeType.DELAY:
            seconds = node.config.get("seconds", 1)
            base_latency = seconds * 1000
        elif node.node_type == NodeType.AGENT:
            # Larger models are slightly slower
            model = node.config.get("model", "")
            if "gpt-4" in model and "mini" not in model:
                base_latency *= 1.5
        
        return base_latency
    
    def _calculate_critical_path(self, workflow: Workflow) -> List[str]:
        """Calculate the critical path (longest path) through the workflow."""
        if not workflow.nodes:
            return []
        
        # Find start nodes (no incoming edges)
        start_nodes = [
            n.id for n in workflow.nodes 
            if not workflow.get_incoming_edges(n.id)
        ]
        
        if not start_nodes:
            start_nodes = [workflow.nodes[0].id]
        
        # BFS/DFS to find longest path
        longest_path = []
        
        def dfs(node_id: str, current_path: List[str]):
            nonlocal longest_path
            current_path = current_path + [node_id]
            
            outgoing = workflow.get_outgoing_edges(node_id)
            
            if not outgoing:
                if len(current_path) > len(longest_path):
                    longest_path = current_path
            else:
                for edge in outgoing:
                    dfs(edge.target, current_path)
        
        for start in start_nodes:
            dfs(start, [])
        
        return longest_path
    
    def _count_parallel_opportunities(self, workflow: Workflow) -> int:
        """Count nodes that could run in parallel."""
        opportunities = 0
        
        for node in workflow.nodes:
            outgoing = workflow.get_outgoing_edges(node.id)
            if len(outgoing) > 1:
                # This node fans out to multiple nodes
                opportunities += len(outgoing) - 1
        
        return opportunities
    
    def predict_resources(self, workflow: Workflow) -> ResourcePrediction:
        """Predict resource usage."""
        estimated_tokens = 0
        estimated_api_calls = 0
        estimated_memory = 50.0  # Base memory in MB
        
        for node in workflow.nodes:
            if node.node_type == NodeType.AGENT:
                estimated_tokens += 2000  # Average tokens
                estimated_api_calls += 1
                estimated_memory += 10  # Additional memory per agent
            elif node.node_type == NodeType.RAG_SEARCH:
                estimated_tokens += 500
                estimated_api_calls += 1
                estimated_memory += 50  # Vector store memory
            elif node.node_type == NodeType.HTTP:
                estimated_api_calls += 1
        
        return ResourcePrediction(
            estimated_tokens=estimated_tokens,
            estimated_api_calls=estimated_api_calls,
            estimated_memory_mb=estimated_memory,
        )

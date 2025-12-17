"""
Agno Flow Studio v3.0 - Workflow Validation

Validates workflows for correctness and best practices.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from .types import Workflow, Node, Connection, NodeType, DataType


class ValidationSeverity(str, Enum):
    """Validation issue severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    message: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "message": self.message,
            "nodeId": self.node_id,
            "edgeId": self.edge_id,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of workflow validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def to_dict(self) -> dict:
        return {
            "isValid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "errorCount": len(self.errors),
            "warningCount": len(self.warnings),
        }


class WorkflowValidator:
    """
    Validates workflows for correctness.
    
    Checks:
    - Has input and output nodes
    - No orphan nodes
    - No cycles (for non-loop nodes)
    - Required ports connected
    - Type compatibility
    - Configuration validity
    """
    
    def validate(self, workflow: Workflow) -> ValidationResult:
        """Validate a workflow."""
        issues: List[ValidationIssue] = []
        
        # Check for input nodes
        input_nodes = workflow.get_input_nodes()
        if not input_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Workflow must have at least one Input node",
                suggestion="Add an Input node to define workflow entry point"
            ))
        
        # Check for output nodes
        output_nodes = workflow.get_output_nodes()
        if not output_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Workflow must have at least one Output node",
                suggestion="Add an Output node to define workflow result"
            ))
        
        # Check for orphan nodes
        issues.extend(self._check_orphan_nodes(workflow))
        
        # Check for cycles
        issues.extend(self._check_cycles(workflow))
        
        # Check required connections
        issues.extend(self._check_required_connections(workflow))
        
        # Check type compatibility
        issues.extend(self._check_type_compatibility(workflow))
        
        # Check node configurations
        issues.extend(self._check_node_configs(workflow))
        
        # Check for best practices
        issues.extend(self._check_best_practices(workflow))
        
        is_valid = not any(i.severity == ValidationSeverity.ERROR for i in issues)
        
        return ValidationResult(is_valid=is_valid, issues=issues)
    
    def _check_orphan_nodes(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check for nodes with no connections."""
        issues = []
        
        for node in workflow.nodes:
            # Input nodes don't need incoming connections
            if node.node_type == NodeType.INPUT:
                if not workflow.get_outgoing_edges(node.id):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Input node '{node.label}' has no outgoing connections",
                        node_id=node.id,
                        suggestion="Connect this node to start the workflow"
                    ))
            # Output nodes don't need outgoing connections
            elif node.node_type == NodeType.OUTPUT:
                if not workflow.get_incoming_edges(node.id):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Output node '{node.label}' has no incoming connections",
                        node_id=node.id,
                        suggestion="Connect a node to provide output data"
                    ))
            else:
                incoming = workflow.get_incoming_edges(node.id)
                outgoing = workflow.get_outgoing_edges(node.id)
                
                if not incoming and not outgoing:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Node '{node.label}' is not connected to any other node",
                        node_id=node.id,
                        suggestion="Connect this node or remove it"
                    ))
        
        return issues
    
    def _check_cycles(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check for cycles in the workflow (except loops)."""
        issues = []
        
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for edge in workflow.get_outgoing_edges(node_id):
                target = edge.target
                node = workflow.get_node(target)
                
                # Skip loop nodes as they intentionally create cycles
                if node and node.node_type == NodeType.LOOP:
                    continue
                
                if target not in visited:
                    if dfs(target):
                        return True
                elif target in rec_stack:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Cycle detected involving node '{node.label if node else target}'",
                        node_id=target,
                        suggestion="Remove the connection creating the cycle or use a Loop node"
                    ))
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in workflow.nodes:
            if node.id not in visited:
                dfs(node.id)
        
        return issues
    
    def _check_required_connections(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check that required ports are connected."""
        issues = []
        
        for node in workflow.nodes:
            incoming = workflow.get_incoming_edges(node.id)
            connected_handles = {e.target_handle for e in incoming if e.target_handle}
            
            for port in node.inputs:
                if port.required and port.id not in connected_handles and port.name not in connected_handles:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Required port '{port.name}' on node '{node.label}' is not connected",
                        node_id=node.id,
                        suggestion=f"Connect a node to the '{port.name}' port"
                    ))
        
        return issues
    
    def _check_type_compatibility(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check that connected ports have compatible types."""
        issues = []
        
        for edge in workflow.edges:
            source_node = workflow.get_node(edge.source)
            target_node = workflow.get_node(edge.target)
            
            if not source_node or not target_node:
                continue
            
            # Find source port
            source_port = None
            if edge.source_handle:
                source_port = next(
                    (p for p in source_node.outputs if p.id == edge.source_handle or p.name == edge.source_handle),
                    None
                )
            elif source_node.outputs:
                source_port = source_node.outputs[0]
            
            # Find target port
            target_port = None
            if edge.target_handle:
                target_port = next(
                    (p for p in target_node.inputs if p.id == edge.target_handle or p.name == edge.target_handle),
                    None
                )
            elif target_node.inputs:
                target_port = target_node.inputs[0]
            
            if source_port and target_port:
                # Check type compatibility
                if not self._types_compatible(source_port.data_type, target_port.data_type):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Type mismatch: '{source_port.data_type.value}' connected to '{target_port.data_type.value}'",
                        edge_id=edge.id,
                        suggestion="Consider adding a Transform node to convert types"
                    ))
        
        return issues
    
    def _types_compatible(self, source: DataType, target: DataType) -> bool:
        """Check if two data types are compatible."""
        if source == target:
            return True
        if target == DataType.ANY:
            return True
        if source == DataType.ANY:
            return True
        
        # Additional compatibility rules
        compatible_pairs = [
            (DataType.STRING, DataType.MESSAGE),
            (DataType.MESSAGE, DataType.STRING),
            (DataType.OBJECT, DataType.CONTEXT),
            (DataType.CONTEXT, DataType.OBJECT),
        ]
        
        return (source, target) in compatible_pairs
    
    def _check_node_configs(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check node configurations are valid."""
        issues = []
        
        for node in workflow.nodes:
            # Check agent nodes have model
            if node.node_type == NodeType.AGENT:
                if not node.config.get("model"):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Agent node '{node.label}' has no model specified",
                        node_id=node.id,
                        suggestion="Set a model in the node configuration"
                    ))
            
            # Check HTTP nodes have URL
            if node.node_type == NodeType.HTTP:
                if not node.config.get("url"):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"HTTP node '{node.label}' has no URL specified",
                        node_id=node.id,
                        suggestion="Set the URL in the node configuration"
                    ))
            
            # Check condition nodes have condition
            if node.node_type == NodeType.CONDITION:
                if not node.config.get("condition"):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Condition node '{node.label}' has no condition specified",
                        node_id=node.id,
                        suggestion="Set a condition expression"
                    ))
        
        return issues
    
    def _check_best_practices(self, workflow: Workflow) -> List[ValidationIssue]:
        """Check for workflow best practices."""
        issues = []
        
        # Check for very long chains
        max_chain_length = self._calculate_longest_path(workflow)
        if max_chain_length > 20:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message=f"Workflow has a very long execution path ({max_chain_length} nodes)",
                suggestion="Consider breaking into sub-workflows for maintainability"
            ))
        
        # Check for missing error handling
        has_error_handling = any(
            node.node_type in [NodeType.RETRY, NodeType.CIRCUIT_BREAKER]
            for node in workflow.nodes
        )
        if not has_error_handling and len(workflow.nodes) > 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Workflow has no error handling nodes",
                suggestion="Consider adding Retry or Circuit Breaker nodes for resilience"
            ))
        
        return issues
    
    def _calculate_longest_path(self, workflow: Workflow) -> int:
        """Calculate the longest path in the workflow."""
        if not workflow.nodes:
            return 0
        
        # Find nodes with no incoming edges (start nodes)
        in_degree = {n.id: 0 for n in workflow.nodes}
        for edge in workflow.edges:
            if edge.target in in_degree:
                in_degree[edge.target] += 1
        
        start_nodes = [nid for nid, deg in in_degree.items() if deg == 0]
        
        # BFS to find longest path
        max_length = 0
        for start in start_nodes:
            visited = {start: 1}
            queue = [start]
            
            while queue:
                current = queue.pop(0)
                current_length = visited[current]
                max_length = max(max_length, current_length)
                
                for edge in workflow.get_outgoing_edges(current):
                    if edge.target not in visited or visited[edge.target] < current_length + 1:
                        visited[edge.target] = current_length + 1
                        queue.append(edge.target)
        
        return max_length

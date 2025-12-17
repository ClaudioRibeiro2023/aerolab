"""
Agno Flow Studio v3.0 - Workflow Engine

Executes workflows with real-time updates and debugging support.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Any, Callable, Dict, List
from dataclasses import dataclass, field

from .types import (
    Workflow, Node, Connection, Execution, ExecutionStep,
    ExecutionStatus, NodeType, WorkflowStatus
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    execution: Execution
    workflow: Workflow
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Callbacks
    on_node_start: Optional[Callable[[str], None]] = None
    on_node_complete: Optional[Callable[[str, Any], None]] = None
    on_node_error: Optional[Callable[[str, str], None]] = None
    on_progress: Optional[Callable[[float], None]] = None


class WorkflowEngine:
    """
    Workflow execution engine.
    
    Features:
    - Async execution
    - Real-time status updates
    - Breakpoint support
    - Cost tracking
    - Error handling
    """
    
    def __init__(self):
        self.executors: Dict[NodeType, "NodeExecutor"] = {}
        self.running_executions: Dict[str, ExecutionContext] = {}
        self._breakpoints: set[str] = set()
        self._paused: bool = False
        
    def register_executor(self, node_type: NodeType, executor: "NodeExecutor"):
        """Register a node executor."""
        self.executors[node_type] = executor
        
    async def execute(
        self,
        workflow: Workflow,
        input_data: Dict[str, Any],
        on_node_start: Optional[Callable] = None,
        on_node_complete: Optional[Callable] = None,
        on_node_error: Optional[Callable] = None,
    ) -> Execution:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            input_data: Input data
            on_node_start: Callback when node starts
            on_node_complete: Callback when node completes
            on_node_error: Callback on node error
            
        Returns:
            Execution result
        """
        # Create execution
        execution = Execution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            input_data=input_data,
            steps=[
                ExecutionStep(node_id=n.id, node_name=n.label)
                for n in workflow.nodes
            ]
        )
        
        # Create context
        ctx = ExecutionContext(
            execution=execution,
            workflow=workflow,
            variables=dict(workflow.variables),
            on_node_start=on_node_start,
            on_node_complete=on_node_complete,
            on_node_error=on_node_error,
        )
        
        self.running_executions[execution.id] = ctx
        
        try:
            # Find input nodes
            input_nodes = workflow.get_input_nodes()
            if not input_nodes:
                raise ValueError("Workflow has no input nodes")
            
            # Set input data to input nodes
            for node in input_nodes:
                ctx.node_outputs[node.id] = input_data
            
            # Build execution order (topological sort)
            execution_order = self._topological_sort(workflow)
            
            # Execute nodes in order
            total_nodes = len(execution_order)
            for i, node_id in enumerate(execution_order):
                if self._paused:
                    await self._wait_for_resume()
                
                # Check breakpoint
                if node_id in self._breakpoints:
                    logger.info(f"Breakpoint hit at node {node_id}")
                    self._paused = True
                    await self._wait_for_resume()
                
                node = workflow.get_node(node_id)
                if not node:
                    continue
                    
                await self._execute_node(ctx, node)
                
                # Update progress
                progress = (i + 1) / total_nodes
                if ctx.on_progress:
                    ctx.on_progress(progress)
            
            # Get output from output nodes
            output_nodes = workflow.get_output_nodes()
            output_data = {}
            for node in output_nodes:
                if node.id in ctx.node_outputs:
                    output_data[node.label] = ctx.node_outputs[node.id]
            
            # Complete execution
            execution.status = ExecutionStatus.SUCCESS
            execution.output_data = output_data
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds() * 1000
            
        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            
        finally:
            del self.running_executions[execution.id]
            
        return execution
    
    async def _execute_node(self, ctx: ExecutionContext, node: Node):
        """Execute a single node."""
        step = next((s for s in ctx.execution.steps if s.node_id == node.id), None)
        if not step:
            return
            
        try:
            # Update status
            step.status = ExecutionStatus.RUNNING
            step.started_at = datetime.now()
            ctx.execution.current_step = node.id
            
            if ctx.on_node_start:
                ctx.on_node_start(node.id)
            
            # Get input data from connected nodes
            incoming_edges = ctx.workflow.get_incoming_edges(node.id)
            input_data = {}
            
            for edge in incoming_edges:
                source_output = ctx.node_outputs.get(edge.source)
                if source_output is not None:
                    handle = edge.target_handle or "input"
                    input_data[handle] = source_output
            
            # Execute node based on type
            executor = self.executors.get(node.node_type)
            if executor:
                output = await executor.execute(node, input_data, ctx.variables)
            else:
                # Default passthrough
                output = input_data.get("input", input_data)
            
            # Store output
            ctx.node_outputs[node.id] = output
            
            # Update step
            step.status = ExecutionStatus.SUCCESS
            step.output_data = output
            step.completed_at = datetime.now()
            step.duration = (step.completed_at - step.started_at).total_seconds() * 1000
            
            # Track costs
            if hasattr(executor, 'last_token_usage'):
                step.token_usage = executor.last_token_usage
                ctx.execution.total_tokens += step.token_usage
            if hasattr(executor, 'last_cost'):
                step.cost = executor.last_cost
                ctx.execution.total_cost += step.cost
            
            if ctx.on_node_complete:
                ctx.on_node_complete(node.id, output)
                
        except Exception as e:
            step.status = ExecutionStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            
            if ctx.on_node_error:
                ctx.on_node_error(node.id, str(e))
            
            # Check error handling mode
            if ctx.workflow.settings.error_handling == "stop":
                raise
    
    def _topological_sort(self, workflow: Workflow) -> List[str]:
        """Sort nodes in execution order."""
        in_degree: Dict[str, int] = {n.id: 0 for n in workflow.nodes}
        
        for edge in workflow.edges:
            if edge.target in in_degree:
                in_degree[edge.target] += 1
        
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for edge in workflow.get_outgoing_edges(node_id):
                if edge.target in in_degree:
                    in_degree[edge.target] -= 1
                    if in_degree[edge.target] == 0:
                        queue.append(edge.target)
        
        return result
    
    async def _wait_for_resume(self):
        """Wait until execution is resumed."""
        while self._paused:
            await asyncio.sleep(0.1)
    
    def pause(self, execution_id: str):
        """Pause execution."""
        self._paused = True
        
    def resume(self, execution_id: str):
        """Resume execution."""
        self._paused = False
        
    def stop(self, execution_id: str):
        """Stop execution."""
        if execution_id in self.running_executions:
            ctx = self.running_executions[execution_id]
            ctx.execution.status = ExecutionStatus.CANCELLED
            self._paused = False
    
    def add_breakpoint(self, node_id: str):
        """Add breakpoint."""
        self._breakpoints.add(node_id)
        
    def remove_breakpoint(self, node_id: str):
        """Remove breakpoint."""
        self._breakpoints.discard(node_id)
        
    def clear_breakpoints(self):
        """Clear all breakpoints."""
        self._breakpoints.clear()


# Global engine instance
_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine

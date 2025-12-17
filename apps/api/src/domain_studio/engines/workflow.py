"""
Workflow Engine - Automação de workflows com human-in-the-loop.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from ..core.types import DomainType, WorkflowStepType

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Status de workflow."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"         # Waiting for human input
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Step de workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: WorkflowStepType = WorkflowStepType.AGENT
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    on_error: str = "fail"
    max_retries: int = 3


@dataclass
class WorkflowDefinition:
    """Definição de workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    domain: Optional[DomainType] = None
    steps: List[WorkflowStep] = field(default_factory=list)
    human_checkpoints: List[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class StepResult:
    """Resultado de um step."""
    step_id: str
    status: str = "completed"
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    retries: int = 0


@dataclass
class WorkflowExecution:
    """Execução de workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # Progress
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    
    # Results
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    output: Any = None
    error: Optional[str] = None
    
    # Human checkpoints
    pending_approval: Optional[str] = None
    approvals: Dict[str, Dict] = field(default_factory=dict)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Input
    inputs: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Engine de execução de workflows.
    
    Features:
    - Step-by-step execution
    - Parallel execution
    - Human-in-the-loop checkpoints
    - Error handling and retries
    - Timeout management
    - Event callbacks
    """
    
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._step_handlers: Dict[WorkflowStepType, Callable] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info("WorkflowEngine initialized")
    
    def _register_default_handlers(self) -> None:
        """Register default step handlers."""
        self._step_handlers[WorkflowStepType.AGENT] = self._handle_agent_step
        self._step_handlers[WorkflowStepType.TOOL] = self._handle_tool_step
        self._step_handlers[WorkflowStepType.HUMAN] = self._handle_human_step
        self._step_handlers[WorkflowStepType.CONDITION] = self._handle_condition_step
        self._step_handlers[WorkflowStepType.TRANSFORM] = self._handle_transform_step
    
    # ============================================================
    # WORKFLOW REGISTRATION
    # ============================================================
    
    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """Register a workflow definition."""
        self._workflows[workflow.id] = workflow
        logger.info("Registered workflow: %s", workflow.name)
        return workflow.id
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self, domain: Optional[DomainType] = None) -> List[WorkflowDefinition]:
        """List registered workflows."""
        workflows = list(self._workflows.values())
        if domain:
            workflows = [w for w in workflows if w.domain == domain]
        return workflows
    
    # ============================================================
    # WORKFLOW EXECUTION
    # ============================================================
    
    async def execute(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> WorkflowExecution:
        """Execute a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            inputs=inputs,
            started_at=datetime.now()
        )
        self._executions[execution.id] = execution
        
        logger.info("Starting workflow: %s (execution: %s)", workflow.name, execution.id)
        
        # Emit start event
        await self._emit("workflow_started", execution)
        
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # Build execution order (respecting dependencies)
            ordered_steps = self._topological_sort(workflow.steps)
            
            # Execute steps
            for step in ordered_steps:
                # Check if paused for human input
                if execution.status == WorkflowStatus.PAUSED:
                    break
                
                # Check dependencies
                if not self._dependencies_met(step, execution):
                    continue
                
                # Execute step
                execution.current_step = step.id
                await self._emit("step_started", execution, step)
                
                result = await self._execute_step(step, execution, context)
                execution.step_results[step.id] = result
                
                if result.status == "completed":
                    execution.completed_steps.append(step.id)
                    await self._emit("step_completed", execution, step, result)
                elif result.status == "failed" and step.on_error == "fail":
                    execution.status = WorkflowStatus.FAILED
                    execution.error = result.error
                    await self._emit("step_failed", execution, step, result)
                    break
                elif result.status == "paused":
                    execution.status = WorkflowStatus.PAUSED
                    execution.pending_approval = step.id
                    await self._emit("step_paused", execution, step)
                    break
            
            # Check completion
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.output = self._collect_outputs(execution)
                execution.completed_at = datetime.now()
                await self._emit("workflow_completed", execution)
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            logger.error("Workflow failed: %s", str(e))
            await self._emit("workflow_failed", execution)
        
        logger.info("Workflow %s: %s", execution.id, execution.status.value)
        return execution
    
    async def resume(
        self,
        execution_id: str,
        approval: Dict[str, Any]
    ) -> WorkflowExecution:
        """Resume a paused workflow after human approval."""
        execution = self._executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        if execution.status != WorkflowStatus.PAUSED:
            raise ValueError(f"Execution is not paused: {execution.status}")
        
        step_id = execution.pending_approval
        if not step_id:
            raise ValueError("No pending approval")
        
        # Record approval
        execution.approvals[step_id] = {
            "approved_at": datetime.now().isoformat(),
            "approval": approval
        }
        
        # Mark step as completed
        execution.step_results[step_id] = StepResult(
            step_id=step_id,
            status="completed",
            output=approval
        )
        execution.completed_steps.append(step_id)
        execution.pending_approval = None
        
        logger.info("Workflow resumed: %s", execution_id)
        
        # Continue execution
        workflow = self.get_workflow(execution.workflow_id)
        if workflow:
            execution.status = WorkflowStatus.RUNNING
            
            # Find remaining steps
            ordered_steps = self._topological_sort(workflow.steps)
            remaining = [s for s in ordered_steps if s.id not in execution.completed_steps]
            
            for step in remaining:
                if not self._dependencies_met(step, execution):
                    continue
                
                execution.current_step = step.id
                result = await self._execute_step(step, execution, None)
                execution.step_results[step.id] = result
                
                if result.status == "completed":
                    execution.completed_steps.append(step.id)
                elif result.status == "paused":
                    execution.status = WorkflowStatus.PAUSED
                    execution.pending_approval = step.id
                    break
                elif result.status == "failed" and step.on_error == "fail":
                    execution.status = WorkflowStatus.FAILED
                    execution.error = result.error
                    break
            
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.output = self._collect_outputs(execution)
                execution.completed_at = datetime.now()
        
        return execution
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        return self._executions.get(execution_id)
    
    # ============================================================
    # STEP EXECUTION
    # ============================================================
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Execute a single step."""
        start_time = datetime.now()
        
        handler = self._step_handlers.get(step.type)
        if not handler:
            return StepResult(
                step_id=step.id,
                status="failed",
                error=f"No handler for step type: {step.type}"
            )
        
        # Retry logic
        last_error = None
        for attempt in range(step.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    handler(step, execution, context),
                    timeout=step.timeout_seconds
                )
                result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                result.retries = attempt
                return result
            except asyncio.TimeoutError:
                last_error = "Step timed out"
            except Exception as e:
                last_error = str(e)
                logger.warning("Step %s attempt %d failed: %s", step.name, attempt + 1, last_error)
        
        return StepResult(
            step_id=step.id,
            status="failed",
            error=last_error,
            retries=step.max_retries
        )
    
    async def _handle_agent_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Handle agent step."""
        agent_name = step.config.get("agent")
        prompt = step.config.get("prompt", "")
        
        # Simulated agent execution
        output = f"Agent {agent_name} executed with prompt: {prompt[:50]}..."
        
        return StepResult(
            step_id=step.id,
            status="completed",
            output=output
        )
    
    async def _handle_tool_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Handle tool step."""
        tool_name = step.config.get("tool")
        args = step.config.get("args", {})
        
        # Simulated tool execution
        output = f"Tool {tool_name} executed with args: {args}"
        
        return StepResult(
            step_id=step.id,
            status="completed",
            output=output
        )
    
    async def _handle_human_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Handle human checkpoint step."""
        return StepResult(
            step_id=step.id,
            status="paused",
            output={"message": step.config.get("message", "Awaiting human approval")}
        )
    
    async def _handle_condition_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Handle condition step."""
        condition = step.config.get("condition", "true")
        
        # Evaluate condition (simplified)
        result = condition.lower() == "true"
        
        return StepResult(
            step_id=step.id,
            status="completed",
            output={"condition_met": result}
        )
    
    async def _handle_transform_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Optional[Dict]
    ) -> StepResult:
        """Handle transform step."""
        input_key = step.config.get("input")
        transform = step.config.get("transform", "identity")
        
        # Get input from previous step
        input_data = None
        if input_key and input_key in execution.step_results:
            input_data = execution.step_results[input_key].output
        
        # Apply transform
        output = {"transformed": input_data, "transform": transform}
        
        return StepResult(
            step_id=step.id,
            status="completed",
            output=output
        )
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _topological_sort(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Sort steps respecting dependencies."""
        # Build dependency graph
        in_degree = {s.id: len(s.depends_on) for s in steps}
        step_map = {s.id: s for s in steps}
        
        # Find steps with no dependencies
        queue = [s for s in steps if not s.depends_on]
        sorted_steps = []
        
        while queue:
            step = queue.pop(0)
            sorted_steps.append(step)
            
            # Reduce in-degree of dependent steps
            for other in steps:
                if step.id in other.depends_on:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other)
        
        return sorted_steps
    
    def _dependencies_met(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Check if step dependencies are met."""
        return all(dep in execution.completed_steps for dep in step.depends_on)
    
    def _collect_outputs(self, execution: WorkflowExecution) -> Dict:
        """Collect outputs from all steps."""
        return {
            step_id: result.output
            for step_id, result in execution.step_results.items()
            if result.status == "completed"
        }
    
    # ============================================================
    # EVENTS
    # ============================================================
    
    def on(self, event: str, callback: Callable) -> None:
        """Register event callback."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    async def _emit(self, event: str, *args) -> None:
        """Emit event to callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error("Event callback error: %s", str(e))


# ============================================================
# FACTORY
# ============================================================

_engine: Optional[WorkflowEngine] = None

def get_workflow_engine() -> WorkflowEngine:
    """Get singleton workflow engine."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine

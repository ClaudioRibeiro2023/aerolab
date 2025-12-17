"""
Módulo de Workflows - Orquestração avançada de fluxos de trabalho.

Arquitetura:
- Core: Engine, State, Execution, Registry
- Steps: Agent, Condition, Parallel, Loop, MultiAgent
- Triggers: Webhook, Schedule, Event
- Observability: Tracing, Metrics, Audit

Uso básico:
    from src.workflows import WorkflowEngine, WorkflowDefinition, WorkflowStep
    
    # Criar engine
    engine = WorkflowEngine()
    
    # Registrar handlers
    engine.register_step_handler("agent", AgentStepHandler())
    
    # Criar workflow
    workflow = WorkflowDefinition(
        id="my-workflow",
        name="My Workflow",
        steps=[
            WorkflowStep(id="step1", type="agent", name="Step 1", config={...})
        ]
    )
    
    # Registrar e executar
    registry.register(workflow)
    result = await engine.run("my-workflow", inputs={...})
"""

__all__ = []

# Core
try:
    from .core.engine import WorkflowEngine, create_engine, get_engine
    from .core.execution import ExecutionContext, ExecutionResult, ExecutionStatus, StepResult
    from .core.state import StateManager, WorkflowState, WorkflowStatus, Checkpoint
    from .core.registry import WorkflowRegistry, WorkflowDefinition, WorkflowStep, get_registry
    from .core.variables import VariableResolver, Expression, resolve, evaluate
    
    __all__.extend([
        "WorkflowEngine", "create_engine", "get_engine",
        "ExecutionContext", "ExecutionResult", "ExecutionStatus", "StepResult",
        "StateManager", "WorkflowState", "WorkflowStatus", "Checkpoint",
        "WorkflowRegistry", "WorkflowDefinition", "WorkflowStep", "get_registry",
        "VariableResolver", "Expression", "resolve", "evaluate"
    ])
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")

# Steps
try:
    from .steps.base import BaseStep, StepHandler
    from .steps.agent_step import AgentStep, AgentStepHandler
    from .steps.condition_step import ConditionStep, ConditionStepHandler, Branch
    from .steps.parallel_step import ParallelStep, ParallelStepHandler, JoinStrategy
    from .steps.loop_step import LoopStep, LoopStepHandler, LoopType
    from .steps.multi_agent_step import MultiAgentStep, MultiAgentStepHandler, OrchestrationPattern, AgentConfig
    
    __all__.extend([
        "BaseStep", "StepHandler",
        "AgentStep", "AgentStepHandler",
        "ConditionStep", "ConditionStepHandler", "Branch",
        "ParallelStep", "ParallelStepHandler", "JoinStrategy",
        "LoopStep", "LoopStepHandler", "LoopType",
        "MultiAgentStep", "MultiAgentStepHandler", "OrchestrationPattern", "AgentConfig"
    ])
except ImportError as e:
    print(f"Warning: Could not import step modules: {e}")

# Triggers
try:
    from .triggers.base import BaseTrigger, TriggerConfig, TriggerResult, TriggerType
    from .triggers.webhook import WebhookTrigger, WebhookConfig
    from .triggers.schedule import ScheduleTrigger, ScheduleConfig, CronExpression, SCHEDULE_PRESETS
    from .triggers.event import EventTrigger, EventBus, WorkflowEvent, EventFilter, get_event_bus, SystemEvents
    
    __all__.extend([
        "BaseTrigger", "TriggerConfig", "TriggerResult", "TriggerType",
        "WebhookTrigger", "WebhookConfig",
        "ScheduleTrigger", "ScheduleConfig", "CronExpression", "SCHEDULE_PRESETS",
        "EventTrigger", "EventBus", "WorkflowEvent", "EventFilter", "get_event_bus", "SystemEvents"
    ])
except ImportError as e:
    print(f"Warning: Could not import trigger modules: {e}")

# Observability
try:
    from .observability.tracing import WorkflowTracer, create_tracer, trace_workflow, trace_step, get_tracer
    from .observability.metrics import WorkflowMetrics, MetricsCollector, get_metrics
    from .observability.audit import AuditLog, AuditEntry, AuditAction, get_audit_log
    
    __all__.extend([
        "WorkflowTracer", "create_tracer", "trace_workflow", "trace_step", "get_tracer",
        "WorkflowMetrics", "MetricsCollector", "get_metrics",
        "AuditLog", "AuditEntry", "AuditAction", "get_audit_log"
    ])
except ImportError as e:
    print(f"Warning: Could not import observability modules: {e}")

# Versioning
try:
    from .versioning.versions import WorkflowVersion, VersionManager, VersionStatus, get_version_manager
    from .versioning.diff import DiffEngine, VersionDiff, DiffType
    
    __all__.extend([
        "WorkflowVersion", "VersionManager", "VersionStatus", "get_version_manager",
        "DiffEngine", "VersionDiff", "DiffType"
    ])
except ImportError as e:
    print(f"Warning: Could not import versioning modules: {e}")

# AI Features
try:
    from .ai.assistant import WorkflowAssistant, get_assistant, StepSuggestion, WorkflowSuggestion
    from .ai.optimizer import WorkflowOptimizer, OptimizationRecommendation, OptimizationType
    
    __all__.extend([
        "WorkflowAssistant", "get_assistant", "StepSuggestion", "WorkflowSuggestion",
        "WorkflowOptimizer", "OptimizationRecommendation", "OptimizationType"
    ])
except ImportError as e:
    print(f"Warning: Could not import AI modules: {e}")

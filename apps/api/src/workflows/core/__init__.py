"""
Core do módulo de Workflows.

Componentes:
- WorkflowEngine: Orquestrador principal
- ExecutionContext: Contexto de execução
- StateManager: Gerenciamento de estado durável
- WorkflowRegistry: Registro de workflows
"""

from .engine import WorkflowEngine, create_engine
from .execution import ExecutionContext, ExecutionResult, ExecutionStatus
from .state import StateManager, WorkflowState, Checkpoint
from .registry import WorkflowRegistry, get_registry
from .variables import VariableResolver, Expression

__all__ = [
    "WorkflowEngine",
    "create_engine",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionStatus",
    "StateManager",
    "WorkflowState",
    "Checkpoint",
    "WorkflowRegistry",
    "get_registry",
    "VariableResolver",
    "Expression",
]

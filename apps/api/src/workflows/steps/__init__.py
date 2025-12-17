"""
Step Types para Workflows.

Tipos disponíveis:
- AgentStep: Executa agente
- MultiAgentStep: Orquestra múltiplos agentes
- ConditionStep: Branching condicional
- ParallelStep: Execução paralela
- LoopStep: Iteração
- ActionStep: Ações genéricas (HTTP, DB)
- WaitStep: Aguarda evento/tempo
- SagaStep: Transações com compensação
"""

from .base import BaseStep, StepHandler
from .agent_step import AgentStep, AgentStepHandler
from .condition_step import ConditionStep, ConditionStepHandler
from .parallel_step import ParallelStep, ParallelStepHandler
from .loop_step import LoopStep, LoopStepHandler
from .multi_agent_step import MultiAgentStep, MultiAgentStepHandler, OrchestrationPattern

__all__ = [
    # Base
    "BaseStep",
    "StepHandler",
    # Steps
    "AgentStep",
    "AgentStepHandler",
    "ConditionStep",
    "ConditionStepHandler",
    "ParallelStep",
    "ParallelStepHandler",
    "LoopStep",
    "LoopStepHandler",
    "MultiAgentStep",
    "MultiAgentStepHandler",
    "OrchestrationPattern",
]

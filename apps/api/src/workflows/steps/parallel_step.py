"""
Parallel Step - Execução paralela de múltiplos steps.

Suporta:
- Fan-out: Distribuir para múltiplos steps
- Fan-in: Coletar resultados
- Estratégias de join: all, any, first
- Limite de concorrência
"""

import asyncio
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
import logging

from .base import BaseStep, StepHandler
from ..core.execution import ExecutionContext, ParallelExecutor, StepResult, ExecutionStatus
from ..core.registry import WorkflowStep

logger = logging.getLogger(__name__)


class JoinStrategy:
    """Estratégias para aguardar resultados paralelos."""
    ALL = "all"       # Aguarda todos completarem
    ANY = "any"       # Retorna quando qualquer um tiver sucesso
    FIRST = "first"   # Retorna o primeiro a completar


@dataclass
class ParallelBranch:
    """Define um branch paralelo."""
    id: str
    step_type: str  # agent, action, etc.
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "step_type": self.step_type,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ParallelBranch":
        return cls(
            id=data["id"],
            step_type=data.get("step_type", data.get("type", "agent")),
            config=data.get("config", {})
        )


@dataclass
class ParallelStep(BaseStep):
    """
    Step que executa múltiplos branches em paralelo.
    
    Exemplo:
        step = ParallelStep(
            id="multi_analyze",
            name="Multi Analysis",
            branches=[
                ParallelBranch("sentiment", "agent", {"agent_id": "sentiment_analyzer"}),
                ParallelBranch("entities", "agent", {"agent_id": "entity_extractor"}),
                ParallelBranch("summary", "agent", {"agent_id": "summarizer"}),
            ],
            join_strategy=JoinStrategy.ALL,
            output_variable="analysis_results"
        )
    """
    branches: List[ParallelBranch] = field(default_factory=list)
    join_strategy: str = JoinStrategy.ALL
    max_concurrent: int = 10
    output_variable: Optional[str] = None
    fail_on_error: bool = True  # Falhar se qualquer branch falhar
    
    @property
    def step_type(self) -> str:
        return "parallel"
    
    async def execute(self, context: ExecutionContext) -> Any:
        """Executa branches em paralelo."""
        if not self.branches:
            return {"branches": [], "results": {}}
        
        executor = ParallelExecutor(self.max_concurrent)
        
        # Criar funções de execução para cada branch
        async def execute_branch(branch: ParallelBranch) -> Dict:
            """Executa um branch individual."""
            # Resolver config com variáveis
            resolved_config = {}
            for key, value in branch.config.items():
                if isinstance(value, str):
                    resolved_config[key] = context.resolve(value)
                else:
                    resolved_config[key] = value
            
            # Simular execução (em produção, chamaria o step handler real)
            logger.info(f"Parallel branch {branch.id} executing...")
            
            # Placeholder
            return {
                "branch_id": branch.id,
                "step_type": branch.step_type,
                "result": f"Result from {branch.id}",
                "config": resolved_config
            }
        
        # Criar tasks
        tasks = []
        for branch in self.branches:
            async def wrapper(b=branch):
                return await execute_branch(b)
            tasks.append((branch.id, wrapper))
        
        # Executar em paralelo
        results = await executor.execute_parallel(
            tasks,
            context,
            join_strategy=self.join_strategy
        )
        
        # Processar resultados
        output = {
            "branches": [b.id for b in self.branches],
            "results": {},
            "failed": [],
            "succeeded": []
        }
        
        for result in results:
            if result.is_success:
                output["succeeded"].append(result.step_id)
                output["results"][result.step_id] = result.output
            else:
                output["failed"].append({
                    "branch_id": result.step_id,
                    "error": result.error
                })
        
        # Verificar falhas
        if output["failed"] and self.fail_on_error:
            logger.warning(f"Parallel step {self.id} had {len(output['failed'])} failures")
        
        # Salvar resultado
        if self.output_variable:
            context.set_variable(self.output_variable, output["results"])
        
        logger.info(f"Parallel step {self.id} completed: {len(output['succeeded'])} succeeded, {len(output['failed'])} failed")
        
        return output
    
    def get_config(self) -> Dict[str, Any]:
        config = super().get_config()
        config.update({
            "branches": [b.to_dict() for b in self.branches],
            "join_strategy": self.join_strategy,
            "max_concurrent": self.max_concurrent,
            "output_variable": self.output_variable,
            "fail_on_error": self.fail_on_error
        })
        return config
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.branches:
            errors.append("Must have at least one branch")
        if self.join_strategy not in (JoinStrategy.ALL, JoinStrategy.ANY, JoinStrategy.FIRST):
            errors.append(f"Invalid join_strategy: {self.join_strategy}")
        return errors


class ParallelStepHandler(StepHandler):
    """Handler para ParallelStep."""
    
    def __init__(self, step_handlers: Optional[Dict[str, StepHandler]] = None):
        self._step_handlers = step_handlers or {}
    
    @property
    def step_type(self) -> str:
        return "parallel"
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Executa step paralelo."""
        config = step.config
        
        # Parse branches
        branches = []
        for b in config.get("branches", []):
            if isinstance(b, dict):
                branches.append(ParallelBranch.from_dict(b))
        
        parallel_step = ParallelStep(
            id=step.id,
            name=step.name,
            branches=branches,
            join_strategy=config.get("join_strategy", JoinStrategy.ALL),
            max_concurrent=config.get("max_concurrent", 10),
            output_variable=config.get("output_variable"),
            fail_on_error=config.get("fail_on_error", True)
        )
        
        return await parallel_step.execute(context)

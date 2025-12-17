"""
Execution Layer para Workflows.

Gerencia a execução de steps com:
- Retry automático com backoff
- Timeout handling
- Error recovery
- Métricas de execução
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, Awaitable, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import traceback

from .state import WorkflowState, WorkflowStatus, StepStatus
from .variables import VariableResolver, get_resolver


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status de execução."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class RetryPolicy:
    """Política de retry."""
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    retry_on: List[type] = field(default_factory=lambda: [Exception])
    
    def get_delay(self, attempt: int) -> float:
        """Calcula delay para tentativa."""
        delay = self.initial_delay_ms * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_ms) / 1000


@dataclass
class ExecutionConfig:
    """Configuração de execução."""
    timeout_seconds: Optional[float] = 300  # 5 min default
    retry_policy: Optional[RetryPolicy] = None
    checkpoint_after: bool = True  # Checkpoint após cada step
    fail_fast: bool = False  # Para imediatamente em erro
    parallel_limit: int = 10  # Máximo de steps paralelos


@dataclass
class StepResult:
    """Resultado de execução de um step."""
    step_id: str
    status: ExecutionStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS
    
    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


@dataclass
class ExecutionResult:
    """Resultado de execução do workflow."""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    step_results: List[StepResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "outputs": self.outputs,
            "step_results": [r.to_dict() for r in self.step_results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "error": self.error
        }


class ExecutionContext:
    """
    Contexto de execução de um workflow.
    
    Mantém:
    - Estado atual
    - Variáveis
    - Histórico de steps
    - Configurações
    """
    
    def __init__(
        self,
        state: WorkflowState,
        config: Optional[ExecutionConfig] = None
    ):
        self.state = state
        self.config = config or ExecutionConfig()
        self._resolver = get_resolver()
        self._cancelled = False
        self._paused = False
    
    @property
    def execution_id(self) -> str:
        return self.state.execution_id
    
    @property
    def workflow_id(self) -> str:
        return self.state.workflow_id
    
    @property
    def variables(self) -> Dict[str, Any]:
        return self.state.variables
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
    
    @property
    def is_paused(self) -> bool:
        return self._paused
    
    def set_variable(self, name: str, value: Any) -> None:
        """Define variável."""
        self.state.set_variable(name, value)
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Obtém variável."""
        return self.state.get_variable(name, default)
    
    def resolve(self, template: str) -> str:
        """Resolve template com variáveis do contexto."""
        return self._resolver.resolve(template, self.variables)
    
    def evaluate_condition(self, condition: str) -> bool:
        """Avalia condição."""
        return self._resolver.evaluate_condition(condition, self.variables)
    
    def cancel(self) -> None:
        """Cancela execução."""
        self._cancelled = True
        self.state.status = WorkflowStatus.CANCELLED
    
    def pause(self) -> None:
        """Pausa execução."""
        self._paused = True
        self.state.status = WorkflowStatus.PAUSED
    
    def resume(self) -> None:
        """Resume execução."""
        self._paused = False
        self.state.status = WorkflowStatus.RUNNING
    
    def get_step_output(self, step_id: str) -> Optional[Any]:
        """Obtém output de um step anterior."""
        step_state = self.state.step_states.get(step_id)
        if step_state:
            return step_state.output_data
        return None
    
    def with_result(self, step_id: str, result: StepResult) -> "ExecutionContext":
        """Retorna contexto atualizado com resultado do step."""
        self.state.mark_step_completed(step_id, result.output)
        
        # Adicionar output às variáveis
        if result.output is not None:
            self.set_variable(step_id, result.output)
            self.set_variable("_last", result.output)
            self.set_variable("_last_step", step_id)
        
        return self


class StepExecutor:
    """
    Executor de steps individuais.
    
    Gerencia:
    - Timeout
    - Retry com backoff
    - Logging
    - Métricas
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
    
    async def execute(
        self,
        step_id: str,
        step_fn: Callable[[ExecutionContext], Awaitable[Any]],
        context: ExecutionContext,
        retry_policy: Optional[RetryPolicy] = None
    ) -> StepResult:
        """
        Executa um step.
        
        Args:
            step_id: ID do step
            step_fn: Função async que executa o step
            context: Contexto de execução
            retry_policy: Política de retry (opcional)
        """
        policy = retry_policy or self.config.retry_policy or RetryPolicy(max_retries=0)
        
        result = StepResult(
            step_id=step_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Marcar step como iniciado
        context.state.mark_step_started(step_id)
        
        attempt = 0
        last_error = None
        
        while attempt <= policy.max_retries:
            if context.is_cancelled:
                result.status = ExecutionStatus.CANCELLED
                result.error = "Execution cancelled"
                break
            
            try:
                # Executar com timeout
                if self.config.timeout_seconds:
                    output = await asyncio.wait_for(
                        step_fn(context),
                        timeout=self.config.timeout_seconds
                    )
                else:
                    output = await step_fn(context)
                
                # Sucesso
                result.status = ExecutionStatus.SUCCESS
                result.output = output
                result.completed_at = datetime.now()
                result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
                result.retry_count = attempt
                
                context.state.mark_step_completed(step_id, {"result": output})
                
                logger.info(f"Step {step_id} completed successfully in {result.duration_ms:.0f}ms")
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout_seconds}s"
                result.status = ExecutionStatus.TIMEOUT
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Step {step_id} attempt {attempt + 1} failed: {e}")
                
                # Verificar se deve fazer retry
                should_retry = any(isinstance(e, t) for t in policy.retry_on)
                
                if should_retry and attempt < policy.max_retries:
                    result.status = ExecutionStatus.RETRYING
                    delay = policy.get_delay(attempt)
                    logger.info(f"Retrying step {step_id} in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    result.status = ExecutionStatus.FAILED
                    break
            
            attempt += 1
        
        # Falhou após todas as tentativas
        result.status = ExecutionStatus.FAILED
        result.error = last_error
        result.completed_at = datetime.now()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
        result.retry_count = attempt
        
        context.state.mark_step_failed(step_id, last_error or "Unknown error")
        
        logger.error(f"Step {step_id} failed after {attempt} attempts: {last_error}")
        return result


class ParallelExecutor:
    """
    Executor de steps em paralelo.
    
    Suporta:
    - Fan-out/Fan-in
    - Limite de concorrência
    - Estratégias de join (all, any, first)
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._step_executor = StepExecutor()
    
    async def execute_parallel(
        self,
        steps: List[tuple],  # List of (step_id, step_fn)
        context: ExecutionContext,
        join_strategy: str = "all"  # all, any, first
    ) -> List[StepResult]:
        """
        Executa múltiplos steps em paralelo.
        
        Args:
            steps: Lista de (step_id, step_fn)
            context: Contexto de execução
            join_strategy: Como aguardar resultados
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_semaphore(step_id: str, step_fn):
            async with semaphore:
                return await self._step_executor.execute(step_id, step_fn, context)
        
        tasks = [
            asyncio.create_task(run_with_semaphore(step_id, step_fn))
            for step_id, step_fn in steps
        ]
        
        if join_strategy == "first":
            # Retorna quando o primeiro completar
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            # Cancelar pendentes
            for task in pending:
                task.cancel()
            return [task.result() for task in done]
        
        elif join_strategy == "any":
            # Retorna quando qualquer um tiver sucesso
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            # Continuar até ter um sucesso
            while done:
                for task in done:
                    result = task.result()
                    if result.is_success:
                        for p in pending:
                            p.cancel()
                        return [result]
                if not pending:
                    break
                done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED
                )
            # Nenhum sucesso
            return [task.result() for task in tasks]
        
        else:  # all
            # Aguarda todos
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [
                r if isinstance(r, StepResult) 
                else StepResult(
                    step_id="unknown",
                    status=ExecutionStatus.FAILED,
                    error=str(r)
                )
                for r in results
            ]


# Factory
def create_executor(config: Optional[ExecutionConfig] = None) -> StepExecutor:
    """Cria step executor."""
    return StepExecutor(config)


def create_parallel_executor(max_concurrent: int = 10) -> ParallelExecutor:
    """Cria parallel executor."""
    return ParallelExecutor(max_concurrent)

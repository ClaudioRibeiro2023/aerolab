"""
Workflow Engine - Orquestrador principal de workflows.

Arquitetura:
- Durable Execution com checkpointing
- Step execution com retry e timeout
- Suporte a execução paralela
- Recovery automático de falhas

Padrões implementados:
- Temporal-style durable execution
- Saga pattern com compensação
- Event-driven execution
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Awaitable, Type
from dataclasses import dataclass, field
import logging

from .state import StateManager, WorkflowState, WorkflowStatus, Checkpoint
from .execution import (
    ExecutionContext, ExecutionResult, ExecutionStatus,
    StepExecutor, StepResult, ExecutionConfig, ParallelExecutor
)
from .registry import WorkflowRegistry, WorkflowDefinition, WorkflowStep, get_registry
from .variables import get_resolver

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Engine principal de execução de workflows.
    
    Features:
    - Durable execution com checkpoints
    - Retry automático com backoff exponencial
    - Parallel step execution
    - Recovery de falhas
    - Observability hooks
    
    Exemplo:
        engine = WorkflowEngine()
        
        # Registrar step handlers
        engine.register_step_handler("agent", AgentStepHandler())
        engine.register_step_handler("condition", ConditionStepHandler())
        
        # Executar workflow
        result = await engine.run("my-workflow", inputs={"data": "..."})
        
        if result.is_success:
            print("Output:", result.outputs)
        else:
            print("Error:", result.error)
    """
    
    def __init__(
        self,
        registry: Optional[WorkflowRegistry] = None,
        state_manager: Optional[StateManager] = None,
        config: Optional[ExecutionConfig] = None
    ):
        self.registry = registry or get_registry()
        self.state_manager = state_manager or StateManager()
        self.config = config or ExecutionConfig()
        
        self._step_handlers: Dict[str, "StepHandler"] = {}
        self._step_executor = StepExecutor(self.config)
        self._parallel_executor = ParallelExecutor(self.config.parallel_limit)
        
        # Hooks para observabilidade
        self._on_start: List[Callable] = []
        self._on_step_start: List[Callable] = []
        self._on_step_complete: List[Callable] = []
        self._on_complete: List[Callable] = []
        self._on_error: List[Callable] = []
        
        # Registrar handlers padrão
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Registra handlers padrão."""
        # Handlers serão implementados no módulo steps/
        pass
    
    def register_step_handler(
        self,
        step_type: str,
        handler: "StepHandler"
    ) -> None:
        """
        Registra handler para um tipo de step.
        
        Args:
            step_type: Tipo do step (agent, condition, etc)
            handler: Handler que processa o step
        """
        self._step_handlers[step_type] = handler
        logger.debug(f"Registered step handler: {step_type}")
    
    def on_start(self, callback: Callable) -> None:
        """Adiciona hook para início de workflow."""
        self._on_start.append(callback)
    
    def on_step_start(self, callback: Callable) -> None:
        """Adiciona hook para início de step."""
        self._on_step_start.append(callback)
    
    def on_step_complete(self, callback: Callable) -> None:
        """Adiciona hook para conclusão de step."""
        self._on_step_complete.append(callback)
    
    def on_complete(self, callback: Callable) -> None:
        """Adiciona hook para conclusão de workflow."""
        self._on_complete.append(callback)
    
    def on_error(self, callback: Callable) -> None:
        """Adiciona hook para erros."""
        self._on_error.append(callback)
    
    async def run(
        self,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
        resume_from: Optional[str] = None  # Checkpoint ID para resumir
    ) -> ExecutionResult:
        """
        Executa um workflow.
        
        Args:
            workflow_id: ID do workflow a executar
            inputs: Inputs iniciais
            execution_id: ID da execução (gerado se não fornecido)
            resume_from: ID do checkpoint para resumir
            
        Returns:
            ExecutionResult com outputs e status
        """
        start_time = time.time()
        execution_id = execution_id or f"exec_{uuid.uuid4().hex[:12]}"
        
        # Obter definição do workflow
        workflow = self.registry.get(workflow_id)
        if not workflow:
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=ExecutionStatus.FAILED,
                error=f"Workflow not found: {workflow_id}"
            )
        
        # Verificar se está habilitado
        if not workflow.enabled:
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=ExecutionStatus.FAILED,
                error=f"Workflow is disabled: {workflow_id}"
            )
        
        # Criar ou recuperar estado
        if resume_from:
            state = self.state_manager.recover(execution_id)
            if not state:
                return ExecutionResult(
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    status=ExecutionStatus.FAILED,
                    error=f"Cannot resume: checkpoint not found"
                )
        else:
            state = self.state_manager.create_state(
                execution_id=execution_id,
                workflow_id=workflow_id,
                initial_variables=inputs or {},
                metadata={"workflow_version": workflow.version}
            )
        
        # Criar contexto de execução
        context = ExecutionContext(state, self.config)
        
        # Notificar início
        state.status = WorkflowStatus.RUNNING
        await self._emit_start(workflow, context)
        
        result = ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # Executar workflow
            await self._execute_workflow(workflow, context, result)
            
            # Marcar como completo
            if not context.is_cancelled and result.status != ExecutionStatus.FAILED:
                result.status = ExecutionStatus.SUCCESS
                result.outputs = context.variables.copy()
                self.state_manager.mark_completed(execution_id, result.outputs)
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            self.state_manager.mark_failed(execution_id, str(e))
            await self._emit_error(workflow, context, e)
            logger.exception(f"Workflow {workflow_id} failed: {e}")
        
        finally:
            result.completed_at = datetime.now()
            result.duration_ms = (time.time() - start_time) * 1000
            await self._emit_complete(workflow, context, result)
        
        return result
    
    async def _execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        result: ExecutionResult
    ) -> None:
        """Executa o workflow step by step."""
        current_step = workflow.get_start_step()
        
        while current_step and not context.is_cancelled:
            # Verificar pause
            if context.is_paused:
                self.state_manager.checkpoint(context.state)
                return
            
            # Checkpoint antes do step
            if self.config.checkpoint_after:
                self.state_manager.checkpoint(context.state)
            
            # Notificar início do step
            await self._emit_step_start(workflow, current_step, context)
            
            # Executar step
            step_result = await self._execute_step(current_step, context)
            result.step_results.append(step_result)
            
            # Atualizar contexto
            context = context.with_result(current_step.id, step_result)
            
            # Notificar conclusão do step
            await self._emit_step_complete(workflow, current_step, context, step_result)
            
            # Verificar erro
            if not step_result.is_success:
                if self.config.fail_fast:
                    result.status = ExecutionStatus.FAILED
                    result.error = step_result.error
                    return
                
                # Tentar on_error step se definido
                if current_step.on_error:
                    error_step = workflow.get_step(current_step.on_error)
                    if error_step:
                        current_step = error_step
                        continue
                else:
                    result.status = ExecutionStatus.FAILED
                    result.error = step_result.error
                    return
            
            # Determinar próximo step
            current_step = self._get_next_step(workflow, current_step, context)
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> StepResult:
        """Executa um step individual."""
        handler = self._step_handlers.get(step.type)
        
        if not handler:
            # Handler genérico para tipos não registrados
            return StepResult(
                step_id=step.id,
                status=ExecutionStatus.FAILED,
                error=f"No handler for step type: {step.type}"
            )
        
        # Criar função de execução
        async def step_fn(ctx: ExecutionContext) -> Any:
            return await handler.execute(step, ctx)
        
        # Executar com retry
        return await self._step_executor.execute(
            step_id=step.id,
            step_fn=step_fn,
            context=context
        )
    
    def _get_next_step(
        self,
        workflow: WorkflowDefinition,
        current_step: WorkflowStep,
        context: ExecutionContext
    ) -> Optional[WorkflowStep]:
        """Determina o próximo step baseado no resultado."""
        # Se step define next_step, usar
        if current_step.next_step:
            return workflow.get_step(current_step.next_step)
        
        # Senão, seguir ordem sequencial
        return workflow.get_next_step(current_step.id)
    
    async def pause(self, execution_id: str) -> bool:
        """Pausa uma execução em andamento."""
        state = self.state_manager.get_state(execution_id)
        if state and state.is_running:
            state.status = WorkflowStatus.PAUSED
            self.state_manager.checkpoint(state)
            return True
        return False
    
    async def resume(self, execution_id: str) -> Optional[ExecutionResult]:
        """Resume uma execução pausada."""
        state = self.state_manager.get_state(execution_id)
        if state and state.status == WorkflowStatus.PAUSED:
            return await self.run(
                workflow_id=state.workflow_id,
                execution_id=execution_id,
                resume_from=execution_id
            )
        return None
    
    async def cancel(self, execution_id: str) -> bool:
        """Cancela uma execução em andamento."""
        state = self.state_manager.get_state(execution_id)
        if state and not state.is_complete:
            state.status = WorkflowStatus.CANCELLED
            self.state_manager.update_state(state)
            return True
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Obtém status de uma execução."""
        state = self.state_manager.get_state(execution_id)
        if state:
            return state.to_dict()
        return None
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[Dict]:
        """Lista execuções."""
        states = self.state_manager.list_executions(workflow_id, status)
        return [s.to_dict() for s in states]
    
    # Event emitters
    async def _emit_start(self, workflow: WorkflowDefinition, context: ExecutionContext) -> None:
        for callback in self._on_start:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow, context)
                else:
                    callback(workflow, context)
            except Exception as e:
                logger.warning(f"on_start hook error: {e}")
    
    async def _emit_step_start(
        self,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> None:
        for callback in self._on_step_start:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow, step, context)
                else:
                    callback(workflow, step, context)
            except Exception as e:
                logger.warning(f"on_step_start hook error: {e}")
    
    async def _emit_step_complete(
        self,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        context: ExecutionContext,
        result: StepResult
    ) -> None:
        for callback in self._on_step_complete:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow, step, context, result)
                else:
                    callback(workflow, step, context, result)
            except Exception as e:
                logger.warning(f"on_step_complete hook error: {e}")
    
    async def _emit_complete(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        result: ExecutionResult
    ) -> None:
        for callback in self._on_complete:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow, context, result)
                else:
                    callback(workflow, context, result)
            except Exception as e:
                logger.warning(f"on_complete hook error: {e}")
    
    async def _emit_error(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        error: Exception
    ) -> None:
        for callback in self._on_error:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(workflow, context, error)
                else:
                    callback(workflow, context, error)
            except Exception as e:
                logger.warning(f"on_error hook error: {e}")


class StepHandler:
    """
    Interface para handlers de steps.
    
    Cada tipo de step (agent, condition, parallel, etc.)
    deve implementar um handler.
    """
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """
        Executa o step.
        
        Args:
            step: Definição do step
            context: Contexto de execução
            
        Returns:
            Output do step
        """
        raise NotImplementedError


# Factory functions
def create_engine(
    registry: Optional[WorkflowRegistry] = None,
    state_manager: Optional[StateManager] = None,
    config: Optional[ExecutionConfig] = None
) -> WorkflowEngine:
    """Cria nova instância do engine."""
    return WorkflowEngine(registry, state_manager, config)


# Singleton global
_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Obtém engine global."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine

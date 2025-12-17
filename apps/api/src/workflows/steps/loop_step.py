"""
Loop Step - Iteração sobre coleções ou condições.

Suporta:
- For each: Iterar sobre lista
- While: Repetir enquanto condição for verdadeira
- Until: Repetir até condição ser verdadeira
- Map: Aplicar step a cada item e coletar resultados
"""

import asyncio
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
import logging

from .base import BaseStep, StepHandler
from ..core.execution import ExecutionContext
from ..core.registry import WorkflowStep

logger = logging.getLogger(__name__)


class LoopType:
    """Tipos de loop."""
    FOR_EACH = "for_each"   # Iterar sobre lista
    WHILE = "while"         # Enquanto condição for true
    UNTIL = "until"         # Até condição ser true
    MAP = "map"             # Map com coleta de resultados
    TIMES = "times"         # Repetir N vezes


@dataclass
class LoopStep(BaseStep):
    """
    Step de iteração.
    
    Exemplo for_each:
        step = LoopStep(
            id="process_items",
            name="Process Each Item",
            loop_type=LoopType.FOR_EACH,
            items_variable="data.items",
            item_variable="current_item",
            step_config={
                "type": "agent",
                "agent_id": "processor",
                "prompt": "Process: ${current_item}"
            }
        )
    
    Exemplo while:
        step = LoopStep(
            id="retry_until_success",
            name="Retry Until Success",
            loop_type=LoopType.WHILE,
            condition="${retry_count} < 5 and ${success} == false",
            step_config={...}
        )
    
    Exemplo map:
        step = LoopStep(
            id="map_transform",
            name="Transform Items",
            loop_type=LoopType.MAP,
            items_variable="input_items",
            step_config={...},
            output_variable="transformed_items"
        )
    """
    loop_type: str = LoopType.FOR_EACH
    
    # For each / Map
    items_variable: Optional[str] = None  # Expressão para obter lista
    item_variable: str = "item"  # Nome da variável para item atual
    index_variable: str = "index"  # Nome da variável para índice
    
    # While / Until
    condition: Optional[str] = None
    
    # Times
    times: int = 1
    
    # Step a executar
    step_config: Dict[str, Any] = field(default_factory=dict)
    
    # Controle
    max_iterations: int = 1000  # Limite de segurança
    parallel: bool = False  # Executar iterações em paralelo
    continue_on_error: bool = False
    
    # Output
    output_variable: Optional[str] = None
    collect_results: bool = True
    
    @property
    def step_type(self) -> str:
        return "loop"
    
    async def execute(self, context: ExecutionContext) -> Any:
        """Executa o loop."""
        results = []
        iteration = 0
        
        if self.loop_type == LoopType.FOR_EACH or self.loop_type == LoopType.MAP:
            results = await self._execute_for_each(context)
        
        elif self.loop_type == LoopType.WHILE:
            results = await self._execute_while(context, until=False)
        
        elif self.loop_type == LoopType.UNTIL:
            results = await self._execute_while(context, until=True)
        
        elif self.loop_type == LoopType.TIMES:
            results = await self._execute_times(context)
        
        output = {
            "loop_type": self.loop_type,
            "iterations": len(results),
            "results": results if self.collect_results else None
        }
        
        if self.output_variable:
            if self.loop_type == LoopType.MAP:
                # Map retorna apenas os resultados
                context.set_variable(self.output_variable, results)
            else:
                context.set_variable(self.output_variable, output)
        
        logger.info(f"Loop {self.id} completed: {len(results)} iterations")
        return output
    
    async def _execute_for_each(self, context: ExecutionContext) -> List[Any]:
        """Executa for each loop."""
        # Obter itens
        items = self._resolve_items(context)
        if not items:
            return []
        
        results = []
        
        for i, item in enumerate(items):
            if i >= self.max_iterations:
                logger.warning(f"Loop {self.id} hit max_iterations limit")
                break
            
            if context.is_cancelled:
                break
            
            # Definir variáveis de iteração
            context.set_variable(self.item_variable, item)
            context.set_variable(self.index_variable, i)
            
            try:
                # Executar step (placeholder)
                result = await self._execute_iteration_step(context, i)
                results.append(result)
            except Exception as e:
                if not self.continue_on_error:
                    raise
                logger.warning(f"Loop {self.id} iteration {i} failed: {e}")
                results.append({"error": str(e)})
        
        return results
    
    async def _execute_while(self, context: ExecutionContext, until: bool = False) -> List[Any]:
        """Executa while/until loop."""
        results = []
        iteration = 0
        
        while iteration < self.max_iterations:
            if context.is_cancelled:
                break
            
            # Avaliar condição
            condition_result = context.evaluate_condition(self.condition) if self.condition else False
            
            # until: parar quando condição for true
            # while: parar quando condição for false
            should_stop = condition_result if until else not condition_result
            
            if should_stop:
                break
            
            # Definir variáveis de iteração
            context.set_variable(self.index_variable, iteration)
            
            try:
                result = await self._execute_iteration_step(context, iteration)
                results.append(result)
            except Exception as e:
                if not self.continue_on_error:
                    raise
                logger.warning(f"Loop {self.id} iteration {iteration} failed: {e}")
                results.append({"error": str(e)})
            
            iteration += 1
        
        return results
    
    async def _execute_times(self, context: ExecutionContext) -> List[Any]:
        """Executa loop N vezes."""
        results = []
        
        for i in range(min(self.times, self.max_iterations)):
            if context.is_cancelled:
                break
            
            context.set_variable(self.index_variable, i)
            
            try:
                result = await self._execute_iteration_step(context, i)
                results.append(result)
            except Exception as e:
                if not self.continue_on_error:
                    raise
                logger.warning(f"Loop {self.id} iteration {i} failed: {e}")
                results.append({"error": str(e)})
        
        return results
    
    async def _execute_iteration_step(self, context: ExecutionContext, iteration: int) -> Any:
        """Executa step de uma iteração."""
        # Placeholder - em produção, chamaria o step handler real
        logger.debug(f"Loop {self.id} executing iteration {iteration}")
        
        # Simular execução
        return {
            "iteration": iteration,
            "item": context.get_variable(self.item_variable),
            "result": f"Iteration {iteration} result"
        }
    
    def _resolve_items(self, context: ExecutionContext) -> List[Any]:
        """Resolve lista de itens."""
        if not self.items_variable:
            return []
        
        # Resolver expressão
        from ..core.variables import ExpressionEvaluator
        items = ExpressionEvaluator.evaluate(f"${{{self.items_variable}}}", context.variables)
        
        if isinstance(items, list):
            return items
        elif isinstance(items, dict):
            return list(items.items())
        elif isinstance(items, str):
            return list(items)
        
        return []
    
    def get_config(self) -> Dict[str, Any]:
        config = super().get_config()
        config.update({
            "loop_type": self.loop_type,
            "items_variable": self.items_variable,
            "item_variable": self.item_variable,
            "index_variable": self.index_variable,
            "condition": self.condition,
            "times": self.times,
            "step_config": self.step_config,
            "max_iterations": self.max_iterations,
            "parallel": self.parallel,
            "continue_on_error": self.continue_on_error,
            "output_variable": self.output_variable,
            "collect_results": self.collect_results
        })
        return config


class LoopStepHandler(StepHandler):
    """Handler para LoopStep."""
    
    @property
    def step_type(self) -> str:
        return "loop"
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Executa step de loop."""
        config = step.config
        
        loop_step = LoopStep(
            id=step.id,
            name=step.name,
            loop_type=config.get("loop_type", LoopType.FOR_EACH),
            items_variable=config.get("items_variable", config.get("items")),
            item_variable=config.get("item_variable", "item"),
            index_variable=config.get("index_variable", "index"),
            condition=config.get("condition"),
            times=config.get("times", 1),
            step_config=config.get("step_config", config.get("step", {})),
            max_iterations=config.get("max_iterations", 1000),
            parallel=config.get("parallel", False),
            continue_on_error=config.get("continue_on_error", False),
            output_variable=config.get("output_variable"),
            collect_results=config.get("collect_results", True)
        )
        
        return await loop_step.execute(context)

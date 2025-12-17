"""
Base classes para Steps de Workflow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

from ..core.execution import ExecutionContext, StepResult, ExecutionStatus
from ..core.registry import WorkflowStep


@dataclass
class BaseStep(ABC):
    """
    Classe base para todos os tipos de step.
    
    Cada step deve:
    - Ter um ID único
    - Implementar execute()
    - Retornar output serializável
    """
    id: str
    name: str
    description: str = ""
    timeout_seconds: Optional[int] = None
    retry_config: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    @abstractmethod
    def step_type(self) -> str:
        """Tipo do step (agent, condition, etc)."""
        pass
    
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> Any:
        """
        Executa o step.
        
        Args:
            context: Contexto de execução com variáveis
            
        Returns:
            Output do step (será salvo no contexto)
        """
        pass
    
    def validate(self) -> List[str]:
        """Valida configuração do step."""
        errors = []
        if not self.id:
            errors.append("Step ID is required")
        if not self.name:
            errors.append("Step name is required")
        return errors
    
    def to_workflow_step(self) -> WorkflowStep:
        """Converte para WorkflowStep."""
        return WorkflowStep(
            id=self.id,
            type=self.step_type,
            name=self.name,
            config=self.get_config(),
            timeout_seconds=self.timeout_seconds,
            retry_policy=self.retry_config
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração do step como dict."""
        return {
            "description": self.description,
            "metadata": self.metadata
        }


class StepHandler(ABC):
    """
    Handler base para processar steps.
    
    Cada tipo de step tem um handler associado
    que sabe como executá-lo.
    """
    
    @property
    @abstractmethod
    def step_type(self) -> str:
        """Tipo de step que este handler processa."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """
        Executa o step.
        
        Args:
            step: Definição do step do workflow
            context: Contexto de execução
            
        Returns:
            Output do step
        """
        pass
    
    def validate_config(self, config: Dict) -> List[str]:
        """Valida configuração do step."""
        return []
    
    def create_from_config(self, step: WorkflowStep) -> BaseStep:
        """Cria instância de step a partir de config."""
        raise NotImplementedError

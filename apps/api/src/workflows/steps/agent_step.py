"""
Agent Step - Executa um agente.

Suporta:
- Resolução de prompt com variáveis
- Configuração de modelo
- Uso de tools
- Integração com RAG
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging

from .base import BaseStep, StepHandler
from ..core.execution import ExecutionContext
from ..core.registry import WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class AgentStep(BaseStep):
    """
    Step que executa um agente.
    
    Exemplo:
        step = AgentStep(
            id="analyze",
            name="Analyzer Agent",
            agent_id="analyzer",
            prompt="Analyze: ${input_data}",
            output_variable="analysis"
        )
    """
    agent_id: str = ""
    prompt: str = ""
    output_variable: Optional[str] = None
    model_override: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: List[str] = field(default_factory=list)
    use_rag: bool = False
    rag_collection: Optional[str] = None
    rag_top_k: int = 3
    system_prompt: Optional[str] = None
    
    @property
    def step_type(self) -> str:
        return "agent"
    
    async def execute(self, context: ExecutionContext) -> Any:
        """Executa o agente."""
        # Resolver prompt com variáveis
        resolved_prompt = context.resolve(self.prompt)
        
        # Obter agente do registry
        # Em produção, isso viria de um AgentRegistry
        agent_config = {
            "agent_id": self.agent_id,
            "prompt": resolved_prompt,
            "model": self.model_override,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools,
            "use_rag": self.use_rag,
            "rag_collection": self.rag_collection,
            "rag_top_k": self.rag_top_k,
            "system_prompt": context.resolve(self.system_prompt) if self.system_prompt else None
        }
        
        # Simular execução do agente
        # Em produção, chamaria o agente real
        logger.info(f"Executing agent {self.agent_id} with prompt: {resolved_prompt[:100]}...")
        
        # Placeholder para resultado
        result = {
            "agent_id": self.agent_id,
            "prompt": resolved_prompt,
            "response": f"[Agent {self.agent_id} response to: {resolved_prompt[:50]}...]",
            "tokens_used": 0,
            "model": self.model_override or "default"
        }
        
        # Salvar em variável se especificado
        if self.output_variable:
            context.set_variable(self.output_variable, result.get("response", result))
        
        return result
    
    def get_config(self) -> Dict[str, Any]:
        config = super().get_config()
        config.update({
            "agent_id": self.agent_id,
            "prompt": self.prompt,
            "output_variable": self.output_variable,
            "model_override": self.model_override,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools,
            "use_rag": self.use_rag,
            "rag_collection": self.rag_collection,
            "system_prompt": self.system_prompt
        })
        return config
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.agent_id:
            errors.append("agent_id is required")
        if not self.prompt:
            errors.append("prompt is required")
        return errors


class AgentStepHandler(StepHandler):
    """Handler para AgentStep."""
    
    def __init__(self, agent_registry: Optional[Any] = None):
        self._agent_registry = agent_registry
    
    @property
    def step_type(self) -> str:
        return "agent"
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Executa step de agente."""
        config = step.config
        
        # Criar step a partir de config
        agent_step = AgentStep(
            id=step.id,
            name=step.name,
            agent_id=config.get("agent_id", step.name),
            prompt=config.get("prompt", config.get("input_template", "")),
            output_variable=config.get("output_variable", config.get("output_var")),
            model_override=config.get("model_override"),
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens"),
            tools=config.get("tools", []),
            use_rag=config.get("use_rag", False),
            rag_collection=config.get("rag_collection"),
            system_prompt=config.get("system_prompt")
        )
        
        return await agent_step.execute(context)
    
    def validate_config(self, config: Dict) -> List[str]:
        errors = []
        if not config.get("agent_id") and not config.get("name"):
            errors.append("agent_id or name is required")
        return errors

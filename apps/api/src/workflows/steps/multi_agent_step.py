"""
Multi-Agent Step - Orquestração de múltiplos agentes.

Padrões suportados (inspirados em LangGraph/CrewAI):
- Sequential (Crew): Agentes em sequência
- Hierarchical: Manager coordena workers
- Collaborative: Agentes colaboram em loop
- Debate: Agentes debatem até consenso
- Router: Roteia para agente ideal
"""

import asyncio
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from .base import BaseStep, StepHandler
from ..core.execution import ExecutionContext
from ..core.registry import WorkflowStep

logger = logging.getLogger(__name__)


class OrchestrationPattern(Enum):
    """Padrões de orquestração multi-agente."""
    SEQUENTIAL = "sequential"       # Crew pattern: agentes em sequência
    HIERARCHICAL = "hierarchical"   # Manager + workers
    COLLABORATIVE = "collaborative" # Agentes colaboram em loop
    DEBATE = "debate"              # Agentes debatem até consenso
    ROUTER = "router"              # Roteia para melhor agente
    VOTING = "voting"              # Todos respondem, voto decide
    CHAIN = "chain"                # Output de um é input do próximo


@dataclass
class AgentConfig:
    """Configuração de um agente no multi-agent step."""
    id: str
    agent_id: str
    role: str = ""
    goal: str = ""
    prompt_template: str = ""
    backstory: str = ""
    tools: List[str] = field(default_factory=list)
    allow_delegation: bool = False  # Pode delegar para outros agentes
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "role": self.role,
            "goal": self.goal,
            "prompt_template": self.prompt_template,
            "backstory": self.backstory,
            "tools": self.tools,
            "allow_delegation": self.allow_delegation
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentConfig":
        return cls(
            id=data.get("id", data.get("agent_id")),
            agent_id=data.get("agent_id", data.get("id")),
            role=data.get("role", ""),
            goal=data.get("goal", ""),
            prompt_template=data.get("prompt_template", data.get("prompt", "")),
            backstory=data.get("backstory", ""),
            tools=data.get("tools", []),
            allow_delegation=data.get("allow_delegation", False)
        )


@dataclass
class MultiAgentStep(BaseStep):
    """
    Step que orquestra múltiplos agentes.
    
    Exemplo Sequential (Crew):
        step = MultiAgentStep(
            id="content_crew",
            name="Content Creation Crew",
            pattern=OrchestrationPattern.SEQUENTIAL,
            agents=[
                AgentConfig("researcher", "Researcher", role="Pesquisador"),
                AgentConfig("writer", "Writer", role="Escritor"),
                AgentConfig("reviewer", "Reviewer", role="Revisor"),
            ],
            task="${input_task}"
        )
    
    Exemplo Hierarchical:
        step = MultiAgentStep(
            id="dev_team",
            name="Development Team",
            pattern=OrchestrationPattern.HIERARCHICAL,
            manager_agent=AgentConfig("manager", "ProjectManager"),
            agents=[
                AgentConfig("frontend", "FrontendDev"),
                AgentConfig("backend", "BackendDev"),
                AgentConfig("qa", "QAEngineer"),
            ]
        )
    
    Exemplo Debate:
        step = MultiAgentStep(
            id="debate",
            name="Expert Debate",
            pattern=OrchestrationPattern.DEBATE,
            agents=[
                AgentConfig("optimist", "OptimistAnalyst"),
                AgentConfig("pessimist", "PessimistAnalyst"),
            ],
            max_rounds=5,
            consensus_threshold=0.8
        )
    """
    pattern: OrchestrationPattern = OrchestrationPattern.SEQUENTIAL
    agents: List[AgentConfig] = field(default_factory=list)
    manager_agent: Optional[AgentConfig] = None
    task: str = ""  # Task/goal para os agentes
    
    # Controle
    max_rounds: int = 10
    consensus_threshold: float = 0.8
    timeout_per_agent: int = 60
    
    # Router pattern
    router_prompt: Optional[str] = None  # Prompt para decidir qual agente usar
    
    # Output
    output_variable: Optional[str] = None
    include_intermediate: bool = False  # Incluir respostas intermediárias
    
    @property
    def step_type(self) -> str:
        return "multi_agent"
    
    async def execute(self, context: ExecutionContext) -> Any:
        """Executa orquestração multi-agente."""
        resolved_task = context.resolve(self.task)
        
        result = {
            "pattern": self.pattern.value,
            "agents": [a.id for a in self.agents],
            "task": resolved_task,
            "rounds": [],
            "final_output": None
        }
        
        if self.pattern == OrchestrationPattern.SEQUENTIAL:
            result = await self._execute_sequential(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.HIERARCHICAL:
            result = await self._execute_hierarchical(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.COLLABORATIVE:
            result = await self._execute_collaborative(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.DEBATE:
            result = await self._execute_debate(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.ROUTER:
            result = await self._execute_router(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.VOTING:
            result = await self._execute_voting(context, resolved_task, result)
        
        elif self.pattern == OrchestrationPattern.CHAIN:
            result = await self._execute_chain(context, resolved_task, result)
        
        if self.output_variable:
            context.set_variable(self.output_variable, result.get("final_output", result))
        
        logger.info(f"MultiAgent {self.id} ({self.pattern.value}) completed with {len(result.get('rounds', []))} rounds")
        
        return result
    
    async def _execute_sequential(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Executa agentes em sequência (Crew pattern)."""
        current_input = task
        
        for agent in self.agents:
            agent_result = await self._run_agent(agent, current_input, context)
            result["rounds"].append({
                "agent": agent.id,
                "input": current_input[:100],
                "output": agent_result
            })
            current_input = agent_result  # Output vira input do próximo
        
        result["final_output"] = current_input
        return result
    
    async def _execute_hierarchical(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Executa com manager coordenando workers."""
        if not self.manager_agent:
            return await self._execute_sequential(context, task, result)
        
        # Manager planeja
        plan_prompt = f"Plan how to accomplish: {task}\nAvailable workers: {[a.role for a in self.agents]}"
        plan = await self._run_agent(self.manager_agent, plan_prompt, context)
        result["rounds"].append({"agent": "manager", "action": "plan", "output": plan})
        
        # Workers executam (simplificado)
        worker_results = []
        for agent in self.agents:
            worker_result = await self._run_agent(agent, f"Execute your part of: {task}\nPlan: {plan}", context)
            worker_results.append({"agent": agent.id, "result": worker_result})
            result["rounds"].append({"agent": agent.id, "action": "execute", "output": worker_result})
        
        # Manager sintetiza
        synthesis_prompt = f"Synthesize results:\n{worker_results}"
        final = await self._run_agent(self.manager_agent, synthesis_prompt, context)
        result["rounds"].append({"agent": "manager", "action": "synthesize", "output": final})
        
        result["final_output"] = final
        return result
    
    async def _execute_collaborative(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Agentes colaboram em múltiplas rodadas."""
        shared_context = {"task": task, "contributions": []}
        
        for round_num in range(self.max_rounds):
            round_results = []
            
            for agent in self.agents:
                prompt = f"Task: {task}\nPrevious contributions: {shared_context['contributions'][-3:]}\nAdd your contribution:"
                agent_result = await self._run_agent(agent, prompt, context)
                round_results.append({"agent": agent.id, "contribution": agent_result})
                shared_context["contributions"].append({"agent": agent.id, "text": agent_result})
            
            result["rounds"].append({"round": round_num, "contributions": round_results})
            
            # Check if done (simplificado)
            if round_num >= 2:  # Mínimo 3 rodadas
                break
        
        result["final_output"] = shared_context["contributions"][-1]["text"] if shared_context["contributions"] else ""
        return result
    
    async def _execute_debate(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Agentes debatem até consenso."""
        positions = {}
        
        # Posições iniciais
        for agent in self.agents:
            position = await self._run_agent(agent, f"State your position on: {task}", context)
            positions[agent.id] = position
            result["rounds"].append({"round": 0, "agent": agent.id, "position": position})
        
        # Rodadas de debate
        for round_num in range(1, self.max_rounds):
            new_positions = {}
            
            for agent in self.agents:
                other_positions = {k: v for k, v in positions.items() if k != agent.id}
                prompt = f"Task: {task}\nYour position: {positions[agent.id]}\nOther positions: {other_positions}\nRevise your position:"
                new_position = await self._run_agent(agent, prompt, context)
                new_positions[agent.id] = new_position
                result["rounds"].append({"round": round_num, "agent": agent.id, "position": new_position})
            
            positions = new_positions
            
            # Check consensus (simplificado)
            if round_num >= 3:
                break
        
        # Final synthesis
        result["final_output"] = f"Consensus: {list(positions.values())[0]}"
        result["positions"] = positions
        return result
    
    async def _execute_router(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Roteia para o melhor agente baseado no task."""
        # Decidir qual agente
        agent_descriptions = "\n".join([f"- {a.id}: {a.role} - {a.goal}" for a in self.agents])
        router_prompt = self.router_prompt or f"Select best agent for: {task}\nAgents:\n{agent_descriptions}\nRespond with just the agent id."
        
        selected_id = await self._run_agent(
            AgentConfig("router", "Router"),
            router_prompt,
            context
        )
        
        # Encontrar agente selecionado
        selected_agent = next((a for a in self.agents if a.id in selected_id.lower()), self.agents[0])
        
        result["selected_agent"] = selected_agent.id
        result["rounds"].append({"agent": "router", "selected": selected_agent.id})
        
        # Executar agente selecionado
        agent_result = await self._run_agent(selected_agent, task, context)
        result["rounds"].append({"agent": selected_agent.id, "output": agent_result})
        
        result["final_output"] = agent_result
        return result
    
    async def _execute_voting(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Todos agentes respondem, voto decide."""
        responses = {}
        
        # Todos respondem
        for agent in self.agents:
            response = await self._run_agent(agent, task, context)
            responses[agent.id] = response
            result["rounds"].append({"agent": agent.id, "response": response})
        
        result["responses"] = responses
        
        # Votação (simplificado - em produção usaria embeddings para similaridade)
        result["final_output"] = list(responses.values())[0]  # Primeiro por enquanto
        return result
    
    async def _execute_chain(self, context: ExecutionContext, task: str, result: Dict) -> Dict:
        """Chain: output de cada agente é input do próximo."""
        current = task
        
        for agent in self.agents:
            prompt = agent.prompt_template.replace("${input}", current) if agent.prompt_template else current
            resolved_prompt = context.resolve(prompt)
            
            output = await self._run_agent(agent, resolved_prompt, context)
            result["rounds"].append({
                "agent": agent.id,
                "input": current[:100],
                "output": output
            })
            current = output
        
        result["final_output"] = current
        return result
    
    async def _run_agent(self, agent: AgentConfig, prompt: str, context: ExecutionContext) -> str:
        """Executa um agente individual."""
        # Placeholder - em produção, chamaria o agente real
        logger.debug(f"Running agent {agent.id} with role '{agent.role}'")
        
        # Simular execução
        return f"[{agent.id}] Response to: {prompt[:50]}..."
    
    def get_config(self) -> Dict[str, Any]:
        config = super().get_config()
        config.update({
            "pattern": self.pattern.value,
            "agents": [a.to_dict() for a in self.agents],
            "manager_agent": self.manager_agent.to_dict() if self.manager_agent else None,
            "task": self.task,
            "max_rounds": self.max_rounds,
            "consensus_threshold": self.consensus_threshold,
            "router_prompt": self.router_prompt,
            "output_variable": self.output_variable
        })
        return config
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.agents:
            errors.append("Must have at least one agent")
        if self.pattern == OrchestrationPattern.HIERARCHICAL and not self.manager_agent:
            errors.append("Hierarchical pattern requires manager_agent")
        return errors


class MultiAgentStepHandler(StepHandler):
    """Handler para MultiAgentStep."""
    
    @property
    def step_type(self) -> str:
        return "multi_agent"
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Executa step multi-agente."""
        config = step.config
        
        # Parse agents
        agents = []
        for a in config.get("agents", []):
            if isinstance(a, dict):
                agents.append(AgentConfig.from_dict(a))
        
        # Parse manager
        manager = None
        if config.get("manager_agent"):
            manager = AgentConfig.from_dict(config["manager_agent"])
        
        # Parse pattern
        pattern_str = config.get("pattern", "sequential")
        try:
            pattern = OrchestrationPattern(pattern_str)
        except ValueError:
            pattern = OrchestrationPattern.SEQUENTIAL
        
        multi_agent_step = MultiAgentStep(
            id=step.id,
            name=step.name,
            pattern=pattern,
            agents=agents,
            manager_agent=manager,
            task=config.get("task", config.get("input_template", "")),
            max_rounds=config.get("max_rounds", 10),
            consensus_threshold=config.get("consensus_threshold", 0.8),
            router_prompt=config.get("router_prompt"),
            output_variable=config.get("output_variable")
        )
        
        return await multi_agent_step.execute(context)

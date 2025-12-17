"""
Agno SDK - Team (Multi-Agent)

Sistema de orquestração multi-agente.
Permite criar equipes de agentes que colaboram.

Workflows suportados:
- sequential: Agentes executam em sequência
- parallel: Agentes executam em paralelo
- hierarchical: Um agente supervisor delega para outros
- debate: Agentes debatem até consenso

Uso:
```python
from agno import Team, Agent

researcher = Agent(name="researcher", model="gpt-4o")
writer = Agent(name="writer", model="gpt-4o")
reviewer = Agent(name="reviewer", model="gpt-4o")

# Equipe sequencial
team = Team(
    agents=[researcher, writer, reviewer],
    workflow="sequential"
)
result = team.run("Write a report about AI")

# Equipe com supervisor
team = Team(
    agents=[researcher, writer],
    supervisor=reviewer,
    workflow="hierarchical"
)
```
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union, Callable
import logging

from .agent import Agent, AgentConfig
from .types import (
    Response, Context, AgentState, Usage,
    TeamRun, AgentRun, ResponseStatus
)


logger = logging.getLogger(__name__)


@dataclass
class TeamConfig:
    """
    Configuração da equipe.
    
    Attributes:
        name: Nome da equipe
        workflow: Tipo de workflow
        max_iterations: Máximo de iterações
        consensus_threshold: Threshold para consenso (debate)
    """
    name: str = "team"
    workflow: str = "sequential"  # sequential, parallel, hierarchical, debate
    max_iterations: int = 10
    consensus_threshold: float = 0.8
    
    # Timeouts
    agent_timeout: float = 120.0
    team_timeout: float = 600.0


class Team:
    """
    Equipe multi-agente.
    
    Orquestra múltiplos agentes para completar tarefas complexas.
    
    Workflows:
    - **sequential**: Cada agente executa em sequência,
      passando seu output como input para o próximo.
    - **parallel**: Todos os agentes executam em paralelo,
      resultados são combinados.
    - **hierarchical**: Um supervisor delega tarefas
      para agentes especializados.
    - **debate**: Agentes debatem uma questão até
      atingir consenso.
    
    Uso:
    ```python
    team = Team(
        agents=[agent1, agent2, agent3],
        workflow="sequential"
    )
    
    result = team.run("Complex task")
    
    # Com contexto compartilhado
    result = team.run("Task", context=Context(user_id="123"))
    ```
    """
    
    def __init__(
        self,
        agents: list[Agent],
        workflow: str = "sequential",
        supervisor: Optional[Agent] = None,
        config: Optional[TeamConfig] = None,
        **kwargs
    ):
        if config:
            self.config = config
        else:
            self.config = TeamConfig(workflow=workflow, **kwargs)
        
        self.agents = agents
        self.supervisor = supervisor
        
        # Estado
        self._runs: list[TeamRun] = []
        self._current_run: Optional[TeamRun] = None
    
    @property
    def name(self) -> str:
        """Nome da equipe."""
        return self.config.name
    
    async def arun(
        self,
        task: str,
        context: Optional[Context] = None
    ) -> Response:
        """
        Executa a equipe de forma assíncrona.
        
        Args:
            task: Tarefa a executar
            context: Contexto compartilhado
            
        Returns:
            Response com resultado final
        """
        start_time = datetime.now()
        context = context or Context()
        
        # Criar run
        self._current_run = TeamRun(
            team_name=self.name,
            input=task,
            workflow=self.config.workflow
        )
        self._current_run.status = AgentState.THINKING
        
        try:
            # Executar workflow apropriado
            if self.config.workflow == "sequential":
                result = await self._run_sequential(task, context)
            elif self.config.workflow == "parallel":
                result = await self._run_parallel(task, context)
            elif self.config.workflow == "hierarchical":
                result = await self._run_hierarchical(task, context)
            elif self.config.workflow == "debate":
                result = await self._run_debate(task, context)
            else:
                raise ValueError(f"Unknown workflow: {self.config.workflow}")
            
            # Completar run
            self._current_run.output = result.content
            self._current_run.status = AgentState.COMPLETED
            self._current_run.completed_at = datetime.now()
            self._current_run.total_duration_ms = (
                datetime.now() - start_time
            ).total_seconds() * 1000
            
            self._runs.append(self._current_run)
            
            return result
            
        except Exception as e:
            logger.exception(f"Team execution error: {e}")
            self._current_run.status = AgentState.ERROR
            self._current_run.error = str(e)
            
            return Response(
                content="",
                status=ResponseStatus.ERROR,
                error=str(e)
            )
    
    def run(
        self,
        task: str,
        context: Optional[Context] = None
    ) -> Response:
        """
        Executa a equipe de forma síncrona.
        
        Args:
            task: Tarefa a executar
            context: Contexto compartilhado
            
        Returns:
            Response com resultado final
        """
        return asyncio.run(self.arun(task, context))
    
    async def _run_sequential(
        self,
        task: str,
        context: Context
    ) -> Response:
        """
        Executa agentes em sequência.
        
        Cada agente recebe o output do anterior.
        """
        current_input = task
        total_usage = Usage()
        all_messages = []
        
        for i, agent in enumerate(self.agents):
            logger.info(f"Sequential: Running agent {i+1}/{len(self.agents)}: {agent.name}")
            
            # Preparar input com contexto do anterior
            if i > 0:
                current_input = f"""Previous agent output:
{current_input}

Continue the task: {task}"""
            
            # Executar agente
            response = await agent.arun(current_input, context)
            
            # Registrar run
            agent_run = AgentRun(
                agent_name=agent.name,
                input=current_input,
                output=response.content,
                usage=response.usage,
                duration_ms=response.duration_ms
            )
            self._current_run.agent_runs.append(agent_run)
            
            # Acumular métricas
            total_usage = total_usage + response.usage
            all_messages.extend(response.messages)
            
            # Output vira input do próximo
            current_input = response.content
        
        self._current_run.total_usage = total_usage
        
        return Response(
            content=current_input,
            messages=all_messages,
            usage=total_usage,
            status=ResponseStatus.SUCCESS
        )
    
    async def _run_parallel(
        self,
        task: str,
        context: Context
    ) -> Response:
        """
        Executa agentes em paralelo.
        
        Todos executam simultaneamente, resultados são combinados.
        """
        logger.info(f"Parallel: Running {len(self.agents)} agents")
        
        # Criar tasks
        tasks = [
            agent.arun(task, context)
            for agent in self.agents
        ]
        
        # Executar em paralelo
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        results = []
        total_usage = Usage()
        
        for agent, response in zip(self.agents, responses):
            if isinstance(response, Exception):
                results.append(f"[{agent.name}] Error: {response}")
                continue
            
            results.append(f"[{agent.name}]\n{response.content}")
            total_usage = total_usage + response.usage
            
            agent_run = AgentRun(
                agent_name=agent.name,
                input=task,
                output=response.content,
                usage=response.usage,
                duration_ms=response.duration_ms
            )
            self._current_run.agent_runs.append(agent_run)
        
        # Combinar resultados
        combined = "\n\n---\n\n".join(results)
        
        self._current_run.total_usage = total_usage
        
        return Response(
            content=combined,
            usage=total_usage,
            status=ResponseStatus.SUCCESS
        )
    
    async def _run_hierarchical(
        self,
        task: str,
        context: Context
    ) -> Response:
        """
        Executa com supervisor hierárquico.
        
        Supervisor delega subtarefas para agentes especializados.
        """
        if not self.supervisor:
            raise ValueError("Hierarchical workflow requires a supervisor")
        
        # Preparar lista de agentes disponíveis
        agents_desc = "\n".join([
            f"- {agent.name}: {agent.config.instructions[:100]}..."
            for agent in self.agents
        ])
        
        supervisor_prompt = f"""You are a team supervisor. You have these agents available:

{agents_desc}

Your task is to coordinate them to complete: {task}

For each step, respond with:
1. Which agent to use (by name)
2. What specific task to give them

Format your response as:
AGENT: <agent_name>
TASK: <specific task>

Or when done:
DONE: <final summary>"""

        iterations = 0
        total_usage = Usage()
        results = []
        
        while iterations < self.config.max_iterations:
            iterations += 1
            
            # Perguntar ao supervisor
            context_msg = f"\n\nPrevious results:\n{chr(10).join(results)}" if results else ""
            supervisor_input = supervisor_prompt + context_msg
            
            supervisor_response = await self.supervisor.arun(supervisor_input, context)
            total_usage = total_usage + supervisor_response.usage
            
            content = supervisor_response.content
            
            # Verificar se terminou
            if "DONE:" in content:
                final_summary = content.split("DONE:")[1].strip()
                break
            
            # Parse delegação
            if "AGENT:" in content and "TASK:" in content:
                agent_name = content.split("AGENT:")[1].split("\n")[0].strip()
                agent_task = content.split("TASK:")[1].strip()
                
                # Encontrar agente
                agent = next(
                    (a for a in self.agents if a.name.lower() == agent_name.lower()),
                    None
                )
                
                if agent:
                    response = await agent.arun(agent_task, context)
                    results.append(f"[{agent.name}]: {response.content}")
                    total_usage = total_usage + response.usage
                    
                    agent_run = AgentRun(
                        agent_name=agent.name,
                        input=agent_task,
                        output=response.content,
                        usage=response.usage
                    )
                    self._current_run.agent_runs.append(agent_run)
                else:
                    results.append(f"Agent '{agent_name}' not found")
        else:
            final_summary = "\n\n".join(results)
        
        self._current_run.total_usage = total_usage
        
        return Response(
            content=final_summary,
            usage=total_usage,
            status=ResponseStatus.SUCCESS
        )
    
    async def _run_debate(
        self,
        task: str,
        context: Context
    ) -> Response:
        """
        Executa debate entre agentes.
        
        Agentes debatem até atingir consenso ou máximo de iterações.
        """
        if len(self.agents) < 2:
            raise ValueError("Debate requires at least 2 agents")
        
        debate_history = []
        total_usage = Usage()
        
        for iteration in range(self.config.max_iterations):
            round_responses = []
            
            for agent in self.agents:
                # Preparar prompt de debate
                history_text = "\n\n".join([
                    f"[{h['agent']}]: {h['response']}"
                    for h in debate_history[-6:]  # Últimas 6 respostas
                ])
                
                if debate_history:
                    prompt = f"""Topic: {task}

Previous discussion:
{history_text}

Please provide your perspective, considering the previous arguments. 
If you agree with the emerging consensus, say "I AGREE: <summary>".
Otherwise, present your counterarguments."""
                else:
                    prompt = f"""Topic: {task}

Please provide your initial perspective on this topic."""
                
                response = await agent.arun(prompt, context)
                total_usage = total_usage + response.usage
                
                debate_history.append({
                    "agent": agent.name,
                    "response": response.content
                })
                round_responses.append(response.content)
                
                # Verificar consenso
                if "I AGREE:" in response.content:
                    agreement_count = sum(
                        1 for r in round_responses if "I AGREE:" in r
                    )
                    
                    if agreement_count / len(self.agents) >= self.config.consensus_threshold:
                        # Consenso atingido
                        consensus = response.content.split("I AGREE:")[1].strip()
                        
                        self._current_run.total_usage = total_usage
                        
                        return Response(
                            content=f"Consensus reached after {iteration + 1} rounds:\n\n{consensus}",
                            usage=total_usage,
                            status=ResponseStatus.SUCCESS,
                            metadata={"rounds": iteration + 1, "consensus": True}
                        )
        
        # Sem consenso, retornar resumo do debate
        final_summary = "\n\n".join([
            f"[{h['agent']}]: {h['response'][:200]}..."
            for h in debate_history[-len(self.agents):]
        ])
        
        self._current_run.total_usage = total_usage
        
        return Response(
            content=f"No consensus after {self.config.max_iterations} rounds.\n\nFinal positions:\n{final_summary}",
            usage=total_usage,
            status=ResponseStatus.SUCCESS,
            metadata={"rounds": self.config.max_iterations, "consensus": False}
        )
    
    def add_agent(self, agent: Agent) -> None:
        """Adiciona um agente à equipe."""
        self.agents.append(agent)
    
    def remove_agent(self, name: str) -> bool:
        """Remove um agente pelo nome."""
        for i, agent in enumerate(self.agents):
            if agent.name == name:
                self.agents.pop(i)
                return True
        return False
    
    def get_metrics(self) -> dict:
        """Retorna métricas da equipe."""
        total_runs = len(self._runs)
        
        return {
            "name": self.name,
            "workflow": self.config.workflow,
            "agents_count": len(self.agents),
            "total_runs": total_runs,
            "agents": [a.get_metrics() for a in self.agents]
        }


# Factory functions

def create_sequential_team(agents: list[Agent], **kwargs) -> Team:
    """Cria equipe sequencial."""
    return Team(agents=agents, workflow="sequential", **kwargs)


def create_parallel_team(agents: list[Agent], **kwargs) -> Team:
    """Cria equipe paralela."""
    return Team(agents=agents, workflow="parallel", **kwargs)


def create_hierarchical_team(
    agents: list[Agent],
    supervisor: Agent,
    **kwargs
) -> Team:
    """Cria equipe hierárquica."""
    return Team(
        agents=agents,
        supervisor=supervisor,
        workflow="hierarchical",
        **kwargs
    )


def create_debate_team(agents: list[Agent], **kwargs) -> Team:
    """Cria equipe de debate."""
    return Team(agents=agents, workflow="debate", **kwargs)

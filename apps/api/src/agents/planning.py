"""
Planning System - Sistema de Planejamento para Agentes

Implementa múltiplas estratégias de planejamento:
- ReAct: Reasoning + Acting
- CoT: Chain of Thought
- ToT: Tree of Thoughts
- GoT: Graph of Thoughts

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Planning System                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Task        │  │ Planner     │  │ Executor    │         │
│  │ Decomposer  │  │             │  │             │         │
│  │             │  │ - ReAct     │  │ - Step exec │         │
│  │ - Analyze   │→│ - CoT       │→│ - Monitor   │         │
│  │ - Split     │  │ - ToT       │  │ - Adapt     │         │
│  │ - Prioritize│  │ - GoT       │  │ - Verify    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │ Reflection│                            │
│                    │ - Evaluate│                            │
│                    │ - Learn   │                            │
│                    │ - Improve │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Callable, Awaitable
from enum import Enum
import logging
import json

from openai import AsyncOpenAI


logger = logging.getLogger(__name__)


class PlanningStrategy(str, Enum):
    """Estratégias de planejamento."""
    REACT = "react"
    COT = "cot"
    TOT = "tot"
    GOT = "got"
    STEP_BACK = "step_back"
    DECOMPOSE = "decompose"


class StepStatus(str, Enum):
    """Status de um step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """
    Representa um passo no plano.
    """
    id: int
    description: str
    reasoning: str = ""
    
    # Estado
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    
    # Dependências
    depends_on: list[int] = field(default_factory=list)
    
    # Tool a usar (opcional)
    tool_name: Optional[str] = None
    tool_args: dict = field(default_factory=dict)
    
    # Métricas
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "description": self.description,
            "reasoning": self.reasoning,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "duration_ms": self.duration_ms
        }


@dataclass
class Plan:
    """
    Representa um plano de execução.
    """
    goal: str
    strategy: PlanningStrategy
    steps: list[PlanStep] = field(default_factory=list)
    
    # Estado
    current_step: int = 0
    status: StepStatus = StepStatus.PENDING
    
    # Reflexão
    reflections: list[str] = field(default_factory=list)
    
    # Resultado final
    final_result: Optional[str] = None
    
    # Métricas
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0
    
    def add_step(self, step: PlanStep) -> None:
        """Adiciona um passo."""
        step.id = len(self.steps) + 1
        self.steps.append(step)
    
    def get_current_step(self) -> Optional[PlanStep]:
        """Retorna passo atual."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def advance(self) -> bool:
        """Avança para próximo passo."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            return True
        return False
    
    def get_completed_steps_summary(self) -> str:
        """Resumo dos passos completados."""
        completed = [s for s in self.steps if s.status == StepStatus.COMPLETED]
        if not completed:
            return "No steps completed yet."
        
        return "\n".join([
            f"Step {s.id}: {s.description} -> {s.result[:100]}..."
            for s in completed
        ])
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "goal": self.goal,
            "strategy": self.strategy.value,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "status": self.status.value,
            "reflections": self.reflections,
            "final_result": self.final_result,
            "total_duration_ms": self.total_duration_ms
        }


class TaskDecomposer:
    """
    Decompõe tarefas complexas em subtarefas.
    """
    
    DECOMPOSE_PROMPT = """You are a task decomposition expert.

Given a complex task, break it down into smaller, actionable steps.
Each step should be:
1. Clear and specific
2. Achievable with available tools
3. Logically ordered

Task: {task}

Available tools: {tools}

Respond in JSON format:
{{
    "analysis": "Brief analysis of the task",
    "steps": [
        {{
            "description": "What to do",
            "reasoning": "Why this step",
            "tool": "tool_name or null",
            "depends_on": [step_ids]
        }}
    ]
}}"""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self._client = client
    
    async def _get_client(self) -> AsyncOpenAI:
        """Obtém cliente OpenAI."""
        if self._client is None:
            import os
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    async def decompose(
        self,
        task: str,
        available_tools: list[str] = None
    ) -> list[PlanStep]:
        """
        Decompõe tarefa em passos.
        
        Args:
            task: Tarefa a decompor
            available_tools: Ferramentas disponíveis
            
        Returns:
            Lista de PlanStep
        """
        client = await self._get_client()
        tools_str = ", ".join(available_tools) if available_tools else "none"
        
        prompt = self.DECOMPOSE_PROMPT.format(
            task=task,
            tools=tools_str
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        steps = []
        for i, step_data in enumerate(data.get("steps", []), 1):
            step = PlanStep(
                id=i,
                description=step_data.get("description", ""),
                reasoning=step_data.get("reasoning", ""),
                tool_name=step_data.get("tool"),
                depends_on=step_data.get("depends_on", [])
            )
            steps.append(step)
        
        return steps


class ReActPlanner:
    """
    Implementa ReAct: Reasoning + Acting.
    
    Ciclo:
    1. Thought: Raciocinar sobre o estado atual
    2. Action: Decidir ação a tomar
    3. Observation: Observar resultado
    4. Repeat até concluir
    """
    
    REACT_PROMPT = """You are an AI assistant using the ReAct framework.

Task: {task}

Previous steps:
{history}

Available actions:
{actions}

Respond with your next step in this format:
Thought: [Your reasoning about what to do next]
Action: [The action to take - either a tool name or "finish"]
Action Input: [Input for the action, or final answer if finishing]"""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self._client = client
    
    async def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            import os
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    async def plan_next_step(
        self,
        task: str,
        history: list[dict],
        available_actions: list[str]
    ) -> dict:
        """
        Planeja próximo passo usando ReAct.
        
        Args:
            task: Tarefa original
            history: Histórico de pensamentos/ações
            available_actions: Ações disponíveis
            
        Returns:
            Dict com thought, action, action_input
        """
        client = await self._get_client()
        
        history_str = ""
        for h in history:
            history_str += f"Thought: {h.get('thought', '')}\n"
            history_str += f"Action: {h.get('action', '')}\n"
            history_str += f"Observation: {h.get('observation', '')}\n\n"
        
        if not history_str:
            history_str = "No previous steps."
        
        actions_str = ", ".join(available_actions + ["finish"])
        
        prompt = self.REACT_PROMPT.format(
            task=task,
            history=history_str,
            actions=actions_str
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Parse response
        result = {
            "thought": "",
            "action": "",
            "action_input": ""
        }
        
        lines = content.split("\n")
        for line in lines:
            if line.startswith("Thought:"):
                result["thought"] = line[8:].strip()
            elif line.startswith("Action:"):
                result["action"] = line[7:].strip()
            elif line.startswith("Action Input:"):
                result["action_input"] = line[13:].strip()
        
        return result


class TreeOfThoughts:
    """
    Implementa Tree of Thoughts (ToT).
    
    Explora múltiplos caminhos de raciocínio em paralelo,
    avaliando e podando branches menos promissoras.
    """
    
    GENERATE_PROMPT = """Generate {n} different approaches to solve this problem.

Problem: {problem}

Current state: {state}

For each approach, provide:
1. A brief description
2. Pros and cons
3. Estimated success probability (0-1)

Format as JSON:
{{
    "approaches": [
        {{
            "description": "...",
            "pros": ["..."],
            "cons": ["..."],
            "probability": 0.X
        }}
    ]
}}"""

    EVALUATE_PROMPT = """Evaluate this thought/approach:

Problem: {problem}
Approach: {approach}

Rate from 0-10:
1. Feasibility
2. Effectiveness
3. Efficiency

Respond in JSON:
{{
    "feasibility": X,
    "effectiveness": X,
    "efficiency": X,
    "overall": X,
    "reasoning": "..."
}}"""

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        breadth: int = 3,
        depth: int = 3
    ):
        self._client = client
        self.breadth = breadth
        self.depth = depth
    
    async def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            import os
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    async def generate_thoughts(
        self,
        problem: str,
        state: str,
        n: int = 3
    ) -> list[dict]:
        """Gera múltiplos pensamentos/abordagens."""
        client = await self._get_client()
        
        prompt = self.GENERATE_PROMPT.format(
            n=n,
            problem=problem,
            state=state
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        return data.get("approaches", [])
    
    async def evaluate_thought(
        self,
        problem: str,
        approach: str
    ) -> dict:
        """Avalia um pensamento/abordagem."""
        client = await self._get_client()
        
        prompt = self.EVALUATE_PROMPT.format(
            problem=problem,
            approach=approach
        )
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    
    async def search(
        self,
        problem: str,
        initial_state: str = ""
    ) -> list[dict]:
        """
        Executa busca ToT.
        
        Returns:
            Lista de pensamentos ordenados por score
        """
        all_thoughts = []
        current_states = [initial_state or "Starting point"]
        
        for depth in range(self.depth):
            next_states = []
            
            for state in current_states:
                # Gerar pensamentos
                thoughts = await self.generate_thoughts(
                    problem, state, self.breadth
                )
                
                # Avaliar cada pensamento
                for thought in thoughts:
                    evaluation = await self.evaluate_thought(
                        problem,
                        thought["description"]
                    )
                    
                    thought["evaluation"] = evaluation
                    thought["depth"] = depth
                    thought["parent_state"] = state
                    all_thoughts.append(thought)
                    
                    # Estado para próxima iteração
                    if evaluation["overall"] >= 6:
                        next_states.append(thought["description"])
            
            current_states = next_states[:self.breadth]
            
            if not current_states:
                break
        
        # Ordenar por score
        all_thoughts.sort(
            key=lambda x: x.get("evaluation", {}).get("overall", 0),
            reverse=True
        )
        
        return all_thoughts


class PlanningAgent:
    """
    Agente com capacidades de planejamento.
    
    Combina múltiplas estratégias de planejamento
    para resolver tarefas complexas.
    
    Uso:
    ```python
    agent = PlanningAgent()
    
    # Criar plano
    plan = await agent.create_plan(
        "Write a research report about AI",
        strategy=PlanningStrategy.REACT
    )
    
    # Executar plano
    result = await agent.execute_plan(plan)
    ```
    """
    
    def __init__(
        self,
        default_strategy: PlanningStrategy = PlanningStrategy.REACT,
        client: Optional[AsyncOpenAI] = None
    ):
        self.default_strategy = default_strategy
        self._client = client
        
        # Componentes
        self.decomposer = TaskDecomposer(client)
        self.react_planner = ReActPlanner(client)
        self.tot = TreeOfThoughts(client)
        
        # Tool executor (a ser injetado)
        self._tool_executor: Optional[Callable] = None
        
        # Histórico
        self._plans: list[Plan] = []
    
    async def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            import os
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    def set_tool_executor(
        self,
        executor: Callable[[str, dict], Awaitable[str]]
    ) -> None:
        """Define executor de ferramentas."""
        self._tool_executor = executor
    
    async def create_plan(
        self,
        goal: str,
        strategy: Optional[PlanningStrategy] = None,
        available_tools: list[str] = None
    ) -> Plan:
        """
        Cria um plano para atingir o objetivo.
        
        Args:
            goal: Objetivo a atingir
            strategy: Estratégia de planejamento
            available_tools: Ferramentas disponíveis
            
        Returns:
            Plan
        """
        strategy = strategy or self.default_strategy
        
        plan = Plan(goal=goal, strategy=strategy)
        
        if strategy == PlanningStrategy.DECOMPOSE:
            # Decompor em passos
            steps = await self.decomposer.decompose(goal, available_tools)
            for step in steps:
                plan.add_step(step)
        
        elif strategy == PlanningStrategy.TOT:
            # Usar Tree of Thoughts
            thoughts = await self.tot.search(goal)
            
            # Converter melhores pensamentos em passos
            for i, thought in enumerate(thoughts[:5], 1):
                step = PlanStep(
                    id=i,
                    description=thought["description"],
                    reasoning=thought.get("evaluation", {}).get("reasoning", "")
                )
                plan.add_step(step)
        
        else:  # REACT ou outros
            # Para ReAct, criamos um plano inicial básico
            initial_step = PlanStep(
                id=1,
                description="Analyze task and determine approach",
                reasoning="Start by understanding the task"
            )
            plan.add_step(initial_step)
        
        plan.status = StepStatus.PENDING
        self._plans.append(plan)
        
        return plan
    
    async def execute_plan(
        self,
        plan: Plan,
        max_iterations: int = 10
    ) -> str:
        """
        Executa um plano.
        
        Args:
            plan: Plano a executar
            max_iterations: Máximo de iterações (para ReAct)
            
        Returns:
            Resultado final
        """
        start = datetime.now()
        plan.status = StepStatus.IN_PROGRESS
        
        try:
            if plan.strategy == PlanningStrategy.REACT:
                result = await self._execute_react(plan, max_iterations)
            else:
                result = await self._execute_sequential(plan)
            
            plan.status = StepStatus.COMPLETED
            plan.final_result = result
            
        except Exception as e:
            plan.status = StepStatus.FAILED
            plan.final_result = f"Execution failed: {e}"
            result = plan.final_result
        
        plan.completed_at = datetime.now()
        plan.total_duration_ms = (datetime.now() - start).total_seconds() * 1000
        
        return result
    
    async def _execute_react(
        self,
        plan: Plan,
        max_iterations: int
    ) -> str:
        """Executa plano usando ReAct."""
        history = []
        available_actions = ["search", "calculate", "write", "analyze"]
        
        if self._tool_executor:
            # Adicionar tools disponíveis
            pass
        
        for iteration in range(max_iterations):
            # Obter próximo passo
            step_result = await self.react_planner.plan_next_step(
                plan.goal,
                history,
                available_actions
            )
            
            thought = step_result["thought"]
            action = step_result["action"].lower()
            action_input = step_result["action_input"]
            
            # Registrar no plano
            step = PlanStep(
                id=len(plan.steps) + 1,
                description=action,
                reasoning=thought
            )
            step.started_at = datetime.now()
            
            # Verificar se terminou
            if action == "finish":
                step.status = StepStatus.COMPLETED
                step.result = action_input
                plan.add_step(step)
                
                # Adicionar reflexão
                plan.reflections.append(f"Completed in {iteration + 1} iterations")
                
                return action_input
            
            # Executar ação
            observation = ""
            
            if self._tool_executor and action in available_actions:
                try:
                    observation = await self._tool_executor(action, {"input": action_input})
                    step.status = StepStatus.COMPLETED
                except Exception as e:
                    observation = f"Error: {e}"
                    step.status = StepStatus.FAILED
            else:
                observation = f"Action '{action}' not available"
                step.status = StepStatus.SKIPPED
            
            step.result = observation
            step.completed_at = datetime.now()
            plan.add_step(step)
            
            # Adicionar ao histórico
            history.append({
                "thought": thought,
                "action": action,
                "observation": observation
            })
        
        return "Max iterations reached without completion"
    
    async def _execute_sequential(self, plan: Plan) -> str:
        """Executa plano sequencialmente."""
        results = []
        
        for step in plan.steps:
            step.status = StepStatus.IN_PROGRESS
            step.started_at = datetime.now()
            
            # Verificar dependências
            deps_completed = all(
                plan.steps[d-1].status == StepStatus.COMPLETED
                for d in step.depends_on
                if d > 0 and d <= len(plan.steps)
            )
            
            if not deps_completed:
                step.status = StepStatus.SKIPPED
                step.error = "Dependencies not completed"
                continue
            
            # Executar passo
            if step.tool_name and self._tool_executor:
                try:
                    result = await self._tool_executor(step.tool_name, step.tool_args)
                    step.result = result
                    step.status = StepStatus.COMPLETED
                    results.append(f"Step {step.id}: {result}")
                except Exception as e:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
            else:
                # Sem tool, marcar como completado
                step.status = StepStatus.COMPLETED
                step.result = f"Completed: {step.description}"
                results.append(step.result)
            
            step.completed_at = datetime.now()
        
        return "\n".join(results)
    
    async def reflect(self, plan: Plan) -> str:
        """
        Reflete sobre a execução do plano.
        
        Args:
            plan: Plano executado
            
        Returns:
            Reflexão
        """
        client = await self._get_client()
        
        prompt = f"""Reflect on this plan execution:

Goal: {plan.goal}
Strategy: {plan.strategy.value}
Status: {plan.status.value}

Steps:
{plan.get_completed_steps_summary()}

Final result: {plan.final_result}

Provide:
1. What went well
2. What could be improved
3. Lessons learned"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        reflection = response.choices[0].message.content
        plan.reflections.append(reflection)
        
        return reflection
    
    def get_plans_history(self, limit: int = 10) -> list[dict]:
        """Retorna histórico de planos."""
        return [p.to_dict() for p in self._plans[-limit:]]

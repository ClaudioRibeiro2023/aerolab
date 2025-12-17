"""
Agno Team Orchestrator v2.0 - Orchestration Engine

Core engine with 15+ orchestration modes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import logging

from .types import (
    OrchestrationMode, TeamConfiguration, TeamExecution, ExecutionStatus,
    Task, TaskResult, TaskStatus, Message, MessageType, Priority,
    AgentProfile, Conflict, Resolution, ResolutionStrategy
)
from .tasks import TaskManager, TaskScheduler
from .communication import MessageBus

logger = logging.getLogger(__name__)


# ============================================================
# BASE ORCHESTRATOR
# ============================================================

class BaseOrchestrator(ABC):
    """Base class for orchestration modes."""
    
    def __init__(self, config: TeamConfiguration):
        self.config = config
        self.message_bus = MessageBus()
        self.task_manager = TaskManager()
        self._execution: Optional[TeamExecution] = None
    
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        """Execute the team with this orchestration mode."""
        pass
    
    async def _execute_agent(
        self,
        agent: AgentProfile,
        task: Task,
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute a single agent on a task."""
        start_time = datetime.now()
        
        try:
            # Build prompt
            prompt = self._build_prompt(agent, task, context)
            
            # Simulate execution (replace with actual LLM call)
            output = await self._call_llm(agent, prompt)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return TaskResult(
                task_id=task.id,
                success=True,
                output=output,
                quality_score=0.85,  # Would be calculated
                tokens_used=1000,
                cost=0.01,
                duration_ms=int(duration),
                agent_id=agent.id,
            )
        except Exception as e:
            logger.error(f"Agent {agent.name} failed on task {task.name}: {e}")
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                agent_id=agent.id,
            )
    
    def _build_prompt(
        self,
        agent: AgentProfile,
        task: Task,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for agent."""
        return f"""You are {agent.name}, {agent.role}.

GOAL: {agent.goal}

BACKSTORY: {agent.backstory}

TASK: {task.name}
{task.description}

EXPECTED OUTPUT: {task.expected_output}

CONTEXT:
{context}

Please complete the task."""
    
    async def _call_llm(self, agent: AgentProfile, prompt: str) -> str:
        """Call LLM for agent. Override in production."""
        # Placeholder - would integrate with actual LLM
        await asyncio.sleep(0.1)  # Simulate latency
        return f"[Response from {agent.name}]: Task completed successfully."
    
    def _create_execution(self) -> TeamExecution:
        """Create execution record."""
        return TeamExecution(
            team_id=self.config.id,
            team_config=self.config,
            status=ExecutionStatus.PENDING,
            tasks_total=len(self.config.tasks),
            started_at=datetime.now(),
        )


# ============================================================
# SEQUENTIAL ORCHESTRATOR
# ============================================================

class SequentialOrchestrator(BaseOrchestrator):
    """Execute agents sequentially, one after another."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data, "results": {}}
        
        for i, agent in enumerate(self.config.agents):
            task = self.config.tasks[i] if i < len(self.config.tasks) else Task(
                name=f"Task for {agent.name}",
                description="Process the input"
            )
            
            result = await self._execute_agent(agent, task, context)
            
            context["results"][agent.id] = result.output
            execution.task_results.append(result)
            execution.tasks_completed += 1
            execution.total_tokens += result.tokens_used
            execution.total_cost += result.cost
            
            if progress_callback:
                await progress_callback(execution)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = context["results"]
        
        return execution


# ============================================================
# PARALLEL ORCHESTRATOR
# ============================================================

class ParallelOrchestrator(BaseOrchestrator):
    """Execute agents in parallel."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data}
        
        # Execute all agents in parallel
        tasks = []
        for i, agent in enumerate(self.config.agents):
            task = self.config.tasks[i] if i < len(self.config.tasks) else Task(
                name=f"Task for {agent.name}",
                description="Process the input"
            )
            tasks.append(self._execute_agent(agent, task, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        outputs = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                result = TaskResult(
                    task_id=f"task_{i}",
                    success=False,
                    error=str(result),
                    agent_id=self.config.agents[i].id
                )
            
            outputs[self.config.agents[i].id] = result.output
            execution.task_results.append(result)
            execution.tasks_completed += 1
            execution.total_tokens += result.tokens_used
            execution.total_cost += result.cost
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = outputs
        
        return execution


# ============================================================
# HIERARCHICAL ORCHESTRATOR
# ============================================================

class HierarchicalOrchestrator(BaseOrchestrator):
    """Supervisor delegates to workers."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        # First agent is supervisor
        supervisor = self.config.agents[0] if self.config.agents else None
        workers = self.config.agents[1:] if len(self.config.agents) > 1 else []
        
        if not supervisor:
            execution.status = ExecutionStatus.FAILED
            execution.error = "No supervisor defined"
            return execution
        
        context = {"input": input_data, "results": {}}
        
        # Supervisor creates plan
        plan_task = Task(
            name="Create Execution Plan",
            description=f"Create a plan to process: {input_data}. Available workers: {[w.name for w in workers]}"
        )
        
        plan_result = await self._execute_agent(supervisor, plan_task, context)
        execution.task_results.append(plan_result)
        
        # Workers execute (simplified - would parse plan)
        for worker in workers:
            task = Task(
                name=f"Execute assigned work",
                description=f"Complete your assigned portion of the plan"
            )
            
            result = await self._execute_agent(worker, task, context)
            context["results"][worker.id] = result.output
            execution.task_results.append(result)
            execution.tasks_completed += 1
        
        # Supervisor synthesizes
        synthesis_task = Task(
            name="Synthesize Results",
            description=f"Synthesize worker outputs into final result"
        )
        
        synthesis_result = await self._execute_agent(supervisor, synthesis_task, context)
        execution.task_results.append(synthesis_result)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = synthesis_result.output
        
        return execution


# ============================================================
# DEBATE ORCHESTRATOR
# ============================================================

class DebateOrchestrator(BaseOrchestrator):
    """Agents debate to reach best solution."""
    
    def __init__(self, config: TeamConfiguration, max_rounds: int = 3):
        super().__init__(config)
        self.max_rounds = max_rounds
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data, "debate_history": []}
        
        # Initial positions
        positions = {}
        for agent in self.config.agents:
            task = Task(
                name="State Initial Position",
                description=f"State your position on: {input_data}"
            )
            result = await self._execute_agent(agent, task, context)
            positions[agent.id] = result.output
            execution.task_results.append(result)
        
        context["debate_history"].append({"round": 0, "positions": positions.copy()})
        
        # Debate rounds
        for round_num in range(1, self.max_rounds + 1):
            new_positions = {}
            
            for agent in self.config.agents:
                other_positions = {k: v for k, v in positions.items() if k != agent.id}
                
                task = Task(
                    name=f"Debate Round {round_num}",
                    description=f"Consider other positions and refine yours: {other_positions}"
                )
                
                result = await self._execute_agent(agent, task, context)
                new_positions[agent.id] = result.output
                execution.task_results.append(result)
            
            positions = new_positions
            context["debate_history"].append({"round": round_num, "positions": positions.copy()})
        
        # Final synthesis
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "final_positions": positions,
            "debate_history": context["debate_history"],
        }
        
        return execution


# ============================================================
# CONSENSUS ORCHESTRATOR
# ============================================================

class ConsensusOrchestrator(BaseOrchestrator):
    """Agents work towards consensus."""
    
    def __init__(self, config: TeamConfiguration, max_rounds: int = 5):
        super().__init__(config)
        self.max_rounds = max_rounds
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data, "proposals": [], "agreements": []}
        
        for round_num in range(self.max_rounds):
            # Each agent proposes or comments
            round_proposals = []
            
            for agent in self.config.agents:
                task = Task(
                    name=f"Consensus Round {round_num + 1}",
                    description=f"Propose solution or comment on existing: {context['proposals']}"
                )
                
                result = await self._execute_agent(agent, task, context)
                round_proposals.append({
                    "agent": agent.id,
                    "proposal": result.output,
                })
                execution.task_results.append(result)
            
            context["proposals"].extend(round_proposals)
            
            # Check for consensus (simplified)
            if self._check_consensus(round_proposals):
                break
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "consensus_reached": True,
            "final_proposal": context["proposals"][-1] if context["proposals"] else None,
        }
        
        return execution
    
    def _check_consensus(self, proposals: List[Dict]) -> bool:
        """Check if consensus is reached (simplified)."""
        # In production, would use semantic similarity
        return len(proposals) > 0 and all(
            "agree" in str(p.get("proposal", "")).lower()
            for p in proposals
        )


# ============================================================
# VOTING ORCHESTRATOR
# ============================================================

class VotingOrchestrator(BaseOrchestrator):
    """Agents vote on proposals."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data}
        
        # Generate proposals
        proposals = []
        for agent in self.config.agents:
            task = Task(
                name="Generate Proposal",
                description=f"Generate a proposal for: {input_data}"
            )
            
            result = await self._execute_agent(agent, task, context)
            proposals.append({
                "agent": agent.id,
                "proposal": result.output,
            })
            execution.task_results.append(result)
        
        # Vote on proposals
        votes = {i: 0 for i in range(len(proposals))}
        
        for agent in self.config.agents:
            task = Task(
                name="Vote on Proposals",
                description=f"Vote for best proposal (0-{len(proposals)-1}): {proposals}"
            )
            
            result = await self._execute_agent(agent, task, context)
            # Parse vote (simplified)
            try:
                vote = int(str(result.output)[0]) % len(proposals)
                votes[vote] += 1
            except:
                pass
        
        # Determine winner
        winner_idx = max(votes.keys(), key=lambda k: votes[k])
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "proposals": proposals,
            "votes": votes,
            "winner": proposals[winner_idx],
        }
        
        return execution


# ============================================================
# EXPERT PANEL ORCHESTRATOR
# ============================================================

class ExpertPanelOrchestrator(BaseOrchestrator):
    """Panel of experts each contribute expertise."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        context = {"input": input_data, "expert_opinions": []}
        
        # Each expert provides perspective
        for agent in self.config.agents:
            task = Task(
                name=f"Expert Opinion: {agent.role}",
                description=f"Provide expert analysis from your {agent.role} perspective on: {input_data}"
            )
            
            result = await self._execute_agent(agent, task, context)
            context["expert_opinions"].append({
                "expert": agent.name,
                "role": agent.role,
                "opinion": result.output,
            })
            execution.task_results.append(result)
        
        # Synthesize opinions (by first agent or designated synthesizer)
        synthesizer = self.config.agents[0]
        synthesis_task = Task(
            name="Synthesize Expert Opinions",
            description=f"Synthesize all expert opinions into comprehensive analysis: {context['expert_opinions']}"
        )
        
        synthesis_result = await self._execute_agent(synthesizer, synthesis_task, context)
        execution.task_results.append(synthesis_result)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "expert_opinions": context["expert_opinions"],
            "synthesis": synthesis_result.output,
        }
        
        return execution


# ============================================================
# PIPELINE ORCHESTRATOR
# ============================================================

class PipelineOrchestrator(BaseOrchestrator):
    """Process data through pipeline of agents."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        current_data = input_data
        pipeline_stages = []
        
        for i, agent in enumerate(self.config.agents):
            task = self.config.tasks[i] if i < len(self.config.tasks) else Task(
                name=f"Pipeline Stage {i + 1}",
                description="Process and transform input"
            )
            
            context = {"input": current_data, "stage": i + 1}
            result = await self._execute_agent(agent, task, context)
            
            pipeline_stages.append({
                "stage": i + 1,
                "agent": agent.name,
                "input": current_data,
                "output": result.output,
            })
            
            current_data = result.output
            execution.task_results.append(result)
            execution.tasks_completed += 1
            
            if progress_callback:
                await progress_callback(execution)
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "final_output": current_data,
            "pipeline_stages": pipeline_stages,
        }
        
        return execution


# ============================================================
# SWARM ORCHESTRATOR
# ============================================================

class SwarmOrchestrator(BaseOrchestrator):
    """Swarm intelligence - emergent behavior."""
    
    def __init__(self, config: TeamConfiguration, iterations: int = 3):
        super().__init__(config)
        self.iterations = iterations
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        execution = self._create_execution()
        execution.status = ExecutionStatus.RUNNING
        
        # Each agent has a solution
        solutions = {}
        
        for agent in self.config.agents:
            task = Task(
                name="Initial Solution",
                description=f"Generate initial solution for: {input_data}"
            )
            result = await self._execute_agent(agent, task, {"input": input_data})
            solutions[agent.id] = {"solution": result.output, "score": 0.5}
            execution.task_results.append(result)
        
        # Iterate - agents learn from best solutions
        for iteration in range(self.iterations):
            # Find best solution (simplified)
            best = max(solutions.items(), key=lambda x: x[1]["score"])
            
            for agent in self.config.agents:
                if solutions[agent.id]["score"] < best[1]["score"]:
                    task = Task(
                        name=f"Improve Solution (Iteration {iteration + 1})",
                        description=f"Improve your solution based on best: {best[1]['solution']}"
                    )
                    result = await self._execute_agent(
                        agent, task, 
                        {"current": solutions[agent.id], "best": best[1]}
                    )
                    solutions[agent.id] = {
                        "solution": result.output,
                        "score": min(1.0, solutions[agent.id]["score"] + 0.1)
                    }
                    execution.task_results.append(result)
        
        # Final best solution
        best_final = max(solutions.items(), key=lambda x: x[1]["score"])
        
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.output = {
            "best_solution": best_final[1]["solution"],
            "all_solutions": solutions,
        }
        
        return execution


# ============================================================
# ORCHESTRATION ENGINE
# ============================================================

class TeamOrchestrationEngine:
    """Main orchestration engine."""
    
    ORCHESTRATORS = {
        OrchestrationMode.SEQUENTIAL: SequentialOrchestrator,
        OrchestrationMode.PARALLEL: ParallelOrchestrator,
        OrchestrationMode.HIERARCHICAL: HierarchicalOrchestrator,
        OrchestrationMode.DEBATE: DebateOrchestrator,
        OrchestrationMode.CONSENSUS: ConsensusOrchestrator,
        OrchestrationMode.VOTING: VotingOrchestrator,
        OrchestrationMode.EXPERT_PANEL: ExpertPanelOrchestrator,
        OrchestrationMode.PIPELINE: PipelineOrchestrator,
        OrchestrationMode.SWARM: SwarmOrchestrator,
    }
    
    def __init__(self):
        self._executions: Dict[str, TeamExecution] = {}
    
    async def execute(
        self,
        config: TeamConfiguration,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> TeamExecution:
        """Execute a team configuration."""
        orchestrator_class = self.ORCHESTRATORS.get(config.mode)
        
        if not orchestrator_class:
            # Default to sequential
            orchestrator_class = SequentialOrchestrator
        
        orchestrator = orchestrator_class(config)
        execution = await orchestrator.execute(input_data, progress_callback)
        
        self._executions[execution.id] = execution
        return execution
    
    def get_execution(self, execution_id: str) -> Optional[TeamExecution]:
        """Get execution by ID."""
        return self._executions.get(execution_id)
    
    def list_executions(self) -> List[TeamExecution]:
        """List all executions."""
        return list(self._executions.values())
    
    @staticmethod
    def list_modes() -> List[str]:
        """List available orchestration modes."""
        return [mode.value for mode in OrchestrationMode]


# Singleton
_engine: Optional[TeamOrchestrationEngine] = None


def get_orchestration_engine() -> TeamOrchestrationEngine:
    """Get the global orchestration engine."""
    global _engine
    if _engine is None:
        _engine = TeamOrchestrationEngine()
    return _engine

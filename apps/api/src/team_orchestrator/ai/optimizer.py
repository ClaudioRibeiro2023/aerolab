"""
Agno Team Orchestrator v2.0 - Team Optimizer

AI-powered team optimization.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..types import (
    TeamConfiguration, TeamExecution, TeamMetrics,
    AgentProfile, OrchestrationMode
)

logger = logging.getLogger(__name__)


class OptimizationObjective(str, Enum):
    """Optimization objectives."""
    PERFORMANCE = "performance"
    SPEED = "speed"
    COST = "cost"
    BALANCED = "balanced"


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion."""
    category: str  # composition, config, mode, structure
    description: str
    impact: str  # high, medium, low
    confidence: float  # 0-1
    implementation: Optional[Dict[str, Any]] = None


@dataclass
class OptimizationResult:
    """Result of optimization analysis."""
    suggestions: List[OptimizationSuggestion]
    expected_improvement: Dict[str, float]
    confidence: float
    analysis: Dict[str, Any] = field(default_factory=dict)


class TeamOptimizer:
    """
    Optimizes team composition and configuration.
    
    Analyzes:
    - Agent composition and compatibility
    - Task-agent fit
    - Orchestration mode effectiveness
    - Resource utilization
    """
    
    def __init__(self):
        self._history: Dict[str, List[TeamExecution]] = {}
    
    async def optimize(
        self,
        team: TeamConfiguration,
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        history: Optional[List[TeamExecution]] = None
    ) -> OptimizationResult:
        """
        Optimize team configuration.
        
        Args:
            team: Current team configuration
            objective: Optimization objective
            history: Historical executions for analysis
            
        Returns:
            OptimizationResult with suggestions
        """
        suggestions = []
        
        # Store history
        if history:
            self._history[team.id] = history
        
        # 1. Analyze composition
        composition_suggestions = await self._analyze_composition(team, objective)
        suggestions.extend(composition_suggestions)
        
        # 2. Analyze mode
        mode_suggestions = await self._analyze_mode(team, objective)
        suggestions.extend(mode_suggestions)
        
        # 3. Analyze agent fit
        fit_suggestions = await self._analyze_agent_fit(team)
        suggestions.extend(fit_suggestions)
        
        # 4. Analyze bottlenecks
        if history:
            bottleneck_suggestions = await self._analyze_bottlenecks(team, history)
            suggestions.extend(bottleneck_suggestions)
        
        # Calculate expected improvement
        improvement = self._calculate_improvement(suggestions, objective)
        
        # Calculate confidence
        confidence = self._calculate_confidence(history)
        
        return OptimizationResult(
            suggestions=suggestions,
            expected_improvement=improvement,
            confidence=confidence,
            analysis={
                "team_size": len(team.agents),
                "task_count": len(team.tasks),
                "mode": team.mode.value,
                "history_count": len(history) if history else 0,
            }
        )
    
    async def _analyze_composition(
        self,
        team: TeamConfiguration,
        objective: OptimizationObjective
    ) -> List[OptimizationSuggestion]:
        """Analyze team composition."""
        suggestions = []
        
        # Check team size
        if len(team.agents) < 2:
            suggestions.append(OptimizationSuggestion(
                category="composition",
                description="Team has less than 2 agents. Consider adding complementary agents.",
                impact="high",
                confidence=0.9,
            ))
        
        if len(team.agents) > 6:
            suggestions.append(OptimizationSuggestion(
                category="composition",
                description="Team has more than 6 agents. Consider splitting into sub-teams.",
                impact="medium",
                confidence=0.7,
            ))
        
        # Check skill coverage
        skill_coverage = self._assess_skill_coverage(team)
        if skill_coverage < 0.7:
            suggestions.append(OptimizationSuggestion(
                category="composition",
                description=f"Skill coverage is {skill_coverage:.0%}. Consider adding agents with missing skills.",
                impact="medium",
                confidence=0.8,
            ))
        
        # Check compatibility
        compatibility = self._calculate_compatibility(team.agents)
        if compatibility < 0.6:
            suggestions.append(OptimizationSuggestion(
                category="composition",
                description=f"Team compatibility is {compatibility:.0%}. Consider adjusting personalities or roles.",
                impact="medium",
                confidence=0.75,
            ))
        
        return suggestions
    
    async def _analyze_mode(
        self,
        team: TeamConfiguration,
        objective: OptimizationObjective
    ) -> List[OptimizationSuggestion]:
        """Analyze orchestration mode."""
        suggestions = []
        
        # Suggest mode based on objective
        suggested_mode = self._suggest_mode(team, objective)
        
        if suggested_mode != team.mode:
            suggestions.append(OptimizationSuggestion(
                category="mode",
                description=f"Consider using '{suggested_mode.value}' mode instead of '{team.mode.value}' for {objective.value} optimization.",
                impact="high",
                confidence=0.7,
                implementation={"mode": suggested_mode.value},
            ))
        
        # Check mode-specific optimizations
        if team.mode == OrchestrationMode.HIERARCHICAL and not team.supervisor_id:
            suggestions.append(OptimizationSuggestion(
                category="mode",
                description="Hierarchical mode requires a supervisor. Set supervisor_id.",
                impact="high",
                confidence=0.95,
            ))
        
        return suggestions
    
    async def _analyze_agent_fit(
        self,
        team: TeamConfiguration
    ) -> List[OptimizationSuggestion]:
        """Analyze agent-task fit."""
        suggestions = []
        
        for task in team.tasks:
            best_agent = self._find_best_agent_for_task(task, team.agents)
            
            if task.assigned_to and task.assigned_to != best_agent.id:
                suggestions.append(OptimizationSuggestion(
                    category="assignment",
                    description=f"Task '{task.name}' might be better suited for agent '{best_agent.name}'.",
                    impact="low",
                    confidence=0.6,
                    implementation={"task_id": task.id, "agent_id": best_agent.id},
                ))
        
        return suggestions
    
    async def _analyze_bottlenecks(
        self,
        team: TeamConfiguration,
        history: List[TeamExecution]
    ) -> List[OptimizationSuggestion]:
        """Analyze bottlenecks from history."""
        suggestions = []
        
        # Find slowest tasks
        task_durations = {}
        for execution in history:
            for result in execution.task_results:
                if result.task_id not in task_durations:
                    task_durations[result.task_id] = []
                task_durations[result.task_id].append(result.duration_ms)
        
        for task_id, durations in task_durations.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 30000:  # > 30 seconds
                suggestions.append(OptimizationSuggestion(
                    category="bottleneck",
                    description=f"Task {task_id} takes avg {avg_duration/1000:.1f}s. Consider parallelizing or simplifying.",
                    impact="medium",
                    confidence=0.8,
                ))
        
        # Find high-failure tasks
        task_failures = {}
        for execution in history:
            for result in execution.task_results:
                if result.task_id not in task_failures:
                    task_failures[result.task_id] = {"success": 0, "fail": 0}
                if result.success:
                    task_failures[result.task_id]["success"] += 1
                else:
                    task_failures[result.task_id]["fail"] += 1
        
        for task_id, counts in task_failures.items():
            total = counts["success"] + counts["fail"]
            if total > 2 and counts["fail"] / total > 0.3:
                suggestions.append(OptimizationSuggestion(
                    category="reliability",
                    description=f"Task {task_id} has {counts['fail']/total:.0%} failure rate. Review task requirements.",
                    impact="high",
                    confidence=0.85,
                ))
        
        return suggestions
    
    def _suggest_mode(
        self,
        team: TeamConfiguration,
        objective: OptimizationObjective
    ) -> OrchestrationMode:
        """Suggest best mode for objective."""
        if objective == OptimizationObjective.SPEED:
            return OrchestrationMode.PARALLEL
        
        if objective == OptimizationObjective.COST:
            return OrchestrationMode.SEQUENTIAL
        
        if objective == OptimizationObjective.PERFORMANCE:
            if len(team.agents) > 3:
                return OrchestrationMode.HIERARCHICAL
            return OrchestrationMode.EXPERT_PANEL
        
        # Balanced
        return OrchestrationMode.PIPELINE
    
    def _assess_skill_coverage(self, team: TeamConfiguration) -> float:
        """Assess skill coverage for tasks."""
        if not team.tasks:
            return 1.0
        
        required_skills = set()
        for task in team.tasks:
            required_skills.update(task.tools_required)
        
        if not required_skills:
            return 1.0
        
        available_skills = set()
        for agent in team.agents:
            available_skills.update(agent.tools)
        
        covered = len(required_skills & available_skills)
        return covered / len(required_skills)
    
    def _calculate_compatibility(self, agents: List[AgentProfile]) -> float:
        """Calculate team compatibility."""
        if len(agents) < 2:
            return 1.0
        
        total = 0.0
        pairs = 0
        
        for i, a1 in enumerate(agents):
            for a2 in agents[i + 1:]:
                total += a1.calculate_compatibility(a2)
                pairs += 1
        
        return total / pairs if pairs > 0 else 1.0
    
    def _find_best_agent_for_task(
        self,
        task,
        agents: List[AgentProfile]
    ) -> AgentProfile:
        """Find best agent for a task."""
        best_agent = agents[0]
        best_score = 0.0
        
        for agent in agents:
            score = 0.0
            
            # Tool match
            if task.tools_required:
                tool_match = len(set(agent.tools) & set(task.tools_required)) / len(task.tools_required)
                score += 0.5 * tool_match
            else:
                score += 0.5
            
            # Skill relevance (simplified)
            score += 0.5 * (agent.performance_score if agent.performance_score else 0.5)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    def _calculate_improvement(
        self,
        suggestions: List[OptimizationSuggestion],
        objective: OptimizationObjective
    ) -> Dict[str, float]:
        """Calculate expected improvement."""
        improvement = {
            "performance": 0.0,
            "speed": 0.0,
            "cost": 0.0,
        }
        
        impact_weights = {"high": 0.15, "medium": 0.08, "low": 0.03}
        
        for suggestion in suggestions:
            weight = impact_weights.get(suggestion.impact, 0.05)
            
            if objective == OptimizationObjective.PERFORMANCE:
                improvement["performance"] += weight * suggestion.confidence
            elif objective == OptimizationObjective.SPEED:
                improvement["speed"] += weight * suggestion.confidence
            elif objective == OptimizationObjective.COST:
                improvement["cost"] += weight * suggestion.confidence
            else:
                improvement["performance"] += weight * suggestion.confidence * 0.4
                improvement["speed"] += weight * suggestion.confidence * 0.3
                improvement["cost"] += weight * suggestion.confidence * 0.3
        
        return improvement
    
    def _calculate_confidence(self, history: Optional[List[TeamExecution]]) -> float:
        """Calculate confidence in suggestions."""
        if not history:
            return 0.5  # Low confidence without history
        
        if len(history) < 5:
            return 0.6
        
        if len(history) < 20:
            return 0.75
        
        return 0.9

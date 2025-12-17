"""
Agno Team Orchestrator v2.0 - Agent Learning System

Continuous learning and improvement for agents.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..types import AgentProfile, PersonalityTraits, Skill

logger = logging.getLogger(__name__)


@dataclass
class Feedback:
    """Feedback for agent performance."""
    execution_id: str
    agent_id: str
    rating: float  # 1-5
    comments: str = ""
    aspects: Dict[str, float] = field(default_factory=dict)  # quality, speed, accuracy, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "human"  # human, auto, peer


@dataclass
class PerformancePattern:
    """Identified performance pattern."""
    pattern_type: str
    description: str
    frequency: int
    impact: str  # positive, negative, neutral
    suggestion: Optional[str] = None


@dataclass
class AgentEvolution:
    """Evolution record for an agent."""
    agent_id: str
    version: str
    changes: Dict[str, Any]
    reason: str
    created_at: datetime = field(default_factory=datetime.now)


class AgentLearningSystem:
    """
    Continuous learning system for agents.
    
    Features:
    - Feedback collection and analysis
    - Pattern recognition
    - Personality adjustment
    - Skill updates
    - Agent evolution
    """
    
    def __init__(self):
        self._feedback: Dict[str, List[Feedback]] = {}
        self._patterns: Dict[str, List[PerformancePattern]] = {}
        self._evolutions: Dict[str, List[AgentEvolution]] = {}
    
    async def learn_from_feedback(
        self,
        agent_id: str,
        execution_id: str,
        feedback: Feedback
    ) -> Dict[str, Any]:
        """
        Learn from feedback.
        
        Args:
            agent_id: Agent ID
            execution_id: Execution this feedback is for
            feedback: Feedback data
            
        Returns:
            Learning results
        """
        # Store feedback
        if agent_id not in self._feedback:
            self._feedback[agent_id] = []
        self._feedback[agent_id].append(feedback)
        
        results = {
            "agent_id": agent_id,
            "feedback_count": len(self._feedback[agent_id]),
            "adjustments": [],
        }
        
        # Analyze patterns
        patterns = await self._analyze_patterns(agent_id)
        self._patterns[agent_id] = patterns
        
        results["patterns_found"] = len(patterns)
        
        # Check if adjustments needed
        if len(self._feedback[agent_id]) >= 5:
            adjustments = await self._calculate_adjustments(agent_id)
            results["adjustments"] = adjustments
        
        return results
    
    async def _analyze_patterns(self, agent_id: str) -> List[PerformancePattern]:
        """Analyze feedback for patterns."""
        feedback_list = self._feedback.get(agent_id, [])
        patterns = []
        
        if len(feedback_list) < 3:
            return patterns
        
        # Analyze ratings trend
        ratings = [f.rating for f in feedback_list[-10:]]
        avg_rating = sum(ratings) / len(ratings)
        
        if avg_rating < 3.0:
            patterns.append(PerformancePattern(
                pattern_type="low_performance",
                description="Consistently low ratings",
                frequency=len([r for r in ratings if r < 3]),
                impact="negative",
                suggestion="Review agent configuration and prompts",
            ))
        elif avg_rating > 4.5:
            patterns.append(PerformancePattern(
                pattern_type="high_performance",
                description="Consistently high ratings",
                frequency=len([r for r in ratings if r >= 4]),
                impact="positive",
            ))
        
        # Analyze aspect patterns
        aspect_scores = {}
        for fb in feedback_list[-10:]:
            for aspect, score in fb.aspects.items():
                if aspect not in aspect_scores:
                    aspect_scores[aspect] = []
                aspect_scores[aspect].append(score)
        
        for aspect, scores in aspect_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 3.0:
                patterns.append(PerformancePattern(
                    pattern_type=f"weak_{aspect}",
                    description=f"Weakness in {aspect}",
                    frequency=len(scores),
                    impact="negative",
                    suggestion=f"Improve {aspect} through training or configuration",
                ))
        
        return patterns
    
    async def _calculate_adjustments(self, agent_id: str) -> List[Dict[str, Any]]:
        """Calculate needed adjustments."""
        adjustments = []
        patterns = self._patterns.get(agent_id, [])
        
        for pattern in patterns:
            if pattern.impact == "negative":
                if "quality" in pattern.pattern_type:
                    adjustments.append({
                        "type": "temperature",
                        "action": "decrease",
                        "reason": "Improve output quality",
                    })
                elif "speed" in pattern.pattern_type:
                    adjustments.append({
                        "type": "max_tokens",
                        "action": "decrease",
                        "reason": "Improve response speed",
                    })
                elif "low_performance" in pattern.pattern_type:
                    adjustments.append({
                        "type": "prompt",
                        "action": "review",
                        "reason": "Overall performance improvement needed",
                    })
        
        return adjustments
    
    async def adjust_personality(
        self,
        agent: AgentProfile,
        adjustments: Dict[str, float]
    ) -> AgentProfile:
        """
        Adjust agent personality based on feedback.
        
        Args:
            agent: Agent profile
            adjustments: Personality adjustments (-0.2 to 0.2)
            
        Returns:
            Updated agent profile
        """
        current = agent.personality
        
        for trait, delta in adjustments.items():
            if hasattr(current, trait):
                current_value = getattr(current, trait)
                new_value = max(0, min(1, current_value + delta))
                setattr(current, trait, new_value)
        
        agent.personality = current
        agent.updated_at = datetime.now()
        
        # Record evolution
        self._record_evolution(
            agent.id,
            agent.version,
            {"personality": adjustments},
            "Personality adjustment based on feedback"
        )
        
        return agent
    
    async def update_skills(
        self,
        agent: AgentProfile,
        skill_updates: Dict[str, float]
    ) -> AgentProfile:
        """
        Update agent skill levels.
        
        Args:
            agent: Agent profile
            skill_updates: Skill level changes
            
        Returns:
            Updated agent profile
        """
        for skill_name, delta in skill_updates.items():
            found = False
            for skill in agent.skills:
                if skill.name.lower() == skill_name.lower():
                    skill.level = max(0, min(100, skill.level + delta))
                    found = True
                    break
            
            if not found and delta > 0:
                # Add new skill
                agent.skills.append(Skill(
                    name=skill_name,
                    level=min(100, 50 + delta),
                    category="learned",
                ))
        
        agent.updated_at = datetime.now()
        
        # Record evolution
        self._record_evolution(
            agent.id,
            agent.version,
            {"skills": skill_updates},
            "Skill update based on performance"
        )
        
        return agent
    
    async def improve_prompts(
        self,
        agent: AgentProfile,
        feedback_summary: str
    ) -> str:
        """
        Generate improved system prompt.
        
        Args:
            agent: Agent profile
            feedback_summary: Summary of feedback
            
        Returns:
            Improved system prompt
        """
        current_prompt = agent.system_prompt or ""
        
        # Add learning-based improvements
        improvements = []
        
        patterns = self._patterns.get(agent.id, [])
        for pattern in patterns:
            if pattern.suggestion:
                improvements.append(f"- {pattern.suggestion}")
        
        if improvements:
            improvement_section = "\n\nIMPROVEMENT GUIDELINES:\n" + "\n".join(improvements)
            return current_prompt + improvement_section
        
        return current_prompt
    
    async def evolve_agent(
        self,
        agent: AgentProfile,
        target_improvement: str = "balanced"
    ) -> AgentProfile:
        """
        Evolve agent based on accumulated learning.
        
        Args:
            agent: Agent to evolve
            target_improvement: Focus area (balanced, quality, speed, reliability)
            
        Returns:
            Evolved agent profile
        """
        # Analyze performance
        feedback_list = self._feedback.get(agent.id, [])
        patterns = self._patterns.get(agent.id, [])
        
        changes = {}
        
        # Personality evolution
        if target_improvement in ["quality", "balanced"]:
            changes["conscientiousness"] = 0.05
        
        if target_improvement in ["speed", "balanced"]:
            changes["decision_style"] = "decisive"
        
        if target_improvement == "reliability":
            changes["risk_tolerance"] = -0.1
        
        # Apply changes
        if any(k in changes for k in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]):
            personality_changes = {k: v for k, v in changes.items() if k in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
            await self.adjust_personality(agent, personality_changes)
        
        # Update performance score
        if feedback_list:
            avg_rating = sum(f.rating for f in feedback_list[-20:]) / min(20, len(feedback_list))
            agent.performance_score = avg_rating / 5.0
        
        # Increment version
        version_parts = agent.version.split(".")
        try:
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            agent.version = ".".join(version_parts)
        except ValueError:
            agent.version = agent.version + ".1"
        
        agent.updated_at = datetime.now()
        
        # Record evolution
        self._record_evolution(
            agent.id,
            agent.version,
            changes,
            f"Evolution for {target_improvement} improvement"
        )
        
        return agent
    
    def _record_evolution(
        self,
        agent_id: str,
        version: str,
        changes: Dict[str, Any],
        reason: str
    ):
        """Record agent evolution."""
        if agent_id not in self._evolutions:
            self._evolutions[agent_id] = []
        
        self._evolutions[agent_id].append(AgentEvolution(
            agent_id=agent_id,
            version=version,
            changes=changes,
            reason=reason,
        ))
    
    def get_feedback(self, agent_id: str) -> List[Feedback]:
        """Get feedback for agent."""
        return self._feedback.get(agent_id, [])
    
    def get_patterns(self, agent_id: str) -> List[PerformancePattern]:
        """Get patterns for agent."""
        return self._patterns.get(agent_id, [])
    
    def get_evolution_history(self, agent_id: str) -> List[AgentEvolution]:
        """Get evolution history for agent."""
        return self._evolutions.get(agent_id, [])
    
    def get_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get performance summary for agent."""
        feedback_list = self._feedback.get(agent_id, [])
        
        if not feedback_list:
            return {"status": "no_data"}
        
        ratings = [f.rating for f in feedback_list]
        
        return {
            "total_feedback": len(feedback_list),
            "average_rating": sum(ratings) / len(ratings),
            "min_rating": min(ratings),
            "max_rating": max(ratings),
            "patterns": len(self._patterns.get(agent_id, [])),
            "evolutions": len(self._evolutions.get(agent_id, [])),
        }

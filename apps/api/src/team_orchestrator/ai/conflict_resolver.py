"""
Agno Team Orchestrator v2.0 - Conflict Resolution

Resolve conflicts between agents.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from ..types import (
    Conflict, Resolution, ResolutionStrategy, ConflictType,
    AgentProfile, Message
)

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Agent position in conflict."""
    agent_id: str
    stance: str
    arguments: List[str]
    priority: float  # 0-1, how strongly held
    flexibility: float  # 0-1, willingness to compromise


# ============================================================
# RESOLUTION STRATEGIES
# ============================================================

class BaseResolutionStrategy:
    """Base class for resolution strategies."""
    
    async def analyze(self, conflict: Conflict) -> Dict[str, Any]:
        """Analyze the conflict."""
        return {
            "type": conflict.type.value,
            "parties": conflict.parties,
            "complexity": self._assess_complexity(conflict),
        }
    
    async def collect_positions(self, parties: List[str]) -> Dict[str, Position]:
        """Collect positions from all parties."""
        positions = {}
        for party in parties:
            positions[party] = Position(
                agent_id=party,
                stance=f"Position of {party}",
                arguments=[],
                priority=0.5,
                flexibility=0.5,
            )
        return positions
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        """Find resolution."""
        raise NotImplementedError
    
    async def validate(self, resolution: Resolution) -> bool:
        """Validate resolution."""
        return len(resolution.rejected_by) == 0
    
    def _assess_complexity(self, conflict: Conflict) -> str:
        """Assess conflict complexity."""
        if len(conflict.parties) > 3:
            return "high"
        if conflict.type in [ConflictType.DEADLOCK, ConflictType.RESOURCE_CONTENTION]:
            return "high"
        return "medium"


class VotingStrategy(BaseResolutionStrategy):
    """Simple majority voting."""
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        # Count votes for each stance
        stance_votes = {}
        for pos in positions.values():
            stance_votes[pos.stance] = stance_votes.get(pos.stance, 0) + 1
        
        # Find winner
        winner_stance = max(stance_votes.keys(), key=lambda s: stance_votes[s])
        
        accepted = [p.agent_id for p in positions.values() if p.stance == winner_stance]
        rejected = [p.agent_id for p in positions.values() if p.stance != winner_stance]
        
        return Resolution(
            strategy_used=ResolutionStrategy.VOTING,
            outcome={"winning_stance": winner_stance, "votes": stance_votes},
            accepted_by=accepted,
            rejected_by=rejected,
        )


class WeightedVotingStrategy(BaseResolutionStrategy):
    """Weighted voting by expertise."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {}
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        stance_scores = {}
        
        for agent_id, pos in positions.items():
            weight = self.weights.get(agent_id, 1.0)
            stance_scores[pos.stance] = stance_scores.get(pos.stance, 0) + weight
        
        winner_stance = max(stance_scores.keys(), key=lambda s: stance_scores[s])
        
        accepted = [p.agent_id for p in positions.values() if p.stance == winner_stance]
        rejected = [p.agent_id for p in positions.values() if p.stance != winner_stance]
        
        return Resolution(
            strategy_used=ResolutionStrategy.WEIGHTED_VOTING,
            outcome={"winning_stance": winner_stance, "scores": stance_scores},
            accepted_by=accepted,
            rejected_by=rejected,
        )


class ConsensusStrategy(BaseResolutionStrategy):
    """Consensus building."""
    
    def __init__(self, max_rounds: int = 5):
        self.max_rounds = max_rounds
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        # Try to find common ground
        common_points = self._find_common_ground(positions)
        
        # Create compromise
        compromise = self._create_compromise(positions, common_points)
        
        # Check acceptance
        accepted = []
        rejected = []
        
        for agent_id, pos in positions.items():
            if pos.flexibility > 0.5:
                accepted.append(agent_id)
            else:
                rejected.append(agent_id)
        
        return Resolution(
            strategy_used=ResolutionStrategy.CONSENSUS,
            outcome={"compromise": compromise, "common_ground": common_points},
            accepted_by=accepted,
            rejected_by=rejected,
        )
    
    def _find_common_ground(self, positions: Dict[str, Position]) -> List[str]:
        """Find common points between positions."""
        # Simplified - would use semantic similarity
        return ["collaboration", "quality"]
    
    def _create_compromise(
        self,
        positions: Dict[str, Position],
        common_points: List[str]
    ) -> str:
        """Create compromise proposal."""
        return f"Compromise based on: {', '.join(common_points)}"


class SupervisorStrategy(BaseResolutionStrategy):
    """Supervisor makes final decision."""
    
    def __init__(self, supervisor_id: str):
        self.supervisor_id = supervisor_id
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        # Supervisor decides
        supervisor_pos = positions.get(self.supervisor_id)
        
        if supervisor_pos:
            decision = supervisor_pos.stance
        else:
            # Default to first position
            decision = list(positions.values())[0].stance if positions else "No decision"
        
        return Resolution(
            strategy_used=ResolutionStrategy.SUPERVISOR,
            outcome={"decision": decision, "decided_by": self.supervisor_id},
            accepted_by=list(positions.keys()),
            rejected_by=[],
        )


class NegotiationStrategy(BaseResolutionStrategy):
    """Negotiation between parties."""
    
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
    
    async def find_resolution(self, positions: Dict[str, Position]) -> Resolution:
        # Simulate negotiation rounds
        current_positions = positions.copy()
        
        for round_num in range(self.max_rounds):
            # Each flexible agent moves towards center
            for agent_id, pos in current_positions.items():
                if pos.flexibility > 0.5:
                    pos.priority *= 0.8  # Reduce priority each round
        
        # Find middle ground
        middle_ground = "Negotiated agreement"
        
        accepted = [p.agent_id for p in current_positions.values() if p.priority < 0.7]
        rejected = [p.agent_id for p in current_positions.values() if p.priority >= 0.7]
        
        return Resolution(
            strategy_used=ResolutionStrategy.NEGOTIATION,
            outcome={"agreement": middle_ground, "rounds": self.max_rounds},
            accepted_by=accepted,
            rejected_by=rejected,
        )


# ============================================================
# CONFLICT RESOLVER
# ============================================================

class ConflictResolver:
    """
    Resolves conflicts between agents.
    
    Supports multiple strategies:
    - voting: Simple majority
    - weighted_voting: By expertise
    - consensus: Build agreement
    - supervisor: Authority decides
    - negotiation: Back-and-forth
    """
    
    STRATEGIES = {
        ResolutionStrategy.VOTING: VotingStrategy,
        ResolutionStrategy.WEIGHTED_VOTING: WeightedVotingStrategy,
        ResolutionStrategy.CONSENSUS: ConsensusStrategy,
        ResolutionStrategy.SUPERVISOR: SupervisorStrategy,
        ResolutionStrategy.NEGOTIATION: NegotiationStrategy,
    }
    
    def __init__(self):
        self._history: List[Resolution] = []
    
    async def resolve(
        self,
        conflict: Conflict,
        strategy: ResolutionStrategy = ResolutionStrategy.CONSENSUS,
        **kwargs
    ) -> Resolution:
        """
        Resolve a conflict.
        
        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy to use
            **kwargs: Additional arguments for strategy
            
        Returns:
            Resolution with outcome
        """
        logger.info(f"Resolving conflict {conflict.id} using {strategy.value}")
        
        # Get strategy instance
        strategy_class = self.STRATEGIES.get(strategy, ConsensusStrategy)
        resolver = strategy_class(**kwargs)
        
        # Analyze conflict
        analysis = await resolver.analyze(conflict)
        logger.debug(f"Conflict analysis: {analysis}")
        
        # Collect positions
        positions = await resolver.collect_positions(conflict.parties)
        
        # Enrich with conflict data
        for agent_id, data in conflict.positions.items():
            if agent_id in positions:
                positions[agent_id].stance = str(data.get("stance", positions[agent_id].stance))
                positions[agent_id].arguments = data.get("arguments", [])
        
        # Find resolution
        resolution = await resolver.find_resolution(positions)
        resolution.conflict_id = conflict.id
        
        # Validate
        if not await resolver.validate(resolution):
            logger.warning(f"Resolution not fully accepted: {resolution.rejected_by}")
            
            # Try to escalate if too many rejections
            if len(resolution.rejected_by) > len(resolution.accepted_by):
                resolution = await self._escalate(conflict, resolution)
        
        # Store in history
        self._history.append(resolution)
        
        return resolution
    
    async def _escalate(
        self,
        conflict: Conflict,
        failed_resolution: Resolution
    ) -> Resolution:
        """Escalate to higher authority or different strategy."""
        logger.info(f"Escalating conflict {conflict.id}")
        
        # Try supervisor strategy as escalation
        if failed_resolution.strategy_used != ResolutionStrategy.SUPERVISOR:
            # Find a supervisor (first agent as default)
            supervisor_id = conflict.parties[0] if conflict.parties else "system"
            
            resolver = SupervisorStrategy(supervisor_id)
            positions = await resolver.collect_positions(conflict.parties)
            
            resolution = await resolver.find_resolution(positions)
            resolution.conflict_id = conflict.id
            
            return resolution
        
        # If supervisor already failed, mark as human needed
        return Resolution(
            conflict_id=conflict.id,
            strategy_used=ResolutionStrategy.HUMAN,
            outcome={"status": "requires_human_intervention"},
            accepted_by=[],
            rejected_by=conflict.parties,
        )
    
    def get_history(self) -> List[Resolution]:
        """Get resolution history."""
        return self._history
    
    def get_success_rate(self) -> float:
        """Get resolution success rate."""
        if not self._history:
            return 0.0
        
        successful = sum(1 for r in self._history if len(r.rejected_by) == 0)
        return successful / len(self._history)

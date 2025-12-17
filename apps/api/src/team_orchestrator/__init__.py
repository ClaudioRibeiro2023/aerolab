"""
Agno Team Orchestrator v2.0

Advanced multi-agent team orchestration system.

Features:
- 15+ Orchestration Modes
- Agent Profiles with OCEAN Personality
- Task System with Dependencies
- Shared Memory Space
- NL Team Builder
- Auto-Optimization
- Conflict Resolution
- Version Control & A/B Testing
- Simulation & Replay
"""

from .types import (
    # Enums
    OrchestrationMode, TaskType, Priority, MessageType,
    CommunicationStyle, DecisionStyle, AssignmentStrategy,
    AgentStatus, TaskStatus, ExecutionStatus,
    
    # Agent Profile
    PersonalityTraits, Skill, AgentProfile,
    
    # Task
    QualityCriterion, Task, TaskResult,
    
    # Communication
    Message, Conversation, MessageThread,
    
    # Memory
    MemoryScope, MemoryItem,
    
    # Team
    TeamConfiguration, TeamExecution, TeamMetrics,
)

from .engine import TeamOrchestrationEngine, get_orchestration_engine
from .profiles import AgentProfileManager, PERSONA_LIBRARY
from .tasks import TaskManager, TaskScheduler
from .memory import TeamMemorySpace
from .communication import MessageBus, ConversationManager

__version__ = "2.0.0"

__all__ = [
    # Types
    "OrchestrationMode", "TaskType", "Priority", "MessageType",
    "PersonalityTraits", "Skill", "AgentProfile",
    "Task", "TaskResult", "QualityCriterion",
    "Message", "Conversation",
    "TeamConfiguration", "TeamExecution", "TeamMetrics",
    
    # Core
    "TeamOrchestrationEngine", "get_orchestration_engine",
    "AgentProfileManager", "PERSONA_LIBRARY",
    "TaskManager", "TaskScheduler",
    "TeamMemorySpace",
    "MessageBus", "ConversationManager",
]

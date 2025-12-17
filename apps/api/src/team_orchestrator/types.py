"""
Agno Team Orchestrator v2.0 - Type Definitions

Complete type system for advanced multi-agent orchestration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import uuid


# ============================================================
# ENUMS
# ============================================================

class OrchestrationMode(str, Enum):
    """Orchestration modes for team execution."""
    # Basic
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    
    # Hierarchical
    HIERARCHICAL = "hierarchical"
    DELEGATION = "delegation"
    
    # Collaborative
    ROUND_ROBIN = "round_robin"
    DEBATE = "debate"
    CONSENSUS = "consensus"
    VOTING = "voting"
    DEMOCRATIC = "democratic"
    
    # Advanced
    SWARM = "swarm"
    EXPERT_PANEL = "expert_panel"
    AUCTION = "auction"
    NEGOTIATION = "negotiation"
    TOURNAMENT = "tournament"
    
    # Evolutionary
    EVOLUTIONARY = "evolutionary"
    EMERGENT = "emergent"


class TaskType(str, Enum):
    """Types of tasks."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATION = "creation"
    REVIEW = "review"
    DECISION = "decision"
    COMMUNICATION = "communication"
    CODE = "code"
    DATA = "data"
    DESIGN = "design"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MessageType(str, Enum):
    """Types of inter-agent messages."""
    REQUEST = "request"
    RESPONSE = "response"
    INFORM = "inform"
    QUERY = "query"
    DELEGATE = "delegate"
    FEEDBACK = "feedback"
    BROADCAST = "broadcast"
    ACK = "ack"
    ERROR = "error"


class CommunicationStyle(str, Enum):
    """Agent communication styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    CONCISE = "concise"
    DETAILED = "detailed"


class DecisionStyle(str, Enum):
    """Agent decision-making styles."""
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    COLLABORATIVE = "collaborative"
    DECISIVE = "decisive"
    CAUTIOUS = "cautious"


class AssignmentStrategy(str, Enum):
    """Task assignment strategies."""
    BEST_FIT = "best_fit"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    AUCTION = "auction"
    MANUAL = "manual"
    RANDOM = "random"


class AgentStatus(str, Enum):
    """Agent status."""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, Enum):
    """Team execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MemoryScope(str, Enum):
    """Memory scope."""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ConflictType(str, Enum):
    """Types of conflicts."""
    OPINION_DIFFERENCE = "opinion_difference"
    RESOURCE_CONTENTION = "resource_contention"
    PRIORITY_CONFLICT = "priority_conflict"
    DEADLOCK = "deadlock"


class ResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""
    VOTING = "voting"
    WEIGHTED_VOTING = "weighted_voting"
    SUPERVISOR = "supervisor"
    CONSENSUS = "consensus"
    NEGOTIATION = "negotiation"
    ARBITRATION = "arbitration"
    COMPROMISE = "compromise"
    HUMAN = "human"


# ============================================================
# AGENT PROFILE (Sprint 1)
# ============================================================

@dataclass
class PersonalityTraits:
    """OCEAN personality model."""
    openness: float = 0.5          # 0-1: Creativity, curiosity
    conscientiousness: float = 0.5  # 0-1: Organization, dependability
    extraversion: float = 0.5       # 0-1: Sociability, assertiveness
    agreeableness: float = 0.5      # 0-1: Cooperation, trust
    neuroticism: float = 0.5        # 0-1: Emotional stability (inverted)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PersonalityTraits":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Skill:
    """Agent skill."""
    name: str
    level: float  # 0-100
    category: str
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "level": self.level,
            "category": self.category,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Skill":
        return cls(**data)


@dataclass
class AgentProfile:
    """Complete agent profile."""
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    avatar: str = ""
    role: str = ""
    
    # Personality
    personality: PersonalityTraits = field(default_factory=PersonalityTraits)
    
    # Goals
    goal: str = ""
    backstory: str = ""
    motivation: str = ""
    
    # Skills
    skills: List[Skill] = field(default_factory=list)
    expertise_domains: List[str] = field(default_factory=list)
    
    # Behavior
    communication_style: CommunicationStyle = CommunicationStyle.FORMAL
    decision_style: DecisionStyle = DecisionStyle.ANALYTICAL
    risk_tolerance: float = 0.5  # 0-1
    
    # LLM Configuration
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    system_prompt: str = ""
    
    # Tools
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    
    # Limits
    max_tokens_per_turn: int = 4096
    max_iterations: int = 10
    timeout_seconds: int = 300
    
    # Learning
    learning_enabled: bool = True
    performance_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "avatar": self.avatar,
            "role": self.role,
            "personality": self.personality.to_dict(),
            "goal": self.goal,
            "backstory": self.backstory,
            "motivation": self.motivation,
            "skills": [s.to_dict() for s in self.skills],
            "expertise_domains": self.expertise_domains,
            "communication_style": self.communication_style.value,
            "decision_style": self.decision_style.value,
            "risk_tolerance": self.risk_tolerance,
            "model": self.model,
            "temperature": self.temperature,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "mcp_servers": self.mcp_servers,
            "max_tokens_per_turn": self.max_tokens_per_turn,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "learning_enabled": self.learning_enabled,
            "performance_score": self.performance_score,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentProfile":
        data = data.copy()
        if "personality" in data:
            data["personality"] = PersonalityTraits.from_dict(data["personality"])
        if "skills" in data:
            data["skills"] = [Skill.from_dict(s) for s in data["skills"]]
        if "communication_style" in data:
            data["communication_style"] = CommunicationStyle(data["communication_style"])
        if "decision_style" in data:
            data["decision_style"] = DecisionStyle(data["decision_style"])
        # Remove fields not in dataclass
        valid_fields = set(cls.__dataclass_fields__.keys())
        data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**data)
    
    def get_skill_level(self, skill_name: str) -> float:
        """Get skill level by name."""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill.level
        return 0.0
    
    def calculate_compatibility(self, other: "AgentProfile") -> float:
        """Calculate compatibility score with another agent."""
        score = 0.0
        
        # Personality compatibility (complementary traits)
        p1, p2 = self.personality, other.personality
        score += 0.3 * (1 - abs(p1.extraversion - (1 - p2.extraversion)))
        score += 0.2 * (1 - abs(p1.agreeableness - p2.agreeableness))
        score += 0.2 * min(p1.conscientiousness, p2.conscientiousness)
        
        # Skill complementarity
        my_skills = {s.name.lower() for s in self.skills}
        their_skills = {s.name.lower() for s in other.skills}
        overlap = len(my_skills & their_skills)
        unique = len(my_skills | their_skills)
        if unique > 0:
            score += 0.3 * (1 - overlap / unique)  # Less overlap = more complementary
        
        return min(1.0, max(0.0, score))


# ============================================================
# TASK SYSTEM (Sprint 2)
# ============================================================

@dataclass
class QualityCriterion:
    """Quality criterion for task output."""
    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.7
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "threshold": self.threshold,
        }


@dataclass
class Task:
    """Task definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Type
    type: TaskType = TaskType.CUSTOM
    
    # Assignment
    assigned_to: Optional[str] = None
    assignment_strategy: AssignmentStrategy = AssignmentStrategy.BEST_FIT
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    
    # I/O
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    
    # Quality
    quality_criteria: List[QualityCriterion] = field(default_factory=list)
    acceptance_threshold: float = 0.7
    requires_review: bool = False
    reviewer_agent: Optional[str] = None
    
    # Timing
    estimated_duration: Optional[timedelta] = None
    deadline: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    
    # Resources
    max_tokens: int = 4096
    max_cost: float = 1.0
    tools_required: List[str] = field(default_factory=list)
    
    # Status
    status: TaskStatus = TaskStatus.PENDING
    
    # Execution
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "assigned_to": self.assigned_to,
            "assignment_strategy": self.assignment_strategy.value,
            "dependencies": self.dependencies,
            "expected_output": self.expected_output,
            "priority": self.priority.value,
            "status": self.status.value,
            "requires_review": self.requires_review,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        data = data.copy()
        if "type" in data:
            data["type"] = TaskType(data["type"])
        if "assignment_strategy" in data:
            data["assignment_strategy"] = AssignmentStrategy(data["assignment_strategy"])
        if "priority" in data:
            data["priority"] = Priority(data["priority"])
        if "status" in data:
            data["status"] = TaskStatus(data["status"])
        valid_fields = set(cls.__dataclass_fields__.keys())
        data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**data)


@dataclass
class TaskResult:
    """Task execution result."""
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    quality_score: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    agent_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "quality_score": self.quality_score,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "duration_ms": self.duration_ms,
            "agent_id": self.agent_id,
        }


# ============================================================
# COMMUNICATION (Sprint 4)
# ============================================================

@dataclass
class Attachment:
    """Message attachment."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # image, file, code, data
    content: Any = None
    url: Optional[str] = None


@dataclass
class Message:
    """Inter-agent message."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str = ""
    
    # Sender/Recipients
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    
    # Content
    type: MessageType = MessageType.INFORM
    content: str = ""
    structured_data: Optional[Dict] = None
    attachments: List[Attachment] = field(default_factory=list)
    
    # Context
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    
    # Status
    read_by: Set[str] = field(default_factory=set)
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "recipients": self.recipients,
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
        }


@dataclass
class Conversation:
    """Conversation between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    topic: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, resolved, archived


@dataclass
class MessageThread:
    """Message thread."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)


# ============================================================
# MEMORY (Sprint 5)
# ============================================================

@dataclass
class MemoryItem:
    """Memory item."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    scope: MemoryScope = MemoryScope.WORKING
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    relevance_score: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "scope": self.scope.value,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# TEAM CONFIGURATION
# ============================================================

@dataclass
class TeamConfiguration:
    """Team configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Members
    agents: List[AgentProfile] = field(default_factory=list)
    supervisor_id: Optional[str] = None
    
    # Orchestration
    mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL
    
    # Tasks
    tasks: List[Task] = field(default_factory=list)
    
    # Memory
    shared_memory_enabled: bool = True
    memory_config: Dict[str, Any] = field(default_factory=dict)
    
    # Settings
    max_iterations: int = 50
    timeout_seconds: int = 3600
    max_cost: float = 10.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": [a.to_dict() for a in self.agents],
            "supervisor_id": self.supervisor_id,
            "mode": self.mode.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "shared_memory_enabled": self.shared_memory_enabled,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TeamConfiguration":
        data = data.copy()
        if "agents" in data:
            data["agents"] = [AgentProfile.from_dict(a) for a in data["agents"]]
        if "tasks" in data:
            data["tasks"] = [Task.from_dict(t) for t in data["tasks"]]
        if "mode" in data:
            data["mode"] = OrchestrationMode(data["mode"])
        valid_fields = set(cls.__dataclass_fields__.keys())
        data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**data)


@dataclass
class TeamExecution:
    """Team execution state."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    team_id: str = ""
    team_config: Optional[TeamConfiguration] = None
    
    # Status
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_step: int = 0
    
    # Progress
    tasks_completed: int = 0
    tasks_total: int = 0
    
    # Results
    output: Any = None
    error: Optional[str] = None
    
    # Metrics
    total_tokens: int = 0
    total_cost: float = 0.0
    total_messages: int = 0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # History
    messages: List[Message] = field(default_factory=list)
    task_results: List[TaskResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "team_id": self.team_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "tasks_completed": self.tasks_completed,
            "tasks_total": self.tasks_total,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "output": self.output,
            "error": self.error,
        }


@dataclass
class TeamMetrics:
    """Team performance metrics."""
    team_id: str = ""
    
    # Execution
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    # Performance
    avg_execution_time_ms: float = 0.0
    avg_quality_score: float = 0.0
    avg_tokens_per_execution: float = 0.0
    avg_cost_per_execution: float = 0.0
    
    # Agent metrics
    agent_performance: Dict[str, Dict] = field(default_factory=dict)
    
    # Task metrics
    task_success_rate: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "success_rate": self.successful_executions / max(1, self.total_executions),
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "avg_quality_score": self.avg_quality_score,
            "avg_cost_per_execution": self.avg_cost_per_execution,
        }


# ============================================================
# CONFLICT RESOLUTION (Sprint 12)
# ============================================================

@dataclass
class Conflict:
    """Conflict between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ConflictType = ConflictType.OPINION_DIFFERENCE
    parties: List[str] = field(default_factory=list)
    topic: str = ""
    positions: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Resolution:
    """Conflict resolution."""
    conflict_id: str = ""
    strategy_used: ResolutionStrategy = ResolutionStrategy.CONSENSUS
    outcome: Any = None
    accepted_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    resolved_at: datetime = field(default_factory=datetime.now)


# ============================================================
# SLA & BUDGET (Sprint 15)
# ============================================================

@dataclass
class TeamSLA:
    """SLA definition for team."""
    team_id: str = ""
    max_response_time: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    min_quality_score: float = 0.7
    max_cost_per_execution: float = 1.0
    availability_target: float = 0.999
    error_rate_threshold: float = 0.05


@dataclass
class TeamBudget:
    """Budget for team."""
    team_id: str = ""
    daily_limit: float = 10.0
    weekly_limit: float = 50.0
    monthly_limit: float = 200.0
    per_execution_limit: float = 1.0
    alert_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.75, 0.9])
    current_daily_spend: float = 0.0
    current_weekly_spend: float = 0.0
    current_monthly_spend: float = 0.0

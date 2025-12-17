"""
Agno Flow Studio v3.0 - Types

Core type definitions for the visual workflow builder.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union
from enum import Enum
import uuid


# ============================================================
# Enums
# ============================================================

class NodeCategory(str, Enum):
    """Node categories."""
    AGENTS = "agents"
    LOGIC = "logic"
    DATA = "data"
    MEMORY = "memory"
    INTEGRATIONS = "integrations"
    GOVERNANCE = "governance"
    INPUT = "input"
    OUTPUT = "output"


class NodeType(str, Enum):
    """All available node types."""
    # Agents
    AGENT = "agent"
    TEAM = "team"
    SUPERVISOR = "supervisor"
    CRITIC = "critic"
    PLANNER = "planner"
    TOOL_USER = "tool-user"
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    MULTI_MODAL = "multi-modal"
    STREAMING = "streaming"
    MEMORY_AGENT = "memory-agent"
    
    # Logic
    CONDITION = "condition"
    SWITCH = "switch"
    LOOP = "loop"
    PARALLEL = "parallel"
    JOIN = "join"
    GATE = "gate"
    DELAY = "delay"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit-breaker"
    RATE_LIMITER = "rate-limiter"
    
    # Data
    TRANSFORM = "transform"
    MAP = "map"
    FILTER = "filter"
    REDUCE = "reduce"
    SORT = "sort"
    MERGE = "merge"
    SPLIT = "split"
    AGGREGATE = "aggregate"
    CACHE = "cache"
    SCHEMA_VALIDATOR = "schema-validator"
    
    # Memory
    MEMORY_READ = "memory-read"
    MEMORY_WRITE = "memory-write"
    LONG_TERM = "long-term"
    SHORT_TERM = "short-term"
    RAG_SEARCH = "rag-search"
    RAG_INGEST = "rag-ingest"
    VECTOR_STORE = "vector-store"
    RERANKER = "reranker"
    
    # Integrations
    HTTP = "http"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    DATABASE = "database"
    QUEUE = "queue"
    STORAGE = "storage"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    MCP_TOOL = "mcp-tool"
    
    # Governance
    HUMAN_APPROVAL = "human-approval"
    CHECKPOINT = "checkpoint"
    AUDIT_LOG = "audit-log"
    SECRET_FETCH = "secret-fetch"
    COST_GUARD = "cost-guard"
    TIME_GUARD = "time-guard"
    COMPLIANCE_CHECK = "compliance-check"
    PII_DETECTOR = "pii-detector"
    
    # I/O
    INPUT = "input"
    OUTPUT = "output"


class PortType(str, Enum):
    """Port types."""
    INPUT = "input"
    OUTPUT = "output"


class DataType(str, Enum):
    """Supported data types."""
    ANY = "any"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    MESSAGE = "message"
    CONTEXT = "context"
    FILE = "file"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class WorkflowStatus(str, Enum):
    """Workflow states."""
    DRAFT = "draft"
    PUBLISHED = "published"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Execution states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    SKIPPED = "skipped"


# ============================================================
# Data Classes
# ============================================================

@dataclass
class Position:
    """Node position on canvas."""
    x: float = 0
    y: float = 0
    
    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass
class Port:
    """Connection port."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: PortType = PortType.INPUT
    data_type: DataType = DataType.ANY
    required: bool = False
    multiple: bool = False
    default_value: Any = None
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "dataType": self.data_type.value,
            "required": self.required,
            "multiple": self.multiple,
            "defaultValue": self.default_value,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Port":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=PortType(data.get("type", "input")),
            data_type=DataType(data.get("dataType", "any")),
            required=data.get("required", False),
            multiple=data.get("multiple", False),
            default_value=data.get("defaultValue"),
            description=data.get("description", ""),
        )


@dataclass
class Connection:
    """Connection between nodes."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    source_handle: Optional[str] = None
    target: str = ""
    target_handle: Optional[str] = None
    condition: Optional[str] = None
    label: Optional[str] = None
    animated: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "sourceHandle": self.source_handle,
            "target": self.target,
            "targetHandle": self.target_handle,
            "data": {
                "condition": self.condition,
                "label": self.label,
                "animated": self.animated,
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        edge_data = data.get("data", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source=data.get("source", ""),
            source_handle=data.get("sourceHandle"),
            target=data.get("target", ""),
            target_handle=data.get("targetHandle"),
            condition=edge_data.get("condition"),
            label=edge_data.get("label"),
            animated=edge_data.get("animated", True),
        )


@dataclass
class Node:
    """Workflow node."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "custom"
    position: Position = field(default_factory=Position)
    
    # Node data
    label: str = ""
    description: str = ""
    node_type: NodeType = NodeType.AGENT
    category: NodeCategory = NodeCategory.AGENTS
    icon: str = "Bot"
    color: str = "#3B82F6"
    
    # Ports
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    
    # Configuration
    config: dict = field(default_factory=dict)
    
    # Runtime state
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None
    output: Any = None
    execution_time: Optional[float] = None
    token_usage: Optional[int] = None
    cost: Optional[float] = None
    
    # UI state
    collapsed: bool = False
    selected: bool = False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position.to_dict(),
            "data": {
                "label": self.label,
                "description": self.description,
                "nodeType": self.node_type.value,
                "category": self.category.value,
                "icon": self.icon,
                "color": self.color,
                "inputs": [p.to_dict() for p in self.inputs],
                "outputs": [p.to_dict() for p in self.outputs],
                "config": self.config,
                "status": self.status.value if self.status else None,
                "error": self.error,
                "output": self.output,
                "executionTime": self.execution_time,
                "tokenUsage": self.token_usage,
                "cost": self.cost,
                "collapsed": self.collapsed,
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        node_data = data.get("data", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data.get("type", "custom"),
            position=Position.from_dict(data.get("position", {})),
            label=node_data.get("label", ""),
            description=node_data.get("description", ""),
            node_type=NodeType(node_data.get("nodeType", "agent")),
            category=NodeCategory(node_data.get("category", "agents")),
            icon=node_data.get("icon", "Bot"),
            color=node_data.get("color", "#3B82F6"),
            inputs=[Port.from_dict(p) for p in node_data.get("inputs", [])],
            outputs=[Port.from_dict(p) for p in node_data.get("outputs", [])],
            config=node_data.get("config", {}),
            status=ExecutionStatus(node_data.get("status", "pending")) if node_data.get("status") else ExecutionStatus.PENDING,
            error=node_data.get("error"),
            collapsed=node_data.get("collapsed", False),
        )


@dataclass
class WorkflowSettings:
    """Workflow settings."""
    timeout: int = 300000  # 5 minutes
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    error_handling: str = "stop"  # stop, continue, fallback
    logging: str = "full"  # none, minimal, full
    cost_limit: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "timeout": self.timeout,
            "retryPolicy": {
                "maxRetries": self.max_retries,
                "backoffMultiplier": self.backoff_multiplier,
            },
            "errorHandling": self.error_handling,
            "logging": self.logging,
            "costLimit": self.cost_limit,
        }


@dataclass
class Workflow:
    """Complete workflow definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    
    # Graph
    nodes: list[Node] = field(default_factory=list)
    edges: list[Connection] = field(default_factory=list)
    
    # Viewport
    viewport_x: float = 0
    viewport_y: float = 0
    viewport_zoom: float = 1
    
    # Configuration
    variables: dict = field(default_factory=dict)
    settings: WorkflowSettings = field(default_factory=WorkflowSettings)
    
    # Metadata
    tags: list[str] = field(default_factory=list)
    folder: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_input_nodes(self) -> list[Node]:
        """Get all input nodes."""
        return [n for n in self.nodes if n.node_type == NodeType.INPUT]
    
    def get_output_nodes(self) -> list[Node]:
        """Get all output nodes."""
        return [n for n in self.nodes if n.node_type == NodeType.OUTPUT]
    
    def get_incoming_edges(self, node_id: str) -> list[Connection]:
        """Get edges targeting a node."""
        return [e for e in self.edges if e.target == node_id]
    
    def get_outgoing_edges(self, node_id: str) -> list[Connection]:
        """Get edges from a node."""
        return [e for e in self.edges if e.source == node_id]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "viewport": {
                "x": self.viewport_x,
                "y": self.viewport_y,
                "zoom": self.viewport_zoom,
            },
            "variables": self.variables,
            "settings": self.settings.to_dict(),
            "tags": self.tags,
            "folder": self.folder,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "createdBy": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        viewport = data.get("viewport", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            status=WorkflowStatus(data.get("status", "draft")),
            nodes=[Node.from_dict(n) for n in data.get("nodes", [])],
            edges=[Connection.from_dict(e) for e in data.get("edges", [])],
            viewport_x=viewport.get("x", 0),
            viewport_y=viewport.get("y", 0),
            viewport_zoom=viewport.get("zoom", 1),
            variables=data.get("variables", {}),
            tags=data.get("tags", []),
            folder=data.get("folder"),
            created_by=data.get("createdBy"),
        )


@dataclass
class ExecutionStep:
    """Single step in workflow execution."""
    node_id: str
    node_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    input_data: Any = None
    output_data: Any = None
    error: Optional[str] = None
    token_usage: Optional[int] = None
    cost: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "nodeId": self.node_id,
            "nodeName": self.node_name,
            "status": self.status.value,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "input": self.input_data,
            "output": self.output_data,
            "error": self.error,
            "tokenUsage": self.token_usage,
            "cost": self.cost,
        }


@dataclass
class Execution:
    """Workflow execution instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    triggered_by: str = "manual"  # manual, schedule, webhook, api
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Data
    input_data: dict = field(default_factory=dict)
    output_data: Optional[dict] = None
    
    # Steps
    steps: list[ExecutionStep] = field(default_factory=list)
    current_step: Optional[str] = None
    
    # Metrics
    total_tokens: int = 0
    total_cost: float = 0.0
    
    # Error
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflowId": self.workflow_id,
            "status": self.status.value,
            "triggeredBy": self.triggered_by,
            "startedAt": self.started_at.isoformat(),
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "input": self.input_data,
            "output": self.output_data,
            "steps": [s.to_dict() for s in self.steps],
            "currentStep": self.current_step,
            "totalTokens": self.total_tokens,
            "totalCost": self.total_cost,
            "error": self.error,
        }

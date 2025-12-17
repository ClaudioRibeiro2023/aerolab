"""
Agent Studio - Tipos e Estruturas de Dados

Define estruturas para o editor visual de workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union
from enum import Enum
import uuid


class NodeType(str, Enum):
    """Tipos de nós disponíveis."""
    # Agents
    AGENT = "agent"
    TEAM = "team"
    
    # Tools
    TOOL = "tool"
    MCP_TOOL = "mcp_tool"
    
    # Logic
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SWITCH = "switch"
    
    # Memory
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    
    # RAG
    RAG_SEARCH = "rag_search"
    RAG_INGEST = "rag_ingest"
    
    # I/O
    INPUT = "input"
    OUTPUT = "output"
    
    # Utilities
    TRANSFORM = "transform"
    DELAY = "delay"
    HTTP = "http"
    CODE = "code"


class PortType(str, Enum):
    """Tipos de porta."""
    INPUT = "input"
    OUTPUT = "output"


class DataType(str, Enum):
    """Tipos de dados suportados."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"
    MESSAGE = "message"
    CONTEXT = "context"


class WorkflowState(str, Enum):
    """Estados do workflow."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Position:
    """Posição de um nó no canvas."""
    x: float = 0
    y: float = 0
    
    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass
class Port:
    """
    Porta de conexão de um nó.
    
    Cada nó tem portas de entrada e saída para conectar a outros nós.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: PortType = PortType.INPUT
    data_type: DataType = DataType.ANY
    
    # Configuração
    required: bool = False
    multiple: bool = False  # Permite múltiplas conexões
    
    # Valor default
    default_value: Any = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "data_type": self.data_type.value,
            "required": self.required,
            "multiple": self.multiple,
            "default_value": self.default_value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Port":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=PortType(data.get("type", "input")),
            data_type=DataType(data.get("data_type", "any")),
            required=data.get("required", False),
            multiple=data.get("multiple", False),
            default_value=data.get("default_value")
        )


@dataclass
class Connection:
    """
    Conexão entre dois nós.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Source
    source_node_id: str = ""
    source_port_id: str = ""
    
    # Target
    target_node_id: str = ""
    target_port_id: str = ""
    
    # Condição opcional
    condition: Optional[str] = None
    
    # Label
    label: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "source_port_id": self.source_port_id,
            "target_node_id": self.target_node_id,
            "target_port_id": self.target_port_id,
            "condition": self.condition,
            "label": self.label
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_node_id=data.get("source_node_id", ""),
            source_port_id=data.get("source_port_id", ""),
            target_node_id=data.get("target_node_id", ""),
            target_port_id=data.get("target_port_id", ""),
            condition=data.get("condition"),
            label=data.get("label")
        )


@dataclass
class Node:
    """
    Nó base do workflow.
    
    Representa um componente do workflow (agente, tool, lógica, etc).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType = NodeType.AGENT
    name: str = ""
    description: str = ""
    
    # Visual
    position: Position = field(default_factory=Position)
    collapsed: bool = False
    color: Optional[str] = None
    icon: Optional[str] = None
    
    # Portas
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    
    # Configuração específica do tipo
    config: dict = field(default_factory=dict)
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def get_input_port(self, name: str) -> Optional[Port]:
        """Obtém porta de entrada pelo nome."""
        for port in self.inputs:
            if port.name == name:
                return port
        return None
    
    def get_output_port(self, name: str) -> Optional[Port]:
        """Obtém porta de saída pelo nome."""
        for port in self.outputs:
            if port.name == name:
                return port
        return None
    
    def add_input(
        self,
        name: str,
        data_type: DataType = DataType.ANY,
        required: bool = False
    ) -> Port:
        """Adiciona porta de entrada."""
        port = Port(
            name=name,
            type=PortType.INPUT,
            data_type=data_type,
            required=required
        )
        self.inputs.append(port)
        return port
    
    def add_output(
        self,
        name: str,
        data_type: DataType = DataType.ANY
    ) -> Port:
        """Adiciona porta de saída."""
        port = Port(
            name=name,
            type=PortType.OUTPUT,
            data_type=data_type
        )
        self.outputs.append(port)
        return port
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "position": self.position.to_dict(),
            "collapsed": self.collapsed,
            "color": self.color,
            "icon": self.icon,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "config": self.config,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=NodeType(data.get("type", "agent")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            position=Position.from_dict(data.get("position", {})),
            collapsed=data.get("collapsed", False),
            color=data.get("color"),
            icon=data.get("icon"),
            inputs=[Port.from_dict(p) for p in data.get("inputs", [])],
            outputs=[Port.from_dict(p) for p in data.get("outputs", [])],
            config=data.get("config", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class Workflow:
    """
    Representa um workflow completo.
    
    Um workflow é composto por nós e conexões que definem
    o fluxo de execução.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Componentes
    nodes: list[Node] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    
    # Estado
    state: WorkflowState = WorkflowState.DRAFT
    
    # Configuração global
    config: dict = field(default_factory=dict)
    
    # Variáveis
    variables: dict = field(default_factory=dict)
    
    # Versionamento
    version: str = "1.0.0"
    
    # Metadados
    project_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Tags
    tags: list[str] = field(default_factory=list)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Obtém nó pelo ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def add_node(self, node: Node) -> None:
        """Adiciona um nó."""
        self.nodes.append(node)
        self.updated_at = datetime.now()
    
    def remove_node(self, node_id: str) -> bool:
        """Remove um nó e suas conexões."""
        # Remover nó
        node_removed = False
        for i, node in enumerate(self.nodes):
            if node.id == node_id:
                self.nodes.pop(i)
                node_removed = True
                break
        
        if not node_removed:
            return False
        
        # Remover conexões relacionadas
        self.connections = [
            c for c in self.connections
            if c.source_node_id != node_id and c.target_node_id != node_id
        ]
        
        self.updated_at = datetime.now()
        return True
    
    def add_connection(self, connection: Connection) -> None:
        """Adiciona uma conexão."""
        self.connections.append(connection)
        self.updated_at = datetime.now()
    
    def remove_connection(self, connection_id: str) -> bool:
        """Remove uma conexão."""
        for i, conn in enumerate(self.connections):
            if conn.id == connection_id:
                self.connections.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_node_connections(self, node_id: str) -> list[Connection]:
        """Obtém todas as conexões de um nó."""
        return [
            c for c in self.connections
            if c.source_node_id == node_id or c.target_node_id == node_id
        ]
    
    def get_incoming_connections(self, node_id: str) -> list[Connection]:
        """Obtém conexões entrando em um nó."""
        return [c for c in self.connections if c.target_node_id == node_id]
    
    def get_outgoing_connections(self, node_id: str) -> list[Connection]:
        """Obtém conexões saindo de um nó."""
        return [c for c in self.connections if c.source_node_id == node_id]
    
    def get_input_nodes(self) -> list[Node]:
        """Obtém nós de entrada."""
        return [n for n in self.nodes if n.type == NodeType.INPUT]
    
    def get_output_nodes(self) -> list[Node]:
        """Obtém nós de saída."""
        return [n for n in self.nodes if n.type == NodeType.OUTPUT]
    
    def validate(self) -> list[str]:
        """
        Valida o workflow.
        
        Returns:
            Lista de erros (vazia se válido)
        """
        errors = []
        
        # Verificar se tem nó de entrada
        if not self.get_input_nodes():
            errors.append("Workflow must have at least one Input node")
        
        # Verificar se tem nó de saída
        if not self.get_output_nodes():
            errors.append("Workflow must have at least one Output node")
        
        # Verificar conexões órfãs
        node_ids = {n.id for n in self.nodes}
        for conn in self.connections:
            if conn.source_node_id not in node_ids:
                errors.append(f"Connection {conn.id} references unknown source node")
            if conn.target_node_id not in node_ids:
                errors.append(f"Connection {conn.id} references unknown target node")
        
        # Verificar portas obrigatórias
        for node in self.nodes:
            incoming = self.get_incoming_connections(node.id)
            connected_ports = {c.target_port_id for c in incoming}
            
            for port in node.inputs:
                if port.required and port.id not in connected_ports:
                    errors.append(f"Node {node.name}: required input '{port.name}' not connected")
        
        return errors
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": [c.to_dict() for c in self.connections],
            "state": self.state.value,
            "config": self.config,
            "variables": self.variables,
            "version": self.version,
            "project_id": self.project_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            nodes=[Node.from_dict(n) for n in data.get("nodes", [])],
            connections=[Connection.from_dict(c) for c in data.get("connections", [])],
            state=WorkflowState(data.get("state", "draft")),
            config=data.get("config", {}),
            variables=data.get("variables", {}),
            version=data.get("version", "1.0.0"),
            project_id=data.get("project_id"),
            created_by=data.get("created_by"),
            tags=data.get("tags", [])
        )


@dataclass
class ExecutionContext:
    """Contexto de execução de um workflow."""
    workflow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Dados
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)
    
    # Estado dos nós
    node_states: dict = field(default_factory=dict)
    node_outputs: dict = field(default_factory=dict)
    
    # Progresso
    current_node_id: Optional[str] = None
    completed_nodes: set = field(default_factory=set)
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Erros
    errors: list[str] = field(default_factory=list)
    
    def set_node_output(self, node_id: str, output: Any) -> None:
        """Define output de um nó."""
        self.node_outputs[node_id] = output
        self.completed_nodes.add(node_id)
    
    def get_node_output(self, node_id: str) -> Any:
        """Obtém output de um nó."""
        return self.node_outputs.get(node_id)
    
    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "variables": self.variables,
            "completed_nodes": list(self.completed_nodes),
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

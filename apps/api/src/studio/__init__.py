"""
Agent Studio - Editor Visual de Agentes

Sistema de criação visual de agentes e workflows.
Permite construir agentes via drag-and-drop sem código.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                     Agent Studio                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Canvas      │  │ Node        │  │ Workflow    │         │
│  │ Editor      │  │ Library     │  │ Engine      │         │
│  │             │  │             │  │             │         │
│  │ - Drag/Drop│  │ - Agents    │  │ - Validate  │         │
│  │ - Connect   │  │ - Tools     │  │ - Execute   │         │
│  │ - Arrange   │  │ - Logic     │  │ - Monitor   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Export   │                            │
│                    │  - JSON   │                            │
│                    │  - Python │                            │
│                    │  - API    │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘

Componentes:
- Canvas: Editor visual com nós e conexões
- Nodes: Agentes, Tools, Logic, Memory
- Workflow: Engine de execução
- Templates: Workflows pré-construídos

Uso:
```python
from studio import WorkflowBuilder, Node, Connection

# Criar workflow
builder = WorkflowBuilder("customer_support")

# Adicionar nós
classifier = builder.add_node(AgentNode("classifier"))
responder = builder.add_node(AgentNode("responder"))

# Conectar
builder.connect(classifier, responder, condition="category == 'billing'")

# Exportar
workflow = builder.build()
result = await workflow.execute("Help with my bill")
```
"""

from .types import (
    Node,
    NodeType,
    Connection,
    Port,
    Position,
    Workflow,
    WorkflowState
)
from .nodes import (
    AgentNode,
    ToolNode,
    LogicNode,
    MemoryNode,
    InputNode,
    OutputNode
)
from .builder import WorkflowBuilder
from .engine import WorkflowEngine, get_workflow_engine
from .templates import TemplateLibrary, get_template_library

__all__ = [
    # Types
    "Node",
    "NodeType",
    "Connection",
    "Port",
    "Position",
    "Workflow",
    "WorkflowState",
    # Nodes
    "AgentNode",
    "ToolNode",
    "LogicNode",
    "MemoryNode",
    "InputNode",
    "OutputNode",
    # Builder
    "WorkflowBuilder",
    # Engine
    "WorkflowEngine",
    "get_workflow_engine",
    # Templates
    "TemplateLibrary",
    "get_template_library"
]

__version__ = "2.0.0"

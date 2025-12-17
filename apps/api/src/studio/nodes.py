"""
Agent Studio - Nós Especializados

Define os tipos de nós disponíveis no editor visual.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import uuid

from .types import Node, NodeType, Port, PortType, DataType, Position


class BaseNode(Node):
    """Base class para nós especializados."""
    
    def __init__(self, name: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self._setup_ports()
    
    def _setup_ports(self) -> None:
        """Configura portas padrão - override nas subclasses."""
        pass


class InputNode(BaseNode):
    """
    Nó de entrada do workflow.
    
    Recebe dados de entrada e os passa para o workflow.
    """
    
    def __init__(self, name: str = "Input", **kwargs):
        kwargs["type"] = NodeType.INPUT
        kwargs.setdefault("icon", "📥")
        kwargs.setdefault("color", "#4CAF50")
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_output("data", DataType.ANY)
        self.add_output("message", DataType.MESSAGE)


class OutputNode(BaseNode):
    """
    Nó de saída do workflow.
    
    Coleta o resultado final do workflow.
    """
    
    def __init__(self, name: str = "Output", **kwargs):
        kwargs["type"] = NodeType.OUTPUT
        kwargs.setdefault("icon", "📤")
        kwargs.setdefault("color", "#F44336")
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("data", DataType.ANY, required=True)


class AgentNode(BaseNode):
    """
    Nó de agente.
    
    Executa um agente LLM com configuração específica.
    """
    
    def __init__(
        self,
        name: str = "Agent",
        model: str = "gpt-4o",
        instructions: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.AGENT
        kwargs.setdefault("icon", "🤖")
        kwargs.setdefault("color", "#2196F3")
        
        # Config do agente
        kwargs.setdefault("config", {})
        kwargs["config"]["model"] = model
        kwargs["config"]["instructions"] = instructions
        kwargs["config"]["temperature"] = kwargs.get("temperature", 0.7)
        kwargs["config"]["max_tokens"] = kwargs.get("max_tokens", 4096)
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        # Inputs
        self.add_input("message", DataType.MESSAGE, required=True)
        self.add_input("context", DataType.CONTEXT)
        self.add_input("tools", DataType.ARRAY)
        
        # Outputs
        self.add_output("response", DataType.STRING)
        self.add_output("tool_calls", DataType.ARRAY)
        self.add_output("usage", DataType.OBJECT)


class TeamNode(BaseNode):
    """
    Nó de equipe multi-agente.
    
    Orquestra múltiplos agentes.
    """
    
    def __init__(
        self,
        name: str = "Team",
        workflow: str = "sequential",
        **kwargs
    ):
        kwargs["type"] = NodeType.TEAM
        kwargs.setdefault("icon", "👥")
        kwargs.setdefault("color", "#9C27B0")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["workflow"] = workflow
        kwargs["config"]["agents"] = kwargs.get("agents", [])
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("task", DataType.STRING, required=True)
        self.add_input("context", DataType.CONTEXT)
        
        self.add_output("result", DataType.STRING)
        self.add_output("agent_outputs", DataType.ARRAY)


class ToolNode(BaseNode):
    """
    Nó de ferramenta.
    
    Executa uma ferramenta específica.
    """
    
    def __init__(
        self,
        name: str = "Tool",
        tool_name: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.TOOL
        kwargs.setdefault("icon", "🔧")
        kwargs.setdefault("color", "#FF9800")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["tool_name"] = tool_name
        kwargs["config"]["parameters"] = kwargs.get("parameters", {})
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("input", DataType.ANY, required=True)
        self.add_input("parameters", DataType.OBJECT)
        
        self.add_output("result", DataType.ANY)
        self.add_output("error", DataType.STRING)


class MCPToolNode(BaseNode):
    """
    Nó de ferramenta MCP.
    
    Executa uma tool de um servidor MCP.
    """
    
    def __init__(
        self,
        name: str = "MCP Tool",
        server_id: str = "",
        tool_name: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.MCP_TOOL
        kwargs.setdefault("icon", "🔌")
        kwargs.setdefault("color", "#607D8B")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["server_id"] = server_id
        kwargs["config"]["tool_name"] = tool_name
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("arguments", DataType.OBJECT, required=True)
        
        self.add_output("result", DataType.ANY)


class LogicNode(BaseNode):
    """Base para nós de lógica."""
    pass


class ConditionNode(LogicNode):
    """
    Nó de condição.
    
    Roteia baseado em condição.
    """
    
    def __init__(
        self,
        name: str = "Condition",
        condition: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.CONDITION
        kwargs.setdefault("icon", "❓")
        kwargs.setdefault("color", "#795548")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["condition"] = condition
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("value", DataType.ANY, required=True)
        
        self.add_output("true", DataType.ANY)
        self.add_output("false", DataType.ANY)


class SwitchNode(LogicNode):
    """
    Nó switch/case.
    
    Roteia para múltiplos caminhos baseado em valor.
    """
    
    def __init__(
        self,
        name: str = "Switch",
        cases: list[str] = None,
        **kwargs
    ):
        kwargs["type"] = NodeType.SWITCH
        kwargs.setdefault("icon", "🔀")
        kwargs.setdefault("color", "#795548")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["cases"] = cases or []
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("value", DataType.ANY, required=True)
        
        # Porta para cada case + default
        for case in self.config.get("cases", []):
            self.add_output(f"case_{case}", DataType.ANY)
        self.add_output("default", DataType.ANY)


class LoopNode(LogicNode):
    """
    Nó de loop.
    
    Executa nós filhos em loop.
    """
    
    def __init__(
        self,
        name: str = "Loop",
        max_iterations: int = 10,
        **kwargs
    ):
        kwargs["type"] = NodeType.LOOP
        kwargs.setdefault("icon", "🔄")
        kwargs.setdefault("color", "#3F51B5")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["max_iterations"] = max_iterations
        kwargs["config"]["condition"] = kwargs.get("condition", "")
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("items", DataType.ARRAY, required=True)
        
        self.add_output("item", DataType.ANY)  # Cada item
        self.add_output("index", DataType.NUMBER)
        self.add_output("complete", DataType.ARRAY)  # Todos os resultados


class ParallelNode(LogicNode):
    """
    Nó paralelo.
    
    Executa múltiplos caminhos em paralelo.
    """
    
    def __init__(
        self,
        name: str = "Parallel",
        branches: int = 2,
        **kwargs
    ):
        kwargs["type"] = NodeType.PARALLEL
        kwargs.setdefault("icon", "⚡")
        kwargs.setdefault("color", "#E91E63")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["branches"] = branches
        kwargs["config"]["wait_all"] = kwargs.get("wait_all", True)
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("input", DataType.ANY, required=True)
        
        # Criar porta para cada branch
        for i in range(self.config.get("branches", 2)):
            self.add_output(f"branch_{i+1}", DataType.ANY)
        
        self.add_output("results", DataType.ARRAY)


class MemoryNode(BaseNode):
    """Base para nós de memória."""
    pass


class MemoryReadNode(MemoryNode):
    """
    Nó de leitura de memória.
    
    Busca memórias relevantes.
    """
    
    def __init__(self, name: str = "Memory Read", **kwargs):
        kwargs["type"] = NodeType.MEMORY_READ
        kwargs.setdefault("icon", "📖")
        kwargs.setdefault("color", "#00BCD4")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["memory_type"] = kwargs.get("memory_type", "long_term")
        kwargs["config"]["limit"] = kwargs.get("limit", 10)
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("query", DataType.STRING, required=True)
        self.add_input("session_id", DataType.STRING)
        
        self.add_output("memories", DataType.ARRAY)
        self.add_output("context", DataType.CONTEXT)


class MemoryWriteNode(MemoryNode):
    """
    Nó de escrita de memória.
    
    Armazena informações na memória.
    """
    
    def __init__(self, name: str = "Memory Write", **kwargs):
        kwargs["type"] = NodeType.MEMORY_WRITE
        kwargs.setdefault("icon", "📝")
        kwargs.setdefault("color", "#00BCD4")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["memory_type"] = kwargs.get("memory_type", "long_term")
        kwargs["config"]["importance"] = kwargs.get("importance", 0.5)
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("content", DataType.STRING, required=True)
        self.add_input("tags", DataType.ARRAY)
        self.add_input("session_id", DataType.STRING)
        
        self.add_output("memory_id", DataType.STRING)


class RAGSearchNode(BaseNode):
    """
    Nó de busca RAG.
    
    Busca documentos no sistema RAG.
    """
    
    def __init__(self, name: str = "RAG Search", **kwargs):
        kwargs["type"] = NodeType.RAG_SEARCH
        kwargs.setdefault("icon", "🔍")
        kwargs.setdefault("color", "#009688")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["limit"] = kwargs.get("limit", 10)
        kwargs["config"]["rerank"] = kwargs.get("rerank", True)
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("query", DataType.STRING, required=True)
        self.add_input("filters", DataType.OBJECT)
        
        self.add_output("documents", DataType.ARRAY)
        self.add_output("context", DataType.STRING)


class TransformNode(BaseNode):
    """
    Nó de transformação.
    
    Transforma dados usando código Python ou template.
    """
    
    def __init__(
        self,
        name: str = "Transform",
        code: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.TRANSFORM
        kwargs.setdefault("icon", "⚙️")
        kwargs.setdefault("color", "#FF5722")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["code"] = code
        kwargs["config"]["language"] = kwargs.get("language", "python")
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("data", DataType.ANY, required=True)
        
        self.add_output("result", DataType.ANY)


class HTTPNode(BaseNode):
    """
    Nó de requisição HTTP.
    
    Faz requisições HTTP externas.
    """
    
    def __init__(
        self,
        name: str = "HTTP Request",
        method: str = "GET",
        url: str = "",
        **kwargs
    ):
        kwargs["type"] = NodeType.HTTP
        kwargs.setdefault("icon", "🌐")
        kwargs.setdefault("color", "#673AB7")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["method"] = method
        kwargs["config"]["url"] = url
        kwargs["config"]["headers"] = kwargs.get("headers", {})
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("body", DataType.ANY)
        self.add_input("query_params", DataType.OBJECT)
        
        self.add_output("response", DataType.ANY)
        self.add_output("status", DataType.NUMBER)
        self.add_output("headers", DataType.OBJECT)


class DelayNode(BaseNode):
    """
    Nó de delay.
    
    Adiciona um atraso na execução.
    """
    
    def __init__(
        self,
        name: str = "Delay",
        seconds: float = 1.0,
        **kwargs
    ):
        kwargs["type"] = NodeType.DELAY
        kwargs.setdefault("icon", "⏱️")
        kwargs.setdefault("color", "#9E9E9E")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["seconds"] = seconds
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("input", DataType.ANY, required=True)
        
        self.add_output("output", DataType.ANY)


class CodeNode(BaseNode):
    """
    Nó de código customizado.
    
    Executa código Python customizado.
    """
    
    def __init__(
        self,
        name: str = "Code",
        code: str = "def execute(inputs):\n    return inputs",
        **kwargs
    ):
        kwargs["type"] = NodeType.CODE
        kwargs.setdefault("icon", "💻")
        kwargs.setdefault("color", "#212121")
        
        kwargs.setdefault("config", {})
        kwargs["config"]["code"] = code
        
        super().__init__(name=name, **kwargs)
    
    def _setup_ports(self) -> None:
        self.add_input("inputs", DataType.OBJECT, required=True)
        
        self.add_output("result", DataType.ANY)
        self.add_output("error", DataType.STRING)


# Factory function
def create_node(node_type: str, **kwargs) -> Node:
    """
    Cria um nó pelo tipo.
    
    Args:
        node_type: Tipo do nó
        **kwargs: Argumentos do nó
        
    Returns:
        Instância do nó
    """
    NODE_CLASSES = {
        "input": InputNode,
        "output": OutputNode,
        "agent": AgentNode,
        "team": TeamNode,
        "tool": ToolNode,
        "mcp_tool": MCPToolNode,
        "condition": ConditionNode,
        "switch": SwitchNode,
        "loop": LoopNode,
        "parallel": ParallelNode,
        "memory_read": MemoryReadNode,
        "memory_write": MemoryWriteNode,
        "rag_search": RAGSearchNode,
        "transform": TransformNode,
        "http": HTTPNode,
        "delay": DelayNode,
        "code": CodeNode
    }
    
    node_class = NODE_CLASSES.get(node_type, Node)
    return node_class(**kwargs)

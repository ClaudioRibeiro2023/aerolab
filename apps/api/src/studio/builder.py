"""
Agent Studio - Workflow Builder

API fluente para construção de workflows.
"""

from typing import Optional, Union
import uuid

from .types import (
    Workflow, Node, Connection, Position, WorkflowState,
    NodeType, Port, DataType
)
from .nodes import (
    create_node, InputNode, OutputNode, AgentNode, ToolNode,
    ConditionNode, LoopNode, ParallelNode
)


class WorkflowBuilder:
    """
    Builder para construção de workflows.
    
    Fornece API fluente para criar workflows programaticamente.
    
    Uso:
    ```python
    builder = WorkflowBuilder("customer_support")
    
    # Adicionar nós
    input_node = builder.add_input("user_message")
    classifier = builder.add_agent("classifier", model="gpt-4o")
    responder = builder.add_agent("responder")
    output_node = builder.add_output("response")
    
    # Conectar
    builder.connect(input_node, classifier)
    builder.connect(classifier, responder)
    builder.connect(responder, output_node)
    
    # Build
    workflow = builder.build()
    ```
    """
    
    def __init__(self, name: str, description: str = ""):
        self._workflow = Workflow(name=name, description=description)
        self._node_counter = 0
        self._auto_layout = True
        self._row_height = 150
        self._col_width = 250
    
    @property
    def workflow(self) -> Workflow:
        """Acesso ao workflow em construção."""
        return self._workflow
    
    def set_project(self, project_id: int) -> "WorkflowBuilder":
        """Define projeto."""
        self._workflow.project_id = project_id
        return self
    
    def set_variables(self, variables: dict) -> "WorkflowBuilder":
        """Define variáveis globais."""
        self._workflow.variables = variables
        return self
    
    def add_variable(self, name: str, value: any) -> "WorkflowBuilder":
        """Adiciona uma variável."""
        self._workflow.variables[name] = value
        return self
    
    def add_tag(self, tag: str) -> "WorkflowBuilder":
        """Adiciona uma tag."""
        if tag not in self._workflow.tags:
            self._workflow.tags.append(tag)
        return self
    
    # ==================== Adicionar Nós ====================
    
    def _next_position(self) -> Position:
        """Calcula próxima posição para auto-layout."""
        self._node_counter += 1
        row = (self._node_counter - 1) // 4
        col = (self._node_counter - 1) % 4
        return Position(x=col * self._col_width + 50, y=row * self._row_height + 50)
    
    def add_node(self, node: Node) -> Node:
        """
        Adiciona um nó ao workflow.
        
        Args:
            node: Nó a adicionar
            
        Returns:
            O nó adicionado
        """
        if self._auto_layout and node.position.x == 0 and node.position.y == 0:
            node.position = self._next_position()
        
        self._workflow.add_node(node)
        return node
    
    def add_input(self, name: str = "Input", **kwargs) -> Node:
        """Adiciona nó de entrada."""
        node = InputNode(name=name, **kwargs)
        return self.add_node(node)
    
    def add_output(self, name: str = "Output", **kwargs) -> Node:
        """Adiciona nó de saída."""
        node = OutputNode(name=name, **kwargs)
        return self.add_node(node)
    
    def add_agent(
        self,
        name: str = "Agent",
        model: str = "gpt-4o",
        instructions: str = "",
        **kwargs
    ) -> Node:
        """
        Adiciona nó de agente.
        
        Args:
            name: Nome do agente
            model: Modelo LLM
            instructions: Instruções do agente
            
        Returns:
            Nó criado
        """
        node = AgentNode(
            name=name,
            model=model,
            instructions=instructions,
            **kwargs
        )
        return self.add_node(node)
    
    def add_tool(
        self,
        name: str = "Tool",
        tool_name: str = "",
        **kwargs
    ) -> Node:
        """Adiciona nó de ferramenta."""
        node = ToolNode(name=name, tool_name=tool_name, **kwargs)
        return self.add_node(node)
    
    def add_condition(
        self,
        name: str = "Condition",
        condition: str = "",
        **kwargs
    ) -> Node:
        """Adiciona nó de condição."""
        node = ConditionNode(name=name, condition=condition, **kwargs)
        return self.add_node(node)
    
    def add_loop(
        self,
        name: str = "Loop",
        max_iterations: int = 10,
        **kwargs
    ) -> Node:
        """Adiciona nó de loop."""
        node = LoopNode(name=name, max_iterations=max_iterations, **kwargs)
        return self.add_node(node)
    
    def add_parallel(
        self,
        name: str = "Parallel",
        branches: int = 2,
        **kwargs
    ) -> Node:
        """Adiciona nó paralelo."""
        node = ParallelNode(name=name, branches=branches, **kwargs)
        return self.add_node(node)
    
    def add_custom(self, node_type: str, **kwargs) -> Node:
        """Adiciona nó customizado pelo tipo."""
        node = create_node(node_type, **kwargs)
        return self.add_node(node)
    
    # ==================== Conectar Nós ====================
    
    def connect(
        self,
        source: Union[Node, str],
        target: Union[Node, str],
        source_port: Optional[str] = None,
        target_port: Optional[str] = None,
        condition: Optional[str] = None,
        label: Optional[str] = None
    ) -> Connection:
        """
        Conecta dois nós.
        
        Args:
            source: Nó ou ID de origem
            target: Nó ou ID de destino
            source_port: Nome da porta de saída (opcional)
            target_port: Nome da porta de entrada (opcional)
            condition: Condição para a conexão (opcional)
            label: Label da conexão (opcional)
            
        Returns:
            Conexão criada
        """
        # Resolver IDs
        source_id = source.id if isinstance(source, Node) else source
        target_id = target.id if isinstance(target, Node) else target
        
        # Obter nós
        source_node = self._workflow.get_node(source_id)
        target_node = self._workflow.get_node(target_id)
        
        if not source_node or not target_node:
            raise ValueError("Source or target node not found in workflow")
        
        # Resolver portas
        source_port_id = ""
        target_port_id = ""
        
        if source_port:
            port = source_node.get_output_port(source_port)
            if port:
                source_port_id = port.id
        elif source_node.outputs:
            source_port_id = source_node.outputs[0].id
        
        if target_port:
            port = target_node.get_input_port(target_port)
            if port:
                target_port_id = port.id
        elif target_node.inputs:
            target_port_id = target_node.inputs[0].id
        
        # Criar conexão
        connection = Connection(
            source_node_id=source_id,
            source_port_id=source_port_id,
            target_node_id=target_id,
            target_port_id=target_port_id,
            condition=condition,
            label=label
        )
        
        self._workflow.add_connection(connection)
        return connection
    
    def chain(self, *nodes: Node) -> "WorkflowBuilder":
        """
        Conecta múltiplos nós em sequência.
        
        Args:
            *nodes: Nós a conectar em cadeia
            
        Returns:
            Self para chaining
        """
        for i in range(len(nodes) - 1):
            self.connect(nodes[i], nodes[i + 1])
        return self
    
    # ==================== Build ====================
    
    def validate(self) -> list[str]:
        """Valida o workflow."""
        return self._workflow.validate()
    
    def build(self, validate: bool = True) -> Workflow:
        """
        Constrói e retorna o workflow.
        
        Args:
            validate: Se deve validar antes de retornar
            
        Returns:
            Workflow construído
            
        Raises:
            ValueError: Se validação falhar
        """
        if validate:
            errors = self.validate()
            if errors:
                raise ValueError(f"Workflow validation failed: {errors}")
        
        self._workflow.state = WorkflowState.DRAFT
        return self._workflow
    
    def build_and_publish(self) -> Workflow:
        """Constrói e publica o workflow."""
        workflow = self.build()
        workflow.state = WorkflowState.PUBLISHED
        return workflow
    
    # ==================== Export ====================
    
    def to_json(self) -> str:
        """Exporta workflow como JSON."""
        import json
        return json.dumps(self._workflow.to_dict(), indent=2, default=str)
    
    def to_python(self) -> str:
        """
        Exporta workflow como código Python.
        
        Gera código executável equivalente ao workflow.
        """
        lines = [
            "# Generated workflow code",
            "from studio import WorkflowBuilder",
            "",
            f'builder = WorkflowBuilder("{self._workflow.name}")',
            ""
        ]
        
        # Gerar código para cada nó
        node_vars = {}
        for i, node in enumerate(self._workflow.nodes):
            var_name = f"node_{i}"
            node_vars[node.id] = var_name
            
            if node.type == NodeType.INPUT:
                lines.append(f'{var_name} = builder.add_input("{node.name}")')
            elif node.type == NodeType.OUTPUT:
                lines.append(f'{var_name} = builder.add_output("{node.name}")')
            elif node.type == NodeType.AGENT:
                model = node.config.get("model", "gpt-4o")
                lines.append(f'{var_name} = builder.add_agent("{node.name}", model="{model}")')
            else:
                lines.append(f'{var_name} = builder.add_custom("{node.type.value}", name="{node.name}")')
        
        lines.append("")
        
        # Gerar conexões
        for conn in self._workflow.connections:
            source_var = node_vars.get(conn.source_node_id, "unknown")
            target_var = node_vars.get(conn.target_node_id, "unknown")
            lines.append(f'builder.connect({source_var}, {target_var})')
        
        lines.extend([
            "",
            "workflow = builder.build()",
            ""
        ])
        
        return "\n".join(lines)
    
    # ==================== Templates ====================
    
    @classmethod
    def from_template(cls, template_name: str) -> "WorkflowBuilder":
        """
        Cria builder a partir de um template.
        
        Args:
            template_name: Nome do template
            
        Returns:
            WorkflowBuilder configurado
        """
        from .templates import get_template_library
        
        library = get_template_library()
        template = library.get_template(template_name)
        
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        builder = cls(template.name, template.description)
        
        # Copiar nós e conexões do template
        for node in template.nodes:
            builder.add_node(Node.from_dict(node.to_dict()))
        
        for conn in template.connections:
            builder._workflow.add_connection(Connection.from_dict(conn.to_dict()))
        
        return builder
    
    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowBuilder":
        """
        Cria builder a partir de JSON.
        
        Args:
            json_str: String JSON do workflow
            
        Returns:
            WorkflowBuilder
        """
        import json
        data = json.loads(json_str)
        workflow = Workflow.from_dict(data)
        
        builder = cls(workflow.name, workflow.description)
        builder._workflow = workflow
        
        return builder

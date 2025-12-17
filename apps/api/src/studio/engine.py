"""
Agent Studio - Workflow Engine

Motor de execução de workflows.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Callable, Awaitable
import logging
import json

from .types import (
    Workflow, Node, Connection, ExecutionContext, WorkflowState, NodeType
)


logger = logging.getLogger(__name__)


@dataclass
class NodeExecutor:
    """Executor base para nós."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        """
        Executa um nó.
        
        Args:
            node: Nó a executar
            inputs: Dados de entrada
            context: Contexto de execução
            
        Returns:
            Output do nó
        """
        raise NotImplementedError


class AgentNodeExecutor(NodeExecutor):
    """Executor para nós de agente."""
    
    def __init__(self):
        self._agent_cache = {}
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        from ..sdk.agent import Agent
        
        # Obter ou criar agente
        agent_id = node.id
        
        if agent_id not in self._agent_cache:
            config = node.config
            self._agent_cache[agent_id] = Agent(
                name=node.name,
                model=config.get("model", "gpt-4o"),
                instructions=config.get("instructions", ""),
                temperature=config.get("temperature", 0.7)
            )
        
        agent = self._agent_cache[agent_id]
        
        # Executar
        message = inputs.get("message", inputs.get("data", ""))
        if isinstance(message, dict):
            message = message.get("content", str(message))
        
        response = await agent.arun(str(message))
        
        return {
            "response": response.content,
            "tool_calls": [tc.to_dict() for tc in response.tool_calls],
            "usage": response.usage.to_dict() if response.usage else {}
        }


class ToolNodeExecutor(NodeExecutor):
    """Executor para nós de ferramenta."""
    
    def __init__(self):
        self._tool_registry = None
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        from ..sdk.tool import get_tool_registry
        
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
        
        tool_name = node.config.get("tool_name", "")
        tool = self._tool_registry.get(tool_name)
        
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}
        
        # Executar tool
        input_data = inputs.get("input", inputs)
        params = inputs.get("parameters", node.config.get("parameters", {}))
        
        try:
            result = await tool.aexecute(**params, input=input_data)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}


class ConditionNodeExecutor(NodeExecutor):
    """Executor para nós de condição."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        condition = node.config.get("condition", "")
        value = inputs.get("value", inputs)
        
        # Avaliar condição
        try:
            # Contexto para eval
            eval_context = {
                "value": value,
                "inputs": inputs,
                "variables": context.variables,
                **inputs
            }
            
            result = eval(condition, {"__builtins__": {}}, eval_context)
            
            return {
                "true": value if result else None,
                "false": value if not result else None,
                "_branch": "true" if result else "false"
            }
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return {"false": value, "_branch": "false"}


class LoopNodeExecutor(NodeExecutor):
    """Executor para nós de loop."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        items = inputs.get("items", [])
        max_iterations = node.config.get("max_iterations", 10)
        
        results = []
        
        for i, item in enumerate(items[:max_iterations]):
            results.append({
                "item": item,
                "index": i
            })
        
        return {
            "complete": results,
            "count": len(results)
        }


class MemoryNodeExecutor(NodeExecutor):
    """Executor para nós de memória."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        from ..sdk.memory import Memory
        
        memory_type = node.config.get("memory_type", "long_term")
        memory = Memory(type=memory_type)
        
        if node.type == NodeType.MEMORY_READ:
            query = inputs.get("query", "")
            limit = node.config.get("limit", 10)
            
            results = await memory.search(query, limit=limit)
            
            return {
                "memories": results,
                "context": "\n".join([r.get("content", "") for r in results])
            }
        
        elif node.type == NodeType.MEMORY_WRITE:
            content = inputs.get("content", "")
            importance = node.config.get("importance", 0.5)
            tags = inputs.get("tags", [])
            
            memory_id = await memory.store(
                content=content,
                importance=importance,
                tags=tags
            )
            
            return {"memory_id": memory_id}
        
        return {}


class RAGNodeExecutor(NodeExecutor):
    """Executor para nós de RAG."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        from ..rag.v2.pipeline import get_rag_pipeline
        
        pipeline = get_rag_pipeline()
        
        query = inputs.get("query", "")
        limit = node.config.get("limit", 10)
        
        result = await pipeline.query(query, top_k=limit)
        
        return {
            "documents": [
                {"content": doc.content, "score": doc.score}
                for doc in result.documents
            ],
            "context": result.context
        }


class TransformNodeExecutor(NodeExecutor):
    """Executor para nós de transformação."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        code = node.config.get("code", "")
        data = inputs.get("data", inputs)
        
        try:
            # Executar código de transformação
            local_vars = {"data": data, "inputs": inputs}
            exec(code, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict}}, local_vars)
            
            return {"result": local_vars.get("result", data)}
        except Exception as e:
            return {"result": data, "error": str(e)}


class HTTPNodeExecutor(NodeExecutor):
    """Executor para nós HTTP."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        import aiohttp
        
        method = node.config.get("method", "GET")
        url = node.config.get("url", "")
        headers = node.config.get("headers", {})
        
        body = inputs.get("body")
        params = inputs.get("query_params", {})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=body if body else None,
                    params=params,
                    headers=headers
                ) as response:
                    return {
                        "response": await response.json(),
                        "status": response.status,
                        "headers": dict(response.headers)
                    }
        except Exception as e:
            return {"error": str(e), "status": 0}


class DelayNodeExecutor(NodeExecutor):
    """Executor para nós de delay."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        seconds = node.config.get("seconds", 1.0)
        await asyncio.sleep(seconds)
        
        return {"output": inputs.get("input", inputs)}


class CodeNodeExecutor(NodeExecutor):
    """Executor para nós de código."""
    
    async def execute(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        code = node.config.get("code", "")
        
        try:
            # Definir função
            local_vars = {}
            exec(code, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict, "print": print}}, local_vars)
            
            # Executar função execute
            if "execute" in local_vars:
                result = local_vars["execute"](inputs.get("inputs", inputs))
                return {"result": result}
            
            return {"error": "No execute function defined"}
        except Exception as e:
            return {"error": str(e)}


class WorkflowEngine:
    """
    Motor de execução de workflows.
    
    Executa workflows definidos no Agent Studio.
    
    Uso:
    ```python
    engine = WorkflowEngine()
    
    # Executar workflow
    result = await engine.execute(workflow, {"message": "Hello"})
    
    # Com streaming
    async for update in engine.execute_stream(workflow, inputs):
        print(update)
    ```
    """
    
    def __init__(self):
        # Executores por tipo de nó
        self._executors: dict[NodeType, NodeExecutor] = {
            NodeType.AGENT: AgentNodeExecutor(),
            NodeType.TOOL: ToolNodeExecutor(),
            NodeType.CONDITION: ConditionNodeExecutor(),
            NodeType.LOOP: LoopNodeExecutor(),
            NodeType.MEMORY_READ: MemoryNodeExecutor(),
            NodeType.MEMORY_WRITE: MemoryNodeExecutor(),
            NodeType.RAG_SEARCH: RAGNodeExecutor(),
            NodeType.TRANSFORM: TransformNodeExecutor(),
            NodeType.HTTP: HTTPNodeExecutor(),
            NodeType.DELAY: DelayNodeExecutor(),
            NodeType.CODE: CodeNodeExecutor()
        }
        
        # Histórico de execuções
        self._executions: list[ExecutionContext] = []
        
        # Hooks
        self._on_node_start: list[Callable] = []
        self._on_node_complete: list[Callable] = []
    
    def register_executor(
        self,
        node_type: NodeType,
        executor: NodeExecutor
    ) -> None:
        """Registra executor customizado."""
        self._executors[node_type] = executor
    
    def on_node_start(self, callback: Callable) -> None:
        """Registra callback para início de nó."""
        self._on_node_start.append(callback)
    
    def on_node_complete(self, callback: Callable) -> None:
        """Registra callback para fim de nó."""
        self._on_node_complete.append(callback)
    
    async def execute(
        self,
        workflow: Workflow,
        inputs: dict,
        variables: Optional[dict] = None
    ) -> dict:
        """
        Executa um workflow.
        
        Args:
            workflow: Workflow a executar
            inputs: Dados de entrada
            variables: Variáveis adicionais
            
        Returns:
            Outputs do workflow
        """
        # Criar contexto
        context = ExecutionContext(
            workflow_id=workflow.id,
            inputs=inputs,
            variables={**workflow.variables, **(variables or {})}
        )
        
        # Validar workflow
        errors = workflow.validate()
        if errors:
            context.errors = errors
            return {"error": errors}
        
        # Encontrar nós de entrada
        input_nodes = workflow.get_input_nodes()
        
        # Processar nós de entrada
        for node in input_nodes:
            context.set_node_output(node.id, {"data": inputs, "message": inputs})
        
        # Executar em ordem topológica
        await self._execute_graph(workflow, context)
        
        # Coletar outputs
        output_nodes = workflow.get_output_nodes()
        outputs = {}
        
        for node in output_nodes:
            output = context.get_node_output(node.id)
            if output:
                outputs[node.name] = output
        
        context.outputs = outputs
        context.completed_at = datetime.now()
        
        self._executions.append(context)
        
        return outputs
    
    async def _execute_graph(
        self,
        workflow: Workflow,
        context: ExecutionContext
    ) -> None:
        """Executa o grafo de nós."""
        # Calcular ordem topológica
        order = self._topological_sort(workflow)
        
        for node_id in order:
            node = workflow.get_node(node_id)
            
            if not node or node_id in context.completed_nodes:
                continue
            
            # Pular Input (já processado)
            if node.type == NodeType.INPUT:
                continue
            
            # Coletar inputs das conexões
            node_inputs = await self._collect_inputs(workflow, node, context)
            
            # Verificar se pode executar (dependências satisfeitas)
            incoming = workflow.get_incoming_connections(node_id)
            deps_ready = all(
                conn.source_node_id in context.completed_nodes
                for conn in incoming
            )
            
            if not deps_ready:
                continue
            
            # Executar nó
            context.current_node_id = node_id
            
            # Callbacks
            for cb in self._on_node_start:
                await cb(node, context) if asyncio.iscoroutinefunction(cb) else cb(node, context)
            
            try:
                output = await self._execute_node(node, node_inputs, context)
                context.set_node_output(node_id, output)
                
            except Exception as e:
                logger.error(f"Node {node.name} failed: {e}")
                context.errors.append(f"Node {node.name}: {e}")
                context.set_node_output(node_id, {"error": str(e)})
            
            # Callbacks
            for cb in self._on_node_complete:
                await cb(node, context) if asyncio.iscoroutinefunction(cb) else cb(node, context)
    
    async def _execute_node(
        self,
        node: Node,
        inputs: dict,
        context: ExecutionContext
    ) -> Any:
        """Executa um nó individual."""
        executor = self._executors.get(node.type)
        
        if executor:
            return await executor.execute(node, inputs, context)
        
        # Output node - passar dados
        if node.type == NodeType.OUTPUT:
            return inputs
        
        # Nó sem executor - passar inputs
        return inputs
    
    async def _collect_inputs(
        self,
        workflow: Workflow,
        node: Node,
        context: ExecutionContext
    ) -> dict:
        """Coleta inputs de um nó das conexões."""
        inputs = {}
        
        for conn in workflow.get_incoming_connections(node.id):
            source_output = context.get_node_output(conn.source_node_id)
            
            if source_output is None:
                continue
            
            # Verificar condição
            if conn.condition:
                try:
                    if not eval(conn.condition, {"__builtins__": {}}, {"value": source_output}):
                        continue
                except:
                    pass
            
            # Mapear para porta de entrada
            target_port = None
            for port in node.inputs:
                if port.id == conn.target_port_id:
                    target_port = port
                    break
            
            if target_port:
                # Extrair valor da porta de saída
                if isinstance(source_output, dict):
                    # Tentar encontrar valor correspondente
                    for key in [target_port.name, "data", "result", "response", "output"]:
                        if key in source_output:
                            inputs[target_port.name] = source_output[key]
                            break
                    else:
                        inputs[target_port.name] = source_output
                else:
                    inputs[target_port.name] = source_output
            else:
                # Merge geral
                if isinstance(source_output, dict):
                    inputs.update(source_output)
                else:
                    inputs["data"] = source_output
        
        return inputs
    
    def _topological_sort(self, workflow: Workflow) -> list[str]:
        """Ordena nós topologicamente."""
        # Calcular in-degree
        in_degree = {node.id: 0 for node in workflow.nodes}
        
        for conn in workflow.connections:
            if conn.target_node_id in in_degree:
                in_degree[conn.target_node_id] += 1
        
        # Fila com nós sem dependências
        queue = [nid for nid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # Reduzir in-degree dos vizinhos
            for conn in workflow.get_outgoing_connections(node_id):
                if conn.target_node_id in in_degree:
                    in_degree[conn.target_node_id] -= 1
                    if in_degree[conn.target_node_id] == 0:
                        queue.append(conn.target_node_id)
        
        return result
    
    def get_execution_history(self, limit: int = 10) -> list[dict]:
        """Retorna histórico de execuções."""
        return [e.to_dict() for e in self._executions[-limit:]]


# Singleton
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Retorna o workflow engine singleton."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine

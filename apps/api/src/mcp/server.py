"""
MCP Server - Implementação de server MCP

Expõe recursos da plataforma Agno via protocolo MCP,
permitindo que LLMs externos acessem:
- RAG: Busca em documentos e conhecimento
- Memory: Sistema de memória de agentes
- Tools: Ferramentas internas da plataforma
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Any, Callable, Awaitable
import logging

from .types import (
    MCPMessage, MCPError, MCPCapabilities,
    MCPTool, MCPResource, MCPPrompt,
    ToolParameter, PromptArgument, PromptMessage,
    ServerInfo, MessageRole
)


logger = logging.getLogger(__name__)


# Type alias para handlers
ToolHandler = Callable[[dict], Awaitable[Any]]
ResourceHandler = Callable[[str], Awaitable[str]]


class MCPServerBase(ABC):
    """
    Base class para servers MCP.
    
    Implementa o protocolo MCP do lado do server,
    permitindo expor tools, resources e prompts.
    """
    
    PROTOCOL_VERSION = "2024-11-05"
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        
        # Registros
        self._tools: dict[str, tuple[MCPTool, ToolHandler]] = {}
        self._resources: dict[str, tuple[MCPResource, ResourceHandler]] = {}
        self._prompts: dict[str, MCPPrompt] = {}
        
        # Capabilities
        self._capabilities = MCPCapabilities()
        
        # Estado
        self._initialized = False
        self._client_info: Optional[dict] = None
    
    def register_tool(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: Optional[list[ToolParameter]] = None
    ) -> None:
        """
        Registra uma ferramenta.
        
        Args:
            name: Nome da ferramenta
            description: Descrição
            handler: Função async que executa a ferramenta
            parameters: Lista de parâmetros
        """
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters or []
        )
        
        self._tools[name] = (tool, handler)
        self._capabilities.tools = True
        
        logger.debug(f"Tool registrada: {name}")
    
    def register_resource(
        self,
        uri: str,
        name: str,
        handler: ResourceHandler,
        description: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> None:
        """
        Registra um recurso.
        
        Args:
            uri: URI do recurso
            name: Nome do recurso
            handler: Função async que retorna conteúdo
            description: Descrição
            mime_type: MIME type
        """
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        
        self._resources[uri] = (resource, handler)
        self._capabilities.resources = True
        
        logger.debug(f"Resource registrado: {uri}")
    
    def register_prompt(
        self,
        name: str,
        description: Optional[str] = None,
        arguments: Optional[list[PromptArgument]] = None
    ) -> None:
        """
        Registra um prompt.
        
        Args:
            name: Nome do prompt
            description: Descrição
            arguments: Argumentos do prompt
        """
        prompt = MCPPrompt(
            name=name,
            description=description,
            arguments=arguments or []
        )
        
        self._prompts[name] = prompt
        self._capabilities.prompts = True
        
        logger.debug(f"Prompt registrado: {name}")
    
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """
        Processa uma mensagem MCP.
        
        Args:
            message: Mensagem recebida
            
        Returns:
            Resposta ou None para notificações
        """
        try:
            if message.is_notification():
                await self._handle_notification(message)
                return None
            
            if not message.is_request():
                return MCPMessage.error_response(
                    message.id or 0,
                    MCPError.INVALID_REQUEST,
                    "Invalid message type"
                )
            
            result = await self._handle_request(message)
            
            return MCPMessage.response(message.id, result)
            
        except MCPError as e:
            return MCPMessage.error_response(
                message.id or 0,
                e.code,
                e.message,
                e.data
            )
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
            return MCPMessage.error_response(
                message.id or 0,
                MCPError.INTERNAL_ERROR,
                str(e)
            )
    
    async def _handle_notification(self, message: MCPMessage) -> None:
        """Processa notificação."""
        method = message.method
        
        if method == "notifications/initialized":
            logger.info("Client initialized")
        elif method == "notifications/cancelled":
            # Cancelamento de request
            request_id = message.params.get("requestId") if message.params else None
            logger.debug(f"Request {request_id} cancelled")
        else:
            logger.debug(f"Unknown notification: {method}")
    
    async def _handle_request(self, message: MCPMessage) -> Any:
        """Processa request e retorna resultado."""
        method = message.method
        params = message.params or {}
        
        # Handlers de métodos
        handlers = {
            "initialize": self._handle_initialize,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        }
        
        handler = handlers.get(method)
        
        if handler is None:
            raise MCPError(
                code=MCPError.METHOD_NOT_FOUND,
                message=f"Unknown method: {method}"
            )
        
        return await handler(params)
    
    async def _handle_initialize(self, params: dict) -> dict:
        """Handler para initialize."""
        protocol_version = params.get("protocolVersion", self.PROTOCOL_VERSION)
        self._client_info = params.get("clientInfo", {})
        
        self._initialized = True
        
        return {
            "protocolVersion": protocol_version,
            "capabilities": self._capabilities.to_dict(),
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    async def _handle_ping(self, params: dict) -> dict:
        """Handler para ping."""
        return {}
    
    async def _handle_tools_list(self, params: dict) -> dict:
        """Handler para tools/list."""
        tools = [tool.to_dict() for tool, _ in self._tools.values()]
        return {"tools": tools}
    
    async def _handle_tools_call(self, params: dict) -> dict:
        """Handler para tools/call."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self._tools:
            raise MCPError(
                code=MCPError.INVALID_PARAMS,
                message=f"Unknown tool: {name}"
            )
        
        tool, handler = self._tools[name]
        
        try:
            result = await handler(arguments)
            
            # Converter resultado para formato MCP
            if isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, dict):
                content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            elif isinstance(result, list):
                content = result
            else:
                content = [{"type": "text", "text": str(result)}]
            
            return {"content": content}
            
        except Exception as e:
            return {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True
            }
    
    async def _handle_resources_list(self, params: dict) -> dict:
        """Handler para resources/list."""
        resources = [resource.to_dict() for resource, _ in self._resources.values()]
        return {"resources": resources}
    
    async def _handle_resources_read(self, params: dict) -> dict:
        """Handler para resources/read."""
        uri = params.get("uri")
        
        if uri not in self._resources:
            raise MCPError(
                code=MCPError.INVALID_PARAMS,
                message=f"Unknown resource: {uri}"
            )
        
        resource, handler = self._resources[uri]
        
        content = await handler(uri)
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": resource.mime_type or "text/plain",
                "text": content
            }]
        }
    
    async def _handle_prompts_list(self, params: dict) -> dict:
        """Handler para prompts/list."""
        prompts = [prompt.to_dict() for prompt in self._prompts.values()]
        return {"prompts": prompts}
    
    async def _handle_prompts_get(self, params: dict) -> dict:
        """Handler para prompts/get."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self._prompts:
            raise MCPError(
                code=MCPError.INVALID_PARAMS,
                message=f"Unknown prompt: {name}"
            )
        
        # Subclasses devem sobrescrever para gerar mensagens
        messages = await self._generate_prompt_messages(name, arguments)
        
        return {"messages": messages}
    
    @abstractmethod
    async def _generate_prompt_messages(
        self,
        name: str,
        arguments: dict
    ) -> list[dict]:
        """
        Gera mensagens para um prompt.
        
        Deve ser implementado por subclasses.
        """
        pass


class AgnoMCPServer(MCPServerBase):
    """
    Server MCP da plataforma Agno.
    
    Expõe:
    - RAG Search: Busca em documentos
    - Memory: Sistema de memória
    - Agents: Informações de agentes
    """
    
    def __init__(self):
        super().__init__(
            name="agno-platform",
            version="2.0.0",
            description="Agno AI Platform MCP Server"
        )
        
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    def _setup_tools(self) -> None:
        """Configura ferramentas."""
        
        # RAG Search
        self.register_tool(
            name="rag_search",
            description="Search documents and knowledge base using semantic search",
            handler=self._tool_rag_search,
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query",
                    required=True
                ),
                ToolParameter(
                    name="project_id",
                    type="integer",
                    description="Project ID to search in"
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum results",
                    default=10
                )
            ]
        )
        
        # Memory Store
        self.register_tool(
            name="memory_store",
            description="Store a memory for later retrieval",
            handler=self._tool_memory_store,
            parameters=[
                ToolParameter(
                    name="content",
                    type="string",
                    description="Memory content to store",
                    required=True
                ),
                ToolParameter(
                    name="agent_id",
                    type="string",
                    description="Agent ID"
                ),
                ToolParameter(
                    name="importance",
                    type="number",
                    description="Importance score (0-1)",
                    default=0.5
                )
            ]
        )
        
        # Memory Search
        self.register_tool(
            name="memory_search",
            description="Search stored memories",
            handler=self._tool_memory_search,
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query",
                    required=True
                ),
                ToolParameter(
                    name="agent_id",
                    type="string",
                    description="Agent ID"
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum results",
                    default=5
                )
            ]
        )
        
        # List Agents
        self.register_tool(
            name="list_agents",
            description="List available AI agents",
            handler=self._tool_list_agents,
            parameters=[
                ToolParameter(
                    name="project_id",
                    type="integer",
                    description="Project ID"
                )
            ]
        )
    
    def _setup_resources(self) -> None:
        """Configura recursos."""
        
        self.register_resource(
            uri="agno://agents",
            name="Available Agents",
            handler=self._resource_agents,
            description="List of available AI agents",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="agno://tools",
            name="Available Tools",
            handler=self._resource_tools,
            description="List of available tools",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="agno://config",
            name="Platform Configuration",
            handler=self._resource_config,
            description="Platform configuration",
            mime_type="application/json"
        )
    
    def _setup_prompts(self) -> None:
        """Configura prompts."""
        
        self.register_prompt(
            name="analyze_document",
            description="Analyze a document and extract key information",
            arguments=[
                PromptArgument(
                    name="document_url",
                    description="URL or path to document",
                    required=True
                )
            ]
        )
        
        self.register_prompt(
            name="summarize_conversation",
            description="Summarize a conversation history",
            arguments=[
                PromptArgument(
                    name="session_id",
                    description="Session ID to summarize",
                    required=True
                )
            ]
        )
    
    # Tool Handlers
    
    async def _tool_rag_search(self, args: dict) -> str:
        """Handler para rag_search."""
        from ..rag.v2.pipeline import get_rag_pipeline
        
        query = args.get("query", "")
        project_id = args.get("project_id")
        limit = args.get("limit", 10)
        
        try:
            pipeline = get_rag_pipeline()
            results = await pipeline.retrieve(
                query=query,
                project_id=project_id,
                top_k=limit
            )
            
            # Formatar resultados
            output = []
            for i, chunk in enumerate(results, 1):
                output.append(f"{i}. {chunk.content[:200]}...")
            
            return "\n\n".join(output) if output else "No results found"
            
        except Exception as e:
            return f"Search error: {e}"
    
    async def _tool_memory_store(self, args: dict) -> str:
        """Handler para memory_store."""
        from ..memory.v2.manager import get_memory_manager
        
        content = args.get("content", "")
        agent_id = args.get("agent_id")
        importance = args.get("importance", 0.5)
        
        try:
            manager = get_memory_manager()
            memory = await manager.store_long_term(
                content=content,
                agent_id=agent_id,
                importance=importance
            )
            
            return f"Memory stored with ID: {memory.id}"
            
        except Exception as e:
            return f"Error storing memory: {e}"
    
    async def _tool_memory_search(self, args: dict) -> str:
        """Handler para memory_search."""
        from ..memory.v2.manager import get_memory_manager
        
        query = args.get("query", "")
        agent_id = args.get("agent_id")
        limit = args.get("limit", 5)
        
        try:
            manager = get_memory_manager()
            results = await manager.search_memories(
                query=query,
                agent_id=agent_id,
                limit=limit
            )
            
            output = []
            for i, result in enumerate(results, 1):
                output.append(f"{i}. [{result.score:.2f}] {result.memory.content[:150]}...")
            
            return "\n\n".join(output) if output else "No memories found"
            
        except Exception as e:
            return f"Search error: {e}"
    
    async def _tool_list_agents(self, args: dict) -> str:
        """Handler para list_agents."""
        # Placeholder - integrar com sistema de agentes
        return json.dumps([
            {"name": "assistant", "description": "General purpose assistant"},
            {"name": "researcher", "description": "Research and analysis agent"},
            {"name": "coder", "description": "Code generation and review agent"}
        ], indent=2)
    
    # Resource Handlers
    
    async def _resource_agents(self, uri: str) -> str:
        """Handler para resource agents."""
        return json.dumps({
            "agents": [
                {"name": "assistant", "status": "active"},
                {"name": "researcher", "status": "active"},
                {"name": "coder", "status": "active"}
            ]
        }, indent=2)
    
    async def _resource_tools(self, uri: str) -> str:
        """Handler para resource tools."""
        tools = [tool.to_dict() for tool, _ in self._tools.values()]
        return json.dumps({"tools": tools}, indent=2)
    
    async def _resource_config(self, uri: str) -> str:
        """Handler para resource config."""
        return json.dumps({
            "platform": "Agno",
            "version": self.version,
            "features": ["rag", "memory", "agents", "tools"]
        }, indent=2)
    
    # Prompt Generator
    
    async def _generate_prompt_messages(
        self,
        name: str,
        arguments: dict
    ) -> list[dict]:
        """Gera mensagens para prompts."""
        
        if name == "analyze_document":
            doc_url = arguments.get("document_url", "")
            return [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please analyze the document at {doc_url} and extract:\n"
                               "1. Key topics and themes\n"
                               "2. Main arguments or points\n"
                               "3. Important entities mentioned\n"
                               "4. A brief summary"
                    }
                }
            ]
        
        elif name == "summarize_conversation":
            session_id = arguments.get("session_id", "")
            return [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Please summarize the conversation from session {session_id}:\n"
                               "1. Main topics discussed\n"
                               "2. Key decisions or conclusions\n"
                               "3. Action items if any\n"
                               "4. Overall sentiment"
                    }
                }
            ]
        
        return []


# Factory para criar server
def create_agno_mcp_server() -> AgnoMCPServer:
    """Cria instância do server MCP Agno."""
    return AgnoMCPServer()

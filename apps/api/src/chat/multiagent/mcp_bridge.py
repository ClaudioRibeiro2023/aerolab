"""
MCP Bridge - Integração com Model Context Protocol.

Conecta o chat com servidores MCP para:
- Ferramentas externas
- Recursos de dados
- Prompts dinâmicos
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class MCPResourceType(str, Enum):
    """Tipos de recursos MCP."""
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class MCPTool:
    """Ferramenta MCP."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    server_name: str = ""
    
    def to_openai_format(self) -> Dict:
        """Converte para formato OpenAI tools."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class MCPResource:
    """Recurso MCP."""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    server_name: str = ""


@dataclass
class MCPServer:
    """Configuração de servidor MCP."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    is_connected: bool = False
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)


class MCPBridge:
    """
    Bridge para servidores MCP.
    
    Gerencia conexões com servidores MCP e expõe suas
    ferramentas e recursos para o chat.
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tool_handlers: Dict[str, Callable] = {}
    
    async def connect(self, server: MCPServer) -> bool:
        """
        Conecta a um servidor MCP.
        
        Em produção: usar subprocess para spawnar servidor
        e comunicar via stdio/SSE.
        """
        try:
            # Placeholder: simular conexão
            server.is_connected = True
            self._servers[server.name] = server
            
            logger.info(f"Connected to MCP server: {server.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server.name}: {e}")
            return False
    
    async def disconnect(self, server_name: str) -> bool:
        """Desconecta de um servidor MCP."""
        server = self._servers.pop(server_name, None)
        if server:
            server.is_connected = False
            logger.info(f"Disconnected from MCP server: {server_name}")
            return True
        return False
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """Lista ferramentas disponíveis."""
        tools = []
        
        for name, server in self._servers.items():
            if server_name and name != server_name:
                continue
            if server.is_connected:
                tools.extend(server.tools)
        
        return tools
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """Lista recursos disponíveis."""
        resources = []
        
        for name, server in self._servers.items():
            if server_name and name != server_name:
                continue
            if server.is_connected:
                resources.extend(server.resources)
        
        return resources
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Chama uma ferramenta MCP.
        
        Args:
            tool_name: Nome da ferramenta
            arguments: Argumentos
            
        Returns:
            Resultado da ferramenta
        """
        # Encontrar servidor que tem a ferramenta
        for server in self._servers.values():
            if not server.is_connected:
                continue
            
            for tool in server.tools:
                if tool.name == tool_name:
                    return await self._execute_tool(server, tool, arguments)
        
        return {"error": f"Tool not found: {tool_name}"}
    
    async def _execute_tool(
        self,
        server: MCPServer,
        tool: MCPTool,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa uma ferramenta em um servidor."""
        try:
            # Em produção: enviar request via MCP protocol
            # Por agora, placeholder
            logger.info(f"Executing MCP tool: {tool.name} with args: {arguments}")
            
            return {
                "result": f"[MCP tool {tool.name} execution placeholder]",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"MCP tool execution error: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Lê um recurso MCP."""
        for server in self._servers.values():
            if not server.is_connected:
                continue
            
            for resource in server.resources:
                if resource.uri == uri:
                    return await self._fetch_resource(server, resource)
        
        return {"error": f"Resource not found: {uri}"}
    
    async def _fetch_resource(
        self,
        server: MCPServer,
        resource: MCPResource
    ) -> Dict[str, Any]:
        """Busca conteúdo de um recurso."""
        try:
            # Em produção: enviar request via MCP protocol
            logger.info(f"Fetching MCP resource: {resource.uri}")
            
            return {
                "content": f"[MCP resource {resource.name} content placeholder]",
                "mime_type": resource.mime_type,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"MCP resource fetch error: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_tools_for_chat(self) -> List[Dict]:
        """Retorna ferramentas em formato para chat completions."""
        tools = []
        
        for server in self._servers.values():
            if server.is_connected:
                for tool in server.tools:
                    tools.append(tool.to_openai_format())
        
        return tools
    
    def register_builtin_servers(self) -> None:
        """Registra servidores MCP built-in comuns."""
        # Exemplos de servidores populares
        builtin = [
            MCPServer(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                tools=[
                    MCPTool(
                        name="read_file",
                        description="Read contents of a file",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "File path"}
                            },
                            "required": ["path"]
                        }
                    ),
                    MCPTool(
                        name="write_file",
                        description="Write contents to a file",
                        parameters={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["path", "content"]
                        }
                    )
                ]
            ),
            MCPServer(
                name="github",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                tools=[
                    MCPTool(
                        name="search_repositories",
                        description="Search GitHub repositories",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    )
                ]
            )
        ]
        
        for server in builtin:
            self._servers[server.name] = server


# Singleton
_mcp_bridge: Optional[MCPBridge] = None


def get_mcp_bridge() -> MCPBridge:
    global _mcp_bridge
    if _mcp_bridge is None:
        _mcp_bridge = MCPBridge()
    return _mcp_bridge

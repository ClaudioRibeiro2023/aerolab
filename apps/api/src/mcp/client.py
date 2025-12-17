"""
MCP Client - Cliente para conectar a servers MCP

Implementa o lado cliente do Model Context Protocol,
permitindo:
- Conexão a servers MCP externos
- Descoberta de tools, resources e prompts
- Invocação de ferramentas
- Leitura de recursos
"""

import asyncio
from datetime import datetime
from typing import Optional, Any, AsyncIterator
import logging
import uuid

from .types import (
    MCPServer, MCPTool, MCPResource, MCPPrompt,
    MCPMessage, MCPError, MCPCapabilities,
    ToolCall, ToolResult, ResourceContent,
    ServerStatus, TransportType, ClientInfo, ServerInfo
)
from .transports import Transport, StdioTransport, HTTPTransport, SSETransport, TransportFactory


logger = logging.getLogger(__name__)


class MCPClient:
    """
    Cliente MCP para conectar a servers externos.
    
    Gerencia conexão, comunicação e estado com um server MCP.
    
    Uso:
    ```python
    client = MCPClient(server)
    await client.connect()
    
    # Listar ferramentas
    tools = await client.list_tools()
    
    # Invocar ferramenta
    result = await client.call_tool("search", {"query": "test"})
    
    await client.disconnect()
    ```
    """
    
    # Versão do protocolo suportada
    PROTOCOL_VERSION = "2024-11-05"
    
    def __init__(self, server: MCPServer):
        self.server = server
        
        self._transport: Optional[Transport] = None
        self._initialized = False
        self._server_info: Optional[ServerInfo] = None
        
        # Cache de capabilities
        self._tools: list[MCPTool] = []
        self._resources: list[MCPResource] = []
        self._prompts: list[MCPPrompt] = []
        
        # Pending requests
        self._pending: dict[str, asyncio.Future] = {}
        self._request_id = 0
        
        # Métricas
        self.total_calls = 0
        self.failed_calls = 0
        self.total_latency_ms = 0
    
    def _next_id(self) -> int:
        """Gera próximo ID de request."""
        self._request_id += 1
        return self._request_id
    
    async def connect(self) -> None:
        """
        Estabelece conexão com o server MCP.
        
        1. Cria transporte apropriado
        2. Conecta ao processo/server
        3. Envia initialize
        4. Recebe capabilities
        5. Envia initialized notification
        """
        if self._initialized:
            return
        
        try:
            self.server.status = ServerStatus.CONNECTING
            
            # Criar transporte
            self._transport = self._create_transport()
            
            # Conectar
            await self._transport.connect()
            
            # Inicializar protocolo
            await self._initialize()
            
            self.server.status = ServerStatus.CONNECTED
            self.server.connected_at = datetime.now()
            self._initialized = True
            
            logger.info(f"Conectado ao server MCP: {self.server.name}")
            
        except Exception as e:
            self.server.status = ServerStatus.ERROR
            logger.error(f"Erro ao conectar: {e}")
            raise
    
    def _create_transport(self) -> Transport:
        """Cria transporte baseado na configuração do server."""
        if self.server.transport == TransportType.STDIO:
            if not self.server.command:
                raise MCPError(
                    code=MCPError.INVALID_PARAMS,
                    message="Command required for stdio transport"
                )
            return StdioTransport(
                command=self.server.command,
                args=self.server.args,
                env=self.server.env
            )
        
        elif self.server.transport == TransportType.HTTP:
            if not self.server.url:
                raise MCPError(
                    code=MCPError.INVALID_PARAMS,
                    message="URL required for HTTP transport"
                )
            return HTTPTransport(url=self.server.url)
        
        elif self.server.transport == TransportType.SSE:
            if not self.server.url:
                raise MCPError(
                    code=MCPError.INVALID_PARAMS,
                    message="URL required for SSE transport"
                )
            return SSETransport(url=self.server.url)
        
        else:
            raise MCPError(
                code=MCPError.INVALID_PARAMS,
                message=f"Unknown transport: {self.server.transport}"
            )
    
    async def _initialize(self) -> None:
        """Executa handshake de inicialização."""
        # Enviar initialize
        client_info = ClientInfo()
        
        response = await self._request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {},  # Client capabilities
            "clientInfo": client_info.to_dict()
        })
        
        if response.error:
            raise MCPError(
                code=response.error.get("code", MCPError.INTERNAL_ERROR),
                message=response.error.get("message", "Initialize failed")
            )
        
        result = response.result
        
        # Parse server info
        self._server_info = ServerInfo(
            name=result.get("serverInfo", {}).get("name", self.server.name),
            version=result.get("serverInfo", {}).get("version", "unknown"),
            protocol_version=result.get("protocolVersion", self.PROTOCOL_VERSION),
            capabilities=MCPCapabilities.from_dict(result.get("capabilities", {}))
        )
        
        self.server.capabilities = self._server_info.capabilities
        
        # Enviar notification initialized
        await self._notify("notifications/initialized", {})
        
        logger.debug(f"Server inicializado: {self._server_info.name} v{self._server_info.version}")
    
    async def disconnect(self) -> None:
        """Desconecta do server MCP."""
        if self._transport:
            await self._transport.disconnect()
            self._transport = None
        
        self._initialized = False
        self.server.status = ServerStatus.DISCONNECTED
        
        # Limpar cache
        self._tools.clear()
        self._resources.clear()
        self._prompts.clear()
        
        logger.info(f"Desconectado do server: {self.server.name}")
    
    async def _request(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 30.0
    ) -> MCPMessage:
        """
        Envia request e aguarda response.
        
        Args:
            method: Método MCP
            params: Parâmetros
            timeout: Timeout em segundos
            
        Returns:
            MCPMessage com resultado ou erro
        """
        if not self._transport:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message="Not connected"
            )
        
        request_id = self._next_id()
        message = MCPMessage.request(method, params, request_id)
        
        start = datetime.now()
        
        try:
            # Para HTTP, usar send_and_receive
            if isinstance(self._transport, HTTPTransport):
                response = await self._transport.send_and_receive(message)
            elif isinstance(self._transport, SSETransport):
                response = await self._transport.send_and_receive(message, timeout)
            else:
                # Para stdio, enviar e aguardar response
                await self._transport.send(message)
                
                # Aguardar resposta com ID correto
                response = None
                deadline = asyncio.get_event_loop().time() + timeout
                
                while asyncio.get_event_loop().time() < deadline:
                    msg = await self._transport.receive()
                    
                    if msg and msg.id == request_id:
                        response = msg
                        break
                
                if response is None:
                    raise MCPError(
                        code=MCPError.INTERNAL_ERROR,
                        message=f"Timeout waiting for response"
                    )
            
            elapsed = (datetime.now() - start).total_seconds() * 1000
            self.total_latency_ms += elapsed
            self.total_calls += 1
            
            self.server.total_calls += 1
            self.server.last_activity = datetime.now()
            
            return response
            
        except Exception as e:
            self.failed_calls += 1
            self.server.error_count += 1
            raise
    
    async def _notify(self, method: str, params: Optional[dict] = None) -> None:
        """Envia notificação (sem esperar resposta)."""
        if not self._transport:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message="Not connected"
            )
        
        message = MCPMessage.notification(method, params)
        await self._transport.send(message)
    
    # ==================== Tools ====================
    
    async def list_tools(self, force_refresh: bool = False) -> list[MCPTool]:
        """
        Lista ferramentas disponíveis no server.
        
        Args:
            force_refresh: Forçar atualização do cache
            
        Returns:
            Lista de MCPTool
        """
        if self._tools and not force_refresh:
            return self._tools
        
        if not self.server.capabilities.tools:
            return []
        
        response = await self._request("tools/list")
        
        if response.error:
            raise MCPError(
                code=response.error.get("code"),
                message=response.error.get("message")
            )
        
        tools_data = response.result.get("tools", [])
        
        self._tools = [
            MCPTool.from_dict(t, self.server.id)
            for t in tools_data
        ]
        
        logger.debug(f"Descobertas {len(self._tools)} ferramentas")
        
        return self._tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[dict] = None
    ) -> ToolResult:
        """
        Invoca uma ferramenta no server.
        
        Args:
            name: Nome da ferramenta
            arguments: Argumentos da ferramenta
            
        Returns:
            ToolResult com conteúdo ou erro
        """
        start = datetime.now()
        
        call = ToolCall(
            tool_name=name,
            arguments=arguments or {},
            server_id=self.server.id
        )
        
        response = await self._request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        elapsed = (datetime.now() - start).total_seconds() * 1000
        
        if response.error:
            return ToolResult(
                call_id=call.id,
                content=response.error.get("message", "Unknown error"),
                is_error=True,
                error_message=response.error.get("message"),
                duration_ms=elapsed
            )
        
        result = response.result
        content = result.get("content", [])
        
        # Extrair texto do conteúdo
        text_content = ""
        for item in content:
            if item.get("type") == "text":
                text_content += item.get("text", "")
        
        return ToolResult(
            call_id=call.id,
            content=text_content or content,
            is_error=result.get("isError", False),
            duration_ms=elapsed
        )
    
    # ==================== Resources ====================
    
    async def list_resources(self, force_refresh: bool = False) -> list[MCPResource]:
        """
        Lista recursos disponíveis no server.
        
        Args:
            force_refresh: Forçar atualização do cache
            
        Returns:
            Lista de MCPResource
        """
        if self._resources and not force_refresh:
            return self._resources
        
        if not self.server.capabilities.resources:
            return []
        
        response = await self._request("resources/list")
        
        if response.error:
            raise MCPError(
                code=response.error.get("code"),
                message=response.error.get("message")
            )
        
        resources_data = response.result.get("resources", [])
        
        self._resources = [
            MCPResource.from_dict(r, self.server.id)
            for r in resources_data
        ]
        
        logger.debug(f"Descobertos {len(self._resources)} recursos")
        
        return self._resources
    
    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Lê conteúdo de um recurso.
        
        Args:
            uri: URI do recurso
            
        Returns:
            ResourceContent com dados
        """
        response = await self._request("resources/read", {
            "uri": uri
        })
        
        if response.error:
            raise MCPError(
                code=response.error.get("code"),
                message=response.error.get("message")
            )
        
        contents = response.result.get("contents", [])
        
        if not contents:
            return ResourceContent(uri=uri)
        
        content = contents[0]
        
        return ResourceContent(
            uri=content.get("uri", uri),
            mime_type=content.get("mimeType"),
            text=content.get("text"),
            blob=content.get("blob")
        )
    
    async def subscribe_resource(self, uri: str) -> bool:
        """
        Inscreve-se para atualizações de um recurso.
        
        Args:
            uri: URI do recurso
            
        Returns:
            True se inscrito com sucesso
        """
        if not self.server.capabilities.resources_subscribe:
            return False
        
        response = await self._request("resources/subscribe", {
            "uri": uri
        })
        
        return response.error is None
    
    # ==================== Prompts ====================
    
    async def list_prompts(self, force_refresh: bool = False) -> list[MCPPrompt]:
        """
        Lista prompts disponíveis no server.
        
        Args:
            force_refresh: Forçar atualização do cache
            
        Returns:
            Lista de MCPPrompt
        """
        if self._prompts and not force_refresh:
            return self._prompts
        
        if not self.server.capabilities.prompts:
            return []
        
        response = await self._request("prompts/list")
        
        if response.error:
            raise MCPError(
                code=response.error.get("code"),
                message=response.error.get("message")
            )
        
        prompts_data = response.result.get("prompts", [])
        
        self._prompts = [
            MCPPrompt.from_dict(p, self.server.id)
            for p in prompts_data
        ]
        
        logger.debug(f"Descobertos {len(self._prompts)} prompts")
        
        return self._prompts
    
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[dict] = None
    ) -> list[dict]:
        """
        Obtém mensagens de um prompt.
        
        Args:
            name: Nome do prompt
            arguments: Argumentos do prompt
            
        Returns:
            Lista de mensagens
        """
        response = await self._request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        if response.error:
            raise MCPError(
                code=response.error.get("code"),
                message=response.error.get("message")
            )
        
        return response.result.get("messages", [])
    
    # ==================== Utilities ====================
    
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self._initialized and self._transport is not None and self._transport.is_connected()
    
    def get_tools_for_llm(self) -> list[dict]:
        """
        Retorna ferramentas em formato compatível com OpenAI/Anthropic.
        
        Converte as ferramentas MCP para o formato de function calling
        usado por LLMs.
        """
        tools = []
        
        for tool in self._tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": f"{self.server.name}_{tool.name}",
                    "description": tool.description,
                    "parameters": tool.to_dict()["inputSchema"]
                }
            })
        
        return tools
    
    def get_metrics(self) -> dict:
        """Retorna métricas do client."""
        avg_latency = self.total_latency_ms / max(self.total_calls, 1)
        
        return {
            "server_name": self.server.name,
            "status": self.server.status.value,
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "success_rate": (self.total_calls - self.failed_calls) / max(self.total_calls, 1),
            "avg_latency_ms": avg_latency,
            "tools_count": len(self._tools),
            "resources_count": len(self._resources),
            "prompts_count": len(self._prompts)
        }


# Singleton registry para clients
_mcp_clients: dict[str, MCPClient] = {}


def get_mcp_client(server: MCPServer) -> MCPClient:
    """
    Retorna client MCP para um server.
    
    Reutiliza clients existentes baseado no ID do server.
    """
    if server.id not in _mcp_clients:
        _mcp_clients[server.id] = MCPClient(server)
    return _mcp_clients[server.id]


async def close_all_clients() -> None:
    """Fecha todos os clients MCP."""
    for client in _mcp_clients.values():
        await client.disconnect()
    _mcp_clients.clear()

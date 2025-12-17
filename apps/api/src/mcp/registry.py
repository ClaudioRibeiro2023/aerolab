"""
MCP Registry - Gerenciamento de servers MCP

Centraliza:
- Registro e descoberta de servers
- Gerenciamento de conexões
- Health checks
- Métricas agregadas
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging
import os

from .types import (
    MCPServer, MCPTool, MCPResource, MCPPrompt,
    ServerStatus, TransportType
)
from .client import MCPClient, get_mcp_client


logger = logging.getLogger(__name__)


# Servers MCP conhecidos/populares
KNOWN_SERVERS = {
    "github": {
        "name": "GitHub",
        "description": "Access GitHub repositories, issues, and PRs",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "transport": "stdio"
    },
    "slack": {
        "name": "Slack",
        "description": "Read and search Slack messages and channels",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
        "transport": "stdio"
    },
    "filesystem": {
        "name": "Filesystem",
        "description": "Read, write, and manage local files",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "transport": "stdio"
    },
    "postgres": {
        "name": "PostgreSQL",
        "description": "Query PostgreSQL databases",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env_vars": ["POSTGRES_CONNECTION_STRING"],
        "transport": "stdio"
    },
    "puppeteer": {
        "name": "Puppeteer",
        "description": "Browser automation and web scraping",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "transport": "stdio"
    },
    "brave-search": {
        "name": "Brave Search",
        "description": "Web search via Brave Search API",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env_vars": ["BRAVE_API_KEY"],
        "transport": "stdio"
    },
    "google-drive": {
        "name": "Google Drive",
        "description": "Access Google Drive files",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-gdrive"],
        "env_vars": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "transport": "stdio"
    },
    "memory": {
        "name": "Memory",
        "description": "Simple knowledge graph memory",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "transport": "stdio"
    }
}


class MCPRegistry:
    """
    Registry central para servers MCP.
    
    Gerencia:
    - Registro de servers
    - Conexões e reconexões
    - Descoberta de capabilities
    - Health monitoring
    - Agregação de tools/resources
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser("~/.agno/mcp_servers.json")
        
        # Servers registrados
        self._servers: dict[str, MCPServer] = {}
        
        # Clients ativos
        self._clients: dict[str, MCPClient] = {}
        
        # Cache agregado
        self._all_tools: list[MCPTool] = []
        self._all_resources: list[MCPResource] = []
        self._all_prompts: list[MCPPrompt] = []
        
        # Health check
        self._health_task: Optional[asyncio.Task] = None
        self._health_interval = 60  # segundos
        
        # Callbacks
        self._on_server_connected: Optional[Callable] = None
        self._on_server_disconnected: Optional[Callable] = None
        self._on_tools_changed: Optional[Callable] = None
    
    def set_callbacks(
        self,
        on_connected: Optional[Callable] = None,
        on_disconnected: Optional[Callable] = None,
        on_tools_changed: Optional[Callable] = None
    ) -> None:
        """Define callbacks para eventos."""
        self._on_server_connected = on_connected
        self._on_server_disconnected = on_disconnected
        self._on_tools_changed = on_tools_changed
    
    async def load_config(self) -> None:
        """Carrega configuração de servers do arquivo."""
        if not os.path.exists(self.config_path):
            logger.info("Arquivo de configuração MCP não encontrado")
            return
        
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            
            for server_config in config.get("servers", []):
                server = MCPServer(
                    id=server_config.get("id"),
                    name=server_config.get("name", ""),
                    description=server_config.get("description"),
                    transport=TransportType(server_config.get("transport", "stdio")),
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    url=server_config.get("url")
                )
                
                self._servers[server.id] = server
            
            logger.info(f"Carregados {len(self._servers)} servers MCP")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração MCP: {e}")
    
    async def save_config(self) -> None:
        """Salva configuração de servers no arquivo."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        config = {
            "servers": [
                {
                    "id": server.id,
                    "name": server.name,
                    "description": server.description,
                    "transport": server.transport.value,
                    "command": server.command,
                    "args": server.args,
                    "env": server.env,
                    "url": server.url
                }
                for server in self._servers.values()
            ]
        }
        
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuração MCP salva")
    
    def register_server(self, server: MCPServer) -> None:
        """
        Registra um server MCP.
        
        Args:
            server: Server a registrar
        """
        self._servers[server.id] = server
        logger.info(f"Server registrado: {server.name}")
    
    def register_known_server(
        self,
        server_key: str,
        env: Optional[dict[str, str]] = None
    ) -> Optional[MCPServer]:
        """
        Registra um server conhecido pelo key.
        
        Args:
            server_key: Key do server em KNOWN_SERVERS
            env: Variáveis de ambiente
            
        Returns:
            MCPServer criado ou None se não encontrado
        """
        if server_key not in KNOWN_SERVERS:
            logger.warning(f"Server desconhecido: {server_key}")
            return None
        
        config = KNOWN_SERVERS[server_key]
        
        server = MCPServer(
            name=config["name"],
            description=config.get("description"),
            transport=TransportType(config.get("transport", "stdio")),
            command=config.get("command"),
            args=config.get("args", []),
            env=env or {}
        )
        
        self.register_server(server)
        return server
    
    def unregister_server(self, server_id: str) -> bool:
        """
        Remove um server do registro.
        
        Args:
            server_id: ID do server
            
        Returns:
            True se removido
        """
        if server_id in self._servers:
            del self._servers[server_id]
            
            if server_id in self._clients:
                asyncio.create_task(self._clients[server_id].disconnect())
                del self._clients[server_id]
            
            logger.info(f"Server removido: {server_id}")
            return True
        
        return False
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Retorna server por ID."""
        return self._servers.get(server_id)
    
    def list_servers(self) -> list[MCPServer]:
        """Lista todos os servers registrados."""
        return list(self._servers.values())
    
    def list_connected_servers(self) -> list[MCPServer]:
        """Lista servers conectados."""
        return [
            server for server in self._servers.values()
            if server.status == ServerStatus.CONNECTED
        ]
    
    async def connect_server(self, server_id: str) -> bool:
        """
        Conecta a um server MCP.
        
        Args:
            server_id: ID do server
            
        Returns:
            True se conectado com sucesso
        """
        server = self._servers.get(server_id)
        if not server:
            logger.error(f"Server não encontrado: {server_id}")
            return False
        
        try:
            client = get_mcp_client(server)
            await client.connect()
            
            self._clients[server_id] = client
            
            # Atualizar cache de capabilities
            await self._refresh_capabilities(server_id)
            
            if self._on_server_connected:
                self._on_server_connected(server)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar server {server.name}: {e}")
            server.status = ServerStatus.ERROR
            return False
    
    async def disconnect_server(self, server_id: str) -> None:
        """Desconecta de um server MCP."""
        if server_id in self._clients:
            await self._clients[server_id].disconnect()
            del self._clients[server_id]
            
            server = self._servers.get(server_id)
            if server and self._on_server_disconnected:
                self._on_server_disconnected(server)
    
    async def connect_all(self) -> dict[str, bool]:
        """
        Conecta a todos os servers registrados.
        
        Returns:
            Dicionário com status de conexão por server
        """
        results = {}
        
        tasks = [
            self.connect_server(server_id)
            for server_id in self._servers.keys()
        ]
        
        server_ids = list(self._servers.keys())
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        
        for server_id, outcome in zip(server_ids, outcomes):
            if isinstance(outcome, Exception):
                results[server_id] = False
            else:
                results[server_id] = outcome
        
        return results
    
    async def disconnect_all(self) -> None:
        """Desconecta de todos os servers."""
        tasks = [
            self.disconnect_server(server_id)
            for server_id in list(self._clients.keys())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _refresh_capabilities(self, server_id: str) -> None:
        """Atualiza cache de capabilities de um server."""
        client = self._clients.get(server_id)
        if not client:
            return
        
        try:
            # Listar tools
            tools = await client.list_tools()
            
            # Remover tools antigas deste server
            self._all_tools = [t for t in self._all_tools if t.server_id != server_id]
            
            # Adicionar novas
            self._all_tools.extend(tools)
            
            # Listar resources
            resources = await client.list_resources()
            self._all_resources = [r for r in self._all_resources if r.server_id != server_id]
            self._all_resources.extend(resources)
            
            # Listar prompts
            prompts = await client.list_prompts()
            self._all_prompts = [p for p in self._all_prompts if p.server_id != server_id]
            self._all_prompts.extend(prompts)
            
            if self._on_tools_changed:
                self._on_tools_changed()
            
            logger.debug(f"Capabilities atualizadas para {server_id}: "
                        f"{len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar capabilities: {e}")
    
    # ==================== Tool Access ====================
    
    def get_all_tools(self) -> list[MCPTool]:
        """Retorna todas as tools de todos os servers conectados."""
        return self._all_tools.copy()
    
    def get_tool(self, name: str) -> Optional[tuple[MCPTool, MCPClient]]:
        """
        Busca uma tool pelo nome.
        
        Args:
            name: Nome da tool
            
        Returns:
            Tupla (tool, client) ou None
        """
        for tool in self._all_tools:
            if tool.name == name and tool.server_id:
                client = self._clients.get(tool.server_id)
                if client:
                    return (tool, client)
        return None
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[dict] = None
    ) -> Optional[str]:
        """
        Invoca uma tool pelo nome.
        
        Args:
            name: Nome da tool
            arguments: Argumentos
            
        Returns:
            Resultado da tool ou None se não encontrada
        """
        result = self.get_tool(name)
        if not result:
            return None
        
        tool, client = result
        tool_result = await client.call_tool(tool.name, arguments)
        
        if tool_result.is_error:
            return f"Error: {tool_result.error_message}"
        
        return str(tool_result.content)
    
    def get_tools_for_llm(self) -> list[dict]:
        """
        Retorna todas as tools em formato LLM.
        
        Converte para formato OpenAI/Anthropic function calling.
        """
        tools = []
        
        for tool in self._all_tools:
            if not tool.enabled:
                continue
            
            server = self._servers.get(tool.server_id) if tool.server_id else None
            prefix = server.name.lower().replace(" ", "_") if server else "mcp"
            
            tools.append({
                "type": "function",
                "function": {
                    "name": f"{prefix}_{tool.name}",
                    "description": tool.description,
                    "parameters": tool.to_dict()["inputSchema"]
                }
            })
        
        return tools
    
    # ==================== Resource Access ====================
    
    def get_all_resources(self) -> list[MCPResource]:
        """Retorna todos os resources de todos os servers."""
        return self._all_resources.copy()
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """
        Lê um resource pelo URI.
        
        Args:
            uri: URI do resource
            
        Returns:
            Conteúdo ou None se não encontrado
        """
        for resource in self._all_resources:
            if resource.uri == uri and resource.server_id:
                client = self._clients.get(resource.server_id)
                if client:
                    content = await client.read_resource(uri)
                    return content.text
        
        return None
    
    # ==================== Health Check ====================
    
    async def start_health_check(self) -> None:
        """Inicia task de health check."""
        if self._health_task is not None:
            return
        
        self._health_task = asyncio.create_task(self._health_check_loop())
    
    async def stop_health_check(self) -> None:
        """Para task de health check."""
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None
    
    async def _health_check_loop(self) -> None:
        """Loop de health check."""
        while True:
            try:
                await asyncio.sleep(self._health_interval)
                await self._check_all_servers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no health check: {e}")
    
    async def _check_all_servers(self) -> None:
        """Verifica saúde de todos os servers."""
        for server_id, client in list(self._clients.items()):
            server = self._servers.get(server_id)
            if not server:
                continue
            
            if not client.is_connected():
                server.status = ServerStatus.DISCONNECTED
                
                # Tentar reconectar
                server.status = ServerStatus.RECONNECTING
                try:
                    await client.connect()
                    server.status = ServerStatus.CONNECTED
                    await self._refresh_capabilities(server_id)
                except Exception:
                    server.status = ServerStatus.ERROR
    
    # ==================== Metrics ====================
    
    def get_metrics(self) -> dict:
        """Retorna métricas agregadas."""
        total_calls = sum(c.total_calls for c in self._clients.values())
        failed_calls = sum(c.failed_calls for c in self._clients.values())
        
        return {
            "servers_total": len(self._servers),
            "servers_connected": len([s for s in self._servers.values() 
                                     if s.status == ServerStatus.CONNECTED]),
            "tools_total": len(self._all_tools),
            "resources_total": len(self._all_resources),
            "prompts_total": len(self._all_prompts),
            "total_calls": total_calls,
            "failed_calls": failed_calls,
            "success_rate": (total_calls - failed_calls) / max(total_calls, 1)
        }
    
    def get_server_metrics(self) -> list[dict]:
        """Retorna métricas por server."""
        metrics = []
        
        for server_id, server in self._servers.items():
            client = self._clients.get(server_id)
            
            metrics.append({
                "server_id": server_id,
                "name": server.name,
                "status": server.status.value,
                "total_calls": server.total_calls,
                "error_count": server.error_count,
                "client_metrics": client.get_metrics() if client else None
            })
        
        return metrics


# Singleton
_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """Retorna o registry MCP singleton."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry

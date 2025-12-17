"""
MCP (Model Context Protocol) - Implementação Completa

O Model Context Protocol é um padrão aberto para conectar LLMs a
fontes de dados e ferramentas externas de forma padronizada.

Este módulo implementa:
- MCP Client: Conecta a servers MCP externos
- MCP Server: Expõe recursos da plataforma via MCP
- MCP Registry: Gerencia descoberta e conexão de servers
- MCP Tools: Ferramentas internas expostas via MCP

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                     AGNO Platform                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ MCP Client  │  │ MCP Server  │  │ MCP Registry│         │
│  │             │  │             │  │             │         │
│  │ - connect() │  │ - tools[]   │  │ - discover()│         │
│  │ - invoke()  │  │ - resources │  │ - register()│         │
│  │ - stream()  │  │ - prompts   │  │ - health()  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Transport │                           │
│                    │  (stdio/   │                           │
│                    │   HTTP)    │                           │
│                    └─────┬─────┘                            │
└──────────────────────────┼──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
    │ GitHub  │      │ Slack   │      │ Custom  │
    │ Server  │      │ Server  │      │ Servers │
    └─────────┘      └─────────┘      └─────────┘
"""

from .types import (
    MCPServer,
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPMessage,
    MCPError,
    MCPCapabilities,
    ToolCall,
    ToolResult,
    ResourceContent,
    ServerStatus
)
from .client import MCPClient, get_mcp_client
from .server import MCPServerBase, AgnoMCPServer
from .registry import MCPRegistry, get_mcp_registry
from .transports import StdioTransport, HTTPTransport, SSETransport

__all__ = [
    # Types
    "MCPServer",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPMessage",
    "MCPError",
    "MCPCapabilities",
    "ToolCall",
    "ToolResult",
    "ResourceContent",
    "ServerStatus",
    # Client
    "MCPClient",
    "get_mcp_client",
    # Server
    "MCPServerBase",
    "AgnoMCPServer",
    # Registry
    "MCPRegistry",
    "get_mcp_registry",
    # Transports
    "StdioTransport",
    "HTTPTransport",
    "SSETransport"
]

__version__ = "2.0.0"

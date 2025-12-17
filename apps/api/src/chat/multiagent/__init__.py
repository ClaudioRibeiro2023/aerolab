"""
Multi-Agent Chat - Suporte a múltiplos agentes e MCP.

Features:
- Routing inteligente
- Agent handoff
- MCP integration
- Computer use
"""

from .routing import AgentRouter, RoutingStrategy
from .handoff import AgentHandoff, HandoffContext
from .mcp_bridge import MCPBridge

__all__ = [
    "AgentRouter",
    "RoutingStrategy",
    "AgentHandoff",
    "HandoffContext",
    "MCPBridge",
]

"""
Base classes para ferramentas customizadas.
"""

from .tool import BaseTool, ToolResult, ToolError, ToolRegistry, get_tool_registry, register_tool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolError",
    "ToolRegistry",
    "get_tool_registry",
    "register_tool",
]

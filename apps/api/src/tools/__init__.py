"""
Módulo de ferramentas customizadas para agentes.

Estrutura:
- base/: Classes base (BaseTool, ToolResult, ToolRegistry)
- geo/: Ferramentas de geolocalização
- database/: Ferramentas de banco de dados
- devops/: Ferramentas de desenvolvimento
- finance/: Ferramentas financeiras
- legal/: Ferramentas jurídicas
- corporate/: Ferramentas corporativas
- slack: Integração com Slack
- notion: Integração com Notion
"""

from .base import BaseTool, ToolResult, ToolError
from .slack import SlackTool, get_slack_tool
from .notion import NotionTool, get_notion_tool, notion_property
from .gmail import GmailTool, get_gmail_tool
from .google_calendar import GoogleCalendarTool, get_google_calendar_tool
from .zapier import ZapierTool, get_zapier_tool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolError",
    # Integrações
    "SlackTool",
    "get_slack_tool",
    "NotionTool",
    "get_notion_tool",
    "notion_property",
    "GmailTool",
    "get_gmail_tool",
    "GoogleCalendarTool",
    "get_google_calendar_tool",
    "ZapierTool",
    "get_zapier_tool",
]

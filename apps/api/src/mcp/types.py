"""
MCP Types - Definições de tipos para o Model Context Protocol

Baseado na especificação oficial do MCP:
https://spec.modelcontextprotocol.io/specification/
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union, Literal
from enum import Enum
import uuid


class ServerStatus(str, Enum):
    """Status de conexão do server."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class TransportType(str, Enum):
    """Tipos de transporte suportados."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    WEBSOCKET = "websocket"


class ResourceType(str, Enum):
    """Tipos de recursos MCP."""
    TEXT = "text"
    BLOB = "blob"
    JSON = "json"


class MessageRole(str, Enum):
    """Papéis de mensagens."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class MCPCapabilities:
    """
    Capacidades declaradas por um server MCP.
    
    Define quais features o server suporta.
    """
    # Recursos
    resources: bool = False
    resources_subscribe: bool = False
    resources_list_changed: bool = False
    
    # Ferramentas
    tools: bool = False
    tools_list_changed: bool = False
    
    # Prompts
    prompts: bool = False
    prompts_list_changed: bool = False
    
    # Logging
    logging: bool = False
    
    # Experimental
    experimental: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Converte para dicionário MCP."""
        caps = {}
        
        if self.resources:
            caps["resources"] = {
                "subscribe": self.resources_subscribe,
                "listChanged": self.resources_list_changed
            }
        
        if self.tools:
            caps["tools"] = {
                "listChanged": self.tools_list_changed
            }
        
        if self.prompts:
            caps["prompts"] = {
                "listChanged": self.prompts_list_changed
            }
        
        if self.logging:
            caps["logging"] = {}
        
        if self.experimental:
            caps["experimental"] = self.experimental
        
        return caps
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPCapabilities":
        """Cria MCPCapabilities a partir de dicionário."""
        resources = data.get("resources", {})
        tools = data.get("tools", {})
        prompts = data.get("prompts", {})
        
        return cls(
            resources=bool(resources),
            resources_subscribe=resources.get("subscribe", False) if resources else False,
            resources_list_changed=resources.get("listChanged", False) if resources else False,
            tools=bool(tools),
            tools_list_changed=tools.get("listChanged", False) if tools else False,
            prompts=bool(prompts),
            prompts_list_changed=prompts.get("listChanged", False) if prompts else False,
            logging=bool(data.get("logging")),
            experimental=data.get("experimental", {})
        )


@dataclass
class MCPServer:
    """
    Representação de um server MCP.
    
    Um server MCP pode expor:
    - Tools: Funções executáveis
    - Resources: Dados/conteúdo acessível
    - Prompts: Templates de prompts pré-definidos
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Conexão
    transport: TransportType = TransportType.STDIO
    command: Optional[str] = None  # Para stdio
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None  # Para HTTP/SSE
    
    # Estado
    status: ServerStatus = ServerStatus.DISCONNECTED
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)
    
    # Metadados
    icon: Optional[str] = None
    vendor: Optional[str] = None
    homepage: Optional[str] = None
    
    # Timestamps
    connected_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Estatísticas
    total_calls: int = 0
    error_count: int = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "transport": self.transport.value,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "url": self.url,
            "status": self.status.value,
            "capabilities": self.capabilities.to_dict(),
            "icon": self.icon,
            "vendor": self.vendor,
            "homepage": self.homepage
        }


@dataclass
class ToolParameter:
    """Parâmetro de uma ferramenta MCP."""
    name: str
    type: str  # string, number, boolean, object, array
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[list] = None
    
    def to_json_schema(self) -> dict:
        """Converte para JSON Schema."""
        schema = {"type": self.type}
        
        if self.description:
            schema["description"] = self.description
        if self.default is not None:
            schema["default"] = self.default
        if self.enum:
            schema["enum"] = self.enum
        
        return schema


@dataclass
class MCPTool:
    """
    Ferramenta MCP executável.
    
    Tools são funções que o LLM pode invocar através
    do server MCP para realizar ações.
    """
    name: str
    description: str = ""
    parameters: list[ToolParameter] = field(default_factory=list)
    
    # Metadados
    server_id: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    
    # Estado
    enabled: bool = True
    requires_confirmation: bool = False
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        # Construir JSON Schema para input
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        input_schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            input_schema["required"] = required
        
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": input_schema
        }
    
    @classmethod
    def from_dict(cls, data: dict, server_id: Optional[str] = None) -> "MCPTool":
        """Cria MCPTool a partir de dicionário MCP."""
        parameters = []
        input_schema = data.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        for name, prop in properties.items():
            parameters.append(ToolParameter(
                name=name,
                type=prop.get("type", "string"),
                description=prop.get("description"),
                required=name in required,
                default=prop.get("default"),
                enum=prop.get("enum")
            ))
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=parameters,
            server_id=server_id
        )


@dataclass
class MCPResource:
    """
    Recurso MCP acessível.
    
    Resources são fontes de dados que o LLM pode
    ler através do server MCP.
    """
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    
    # Metadados
    server_id: Optional[str] = None
    size: Optional[int] = None
    
    # Estado
    subscribed: bool = False
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        result = {
            "uri": self.uri,
            "name": self.name
        }
        
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict, server_id: Optional[str] = None) -> "MCPResource":
        """Cria MCPResource a partir de dicionário MCP."""
        return cls(
            uri=data.get("uri", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            mime_type=data.get("mimeType"),
            server_id=server_id
        )


@dataclass
class ResourceContent:
    """Conteúdo de um recurso MCP."""
    uri: str
    mime_type: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[bytes] = None
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        result = {"uri": self.uri}
        
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            import base64
            result["blob"] = base64.b64encode(self.blob).decode()
        
        return result


@dataclass
class PromptArgument:
    """Argumento de um prompt MCP."""
    name: str
    description: Optional[str] = None
    required: bool = False


@dataclass
class MCPPrompt:
    """
    Prompt MCP pré-definido.
    
    Prompts são templates que podem ser usados
    para guiar a interação com o LLM.
    """
    name: str
    description: Optional[str] = None
    arguments: list[PromptArgument] = field(default_factory=list)
    
    # Metadados
    server_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        result = {"name": self.name}
        
        if self.description:
            result["description"] = self.description
        
        if self.arguments:
            result["arguments"] = [
                {
                    "name": arg.name,
                    "description": arg.description,
                    "required": arg.required
                }
                for arg in self.arguments
            ]
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict, server_id: Optional[str] = None) -> "MCPPrompt":
        """Cria MCPPrompt a partir de dicionário MCP."""
        arguments = [
            PromptArgument(
                name=arg.get("name", ""),
                description=arg.get("description"),
                required=arg.get("required", False)
            )
            for arg in data.get("arguments", [])
        ]
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            arguments=arguments,
            server_id=server_id
        )


@dataclass
class PromptMessage:
    """Mensagem de um prompt MCP."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        return {
            "role": self.role.value,
            "content": {"type": "text", "text": self.content}
        }


@dataclass
class MCPMessage:
    """
    Mensagem do protocolo MCP.
    
    Usa formato JSON-RPC 2.0.
    """
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[dict] = None
    result: Optional[Any] = None
    error: Optional[dict] = None
    
    def is_request(self) -> bool:
        """Verifica se é uma requisição."""
        return self.method is not None
    
    def is_response(self) -> bool:
        """Verifica se é uma resposta."""
        return self.result is not None or self.error is not None
    
    def is_notification(self) -> bool:
        """Verifica se é uma notificação (sem id)."""
        return self.method is not None and self.id is None
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        msg = {"jsonrpc": self.jsonrpc}
        
        if self.id is not None:
            msg["id"] = self.id
        if self.method is not None:
            msg["method"] = self.method
        if self.params is not None:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        
        return msg
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPMessage":
        """Cria MCPMessage a partir de dicionário."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )
    
    @classmethod
    def request(cls, method: str, params: Optional[dict] = None, id: Optional[Union[str, int]] = None) -> "MCPMessage":
        """Cria uma requisição."""
        return cls(
            id=id or str(uuid.uuid4()),
            method=method,
            params=params
        )
    
    @classmethod
    def response(cls, id: Union[str, int], result: Any) -> "MCPMessage":
        """Cria uma resposta de sucesso."""
        return cls(id=id, result=result)
    
    @classmethod
    def error_response(cls, id: Union[str, int], code: int, message: str, data: Any = None) -> "MCPMessage":
        """Cria uma resposta de erro."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return cls(id=id, error=error)
    
    @classmethod
    def notification(cls, method: str, params: Optional[dict] = None) -> "MCPMessage":
        """Cria uma notificação (sem resposta esperada)."""
        return cls(method=method, params=params)


@dataclass
class MCPError(Exception):
    """Erro do protocolo MCP."""
    code: int
    message: str
    data: Optional[Any] = None
    
    # Códigos de erro padrão JSON-RPC
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Códigos de erro MCP específicos
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR = -32001
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error
    
    def __str__(self) -> str:
        return f"MCPError({self.code}): {self.message}"


@dataclass
class ToolCall:
    """
    Chamada de ferramenta.
    
    Representa uma invocação de tool pelo LLM.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    
    # Contexto
    server_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Estado
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "server_id": self.server_id,
            "status": self.status
        }


@dataclass
class ToolResult:
    """
    Resultado de uma chamada de ferramenta.
    """
    call_id: str
    content: Any
    is_error: bool = False
    error_message: Optional[str] = None
    
    # Metadados
    duration_ms: float = 0
    
    def to_dict(self) -> dict:
        """Converte para formato MCP."""
        result = {
            "content": [
                {"type": "text", "text": str(self.content)}
            ]
        }
        
        if self.is_error:
            result["isError"] = True
        
        return result
    
    def to_content_list(self) -> list[dict]:
        """Converte para lista de conteúdos MCP."""
        if isinstance(self.content, str):
            return [{"type": "text", "text": self.content}]
        elif isinstance(self.content, dict):
            return [{"type": "text", "text": str(self.content)}]
        elif isinstance(self.content, list):
            return self.content
        else:
            return [{"type": "text", "text": str(self.content)}]


@dataclass
class ServerInfo:
    """Informações do server retornadas no initialize."""
    name: str
    version: str
    protocol_version: str = "2024-11-05"
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "version": self.version,
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities.to_dict()
        }


@dataclass
class ClientInfo:
    """Informações do client enviadas no initialize."""
    name: str = "Agno Platform"
    version: str = "2.0.0"
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "version": self.version
        }

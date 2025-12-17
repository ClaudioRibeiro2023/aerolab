"""
Agno SDK - Client

Cliente HTTP para conectar à API da plataforma Agno.
Permite usar agentes remotos e acessar recursos da plataforma.

Uso:
```python
from agno import AgnoClient

# Conectar à plataforma
client = AgnoClient(
    api_key="your-api-key",
    base_url="https://api.agno.ai"
)

# Listar agentes
agents = client.agents.list()

# Executar agente remoto
response = client.agents.run("assistant", "Hello!")

# Buscar documentos
results = client.rag.search("AI trends")

# Gerenciar memórias
memories = client.memory.search("important info")
```
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, AsyncIterator
import logging
import os

import aiohttp

from .types import Response, StreamChunk, Context, Usage, ResponseStatus


logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """
    Configuração do cliente.
    
    Attributes:
        api_key: Chave de API
        base_url: URL base da API
        timeout: Timeout em segundos
    """
    api_key: str = ""
    base_url: str = "http://localhost:8000"
    timeout: float = 120.0
    max_retries: int = 3


class AgentsClient:
    """Cliente para endpoints de agentes."""
    
    def __init__(self, client: "AgnoClient"):
        self._client = client
    
    async def list(self, project_id: Optional[int] = None) -> list[dict]:
        """Lista agentes disponíveis."""
        params = {}
        if project_id:
            params["project_id"] = project_id
        
        return await self._client._get("/agents", params=params)
    
    async def get(self, agent_id: str) -> dict:
        """Obtém detalhes de um agente."""
        return await self._client._get(f"/agents/{agent_id}")
    
    async def create(
        self,
        name: str,
        model: str = "gpt-4o",
        instructions: str = "",
        **kwargs
    ) -> dict:
        """Cria um novo agente."""
        data = {
            "name": name,
            "model": model,
            "instructions": instructions,
            **kwargs
        }
        return await self._client._post("/agents", data=data)
    
    async def run(
        self,
        agent_id: str,
        message: str,
        context: Optional[dict] = None
    ) -> Response:
        """
        Executa um agente.
        
        Args:
            agent_id: ID ou nome do agente
            message: Mensagem do usuário
            context: Contexto opcional
            
        Returns:
            Response com resultado
        """
        data = {
            "message": message,
            "context": context or {}
        }
        
        result = await self._client._post(f"/agents/{agent_id}/run", data=data)
        
        return Response(
            content=result.get("content", ""),
            status=ResponseStatus.SUCCESS if not result.get("error") else ResponseStatus.ERROR,
            error=result.get("error"),
            usage=Usage(
                prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
                total_tokens=result.get("usage", {}).get("total_tokens", 0)
            )
        )
    
    async def stream(
        self,
        agent_id: str,
        message: str,
        context: Optional[dict] = None
    ) -> AsyncIterator[StreamChunk]:
        """
        Executa agente com streaming.
        
        Args:
            agent_id: ID ou nome do agente
            message: Mensagem do usuário
            context: Contexto opcional
            
        Yields:
            StreamChunk com deltas
        """
        data = {
            "message": message,
            "context": context or {},
            "stream": True
        }
        
        async for chunk in self._client._stream(f"/agents/{agent_id}/run", data=data):
            yield StreamChunk(
                content=chunk.get("content", ""),
                delta=chunk.get("delta", ""),
                finish_reason=chunk.get("finish_reason")
            )


class RAGClient:
    """Cliente para endpoints de RAG."""
    
    def __init__(self, client: "AgnoClient"):
        self._client = client
    
    async def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Busca documentos.
        
        Args:
            query: Query de busca
            project_id: ID do projeto
            limit: Limite de resultados
            
        Returns:
            Lista de documentos encontrados
        """
        data = {
            "query": query,
            "project_id": project_id,
            "limit": limit
        }
        
        return await self._client._post("/rag/search", data=data)
    
    async def ingest(
        self,
        title: str,
        content: str,
        project_id: int,
        **kwargs
    ) -> dict:
        """
        Ingere um documento.
        
        Args:
            title: Título do documento
            content: Conteúdo
            project_id: ID do projeto
            
        Returns:
            Resultado da ingestão
        """
        data = {
            "title": title,
            "content": content,
            "project_id": project_id,
            **kwargs
        }
        
        return await self._client._post("/rag/ingest", data=data)
    
    async def get_document(self, document_id: int) -> dict:
        """Obtém um documento."""
        return await self._client._get(f"/rag/documents/{document_id}")


class MemoryClient:
    """Cliente para endpoints de memória."""
    
    def __init__(self, client: "AgnoClient"):
        self._client = client
    
    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Busca memórias.
        
        Args:
            query: Query de busca
            agent_id: Filtrar por agente
            limit: Limite de resultados
            
        Returns:
            Lista de memórias
        """
        data = {
            "query": query,
            "agent_id": agent_id,
            "limit": limit
        }
        
        return await self._client._post("/memory/search", data=data)
    
    async def store(
        self,
        content: str,
        agent_id: Optional[str] = None,
        importance: float = 0.5
    ) -> dict:
        """
        Armazena uma memória.
        
        Args:
            content: Conteúdo
            agent_id: ID do agente
            importance: Importância (0-1)
            
        Returns:
            Memória criada
        """
        data = {
            "content": content,
            "agent_id": agent_id,
            "importance": importance
        }
        
        return await self._client._post("/memory/store", data=data)
    
    async def get_context(
        self,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> dict:
        """Obtém contexto de sessão."""
        params = {"session_id": session_id}
        if agent_id:
            params["agent_id"] = agent_id
        
        return await self._client._get("/memory/context", params=params)


class ToolsClient:
    """Cliente para endpoints de ferramentas."""
    
    def __init__(self, client: "AgnoClient"):
        self._client = client
    
    async def list(self) -> list[dict]:
        """Lista ferramentas disponíveis."""
        return await self._client._get("/tools")
    
    async def execute(
        self,
        tool_name: str,
        arguments: dict
    ) -> dict:
        """
        Executa uma ferramenta.
        
        Args:
            tool_name: Nome da ferramenta
            arguments: Argumentos
            
        Returns:
            Resultado da execução
        """
        data = {
            "tool": tool_name,
            "arguments": arguments
        }
        
        return await self._client._post("/tools/execute", data=data)


class MCPClient:
    """Cliente para endpoints MCP."""
    
    def __init__(self, client: "AgnoClient"):
        self._client = client
    
    async def list_servers(self) -> list[dict]:
        """Lista servers MCP conectados."""
        return await self._client._get("/mcp/servers")
    
    async def list_tools(self, server_id: Optional[str] = None) -> list[dict]:
        """Lista tools MCP."""
        params = {}
        if server_id:
            params["server_id"] = server_id
        
        return await self._client._get("/mcp/tools", params=params)
    
    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict
    ) -> dict:
        """
        Chama uma tool MCP.
        
        Args:
            server_id: ID do server
            tool_name: Nome da tool
            arguments: Argumentos
            
        Returns:
            Resultado
        """
        data = {
            "server_id": server_id,
            "tool": tool_name,
            "arguments": arguments
        }
        
        return await self._client._post("/mcp/call", data=data)


class AgnoClient:
    """
    Cliente principal da API Agno.
    
    Fornece acesso a todos os recursos da plataforma.
    
    Uso:
    ```python
    client = AgnoClient(api_key="your-key")
    
    # Agentes
    agents = await client.agents.list()
    response = await client.agents.run("assistant", "Hello!")
    
    # RAG
    results = await client.rag.search("query")
    
    # Memória
    memories = await client.memory.search("info")
    
    # Tools
    tools = await client.tools.list()
    
    # MCP
    servers = await client.mcp.list_servers()
    ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[ClientConfig] = None
    ):
        if config:
            self.config = config
        else:
            self.config = ClientConfig(
                api_key=api_key or os.getenv("AGNO_API_KEY", ""),
                base_url=base_url or os.getenv("AGNO_API_URL", "http://localhost:8000")
            )
        
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Sub-clients
        self.agents = AgentsClient(self)
        self.rag = RAGClient(self)
        self.memory = MemoryClient(self)
        self.tools = ToolsClient(self)
        self.mcp = MCPClient(self)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtém ou cria sessão HTTP."""
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        
        return self._session
    
    async def _get(
        self,
        path: str,
        params: Optional[dict] = None
    ) -> Any:
        """Faz requisição GET."""
        session = await self._get_session()
        url = f"{self.config.base_url}{path}"
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _post(
        self,
        path: str,
        data: Optional[dict] = None
    ) -> Any:
        """Faz requisição POST."""
        session = await self._get_session()
        url = f"{self.config.base_url}{path}"
        
        async with session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _stream(
        self,
        path: str,
        data: Optional[dict] = None
    ) -> AsyncIterator[dict]:
        """Faz requisição com streaming."""
        session = await self._get_session()
        url = f"{self.config.base_url}{path}"
        
        async with session.post(url, json=data) as response:
            response.raise_for_status()
            
            async for line in response.content:
                line = line.decode().strip()
                
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str:
                        yield json.loads(data_str)
    
    async def health(self) -> dict:
        """Verifica saúde da API."""
        return await self._get("/health")
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    # Context manager
    
    async def __aenter__(self) -> "AgnoClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


# Factory function
def create_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> AgnoClient:
    """Cria cliente Agno."""
    return AgnoClient(api_key=api_key, base_url=base_url)

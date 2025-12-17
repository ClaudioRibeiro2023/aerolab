"""
MCP Transports - Camadas de transporte para comunicação MCP

Implementa os transportes suportados:
- stdio: Comunicação via stdin/stdout (processo local)
- HTTP: Comunicação via HTTP POST
- SSE: Server-Sent Events para streaming
"""

import asyncio
import json
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Callable, Any
import logging
import aiohttp
from datetime import datetime

from .types import MCPMessage, MCPError


logger = logging.getLogger(__name__)


class Transport(ABC):
    """
    Interface base para transportes MCP.
    
    Cada transporte implementa como enviar e receber
    mensagens JSON-RPC entre client e server.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Estabelece conexão."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Encerra conexão."""
        pass
    
    @abstractmethod
    async def send(self, message: MCPMessage) -> None:
        """Envia mensagem."""
        pass
    
    @abstractmethod
    async def receive(self) -> Optional[MCPMessage]:
        """Recebe próxima mensagem."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        pass


class StdioTransport(Transport):
    """
    Transporte stdio para servers MCP locais.
    
    Comunica com um processo filho via stdin/stdout.
    Formato de mensagem: JSON lines separados por newline.
    """
    
    def __init__(
        self,
        command: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[str] = None
    ):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd
        
        self._process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._read_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue[MCPMessage] = asyncio.Queue()
        self._on_message: Optional[Callable[[MCPMessage], None]] = None
    
    def set_message_handler(self, handler: Callable[[MCPMessage], None]) -> None:
        """Define handler para mensagens recebidas."""
        self._on_message = handler
    
    async def connect(self) -> None:
        """Inicia o processo e estabelece comunicação."""
        if self._connected:
            return
        
        import os
        
        # Preparar ambiente
        env = os.environ.copy()
        env.update(self.env)
        
        # Iniciar processo
        try:
            self._process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.cwd
            )
            
            self._connected = True
            
            # Iniciar task de leitura
            self._read_task = asyncio.create_task(self._read_loop())
            
            logger.info(f"StdioTransport conectado: {self.command}")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar processo: {e}")
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message=f"Failed to start process: {e}"
            )
    
    async def disconnect(self) -> None:
        """Encerra o processo."""
        self._connected = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            except Exception:
                pass
            
            self._process = None
        
        logger.info("StdioTransport desconectado")
    
    async def send(self, message: MCPMessage) -> None:
        """Envia mensagem via stdin."""
        if not self._connected or not self._process or not self._process.stdin:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message="Not connected"
            )
        
        try:
            data = json.dumps(message.to_dict())
            self._process.stdin.write(f"{data}\n".encode())
            await self._process.stdin.drain()
            
            logger.debug(f"Sent: {message.method or 'response'}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message=f"Failed to send message: {e}"
            )
    
    async def receive(self) -> Optional[MCPMessage]:
        """Recebe próxima mensagem da fila."""
        try:
            message = await asyncio.wait_for(
                self._message_queue.get(),
                timeout=30.0
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def _read_loop(self) -> None:
        """Loop de leitura do stdout."""
        if not self._process or not self._process.stdout:
            return
        
        try:
            while self._connected:
                line = await self._process.stdout.readline()
                
                if not line:
                    break
                
                try:
                    data = json.loads(line.decode().strip())
                    message = MCPMessage.from_dict(data)
                    
                    await self._message_queue.put(message)
                    
                    if self._on_message:
                        self._on_message(message)
                    
                    logger.debug(f"Received: {message.method or 'response'}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {line}")
                    continue
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Erro no read loop: {e}")
            self._connected = False
    
    def is_connected(self) -> bool:
        """Verifica se processo está rodando."""
        return (
            self._connected and 
            self._process is not None and 
            self._process.returncode is None
        )


class HTTPTransport(Transport):
    """
    Transporte HTTP para servers MCP remotos.
    
    Cada mensagem é enviada como POST request.
    Respostas são retornadas no body da resposta HTTP.
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Cria sessão HTTP."""
        if self._connected:
            return
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        default_headers.update(self.headers)
        
        self._session = aiohttp.ClientSession(
            headers=default_headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
        self._connected = True
        logger.info(f"HTTPTransport conectado: {self.url}")
    
    async def disconnect(self) -> None:
        """Fecha sessão HTTP."""
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        logger.info("HTTPTransport desconectado")
    
    async def send(self, message: MCPMessage) -> None:
        """
        Envia mensagem via HTTP POST.
        
        Nota: Para HTTP, send e receive são combinados
        em uma única operação request/response.
        """
        # HTTP transport usa send_and_receive
        pass
    
    async def receive(self) -> Optional[MCPMessage]:
        """
        HTTP não tem receive separado.
        Use send_and_receive.
        """
        return None
    
    async def send_and_receive(self, message: MCPMessage) -> MCPMessage:
        """
        Envia mensagem e aguarda resposta.
        
        Para HTTP, toda comunicação é request/response.
        """
        if not self._connected or not self._session:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message="Not connected"
            )
        
        try:
            async with self._session.post(
                f"{self.url}/mcp",
                json=message.to_dict()
            ) as response:
                
                if response.status != 200:
                    text = await response.text()
                    raise MCPError(
                        code=MCPError.INTERNAL_ERROR,
                        message=f"HTTP {response.status}: {text}"
                    )
                
                data = await response.json()
                return MCPMessage.from_dict(data)
                
        except aiohttp.ClientError as e:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message=f"HTTP error: {e}"
            )
    
    def is_connected(self) -> bool:
        """Verifica se sessão está ativa."""
        return self._connected and self._session is not None


class SSETransport(Transport):
    """
    Transporte Server-Sent Events para streaming.
    
    Usa HTTP POST para enviar mensagens e SSE para receber.
    Ideal para comunicação assíncrona e streaming de resultados.
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._sse_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue[MCPMessage] = asyncio.Queue()
        self._pending_requests: dict[str, asyncio.Future] = {}
    
    async def connect(self) -> None:
        """Estabelece conexão SSE."""
        if self._connected:
            return
        
        default_headers = {
            "Accept": "text/event-stream"
        }
        default_headers.update(self.headers)
        
        self._session = aiohttp.ClientSession(
            headers=default_headers
        )
        
        # Iniciar listener SSE
        self._sse_task = asyncio.create_task(self._sse_listener())
        
        self._connected = True
        logger.info(f"SSETransport conectado: {self.url}")
    
    async def disconnect(self) -> None:
        """Encerra conexão SSE."""
        self._connected = False
        
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.close()
            self._session = None
        
        # Cancelar requests pendentes
        for future in self._pending_requests.values():
            future.cancel()
        self._pending_requests.clear()
        
        logger.info("SSETransport desconectado")
    
    async def send(self, message: MCPMessage) -> None:
        """Envia mensagem via HTTP POST."""
        if not self._connected or not self._session:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message="Not connected"
            )
        
        try:
            headers = {"Content-Type": "application/json"}
            
            async with self._session.post(
                f"{self.url}/message",
                json=message.to_dict(),
                headers=headers
            ) as response:
                
                if response.status != 200 and response.status != 202:
                    text = await response.text()
                    raise MCPError(
                        code=MCPError.INTERNAL_ERROR,
                        message=f"HTTP {response.status}: {text}"
                    )
                    
        except aiohttp.ClientError as e:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message=f"HTTP error: {e}"
            )
    
    async def receive(self) -> Optional[MCPMessage]:
        """Recebe próxima mensagem da fila SSE."""
        try:
            message = await asyncio.wait_for(
                self._message_queue.get(),
                timeout=60.0
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def send_and_receive(
        self,
        message: MCPMessage,
        timeout: float = 30.0
    ) -> MCPMessage:
        """Envia mensagem e aguarda resposta via SSE."""
        if message.id is None:
            raise MCPError(
                code=MCPError.INVALID_REQUEST,
                message="Message must have an id"
            )
        
        # Criar future para resposta
        future: asyncio.Future[MCPMessage] = asyncio.Future()
        self._pending_requests[str(message.id)] = future
        
        try:
            # Enviar mensagem
            await self.send(message)
            
            # Aguardar resposta
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            raise MCPError(
                code=MCPError.INTERNAL_ERROR,
                message=f"Request timeout after {timeout}s"
            )
        finally:
            self._pending_requests.pop(str(message.id), None)
    
    async def _sse_listener(self) -> None:
        """Listener para eventos SSE."""
        if not self._session:
            return
        
        try:
            async with self._session.get(f"{self.url}/events") as response:
                async for line in response.content:
                    if not self._connected:
                        break
                    
                    line = line.decode().strip()
                    
                    if not line or line.startswith(":"):
                        continue
                    
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        
                        try:
                            data = json.loads(data_str)
                            message = MCPMessage.from_dict(data)
                            
                            # Se é resposta a request pendente
                            if message.id and str(message.id) in self._pending_requests:
                                future = self._pending_requests[str(message.id)]
                                if not future.done():
                                    future.set_result(message)
                            else:
                                # Colocar na fila geral
                                await self._message_queue.put(message)
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid SSE data: {data_str}")
                            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE listener error: {e}")
            self._connected = False
    
    def is_connected(self) -> bool:
        """Verifica se conexão SSE está ativa."""
        return self._connected


class TransportFactory:
    """Factory para criar transportes."""
    
    @staticmethod
    def create(
        transport_type: str,
        **kwargs
    ) -> Transport:
        """
        Cria transporte baseado no tipo.
        
        Args:
            transport_type: "stdio", "http", ou "sse"
            **kwargs: Argumentos específicos do transporte
            
        Returns:
            Instância do transporte
        """
        if transport_type == "stdio":
            return StdioTransport(
                command=kwargs.get("command", ""),
                args=kwargs.get("args", []),
                env=kwargs.get("env", {}),
                cwd=kwargs.get("cwd")
            )
        elif transport_type == "http":
            return HTTPTransport(
                url=kwargs.get("url", ""),
                headers=kwargs.get("headers"),
                timeout=kwargs.get("timeout", 30.0)
            )
        elif transport_type == "sse":
            return SSETransport(
                url=kwargs.get("url", ""),
                headers=kwargs.get("headers")
            )
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

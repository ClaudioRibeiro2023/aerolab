"""
Agno SDK - Agent

Classe principal para criar e executar agentes de IA.

Uso:
```python
from agno import Agent

agent = Agent(
    name="assistant",
    model="gpt-4o",
    instructions="You are a helpful assistant."
)

response = agent.run("Hello!")
print(response.content)
```
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, AsyncIterator, Union
import logging
import os

from openai import AsyncOpenAI

from .types import (
    Message, MessageRole, Response, StreamChunk,
    Context, AgentState, Usage, ToolCall, ResponseStatus
)
from .tool import Tool, FunctionTool, ToolRegistry, ToolResult


logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """
    Configuração do agente.
    
    Attributes:
        name: Nome do agente
        model: Modelo LLM a usar
        instructions: Instruções de sistema
        tools: Lista de ferramentas
        temperature: Temperatura de geração
        max_tokens: Máximo de tokens
        max_iterations: Máximo de iterações de tool calling
    """
    name: str = "agent"
    model: str = "gpt-4o"
    instructions: str = "You are a helpful AI assistant."
    
    # Tools
    tools: list[Tool] = field(default_factory=list)
    
    # Parâmetros de geração
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # Comportamento
    max_iterations: int = 10  # Máximo de ciclos de tool calling
    timeout: float = 120.0  # Timeout em segundos
    
    # API
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class Agent:
    """
    Agente de IA com capacidade de usar ferramentas.
    
    O Agent gerencia:
    - Comunicação com LLM
    - Execução de ferramentas
    - Histórico de mensagens
    - Contexto de sessão
    
    Uso:
    ```python
    agent = Agent(
        name="researcher",
        model="gpt-4o",
        instructions="You are a research assistant.",
        tools=[search_tool]
    )
    
    # Execução simples
    response = agent.run("Search for AI trends")
    
    # Com streaming
    for chunk in agent.stream("Tell me about AI"):
        print(chunk, end="")
    
    # Async
    response = await agent.arun("Hello")
    ```
    """
    
    def __init__(
        self,
        name: str = "agent",
        model: str = "gpt-4o",
        instructions: str = "You are a helpful AI assistant.",
        tools: Optional[list[Tool]] = None,
        config: Optional[AgentConfig] = None,
        **kwargs
    ):
        # Usar config se fornecido, senão criar dos parâmetros
        if config:
            self.config = config
        else:
            self.config = AgentConfig(
                name=name,
                model=model,
                instructions=instructions,
                tools=tools or [],
                **kwargs
            )
        
        # Estado
        self._state = AgentState.IDLE
        self._messages: list[Message] = []
        self._context: Optional[Context] = None
        
        # Tool registry
        self._tool_registry = ToolRegistry()
        for tool in self.config.tools:
            if isinstance(tool, Tool):
                self._tool_registry.register(tool)
            elif callable(tool):
                self._tool_registry.register(FunctionTool(tool))
        
        # OpenAI client
        self._client: Optional[AsyncOpenAI] = None
        
        # Métricas
        self._total_runs = 0
        self._total_tokens = 0
        self._total_tool_calls = 0
    
    def _get_client(self) -> AsyncOpenAI:
        """Retorna cliente OpenAI."""
        if self._client is None:
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.base_url
            )
        return self._client
    
    @property
    def name(self) -> str:
        """Nome do agente."""
        return self.config.name
    
    @property
    def state(self) -> AgentState:
        """Estado atual do agente."""
        return self._state
    
    @property
    def messages(self) -> list[Message]:
        """Histórico de mensagens."""
        return self._messages.copy()
    
    def reset(self) -> None:
        """Reseta o estado do agente."""
        self._messages.clear()
        self._state = AgentState.IDLE
        self._context = None
    
    def add_tool(self, tool: Union[Tool, callable]) -> None:
        """Adiciona uma ferramenta."""
        if isinstance(tool, Tool):
            self._tool_registry.register(tool)
        elif callable(tool):
            self._tool_registry.register(FunctionTool(tool))
    
    def _build_messages(self, user_input: str) -> list[dict]:
        """Constrói lista de mensagens para a API."""
        messages = []
        
        # System message
        messages.append({
            "role": "system",
            "content": self.config.instructions
        })
        
        # Histórico
        for msg in self._messages:
            messages.append(msg.to_dict())
        
        # Mensagem do usuário
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    def _get_tools_spec(self) -> Optional[list[dict]]:
        """Retorna especificação de tools para a API."""
        tools = self._tool_registry.to_openai_format()
        return tools if tools else None
    
    async def _execute_tool(self, tool_call: dict) -> str:
        """Executa uma chamada de ferramenta."""
        function = tool_call.get("function", {})
        name = function.get("name", "")
        
        # Parse arguments
        args_str = function.get("arguments", "{}")
        try:
            arguments = json.loads(args_str)
        except json.JSONDecodeError:
            return f"Error: Invalid arguments JSON"
        
        # Executar tool
        result = await self._tool_registry.execute(name, arguments)
        
        self._total_tool_calls += 1
        
        return str(result)
    
    async def _run_completion(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None
    ) -> tuple[str, list[dict], Usage]:
        """Executa uma completion."""
        client = self._get_client()
        
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        response = await client.chat.completions.create(**params)
        
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []
        
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in choice.message.tool_calls
            ]
        
        usage = Usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
        
        return content, tool_calls, usage
    
    async def arun(
        self,
        user_input: str,
        context: Optional[Context] = None
    ) -> Response:
        """
        Executa o agente de forma assíncrona.
        
        Args:
            user_input: Input do usuário
            context: Contexto opcional
            
        Returns:
            Response com resultado
        """
        start_time = datetime.now()
        self._state = AgentState.THINKING
        self._context = context or Context()
        
        # Adicionar mensagem do usuário
        user_msg = Message.user(user_input)
        self._messages.append(user_msg)
        
        total_usage = Usage()
        all_tool_calls = []
        
        try:
            # Construir mensagens
            messages = self._build_messages(user_input)
            tools = self._get_tools_spec()
            
            # Loop de execução (para tool calling)
            iterations = 0
            final_content = ""
            
            while iterations < self.config.max_iterations:
                iterations += 1
                
                # Chamar LLM
                content, tool_calls, usage = await self._run_completion(messages, tools)
                total_usage = total_usage + usage
                
                # Se não há tool calls, terminamos
                if not tool_calls:
                    final_content = content
                    break
                
                # Processar tool calls
                self._state = AgentState.EXECUTING
                
                # Adicionar resposta do assistant com tool calls
                assistant_msg = {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
                }
                messages.append(assistant_msg)
                
                # Executar cada tool
                for tc in tool_calls:
                    all_tool_calls.append(ToolCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"])
                    ))
                    
                    result = await self._execute_tool(tc)
                    
                    # Adicionar resultado
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result
                    }
                    messages.append(tool_msg)
                
                self._state = AgentState.THINKING
            
            # Criar resposta
            assistant_msg = Message.assistant(final_content)
            self._messages.append(assistant_msg)
            
            self._state = AgentState.COMPLETED
            self._total_runs += 1
            self._total_tokens += total_usage.total_tokens
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return Response(
                content=final_content,
                messages=self._messages.copy(),
                tool_calls=all_tool_calls,
                usage=total_usage,
                status=ResponseStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.now(),
                duration_ms=elapsed
            )
            
        except asyncio.TimeoutError:
            self._state = AgentState.ERROR
            return Response(
                content="",
                status=ResponseStatus.TIMEOUT,
                error="Request timed out",
                started_at=start_time,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            self._state = AgentState.ERROR
            logger.exception(f"Error in agent run: {e}")
            return Response(
                content="",
                status=ResponseStatus.ERROR,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now()
            )
    
    def run(
        self,
        user_input: str,
        context: Optional[Context] = None
    ) -> Response:
        """
        Executa o agente de forma síncrona.
        
        Args:
            user_input: Input do usuário
            context: Contexto opcional
            
        Returns:
            Response com resultado
        """
        return asyncio.run(self.arun(user_input, context))
    
    async def astream(
        self,
        user_input: str,
        context: Optional[Context] = None
    ) -> AsyncIterator[StreamChunk]:
        """
        Executa o agente com streaming.
        
        Args:
            user_input: Input do usuário
            context: Contexto opcional
            
        Yields:
            StreamChunk com deltas de conteúdo
        """
        self._state = AgentState.THINKING
        self._context = context or Context()
        
        # Adicionar mensagem do usuário
        user_msg = Message.user(user_input)
        self._messages.append(user_msg)
        
        # Construir mensagens
        messages = self._build_messages(user_input)
        tools = self._get_tools_spec()
        
        client = self._get_client()
        
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True
        }
        
        if tools:
            params["tools"] = tools
        
        full_content = ""
        tool_calls = []
        
        async with client.chat.completions.stream(**params) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                if delta.content:
                    full_content += delta.content
                    yield StreamChunk(
                        content=full_content,
                        delta=delta.content
                    )
                
                if delta.tool_calls:
                    # Acumular tool calls
                    for tc in delta.tool_calls:
                        tool_calls.append(tc)
                
                if chunk.choices[0].finish_reason:
                    yield StreamChunk(
                        content=full_content,
                        delta="",
                        finish_reason=chunk.choices[0].finish_reason
                    )
        
        # Adicionar mensagem final
        assistant_msg = Message.assistant(full_content)
        self._messages.append(assistant_msg)
        
        self._state = AgentState.COMPLETED
        self._total_runs += 1
    
    def stream(
        self,
        user_input: str,
        context: Optional[Context] = None
    ):
        """
        Executa o agente com streaming (versão síncrona).
        
        Retorna um iterador que pode ser usado em for loop.
        """
        async def _stream_wrapper():
            async for chunk in self.astream(user_input, context):
                yield chunk
        
        # Criar event loop se necessário
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Executar o gerador async
        gen = _stream_wrapper()
        
        while True:
            try:
                chunk = loop.run_until_complete(gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
    
    def get_metrics(self) -> dict:
        """Retorna métricas do agente."""
        return {
            "name": self.name,
            "state": self._state.value,
            "total_runs": self._total_runs,
            "total_tokens": self._total_tokens,
            "total_tool_calls": self._total_tool_calls,
            "message_count": len(self._messages),
            "tools_count": len(self._tool_registry.list())
        }

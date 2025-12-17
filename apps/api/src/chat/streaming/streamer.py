"""
Chat Streamer - Gerenciador de streaming de respostas.

Integra com diferentes providers de LLM para streaming unificado.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, AsyncIterator, Dict, Any, Callable, List
import asyncio
import logging
import uuid

from openai import AsyncOpenAI

from .events import StreamEvent, StreamEventType, StreamChunk
from ..core.message import Message, MessageRole, MessageStatus, ToolCall
from ..core.conversation import Conversation
from ..core.context import ContextBuilder, ChatContext

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Configuração de streaming."""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Streaming options
    buffer_size: int = 1  # Chars antes de emitir
    emit_thinking: bool = True
    emit_tool_calls: bool = True
    
    # Timeouts
    timeout_seconds: int = 120
    chunk_timeout_seconds: int = 30


class ChatStreamer:
    """
    Gerenciador de streaming de chat.
    
    Suporta:
    - Streaming de texto com deltas
    - Thinking mode (reasoning steps)
    - Tool calls em tempo real
    - Múltiplos providers
    
    Uso:
    ```python
    streamer = ChatStreamer()
    
    async for event in streamer.stream(
        conversation=conversation,
        user_message="Hello!",
        agent_id="assistant"
    ):
        if event.type == StreamEventType.MESSAGE_DELTA:
            print(event.delta, end="")
    ```
    """
    
    def __init__(
        self,
        config: Optional[StreamConfig] = None,
        openai_client: Optional[AsyncOpenAI] = None
    ):
        self.config = config or StreamConfig()
        self._client = openai_client
        self._context_builder = ContextBuilder()
        
        # Callbacks
        self._on_message_start: Optional[Callable] = None
        self._on_message_done: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
    
    def _get_client(self) -> AsyncOpenAI:
        """Obtém cliente OpenAI."""
        if self._client is None:
            self._client = AsyncOpenAI()
        return self._client
    
    def on_message_start(self, callback: Callable) -> None:
        """Registra callback para início de mensagem."""
        self._on_message_start = callback
    
    def on_message_done(self, callback: Callable) -> None:
        """Registra callback para fim de mensagem."""
        self._on_message_done = callback
    
    def on_error(self, callback: Callable) -> None:
        """Registra callback para erros."""
        self._on_error = callback
    
    async def stream(
        self,
        conversation: Conversation,
        user_message: str,
        agent_id: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        memories: Optional[List[Dict]] = None,
        rag_documents: Optional[List[Dict]] = None
    ) -> AsyncIterator[StreamEvent]:
        """
        Faz streaming de uma resposta.
        
        Args:
            conversation: Conversa atual
            user_message: Mensagem do usuário
            agent_id: ID do agente (opcional)
            tools: Ferramentas disponíveis
            memories: Memórias relevantes
            rag_documents: Documentos RAG
            
        Yields:
            StreamEvent com deltas e status
        """
        message_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Construir contexto
            context = await self._context_builder.build(
                conversation=conversation,
                new_message=user_message,
                memories=memories,
                rag_documents=rag_documents
            )
            
            # Adicionar mensagem do usuário
            api_messages = context.to_api_messages()
            api_messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Emitir início
            yield StreamEvent.message_start(message_id, conversation.id)
            
            if self._on_message_start:
                await self._on_message_start(message_id, conversation.id)
            
            # Configurar request
            params = {
                "model": conversation.settings.model or self.config.model,
                "messages": api_messages,
                "temperature": conversation.settings.temperature or self.config.temperature,
                "max_tokens": conversation.settings.max_tokens or self.config.max_tokens,
                "stream": True
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            # Stream da resposta
            client = self._get_client()
            full_content = ""
            tool_calls_buffer: Dict[int, Dict] = {}
            thinking_content = ""
            in_thinking = False
            
            async with client.chat.completions.create(**params) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    
                    if not delta:
                        continue
                    
                    # Processar conteúdo
                    if delta.content:
                        text = delta.content
                        
                        # Detectar thinking mode (entre <thinking> tags)
                        if "<thinking>" in text:
                            in_thinking = True
                            yield StreamEvent.thinking_start(message_id)
                            text = text.replace("<thinking>", "")
                        
                        if "</thinking>" in text:
                            in_thinking = False
                            text = text.replace("</thinking>", "")
                            yield StreamEvent(
                                type=StreamEventType.THINKING_DONE,
                                content=thinking_content,
                                message_id=message_id
                            )
                            thinking_content = ""
                        
                        if in_thinking and self.config.emit_thinking:
                            thinking_content += text
                            yield StreamEvent.thinking_delta(text, thinking_content, message_id)
                        else:
                            full_content += text
                            yield StreamEvent.message_delta(text, full_content, message_id)
                    
                    # Processar tool calls
                    if delta.tool_calls and self.config.emit_tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {
                                    "id": tc.id or "",
                                    "name": tc.function.name if tc.function else "",
                                    "arguments": ""
                                }
                                
                                if tc.function and tc.function.name:
                                    yield StreamEvent.tool_call_start(
                                        tool_call_id=tc.id or "",
                                        tool_name=tc.function.name,
                                        message_id=message_id
                                    )
                            
                            if tc.function and tc.function.arguments:
                                tool_calls_buffer[idx]["arguments"] += tc.function.arguments
                    
                    # Verificar fim
                    if chunk.choices and chunk.choices[0].finish_reason:
                        break
            
            # Processar tool calls finais
            final_tool_calls = []
            for idx, tc_data in tool_calls_buffer.items():
                final_tool_calls.append(ToolCall(
                    id=tc_data["id"],
                    tool_name=tc_data["name"],
                    arguments=self._parse_tool_args(tc_data["arguments"])
                ))
                
                yield StreamEvent(
                    type=StreamEventType.TOOL_CALL_DONE,
                    tool_call_id=tc_data["id"],
                    tool_name=tc_data["name"],
                    tool_arguments=self._parse_tool_args(tc_data["arguments"]),
                    message_id=message_id
                )
            
            # Calcular métricas
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Emitir conclusão
            yield StreamEvent.message_done(
                content=full_content,
                message_id=message_id,
                finish_reason="stop"
            )
            
            if self._on_message_done:
                await self._on_message_done(
                    message_id=message_id,
                    content=full_content,
                    tool_calls=final_tool_calls,
                    duration_ms=duration_ms
                )
        
        except asyncio.TimeoutError:
            logger.error(f"Streaming timeout for conversation {conversation.id}")
            yield StreamEvent.message_error(
                error="Request timed out",
                message_id=message_id,
                code="timeout"
            )
            
            if self._on_error:
                await self._on_error(message_id, "timeout", "Request timed out")
        
        except Exception as e:
            logger.exception(f"Streaming error: {e}")
            yield StreamEvent.message_error(
                error=str(e),
                message_id=message_id,
                code="error"
            )
            
            if self._on_error:
                await self._on_error(message_id, "error", str(e))
    
    def _parse_tool_args(self, args_str: str) -> Dict:
        """Parse argumentos de tool call."""
        import json
        try:
            return json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            return {"raw": args_str}
    
    async def stream_with_tools(
        self,
        conversation: Conversation,
        user_message: str,
        tools: List[Dict],
        tool_executor: Callable,
        max_iterations: int = 5
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream com execução automática de tools.
        
        Continua executando tools até obter resposta final.
        """
        messages_history = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            tool_calls_collected = []
            final_content = ""
            
            async for event in self.stream(
                conversation=conversation,
                user_message=user_message if iteration == 1 else "",
                tools=tools
            ):
                yield event
                
                if event.type == StreamEventType.TOOL_CALL_DONE:
                    tool_calls_collected.append({
                        "id": event.tool_call_id,
                        "name": event.tool_name,
                        "arguments": event.tool_arguments
                    })
                
                if event.type == StreamEventType.MESSAGE_DONE:
                    final_content = event.content
            
            # Se não houve tool calls, terminamos
            if not tool_calls_collected:
                break
            
            # Executar cada tool
            for tc in tool_calls_collected:
                try:
                    result = await tool_executor(tc["name"], tc["arguments"])
                    
                    yield StreamEvent.tool_result(
                        tool_call_id=tc["id"],
                        result=str(result),
                        message_id=""
                    )
                    
                    # Adicionar ao histórico
                    messages_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result)
                    })
                    
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    yield StreamEvent.tool_result(
                        tool_call_id=tc["id"],
                        result=f"Error: {str(e)}",
                        message_id=""
                    )


# Singleton
_chat_streamer: Optional[ChatStreamer] = None


def get_chat_streamer(**kwargs) -> ChatStreamer:
    """Obtém o streamer singleton."""
    global _chat_streamer
    if _chat_streamer is None:
        _chat_streamer = ChatStreamer(**kwargs)
    return _chat_streamer

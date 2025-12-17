"""
Streaming API - SSE endpoints for real-time chat streaming.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, AsyncGenerator
import asyncio
import json
import time
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Streaming"])


# ============================================
# MODELS
# ============================================

class StreamChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "llama-3.1-8b-instant"
    agent_id: Optional[str] = None
    persona_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None


# ============================================
# SSE HELPERS
# ============================================

def format_sse_event(event_type: str, data: dict) -> str:
    """Format data as SSE event."""
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"


async def stream_llm_response(
    prompt: str,
    model: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """
    Stream LLM response token by token.
    
    Yields SSE-formatted events:
    - message_start: {id, model}
    - message_delta: {delta, index}
    - message_done: {finish_reason, usage}
    - error: {message, code}
    """
    start_time = time.time()
    message_id = f"msg_{int(time.time() * 1000)}"
    
    # Emit start event
    yield format_sse_event("message_start", {
        "id": message_id,
        "model": model,
        "created": int(time.time()),
    })
    
    # Try real LLM providers
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    full_response = ""
    tokens_used = {"input": 0, "output": 0}
    provider_used = "demo"
    
    try:
        # Try Groq (fastest)
        if groq_key and len(groq_key) > 10:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=groq_key)
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                stream = await client.chat.completions.create(
                    model=model if "llama" in model or "mixtral" in model else "llama-3.1-8b-instant",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                index = 0
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        full_response += delta
                        yield format_sse_event("message_delta", {
                            "delta": delta,
                            "index": index,
                        })
                        index += 1
                        await asyncio.sleep(0.01)  # Small delay for smoother streaming
                
                provider_used = "groq"
                tokens_used = {
                    "input": len(prompt) // 4,
                    "output": len(full_response) // 4,
                }
                
            except Exception as e:
                logger.warning(f"Groq streaming failed: {e}")
        
        # Try OpenAI
        if not full_response and openai_key and len(openai_key) > 10:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=openai_key)
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                stream = await client.chat.completions.create(
                    model=model if "gpt" in model else "gpt-4o-mini",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                index = 0
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        full_response += delta
                        yield format_sse_event("message_delta", {
                            "delta": delta,
                            "index": index,
                        })
                        index += 1
                        await asyncio.sleep(0.01)
                
                provider_used = "openai"
                tokens_used = {
                    "input": len(prompt) // 4,
                    "output": len(full_response) // 4,
                }
                
            except Exception as e:
                logger.warning(f"OpenAI streaming failed: {e}")
        
        # Try Anthropic
        if not full_response and anthropic_key and len(anthropic_key) > 10:
            try:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=anthropic_key)
                
                system_msg = system_prompt or "You are a helpful assistant."
                
                async with client.messages.stream(
                    model=model if "claude" in model else "claude-3-5-haiku-20241022",
                    max_tokens=max_tokens,
                    system=system_msg,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    index = 0
                    async for text in stream.text_stream:
                        full_response += text
                        yield format_sse_event("message_delta", {
                            "delta": text,
                            "index": index,
                        })
                        index += 1
                        await asyncio.sleep(0.01)
                
                provider_used = "anthropic"
                tokens_used = {
                    "input": len(prompt) // 4,
                    "output": len(full_response) // 4,
                }
                
            except Exception as e:
                logger.warning(f"Anthropic streaming failed: {e}")
        
        # Fallback: simulate streaming for demo
        if not full_response:
            demo_response = f"""Olá! Recebi sua mensagem: "{prompt[:100]}..."

Esta é uma resposta de demonstração porque nenhuma API LLM está configurada.

Para habilitar respostas reais, configure uma das seguintes variáveis de ambiente:
- GROQ_API_KEY (mais rápido, gratuito)
- OPENAI_API_KEY
- ANTHROPIC_API_KEY

O AeroLab suporta múltiplos provedores de LLM com fallback automático."""
            
            words = demo_response.split(" ")
            index = 0
            for word in words:
                delta = word + " "
                full_response += delta
                yield format_sse_event("message_delta", {
                    "delta": delta,
                    "index": index,
                })
                index += 1
                await asyncio.sleep(0.05)  # Simulate typing
            
            tokens_used = {
                "input": len(prompt) // 4,
                "output": len(full_response) // 4,
            }
        
        # Emit done event
        duration_ms = int((time.time() - start_time) * 1000)
        yield format_sse_event("message_done", {
            "id": message_id,
            "finish_reason": "stop",
            "provider": provider_used,
            "model": model,
            "usage": {
                "prompt_tokens": tokens_used["input"],
                "completion_tokens": tokens_used["output"],
                "total_tokens": tokens_used["input"] + tokens_used["output"],
            },
            "duration_ms": duration_ms,
        })
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield format_sse_event("error", {
            "message": str(e),
            "code": "stream_error",
        })


# ============================================
# ENDPOINTS
# ============================================

@router.post("/stream")
async def stream_chat(request: StreamChatRequest):
    """
    Stream chat response via Server-Sent Events (SSE).
    
    Returns a stream of events:
    - message_start: Initial metadata
    - message_delta: Token chunks
    - message_done: Final stats
    - error: Error info (if any)
    
    Usage:
    ```javascript
    const eventSource = new EventSource('/api/v2/chat/stream', {
      method: 'POST',
      body: JSON.stringify({ message: 'Hello!' })
    });
    
    eventSource.addEventListener('message_delta', (e) => {
      const data = JSON.parse(e.data);
      console.log(data.delta);
    });
    ```
    """
    # Build system prompt
    system_prompt = request.system_prompt
    
    # If persona_id provided, load persona's system prompt
    if request.persona_id:
        try:
            from .personas import _personas_store
            persona = _personas_store.get(request.persona_id)
            if persona:
                system_prompt = persona.get("system_prompt", system_prompt)
        except Exception:
            pass
    
    return StreamingResponse(
        stream_llm_response(
            prompt=request.message,
            model=request.model,
            system_prompt=system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream/health")
async def stream_health():
    """Check streaming endpoint health."""
    return {
        "status": "ok",
        "streaming": True,
        "providers": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
    }

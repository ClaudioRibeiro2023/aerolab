"""
Chat Streaming - Real-time streaming support.

Suporta:
- Server-Sent Events (SSE)
- WebSocket
- Eventos tipados
"""

from .events import StreamChunk, StreamEvent, StreamEventType
from .streamer import ChatStreamer

__all__ = [
    "StreamChunk",
    "StreamEvent",
    "StreamEventType",
    "ChatStreamer",
]

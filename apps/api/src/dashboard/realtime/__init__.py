"""
Real-time Module - Atualizações em tempo real para dashboards.

Features:
- WebSocket connections
- Pub/Sub para widgets
- Streaming de métricas
- Live updates
"""

from .websocket import WebSocketManager, WebSocketConnection
from .pubsub import PubSubManager, Subscription
from .streaming import StreamManager, MetricStream

__all__ = [
    "WebSocketManager",
    "WebSocketConnection",
    "PubSubManager",
    "Subscription",
    "StreamManager",
    "MetricStream",
]

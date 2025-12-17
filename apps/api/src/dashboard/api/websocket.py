"""
Dashboard WebSocket API - Real-time updates via WebSocket.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, Dict, Any
import asyncio
import json
import logging

from ..realtime.websocket import (
    WebSocketManager, 
    WebSocketMessage, 
    MessageType,
    get_websocket_manager
)
from ..realtime.pubsub import get_pubsub_manager, initialize_dashboard_topics
from ..realtime.streaming import get_stream_manager

logger = logging.getLogger(__name__)

websocket_router = APIRouter(tags=["WebSocket"])

# Initialize dashboard topics
initialize_dashboard_topics()


@websocket_router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """Main WebSocket endpoint for dashboard real-time updates."""
    await websocket.accept()
    
    manager = get_websocket_manager()
    connection_id = f"conn_{id(websocket)}"
    
    async def send_message(data: str):
        await websocket.send_text(data)
    
    connection = await manager.connect(
        connection_id=connection_id,
        send_callback=send_message,
        metadata={"token": token}
    )
    
    await connection.send(WebSocketMessage(
        type=MessageType.DATA,
        data={"event": "connected", "connectionId": connection_id}
    ))
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(connection_id, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    finally:
        await manager.disconnect(connection_id)


@websocket_router.websocket("/ws/metrics/{metric_name}")
async def metrics_stream(
    websocket: WebSocket,
    metric_name: str,
    interval: float = Query(default=1.0, ge=0.1, le=60),
):
    """WebSocket endpoint for streaming metric data."""
    await websocket.accept()
    
    stream_manager = get_stream_manager()
    stream_id = f"stream_{metric_name}_{id(websocket)}"
    
    async def on_data(sid: str, point: Dict[str, Any]):
        try:
            await websocket.send_json({"type": "data", "metric": metric_name, "point": point})
        except Exception as e:
            logger.error(f"Error sending metric data: {e}")
    
    stream = stream_manager.create_stream(
        stream_id=stream_id,
        name=f"Metric: {metric_name}",
        query=metric_name,
        interval_seconds=interval,
        data_callback=on_data,
    )
    
    await stream_manager.start_stream(stream_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "pause":
                await stream_manager.pause_stream(stream_id)
            elif msg.get("type") == "resume":
                await stream_manager.resume_stream(stream_id)
            elif msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await stream_manager.stop_stream(stream_id)
        stream_manager.delete_stream(stream_id)


@websocket_router.websocket("/ws/alerts")
async def alerts_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time alert notifications."""
    await websocket.accept()
    
    pubsub = get_pubsub_manager()
    subscriber_id = f"alerts_{id(websocket)}"
    
    async def on_alert(message: Dict[str, Any]):
        try:
            await websocket.send_json({"type": "alert", "data": message})
        except Exception:
            pass
    
    pubsub.subscribe("dashboard.alerts", on_alert, subscriber_id=subscriber_id)
    await websocket.send_json({"type": "subscribed", "channel": "alerts"})
    
    try:
        while True:
            data = await websocket.receive_text()
            if json.loads(data).get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        pubsub.unsubscribe(subscriber_id)

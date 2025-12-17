"""
Agno Team Orchestrator v2.0 - WebSocket API

Real-time communication for team execution.
"""

from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
import asyncio

from ..engine import get_orchestration_engine
from ..types import ExecutionStatus

logger = logging.getLogger(__name__)
websocket_router = APIRouter(tags=["Team Orchestrator WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.execution_subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
        
        # Remove from execution subscriptions
        for subs in self.execution_subscriptions.values():
            subs.discard(websocket)
        
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: dict, client_id: str):
        """Broadcast to all client connections."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await self.send_personal(message, connection)
    
    async def broadcast_to_execution(self, execution_id: str, message: dict):
        """Broadcast to all subscribers of an execution."""
        if execution_id in self.execution_subscriptions:
            for ws in self.execution_subscriptions[execution_id]:
                await self.send_personal(message, ws)
    
    def subscribe_execution(self, execution_id: str, websocket: WebSocket):
        """Subscribe to execution updates."""
        if execution_id not in self.execution_subscriptions:
            self.execution_subscriptions[execution_id] = set()
        self.execution_subscriptions[execution_id].add(websocket)
    
    def unsubscribe_execution(self, execution_id: str, websocket: WebSocket):
        """Unsubscribe from execution updates."""
        if execution_id in self.execution_subscriptions:
            self.execution_subscriptions[execution_id].discard(websocket)


# Global connection manager
manager = ConnectionManager()


@websocket_router.websocket("/ws/teams/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for team orchestration.
    
    Message types:
    - subscribe_execution: Subscribe to execution updates
    - unsubscribe_execution: Unsubscribe from updates
    - execute_team: Start team execution
    - get_status: Get execution status
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            payload = message.get("payload", {})
            
            if msg_type == "subscribe_execution":
                execution_id = payload.get("execution_id")
                if execution_id:
                    manager.subscribe_execution(execution_id, websocket)
                    await manager.send_personal({
                        "type": "subscribed",
                        "execution_id": execution_id,
                    }, websocket)
            
            elif msg_type == "unsubscribe_execution":
                execution_id = payload.get("execution_id")
                if execution_id:
                    manager.unsubscribe_execution(execution_id, websocket)
            
            elif msg_type == "get_status":
                execution_id = payload.get("execution_id")
                if execution_id:
                    engine = get_orchestration_engine()
                    execution = engine.get_execution(execution_id)
                    
                    if execution:
                        await manager.send_personal({
                            "type": "status",
                            "execution": execution.to_dict(),
                        }, websocket)
                    else:
                        await manager.send_personal({
                            "type": "error",
                            "message": "Execution not found",
                        }, websocket)
            
            elif msg_type == "ping":
                await manager.send_personal({"type": "pong"}, websocket)
            
            else:
                await manager.send_personal({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)


async def send_execution_update(execution_id: str, update: dict):
    """Send execution update to subscribers."""
    await manager.broadcast_to_execution(execution_id, {
        "type": "execution_update",
        "execution_id": execution_id,
        **update,
    })


async def send_agent_message(execution_id: str, agent_id: str, message: str):
    """Send agent message to subscribers."""
    await manager.broadcast_to_execution(execution_id, {
        "type": "agent_message",
        "execution_id": execution_id,
        "agent_id": agent_id,
        "message": message,
    })


async def send_task_completed(execution_id: str, task_id: str, result: dict):
    """Send task completion to subscribers."""
    await manager.broadcast_to_execution(execution_id, {
        "type": "task_completed",
        "execution_id": execution_id,
        "task_id": task_id,
        "result": result,
    })

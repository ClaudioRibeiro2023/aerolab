"""
Agno Flow Studio v3.0 - WebSocket API

Real-time updates for workflow execution.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

# Connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # workflow_id -> set of connections
        self.workflow_connections: Dict[str, Set[WebSocket]] = {}
        # execution_id -> set of connections
        self.execution_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect_workflow(self, websocket: WebSocket, workflow_id: str):
        """Connect to workflow updates."""
        await websocket.accept()
        if workflow_id not in self.workflow_connections:
            self.workflow_connections[workflow_id] = set()
        self.workflow_connections[workflow_id].add(websocket)
        logger.info(f"WebSocket connected to workflow {workflow_id}")
    
    async def connect_execution(self, websocket: WebSocket, execution_id: str):
        """Connect to execution updates."""
        await websocket.accept()
        if execution_id not in self.execution_connections:
            self.execution_connections[execution_id] = set()
        self.execution_connections[execution_id].add(websocket)
        logger.info(f"WebSocket connected to execution {execution_id}")
    
    def disconnect_workflow(self, websocket: WebSocket, workflow_id: str):
        """Disconnect from workflow updates."""
        if workflow_id in self.workflow_connections:
            self.workflow_connections[workflow_id].discard(websocket)
            if not self.workflow_connections[workflow_id]:
                del self.workflow_connections[workflow_id]
        logger.info(f"WebSocket disconnected from workflow {workflow_id}")
    
    def disconnect_execution(self, websocket: WebSocket, execution_id: str):
        """Disconnect from execution updates."""
        if execution_id in self.execution_connections:
            self.execution_connections[execution_id].discard(websocket)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]
        logger.info(f"WebSocket disconnected from execution {execution_id}")
    
    async def broadcast_workflow(self, workflow_id: str, message: dict):
        """Broadcast message to all workflow subscribers."""
        if workflow_id in self.workflow_connections:
            dead_connections = set()
            for connection in self.workflow_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            # Clean up dead connections
            self.workflow_connections[workflow_id] -= dead_connections
    
    async def broadcast_execution(self, execution_id: str, message: dict):
        """Broadcast message to all execution subscribers."""
        if execution_id in self.execution_connections:
            dead_connections = set()
            for connection in self.execution_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            # Clean up dead connections
            self.execution_connections[execution_id] -= dead_connections


manager = ConnectionManager()


@websocket_router.websocket("/ws/workflow/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for workflow updates.
    
    Events:
    - node_added: A node was added
    - node_updated: A node was updated
    - node_removed: A node was removed
    - edge_added: An edge was added
    - edge_removed: An edge was removed
    - workflow_saved: Workflow was saved
    """
    await manager.connect_workflow(websocket, workflow_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            # Handle different event types
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif event_type == "cursor_move":
                # Broadcast cursor position to other clients
                await manager.broadcast_workflow(workflow_id, {
                    "type": "cursor_update",
                    "userId": data.get("userId"),
                    "position": data.get("position"),
                })
            
            elif event_type == "node_select":
                # Broadcast selection to other clients
                await manager.broadcast_workflow(workflow_id, {
                    "type": "node_selected",
                    "userId": data.get("userId"),
                    "nodeId": data.get("nodeId"),
                })
            
    except WebSocketDisconnect:
        manager.disconnect_workflow(websocket, workflow_id)


@websocket_router.websocket("/ws/execution/{execution_id}")
async def execution_websocket(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for execution updates.
    
    Events:
    - execution_started: Execution started
    - node_started: A node started executing
    - node_completed: A node completed
    - node_error: A node encountered an error
    - execution_completed: Execution completed
    - execution_failed: Execution failed
    - progress: Progress update
    """
    await manager.connect_execution(websocket, execution_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif event_type == "pause":
                # Handle pause request
                from ..engine import get_workflow_engine
                engine = get_workflow_engine()
                engine.pause(execution_id)
                await websocket.send_json({
                    "type": "execution_paused",
                    "executionId": execution_id,
                })
            
            elif event_type == "resume":
                # Handle resume request
                from ..engine import get_workflow_engine
                engine = get_workflow_engine()
                engine.resume(execution_id)
                await websocket.send_json({
                    "type": "execution_resumed",
                    "executionId": execution_id,
                })
            
            elif event_type == "step":
                # Handle step debug request
                from ..engine import get_workflow_engine
                engine = get_workflow_engine()
                engine.resume(execution_id)
                # Will pause at next breakpoint
                await websocket.send_json({
                    "type": "step_executed",
                    "executionId": execution_id,
                })
    
    except WebSocketDisconnect:
        manager.disconnect_execution(websocket, execution_id)


# Helper functions for broadcasting from engine

async def notify_node_started(execution_id: str, node_id: str, node_name: str):
    """Notify that a node started."""
    await manager.broadcast_execution(execution_id, {
        "type": "node_started",
        "nodeId": node_id,
        "nodeName": node_name,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })


async def notify_node_completed(execution_id: str, node_id: str, output: any):
    """Notify that a node completed."""
    await manager.broadcast_execution(execution_id, {
        "type": "node_completed",
        "nodeId": node_id,
        "output": output,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })


async def notify_node_error(execution_id: str, node_id: str, error: str):
    """Notify that a node encountered an error."""
    await manager.broadcast_execution(execution_id, {
        "type": "node_error",
        "nodeId": node_id,
        "error": error,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })


async def notify_execution_completed(execution_id: str, output: dict):
    """Notify that execution completed."""
    await manager.broadcast_execution(execution_id, {
        "type": "execution_completed",
        "executionId": execution_id,
        "output": output,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })


async def notify_progress(execution_id: str, progress: float, current_node: str):
    """Notify progress update."""
    await manager.broadcast_execution(execution_id, {
        "type": "progress",
        "executionId": execution_id,
        "progress": progress,
        "currentNode": current_node,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })

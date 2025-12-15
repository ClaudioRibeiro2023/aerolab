"""
WebSocket Integration

Provides WebSocket support for real-time features like notifications,
live updates, and collaborative features.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional, Any, Callable, Awaitable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import json
import asyncio
import os

from .logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration
# ============================================================================

WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))  # seconds
WS_MAX_CONNECTIONS_PER_USER = int(os.getenv("WS_MAX_CONNECTIONS_PER_USER", "5"))

# ============================================================================
# Message Types
# ============================================================================

class MessageType(str, Enum):
    """WebSocket message types."""
    # System messages
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    
    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"
    
    # Data updates
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    
    # Presence
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    USER_TYPING = "user.typing"
    
    # Custom
    CUSTOM = "custom"


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: MessageType
    payload: Optional[dict[str, Any]] = None
    timestamp: str = ""
    
    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        super().__init__(**data)
    
    def to_json(self) -> str:
        return self.model_dump_json()


# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections.
    
    Supports:
    - Per-user connections
    - Room-based broadcasting (e.g., by tenant, by resource)
    - Heartbeat monitoring
    
    Usage:
        manager = ConnectionManager()
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await manager.connect(websocket, user_id="user123")
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle incoming message
            except WebSocketDisconnect:
                manager.disconnect(websocket, user_id="user123")
    """
    
    def __init__(self):
        # user_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # room_id -> set of user_ids
        self.rooms: dict[str, set[str]] = {}
        # WebSocket -> user_id mapping for quick lookup
        self.connection_users: dict[WebSocket, str] = {}
        # Heartbeat tasks
        self._heartbeat_tasks: dict[WebSocket, asyncio.Task] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        rooms: Optional[list[str]] = None,
    ) -> bool:
        """
        Accept a WebSocket connection.
        
        Returns False if max connections exceeded.
        """
        # Check connection limit
        current_connections = len(self.active_connections.get(user_id, []))
        if current_connections >= WS_MAX_CONNECTIONS_PER_USER:
            logger.warning("ws_max_connections", user_id=user_id, count=current_connections)
            await websocket.close(code=4000, reason="Maximum connections exceeded")
            return False
        
        await websocket.accept()
        
        # Register connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.connection_users[websocket] = user_id
        
        # Join rooms
        if rooms:
            for room_id in rooms:
                self.join_room(user_id, room_id)
        
        # Start heartbeat
        self._heartbeat_tasks[websocket] = asyncio.create_task(
            self._heartbeat(websocket)
        )
        
        # Send connected message
        await self.send_personal(
            user_id,
            WSMessage(
                type=MessageType.CONNECTED,
                payload={"user_id": user_id, "rooms": rooms or []},
            ),
        )
        
        logger.info("ws_connected", user_id=user_id, rooms=rooms)
        return True
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None) -> None:
        """Disconnect a WebSocket connection."""
        # Get user_id if not provided
        if not user_id:
            user_id = self.connection_users.get(websocket)
        
        if not user_id:
            return
        
        # Cancel heartbeat
        if websocket in self._heartbeat_tasks:
            self._heartbeat_tasks[websocket].cancel()
            del self._heartbeat_tasks[websocket]
        
        # Remove from active connections
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Leave all rooms when user has no more connections
                self._leave_all_rooms(user_id)
        
        # Remove from connection mapping
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        
        logger.info("ws_disconnected", user_id=user_id)
    
    async def _heartbeat(self, websocket: WebSocket) -> None:
        """Send periodic heartbeats to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(WS_HEARTBEAT_INTERVAL)
                await websocket.send_text(
                    WSMessage(type=MessageType.HEARTBEAT).to_json()
                )
        except Exception:
            pass  # Connection closed
    
    def join_room(self, user_id: str, room_id: str) -> None:
        """Add user to a room."""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(user_id)
        logger.debug("ws_room_join", user_id=user_id, room_id=room_id)
    
    def leave_room(self, user_id: str, room_id: str) -> None:
        """Remove user from a room."""
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        logger.debug("ws_room_leave", user_id=user_id, room_id=room_id)
    
    def _leave_all_rooms(self, user_id: str) -> None:
        """Remove user from all rooms."""
        for room_id in list(self.rooms.keys()):
            self.leave_room(user_id, room_id)
    
    async def send_personal(self, user_id: str, message: WSMessage) -> int:
        """
        Send message to all connections of a specific user.
        Returns number of connections message was sent to.
        """
        connections = self.active_connections.get(user_id, [])
        sent = 0
        for connection in connections:
            try:
                await connection.send_text(message.to_json())
                sent += 1
            except Exception as e:
                logger.error("ws_send_error", user_id=user_id, error=str(e))
        return sent
    
    async def send_to_room(self, room_id: str, message: WSMessage, exclude_user: Optional[str] = None) -> int:
        """
        Send message to all users in a room.
        Returns number of users message was sent to.
        """
        users = self.rooms.get(room_id, set())
        sent = 0
        for user_id in users:
            if user_id != exclude_user:
                count = await self.send_personal(user_id, message)
                if count > 0:
                    sent += 1
        return sent
    
    async def broadcast(self, message: WSMessage, exclude_user: Optional[str] = None) -> int:
        """
        Broadcast message to all connected users.
        Returns number of users message was sent to.
        """
        sent = 0
        for user_id in list(self.active_connections.keys()):
            if user_id != exclude_user:
                count = await self.send_personal(user_id, message)
                if count > 0:
                    sent += 1
        return sent
    
    def get_online_users(self) -> list[str]:
        """Get list of all connected user IDs."""
        return list(self.active_connections.keys())
    
    def get_room_users(self, room_id: str) -> list[str]:
        """Get list of user IDs in a room."""
        return list(self.rooms.get(room_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self.active_connections


# Global connection manager
ws_manager = ConnectionManager()


# ============================================================================
# WebSocket Endpoints
# ============================================================================

from fastapi import APIRouter

ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    rooms: Optional[str] = Query(None),  # Comma-separated room IDs
):
    """
    Main WebSocket endpoint.
    
    Query params:
    - user_id: User identifier (required for authenticated connections)
    - rooms: Comma-separated list of rooms to join
    
    Example:
        ws://localhost:8000/ws?user_id=user123&rooms=tenant:acme,project:123
    """
    if not user_id:
        await websocket.close(code=4001, reason="user_id required")
        return
    
    room_list = rooms.split(",") if rooms else []
    
    if not await ws_manager.connect(websocket, user_id, room_list):
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})
                
                # Handle different message types
                if message_type == "join_room":
                    room_id = payload.get("room_id")
                    if room_id:
                        ws_manager.join_room(user_id, room_id)
                        await ws_manager.send_personal(
                            user_id,
                            WSMessage(
                                type=MessageType.CUSTOM,
                                payload={"action": "room_joined", "room_id": room_id},
                            ),
                        )
                
                elif message_type == "leave_room":
                    room_id = payload.get("room_id")
                    if room_id:
                        ws_manager.leave_room(user_id, room_id)
                
                elif message_type == "broadcast_room":
                    room_id = payload.get("room_id")
                    content = payload.get("content")
                    if room_id and content:
                        await ws_manager.send_to_room(
                            room_id,
                            WSMessage(
                                type=MessageType.CUSTOM,
                                payload={"from": user_id, "content": content},
                            ),
                            exclude_user=user_id,
                        )
                
                elif message_type == "typing":
                    room_id = payload.get("room_id")
                    if room_id:
                        await ws_manager.send_to_room(
                            room_id,
                            WSMessage(
                                type=MessageType.USER_TYPING,
                                payload={"user_id": user_id},
                            ),
                            exclude_user=user_id,
                        )
                
            except json.JSONDecodeError:
                await ws_manager.send_personal(
                    user_id,
                    WSMessage(
                        type=MessageType.ERROR,
                        payload={"message": "Invalid JSON"},
                    ),
                )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
        # Notify rooms about user leaving
        for room_id in ws_manager.rooms:
            if user_id in ws_manager.rooms.get(room_id, set()):
                await ws_manager.send_to_room(
                    room_id,
                    WSMessage(
                        type=MessageType.USER_LEFT,
                        payload={"user_id": user_id},
                    ),
                )


@ws_router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status."""
    return {
        "online_users": len(ws_manager.get_online_users()),
        "active_rooms": len(ws_manager.rooms),
        "rooms": {
            room_id: len(users) 
            for room_id, users in ws_manager.rooms.items()
        },
    }


# ============================================================================
# Setup Function
# ============================================================================

def setup_websocket(app: FastAPI) -> None:
    """
    Configure WebSocket support for the FastAPI application.
    
    Usage:
        from app.websocket import setup_websocket, ws_manager, WSMessage, MessageType
        
        setup_websocket(app)
        
        # Send notification to user
        await ws_manager.send_personal(
            user_id="user123",
            message=WSMessage(
                type=MessageType.NOTIFICATION,
                payload={"title": "New message", "body": "You have a new message"}
            )
        )
    """
    app.include_router(ws_router)
    logger.info("websocket_configured", heartbeat_interval=WS_HEARTBEAT_INTERVAL)


# ============================================================================
# Notification Helpers
# ============================================================================

async def send_notification(
    user_id: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Send a notification to a user via WebSocket.
    Returns True if user is online and message was sent.
    """
    if not ws_manager.is_user_online(user_id):
        return False
    
    count = await ws_manager.send_personal(
        user_id,
        WSMessage(
            type=MessageType.NOTIFICATION,
            payload={
                "title": title,
                "body": body,
                "data": data or {},
            },
        ),
    )
    return count > 0


async def broadcast_data_update(
    resource_type: str,
    resource_id: str,
    action: str,  # "created", "updated", "deleted"
    data: Optional[dict] = None,
    room_id: Optional[str] = None,
) -> int:
    """
    Broadcast a data update notification.
    If room_id is provided, sends only to that room.
    Returns number of users notified.
    """
    message_type = {
        "created": MessageType.DATA_CREATED,
        "updated": MessageType.DATA_UPDATED,
        "deleted": MessageType.DATA_DELETED,
    }.get(action, MessageType.DATA_UPDATED)
    
    message = WSMessage(
        type=message_type,
        payload={
            "resource_type": resource_type,
            "resource_id": resource_id,
            "data": data or {},
        },
    )
    
    if room_id:
        return await ws_manager.send_to_room(room_id, message)
    else:
        return await ws_manager.broadcast(message)

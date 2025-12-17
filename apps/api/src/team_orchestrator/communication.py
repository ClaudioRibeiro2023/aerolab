"""
Agno Team Orchestrator v2.0 - Communication Layer

Inter-agent messaging and conversation management.
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from collections import defaultdict
import asyncio
import logging

from .types import (
    Message, MessageType, MessageThread, Conversation,
    Priority, Attachment
)

logger = logging.getLogger(__name__)


# ============================================================
# MESSAGE BUS
# ============================================================

class MessageBus:
    """Central message bus for inter-agent communication."""
    
    def __init__(self):
        self._messages: Dict[str, Message] = {}
        self._threads: Dict[str, MessageThread] = {}
        self._agent_inbox: Dict[str, List[str]] = defaultdict(list)
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._broadcast_subscribers: List[Callable] = []
    
    async def send(
        self,
        sender: str,
        recipients: List[str],
        content: str,
        message_type: MessageType = MessageType.INFORM,
        thread_id: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        **kwargs
    ) -> Message:
        """Send a message."""
        message = Message(
            sender=sender,
            recipients=recipients,
            content=content,
            type=message_type,
            thread_id=thread_id or "",
            priority=priority,
            **kwargs
        )
        
        self._messages[message.id] = message
        
        # Add to thread
        if thread_id:
            if thread_id not in self._threads:
                self._threads[thread_id] = MessageThread(id=thread_id)
            self._threads[thread_id].messages.append(message)
        
        # Deliver to recipients
        for recipient in recipients:
            self._agent_inbox[recipient].append(message.id)
            
            # Notify subscribers
            for callback in self._subscribers.get(recipient, []):
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
        
        # Broadcast if needed
        if message_type == MessageType.BROADCAST:
            for callback in self._broadcast_subscribers:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Broadcast callback error: {e}")
        
        return message
    
    async def broadcast(
        self,
        sender: str,
        content: str,
        **kwargs
    ) -> Message:
        """Broadcast message to all agents."""
        return await self.send(
            sender=sender,
            recipients=["*"],
            content=content,
            message_type=MessageType.BROADCAST,
            **kwargs
        )
    
    async def reply(
        self,
        original_message_id: str,
        sender: str,
        content: str,
        **kwargs
    ) -> Optional[Message]:
        """Reply to a message."""
        original = self._messages.get(original_message_id)
        if not original:
            return None
        
        return await self.send(
            sender=sender,
            recipients=[original.sender],
            content=content,
            message_type=MessageType.RESPONSE,
            thread_id=original.thread_id,
            in_reply_to=original_message_id,
            **kwargs
        )
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
        return self._messages.get(message_id)
    
    def get_inbox(self, agent_id: str) -> List[Message]:
        """Get agent's inbox."""
        message_ids = self._agent_inbox.get(agent_id, [])
        return [self._messages[mid] for mid in message_ids if mid in self._messages]
    
    def get_unread(self, agent_id: str) -> List[Message]:
        """Get unread messages for agent."""
        inbox = self.get_inbox(agent_id)
        return [m for m in inbox if agent_id not in m.read_by]
    
    def mark_read(self, message_id: str, agent_id: str):
        """Mark message as read."""
        message = self._messages.get(message_id)
        if message:
            message.read_by.add(agent_id)
    
    def get_thread(self, thread_id: str) -> Optional[MessageThread]:
        """Get message thread."""
        return self._threads.get(thread_id)
    
    def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe to messages for an agent."""
        self._subscribers[agent_id].append(callback)
    
    def subscribe_broadcast(self, callback: Callable):
        """Subscribe to broadcast messages."""
        self._broadcast_subscribers.append(callback)
    
    def unsubscribe(self, agent_id: str, callback: Callable):
        """Unsubscribe from messages."""
        if callback in self._subscribers.get(agent_id, []):
            self._subscribers[agent_id].remove(callback)
    
    def get_conversation_history(
        self,
        agent1: str,
        agent2: str,
        limit: int = 50
    ) -> List[Message]:
        """Get conversation history between two agents."""
        messages = []
        for message in self._messages.values():
            if (message.sender == agent1 and agent2 in message.recipients) or \
               (message.sender == agent2 and agent1 in message.recipients):
                messages.append(message)
        
        messages.sort(key=lambda m: m.timestamp)
        return messages[-limit:]


# ============================================================
# CONVERSATION MANAGER
# ============================================================

class ConversationManager:
    """Manages conversations between agents."""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self._conversations: Dict[str, Conversation] = {}
    
    def create_conversation(
        self,
        participants: List[str],
        topic: str = ""
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            participants=participants,
            topic=topic,
        )
        self._conversations[conversation.id] = conversation
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        **kwargs
    ) -> Optional[Message]:
        """Add message to conversation."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return None
        
        # Send to all other participants
        recipients = [p for p in conversation.participants if p != sender]
        
        message = await self.message_bus.send(
            sender=sender,
            recipients=recipients,
            content=content,
            thread_id=conversation_id,
            **kwargs
        )
        
        conversation.messages.append(message)
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)
    
    def list_conversations(
        self,
        participant: Optional[str] = None
    ) -> List[Conversation]:
        """List conversations, optionally filtered by participant."""
        conversations = list(self._conversations.values())
        if participant:
            conversations = [
                c for c in conversations 
                if participant in c.participants
            ]
        return conversations
    
    def close_conversation(self, conversation_id: str):
        """Close/archive a conversation."""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            conversation.status = "archived"
    
    def get_context_for_agent(
        self,
        conversation_id: str,
        agent_id: str,
        max_messages: int = 10
    ) -> str:
        """Get conversation context formatted for agent."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return ""
        
        messages = conversation.messages[-max_messages:]
        context_lines = [f"Topic: {conversation.topic}\n"]
        
        for msg in messages:
            sender_label = "You" if msg.sender == agent_id else msg.sender
            context_lines.append(f"{sender_label}: {msg.content}")
        
        return "\n".join(context_lines)


# ============================================================
# PROTOCOL HANDLERS
# ============================================================

class MessageProtocol:
    """Base class for message protocols."""
    
    def encode(self, data: Any) -> str:
        """Encode data to message content."""
        return str(data)
    
    def decode(self, content: str) -> Any:
        """Decode message content to data."""
        return content


class JSONProtocol(MessageProtocol):
    """JSON message protocol."""
    
    def encode(self, data: Any) -> str:
        import json
        return json.dumps(data)
    
    def decode(self, content: str) -> Any:
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content


class StructuredProtocol(MessageProtocol):
    """Structured message protocol with headers."""
    
    def encode(self, data: Dict[str, Any]) -> str:
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def decode(self, content: str) -> Dict[str, Any]:
        result = {}
        for line in content.split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                result[key.strip()] = value.strip()
        return result


# ============================================================
# NOTIFICATION SERVICE
# ============================================================

class NotificationService:
    """Service for real-time notifications."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler."""
        self._handlers[event_type].append(handler)
    
    async def notify(self, event_type: str, data: Any):
        """Send notification."""
        for handler in self._handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
    
    async def notify_message_received(self, message: Message):
        """Notify about new message."""
        await self.notify("message_received", message)
    
    async def notify_task_completed(self, task_id: str, result: Any):
        """Notify about task completion."""
        await self.notify("task_completed", {"task_id": task_id, "result": result})
    
    async def notify_agent_status(self, agent_id: str, status: str):
        """Notify about agent status change."""
        await self.notify("agent_status", {"agent_id": agent_id, "status": status})

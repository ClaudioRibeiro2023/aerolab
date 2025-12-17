"""
Conversations API - CRUD endpoints for chat conversations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# ============================================
# IN-MEMORY STORAGE (replace with DB later)
# ============================================

_conversations_store: Dict[str, Dict] = {}
_messages_store: Dict[str, List[Dict]] = {}


# ============================================
# MODELS
# ============================================

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    model: Optional[str] = "llama-3.1-8b-instant"
    project_id: Optional[str] = None
    persona_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tags: Optional[List[str]] = None


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str
    agent_id: Optional[str] = None
    model: Optional[str] = None
    attachments: Optional[List[Dict]] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    model: str
    project_id: Optional[str] = None
    persona_id: Optional[str] = None
    pinned: bool = False
    archived: bool = False
    message_count: int = 0
    total_tokens: int = 0
    created_at: str
    updated_at: str
    last_message_at: Optional[str] = None
    tags: List[str] = []


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    agent_id: Optional[str] = None
    model: Optional[str] = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    created_at: str


# ============================================
# HELPERS
# ============================================

def generate_title(content: str, agent_name: Optional[str] = None) -> str:
    """Generate a title from first message content."""
    if agent_name:
        prefix = f"Chat com {agent_name}"
    else:
        prefix = "Conversa"
    
    if content:
        truncated = content[:50] + "..." if len(content) > 50 else content
        return truncated
    
    date = datetime.now().strftime("%d/%m %H:%M")
    return f"{prefix} - {date}"


# ============================================
# CONVERSATION ENDPOINTS
# ============================================

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str = Query(default="default_user"),
    project_id: Optional[str] = None,
    archived: bool = False,
    pinned: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
):
    """List conversations for a user."""
    conversations = list(_conversations_store.values())
    
    # Filter by user
    conversations = [c for c in conversations if c.get("user_id") == user_id]
    
    # Filter by project
    if project_id:
        conversations = [c for c in conversations if c.get("project_id") == project_id]
    
    # Filter by archived status
    conversations = [c for c in conversations if c.get("archived", False) == archived]
    
    # Filter by pinned
    if pinned is not None:
        conversations = [c for c in conversations if c.get("pinned", False) == pinned]
    
    # Sort by updated_at desc
    conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    # Pagination
    conversations = conversations[offset:offset + limit]
    
    return conversations


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    user_id: str = Query(default="default_user"),
):
    """Create a new conversation."""
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conversation = {
        "id": conv_id,
        "user_id": user_id,
        "title": data.title or generate_title("", data.agent_name),
        "agent_id": data.agent_id,
        "agent_name": data.agent_name,
        "model": data.model or "llama-3.1-8b-instant",
        "project_id": data.project_id,
        "persona_id": data.persona_id,
        "system_prompt": data.system_prompt,
        "pinned": False,
        "archived": False,
        "message_count": 0,
        "total_tokens": 0,
        "created_at": now,
        "updated_at": now,
        "last_message_at": None,
        "tags": [],
    }
    
    _conversations_store[conv_id] = conversation
    _messages_store[conv_id] = []
    
    logger.info(f"Created conversation {conv_id} for user {user_id}")
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a specific conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return _conversations_store[conversation_id]


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: str, data: ConversationUpdate):
    """Update a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = _conversations_store[conversation_id]
    
    if data.title is not None:
        conversation["title"] = data.title
    if data.pinned is not None:
        conversation["pinned"] = data.pinned
    if data.archived is not None:
        conversation["archived"] = data.archived
    if data.model is not None:
        conversation["model"] = data.model
    if data.system_prompt is not None:
        conversation["system_prompt"] = data.system_prompt
    if data.tags is not None:
        conversation["tags"] = data.tags
    
    conversation["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated conversation {conversation_id}")
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, hard: bool = False):
    """Delete a conversation (soft delete by default)."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if hard:
        del _conversations_store[conversation_id]
        if conversation_id in _messages_store:
            del _messages_store[conversation_id]
        logger.info(f"Hard deleted conversation {conversation_id}")
    else:
        _conversations_store[conversation_id]["archived"] = True
        _conversations_store[conversation_id]["updated_at"] = datetime.now().isoformat()
        logger.info(f"Soft deleted (archived) conversation {conversation_id}")
    
    return {"deleted": conversation_id, "hard": hard}


# ============================================
# MESSAGE ENDPOINTS
# ============================================

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    before: Optional[str] = None,
):
    """List messages in a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = _messages_store.get(conversation_id, [])
    
    # Filter by before timestamp
    if before:
        messages = [m for m in messages if m.get("created_at", "") < before]
    
    # Sort by created_at
    messages.sort(key=lambda x: x.get("created_at", ""))
    
    # Pagination
    messages = messages[offset:offset + limit]
    
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(conversation_id: str, data: MessageCreate):
    """Add a message to a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    msg_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    message = {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": data.role,
        "content": data.content,
        "agent_id": data.agent_id,
        "model": data.model,
        "attachments": data.attachments or [],
        "tokens_prompt": 0,
        "tokens_completion": 0,
        "created_at": now,
    }
    
    if conversation_id not in _messages_store:
        _messages_store[conversation_id] = []
    
    _messages_store[conversation_id].append(message)
    
    # Update conversation
    conversation = _conversations_store[conversation_id]
    conversation["message_count"] = len(_messages_store[conversation_id])
    conversation["updated_at"] = now
    conversation["last_message_at"] = now
    
    # Auto-generate title from first user message
    if conversation["message_count"] == 1 and data.role == "user":
        conversation["title"] = generate_title(data.content, conversation.get("agent_name"))
    
    logger.debug(f"Added message {msg_id} to conversation {conversation_id}")
    return message


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: str, message_id: str):
    """Delete a specific message."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = _messages_store.get(conversation_id, [])
    original_count = len(messages)
    
    _messages_store[conversation_id] = [m for m in messages if m.get("id") != message_id]
    
    if len(_messages_store[conversation_id]) == original_count:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update conversation count
    _conversations_store[conversation_id]["message_count"] = len(_messages_store[conversation_id])
    _conversations_store[conversation_id]["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Deleted message {message_id} from conversation {conversation_id}")
    return {"deleted": message_id}


# ============================================
# UTILITY ENDPOINTS
# ============================================

@router.post("/{conversation_id}/clear")
async def clear_messages(conversation_id: str):
    """Clear all messages in a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    count = len(_messages_store.get(conversation_id, []))
    _messages_store[conversation_id] = []
    
    conversation = _conversations_store[conversation_id]
    conversation["message_count"] = 0
    conversation["total_tokens"] = 0
    conversation["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Cleared {count} messages from conversation {conversation_id}")
    return {"cleared": count, "conversation_id": conversation_id}


@router.post("/{conversation_id}/pin")
async def toggle_pin(conversation_id: str):
    """Toggle pin status of a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = _conversations_store[conversation_id]
    conversation["pinned"] = not conversation.get("pinned", False)
    conversation["updated_at"] = datetime.now().isoformat()
    
    return {"pinned": conversation["pinned"], "conversation_id": conversation_id}


@router.post("/{conversation_id}/archive")
async def toggle_archive(conversation_id: str):
    """Toggle archive status of a conversation."""
    if conversation_id not in _conversations_store:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = _conversations_store[conversation_id]
    conversation["archived"] = not conversation.get("archived", False)
    conversation["updated_at"] = datetime.now().isoformat()
    
    return {"archived": conversation["archived"], "conversation_id": conversation_id}

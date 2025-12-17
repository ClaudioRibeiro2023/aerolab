"""
Chat Service - Serviço principal de chat.

Orquestra todos os componentes:
- Conversas e mensagens
- Sessões
- Streaming
- Persistência
- Agentes
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
import uuid
import logging

from .core.conversation import Conversation, ConversationStatus, ConversationSettings
from .core.message import Message, MessageRole, MessageStatus
from .core.session import Session, SessionManager, get_session_manager
from .core.context import ContextBuilder, get_context_builder
from .streaming.streamer import ChatStreamer, get_chat_streamer
from .streaming.events import StreamEvent, StreamEventType

logger = logging.getLogger(__name__)


class ChatService:
    """
    Serviço principal de chat.
    
    Fornece API de alto nível para:
    - Criar e gerenciar conversas
    - Enviar mensagens com streaming
    - Gerenciar branches e regeneração
    - Integrar com agentes
    
    Uso:
    ```python
    chat = ChatService()
    await chat.initialize()
    
    # Criar conversa
    conversation = await chat.create_conversation(
        user_id="user_123",
        agent_id="assistant"
    )
    
    # Enviar mensagem com streaming
    async for event in chat.send_message_stream(
        conversation_id=conversation.id,
        content="Hello!",
        user_id="user_123"
    ):
        print(event.delta, end="")
    
    # Obter histórico
    messages = await chat.get_messages(conversation.id)
    ```
    """
    
    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        context_builder: Optional[ContextBuilder] = None,
        streamer: Optional[ChatStreamer] = None
    ):
        self._session_manager = session_manager
        self._context_builder = context_builder
        self._streamer = streamer
        
        # Storage em memória (em produção: Supabase)
        self._conversations: Dict[str, Conversation] = {}
        self._messages: Dict[str, List[Message]] = {}
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Inicializa o serviço."""
        if self._initialized:
            return
        
        # Inicializar componentes
        if self._session_manager is None:
            self._session_manager = get_session_manager()
        
        if self._context_builder is None:
            self._context_builder = get_context_builder()
        
        if self._streamer is None:
            self._streamer = get_chat_streamer()
        
        await self._session_manager.initialize()
        
        self._initialized = True
        logger.info("ChatService initialized")
    
    async def shutdown(self) -> None:
        """Encerra o serviço."""
        if self._session_manager:
            await self._session_manager.shutdown()
        self._initialized = False
    
    # ==================== Conversations ====================
    
    async def create_conversation(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        title: Optional[str] = None,
        project_id: Optional[str] = None,
        settings: Optional[ConversationSettings] = None
    ) -> Conversation:
        """
        Cria uma nova conversa.
        
        Args:
            user_id: ID do usuário
            agent_id: ID do agente principal
            title: Título (opcional, será auto-gerado)
            project_id: ID do projeto (opcional)
            settings: Configurações personalizadas
        
        Returns:
            Conversa criada
        """
        conversation = Conversation(
            user_id=user_id,
            title=title or "Nova Conversa",
            auto_title=title is None,
            project_id=project_id,
            settings=settings or ConversationSettings()
        )
        
        if agent_id:
            conversation.add_agent(agent_id)
        
        # Persistir
        self._conversations[conversation.id] = conversation
        self._messages[conversation.id] = []
        
        logger.debug(f"Created conversation {conversation.id} for user {user_id}")
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Obtém uma conversa por ID."""
        conv = self._conversations.get(conversation_id)
        if conv:
            # Carregar mensagens
            conv.messages = self._messages.get(conversation_id, [])
        return conv
    
    async def list_conversations(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """Lista conversas de um usuário."""
        convs = [
            c for c in self._conversations.values()
            if c.user_id == user_id
        ]
        
        if project_id:
            convs = [c for c in convs if c.project_id == project_id]
        
        if status:
            convs = [c for c in convs if c.status == status]
        
        # Ordenar por última atividade
        convs.sort(key=lambda c: c.last_message_at or c.created_at, reverse=True)
        
        return convs[offset:offset + limit]
    
    async def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        pinned: Optional[bool] = None,
        settings: Optional[Dict] = None
    ) -> Optional[Conversation]:
        """Atualiza uma conversa."""
        conv = self._conversations.get(conversation_id)
        if not conv:
            return None
        
        if title is not None:
            conv.update_title(title)
        
        if pinned is not None:
            conv.pinned = pinned
        
        if settings:
            for key, value in settings.items():
                if hasattr(conv.settings, key):
                    setattr(conv.settings, key, value)
        
        conv.updated_at = datetime.now()
        return conv
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """Arquiva uma conversa."""
        conv = self._conversations.get(conversation_id)
        if conv:
            conv.archive()
            return True
        return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Deleta uma conversa."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            self._messages.pop(conversation_id, None)
            return True
        return False
    
    # ==================== Messages ====================
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        user_id: str,
        agent_id: Optional[str] = None
    ) -> Message:
        """
        Envia uma mensagem (sem streaming).
        
        Para streaming, use send_message_stream().
        """
        conv = await self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Criar mensagem do usuário
        user_msg = Message.user(
            content=content,
            conversation_id=conversation_id,
            branch_id=conv.active_branch_id,
            user_id=user_id
        )
        
        # Adicionar à conversa
        conv.add_message(user_msg)
        self._messages[conversation_id].append(user_msg)
        
        # Obter resposta (simplificado - em produção integraria com agentes)
        assistant_msg = Message.assistant(
            content="Response placeholder",
            conversation_id=conversation_id,
            branch_id=conv.active_branch_id,
            agent_id=agent_id or conv.primary_agent_id
        )
        
        conv.add_message(assistant_msg)
        self._messages[conversation_id].append(assistant_msg)
        
        return assistant_msg
    
    async def send_message_stream(
        self,
        conversation_id: str,
        content: str,
        user_id: str,
        agent_id: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> AsyncIterator[StreamEvent]:
        """
        Envia mensagem com streaming.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            user_id: ID do usuário
            agent_id: ID do agente (opcional)
            tools: Ferramentas disponíveis
            
        Yields:
            StreamEvent com deltas e status
        """
        conv = await self.get_conversation(conversation_id)
        if not conv:
            yield StreamEvent.message_error(
                error=f"Conversation {conversation_id} not found",
                message_id="",
                code="not_found"
            )
            return
        
        # Criar mensagem do usuário
        user_msg = Message.user(
            content=content,
            conversation_id=conversation_id,
            branch_id=conv.active_branch_id,
            user_id=user_id
        )
        
        conv.add_message(user_msg)
        self._messages[conversation_id].append(user_msg)
        
        # Preparar mensagem do assistente
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            conversation_id=conversation_id,
            branch_id=conv.active_branch_id,
            agent_id=agent_id or conv.primary_agent_id,
            status=MessageStatus.STREAMING
        )
        
        full_content = ""
        message_id = ""
        
        try:
            async for event in self._streamer.stream(
                conversation=conv,
                user_message=content,
                agent_id=agent_id,
                tools=tools
            ):
                yield event
                
                if event.type == StreamEventType.MESSAGE_START:
                    message_id = event.message_id
                    assistant_msg.id = message_id
                
                elif event.type == StreamEventType.MESSAGE_DELTA:
                    full_content = event.content
                
                elif event.type == StreamEventType.MESSAGE_DONE:
                    assistant_msg.content = full_content
                    assistant_msg.mark_as_done()
                
                elif event.type == StreamEventType.MESSAGE_ERROR:
                    assistant_msg.mark_as_error(event.error or "Unknown error")
            
            # Adicionar à conversa
            conv.add_message(assistant_msg)
            self._messages[conversation_id].append(assistant_msg)
            
            # Auto-generate title se necessário
            if conv.auto_title and conv.message_count == 2:
                await self._generate_title(conv)
        
        except Exception as e:
            logger.exception(f"Error in send_message_stream: {e}")
            yield StreamEvent.message_error(
                error=str(e),
                message_id=message_id,
                code="error"
            )
    
    async def get_messages(
        self,
        conversation_id: str,
        branch_id: Optional[str] = None,
        limit: int = 100,
        before_id: Optional[str] = None
    ) -> List[Message]:
        """Obtém mensagens de uma conversa."""
        messages = self._messages.get(conversation_id, [])
        
        if branch_id:
            messages = [m for m in messages if m.branch_id == branch_id]
        
        if before_id:
            idx = next(
                (i for i, m in enumerate(messages) if m.id == before_id),
                len(messages)
            )
            messages = messages[:idx]
        
        return messages[-limit:]
    
    async def edit_message(
        self,
        conversation_id: str,
        message_id: str,
        new_content: str
    ) -> Optional[Message]:
        """Edita uma mensagem e cria branch."""
        conv = await self.get_conversation(conversation_id)
        if not conv:
            return None
        
        # Encontrar mensagem
        msg = next(
            (m for m in self._messages.get(conversation_id, []) if m.id == message_id),
            None
        )
        
        if not msg:
            return None
        
        # Criar novo branch
        branch = conv.create_branch(
            name=f"Edit {datetime.now().strftime('%H:%M')}",
            from_message_id=message_id
        )
        
        # Criar nova mensagem no branch
        new_msg = Message(
            role=msg.role,
            content=new_content,
            conversation_id=conversation_id,
            branch_id=branch.id,
            user_id=msg.user_id,
            agent_id=msg.agent_id,
            edited_at=datetime.now()
        )
        
        self._messages[conversation_id].append(new_msg)
        conv.switch_branch(branch.id)
        
        return new_msg
    
    async def regenerate_message(
        self,
        conversation_id: str,
        message_id: str
    ) -> AsyncIterator[StreamEvent]:
        """Regenera uma resposta."""
        conv = await self.get_conversation(conversation_id)
        if not conv:
            yield StreamEvent.message_error(
                error="Conversation not found",
                message_id="",
                code="not_found"
            )
            return
        
        # Encontrar mensagem e a anterior do usuário
        messages = self._messages.get(conversation_id, [])
        msg_idx = next(
            (i for i, m in enumerate(messages) if m.id == message_id),
            -1
        )
        
        if msg_idx <= 0:
            yield StreamEvent.message_error(
                error="Message not found or no previous user message",
                message_id="",
                code="not_found"
            )
            return
        
        user_msg = messages[msg_idx - 1]
        if not user_msg.is_user:
            yield StreamEvent.message_error(
                error="Previous message is not from user",
                message_id="",
                code="invalid"
            )
            return
        
        # Criar branch para regeneração
        branch = conv.create_branch(
            name=f"Regen {datetime.now().strftime('%H:%M')}",
            from_message_id=user_msg.id
        )
        conv.switch_branch(branch.id)
        
        # Stream nova resposta
        async for event in self._streamer.stream(
            conversation=conv,
            user_message=user_msg.content
        ):
            yield event
    
    async def add_reaction(
        self,
        conversation_id: str,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> bool:
        """Adiciona reação a uma mensagem."""
        messages = self._messages.get(conversation_id, [])
        msg = next((m for m in messages if m.id == message_id), None)
        
        if msg:
            msg.add_reaction(user_id, emoji)
            return True
        return False
    
    async def set_feedback(
        self,
        conversation_id: str,
        message_id: str,
        feedback: str
    ) -> bool:
        """Define feedback em uma mensagem."""
        messages = self._messages.get(conversation_id, [])
        msg = next((m for m in messages if m.id == message_id), None)
        
        if msg:
            msg.set_feedback(feedback)
            return True
        return False
    
    # ==================== Sessions ====================
    
    async def get_session(self, user_id: str) -> Session:
        """Obtém ou cria sessão para usuário."""
        return await self._session_manager.get_or_create_session(user_id)
    
    async def set_typing(self, user_id: str, conversation_id: str) -> None:
        """Marca usuário como digitando."""
        await self._session_manager.set_typing(user_id, conversation_id)
    
    async def clear_typing(self, user_id: str, conversation_id: str) -> None:
        """Remove indicador de digitação."""
        await self._session_manager.clear_typing(user_id, conversation_id)
    
    async def get_typing_users(self, conversation_id: str) -> List[str]:
        """Obtém usuários digitando em uma conversa."""
        return await self._session_manager.get_typing_users(conversation_id)
    
    # ==================== Helpers ====================
    
    async def _generate_title(self, conversation: Conversation) -> str:
        """Gera título automaticamente baseado na primeira mensagem."""
        messages = self._messages.get(conversation.id, [])
        if not messages:
            return "Nova Conversa"
        
        first_user_msg = next(
            (m for m in messages if m.is_user),
            None
        )
        
        if first_user_msg:
            # Simplificado: usar primeiras palavras
            words = first_user_msg.content.split()[:6]
            title = " ".join(words)
            if len(first_user_msg.content) > len(title):
                title += "..."
            
            conversation.update_title(title)
            return title
        
        return "Nova Conversa"
    
    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Conversation]:
        """Busca conversas por texto."""
        query_lower = query.lower()
        results = []
        
        for conv in self._conversations.values():
            if conv.user_id != user_id:
                continue
            
            # Buscar no título
            if query_lower in conv.title.lower():
                results.append(conv)
                continue
            
            # Buscar nas mensagens
            messages = self._messages.get(conv.id, [])
            for msg in messages:
                if query_lower in msg.content.lower():
                    results.append(conv)
                    break
        
        return results[:limit]


# Singleton
_chat_service: Optional[ChatService] = None


async def get_chat_service() -> ChatService:
    """Obtém o serviço de chat singleton."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
        await _chat_service.initialize()
    return _chat_service

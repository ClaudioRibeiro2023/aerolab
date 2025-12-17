"""
Context Builder - Construção inteligente de contexto para LLM.

Features:
- Sliding window com limite de tokens
- Sumarização automática de histórico
- Integração com memória de longo prazo
- RAG context injection
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from .message import Message, MessageRole
from .conversation import Conversation

logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    """
    Contexto construído para envio ao LLM.
    """
    # Mensagens formatadas
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    # Tokens estimados
    estimated_tokens: int = 0
    
    # System prompt
    system_prompt: str = ""
    
    # Custom instructions
    custom_instructions: Optional[str] = None
    
    # Memórias relevantes
    memories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Documentos RAG
    rag_documents: List[Dict[str, Any]] = field(default_factory=list)
    
    # Histórico sumarizado
    history_summary: Optional[str] = None
    
    # Metadata
    truncated: bool = False
    original_message_count: int = 0
    included_message_count: int = 0
    
    def to_api_messages(self) -> List[Dict[str, str]]:
        """Retorna mensagens formatadas para API."""
        api_messages = []
        
        # System prompt combinado
        system_content = self.system_prompt
        
        if self.custom_instructions:
            system_content += f"\n\n{self.custom_instructions}"
        
        if self.history_summary:
            system_content += f"\n\nPrevious conversation summary: {self.history_summary}"
        
        if self.memories:
            memory_text = "\n".join([m.get("content", "") for m in self.memories[:5]])
            system_content += f"\n\nRelevant memories:\n{memory_text}"
        
        if self.rag_documents:
            doc_text = "\n---\n".join([
                f"[{d.get('title', 'Document')}]\n{d.get('content', '')}" 
                for d in self.rag_documents[:3]
            ])
            system_content += f"\n\nRelevant documents:\n{doc_text}"
        
        if system_content:
            api_messages.append({
                "role": "system",
                "content": system_content.strip()
            })
        
        # Adicionar mensagens
        api_messages.extend(self.messages)
        
        return api_messages


class ContextBuilder:
    """
    Construtor de contexto inteligente.
    
    Gerencia:
    - Limite de tokens (sliding window)
    - Sumarização de histórico antigo
    - Injeção de memórias relevantes
    - Contexto RAG
    """
    
    # Estimativa: ~4 chars por token (aproximado)
    CHARS_PER_TOKEN = 4
    
    def __init__(
        self,
        max_tokens: int = 8000,
        max_messages: int = 50,
        summarize_after: int = 20,
        include_system_prompt: bool = True
    ):
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.summarize_after = summarize_after
        self.include_system_prompt = include_system_prompt
    
    def estimate_tokens(self, text: str) -> int:
        """Estima número de tokens em um texto."""
        return len(text) // self.CHARS_PER_TOKEN
    
    def estimate_message_tokens(self, message: Message) -> int:
        """Estima tokens de uma mensagem."""
        # Conteúdo principal
        tokens = self.estimate_tokens(message.content)
        
        # Overhead do role
        tokens += 4
        
        # Tool calls
        for tc in message.tool_calls:
            tokens += self.estimate_tokens(str(tc.arguments))
            if tc.result:
                tokens += self.estimate_tokens(tc.result)
        
        return tokens
    
    async def build(
        self,
        conversation: Conversation,
        new_message: Optional[str] = None,
        memories: Optional[List[Dict]] = None,
        rag_documents: Optional[List[Dict]] = None
    ) -> ChatContext:
        """
        Constrói contexto para envio ao LLM.
        
        Args:
            conversation: Conversa atual
            new_message: Nova mensagem do usuário (opcional)
            memories: Memórias relevantes (opcional)
            rag_documents: Documentos RAG (opcional)
        
        Returns:
            ChatContext pronto para envio
        """
        context = ChatContext(
            system_prompt=conversation.settings.system_prompt or "",
            custom_instructions=conversation.settings.custom_instructions,
            memories=memories or [],
            rag_documents=rag_documents or [],
            original_message_count=len(conversation.messages)
        )
        
        # Calcular tokens disponíveis
        available_tokens = self.max_tokens
        
        # Reservar tokens para system prompt
        if context.system_prompt:
            available_tokens -= self.estimate_tokens(context.system_prompt)
        
        if context.custom_instructions:
            available_tokens -= self.estimate_tokens(context.custom_instructions)
        
        # Reservar para memórias e RAG
        for mem in context.memories[:5]:
            available_tokens -= self.estimate_tokens(mem.get("content", ""))
        
        for doc in context.rag_documents[:3]:
            available_tokens -= self.estimate_tokens(doc.get("content", ""))
        
        # Reservar para nova mensagem
        if new_message:
            available_tokens -= self.estimate_tokens(new_message)
        
        # Reservar margem para resposta
        available_tokens -= 1000
        
        # Selecionar mensagens (mais recentes primeiro)
        messages = conversation.get_messages()
        
        # Se tem muitas mensagens, sumarizar antigas
        if len(messages) > self.summarize_after:
            old_messages = messages[:-self.summarize_after]
            recent_messages = messages[-self.summarize_after:]
            
            # Gerar sumário do histórico antigo
            context.history_summary = await self._summarize_messages(old_messages)
            available_tokens -= self.estimate_tokens(context.history_summary)
            
            messages = recent_messages
        
        # Selecionar mensagens que cabem no limite
        selected_messages = []
        total_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = self.estimate_message_tokens(msg)
            
            if total_tokens + msg_tokens <= available_tokens:
                selected_messages.insert(0, msg)
                total_tokens += msg_tokens
            else:
                context.truncated = True
                break
        
        # Converter para formato de API
        context.messages = [msg.to_api_format() for msg in selected_messages]
        context.included_message_count = len(selected_messages)
        context.estimated_tokens = total_tokens
        
        return context
    
    async def _summarize_messages(self, messages: List[Message]) -> str:
        """
        Gera sumário de mensagens antigas.
        
        Em produção, isso usaria um LLM para sumarizar.
        Aqui fazemos uma versão simplificada.
        """
        if not messages:
            return ""
        
        # Versão simplificada: extrair pontos principais
        summary_parts = []
        
        # Agrupar por tópicos (mensagens de usuário)
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        
        for i, msg in enumerate(user_messages[:10]):  # Máximo 10 tópicos
            content_preview = msg.content[:100]
            if len(msg.content) > 100:
                content_preview += "..."
            summary_parts.append(f"- User asked about: {content_preview}")
        
        if len(user_messages) > 10:
            summary_parts.append(f"- ...and {len(user_messages) - 10} more topics")
        
        return "\n".join(summary_parts)
    
    async def build_for_regenerate(
        self,
        conversation: Conversation,
        message_id: str,
        memories: Optional[List[Dict]] = None,
        rag_documents: Optional[List[Dict]] = None
    ) -> ChatContext:
        """
        Constrói contexto para regenerar uma mensagem.
        
        Inclui mensagens até o ponto de regeneração.
        """
        # Encontrar índice da mensagem
        messages = conversation.get_messages()
        regen_index = next(
            (i for i, m in enumerate(messages) if m.id == message_id),
            -1
        )
        
        if regen_index == -1:
            raise ValueError(f"Message {message_id} not found")
        
        # Criar conversa temporária com mensagens até o ponto
        temp_conv = Conversation(
            id=conversation.id,
            settings=conversation.settings
        )
        temp_conv.messages = messages[:regen_index]
        
        # A mensagem que estamos regenerando é do usuário
        user_msg = messages[regen_index]
        
        return await self.build(
            temp_conv,
            new_message=user_msg.content if user_msg.is_user else None,
            memories=memories,
            rag_documents=rag_documents
        )
    
    async def build_for_branch(
        self,
        conversation: Conversation,
        branch_id: str,
        memories: Optional[List[Dict]] = None,
        rag_documents: Optional[List[Dict]] = None
    ) -> ChatContext:
        """
        Constrói contexto para um branch específico.
        """
        # Obter mensagens do branch
        branch_messages = conversation.get_messages(branch_id)
        
        # Criar conversa temporária
        temp_conv = Conversation(
            id=conversation.id,
            settings=conversation.settings
        )
        temp_conv.messages = branch_messages
        temp_conv.active_branch_id = branch_id
        
        return await self.build(temp_conv, memories=memories, rag_documents=rag_documents)


# Singleton
_context_builder: Optional[ContextBuilder] = None


def get_context_builder(**kwargs) -> ContextBuilder:
    """Obtém o construtor de contexto singleton."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder(**kwargs)
    return _context_builder

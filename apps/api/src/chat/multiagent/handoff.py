"""
Agent Handoff - Transferência entre agentes.

Permite que um agente transfira a conversa para outro
mantendo contexto e histórico.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class HandoffReason(str, Enum):
    """Razões para handoff."""
    EXPERTISE = "expertise"     # Outro agente é mais qualificado
    ESCALATION = "escalation"   # Escalação para suporte
    USER_REQUEST = "user_request"  # Usuário pediu
    TASK_COMPLETE = "task_complete"  # Tarefa completada
    ERROR = "error"             # Erro no agente atual
    TIMEOUT = "timeout"         # Timeout


@dataclass
class HandoffContext:
    """Contexto para transferência."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Agentes
    from_agent_id: str = ""
    to_agent_id: str = ""
    
    # Razão
    reason: HandoffReason = HandoffReason.EXPERTISE
    reason_detail: str = ""
    
    # Contexto
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    
    # Conversa
    conversation_id: str = ""
    message_count: int = 0
    
    # Timestamps
    initiated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Status
    accepted: bool = False
    rejected_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "reason": self.reason.value,
            "reason_detail": self.reason_detail,
            "summary": self.summary,
            "key_points": self.key_points,
            "pending_tasks": self.pending_tasks,
            "conversation_id": self.conversation_id,
            "message_count": self.message_count,
            "initiated_at": self.initiated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "accepted": self.accepted
        }


class AgentHandoff:
    """
    Gerenciador de handoffs entre agentes.
    """
    
    def __init__(self):
        self._pending_handoffs: Dict[str, HandoffContext] = {}
        self._completed_handoffs: List[HandoffContext] = []
    
    async def initiate(
        self,
        from_agent_id: str,
        to_agent_id: str,
        conversation_id: str,
        reason: HandoffReason = HandoffReason.EXPERTISE,
        reason_detail: str = "",
        summary: str = "",
        key_points: Optional[List[str]] = None,
        pending_tasks: Optional[List[str]] = None
    ) -> HandoffContext:
        """
        Inicia um handoff.
        
        Args:
            from_agent_id: Agente atual
            to_agent_id: Agente destino
            conversation_id: ID da conversa
            reason: Razão do handoff
            reason_detail: Detalhes adicionais
            summary: Resumo da conversa
            key_points: Pontos importantes
            pending_tasks: Tarefas pendentes
            
        Returns:
            HandoffContext criado
        """
        context = HandoffContext(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            conversation_id=conversation_id,
            reason=reason,
            reason_detail=reason_detail,
            summary=summary,
            key_points=key_points or [],
            pending_tasks=pending_tasks or []
        )
        
        self._pending_handoffs[context.id] = context
        
        logger.info(
            f"Handoff initiated: {from_agent_id} -> {to_agent_id} "
            f"(reason: {reason.value})"
        )
        
        return context
    
    async def accept(self, handoff_id: str) -> Optional[HandoffContext]:
        """Aceita um handoff."""
        context = self._pending_handoffs.pop(handoff_id, None)
        
        if context:
            context.accepted = True
            context.completed_at = datetime.now()
            self._completed_handoffs.append(context)
            
            logger.info(f"Handoff accepted: {handoff_id}")
        
        return context
    
    async def reject(
        self,
        handoff_id: str,
        reason: str = ""
    ) -> Optional[HandoffContext]:
        """Rejeita um handoff."""
        context = self._pending_handoffs.pop(handoff_id, None)
        
        if context:
            context.accepted = False
            context.rejected_reason = reason
            context.completed_at = datetime.now()
            self._completed_handoffs.append(context)
            
            logger.info(f"Handoff rejected: {handoff_id} ({reason})")
        
        return context
    
    async def get_pending(self, agent_id: str) -> List[HandoffContext]:
        """Obtém handoffs pendentes para um agente."""
        return [
            h for h in self._pending_handoffs.values()
            if h.to_agent_id == agent_id
        ]
    
    async def generate_summary(
        self,
        conversation_id: str,
        messages: List[Dict]
    ) -> str:
        """
        Gera resumo da conversa para handoff.
        
        Em produção: usar LLM para sumarizar.
        """
        if not messages:
            return "No messages in conversation."
        
        # Simplificado: extrair últimas mensagens
        recent = messages[-5:]
        summary_parts = []
        
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:100]
            summary_parts.append(f"- {role}: {content}...")
        
        return "\n".join(summary_parts)
    
    async def extract_key_points(
        self,
        conversation_id: str,
        messages: List[Dict]
    ) -> List[str]:
        """
        Extrai pontos-chave da conversa.
        
        Em produção: usar LLM para extrair.
        """
        # Simplificado: primeiras mensagens de usuário
        user_messages = [m for m in messages if m.get("role") == "user"]
        
        return [
            m.get("content", "")[:50] + "..."
            for m in user_messages[:3]
        ]


# Singleton
_agent_handoff: Optional[AgentHandoff] = None


def get_agent_handoff() -> AgentHandoff:
    global _agent_handoff
    if _agent_handoff is None:
        _agent_handoff = AgentHandoff()
    return _agent_handoff

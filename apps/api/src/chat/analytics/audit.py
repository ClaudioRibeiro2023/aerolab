"""
Audit Log - Log de auditoria para compliance.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Ações auditadas."""
    # Conversas
    CONVERSATION_CREATE = "conversation.create"
    CONVERSATION_DELETE = "conversation.delete"
    CONVERSATION_ARCHIVE = "conversation.archive"
    CONVERSATION_SHARE = "conversation.share"
    
    # Mensagens
    MESSAGE_SEND = "message.send"
    MESSAGE_EDIT = "message.edit"
    MESSAGE_DELETE = "message.delete"
    MESSAGE_REGENERATE = "message.regenerate"
    
    # Agentes
    AGENT_SELECT = "agent.select"
    AGENT_HANDOFF = "agent.handoff"
    
    # Dados
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    
    # Configurações
    SETTINGS_UPDATE = "settings.update"
    INSTRUCTIONS_UPDATE = "instructions.update"
    
    # Acesso
    LOGIN = "login"
    LOGOUT = "logout"


@dataclass
class AuditEntry:
    """Entrada de auditoria."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Ação
    action: AuditAction = AuditAction.MESSAGE_SEND
    
    # Quem
    user_id: str = ""
    organization_id: Optional[str] = None
    
    # O quê
    resource_type: str = ""  # conversation, message, agent, etc.
    resource_id: str = ""
    
    # Detalhes
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Contexto
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Resultado
    success: bool = True
    error_message: Optional[str] = None
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "action": self.action.value,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


class AuditLog:
    """
    Log de auditoria para compliance enterprise.
    
    Registra todas as ações para:
    - Compliance (GDPR, HIPAA, SOC2)
    - Segurança
    - Troubleshooting
    """
    
    def __init__(self, retention_days: int = 90):
        self._entries: List[AuditEntry] = []
        self.retention_days = retention_days
    
    async def log(
        self,
        action: AuditAction,
        user_id: str,
        resource_type: str = "",
        resource_id: str = "",
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        organization_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditEntry:
        """Registra uma ação."""
        entry = AuditEntry(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
        
        self._entries.append(entry)
        
        # Log também no logger padrão
        log_msg = f"AUDIT: {action.value} by {user_id} on {resource_type}/{resource_id}"
        if success:
            logger.info(log_msg)
        else:
            logger.warning(f"{log_msg} - FAILED: {error_message}")
        
        return entry
    
    async def log_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        action: str = "send"
    ) -> AuditEntry:
        """Shortcut para log de mensagem."""
        action_map = {
            "send": AuditAction.MESSAGE_SEND,
            "edit": AuditAction.MESSAGE_EDIT,
            "delete": AuditAction.MESSAGE_DELETE,
            "regenerate": AuditAction.MESSAGE_REGENERATE
        }
        
        return await self.log(
            action=action_map.get(action, AuditAction.MESSAGE_SEND),
            user_id=user_id,
            resource_type="message",
            resource_id=message_id,
            details={"conversation_id": conversation_id}
        )
    
    async def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Consulta o log de auditoria."""
        results = self._entries
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if action:
            results = [e for e in results if e.action == action]
        
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]
        
        if end_date:
            results = [e for e in results if e.timestamp <= end_date]
        
        # Ordenar por timestamp desc
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)
        
        return results[:limit]
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtém resumo de atividade do usuário."""
        cutoff = datetime.now().replace(hour=0, minute=0, second=0)
        cutoff = cutoff.replace(day=cutoff.day - days) if cutoff.day > days else cutoff
        
        user_entries = [
            e for e in self._entries
            if e.user_id == user_id and e.timestamp >= cutoff
        ]
        
        # Agrupar por ação
        by_action: Dict[str, int] = {}
        for e in user_entries:
            by_action[e.action.value] = by_action.get(e.action.value, 0) + 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(user_entries),
            "by_action": by_action,
            "last_activity": user_entries[0].timestamp.isoformat() if user_entries else None
        }
    
    async def export(
        self,
        user_id: Optional[str] = None,
        format: str = "json"
    ) -> str:
        """Exporta log para formato específico."""
        entries = await self.query(user_id=user_id, limit=10000)
        
        if format == "json":
            import json
            return json.dumps([e.to_dict() for e in entries], indent=2)
        
        elif format == "csv":
            lines = ["id,action,user_id,resource_type,resource_id,success,timestamp"]
            for e in entries:
                lines.append(
                    f"{e.id},{e.action.value},{e.user_id},"
                    f"{e.resource_type},{e.resource_id},{e.success},{e.timestamp.isoformat()}"
                )
            return "\n".join(lines)
        
        return ""


# Singleton
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log

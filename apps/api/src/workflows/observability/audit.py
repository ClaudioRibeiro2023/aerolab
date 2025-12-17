"""
Audit Log para Workflows.

Registra todas as ações para:
- Compliance
- Debugging
- Analytics
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import json


class AuditAction(Enum):
    """Tipos de ações auditáveis."""
    # Workflow
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
    
    # Step
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    STEP_RETRIED = "step.retried"
    
    # Trigger
    TRIGGER_CREATED = "trigger.created"
    TRIGGER_FIRED = "trigger.fired"
    
    # Access
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"


@dataclass
class AuditEntry:
    """Entrada de audit log."""
    id: str
    action: AuditAction
    timestamp: datetime = field(default_factory=datetime.now)
    actor: str = "system"
    resource_type: str = ""
    resource_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "action": self.action.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "success": self.success,
            "error": self.error
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AuditLog:
    """
    Sistema de audit log.
    
    Exemplo:
        audit = AuditLog()
        
        # Registrar ação
        audit.log(
            action=AuditAction.WORKFLOW_STARTED,
            actor="user@example.com",
            resource_type="workflow",
            resource_id="my-workflow",
            details={"execution_id": "exec-123"}
        )
        
        # Buscar logs
        entries = audit.query(
            resource_type="workflow",
            resource_id="my-workflow",
            limit=100
        )
    """
    
    def __init__(self, max_entries: int = 10000):
        self._entries: List[AuditEntry] = []
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._counter = 0
    
    def log(
        self,
        action: AuditAction,
        actor: str = "system",
        resource_type: str = "",
        resource_id: str = "",
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> AuditEntry:
        """Registra uma entrada de audit."""
        with self._lock:
            self._counter += 1
            entry = AuditEntry(
                id=f"audit_{self._counter}",
                action=action,
                actor=actor,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                success=success,
                error=error
            )
            
            self._entries.append(entry)
            
            # Limitar tamanho
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]
            
            return entry
    
    def query(
        self,
        action: Optional[AuditAction] = None,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Busca entradas de audit."""
        with self._lock:
            results = self._entries.copy()
            
            if action:
                results = [e for e in results if e.action == action]
            
            if actor:
                results = [e for e in results if e.actor == actor]
            
            if resource_type:
                results = [e for e in results if e.resource_type == resource_type]
            
            if resource_id:
                results = [e for e in results if e.resource_id == resource_id]
            
            if since:
                results = [e for e in results if e.timestamp >= since]
            
            if until:
                results = [e for e in results if e.timestamp <= until]
            
            if success is not None:
                results = [e for e in results if e.success == success]
            
            return results[-limit:]
    
    def get_recent(self, limit: int = 50) -> List[AuditEntry]:
        """Retorna entradas recentes."""
        with self._lock:
            return self._entries[-limit:]
    
    def export(self, format: str = "json") -> str:
        """Exporta logs."""
        with self._lock:
            if format == "json":
                return json.dumps([e.to_dict() for e in self._entries], indent=2)
            elif format == "jsonl":
                return "\n".join(e.to_json() for e in self._entries)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def clear(self) -> int:
        """Limpa logs. Retorna quantidade removida."""
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count


# Singleton
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """Obtém audit log global."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log

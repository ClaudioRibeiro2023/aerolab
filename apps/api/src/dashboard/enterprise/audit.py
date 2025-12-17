"""
Audit Logger - Log de auditoria para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Ações auditáveis."""
    # Dashboard
    DASHBOARD_CREATE = "dashboard.create"
    DASHBOARD_UPDATE = "dashboard.update"
    DASHBOARD_DELETE = "dashboard.delete"
    DASHBOARD_VIEW = "dashboard.view"
    DASHBOARD_SHARE = "dashboard.share"
    DASHBOARD_EXPORT = "dashboard.export"
    DASHBOARD_IMPORT = "dashboard.import"
    
    # Widget
    WIDGET_CREATE = "widget.create"
    WIDGET_UPDATE = "widget.update"
    WIDGET_DELETE = "widget.delete"
    
    # Alert
    ALERT_CREATE = "alert.create"
    ALERT_UPDATE = "alert.update"
    ALERT_DELETE = "alert.delete"
    ALERT_TRIGGER = "alert.trigger"
    ALERT_ACKNOWLEDGE = "alert.acknowledge"
    
    # User/Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_INVITE = "user.invite"
    USER_ROLE_CHANGE = "user.role_change"
    
    # Admin
    SETTINGS_UPDATE = "settings.update"
    DATASOURCE_CREATE = "datasource.create"
    DATASOURCE_UPDATE = "datasource.update"
    DATASOURCE_DELETE = "datasource.delete"
    
    # System
    SYSTEM_ERROR = "system.error"
    API_ACCESS = "api.access"


class AuditSeverity(str, Enum):
    """Severidade do evento."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Evento de auditoria."""
    id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Ação
    action: AuditAction = AuditAction.DASHBOARD_VIEW
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Contexto
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Recurso
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Detalhes
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Mudanças
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    
    # Request info
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Resultado
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "severity": self.severity.value,
            "userId": self.user_id,
            "tenantId": self.tenant_id,
            "sessionId": self.session_id,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "resourceName": self.resource_name,
            "description": self.description,
            "details": self.details,
            "oldValue": self.old_value,
            "newValue": self.new_value,
            "ipAddress": self.ip_address,
            "userAgent": self.user_agent,
            "requestId": self.request_id,
            "success": self.success,
            "errorMessage": self.error_message,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Logger de auditoria.
    
    Registra e consulta eventos de auditoria.
    """
    
    def __init__(
        self,
        max_events: int = 100000,
        retention_days: int = 90,
    ):
        self._events: List[AuditEvent] = []
        self._max_events = max_events
        self._retention_days = retention_days
        self._event_counter = 0
    
    def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: str = "",
        details: Optional[Dict] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
    ) -> AuditEvent:
        """Registra evento de auditoria."""
        self._event_counter += 1
        
        # Determinar severidade
        if severity is None:
            if not success:
                severity = AuditSeverity.ERROR
            elif action in [AuditAction.SYSTEM_ERROR]:
                severity = AuditSeverity.ERROR
            elif action in [AuditAction.USER_ROLE_CHANGE, AuditAction.SETTINGS_UPDATE]:
                severity = AuditSeverity.WARNING
            else:
                severity = AuditSeverity.INFO
        
        event = AuditEvent(
            id=f"audit_{self._event_counter}",
            action=action,
            severity=severity,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            details=details or {},
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
        )
        
        self._events.append(event)
        self._cleanup()
        
        # Log também para o logger padrão
        log_level = logging.INFO
        if severity == AuditSeverity.WARNING:
            log_level = logging.WARNING
        elif severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            log_level = logging.ERROR
        
        logger.log(
            log_level,
            f"[AUDIT] {action.value} | user={user_id} | resource={resource_type}/{resource_id} | success={success}"
        )
        
        return event
    
    def _cleanup(self):
        """Remove eventos antigos."""
        # Por quantidade
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
        
        # Por idade
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        self._events = [e for e in self._events if e.timestamp > cutoff]
    
    def query(
        self,
        action: Optional[AuditAction] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Consulta eventos de auditoria."""
        events = self._events.copy()
        
        if action:
            events = [e for e in events if e.action == action]
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        if resource_type:
            events = [e for e in events if e.resource_type == resource_type]
        if resource_id:
            events = [e for e in events if e.resource_id == resource_id]
        if severity:
            events = [e for e in events if e.severity == severity]
        if success is not None:
            events = [e for e in events if e.success == success]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Ordenar por timestamp desc
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[offset:offset + limit]
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Obtém atividade de um usuário."""
        cutoff = datetime.now() - timedelta(days=days)
        
        events = [
            e for e in self._events
            if e.user_id == user_id and e.timestamp > cutoff
        ]
        
        # Agrupar por ação
        by_action = {}
        for e in events:
            action = e.action.value
            by_action[action] = by_action.get(action, 0) + 1
        
        # Agrupar por dia
        by_day = {}
        for e in events:
            day = e.timestamp.strftime("%Y-%m-%d")
            by_day[day] = by_day.get(day, 0) + 1
        
        return {
            "totalEvents": len(events),
            "byAction": by_action,
            "byDay": by_day,
            "lastActivity": max(e.timestamp for e in events).isoformat() if events else None,
            "errors": len([e for e in events if not e.success]),
        }
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Obtém histórico de um recurso."""
        return self.query(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
    
    def export_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """Exporta eventos."""
        events = self.query(
            start_time=start_time,
            end_time=end_time,
            limit=999999,
        )
        
        if format == "json":
            return json.dumps([e.to_dict() for e in events], default=str, indent=2)
        elif format == "csv":
            lines = ["timestamp,action,user_id,resource_type,resource_id,success"]
            for e in events:
                lines.append(
                    f"{e.timestamp.isoformat()},{e.action.value},{e.user_id},{e.resource_type},{e.resource_id},{e.success}"
                )
            return "\n".join(lines)
        
        return ""
    
    def get_stats(
        self,
        tenant_id: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Estatísticas de auditoria."""
        cutoff = datetime.now() - timedelta(days=days)
        
        events = [e for e in self._events if e.timestamp > cutoff]
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        
        return {
            "totalEvents": len(events),
            "uniqueUsers": len(set(e.user_id for e in events if e.user_id)),
            "errors": len([e for e in events if not e.success]),
            "bySeverity": {
                sev.value: len([e for e in events if e.severity == sev])
                for sev in AuditSeverity
            },
            "topActions": sorted(
                [
                    {"action": action.value, "count": len([e for e in events if e.action == action])}
                    for action in AuditAction
                ],
                key=lambda x: x["count"],
                reverse=True
            )[:10],
        }


# Singleton
_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Obtém logger de auditoria."""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger

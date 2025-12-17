"""
Sistema de Audit Logging.

Registra todas as ações importantes do sistema para
compliance, debugging e análise de uso.
"""

from .logger import AuditLogger, AuditEvent, EventType, get_audit_logger
from .models import AuditLog

__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditLog",
    "EventType",
    "get_audit_logger",
]

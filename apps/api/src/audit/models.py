"""
Modelos para persistência de audit logs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditLog(Base):
    """Registro de audit log no banco de dados."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user = Column(String(100), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    resource = Column(String(50), nullable=True, index=True)
    action = Column(String(50), nullable=True)
    domain = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(50), nullable=True, index=True)
    status = Column(String(20), nullable=True)  # success, failure, denied
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "user": self.user,
            "user_role": self.user_role,
            "resource": self.resource,
            "action": self.action,
            "domain": self.domain,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "request_id": self.request_id,
            "status": self.status,
            "details": self.details,
            "error_message": self.error_message,
        }

"""
Audit Logger - Sistema de logging de auditoria.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from .models import Base, AuditLog


class EventType(str, Enum):
    """Tipos de eventos de auditoria."""
    # Autenticação
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"

    # Agentes
    AGENT_CREATE = "agent_create"
    AGENT_DELETE = "agent_delete"
    AGENT_RUN = "agent_run"

    # Times
    TEAM_CREATE = "team_create"
    TEAM_DELETE = "team_delete"
    TEAM_RUN = "team_run"

    # Workflows
    WORKFLOW_CREATE = "workflow_create"
    WORKFLOW_DELETE = "workflow_delete"
    WORKFLOW_RUN = "workflow_run"

    # RAG
    RAG_INGEST = "rag_ingest"
    RAG_QUERY = "rag_query"
    RAG_DELETE = "rag_delete"

    # Storage
    STORAGE_UPLOAD = "storage_upload"
    STORAGE_DELETE = "storage_delete"

    # HITL
    HITL_START = "hitl_start"
    HITL_COMPLETE = "hitl_complete"
    HITL_CANCEL = "hitl_cancel"

    # Admin
    CONFIG_VIEW = "config_view"
    CONFIG_CHANGE = "config_change"

    # Segurança
    ACCESS_DENIED = "access_denied"
    RATE_LIMITED = "rate_limited"

    # Genérico
    API_REQUEST = "api_request"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Evento de auditoria."""
    event_type: EventType
    user: Optional[str] = None
    user_role: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    domain: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    status: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        d = asdict(self)
        d["event_type"] = self.event_type.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


class AuditLogger:
    """
    Logger de auditoria com suporte a múltiplos backends.

    Backends:
    - SQLite (padrão)
    - Arquivo JSON
    - Console (debug)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        log_file: Optional[Path] = None,
        console: bool = False,
    ):
        """
        Inicializa o audit logger.

        Args:
            db_path: Caminho para banco SQLite
            log_file: Caminho para arquivo JSON
            console: Se deve logar no console
        """
        self.console = console
        self.log_file = log_file
        self._engine = None
        self._session_factory = None

        # Configurar logging do Python
        self._logger = logging.getLogger("audit")
        if console:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - AUDIT - %(message)s")
            )
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

        # Configurar banco de dados
        if db_path:
            self._setup_db(db_path)
        else:
            # Usar path padrão
            settings = get_settings()
            default_path = settings.BASE_DIR / "data" / "databases" / "audit.db"
            default_path.parent.mkdir(parents=True, exist_ok=True)
            self._setup_db(str(default_path))

    def _setup_db(self, db_path: str) -> None:
        """Configura conexão com banco de dados."""
        self._engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def log(self, event: AuditEvent) -> None:
        """
        Registra um evento de auditoria.

        Args:
            event: Evento a registrar
        """
        # Console
        if self.console:
            self._logger.info(json.dumps(event.to_dict(), default=str))

        # Arquivo JSON
        if self.log_file:
            self._log_to_file(event)

        # Banco de dados
        if self._session_factory:
            self._log_to_db(event)

    def _log_to_file(self, event: AuditEvent) -> None:
        """Registra em arquivo JSON (append)."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), default=str) + "\n")
        except Exception:
            pass

    def _log_to_db(self, event: AuditEvent) -> None:
        """Registra no banco de dados."""
        try:
            with self._session_factory() as session:
                log_entry = AuditLog(
                    timestamp=event.timestamp,
                    event_type=event.event_type.value,
                    user=event.user,
                    user_role=event.user_role,
                    resource=event.resource,
                    action=event.action,
                    domain=event.domain,
                    resource_id=event.resource_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    request_id=event.request_id,
                    status=event.status,
                    details=event.details,
                    error_message=event.error_message,
                )
                session.add(log_entry)
                session.commit()
        except Exception:
            pass

    def query(
        self,
        event_type: Optional[EventType] = None,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Consulta logs de auditoria.

        Args:
            event_type: Filtrar por tipo de evento
            user: Filtrar por usuário
            resource: Filtrar por recurso
            domain: Filtrar por domínio
            status: Filtrar por status
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            Lista de logs
        """
        if not self._session_factory:
            return []

        try:
            with self._session_factory() as session:
                query = session.query(AuditLog)

                if event_type:
                    query = query.filter(AuditLog.event_type == event_type.value)
                if user:
                    query = query.filter(AuditLog.user == user)
                if resource:
                    query = query.filter(AuditLog.resource == resource)
                if domain:
                    query = query.filter(AuditLog.domain == domain)
                if status:
                    query = query.filter(AuditLog.status == status)
                if start_date:
                    query = query.filter(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditLog.timestamp <= end_date)

                query = query.order_by(desc(AuditLog.timestamp))
                query = query.offset(offset).limit(limit)

                return [log.to_dict() for log in query.all()]
        except Exception:
            return []

    def get_user_activity(self, user: str, limit: int = 50) -> List[Dict]:
        """Obtém atividade recente de um usuário."""
        return self.query(user=user, limit=limit)

    def get_security_events(self, limit: int = 100) -> List[Dict]:
        """Obtém eventos de segurança recentes."""
        events = []
        for event_type in [EventType.ACCESS_DENIED, EventType.RATE_LIMITED, EventType.LOGIN_FAILED]:
            events.extend(self.query(event_type=event_type, limit=limit // 3))
        return sorted(events, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de auditoria."""
        if not self._session_factory:
            return {}

        try:
            from sqlalchemy import func

            with self._session_factory() as session:
                total = session.query(func.count(AuditLog.id)).scalar()

                by_type = dict(
                    session.query(AuditLog.event_type, func.count(AuditLog.id))
                    .group_by(AuditLog.event_type)
                    .all()
                )

                by_status = dict(
                    session.query(AuditLog.status, func.count(AuditLog.id))
                    .group_by(AuditLog.status)
                    .all()
                )

                by_user = dict(
                    session.query(AuditLog.user, func.count(AuditLog.id))
                    .filter(AuditLog.user.isnot(None))
                    .group_by(AuditLog.user)
                    .order_by(desc(func.count(AuditLog.id)))
                    .limit(10)
                    .all()
                )

                return {
                    "total": total,
                    "by_type": by_type,
                    "by_status": by_status,
                    "top_users": by_user,
                }
        except Exception:
            return {}


# Instância global
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Retorna a instância global do audit logger."""
    global _audit_logger
    if _audit_logger is None:
        settings = get_settings()
        _audit_logger = AuditLogger(
            console=settings.DEBUG,
        )
    return _audit_logger

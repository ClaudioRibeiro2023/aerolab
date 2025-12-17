"""
Sistema de logging estruturado para AgentOS.

Fornece:
- Logs em formato JSON para fácil parsing
- Níveis de log configuráveis
- Contexto automático (timestamp, request_id, etc.)
- Integração com sistemas de log centralizados
"""

import logging
import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum
from functools import wraps
import threading
import uuid


class LogLevel(Enum):
    """Níveis de log."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Context local para request_id
_context = threading.local()


def set_request_id(request_id: Optional[str] = None):
    """Define o request_id para o contexto atual."""
    _context.request_id = request_id or str(uuid.uuid4())[:8]


def get_request_id() -> Optional[str]:
    """Obtém o request_id do contexto atual."""
    return getattr(_context, "request_id", None)


class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Adicionar request_id se disponível
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # Adicionar extras
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Adicionar exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    traceback.format_exception(*record.exc_info) if all(record.exc_info) else None
                ),
            }

        # Adicionar localização do código
        if record.pathname:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data, default=str, ensure_ascii=False)


class StructuredLogger:
    """Logger estruturado com suporte a contexto."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Retorna um novo logger com contexto adicional."""
        new_logger = StructuredLogger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs):
        """Log interno com dados extras."""
        extra_data = {**self._context, **kwargs}
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None,
        )
        record.extra_data = extra_data if extra_data else None
        self.logger.handle(record)

    def debug(self, message: str, **kwargs):
        """Log de debug."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log de info."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log de warning."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log de erro."""
        if exc_info:
            kwargs["exception"] = traceback.format_exc()
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log crítico."""
        if exc_info:
            kwargs["exception"] = traceback.format_exc()
        self._log(logging.CRITICAL, message, **kwargs)


# Cache de loggers
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str = "agentos") -> StructuredLogger:
    """Obtém ou cria um logger estruturado."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def setup_logging(level: str = "INFO", json_format: bool = True, stream: Any = None):
    """
    Configura o sistema de logging.

    Args:
        level: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Se True, usa formato JSON
        stream: Stream de saída (default: sys.stdout)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remover handlers existentes
    root_logger.handlers = []

    # Criar handler
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )

    root_logger.addHandler(handler)

    # Silenciar loggers muito verbosos
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def log_event(event_type: str, message: str, level: LogLevel = LogLevel.INFO, **data):
    """
    Log de evento estruturado.

    Args:
        event_type: Tipo do evento (ex: "agent.execution", "api.request")
        message: Mensagem descritiva
        level: Nível do log
        **data: Dados adicionais do evento
    """
    logger = get_logger("events")
    log_data = {"event_type": event_type, **data}

    log_method = getattr(logger, level.value.lower())
    log_method(message, **log_data)


def log_execution(func):
    """Decorator para logar execução de funções."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start = datetime.now(timezone.utc)

        logger.debug(f"Starting {func.__name__}", args=str(args)[:100], kwargs=str(kwargs)[:100])

        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info(f"Completed {func.__name__}", duration=duration)
            return result
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.error(f"Failed {func.__name__}", duration=duration, error=str(e), exc_info=True)
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start = datetime.now(timezone.utc)

        logger.debug(f"Starting {func.__name__}")

        try:
            result = func(*args, **kwargs)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info(f"Completed {func.__name__}", duration=duration)
            return result
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.error(f"Failed {func.__name__}", duration=duration, error=str(e), exc_info=True)
            raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

"""
Módulo de observabilidade - métricas, logs e tracing.
"""

from .metrics import (
    registry,
    get_metrics_text,
    track_request,
    track_agent_execution,
    track_error,
    set_active_agents,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    AGENT_EXECUTIONS,
    ACTIVE_AGENTS,
    TOKENS_USED,
    CACHE_HITS,
    CACHE_MISSES,
    ERRORS,
)

from .logging import (
    get_logger,
    setup_logging,
    log_event,
    LogLevel,
)

__all__ = [
    # Metrics
    "registry",
    "get_metrics_text",
    "track_request",
    "track_agent_execution",
    "track_error",
    "set_active_agents",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "AGENT_EXECUTIONS",
    "ACTIVE_AGENTS",
    "TOKENS_USED",
    "CACHE_HITS",
    "CACHE_MISSES",
    "ERRORS",
    # Logging
    "get_logger",
    "setup_logging",
    "log_event",
    "LogLevel",
]

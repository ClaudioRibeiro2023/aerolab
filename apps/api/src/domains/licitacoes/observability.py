"""Observabilidade para o Núcleo Licitações.

Métricas, logs estruturados e monitoramento.
"""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Ponto de métrica."""

    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)


class LicitacoesMetrics:
    """Coletor de métricas do núcleo de licitações."""

    def __init__(self):
        self._metrics: list[MetricPoint] = []
        self._counters: dict[str, int] = {}

    def increment(self, name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
        """Incrementa um contador."""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self._counters[key] = self._counters.get(key, 0) + value

        self._metrics.append(MetricPoint(
            name=name,
            value=float(self._counters[key]),
            timestamp=datetime.now(timezone.utc),
            labels=labels or {},
        ))

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Registra um gauge (valor instantâneo)."""
        self._metrics.append(MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {},
        ))

    def timing(self, name: str, duration_seconds: float, labels: dict[str, str] | None = None) -> None:
        """Registra uma medição de tempo."""
        self._metrics.append(MetricPoint(
            name=f"{name}_seconds",
            value=duration_seconds,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {},
        ))

    def get_metrics(self, name: str | None = None, limit: int = 100) -> list[MetricPoint]:
        """Obtém métricas recentes."""
        metrics = self._metrics
        if name:
            metrics = [m for m in metrics if m.name == name]
        return metrics[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Obtém resumo das métricas."""
        return {
            "total_points": len(self._metrics),
            "counters": dict(self._counters),
            "recent": [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "labels": m.labels,
                }
                for m in self._metrics[-20:]
            ],
        }


class StructuredLogger:
    """Logger estruturado para o núcleo de licitações."""

    def __init__(self, component: str):
        self.component = component
        self._logger = logging.getLogger(f"licitacoes.{component}")

    def _format_log(
        self,
        level: str,
        message: str,
        run_id: str | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Formata log estruturado."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "component": self.component,
            "message": message,
            "run_id": run_id,
            **extra,
        }

    def info(self, message: str, run_id: str | None = None, **extra) -> None:
        log_data = self._format_log("INFO", message, run_id, **extra)
        self._logger.info(json.dumps(log_data))

    def warning(self, message: str, run_id: str | None = None, **extra) -> None:
        log_data = self._format_log("WARNING", message, run_id, **extra)
        self._logger.warning(json.dumps(log_data))

    def error(self, message: str, run_id: str | None = None, **extra) -> None:
        log_data = self._format_log("ERROR", message, run_id, **extra)
        self._logger.error(json.dumps(log_data))

    def debug(self, message: str, run_id: str | None = None, **extra) -> None:
        log_data = self._format_log("DEBUG", message, run_id, **extra)
        self._logger.debug(json.dumps(log_data))


class FlowObserver:
    """Observer para monitorar execução de flows."""

    def __init__(self, metrics: LicitacoesMetrics, logger: StructuredLogger):
        self.metrics = metrics
        self.logger = logger

    def on_flow_start(self, flow_name: str, run_id: str, config: dict[str, Any]) -> None:
        """Callback quando um flow inicia."""
        self.metrics.increment("flow_started", labels={"flow": flow_name})
        self.logger.info(
            f"Flow started: {flow_name}",
            run_id=run_id,
            flow=flow_name,
            config=config,
        )

    def on_flow_end(
        self,
        flow_name: str,
        run_id: str,
        status: str,
        duration_seconds: float,
        items_processed: int = 0,
        items_p0: int = 0,
        items_p1: int = 0,
        errors: list[str] | None = None,
    ) -> None:
        """Callback quando um flow termina."""
        self.metrics.increment("flow_completed", labels={"flow": flow_name, "status": status})
        self.metrics.timing(f"flow_{flow_name}_duration", duration_seconds)
        self.metrics.gauge("flow_items_processed", float(items_processed), labels={"flow": flow_name})
        self.metrics.gauge("flow_items_p0", float(items_p0), labels={"flow": flow_name})
        self.metrics.gauge("flow_items_p1", float(items_p1), labels={"flow": flow_name})

        if errors:
            self.metrics.increment("flow_errors", len(errors), labels={"flow": flow_name})

        self.logger.info(
            f"Flow completed: {flow_name}",
            run_id=run_id,
            flow=flow_name,
            status=status,
            duration_seconds=duration_seconds,
            items_processed=items_processed,
            items_p0=items_p0,
            items_p1=items_p1,
            errors=errors,
        )

    def on_agent_call(
        self,
        agent_name: str,
        run_id: str,
        action: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Callback quando um agente é chamado."""
        self.metrics.increment("agent_calls", labels={"agent": agent_name, "action": action})
        self.metrics.timing(f"agent_{agent_name}_{action}", duration_seconds)

        if not success:
            self.metrics.increment("agent_errors", labels={"agent": agent_name, "action": action})

    def on_source_fetch(
        self,
        source: str,
        run_id: str,
        items_count: int,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Callback quando uma fonte é consultada."""
        self.metrics.increment("source_fetches", labels={"source": source})
        self.metrics.timing(f"source_{source}_fetch", duration_seconds)
        self.metrics.gauge(f"source_{source}_items", float(items_count))

        if not success:
            self.metrics.increment("source_errors", labels={"source": source})


# Singletons
_metrics: LicitacoesMetrics | None = None
_observer: FlowObserver | None = None


def get_metrics() -> LicitacoesMetrics:
    """Obtém instância singleton de métricas."""
    global _metrics
    if _metrics is None:
        _metrics = LicitacoesMetrics()
    return _metrics


def get_observer() -> FlowObserver:
    """Obtém instância singleton do observer."""
    global _observer
    if _observer is None:
        _observer = FlowObserver(
            metrics=get_metrics(),
            logger=StructuredLogger("flow"),
        )
    return _observer


def get_logger(component: str) -> StructuredLogger:
    """Cria logger estruturado para um componente."""
    return StructuredLogger(component)

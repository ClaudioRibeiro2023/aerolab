"""
Alert Engine - Motor de execução de alertas.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
import asyncio
import threading
import logging

from .rules import AlertRule, AlertState, AlertSeverity

logger = logging.getLogger(__name__)


@dataclass
class AlertEvent:
    """Evento de alerta."""
    rule_id: str
    rule_name: str
    state: AlertState
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    values: Dict[str, float] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "ruleId": self.rule_id,
            "ruleName": self.rule_name,
            "state": self.state.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "values": self.values,
            "labels": self.labels,
        }


class AlertEngine:
    """
    Motor de alertas.
    
    Executa avaliação contínua de regras de alerta.
    """
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._events: List[AlertEvent] = []
        self._handlers: List[Callable[[AlertEvent], None]] = []
        self._running = False
        self._lock = threading.RLock()
        self._task: Optional[asyncio.Task] = None
    
    def add_rule(self, rule: AlertRule) -> None:
        """Adiciona regra de alerta."""
        with self._lock:
            self._rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove regra de alerta."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Obtém regra por ID."""
        return self._rules.get(rule_id)
    
    def list_rules(self) -> List[AlertRule]:
        """Lista todas as regras."""
        return list(self._rules.values())
    
    def add_handler(self, handler: Callable[[AlertEvent], None]) -> None:
        """Adiciona handler de eventos."""
        self._handlers.append(handler)
    
    async def evaluate_rule(
        self,
        rule: AlertRule,
        get_metrics: Callable[[List[str]], Dict[str, float]]
    ) -> Optional[AlertEvent]:
        """
        Avalia uma regra de alerta.
        
        Args:
            rule: Regra a avaliar
            get_metrics: Função para obter valores de métricas
            
        Returns:
            AlertEvent se houve mudança de estado
        """
        if not rule.enabled:
            return None
        
        if rule.is_silenced():
            return None
        
        # Obter métricas necessárias
        metric_names = [c.metric for c in rule.conditions]
        values = get_metrics(metric_names)
        
        # Avaliar condições
        is_firing = rule.evaluate(values)
        
        # Atualizar estado
        state_changed = rule.update_state(is_firing)
        
        if state_changed:
            event = AlertEvent(
                rule_id=rule.id,
                rule_name=rule.name,
                state=rule.state,
                severity=rule.severity,
                message=rule.summary,
                values=values,
                labels=rule.labels
            )
            
            self._events.append(event)
            
            # Notificar handlers
            for handler in self._handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Alert handler error: {e}")
            
            return event
        
        return None
    
    async def evaluate_all(
        self,
        get_metrics: Callable[[List[str]], Dict[str, float]]
    ) -> List[AlertEvent]:
        """Avalia todas as regras."""
        events = []
        
        for rule in self._rules.values():
            try:
                event = await self.evaluate_rule(rule, get_metrics)
                if event:
                    events.append(event)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
        
        return events
    
    async def start(
        self,
        get_metrics: Callable[[List[str]], Dict[str, float]],
        interval_seconds: int = 60
    ) -> None:
        """Inicia loop de avaliação."""
        self._running = True
        logger.info("Alert engine started")
        
        while self._running:
            try:
                await self.evaluate_all(get_metrics)
            except Exception as e:
                logger.error(f"Evaluation loop error: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self) -> None:
        """Para o engine."""
        self._running = False
        logger.info("Alert engine stopped")
    
    def get_events(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
        state: Optional[AlertState] = None
    ) -> List[AlertEvent]:
        """Lista eventos de alerta."""
        events = self._events
        
        if severity:
            events = [e for e in events if e.severity == severity]
        if state:
            events = [e for e in events if e.state == state]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_firing_alerts(self) -> List[AlertRule]:
        """Lista alertas ativos."""
        return [r for r in self._rules.values() if r.state == AlertState.FIRING]
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo de alertas."""
        rules = list(self._rules.values())
        
        by_state = {
            "ok": len([r for r in rules if r.state == AlertState.OK]),
            "pending": len([r for r in rules if r.state == AlertState.PENDING]),
            "firing": len([r for r in rules if r.state == AlertState.FIRING]),
            "resolved": len([r for r in rules if r.state == AlertState.RESOLVED]),
        }
        
        by_severity = {
            "info": len([r for r in rules if r.severity == AlertSeverity.INFO]),
            "warning": len([r for r in rules if r.severity == AlertSeverity.WARNING]),
            "error": len([r for r in rules if r.severity == AlertSeverity.ERROR]),
            "critical": len([r for r in rules if r.severity == AlertSeverity.CRITICAL]),
        }
        
        return {
            "totalRules": len(rules),
            "enabled": len([r for r in rules if r.enabled]),
            "byState": by_state,
            "bySeverity": by_severity,
            "firingAlerts": [r.to_dict() for r in self.get_firing_alerts()],
            "recentEvents": [e.to_dict() for e in self.get_events(10)],
        }


# Singleton
_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """Obtém alert engine."""
    global _engine
    if _engine is None:
        _engine = AlertEngine()
    return _engine

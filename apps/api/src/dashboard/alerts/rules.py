"""
Alert Rules - Regras de alerta.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class AlertSeverity(str, Enum):
    """Severidade do alerta."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConditionOperator(str, Enum):
    """Operadores de condição."""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    
    # Agregações
    AVG_ABOVE = "avg_above"
    AVG_BELOW = "avg_below"
    SUM_ABOVE = "sum_above"
    RATE_ABOVE = "rate_above"
    
    # Anomalias
    ANOMALY = "anomaly"


class AlertState(str, Enum):
    """Estado do alerta."""
    OK = "ok"
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class AlertCondition:
    """Condição de alerta."""
    metric: str
    operator: ConditionOperator
    threshold: float = 0.0
    
    # Para condições com duração
    duration: Optional[timedelta] = None
    
    # Labels filter
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Para condições de anomalia
    sensitivity: float = 0.5  # 0.0 = low, 1.0 = high
    
    def evaluate(self, value: float) -> bool:
        """Avalia a condição."""
        if self.operator == ConditionOperator.GREATER_THAN:
            return value > self.threshold
        elif self.operator == ConditionOperator.LESS_THAN:
            return value < self.threshold
        elif self.operator == ConditionOperator.EQUAL:
            return value == self.threshold
        elif self.operator == ConditionOperator.NOT_EQUAL:
            return value != self.threshold
        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return value >= self.threshold
        elif self.operator == ConditionOperator.LESS_EQUAL:
            return value <= self.threshold
        elif self.operator in (ConditionOperator.AVG_ABOVE, ConditionOperator.SUM_ABOVE, ConditionOperator.RATE_ABOVE):
            return value > self.threshold
        elif self.operator == ConditionOperator.AVG_BELOW:
            return value < self.threshold
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric,
            "operator": self.operator.value,
            "threshold": self.threshold,
            "duration": str(self.duration) if self.duration else None,
            "labels": self.labels,
            "sensitivity": self.sensitivity,
        }


@dataclass
class AlertRule:
    """
    Regra de alerta.
    
    Define quando um alerta deve disparar.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Condições
    conditions: List[AlertCondition] = field(default_factory=list)
    condition_logic: str = "and"  # and, or
    
    # Severidade
    severity: AlertSeverity = AlertSeverity.WARNING
    
    # Channels
    channel_ids: List[str] = field(default_factory=list)
    
    # Schedule
    enabled: bool = True
    evaluation_interval: timedelta = field(default_factory=lambda: timedelta(minutes=1))
    
    # Silencing
    silenced_until: Optional[datetime] = None
    
    # Annotations
    summary: str = ""  # Template para resumo
    runbook_url: str = ""
    
    # Labels
    labels: Dict[str, str] = field(default_factory=dict)
    
    # State
    state: AlertState = AlertState.OK
    last_evaluation: Optional[datetime] = None
    last_state_change: Optional[datetime] = None
    firing_since: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def is_silenced(self) -> bool:
        """Verifica se está silenciado."""
        if self.silenced_until is None:
            return False
        return datetime.now() < self.silenced_until
    
    def silence(self, duration: timedelta, reason: str = "") -> None:
        """Silencia o alerta."""
        self.silenced_until = datetime.now() + duration
    
    def unsilence(self) -> None:
        """Remove silenciamento."""
        self.silenced_until = None
    
    def evaluate(self, values: Dict[str, float]) -> bool:
        """
        Avalia todas as condições.
        
        Args:
            values: Dict de métrica -> valor
            
        Returns:
            True se alerta deve disparar
        """
        if not self.conditions:
            return False
        
        results = []
        
        for condition in self.conditions:
            value = values.get(condition.metric)
            if value is None:
                results.append(False)
            else:
                results.append(condition.evaluate(value))
        
        if self.condition_logic == "and":
            return all(results)
        else:  # or
            return any(results)
    
    def update_state(self, is_firing: bool) -> bool:
        """
        Atualiza estado do alerta.
        
        Returns:
            True se houve mudança de estado
        """
        now = datetime.now()
        self.last_evaluation = now
        
        old_state = self.state
        
        if is_firing:
            if self.state == AlertState.OK:
                self.state = AlertState.PENDING
            elif self.state == AlertState.PENDING:
                self.state = AlertState.FIRING
                self.firing_since = now
            # Já firing: permanece firing
        else:
            if self.state in (AlertState.FIRING, AlertState.PENDING):
                self.state = AlertState.RESOLVED
                self.firing_since = None
            elif self.state == AlertState.RESOLVED:
                self.state = AlertState.OK
        
        if self.state != old_state:
            self.last_state_change = now
            return True
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": [c.to_dict() for c in self.conditions],
            "conditionLogic": self.condition_logic,
            "severity": self.severity.value,
            "channelIds": self.channel_ids,
            "enabled": self.enabled,
            "state": self.state.value,
            "silencedUntil": self.silenced_until.isoformat() if self.silenced_until else None,
            "summary": self.summary,
            "runbookUrl": self.runbook_url,
            "labels": self.labels,
            "lastEvaluation": self.last_evaluation.isoformat() if self.last_evaluation else None,
            "firingSince": self.firing_since.isoformat() if self.firing_since else None,
            "createdAt": self.created_at.isoformat(),
        }
    
    @classmethod
    def high_error_rate(cls, threshold: float = 0.05, **kwargs) -> "AlertRule":
        """Cria regra para alta taxa de erro."""
        return cls(
            name="High Error Rate",
            description="Error rate exceeds threshold",
            conditions=[
                AlertCondition(
                    metric="error_rate",
                    operator=ConditionOperator.GREATER_THAN,
                    threshold=threshold
                )
            ],
            severity=AlertSeverity.ERROR,
            summary=f"Error rate is above {threshold * 100}%",
            **kwargs
        )
    
    @classmethod
    def high_latency(cls, threshold_ms: float = 1000, **kwargs) -> "AlertRule":
        """Cria regra para alta latência."""
        return cls(
            name="High Latency",
            description="Latency exceeds threshold",
            conditions=[
                AlertCondition(
                    metric="latency_p95",
                    operator=ConditionOperator.GREATER_THAN,
                    threshold=threshold_ms
                )
            ],
            severity=AlertSeverity.WARNING,
            summary=f"P95 latency is above {threshold_ms}ms",
            **kwargs
        )

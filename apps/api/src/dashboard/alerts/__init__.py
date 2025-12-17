"""
Alerts - Sistema de alertas para dashboards.

Features:
- Alert rules engine
- Múltiplas condições
- Notification channels
- Incident management
"""

from .rules import AlertRule, AlertCondition, AlertSeverity
from .engine import AlertEngine
from .channels import NotificationChannel, ChannelType
from .incidents import Incident, IncidentStatus

__all__ = [
    "AlertRule",
    "AlertCondition",
    "AlertSeverity",
    "AlertEngine",
    "NotificationChannel",
    "ChannelType",
    "Incident",
    "IncidentStatus",
]

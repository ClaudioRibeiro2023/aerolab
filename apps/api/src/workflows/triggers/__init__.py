"""
Sistema de Triggers para Workflows.

Tipos de triggers:
- WebhookTrigger: Dispara via webhook HTTP
- ScheduleTrigger: Dispara via cron schedule
- EventTrigger: Dispara via eventos do sistema
- ManualTrigger: Disparo manual
"""

from .base import BaseTrigger, TriggerConfig, TriggerResult
from .webhook import WebhookTrigger
from .schedule import ScheduleTrigger, CronExpression
from .event import EventTrigger, EventBus

__all__ = [
    "BaseTrigger",
    "TriggerConfig",
    "TriggerResult",
    "WebhookTrigger",
    "ScheduleTrigger",
    "CronExpression",
    "EventTrigger",
    "EventBus",
]

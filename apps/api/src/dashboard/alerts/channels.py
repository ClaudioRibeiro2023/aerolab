"""
Notification Channels - Canais de notificação para alertas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Tipos de canal."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"


@dataclass
class ChannelConfig:
    """Configuração base de canal."""
    pass


@dataclass
class EmailConfig(ChannelConfig):
    """Configuração de email."""
    recipients: List[str] = field(default_factory=list)
    subject_template: str = "[{{ severity }}] {{ name }}"
    body_template: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""


@dataclass
class SlackConfig(ChannelConfig):
    """Configuração de Slack."""
    webhook_url: str = ""
    channel: str = ""
    username: str = "Alert Bot"
    icon_emoji: str = ":warning:"
    mention_users: List[str] = field(default_factory=list)


@dataclass
class TeamsConfig(ChannelConfig):
    """Configuração de Microsoft Teams."""
    webhook_url: str = ""


@dataclass
class PagerDutyConfig(ChannelConfig):
    """Configuração de PagerDuty."""
    integration_key: str = ""
    severity_mapping: Dict[str, str] = field(default_factory=lambda: {
        "critical": "critical",
        "error": "error",
        "warning": "warning",
        "info": "info"
    })


@dataclass
class WebhookConfig(ChannelConfig):
    """Configuração de webhook genérico."""
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    body_template: str = ""


@dataclass
class NotificationChannel:
    """
    Canal de notificação.
    
    Responsável por enviar alertas para um destino.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: ChannelType = ChannelType.WEBHOOK
    
    # Config
    config: ChannelConfig = field(default_factory=ChannelConfig)
    
    # State
    enabled: bool = True
    last_sent: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # Rate limiting
    rate_limit_per_hour: int = 60
    sent_count_current_hour: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    async def send(self, event: Dict) -> bool:
        """
        Envia notificação.
        
        Args:
            event: Dados do evento de alerta
            
        Returns:
            True se enviado com sucesso
        """
        if not self.enabled:
            return False
        
        # Rate limiting
        if self.sent_count_current_hour >= self.rate_limit_per_hour:
            logger.warning(f"Channel {self.name} rate limited")
            return False
        
        try:
            if self.type == ChannelType.SLACK:
                return await self._send_slack(event)
            elif self.type == ChannelType.EMAIL:
                return await self._send_email(event)
            elif self.type == ChannelType.TEAMS:
                return await self._send_teams(event)
            elif self.type == ChannelType.WEBHOOK:
                return await self._send_webhook(event)
            elif self.type == ChannelType.PAGERDUTY:
                return await self._send_pagerduty(event)
            else:
                logger.warning(f"Unsupported channel type: {self.type}")
                return False
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Channel {self.name} send error: {e}")
            return False
    
    async def _send_slack(self, event: Dict) -> bool:
        """Envia para Slack."""
        config = self.config
        if not isinstance(config, SlackConfig):
            return False
        
        # Em produção: usar httpx para POST
        # Por agora: placeholder
        
        severity = event.get("severity", "warning")
        color = {
            "critical": "#dc2626",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6"
        }.get(severity, "#6b7280")
        
        payload = {
            "username": config.username,
            "icon_emoji": config.icon_emoji,
            "attachments": [{
                "color": color,
                "title": event.get("ruleName", "Alert"),
                "text": event.get("message", ""),
                "fields": [
                    {"title": "State", "value": event.get("state"), "short": True},
                    {"title": "Severity", "value": severity, "short": True}
                ],
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        logger.info(f"Slack notification: {event.get('ruleName')}")
        self.last_sent = datetime.now()
        self.sent_count_current_hour += 1
        return True
    
    async def _send_email(self, event: Dict) -> bool:
        """Envia email."""
        config = self.config
        if not isinstance(config, EmailConfig):
            return False
        
        # Em produção: usar smtplib ou serviço de email
        logger.info(f"Email notification to {config.recipients}: {event.get('ruleName')}")
        self.last_sent = datetime.now()
        self.sent_count_current_hour += 1
        return True
    
    async def _send_teams(self, event: Dict) -> bool:
        """Envia para Microsoft Teams."""
        config = self.config
        if not isinstance(config, TeamsConfig):
            return False
        
        # Em produção: usar httpx para POST ao webhook
        logger.info(f"Teams notification: {event.get('ruleName')}")
        self.last_sent = datetime.now()
        self.sent_count_current_hour += 1
        return True
    
    async def _send_webhook(self, event: Dict) -> bool:
        """Envia para webhook genérico."""
        config = self.config
        if not isinstance(config, WebhookConfig):
            return False
        
        # Em produção: usar httpx
        logger.info(f"Webhook notification to {config.url}: {event.get('ruleName')}")
        self.last_sent = datetime.now()
        self.sent_count_current_hour += 1
        return True
    
    async def _send_pagerduty(self, event: Dict) -> bool:
        """Envia para PagerDuty."""
        config = self.config
        if not isinstance(config, PagerDutyConfig):
            return False
        
        # Em produção: usar PagerDuty Events API v2
        logger.info(f"PagerDuty notification: {event.get('ruleName')}")
        self.last_sent = datetime.now()
        self.sent_count_current_hour += 1
        return True
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "enabled": self.enabled,
            "lastSent": self.last_sent.isoformat() if self.last_sent else None,
            "lastError": self.last_error,
            "createdAt": self.created_at.isoformat(),
        }


class ChannelManager:
    """Gerenciador de canais."""
    
    def __init__(self):
        self._channels: Dict[str, NotificationChannel] = {}
    
    def add(self, channel: NotificationChannel) -> None:
        """Adiciona canal."""
        self._channels[channel.id] = channel
    
    def get(self, channel_id: str) -> Optional[NotificationChannel]:
        """Obtém canal por ID."""
        return self._channels.get(channel_id)
    
    def list(self) -> List[NotificationChannel]:
        """Lista canais."""
        return list(self._channels.values())
    
    def remove(self, channel_id: str) -> bool:
        """Remove canal."""
        if channel_id in self._channels:
            del self._channels[channel_id]
            return True
        return False
    
    async def notify_all(
        self,
        channel_ids: List[str],
        event: Dict
    ) -> Dict[str, bool]:
        """Envia para múltiplos canais."""
        results = {}
        
        for channel_id in channel_ids:
            channel = self._channels.get(channel_id)
            if channel:
                results[channel_id] = await channel.send(event)
            else:
                results[channel_id] = False
        
        return results


# Singleton
_manager: Optional[ChannelManager] = None


def get_channel_manager() -> ChannelManager:
    """Obtém gerenciador de canais."""
    global _manager
    if _manager is None:
        _manager = ChannelManager()
    return _manager

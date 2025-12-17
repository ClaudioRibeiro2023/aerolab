"""
Sistema de Webhooks para eventos.

Permite enviar notificações para URLs externas quando eventos ocorrem.
"""

import os
import json
import hmac
import hashlib
import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import httpx


class EventType(Enum):
    """Tipos de eventos suportados."""
    # Agentes
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_EXECUTED = "agent.executed"
    AGENT_FAILED = "agent.failed"
    
    # Execuções
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    
    # Usuários
    USER_CREATED = "user.created"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Sistema
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    HEALTH_CHECK = "health.check"
    
    # Workflows
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"


@dataclass
class WebhookConfig:
    """Configuração de um webhook."""
    id: str
    url: str
    events: List[EventType]
    secret: Optional[str] = None
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    failure_count: int = 0
    
    def matches_event(self, event_type: EventType) -> bool:
        """Verifica se webhook deve receber este evento."""
        return self.enabled and event_type in self.events


@dataclass
class WebhookDelivery:
    """Registro de entrega de webhook."""
    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status_code: Optional[int] = None
    response: Optional[str] = None
    success: bool = False
    duration_ms: float = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class WebhookManager:
    """
    Gerenciador de Webhooks.
    
    Features:
    - Registro de webhooks por evento
    - Assinatura HMAC para segurança
    - Retry automático com backoff
    - Log de deliveries
    - Rate limiting
    
    Configuração:
        WEBHOOK_STORAGE_PATH: Diretório para persistência
        WEBHOOK_RETRY_COUNT: Número de retries (default: 3)
        WEBHOOK_TIMEOUT: Timeout em segundos (default: 30)
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        retry_count: int = 3,
        timeout: float = 30.0
    ):
        self.storage_path = Path(storage_path or os.getenv("WEBHOOK_STORAGE_PATH", "./data/webhooks"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.retry_count = int(os.getenv("WEBHOOK_RETRY_COUNT", str(retry_count)))
        self.timeout = float(os.getenv("WEBHOOK_TIMEOUT", str(timeout)))
        
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        
        self._load_webhooks()
    
    def _load_webhooks(self):
        """Carrega webhooks salvos."""
        webhooks_file = self.storage_path / "webhooks.json"
        if webhooks_file.exists():
            data = json.loads(webhooks_file.read_text())
            for wh in data.get("webhooks", []):
                config = WebhookConfig(
                    id=wh["id"],
                    url=wh["url"],
                    events=[EventType(e) for e in wh["events"]],
                    secret=wh.get("secret"),
                    enabled=wh.get("enabled", True),
                    headers=wh.get("headers", {}),
                    created_at=datetime.fromisoformat(wh["created_at"]),
                    last_triggered=datetime.fromisoformat(wh["last_triggered"]) if wh.get("last_triggered") else None,
                    failure_count=wh.get("failure_count", 0)
                )
                self._webhooks[config.id] = config
    
    def _save_webhooks(self):
        """Salva webhooks."""
        data = {
            "webhooks": [
                {
                    "id": wh.id,
                    "url": wh.url,
                    "events": [e.value for e in wh.events],
                    "secret": wh.secret,
                    "enabled": wh.enabled,
                    "headers": wh.headers,
                    "created_at": wh.created_at.isoformat(),
                    "last_triggered": wh.last_triggered.isoformat() if wh.last_triggered else None,
                    "failure_count": wh.failure_count
                }
                for wh in self._webhooks.values()
            ]
        }
        (self.storage_path / "webhooks.json").write_text(json.dumps(data, indent=2))
    
    def register_webhook(
        self,
        url: str,
        events: List[EventType],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookConfig:
        """
        Registra um novo webhook.
        
        Args:
            url: URL para enviar eventos
            events: Lista de eventos a escutar
            secret: Secret para assinatura HMAC
            headers: Headers customizados
        """
        import uuid
        
        webhook = WebhookConfig(
            id=str(uuid.uuid4()),
            url=url,
            events=events,
            secret=secret,
            headers=headers or {}
        )
        
        self._webhooks[webhook.id] = webhook
        self._save_webhooks()
        
        return webhook
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Remove um webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            self._save_webhooks()
            return True
        return False
    
    def list_webhooks(self) -> List[WebhookConfig]:
        """Lista todos os webhooks."""
        return list(self._webhooks.values())
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Obtém webhook por ID."""
        return self._webhooks.get(webhook_id)
    
    def enable_webhook(self, webhook_id: str) -> bool:
        """Habilita um webhook."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].enabled = True
            self._save_webhooks()
            return True
        return False
    
    def disable_webhook(self, webhook_id: str) -> bool:
        """Desabilita um webhook."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].enabled = False
            self._save_webhooks()
            return True
        return False
    
    async def trigger(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[WebhookDelivery]:
        """
        Dispara evento para todos os webhooks inscritos.
        
        Args:
            event_type: Tipo do evento
            payload: Dados do evento
            metadata: Metadados adicionais
        
        Returns:
            Lista de deliveries
        """
        event_data = {
            "event": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "metadata": metadata or {}
        }
        
        # Encontrar webhooks inscritos
        matching = [
            wh for wh in self._webhooks.values()
            if wh.matches_event(event_type)
        ]
        
        # Disparar em paralelo
        tasks = [
            self._deliver(webhook, event_data)
            for webhook in matching
        ]
        
        deliveries = await asyncio.gather(*tasks)
        
        # Chamar handlers locais
        for handler in self._event_handlers.get(event_type, []):
            try:
                result = handler(event_data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass
        
        return deliveries
    
    async def _deliver(
        self,
        webhook: WebhookConfig,
        event_data: Dict[str, Any]
    ) -> WebhookDelivery:
        """Entrega evento para um webhook."""
        import uuid
        import time
        
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            webhook_id=webhook.id,
            event_type=event_data["event"],
            payload=event_data
        )
        
        body = json.dumps(event_data)
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_data["event"],
            "X-Webhook-Timestamp": event_data["timestamp"],
            **webhook.headers
        }
        
        # Adicionar assinatura se secret configurado
        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        start = time.time()
        
        for attempt in range(self.retry_count + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook.url,
                        content=body,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    delivery.status_code = response.status_code
                    delivery.response = response.text[:500]  # Limitar resposta
                    delivery.success = 200 <= response.status_code < 300
                    delivery.duration_ms = (time.time() - start) * 1000
                    
                    if delivery.success:
                        webhook.last_triggered = datetime.utcnow()
                        webhook.failure_count = 0
                        break
                    
            except Exception as e:
                delivery.error = str(e)
                
                if attempt < self.retry_count:
                    # Backoff exponencial
                    await asyncio.sleep(2 ** attempt)
        
        if not delivery.success:
            webhook.failure_count += 1
            
            # Desabilitar após muitas falhas
            if webhook.failure_count >= 10:
                webhook.enabled = False
        
        self._deliveries.append(delivery)
        self._save_webhooks()
        
        return delivery
    
    def on_event(self, event_type: EventType):
        """Decorator para registrar handler local."""
        def decorator(func: Callable):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func
        return decorator
    
    def get_deliveries(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Lista deliveries recentes."""
        deliveries = self._deliveries
        
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        
        return sorted(deliveries, key=lambda d: d.created_at, reverse=True)[:limit]


# Singleton
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """Obtém instância singleton do WebhookManager."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


# Helper functions
async def emit_event(
    event_type: EventType,
    payload: Dict[str, Any],
    **metadata
) -> List[WebhookDelivery]:
    """Emite um evento."""
    manager = get_webhook_manager()
    return await manager.trigger(event_type, payload, metadata)


def emit_event_sync(
    event_type: EventType,
    payload: Dict[str, Any],
    **metadata
):
    """Emite evento de forma síncrona."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop.run_until_complete(emit_event(event_type, payload, **metadata))

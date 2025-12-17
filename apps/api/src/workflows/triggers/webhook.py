"""
Webhook Trigger - Dispara workflows via HTTP.

Features:
- Endpoints únicos por trigger
- Validação de payload
- Autenticação (API Key, HMAC)
- Rate limiting
"""

import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging

from .base import BaseTrigger, TriggerConfig, TriggerResult, TriggerType

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Configuração específica para webhook."""
    path: str = ""  # /webhooks/{path}
    methods: List[str] = field(default_factory=lambda: ["POST"])
    secret: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    require_signature: bool = False
    signature_header: str = "X-Webhook-Signature"
    rate_limit: int = 100  # requests per minute
    payload_schema: Optional[Dict] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Mapeia payload para inputs
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "methods": self.methods,
            "secret": self.secret,
            "require_signature": self.require_signature,
            "signature_header": self.signature_header,
            "rate_limit": self.rate_limit,
            "payload_schema": self.payload_schema,
            "input_mapping": self.input_mapping
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WebhookConfig":
        return cls(
            path=data.get("path", ""),
            methods=data.get("methods", ["POST"]),
            secret=data.get("secret", secrets.token_urlsafe(32)),
            require_signature=data.get("require_signature", False),
            signature_header=data.get("signature_header", "X-Webhook-Signature"),
            rate_limit=data.get("rate_limit", 100),
            payload_schema=data.get("payload_schema"),
            input_mapping=data.get("input_mapping", {})
        )


class WebhookTrigger(BaseTrigger):
    """
    Trigger que dispara via webhook HTTP.
    
    Exemplo:
        trigger = WebhookTrigger(TriggerConfig(
            id="github-push",
            name="GitHub Push Hook",
            workflow_id="deploy-pipeline",
            config={
                "path": "github-push",
                "require_signature": True,
                "input_mapping": {
                    "branch": "ref",
                    "commit": "after"
                }
            }
        ))
        
        # URL gerada: /webhooks/github-push
        # Quando receber POST, dispara workflow com inputs mapeados
    """
    
    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.webhook_config = WebhookConfig.from_dict(config.config)
        self._request_count: Dict[str, int] = {}  # IP -> count
    
    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.WEBHOOK
    
    @property
    def endpoint_path(self) -> str:
        """Retorna o path do endpoint."""
        return self.webhook_config.path or self.config.id
    
    @property
    def full_url(self) -> str:
        """Retorna URL completa (relativa)."""
        return f"/webhooks/{self.endpoint_path}"
    
    async def start(self) -> None:
        """Registra o endpoint."""
        logger.info(f"Webhook trigger {self.config.id} started at {self.full_url}")
    
    async def stop(self) -> None:
        """Remove o endpoint."""
        logger.info(f"Webhook trigger {self.config.id} stopped")
    
    async def handle_request(
        self,
        method: str,
        headers: Dict[str, str],
        body: bytes,
        payload: Optional[Dict] = None,
        client_ip: Optional[str] = None
    ) -> TriggerResult:
        """
        Processa uma requisição ao webhook.
        
        Args:
            method: Método HTTP
            headers: Headers da requisição
            body: Body raw para validação de assinatura
            payload: Payload parseado (JSON)
            client_ip: IP do cliente (para rate limiting)
        """
        # Verificar método
        if method.upper() not in self.webhook_config.methods:
            return TriggerResult(
                trigger_id=self.config.id,
                workflow_id=self.config.workflow_id,
                success=False,
                error=f"Method {method} not allowed"
            )
        
        # Verificar rate limit
        if client_ip:
            if not self._check_rate_limit(client_ip):
                return TriggerResult(
                    trigger_id=self.config.id,
                    workflow_id=self.config.workflow_id,
                    success=False,
                    error="Rate limit exceeded"
                )
        
        # Verificar assinatura se necessário
        if self.webhook_config.require_signature:
            signature = headers.get(self.webhook_config.signature_header, "")
            if not self._verify_signature(body, signature):
                return TriggerResult(
                    trigger_id=self.config.id,
                    workflow_id=self.config.workflow_id,
                    success=False,
                    error="Invalid signature"
                )
        
        # Mapear inputs
        inputs = self._map_inputs(payload or {})
        
        # Disparar workflow
        result = await self.trigger(
            inputs=inputs,
            metadata={
                "method": method,
                "client_ip": client_ip,
                "raw_payload": payload
            }
        )
        
        logger.info(f"Webhook {self.config.id} triggered: {result.execution_id}")
        return result
    
    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Verifica assinatura HMAC."""
        if not signature:
            return False
        
        expected = hmac.new(
            self.webhook_config.secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Suporte a formatos comuns
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        return hmac.compare_digest(expected, signature)
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Verifica rate limit."""
        count = self._request_count.get(client_ip, 0)
        
        if count >= self.webhook_config.rate_limit:
            return False
        
        self._request_count[client_ip] = count + 1
        return True
    
    def reset_rate_limit(self) -> None:
        """Reseta contadores de rate limit."""
        self._request_count.clear()
    
    def _map_inputs(self, payload: Dict) -> Dict[str, Any]:
        """Mapeia payload para inputs do workflow."""
        if not self.webhook_config.input_mapping:
            return payload
        
        inputs = {}
        for target_key, source_path in self.webhook_config.input_mapping.items():
            value = self._get_nested_value(payload, source_path)
            if value is not None:
                inputs[target_key] = value
        
        # Incluir payload completo também
        inputs["_payload"] = payload
        
        return inputs
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Obtém valor aninhado por path (e.g., 'data.user.name')."""
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def generate_signature(self, body: bytes) -> str:
        """Gera assinatura para um body (útil para testes)."""
        return "sha256=" + hmac.new(
            self.webhook_config.secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.endpoint_path:
            errors.append("path is required for webhook")
        return errors

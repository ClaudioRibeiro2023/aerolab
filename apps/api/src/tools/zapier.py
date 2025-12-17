"""
Ferramenta de integração com Zapier via Webhooks.

Permite disparar automações Zapier e receber dados de Zaps.
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx

from .base import BaseTool


class ZapierTool(BaseTool):
    """
    Ferramenta para integração com Zapier.
    
    Funcionalidades:
    - Disparar webhooks (triggers)
    - Enviar dados para Zaps
    - Receber callbacks
    - Templates de payloads comuns
    
    Configuração:
        Configure ZAPIER_WEBHOOK_URL ou passe URLs específicas por ação.
    """
    
    name = "zapier"
    description = "Dispara automações via webhooks do Zapier"
    
    def __init__(
        self,
        default_webhook_url: Optional[str] = None,
        webhooks: Optional[Dict[str, str]] = None
    ):
        self.default_webhook = default_webhook_url or os.getenv("ZAPIER_WEBHOOK_URL")
        self.webhooks = webhooks or {}
        
        # Carregar webhooks adicionais do ambiente
        for key, value in os.environ.items():
            if key.startswith("ZAPIER_WEBHOOK_"):
                name = key.replace("ZAPIER_WEBHOOK_", "").lower()
                if name != "url":
                    self.webhooks[name] = value
    
    async def trigger(
        self,
        webhook_name: Optional[str] = None,
        webhook_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Dispara um webhook Zapier.
        
        Args:
            webhook_name: Nome do webhook configurado
            webhook_url: URL direta do webhook
            data: Dados a enviar
            **kwargs: Dados adicionais (mesclados com data)
        
        Returns:
            Resposta do Zapier
        """
        # Determinar URL
        url = webhook_url
        if not url and webhook_name:
            url = self.webhooks.get(webhook_name)
        if not url:
            url = self.default_webhook
        
        if not url:
            raise ValueError(
                "Webhook URL não especificada. "
                "Configure ZAPIER_WEBHOOK_URL ou passe webhook_url/webhook_name"
            )
        
        # Preparar payload
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "agentos",
            **(data or {}),
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text,
                "webhook": webhook_name or "default"
            }
    
    async def trigger_agent_event(
        self,
        event_type: str,
        agent_name: str,
        data: Dict[str, Any],
        webhook_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispara evento de agente para Zapier.
        
        Args:
            event_type: Tipo do evento (execution_complete, error, etc.)
            agent_name: Nome do agente
            data: Dados do evento
            webhook_name: Nome do webhook
        """
        return await self.trigger(
            webhook_name=webhook_name,
            data={
                "event_type": event_type,
                "agent_name": agent_name,
                "data": data
            }
        )
    
    async def trigger_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        webhook_name: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispara notificação para Zapier.
        
        Args:
            title: Título da notificação
            message: Mensagem
            level: Nível (info, warning, error, success)
            webhook_name: Nome do webhook
            extra: Dados extras
        """
        return await self.trigger(
            webhook_name=webhook_name or "notifications",
            data={
                "type": "notification",
                "title": title,
                "message": message,
                "level": level,
                **(extra or {})
            }
        )
    
    async def trigger_lead(
        self,
        email: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
        webhook_name: Optional[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Dispara novo lead para Zapier (CRM integration).
        
        Args:
            email: Email do lead
            name: Nome
            company: Empresa
            webhook_name: Nome do webhook
            **extra: Campos extras
        """
        return await self.trigger(
            webhook_name=webhook_name or "leads",
            data={
                "type": "new_lead",
                "email": email,
                "name": name,
                "company": company,
                **extra
            }
        )
    
    async def trigger_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: str = "medium",
        webhook_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria tarefa via Zapier (integração com Trello, Asana, etc.).
        
        Args:
            title: Título da tarefa
            description: Descrição
            due_date: Data de vencimento
            assignee: Responsável
            priority: Prioridade
            webhook_name: Nome do webhook
        """
        return await self.trigger(
            webhook_name=webhook_name or "tasks",
            data={
                "type": "new_task",
                "title": title,
                "description": description,
                "due_date": due_date,
                "assignee": assignee,
                "priority": priority
            }
        )
    
    async def batch_trigger(
        self,
        items: List[Dict[str, Any]],
        webhook_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Dispara múltiplos webhooks em batch.
        
        Args:
            items: Lista de payloads
            webhook_name: Nome do webhook comum
        
        Returns:
            Lista de respostas
        """
        results = []
        for item in items:
            result = await self.trigger(
                webhook_name=webhook_name,
                data=item
            )
            results.append(result)
        return results
    
    def run(self, action: str, **kwargs) -> str:
        """
        Executa uma ação do Zapier.
        
        Args:
            action: Ação (trigger, agent_event, notification, lead, task, batch)
            **kwargs: Argumentos da ação
        """
        import asyncio
        
        actions = {
            "trigger": self.trigger,
            "agent_event": self.trigger_agent_event,
            "notification": self.trigger_notification,
            "lead": self.trigger_lead,
            "task": self.trigger_task,
            "batch": self.batch_trigger,
        }
        
        if action not in actions:
            return f"Ação desconhecida: {action}. Disponíveis: {list(actions.keys())}"
        
        result = asyncio.run(actions[action](**kwargs))
        return json.dumps(result, indent=2, default=str)


def get_zapier_tool(default_webhook_url: Optional[str] = None) -> ZapierTool:
    """Factory para criar ZapierTool."""
    return ZapierTool(default_webhook_url=default_webhook_url)

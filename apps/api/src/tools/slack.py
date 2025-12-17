"""
Ferramenta de integração com Slack.

Permite enviar mensagens, notificações e interagir com canais Slack.
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx

from .base import BaseTool


@dataclass
class SlackMessage:
    """Representa uma mensagem do Slack."""
    channel: str
    text: str
    thread_ts: Optional[str] = None
    blocks: Optional[List[Dict]] = None
    attachments: Optional[List[Dict]] = None


class SlackTool(BaseTool):
    """
    Ferramenta para integração com Slack.
    
    Funcionalidades:
    - Enviar mensagens para canais
    - Enviar mensagens diretas
    - Criar threads de discussão
    - Enviar notificações formatadas
    - Buscar mensagens
    
    Configuração:
        Requer SLACK_BOT_TOKEN no ambiente.
        Opcionalmente SLACK_DEFAULT_CHANNEL para canal padrão.
    """
    
    name = "slack"
    description = "Envia mensagens e notificações para canais Slack"
    
    def __init__(self, token: Optional[str] = None, default_channel: Optional[str] = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel or os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
        self.base_url = "https://slack.com/api"
        
        if not self.token:
            raise ValueError(
                "SLACK_BOT_TOKEN não configurado. "
                "Obtenha um token em https://api.slack.com/apps"
            )
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Faz uma requisição à API do Slack."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{endpoint}",
                headers=self._headers(),
                **kwargs
            )
            data = response.json()
            
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error', 'unknown')}")
            
            return data
    
    async def send_message(
        self,
        text: str,
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem para um canal.
        
        Args:
            text: Texto da mensagem
            channel: Canal destino (usa default se não especificado)
            thread_ts: Timestamp para responder em thread
            blocks: Blocos de formatação avançada
        
        Returns:
            Resposta da API com ts da mensagem
        """
        payload = {
            "channel": channel or self.default_channel,
            "text": text,
        }
        
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        if blocks:
            payload["blocks"] = blocks
        
        return await self._request("POST", "chat.postMessage", json=payload)
    
    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        channel: Optional[str] = None,
        fields: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envia uma notificação formatada.
        
        Args:
            title: Título da notificação
            message: Mensagem principal
            level: Nível (info, warning, error, success)
            channel: Canal destino
            fields: Campos adicionais key-value
        
        Returns:
            Resposta da API
        """
        colors = {
            "info": "#3498db",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "success": "#27ae60",
        }
        
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅",
        }
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emojis.get(level, 'ℹ️')} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        if fields:
            field_blocks = [
                {
                    "type": "mrkdwn",
                    "text": f"*{k}:*\n{v}"
                }
                for k, v in fields.items()
            ]
            blocks.append({
                "type": "section",
                "fields": field_blocks[:10]  # Máximo 10 campos
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Enviado por *AgentOS* 🤖"
                }
            ]
        })
        
        return await self.send_message(
            text=f"{title}: {message}",
            channel=channel,
            blocks=blocks
        )
    
    async def send_agent_result(
        self,
        agent_name: str,
        prompt: str,
        result: str,
        duration: float,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia resultado de execução de agente.
        
        Args:
            agent_name: Nome do agente
            prompt: Prompt executado
            result: Resultado obtido
            duration: Duração em segundos
            channel: Canal destino
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 Resultado: {agent_name}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Prompt:*\n```{prompt[:500]}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resultado:*\n{result[:2000]}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏱️ Duração: {duration:.2f}s"
                    }
                ]
            }
        ]
        
        return await self.send_message(
            text=f"Resultado de {agent_name}",
            channel=channel,
            blocks=blocks
        )
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """Lista canais disponíveis."""
        data = await self._request("GET", "conversations.list")
        return data.get("channels", [])
    
    async def get_channel_history(
        self,
        channel: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtém histórico de mensagens de um canal."""
        data = await self._request(
            "GET",
            "conversations.history",
            params={"channel": channel, "limit": limit}
        )
        return data.get("messages", [])
    
    def run(self, action: str, **kwargs) -> str:
        """
        Executa uma ação do Slack (síncrono para compatibilidade com agentes).
        
        Args:
            action: Ação a executar (send, notify, list_channels)
            **kwargs: Argumentos da ação
        """
        import asyncio
        
        if action == "send":
            result = asyncio.run(self.send_message(**kwargs))
        elif action == "notify":
            result = asyncio.run(self.send_notification(**kwargs))
        elif action == "agent_result":
            result = asyncio.run(self.send_agent_result(**kwargs))
        elif action == "list_channels":
            result = asyncio.run(self.list_channels())
        else:
            return f"Ação desconhecida: {action}"
        
        return json.dumps(result, indent=2, default=str)


def get_slack_tool(token: Optional[str] = None) -> SlackTool:
    """Factory para criar SlackTool."""
    return SlackTool(token=token)

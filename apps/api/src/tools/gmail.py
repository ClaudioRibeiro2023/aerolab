"""
Ferramenta de integração com Gmail.

Permite enviar emails, ler inbox e gerenciar mensagens.
"""

import os
import base64
import json
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import httpx

from .base import BaseTool


class GmailTool(BaseTool):
    """
    Ferramenta para integração com Gmail API.
    
    Funcionalidades:
    - Enviar emails (texto e HTML)
    - Enviar com anexos
    - Listar mensagens do inbox
    - Buscar emails
    - Marcar como lido/não lido
    
    Configuração:
        Requer GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET e GMAIL_REFRESH_TOKEN.
        Ou GMAIL_API_KEY para modo simplificado (somente envio via SMTP).
    """
    
    name = "gmail"
    description = "Envia e gerencia emails via Gmail"
    
    def __init__(
        self,
        credentials: Optional[Dict[str, str]] = None,
        smtp_mode: bool = False
    ):
        self.smtp_mode = smtp_mode
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = {
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
            }
        
        self._access_token: Optional[str] = None
        self._user_email: Optional[str] = None
    
    async def _get_access_token(self) -> str:
        """Obtém ou renova o access token."""
        if self._access_token:
            return self._access_token
        
        if not all([self.credentials.get("client_id"), 
                    self.credentials.get("client_secret"),
                    self.credentials.get("refresh_token")]):
            raise ValueError(
                "Gmail credentials não configuradas. "
                "Configure GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET e GMAIL_REFRESH_TOKEN"
            )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"],
                    "refresh_token": self.credentials["refresh_token"],
                    "grant_type": "refresh_token",
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to refresh token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token
    
    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Faz uma requisição à API do Gmail."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{endpoint}",
                headers=self._headers(token),
                **kwargs
            )
            
            if response.status_code >= 400:
                raise Exception(f"Gmail API error: {response.status_code} - {response.text}")
            
            return response.json() if response.text else {}
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envia um email.
        
        Args:
            to: Destinatário(s) separados por vírgula
            subject: Assunto
            body: Corpo do email (texto ou HTML)
            html: Se True, body é HTML
            cc: Lista de CC
            bcc: Lista de BCC
            attachments: Lista de anexos [{"filename": str, "content": bytes, "mime_type": str}]
        
        Returns:
            Dados da mensagem enviada
        """
        # Criar mensagem
        if attachments:
            message = MIMEMultipart()
            if html:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))
            
            for att in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(att["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{att["filename"]}"'
                )
                message.attach(part)
        else:
            message = MIMEText(body, "html" if html else "plain")
        
        message["to"] = to
        message["subject"] = subject
        
        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)
        
        # Codificar para base64 URL-safe
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        return await self._request(
            "POST",
            "users/me/messages/send",
            json={"raw": raw}
        )
    
    async def send_template_email(
        self,
        to: str,
        template_name: str,
        variables: Dict[str, str],
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia email usando template predefinido.
        
        Args:
            to: Destinatário
            template_name: Nome do template
            variables: Variáveis para substituição
            subject: Assunto (opcional, pode estar no template)
        """
        templates = {
            "welcome": {
                "subject": "Bem-vindo ao AgentOS! 🤖",
                "body": """
                <h2>Olá {name}!</h2>
                <p>Bem-vindo à plataforma AgentOS.</p>
                <p>Você pode começar criando seu primeiro agente em <a href="{url}/agents/new">criar agente</a>.</p>
                <p>Atenciosamente,<br>Equipe AgentOS</p>
                """
            },
            "notification": {
                "subject": "Notificação: {title}",
                "body": """
                <h3>{title}</h3>
                <p>{message}</p>
                <p><small>Enviado por AgentOS em {timestamp}</small></p>
                """
            },
            "agent_result": {
                "subject": "Resultado do Agente: {agent_name}",
                "body": """
                <h2>🤖 {agent_name}</h2>
                <h4>Prompt:</h4>
                <blockquote>{prompt}</blockquote>
                <h4>Resultado:</h4>
                <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
                {result}
                </div>
                <p><small>Duração: {duration}s</small></p>
                """
            }
        }
        
        template = templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' não encontrado")
        
        # Substituir variáveis
        email_subject = subject or template["subject"]
        email_body = template["body"]
        
        for key, value in variables.items():
            email_subject = email_subject.replace(f"{{{key}}}", str(value))
            email_body = email_body.replace(f"{{{key}}}", str(value))
        
        return await self.send_email(
            to=to,
            subject=email_subject,
            body=email_body,
            html=True
        )
    
    async def list_messages(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista mensagens do inbox.
        
        Args:
            query: Query de busca (ex: "is:unread", "from:user@example.com")
            max_results: Número máximo de resultados
            label_ids: Filtrar por labels
        
        Returns:
            Lista de mensagens
        """
        params: Dict[str, Any] = {"maxResults": max_results}
        
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids
        
        data = await self._request("GET", "users/me/messages", params=params)
        return data.get("messages", [])
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma mensagem."""
        return await self._request("GET", f"users/me/messages/{message_id}")
    
    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Marca mensagem como lida."""
        return await self._request(
            "POST",
            f"users/me/messages/{message_id}/modify",
            json={"removeLabelIds": ["UNREAD"]}
        )
    
    async def mark_as_unread(self, message_id: str) -> Dict[str, Any]:
        """Marca mensagem como não lida."""
        return await self._request(
            "POST",
            f"users/me/messages/{message_id}/modify",
            json={"addLabelIds": ["UNREAD"]}
        )
    
    async def trash_message(self, message_id: str) -> Dict[str, Any]:
        """Move mensagem para lixeira."""
        return await self._request("POST", f"users/me/messages/{message_id}/trash")
    
    def run(self, action: str, **kwargs) -> str:
        """
        Executa uma ação do Gmail.
        
        Args:
            action: Ação (send, send_template, list, get, mark_read, trash)
            **kwargs: Argumentos da ação
        """
        import asyncio
        
        actions = {
            "send": self.send_email,
            "send_template": self.send_template_email,
            "list": self.list_messages,
            "get": self.get_message,
            "mark_read": self.mark_as_read,
            "mark_unread": self.mark_as_unread,
            "trash": self.trash_message,
        }
        
        if action not in actions:
            return f"Ação desconhecida: {action}. Disponíveis: {list(actions.keys())}"
        
        result = asyncio.run(actions[action](**kwargs))
        return json.dumps(result, indent=2, default=str)


def get_gmail_tool() -> GmailTool:
    """Factory para criar GmailTool."""
    return GmailTool()

# Eventos e Webhooks

> Sistema de eventos e webhooks da plataforma Agno.

---

## Visão Geral

A plataforma emite eventos em pontos-chave que podem ser capturados via webhooks.

---

## Tipos de Eventos

| Evento | Descrição |
|--------|-----------|
| `agent.created` | Agente criado |
| `agent.updated` | Agente atualizado |
| `agent.deleted` | Agente removido |
| `agent.executed` | Agente executou uma tarefa |
| `team.created` | Time criado |
| `team.executed` | Time executou uma tarefa |
| `workflow.created` | Workflow criado |
| `workflow.executed` | Workflow executou |
| `workflow.failed` | Workflow falhou |
| `rag.ingested` | Documentos indexados |
| `rag.queried` | Query RAG executada |
| `hitl.requested` | Intervenção humana solicitada |
| `hitl.completed` | Intervenção humana completada |

---

## Payload de Evento

```json
{
  "event": "agent.executed",
  "timestamp": "2024-12-16T10:00:00Z",
  "payload": {
    "agent_id": "researcher",
    "input": "What are AI trends?",
    "output": "Based on my research...",
    "duration_ms": 2345
  },
  "metadata": {
    "user_id": "user@example.com",
    "request_id": "uuid"
  }
}
```

---

## Configurando Webhooks

### Registro de Webhook

```http
POST /webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["agent.executed", "workflow.failed"],
  "secret": "your-webhook-secret",
  "headers": {
    "X-Custom-Header": "value"
  }
}
```

### Response

```json
{
  "id": "webhook-uuid",
  "url": "https://your-app.com/webhook",
  "events": ["agent.executed", "workflow.failed"],
  "enabled": true,
  "created_at": "2024-12-16T10:00:00Z"
}
```

---

## Recebendo Webhooks

### Headers

Cada webhook inclui:

```http
Content-Type: application/json
X-Webhook-ID: webhook-uuid
X-Webhook-Event: agent.executed
X-Webhook-Signature: sha256=...
X-Webhook-Timestamp: 1702234567
```

### Verificando Assinatura

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Retries

Se o webhook falhar (não-2xx), o sistema faz retries:

| Tentativa | Delay |
|-----------|-------|
| 1 | Imediato |
| 2 | 1 minuto |
| 3 | 5 minutos |
| 4 | 30 minutos |
| 5 | 2 horas |

Após 5 falhas, o webhook é desabilitado.

---

## Gerenciando Webhooks

```http
GET    /webhooks           # Listar webhooks
GET    /webhooks/{id}      # Obter webhook
PATCH  /webhooks/{id}      # Atualizar webhook
DELETE /webhooks/{id}      # Remover webhook
POST   /webhooks/{id}/test # Testar webhook
```

---

## Código Relevante

- **Implementação:** `src/events/webhooks.py`
- **Models:** `WebhookConfig`, `WebhookDelivery`

---

## [TODO: confirmar]

- Endpoints de webhook management podem não estar todos implementados
- Verificar configuração de retry exata no código

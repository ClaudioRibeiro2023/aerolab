# Modelo de Dados

> Entidades principais e suas relações na plataforma Agno.

---

## Diagrama ER

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Agent     │       │    Team     │       │  Workflow   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ name        │◄──────│ coordinator │       │ name        │
│ model       │       │ name        │       │ steps       │
│ instructions│       │ mode        │       │ status      │
│ tools       │       │ members     │───────►│ created_at  │
│ memory      │       │ created_at  │       │ updated_at  │
│ created_at  │       └─────────────┘       └─────────────┘
└─────────────┘              │
       │                     │
       │              ┌──────┴──────┐
       │              │ TeamMember  │
       │              ├─────────────┤
       └──────────────│ agent_id    │
                      │ role        │
                      └─────────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  RAG Doc    │       │ HITL Session│       │   Tenant    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ collection  │       │ workflow_id │       │ name        │
│ content     │       │ status      │       │ plan        │
│ embedding   │       │ data        │       │ users       │
│ metadata    │       │ created_at  │       │ created_at  │
└─────────────┘       └─────────────┘       └─────────────┘
```

---

## Entidades Principais

### Agent

Agente de IA com configuração e capacidades.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único (UUID ou name) |
| `name` | string | Nome do agente |
| `model` | string | ID do modelo LLM (ex: `groq:llama-3.3-70b-versatile`) |
| `instructions` | string | System prompt |
| `tools` | list[string] | Lista de ferramentas habilitadas |
| `memory` | object | Configuração de memória |
| `created_at` | datetime | Data de criação |
| `updated_at` | datetime | Data de atualização |

**Localização:** `src/agents/models.py`

---

### Team

Time de múltiplos agentes.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único |
| `name` | string | Nome do time |
| `coordinator_id` | string | Agente coordenador |
| `members` | list[TeamMember] | Membros do time |
| `mode` | string | Modo de orquestração |
| `created_at` | datetime | Data de criação |

**Modos:** `sequential`, `parallel`, `hierarchical`, `swarm`

**Localização:** `src/teams/models.py`

---

### Workflow

Pipeline de execução com múltiplos passos.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | Identificador único |
| `name` | string | Nome do workflow |
| `description` | string | Descrição |
| `steps` | list[WorkflowStep] | Passos do workflow |
| `status` | string | Status atual |
| `created_at` | datetime | Data de criação |

**Status:** `draft`, `active`, `paused`, `completed`, `failed`

**Localização:** `src/workflows/models.py`

---

### RAG Document

Documento indexado para RAG.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | ID do documento |
| `collection` | string | Nome da collection |
| `content` | string | Conteúdo textual |
| `embedding` | vector | Vetor de embedding |
| `metadata` | object | Metadados (source, page, etc.) |

**Storage:** ChromaDB

**Localização:** `src/rag/service.py`

---

### HITL Session

Sessão de Human-in-the-Loop.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | ID da sessão |
| `workflow_id` | string | Workflow relacionado |
| `step_id` | string | Passo que solicitou |
| `status` | string | Status da sessão |
| `request_data` | object | Dados do request |
| `response_data` | object | Resposta humana |
| `created_at` | datetime | Data de criação |
| `completed_at` | datetime | Data de conclusão |

**Status:** `pending`, `in_progress`, `completed`, `cancelled`, `timeout`

**Localização:** `src/hitl/models.py`

---

### Tenant

Tenant para multi-tenancy.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | string | ID do tenant |
| `name` | string | Nome |
| `plan` | string | Plano (free, pro, enterprise) |
| `users` | list[string] | Usuários do tenant |
| `settings` | object | Configurações |
| `created_at` | datetime | Data de criação |

**Localização:** `src/auth/multitenancy.py`

---

## Relacionamentos

```
Agent (1) ──── (*) TeamMember
Team (1) ──── (*) TeamMember
Team (1) ──── (1) Agent [coordinator]

Workflow (1) ──── (*) WorkflowStep
WorkflowStep (*) ──── (1) Agent

Workflow (1) ──── (*) HITLSession

Tenant (1) ──── (*) User
Tenant (1) ──── (*) Agent
Tenant (1) ──── (*) Team
```

---

## Schemas JSON

### Agent Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string", "minLength": 1 },
    "model": { "type": "string" },
    "instructions": { "type": "string" },
    "tools": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["name", "model"]
}
```

### Team Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "coordinator_id": { "type": "string" },
    "mode": {
      "type": "string",
      "enum": ["sequential", "parallel", "hierarchical", "swarm"]
    },
    "members": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "agent_id": { "type": "string" },
          "role": { "type": "string" }
        }
      }
    }
  },
  "required": ["name", "coordinator_id"]
}
```

---

## Referências

- [Armazenamento e Migrações](31-armazenamento-e-migracoes.md)
- [RAG Indexação](32-rag-indexacao.md)

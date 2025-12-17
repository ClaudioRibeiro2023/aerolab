# Módulos e Limites

> Documentação dos módulos do sistema e suas responsabilidades.

---

## Visão Geral dos Módulos

O backend é organizado em módulos independentes seguindo arquitetura **feature-first**:

```
src/
├── Core (fundação)
│   ├── agents/          → Agentes de IA
│   ├── teams/           → Times multi-agente
│   ├── workflows/       → Pipelines e workflows
│   └── rag/             → Retrieval-Augmented Generation
│
├── Studios (interfaces visuais)
│   ├── flow_studio/     → Visual workflow builder
│   ├── domain_studio/   → Domínios especializados
│   ├── team_orchestrator/ → Orquestração de times
│   └── dashboard/       → Observabilidade
│
├── Infrastructure (suporte)
│   ├── auth/            → Autenticação/autorização
│   ├── observability/   → Logs, métricas, health
│   ├── os/routes/       → Routers FastAPI
│   └── middleware/      → Rate limiting, etc.
│
└── Extensions (extensões)
    ├── tools/           → 30+ ferramentas
    ├── compliance/      → LGPD/GDPR
    ├── billing/         → Sistema de billing
    └── marketplace/     → Marketplace de agentes
```

---

## Módulos Core

### `agents/` - Agentes de IA

**Responsabilidade:** Criar e gerenciar agentes de IA.

| Componente | Descrição |
|------------|-----------|
| `base_agent.py` | Factory para criar agentes com diferentes LLMs |
| `specialized/` | Agentes especializados (pesquisador, escritor, etc.) |
| `registry.py` | Registro global de agentes disponíveis |

**Interface pública:**
```python
from src.agents import BaseAgent

agent = BaseAgent.create(
    model_id="groq:llama-3.3-70b-versatile",
    instructions="You are a helpful assistant",
    tools=[web_search, code_executor]
)
response = agent.run("What is the weather?")
```

**Dependências:**
- `agno` (framework)
- `tools/` (ferramentas)
- `memory/` (persistência de contexto)

---

### `teams/` - Times Multi-Agente

**Responsabilidade:** Orquestrar múltiplos agentes trabalhando em conjunto.

| Componente | Descrição |
|------------|-----------|
| `models.py` | Team, TeamMember, TeamConfig |
| `pipelines.py` | Pipelines predefinidas (research, content, etc.) |

**Interface pública:**
```python
from src.teams import Team

team = Team(
    name="Research Team",
    coordinator=researcher_agent,
    workers=[writer_agent, editor_agent]
)
result = team.execute("Write a report about AI trends")
```

**Dependências:**
- `agents/` (agentes do time)

---

### `workflows/` - Pipelines e Workflows

**Responsabilidade:** Definir e executar sequências de operações.

| Componente | Descrição |
|------------|-----------|
| `models.py` | Workflow, WorkflowStep, WorkflowStatus |
| `registry.py` | Registro de workflows disponíveis |
| `predefined/` | Workflows prontos para uso |

**Interface pública:**
```python
from src.workflows import WorkflowRegistry

registry = WorkflowRegistry()
workflow = registry.get("research-write")
result = workflow.execute(input_data)
```

**Dependências:**
- `agents/` (execução de steps)
- `teams/` (workflows com times)

---

### `rag/` - Retrieval-Augmented Generation

**Responsabilidade:** Indexar documentos e responder queries com contexto.

| Componente | Descrição |
|------------|-----------|
| `service.py` | RagService (ChromaDB client) |
| `chunking.py` | Estratégias de chunking de texto |

**Interface pública:**
```python
from src.rag import get_rag_service

rag = get_rag_service()
rag.add_texts(collection="docs", texts=["..."])
results = rag.query(collection="docs", query="What is X?")
```

**Dependências:**
- `chromadb` (vector store)
- `config/` (configurações)

---

## Módulos Studios

### `flow_studio/` - Visual Workflow Builder

**Responsabilidade:** Editor visual drag-and-drop para workflows.

| Componente | Descrição |
|------------|-----------|
| `api/` | Endpoints REST |
| `engine.py` | Motor de execução de workflows |
| `executor.py` | Executores de nós |
| `nodes/` | Tipos de nós (agent, condition, loop, etc.) |
| `ai/nl_designer.py` | NL Designer (criar workflows via linguagem natural) |

**Endpoints:**
- `GET /api/flow-studio/health`
- `GET /api/flow-studio/stats`
- `POST /api/flow-studio/execute`

---

### `domain_studio/` - Domínios Especializados

**Responsabilidade:** RAG engines customizados por domínio.

| Componente | Descrição |
|------------|-----------|
| `engines/agentic_rag.py` | RAG com planejamento autônomo |
| `engines/graph_rag.py` | RAG com knowledge graph |
| `engines/compliance_engine.py` | RAG para compliance |
| `engines/multimodal_engine.py` | RAG multimodal |
| `registry.py` | Registro de domínios |

**Endpoints:**
- `GET /api/domain-studio/health`
- `GET /api/domain-studio/domains`
- `POST /api/domain-studio/query`

---

### `team_orchestrator/` - Orquestração de Times

**Responsabilidade:** Coordenar execução de times multi-agente.

| Componente | Descrição |
|------------|-----------|
| `api/` | Endpoints REST |
| `engine.py` | Motor de orquestração |
| `modes/` | Modos de orquestração (sequential, parallel, etc.) |

**Endpoints:**
- `GET /api/team-orchestrator/health`
- `GET /api/team-orchestrator/modes`
- `POST /api/team-orchestrator/execute`

---

### `dashboard/` - Observabilidade

**Responsabilidade:** Métricas, insights e monitoramento.

| Componente | Descrição |
|------------|-----------|
| `api/routes.py` | Endpoints de dashboard |
| `insights/` | Recommendation engine |
| `components/` | Componentes de visualização |

**Endpoints:**
- `GET /api/dashboard/health`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/insights`

---

## Módulos Infrastructure

### `auth/` - Autenticação e Autorização

**Responsabilidade:** JWT, RBAC, SSO, multi-tenancy.

| Componente | Descrição |
|------------|-----------|
| `deps.py` | Dependencies FastAPI (get_current_user) |
| `jwt.py` | Criação e validação de tokens |
| `sso.py` | SSO (Google, GitHub, Microsoft) |
| `multitenancy.py` | Suporte a múltiplos tenants |

**Interface pública:**
```python
from src.auth import get_current_user, create_access_token

# Dependency
@router.get("/protected")
async def protected(user = Depends(get_current_user)):
    return {"user": user.email}

# Token creation
token = create_access_token({"sub": "user@example.com", "role": "admin"})
```

---

### `observability/` - Logs, Métricas, Health

**Responsabilidade:** Monitoramento e diagnóstico.

| Componente | Descrição |
|------------|-----------|
| `logging.py` | Structured JSON logging |
| `metrics.py` | Métricas Prometheus-style |
| `health.py` | Health checks (liveness/readiness) |

**Endpoints:**
- `GET /health` - Status geral
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Métricas Prometheus

---

### `os/routes/` - Routers Modulares

**Responsabilidade:** Endpoints REST organizados por domínio.

| Router | Prefixo | Descrição |
|--------|---------|-----------|
| `auth.py` | `/auth` | Login, perfil |
| `agents.py` | `/agents` | CRUD de agentes |
| `teams.py` | `/teams` | CRUD de times |
| `workflows.py` | `/workflows` | CRUD de workflows |
| `rag.py` | `/rag` | Ingest e query RAG |
| `hitl.py` | `/hitl` | Human-in-the-loop |
| `storage.py` | `/storage` | File storage |
| `memory.py` | `/memory` | Memory management |
| `admin.py` | `/admin` | Administração |
| `audit.py` | `/audit` | Audit logs |

---

## Limites e Boundaries

### Comunicação entre Módulos

```
┌─────────────┐     imports      ┌─────────────┐
│   teams/    │ ───────────────► │   agents/   │
└─────────────┘                  └─────────────┘
       │                                │
       │                                │
       ▼                                ▼
┌─────────────┐                  ┌─────────────┐
│  workflows/ │                  │    rag/     │
└─────────────┘                  └─────────────┘
```

### Regras de Dependência

1. **Core pode depender de Core:** `teams/` pode importar de `agents/`
2. **Studios dependem de Core:** `flow_studio/` pode importar de `agents/`, `workflows/`
3. **Infrastructure é independente:** `auth/`, `observability/` não dependem de Core
4. **Extensions dependem de Core:** `tools/` pode ser usado por `agents/`

### Anti-patterns Evitados

- ❌ Dependências circulares
- ❌ Módulos conhecendo detalhes de implementação de outros
- ❌ Imports de camadas superiores em camadas inferiores

---

## Referências

- [ADR-002: Arquitetura Modular](../adr_v2/decisions/10-architecture/002-arquitetura-modular.md)
- [Mapa do Repositório](../99-anexos/99-mapa-do-repo.md)

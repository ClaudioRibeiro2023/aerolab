# 📘 Referência Técnica Completa — Agno Multi-Agent Platform

> **Versão:** 2.1.0 | **Atualizado:** 2025-12-10
> **Propósito:** Documentação técnica completa para merges, integrações e novos desenvolvedores

---

## Índice

1. [Visão Geral da Plataforma](#1-visão-geral-da-plataforma)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Estrutura de Diretórios](#4-estrutura-de-diretórios)
5. [Módulos do Backend](#5-módulos-do-backend)
6. [Frontend (Next.js)](#6-frontend-nextjs)
7. [API REST](#7-api-rest)
8. [Sistema de Autenticação](#8-sistema-de-autenticação)
9. [Configuração e Variáveis de Ambiente](#9-configuração-e-variáveis-de-ambiente)
10. [Banco de Dados e Persistência](#10-banco-de-dados-e-persistência)
11. [Deploy e Infraestrutura](#11-deploy-e-infraestrutura)
12. [Integrações Externas](#12-integrações-externas)
13. [Testes](#13-testes)
14. [Guia para Merges](#14-guia-para-merges)

---

## 1. Visão Geral da Plataforma

### O que é

A **Agno Multi-Agent Platform** é uma plataforma completa para criação, gerenciamento e execução de agentes de IA. Permite:

- Criar agentes com múltiplos provedores de LLM (OpenAI, Anthropic, Groq)
- Orquestrar times multi-agente para tarefas complexas
- Construir workflows visuais com o Flow Studio
- Implementar RAG (Retrieval-Augmented Generation)
- Gerenciar memória de longo prazo
- Controlar acesso via RBAC

### URLs de Produção

| Ambiente | URL |
|----------|-----|
| Frontend | `https://agno-multi-agent.netlify.app` |
| Backend | `https://web-production-940ab.up.railway.app` |
| Repositório | `https://github.com/ClaudioRibeiro2023/agno-multi-agent-platform` |

### Métricas do Projeto

| Categoria | Quantidade |
|-----------|------------|
| Arquivos Python (src/) | 150+ |
| Componentes React | 50+ |
| Flow Studio Node Types | 60+ |
| Ferramentas disponíveis | 25+ |
| Templates de agentes | 15 |
| Testes automatizados | 348+ |
| Módulos backend | 35+ |

---

## 2. Stack Tecnológica

### Backend

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| Python | 3.12+ | Linguagem principal |
| FastAPI | 0.115+ | Framework web async |
| Agno | 2.0+ | Framework de agentes |
| Pydantic | 2.5+ | Validação e serialização |
| SQLAlchemy | 2.0+ | ORM |
| ChromaDB | 1.0+ | Vector store para RAG |
| uvicorn | 0.34+ | Servidor ASGI |

### Frontend

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| Next.js | 15.x | Framework React |
| React | 18.3 | Biblioteca UI |
| TypeScript | 5.6+ | Tipagem estática |
| TailwindCSS | 3.4+ | Styling |
| Zustand | 4.5+ | State management |
| React Flow | 12.x | Visual workflow builder |
| Recharts | 3.5+ | Gráficos |

### Infraestrutura

| Serviço | Propósito |
|---------|-----------|
| Railway | Backend hosting |
| Netlify | Frontend hosting |
| GitHub Actions | CI/CD |
| Docker | Containerização |
| Redis (opcional) | Cache |

---

## 3. Arquitetura do Sistema

### Diagrama de Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │  Pages  │  │Components│  │  Hooks  │  │ State (Zustand) │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
└───────┼────────────┼────────────┼────────────────┼──────────┘
        │            │            │                │
        └────────────┴────────────┴────────────────┘
                            │
                    ┌───────▼───────┐
                    │   HTTP/WSS    │
                    └───────┬───────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    API Layer                         │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐  │    │
│  │  │ Auth   │ │ Agents │ │ Teams  │ │  Workflows   │  │    │
│  │  │ Router │ │ Router │ │ Router │ │    Router    │  │    │
│  │  └────────┘ └────────┘ └────────┘ └──────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│  ┌─────────────────────────▼───────────────────────────┐    │
│  │                  Business Layer                      │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │    │
│  │  │ Agents  │ │  Teams  │ │Workflows│ │Flow Studio│  │    │
│  │  │ Service │ │ Service │ │ Service │ │  Service  │  │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│  ┌─────────────────────────▼───────────────────────────┐    │
│  │               Infrastructure Layer                   │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐   │    │
│  │  │Config│ │ Auth │ │ RAG  │ │Memory│ │  Tools   │   │    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│  ┌─────────────────────────▼───────────────────────────┐    │
│  │                   Agno Framework                     │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │    │
│  │  │  Agent  │ │  Team   │ │Workflow │ │   Tools   │  │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  LLM APIs │    │  ChromaDB │    │  SQLite   │
    │  (OpenAI, │    │  (Vector  │    │   (DB)    │
    │   Groq)   │    │   Store)  │    │           │
    └───────────┘    └───────────┘    └───────────┘
```

### Padrões de Design

| Padrão | Uso |
|--------|-----|
| **Factory** | Criação de agentes e modelos |
| **Singleton** | Settings e configurações |
| **Strategy** | Múltiplos LLM providers |
| **Chain of Responsibility** | Workflows e pipelines |
| **Repository** | Acesso a dados |

---

## 4. Estrutura de Diretórios

### Raiz do Projeto

```
agno-multi-agent-platform/
├── server.py                 # Entry point principal do backend
├── app.py                    # Entry point legacy (deprecated)
├── start.py                  # Script para iniciar backend+frontend
├── requirements.txt          # Dependências Python
├── pyproject.toml            # Configuração do projeto Python
├── docker-compose.yml        # Orquestração Docker
├── Dockerfile                # Build do container
├── netlify.toml              # Configuração Netlify
├── railway.json              # Configuração Railway
├── mkdocs.yml                # Configuração MkDocs (docs)
│
├── .env.example              # Template de variáveis de ambiente
├── .env                      # Variáveis de ambiente (não commitado)
├── .gitignore                # Arquivos ignorados pelo Git
├── .pre-commit-config.yaml   # Hooks de pre-commit
│
├── src/                      # Código-fonte do backend
├── frontend/                 # Código-fonte do frontend
├── scripts/                  # Scripts de automação
├── tests/                    # Testes automatizados
├── docs/                     # Documentação
├── examples/                 # Exemplos de uso
└── data/                     # Dados e artefatos
```

### Backend (src/)

```
src/
├── __init__.py
├── agents/                   # Agentes base e especializados
│   ├── __init__.py
│   ├── base_agent.py         # Classe BaseAgent (factory)
│   ├── agent_templates.py    # 15 templates pré-configurados
│   └── domains/              # Agentes por domínio
│       ├── geo.py
│       ├── finance.py
│       ├── legal.py
│       └── ...
│
├── auth/                     # Autenticação e autorização
│   ├── __init__.py
│   ├── jwt_handler.py        # Geração/validação de JWT
│   ├── rbac.py               # Role-Based Access Control
│   └── dependencies.py       # FastAPI dependencies
│
├── billing/                  # Sistema de billing
│   ├── metering.py           # Medição de uso
│   ├── pricing.py            # Precificação
│   └── plans.py              # Planos de assinatura
│
├── chat/                     # Módulo de chat
│   ├── api/                  # Endpoints de chat
│   └── services/             # Lógica de chat
│
├── compliance/               # LGPD/GDPR
│   ├── consent.py            # Gestão de consentimento
│   └── pii.py                # Detecção de PII
│
├── config/                   # Configurações centralizadas
│   ├── __init__.py
│   ├── settings.py           # Classe Settings (singleton)
│   └── env_validator.py      # Validação de variáveis
│
├── dashboard/                # Observabilidade e métricas
│   ├── api/
│   ├── models/
│   └── services/
│
├── domain_studio/            # Domínios especializados
│   ├── geo/
│   ├── database/
│   ├── devops/
│   ├── finance/
│   ├── legal/
│   └── corporate/
│
├── enterprise/               # Features enterprise
│   ├── sso/                  # Single Sign-On
│   ├── multiregion/          # Multi-region
│   └── whitelabel/           # White-label
│
├── flow_studio/              # Visual Workflow Builder
│   ├── ai/                   # NL Designer, Optimizer
│   │   ├── nl_designer.py
│   │   ├── optimizer.py
│   │   └── predictor.py
│   ├── api/                  # REST + WebSocket
│   ├── execution/            # Runtime de execução
│   ├── nodes/                # 60+ tipos de nós
│   └── tests/
│
├── marketplace/              # Marketplace de agentes
│   ├── publisher.py
│   ├── search.py
│   └── reviews.py
│
├── mcp/                      # Model Context Protocol
│   └── ...
│
├── memory/                   # Gestão de memória
│   ├── short_term.py
│   ├── long_term.py
│   └── episodic.py
│
├── observability/            # Métricas e tracing
│   ├── metrics.py
│   ├── tracing.py
│   └── logging.py
│
├── os/                       # AgentOS runtime
│   ├── builder.py            # Builder de rotas
│   └── runtime.py
│
├── rag/                      # Retrieval-Augmented Generation
│   ├── __init__.py
│   ├── service.py            # RAG service principal
│   ├── ingestion.py          # Pipeline de ingestão
│   └── retrieval.py          # Busca semântica
│
├── rules/                    # Rules engine
│   └── engine.py
│
├── sdk/                      # SDK Python
│   └── ...
│
├── studio/                   # Agent studio
│   └── ...
│
├── team_orchestrator/        # Orquestração de times
│   ├── coordinator.py
│   └── strategies.py
│
├── teams/                    # Times multi-agente
│   ├── __init__.py
│   ├── presets.py            # Times pré-configurados
│   └── content_team.py
│
├── tools/                    # 25+ ferramentas
│   ├── __init__.py
│   ├── geo/                  # Mapbox, Spatial
│   ├── database/             # SQL, Analytics
│   ├── devops/               # GitHub, Netlify
│   ├── finance/              # Market, Analysis
│   ├── search/               # Tavily, Wikipedia
│   └── integrations/         # Slack, Notion, etc.
│
├── utils/                    # Utilitários compartilhados
│   ├── logger.py
│   └── helpers.py
│
└── workflows/                # Workflows e pipelines
    ├── __init__.py
    ├── registry.py           # Registro de workflows
    ├── executor.py           # Executor de workflows
    └── hitl.py               # Human-in-the-Loop
```

### Frontend (frontend/)

```
frontend/
├── package.json              # Dependências npm
├── next.config.js            # Configuração Next.js
├── tsconfig.json             # Configuração TypeScript
├── tailwind.config.js        # Configuração Tailwind
├── postcss.config.js
│
├── app/                      # App Router (Next.js 15)
│   ├── layout.tsx            # Layout raiz
│   ├── page.tsx              # Página inicial
│   ├── agents/               # CRUD de agentes
│   │   ├── page.tsx
│   │   └── [id]/
│   ├── teams/                # Gestão de times
│   ├── workflows/            # Workflows
│   ├── flow-studio/          # Visual builder
│   ├── chat/                 # Interface de chat
│   ├── rag/                  # Knowledge base
│   ├── analytics/            # Dashboard
│   └── settings/             # Configurações
│
├── components/               # Componentes React
│   ├── ui/                   # Componentes base (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── agents/               # Componentes de agentes
│   ├── chat/                 # Componentes de chat
│   ├── flow/                 # Componentes do Flow Studio
│   └── shared/               # Componentes compartilhados
│
├── lib/                      # Utilities
│   ├── api.ts                # Cliente API
│   ├── auth.ts               # Helpers de autenticação
│   ├── utils.ts              # Funções utilitárias
│   └── stores/               # Zustand stores
│       ├── auth-store.ts
│       ├── agent-store.ts
│       └── flow-store.ts
│
├── hooks/                    # Custom hooks
│   ├── use-agents.ts
│   ├── use-auth.ts
│   └── use-flow.ts
│
└── public/                   # Assets estáticos
    ├── favicon.ico
    └── images/
```

---

## 5. Módulos do Backend

### Core Modules

#### `src/agents/`

Responsável pela criação e gerenciamento de agentes.

```python
from src.agents import BaseAgent

# Criar agente simples
agent = BaseAgent.create(
    name="Assistente",
    role="Você é um assistente útil",
    instructions=["Responda em português", "Seja conciso"],
    model_provider="groq",  # ou "openai", "anthropic"
    model_id="llama-3.3-70b-versatile"
)

# Executar
response = agent.print_response("Olá!")
```

#### `src/teams/`

Coordenação de múltiplos agentes.

```python
from src.teams.presets import create_content_team

# Time de conteúdo (Researcher → Writer → Reviewer)
team = create_content_team(model_provider="groq")
team.print_response("Escreva um artigo sobre IA")
```

#### `src/workflows/`

Pipelines de execução orquestrada.

```python
# Registrar workflow
workflow = {
    "name": "research-write",
    "steps": [
        {"type": "agent", "name": "Researcher", "input_template": "Pesquise: {{topic}}"},
        {"type": "agent", "name": "Writer", "input_template": "Escreva sobre: {{research}}"}
    ]
}

# Executar
result = await execute_workflow("research-write", {"topic": "Blockchain"})
```

#### `src/rag/`

Retrieval-Augmented Generation.

```python
from src.rag.service import RAGService

rag = RAGService()

# Ingerir documentos
await rag.ingest_texts(collection="docs", texts=["Texto 1", "Texto 2"])

# Consultar
results = await rag.query(collection="docs", query="Qual o tema principal?")
```

#### `src/flow_studio/`

Visual Workflow Builder com 60+ tipos de nós.

**Categorias de Nós:**

| Categoria | Exemplos |
|-----------|----------|
| Agents | LLM Call, Agent, Team |
| Logic | Condition, Loop, Switch |
| Data | Transform, Filter, Aggregate |
| Memory | Store, Retrieve, Summarize |
| Integrations | HTTP, Slack, Email |
| Governance | Approval, Audit, Rate Limit |

### Business Modules

#### `src/billing/`

Sistema de billing com metering e pricing.

```python
# Planos disponíveis
PLANS = {
    "free": {"tokens_per_month": 100_000, "price": 0},
    "pro": {"tokens_per_month": 1_000_000, "price": 29},
    "enterprise": {"tokens_per_month": "unlimited", "price": "custom"}
}
```

#### `src/marketplace/`

Marketplace para publicação de agentes.

```python
# Publicar agente
await marketplace.publish({
    "name": "Finance Analyst",
    "description": "Analista financeiro especializado",
    "category": "finance",
    "price": 0  # Gratuito
})
```

#### `src/enterprise/`

Features enterprise: SSO/SAML, Multi-Region, White-Label.

---

## 6. Frontend (Next.js)

### Estrutura de Páginas

| Rota | Descrição |
|------|-----------|
| `/` | Dashboard principal |
| `/agents` | Lista e CRUD de agentes |
| `/agents/[id]` | Detalhes do agente |
| `/teams` | Gestão de times |
| `/workflows` | Lista de workflows |
| `/flow-studio` | Visual workflow builder |
| `/chat` | Interface de chat |
| `/rag` | Knowledge base |
| `/analytics` | Métricas e custos |
| `/settings` | Configurações |

### State Management (Zustand)

```typescript
// lib/stores/auth-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
)
```

### API Client

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' }
})

// Interceptor para JWT
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
```

---

## 7. API REST

### Autenticação

```http
POST /auth/login
Content-Type: application/json

{"username": "user@example.com"}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Agentes

```http
# Listar agentes
GET /agents

# Criar agente (admin)
POST /agents
{
  "name": "MeuAgente",
  "role": "Assistente",
  "model_provider": "groq"
}

# Executar agente
POST /agents/{name}/run
{
  "prompt": "Olá, como você está?"
}

# Deletar agente (admin)
DELETE /agents/{name}
```

### Times

```http
# Listar times
GET /teams

# Criar time (admin)
POST /teams
{
  "name": "analytics",
  "members": ["Researcher", "Writer"]
}

# Executar time
POST /teams/{name}/run
{
  "prompt": "Analise os dados de vendas"
}
```

### Workflows

```http
# Listar workflows
GET /workflows/registry

# Registrar workflow (admin)
POST /workflows/registry
{
  "name": "meu-workflow",
  "steps": [...]
}

# Executar workflow
POST /workflows/registry/{name}/run
{
  "inputs": {"topic": "IA Generativa"}
}
```

### RAG

```http
# Listar coleções
GET /rag/collections

# Ingerir textos (admin)
POST /rag/ingest-texts
{
  "collection": "docs",
  "texts": ["Texto 1", "Texto 2"]
}

# Consultar
POST /rag/query
{
  "collection": "docs",
  "query_text": "Qual o tema principal?"
}
```

### HITL (Human-in-the-Loop)

```http
# Iniciar sessão
POST /workflows/hitl/start
{
  "topic": "Blockchain",
  "style": "neutro"
}

# Completar sessão
POST /workflows/hitl/complete
{
  "session_id": "uuid",
  "approve": true,
  "feedback": "OK"
}
```

### Health & Admin

```http
GET /health
GET /admin/config (admin)
GET /admin/rate-limit/status (admin)
GET /metrics
```

---

## 8. Sistema de Autenticação

### JWT (JSON Web Tokens)

**Estrutura do Token:**

```json
{
  "sub": "user@example.com",
  "role": "admin",
  "exp": 1702234567,
  "iat": 1702148167
}
```

**Configuração:**

```bash
JWT_SECRET=<openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### RBAC (Role-Based Access Control)

| Papel | Permissões |
|-------|------------|
| `admin` | CRUD completo em todos os recursos |
| `user` | Leitura e execução, sem criar/deletar |

**Uso em Código:**

```python
from src.auth.dependencies import require_admin, get_current_user

@router.post("/agents")
async def create_agent(user: User = Depends(require_admin)):
    # Apenas admin pode criar
    ...

@router.get("/agents")
async def list_agents(user: User = Depends(get_current_user)):
    # Qualquer usuário autenticado
    ...
```

### Rate Limiting

| Grupo | Limite |
|-------|--------|
| Auth | 5 requests/10s |
| RAG Query | 3 requests/10s |
| RAG Ingest | 2 requests/10s |
| Agentes | 5 requests/10s |
| Default | 10 requests/10s |

---

## 9. Configuração e Variáveis de Ambiente

### Obrigatórias

```bash
# Pelo menos uma API key de LLM
GROQ_API_KEY=gsk_...
# ou
OPENAI_API_KEY=sk-...
# ou
ANTHROPIC_API_KEY=sk-ant-...

# Segurança
JWT_SECRET=<openssl rand -hex 32>
```

### Servidor

```bash
AGENTOS_HOST=0.0.0.0
AGENTOS_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=http://localhost:3000,https://agno-multi-agent.netlify.app
```

### Modelo Padrão

```bash
DEFAULT_MODEL_PROVIDER=groq
DEFAULT_MODEL_ID=llama-3.3-70b-versatile
```

### Serviços Opcionais

```bash
# Pesquisa web
TAVILY_API_KEY=tvly-...

# Vector store
CHROMA_HOST=
CHROMA_DB_PATH=data/vectorstore

# Cache
REDIS_URL=redis://localhost:6379

# Observabilidade
SENTRY_DSN=
POSTHOG_API_KEY=
LANGSMITH_API_KEY=
```

### Docker

```bash
NEXT_PUBLIC_API_URL=http://localhost:4000
# Portas: Frontend=4001, Backend=4000, ChromaDB=4002, Ollama=4003, Redis=4004
```

---

## 10. Banco de Dados e Persistência

### SQLite (Default)

```python
# Configuração em src/config/settings.py
DATABASE_URL = "sqlite:///data/databases/agents.db"
```

**Localização dos arquivos:**

```
data/
├── databases/
│   ├── agents.db         # Histórico de conversas
│   └── analytics.db      # Métricas
├── vectorstore/          # ChromaDB
└── knowledge/            # Documentos para RAG
```

### ChromaDB (Vector Store)

```python
from src.rag.service import RAGService

# Inicialização
rag = RAGService(
    chroma_host=os.getenv("CHROMA_HOST"),
    persist_path=os.getenv("CHROMA_DB_PATH", "data/vectorstore")
)
```

### Redis (Cache Opcional)

```python
# Configuração
REDIS_URL=redis://localhost:6379

# Uso
from src.cache import get_cache
cache = get_cache()
await cache.set("key", "value", ttl=3600)
```

---

## 11. Deploy e Infraestrutura

### Backend (Railway)

**Configuração (railway.json):**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python server.py",
    "healthcheckPath": "/health"
  }
}
```

**Deploy:**

```bash
# Via script
.\scripts\auto_deploy_railway.ps1

# Ou via CLI
railway up
```

### Frontend (Netlify)

**Configuração (netlify.toml):**

```toml
[build]
  base = "frontend"
  publish = ".next"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "20"
```

**Deploy:**

```bash
# Via script
.\scripts\auto_deploy_netlify.ps1

# Ou via CLI
cd frontend && netlify deploy --prod
```

### Docker

```bash
# Desenvolvimento
docker compose up -d

# Com RAG
docker compose --profile rag up -d

# Com Cache
docker compose --profile cache up -d

# Todos os serviços
docker compose --profile rag --profile cache --profile local-llm up -d
```

### CI/CD (GitHub Actions)

**Workflows disponíveis:**

| Workflow | Trigger | Ação |
|----------|---------|------|
| `ci.yml` | Push/PR | Lint, Test, Build |
| `deploy-staging.yml` | Push staging | Deploy para staging |
| `deploy-production.yml` | Push main | Deploy para produção |

---

## 12. Integrações Externas

### LLM Providers

| Provider | Modelos Recomendados |
|----------|---------------------|
| **Groq** | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` |
| **Anthropic** | `claude-3-5-sonnet-20241022` |
| **Google** | `gemini-pro` |
| **Ollama** | Modelos locais |

### Ferramentas (Tools)

| Categoria | Ferramentas |
|-----------|-------------|
| **Search** | Tavily, SerpAPI, Exa, Wikipedia |
| **Geo** | Mapbox, IBGE, Spatial |
| **Finance** | YFinance, Market Analysis |
| **DevOps** | GitHub, Netlify, Supabase |
| **Comunicação** | Slack, Discord, Email |
| **Produtividade** | Notion, Google Calendar |

### Observabilidade

| Serviço | Propósito |
|---------|-----------|
| Sentry | Error tracking |
| PostHog | Analytics |
| LangSmith | LLM tracing |

---

## 13. Testes

### Estrutura

```
tests/
├── test_api.py               # Testes de API
├── test_v2_modules.py        # 77 testes módulos V2
├── test_billing_marketplace.py  # 105 testes
├── test_enterprise.py        # 62 testes
├── test_stress.py            # 30+ testes de carga
├── e2e/                      # Smoke tests
└── conftest.py               # Fixtures
```

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Com cobertura
python -m pytest tests/ --cov=src --cov-report=html

# Apenas E2E
python -m pytest tests/e2e/ -v

# Testes específicos
python -m pytest tests/ -k "test_auth" -v
```

### Scripts de Validação

```bash
# Infraestrutura completa
python scripts/fulltest.py

# APIs externas
python scripts/test_apis.py

# Validação pós-deploy
.\scripts\auto_validate.ps1
```

---

## 14. Guia para Merges

### Pré-requisitos para Merge

1. **Python 3.12+** no projeto destino
2. **Node.js 20+** para o frontend
3. Compatibilidade com **FastAPI** (se houver backend existente)

### Módulos Independentes (Fácil Merge)

Estes módulos podem ser copiados diretamente:

| Módulo | Dependências | Notas |
|--------|--------------|-------|
| `src/tools/` | Mínimas | Ferramentas standalone |
| `src/rag/` | ChromaDB | Sistema RAG completo |
| `src/auth/` | PyJWT | Sistema de autenticação |
| `src/config/` | Nenhuma | Sistema de configuração |

### Módulos com Dependências (Requer Adaptação)

| Módulo | Dependências | Adaptação |
|--------|--------------|-----------|
| `src/agents/` | Agno framework | Requer `agno` instalado |
| `src/teams/` | `src/agents/` | Importar junto com agents |
| `src/flow_studio/` | React Flow, WebSocket | Mais complexo |

### Passos para Merge

#### 1. Copiar Módulos Desejados

```bash
# Exemplo: copiar módulo RAG
cp -r agno-platform/src/rag/ meu-projeto/src/
```

#### 2. Instalar Dependências

```bash
# Adicionar ao requirements.txt do destino
chromadb>=1.0.0
sentence-transformers>=2.3.0
```

#### 3. Adaptar Imports

```python
# Antes (relativo ao projeto Agno)
from src.config import get_settings

# Depois (adaptar ao seu projeto)
from meu_projeto.config import get_settings
```

#### 4. Configurar Variáveis de Ambiente

Adicionar variáveis necessárias ao `.env` do projeto destino.

#### 5. Integrar Routers (se aplicável)

```python
# No seu app FastAPI
from src.rag.api import router as rag_router

app.include_router(rag_router, prefix="/rag", tags=["RAG"])
```

### Checklist de Merge

- [ ] Dependências adicionadas ao `requirements.txt`
- [ ] Variáveis de ambiente configuradas
- [ ] Imports adaptados ao namespace do projeto
- [ ] Routers integrados ao FastAPI (se aplicável)
- [ ] Testes do módulo executando
- [ ] Documentação atualizada

---

## Conclusão

Este documento cobre todos os aspectos técnicos da Agno Multi-Agent Platform. Para informações mais específicas, consulte:

- [Arquitetura](../10-arquitetura/) - C4, stack, módulos, fluxos e domínios
- [Contratos de API](../20-contratos-para-integracao/21-api.md) - Endpoints e padrões REST
- [Variáveis de ambiente](../50-operacao/54-env-reference.md) - Referência de env vars
- [ADRs (v2)](../adr_v2/README.md) - Decisões arquiteturais atuais
- [ADRs (legado)](../adr/README.md) - Histórico

---

**Última atualização:** 2025-12-10
**Versão:** 2.1.0

# Mapa do Repositório

> **Última atualização:** 2025-12-16
> **Versão:** 2.2.0

Este documento apresenta a estrutura completa do repositório Agno Multi-Agent Platform, com descrições de cada diretório e arquivo central.

---

## Visão Geral da Estrutura

```
agno-multi-agent-platform/
├── .github/                    # CI/CD e automações GitHub
├── data/                       # Dados persistentes (SQLite, ChromaDB)
├── docs/                       # Documentação completa
├── examples/                   # Exemplos de uso
├── frontend/                   # Next.js 15 + React 18
├── scripts/                    # Scripts de automação
├── src/                        # Backend Python (FastAPI)
├── tests/                      # Testes pytest
├── server.py                   # Entrypoint principal do backend
├── pyproject.toml              # Configuração Python/dependências
├── docker-compose.yml          # Orquestração de containers
└── railway.json                # Deploy Railway
```

---

## Diretório `src/` (Backend)

O backend segue arquitetura **feature-first** com 25+ módulos:

```
src/
├── __init__.py                 # Package root
├── __main__.py                 # CLI entrypoint
│
├── agents/                     # Core: Agentes base e especializados
│   ├── base_agent.py           # Classe BaseAgent (factory de agentes)
│   ├── specialized/            # Agentes especializados por domínio
│   └── registry.py             # Registro global de agentes
│
├── auth/                       # Autenticação e Autorização
│   ├── deps.py                 # Dependencies (get_current_user)
│   ├── jwt.py                  # Criação/validação JWT
│   ├── sso.py                  # SSO (Google, GitHub, Microsoft)
│   └── multitenancy.py         # Multi-tenancy support
│
├── billing/                    # Sistema de Billing
│   ├── models.py               # Planos, subscriptions
│   └── stripe_integration.py   # Integração Stripe
│
├── chat/                       # Módulo de Chat
│   ├── api/                    # Endpoints de chat
│   ├── models/                 # Message, Conversation
│   └── services/               # Lógica de chat
│
├── compliance/                 # LGPD/GDPR Compliance
│   └── gdpr.py                 # Consentimento, erasure, export
│
├── config/                     # Configurações Centralizadas
│   ├── __init__.py             # get_settings()
│   ├── settings.py             # Pydantic Settings
│   └── env_validator.py        # Validação de env vars
│
├── dashboard/                  # Observabilidade & Analytics
│   ├── api/                    # Routers FastAPI
│   │   └── routes.py           # /api/dashboard/*
│   ├── components/             # Componentes de dashboard
│   └── insights/               # Recommendation engine
│
├── domain_studio/              # Domínios Especializados
│   ├── engines/                # RAG engines especializados
│   │   ├── agentic_rag.py      # Autonomous RAG
│   │   ├── graph_rag.py        # Knowledge Graph RAG
│   │   ├── compliance_engine.py# Compliance RAG
│   │   └── multimodal_engine.py# Multimodal RAG
│   ├── domains/                # Implementações por domínio
│   └── registry.py             # Registro de domínios
│
├── enterprise/                 # Features Enterprise
│   ├── sso.py                  # Enterprise SSO
│   └── audit_advanced.py       # Audit trails avançados
│
├── events/                     # Sistema de Eventos
│   └── webhooks.py             # Webhooks outbound
│
├── flow_studio/                # Visual Workflow Builder
│   ├── api/                    # /api/flow-studio/*
│   ├── engine.py               # Workflow engine
│   ├── executor.py             # Executores de nós
│   ├── nodes/                  # Tipos de nós
│   └── ai/                     # NL Designer (AI)
│
├── hitl/                       # Human-in-the-Loop
│   ├── repo.py                 # HITLRepository (SQLAlchemy)
│   └── models.py               # HITLSession, HITLAction
│
├── marketplace/                # Marketplace de Agentes
│   ├── api.py                  # /api/marketplace/*
│   └── registry.py             # Registro de agentes publicados
│
├── mcp/                        # Model Context Protocol
│   └── server.py               # MCP server implementation
│
├── memory/                     # Gestão de Memória
│   ├── manager.py              # MemoryManager
│   └── backends/               # Storage backends
│
├── middleware/                 # Middlewares FastAPI
│   └── rate_limit.py           # Rate limiter com sliding window
│
├── observability/              # Métricas e Tracing
│   ├── health.py               # Health checks (liveness/readiness)
│   ├── logging.py              # Structured JSON logging
│   └── metrics.py              # Prometheus-style metrics
│
├── os/                         # AgentOS Runtime
│   ├── routes/                 # Routers modulares
│   │   ├── __init__.py         # Exports de create_*_router
│   │   ├── auth.py             # /auth/*
│   │   ├── agents.py           # /agents/*
│   │   ├── teams.py            # /teams/*
│   │   ├── workflows.py        # /workflows/*
│   │   ├── rag.py              # /rag/*
│   │   ├── hitl.py             # /hitl/*
│   │   ├── storage.py          # /storage/*
│   │   ├── memory.py           # /memory/*
│   │   ├── admin.py            # /admin/*
│   │   ├── audit.py            # /audit/*
│   │   └── metrics.py          # Metrics middleware
│   └── builder_new.py          # App builder modular
│
├── persistence/                # Persistência de Dados
│   ├── postgres.py             # PostgreSQL adapter
│   └── backup.py               # Sistema de backups
│
├── rag/                        # RAG (Retrieval-Augmented Generation)
│   ├── __init__.py             # Exports públicos
│   ├── service.py              # RagService (ChromaDB)
│   └── chunking.py             # Text chunking strategies
│
├── rules/                      # Rules Engine
│   └── engine.py               # Business rules evaluation
│
├── scheduler/                  # Task Scheduler
│   └── scheduler.py            # Cron-based task scheduling
│
├── sdk/                        # SDK Python
│   └── client.py               # AgnoClient para integração
│
├── storage/                    # File Storage
│   └── service.py              # S3/Local storage abstraction
│
├── studio/                     # Agent Studio
│   └── api.py                  # /api/studio/*
│
├── team_orchestrator/          # Orquestração de Times
│   ├── api/                    # /api/team-orchestrator/*
│   ├── engine.py               # Orchestration engine
│   └── modes/                  # Orchestration modes
│
├── teams/                      # Times Multi-Agente
│   ├── models.py               # Team, TeamMember
│   └── pipelines.py            # Pipelines predefinidas
│
├── tools/                      # 30+ Ferramentas
│   ├── web_search.py           # Tavily search
│   ├── code_executor.py        # Code execution sandbox
│   ├── file_tools.py           # File operations
│   ├── google_calendar.py      # Google Calendar API
│   ├── zapier.py               # Zapier webhooks
│   └── ...                     # Outras ferramentas
│
├── utils/                      # Utilitários
│   └── helpers.py              # Funções auxiliares
│
└── workflows/                  # Workflows e Pipelines
    ├── models.py               # Workflow, WorkflowStep
    ├── registry.py             # Registro de workflows
    └── predefined/             # Workflows predefinidos
```

---

## Diretório `frontend/` (Next.js)

```
frontend/
├── app/                        # App Router (Next.js 15)
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page
│   ├── agents/                 # /agents
│   ├── chat/                   # /chat
│   ├── dashboard/              # /dashboard
│   ├── domain-studio/          # /domain-studio
│   ├── flow-studio/            # /flow-studio
│   ├── marketplace/            # /marketplace
│   ├── settings/               # /settings
│   └── team-orchestrator/      # /team-orchestrator
│
├── components/                 # Componentes React
│   ├── ui/                     # shadcn/ui components
│   ├── agents/                 # Agent-related components
│   ├── chat/                   # Chat components
│   ├── dashboard/              # Dashboard components
│   ├── flow-studio/            # Flow builder components
│   └── shared/                 # Shared components
│
├── hooks/                      # Custom React hooks
│   ├── use-agents.ts           # Agents API hook
│   └── use-chat.ts             # Chat API hook
│
├── lib/                        # Utilities
│   ├── api.ts                  # API client (axios)
│   ├── utils.ts                # Helper functions
│   └── constants.ts            # Constants
│
├── providers/                  # React Context providers
│   └── query-provider.tsx      # TanStack Query provider
│
├── store/                      # Zustand stores
│   └── app-store.ts            # Global app state
│
├── types/                      # TypeScript types
│   └── index.ts                # Shared types
│
├── package.json                # Dependencies
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json               # TypeScript config
└── next.config.mjs             # Next.js config
```

---

## Arquivos de Configuração (Raiz)

| Arquivo | Descrição |
|---------|-----------|
| `server.py` | **Entrypoint principal** - FastAPI app com todos os routers |
| `pyproject.toml` | Configuração Python, dependências, ferramentas (black, ruff, pytest) |
| `requirements.txt` | Dependências pip (gerado do pyproject.toml) |
| `docker-compose.yml` | Orquestração: backend, frontend, ChromaDB |
| `Dockerfile` | Build do backend Python |
| `railway.json` | Configuração de deploy Railway |
| `netlify.toml` | Configuração de deploy Netlify (frontend) |
| `.env.example` | Template de variáveis de ambiente |
| `.pre-commit-config.yaml` | Hooks de pre-commit (black, ruff, etc.) |
| `mkdocs.yml` | Configuração MkDocs para docs |

---

## Diretório `.github/`

```
.github/
├── workflows/
│   ├── ci.yml                  # CI: lint, test, typecheck
│   ├── deploy-staging.yml      # Deploy staging (Railway + Netlify)
│   ├── deploy-production.yml   # Deploy production
│   └── netlify-deploy.yml      # Deploy frontend Netlify
└── dependabot.yml              # Dependabot config
```

---

## Diretório `tests/`

```
tests/
├── conftest.py                 # Fixtures pytest
├── test_api.py                 # Testes de API (17 testes)
├── test_modules.py             # Testes de módulos (16 testes)
└── ...                         # Outros testes
```

---

## Diretório `data/`

```
data/
├── chroma/                     # ChromaDB vector store
├── agents.db                   # SQLite - agentes persistidos
├── hitl.db                     # SQLite - HITL sessions
└── backups/                    # Backups automáticos
```

---

## Variáveis de Ambiente Críticas

Ver arquivo `.env.example` para lista completa. As principais são:

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GROQ_API_KEY` | Sim* | API key Groq (LLM) |
| `OPENAI_API_KEY` | Sim* | API key OpenAI |
| `JWT_SECRET` | Sim | Secret para tokens JWT |
| `ADMIN_USERS` | Sim | Lista de admins (emails) |
| `DATABASE_URL` | Não | PostgreSQL (default: SQLite) |
| `CHROMA_HOST` | Não | ChromaDB host (default: local) |

*Pelo menos uma API key de LLM é obrigatória.

---

## Referências Cruzadas

- **Arquitetura:** `docs/10-arquitetura/`
- **Contratos API:** `docs/20-contratos-para-integracao/`
- **ADRs:** `docs/adr_v2/`
- **Setup local:** `docs/50-operacao/50-setup-local.md`

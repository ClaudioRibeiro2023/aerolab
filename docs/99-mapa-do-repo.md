# 🗺️ Mapa do Repositório

> Documento gerado automaticamente. Última atualização: Dezembro 2024

Este documento mapeia a estrutura completa do repositório **AeroLab**, identificando arquivos centrais, dependências reais e pontos de integração.

---

## Estrutura de Diretórios

```
aerolab/
│
├── 📁 apps/                           # Aplicações deployáveis
│   └── web/                           # Frontend React SPA
│       ├── src/
│       │   ├── components/            # Componentes React específicos da app
│       │   ├── pages/                 # Páginas/rotas da aplicação
│       │   ├── modules/               # Módulos de features (ETL, Users, etc.)
│       │   ├── hooks/                 # Custom hooks (useImageOptimization, etc.)
│       │   ├── lib/                   # Utilitários (cdn.ts, sentry.ts)
│       │   └── config/                # Configurações da app
│       ├── e2e/                       # Testes E2E (Playwright)
│       ├── package.json               # Deps: react@18, vite@5, tailwindcss@3
│       ├── vite.config.ts             # Config do Vite
│       ├── tailwind.config.js         # Config do Tailwind
│       └── playwright.config.ts       # Config do Playwright
│
├── 📁 packages/                       # Packages compartilhados (workspace)
│   │
│   ├── shared/                        # Lógica compartilhada
│   │   └── src/
│   │       ├── auth/                  # 🔑 AuthContext, oidcConfig, types
│   │       │   ├── AuthContext.tsx    # Provider de autenticação
│   │       │   ├── oidcConfig.ts      # Config OIDC/Keycloak
│   │       │   └── types.ts           # UserRole, AuthUser, AuthContextType
│   │       ├── api/                   # API client (axios)
│   │       ├── cache/                 # React Query config
│   │       └── utils/                 # Helpers, formatters, logger
│   │
│   ├── design-system/                 # Componentes UI reutilizáveis
│   │   └── src/
│   │       ├── components/            # Button, Input, Modal, Card, etc.
│   │       ├── tokens/                # Design tokens (cores, spacing)
│   │       └── styles/                # Estilos base
│   │
│   └── types/                         # Tipos TypeScript compartilhados
│       └── src/
│           ├── api.ts                 # Tipos de responses da API
│           ├── auth.ts                # Tipos de autenticação
│           └── common.ts              # Tipos genéricos
│
├── 📁 api-template/                   # Backend FastAPI
│   ├── app/
│   │   ├── main.py                    # 🎯 Entry point da API
│   │   ├── rate_limit.py              # Rate limiting (slowapi)
│   │   ├── csrf.py                    # CSRF protection
│   │   ├── session.py                 # Redis session store
│   │   ├── security.py                # CSP headers
│   │   ├── audit.py                   # Audit logging
│   │   ├── analytics.py               # Event tracking
│   │   ├── rls.py                     # Row-level security
│   │   ├── tenant.py                  # Multi-tenancy
│   │   ├── websocket.py               # WebSocket support
│   │   ├── middleware.py              # Custom middlewares
│   │   └── logging_config.py          # Structlog config
│   ├── alembic/                       # Database migrations
│   │   ├── env.py
│   │   └── versions/                  # Migration files
│   ├── alembic.ini                    # Alembic config
│   ├── requirements.txt               # Deps Python
│   └── Dockerfile                     # Container image
│
├── 📁 infra/                          # Infraestrutura
│   ├── docker-compose.yml             # 🐳 Stack principal (db, redis, keycloak, api, frontend)
│   ├── docker-compose.local.yml       # Override para desenvolvimento
│   ├── docker-compose.prod.yml        # Override para produção
│   ├── .env.example                   # Template de variáveis
│   ├── .env.production.example        # Template produção
│   ├── keycloak/                      # Config Keycloak (realm export)
│   ├── k8s/                           # Kubernetes manifests
│   │   ├── deployment.yaml            # Deployments, Services, Ingress
│   │   └── blue-green.yaml            # Blue-green deployment
│   └── monitoring/                    # Observability (Prometheus, Grafana)
│
├── 📁 docs/                           # Documentação
│   ├── INDEX.md                       # Índice da documentação
│   ├── ARCHITECTURE.md                # Arquitetura geral
│   ├── GETTING_STARTED.md             # Guia de início rápido
│   ├── DEPLOY.md                      # Instruções de deploy
│   ├── DESIGN_SYSTEM.md               # Design system
│   ├── ROLES_E_ACESSO.md              # RBAC e permissões
│   ├── TROUBLESHOOTING.md             # Resolução de problemas
│   └── adr/                           # Architecture Decision Records
│
├── 📁 scripts/                        # Scripts de automação
│   └── blue-green-deploy.ps1          # Script de deploy blue-green
│
├── 📁 .github/                        # GitHub config
│   └── workflows/                     # CI/CD pipelines
│
├── 📄 package.json                    # 🎯 Root package (workspaces)
├── 📄 pnpm-workspace.yaml             # Workspace config
├── 📄 pnpm-lock.yaml                  # Lockfile
├── 📄 tsconfig.base.json              # TypeScript base config
├── 📄 .eslintrc.cjs                   # ESLint config
├── 📄 .prettierrc                     # Prettier config
├── 📄 commitlint.config.js            # Commit lint config
├── 📄 README.md                       # Documentação principal
├── 📄 CONTRIBUTING.md                 # Guia de contribuição
└── 📄 todo.md                         # Roadmap/tarefas
```

---

## Arquivos Centrais (Source of Truth)

### Configuração do Projeto

| Arquivo               | Propósito                          | Versão/Info                             |
| --------------------- | ---------------------------------- | --------------------------------------- |
| `package.json`        | Root workspace                     | `@template/platform@1.0.0`, pnpm@9.15.9 |
| `pnpm-workspace.yaml` | Workspaces: `apps/*`, `packages/*` | -                                       |
| `tsconfig.base.json`  | TypeScript base config             | TS 5.3.3                                |

### Frontend (apps/web)

| Arquivo                         | Propósito     | Versão/Info                           |
| ------------------------------- | ------------- | ------------------------------------- |
| `apps/web/package.json`         | Deps frontend | React 18.2, Vite 5.0, TailwindCSS 3.3 |
| `apps/web/vite.config.ts`       | Build config  | Port 13000 (dev)                      |
| `apps/web/tailwind.config.js`   | Design tokens | -                                     |
| `apps/web/playwright.config.ts` | E2E tests     | Chromium + Firefox                    |

### Backend (api-template)

| Arquivo                         | Propósito         | Versão/Info                   |
| ------------------------------- | ----------------- | ----------------------------- |
| `api-template/requirements.txt` | Deps Python       | FastAPI ≥0.104, Pydantic ≥2.5 |
| `api-template/app/main.py`      | API entry point   | v0.1.0, port 8000             |
| `api-template/alembic.ini`      | Migrations config | -                             |

### Autenticação

| Arquivo                                    | Propósito     | Descrição                |
| ------------------------------------------ | ------------- | ------------------------ |
| `packages/shared/src/auth/oidcConfig.ts`   | Config OIDC   | Keycloak endpoints, PKCE |
| `packages/shared/src/auth/AuthContext.tsx` | Auth provider | Login, logout, roles     |
| `packages/shared/src/auth/types.ts`        | Tipos auth    | UserRole, AuthUser       |

### Infraestrutura

| Arquivo                     | Propósito     | Serviços                            |
| --------------------------- | ------------- | ----------------------------------- |
| `infra/docker-compose.yml`  | Stack base    | PostgreSQL 15, Redis 7, Keycloak 23 |
| `infra/.env.example`        | Variáveis     | DB, Redis, Keycloak, API, Frontend  |
| `infra/k8s/deployment.yaml` | K8s manifests | Deployments, Services, HPA          |

---

## Dependências Reais (Confirmadas)

### Frontend (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.12.2",
    "oidc-client-ts": "^2.4.0",
    "axios": "^1.6.2",
    "lucide-react": "^0.294.0",
    "tailwind-merge": "^2.1.0",
    "clsx": "^2.0.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "vite": "^5.0.8",
    "typescript": "5.3.3",
    "@playwright/test": "^1.56.1",
    "vitest": "^4.0.15",
    "tailwindcss": "^3.3.6"
  }
}
```

### Backend (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-jose[cryptography]>=3.3.0
httpx>=0.25.0
redis>=5.0.0
asyncpg>=0.29.0
structlog>=24.1.0
slowapi>=0.1.9
alembic>=1.13.0
sqlalchemy>=2.0.0
itsdangerous>=2.1.0
```

---

## Pontos de Integração

### URLs e Endpoints

| Serviço    | URL Local              | URL Docker           |
| ---------- | ---------------------- | -------------------- |
| Frontend   | http://localhost:13000 | http://frontend:80   |
| API        | http://localhost:8000  | http://api:8000      |
| Keycloak   | http://localhost:8080  | http://keycloak:8080 |
| PostgreSQL | localhost:5432         | db:5432              |
| Redis      | localhost:6379         | redis:6379           |

### Endpoints da API

| Endpoint        | Método | Propósito             |
| --------------- | ------ | --------------------- |
| `/`             | GET    | Health check básico   |
| `/health`       | GET    | Health check          |
| `/health/live`  | GET    | Liveness probe (K8s)  |
| `/health/ready` | GET    | Readiness probe (K8s) |
| `/docs`         | GET    | Swagger UI            |
| `/redoc`        | GET    | ReDoc                 |
| `/api/me`       | GET    | Usuário atual         |
| `/api/config`   | GET    | Config do frontend    |

### Endpoints OIDC (Keycloak)

| Endpoint      | URL                                                              |
| ------------- | ---------------------------------------------------------------- |
| Authorization | `{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth`     |
| Token         | `{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token`    |
| UserInfo      | `{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/userinfo` |
| Logout        | `{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/logout`   |
| JWKS          | `{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs`    |

---

## Variáveis de Ambiente

### Frontend (Vite)

| Variável                  | Default                   | Descrição              |
| ------------------------- | ------------------------- | ---------------------- |
| `VITE_API_URL`            | http://localhost:8000/api | URL da API             |
| `VITE_KEYCLOAK_URL`       | http://localhost:8080     | URL do Keycloak        |
| `VITE_KEYCLOAK_REALM`     | template                  | Realm do Keycloak      |
| `VITE_KEYCLOAK_CLIENT_ID` | template-web              | Client ID OIDC         |
| `VITE_DEMO_MODE`          | false                     | Bypass de autenticação |
| `VITE_APP_URL`            | window.location.origin    | URL da aplicação       |

### Backend (Python)

| Variável             | Default     | Descrição                    |
| -------------------- | ----------- | ---------------------------- |
| `DATABASE_URL`       | -           | PostgreSQL connection string |
| `REDIS_URL`          | -           | Redis connection string      |
| `API_SECRET_KEY`     | -           | Chave secreta da API         |
| `ENVIRONMENT`        | development | Ambiente atual               |
| `RATE_LIMIT_DEFAULT` | 100/minute  | Rate limit padrão            |
| `RATE_LIMIT_AUTH`    | 10/minute   | Rate limit auth              |
| `RATE_LIMIT_API`     | 60/minute   | Rate limit API               |

---

## Scripts Disponíveis

### Root (pnpm)

```bash
pnpm dev          # Inicia frontend em localhost:13000
pnpm build        # Build de produção
pnpm lint         # ESLint
pnpm typecheck    # TypeScript check
pnpm test         # Testes unitários (Vitest)
pnpm test:e2e     # Testes E2E (Playwright)
pnpm clean        # Remove node_modules e dist
```

### API (Python)

```bash
cd api-template
uvicorn app.main:app --reload --port 8000    # Dev server
alembic upgrade head                          # Run migrations
alembic revision --autogenerate -m "..."      # Create migration
```

### Docker

```bash
cd infra
docker-compose up -d                          # Start all services
docker-compose -f docker-compose.prod.yml up  # Production mode
docker-compose logs -f api                    # View API logs
```

---

## Testes

### Cobertura Atual

| Tipo               | Quantidade | Localização                   |
| ------------------ | ---------- | ----------------------------- |
| Unitários (Vitest) | 125        | `packages/*/src/**/*.test.ts` |
| E2E (Playwright)   | 96         | `apps/web/e2e/*.spec.ts`      |

### Categorias E2E

- `accessibility.spec.ts` - Landmarks, ARIA, contraste
- `forms.spec.ts` - Validação, UX de formulários
- `navigation.spec.ts` - Rotas, sidebar, deep links
- `performance.spec.ts` - LCP, cache, lazy loading
- `template.spec.ts` - Layout, responsividade, auth demo

---

_Documento gerado para servir como referência de integração._

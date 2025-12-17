# 🚀 AeroLab

> **Versão:** 1.0.0 | **Última atualização:** Dezembro 2024

Plataforma corporativa moderna para aplicações web com React, TypeScript, TailwindCSS e autenticação via Keycloak.

## ✨ Características

### Core

- **Monorepo** com pnpm 9.x workspaces
- **React 18** + TypeScript 5.3 + Vite 5
- **TailwindCSS 3** para estilização
- **Autenticação OIDC** com Keycloak (bypass para modo demo/dev)
- **Sistema de Roles** (ADMIN, GESTOR, OPERADOR, VIEWER)
- **Design System** compartilhado com Storybook
- **Docker** pronto para produção
- **Playwright** para testes E2E (96 testes)
- **Dark Mode** suportado

### Produção & Escalabilidade (Fase 10)

- **Rate Limiting** com slowapi
- **CSRF Protection** com double-submit cookie
- **Redis Session Store** para produção
- **Database Migrations** com Alembic
- **Row-Level Security** para multi-tenancy
- **Kubernetes Manifests** com HPA e blue-green deploy
- **Analytics** privacy-first com event tracking
- **CDN Integration** com cache otimizado

## 📁 Estrutura do Projeto

```
├── apps/
│   └── web/                    # Aplicação frontend principal (React)
│       ├── src/
│       │   ├── components/     # Componentes React
│       │   ├── pages/          # Páginas da aplicação
│       │   ├── modules/        # Módulos de funcionalidades
│       │   ├── hooks/          # Custom hooks
│       │   └── lib/            # Utilitários (CDN, etc.)
│       └── e2e/                # Testes E2E (Playwright)
│
├── packages/
│   ├── design-system/          # Componentes UI + Storybook
│   ├── shared/                 # Auth, API client, utils, logger
│   └── types/                  # Tipos TypeScript compartilhados
│
├── api-template/               # API Backend (FastAPI)
│   ├── app/                    # Código da aplicação
│   │   ├── rate_limit.py       # Rate limiting
│   │   ├── csrf.py             # CSRF protection
│   │   ├── session.py          # Redis sessions
│   │   ├── security.py         # CSP headers
│   │   ├── audit.py            # Audit logging
│   │   ├── analytics.py        # Event tracking
│   │   ├── rls.py              # Row-level security
│   │   └── tenant.py           # Multi-tenancy
│   └── alembic/                # Database migrations
│
├── infra/
│   ├── docker-compose.yml      # Stack Docker (Postgres, Redis, Keycloak)
│   ├── keycloak/               # Keycloak config
│   └── k8s/                    # Kubernetes manifests
│
├── docs/                       # Documentação completa
├── scripts/                    # Scripts de automação
└── .github/workflows/          # CI/CD (GitHub Actions)
```

## 🚀 Início Rápido

### Pré-requisitos

- Node.js >= 18
- pnpm >= 8
- Docker (opcional, para stack completa)

### Instalação

```bash
# Clone o template
git clone <repo-url> meu-projeto
cd meu-projeto

# Instale dependências
pnpm install

# Inicie o dev server (modo demo - sem auth)
pnpm dev
```

### Modo Demo (Desenvolvimento)

Para desenvolver sem depender do Keycloak:

```bash
# Crie um arquivo .env na pasta apps/web
echo "VITE_DEMO_MODE=true" > apps/web/.env

# Inicie o dev server
pnpm dev
```

### Stack Completa com Docker

```bash
# Suba todos os serviços
docker compose -f infra/docker-compose.yml up -d

# Acesse:
# - Frontend: http://localhost:13000
# - Keycloak: http://localhost:8080 (admin/admin)
# - API: http://localhost:8000
```

## 🔐 Autenticação e Roles

O sistema suporta 4 roles padrão:

| Role     | Descrição                    |
| -------- | ---------------------------- |
| ADMIN    | Acesso total ao sistema      |
| GESTOR   | Gestão de módulos e usuários |
| OPERADOR | Operações do dia-a-dia       |
| VIEWER   | Apenas visualização          |

### Protegendo Rotas

```tsx
// Exige qualquer uma das roles
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']}>
  <MinhaPage />
</ProtectedRoute>

// Exige TODAS as roles
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']} requireAll>
  <MinhaPage />
</ProtectedRoute>
```

### Verificando Roles no Código

```tsx
const { hasRole, hasAnyRole } = useAuth()

if (hasRole('ADMIN')) {
  // Apenas ADMIN
}

if (hasAnyRole(['ADMIN', 'GESTOR'])) {
  // ADMIN ou GESTOR
}
```

## 📦 Criando Novos Módulos

1. Crie a pasta do módulo em `src/modules/`:

```
src/modules/meu-modulo/
├── components/
├── hooks/
├── services/
├── types.ts
└── index.ts
```

2. Adicione a rota em `App.tsx`:

```tsx
<Route path="/meu-modulo/*" element={<MeuModuloRoutes />} />
```

3. Adicione o item no menu em `AppSidebar.tsx`:

```tsx
const navItems = [
  // ...
  { label: 'Meu Módulo', path: '/meu-modulo', icon: <Icon /> },
]
```

## 🎨 Personalização

### Cores (TailwindCSS)

Edite as variáveis CSS em `src/styles/index.css`:

```css
:root {
  --brand-primary: #0087a8;
  --brand-secondary: #005f73;
  --brand-accent: #94d2bd;
}
```

### Logo e Nome

Edite `AppSidebar.tsx` e `LoginPage.tsx` para alterar logo e nome.

## 🧪 Testes

```bash
# Testes E2E
pnpm test:e2e

# Com interface visual
pnpm test:e2e:ui
```

## 📝 Scripts Disponíveis

| Comando          | Descrição                                   |
| ---------------- | ------------------------------------------- |
| `pnpm dev`       | Inicia dev server em http://localhost:13000 |
| `pnpm build`     | Build de produção (packages + app)          |
| `pnpm lint`      | Executa ESLint                              |
| `pnpm lint:fix`  | Corrige problemas de lint                   |
| `pnpm format`    | Formata código com Prettier                 |
| `pnpm typecheck` | Verifica tipos TypeScript                   |
| `pnpm test`      | Testes unitários (Vitest)                   |
| `pnpm test:e2e`  | Testes E2E (Playwright)                     |
| `pnpm clean`     | Limpa node_modules e dist                   |

## 📖 Documentação

Toda a documentação está em [`docs/`](./docs/INDEX.md):

| Documento                                                         | Descrição                            |
| ----------------------------------------------------------------- | ------------------------------------ |
| [INDEX.md](./docs/INDEX.md)                                       | **Portal principal** - índice mestre |
| [operacao/setup-local.md](./docs/operacao/setup-local.md)         | Setup do ambiente de desenvolvimento |
| [operacao/deploy.md](./docs/operacao/deploy.md)                   | Deploy local, staging e produção     |
| [arquitetura/c4-container.md](./docs/arquitetura/c4-container.md) | Arquitetura (diagramas C4)           |
| [seguranca/rbac.md](./docs/seguranca/rbac.md)                     | Sistema de permissões (RBAC)         |
| [DESIGN_SYSTEM.md](./docs/DESIGN_SYSTEM.md)                       | Componentes e tokens                 |
| [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)                   | Resolução de problemas               |

## 🛠️ Tecnologias

| Camada          | Tecnologia     | Versão |
| --------------- | -------------- | ------ |
| Frontend        | React          | 18.x   |
| Linguagem       | TypeScript     | 5.3.x  |
| Build           | Vite           | 5.x    |
| Estilização     | TailwindCSS    | 3.x    |
| Estado          | TanStack Query | 5.x    |
| Auth            | oidc-client-ts | 2.x    |
| API             | FastAPI        | 0.104+ |
| Testes E2E      | Playwright     | 1.x    |
| Package Manager | pnpm           | 9.x    |

## 📄 Licença

MIT

---

_Para contribuir, veja [CONTRIBUTING.md](./CONTRIBUTING.md)_

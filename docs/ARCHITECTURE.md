# 🏗️ Arquitetura do Template Platform

Este documento descreve a arquitetura, decisões técnicas e convenções do projeto.

---

## 1. Visão Geral

O **Template Platform** é um monorepo para aplicações web corporativas, composto por:

```
├── apps/
│   └── web/                 # Aplicação React principal
├── packages/
│   ├── design-system/       # Componentes UI compartilhados
│   ├── shared/              # Lógica compartilhada (auth, api, utils)
│   └── types/               # Tipos TypeScript compartilhados
├── api-template/            # Template de API FastAPI
├── infra/                   # Docker, Keycloak configs
└── docs/                    # Documentação
```

---

## 2. Stack Tecnológica

| Camada                     | Tecnologia      | Versão             |
| -------------------------- | --------------- | ------------------ |
| **Frontend**               | React           | 18.x               |
| **Linguagem**              | TypeScript      | 5.3.x              |
| **Build**                  | Vite            | 5.x                |
| **Estilização**            | TailwindCSS     | 3.x                |
| **Roteamento**             | React Router    | 6.x                |
| **Estado Servidor**        | TanStack Query  | 5.x                |
| **Autenticação**           | OIDC (Keycloak) | oidc-client-ts 2.x |
| **API**                    | FastAPI         | 0.104+             |
| **Gerenciador de Pacotes** | pnpm            | 9.x                |
| **Testes E2E**             | Playwright      | 1.x                |

---

## 3. Estrutura de Pastas

### 3.1 Aplicação Web (`apps/web/`)

```
apps/web/
├── src/
│   ├── components/          # Componentes React
│   │   ├── auth/            # Componentes de autenticação
│   │   ├── common/          # Componentes compartilhados
│   │   └── layout/          # Layout (Header, Sidebar, Footer)
│   ├── hooks/               # Hooks customizados da aplicação
│   ├── modules/             # Módulos de funcionalidades (feature-based)
│   ├── navigation/          # Configuração de navegação/menu
│   ├── pages/               # Páginas da aplicação
│   ├── services/            # Serviços de API
│   ├── styles/              # Estilos globais (CSS)
│   ├── App.tsx              # Componente raiz com rotas
│   └── main.tsx             # Entry point
├── e2e/                     # Testes E2E (Playwright)
├── public/                  # Assets estáticos
└── index.html               # HTML principal
```

### 3.2 Packages Compartilhados

#### `@template/shared`

Lógica compartilhada entre projetos:

- **auth/** — AuthContext, useAuth, oidcConfig, tipos
- **api/** — Cliente HTTP com interceptors
- **utils/** — Formatters, helpers

#### `@template/design-system`

Componentes UI reutilizáveis:

- **components/** — Botões, Cards, Inputs, etc.
- **layout/** — Containers, Grids
- **navigation/** — Menus, Breadcrumbs
- **filters/** — Componentes de filtro

#### `@template/types`

Tipos TypeScript compartilhados (use quando não há lógica associada).

---

## 4. Decisões Arquiteturais (ADRs)

### ADR-001: Autenticação Centralizada

**Contexto:** O projeto tinha AuthContext duplicado em `apps/web` e `packages/shared`.

**Decisão:** Centralizar em `packages/shared/src/auth/`.

**Consequências:**

- ✅ Single source of truth para autenticação
- ✅ Facilita manutenção e testes
- ✅ Permite reutilização em outras apps do monorepo

**Uso:**

```typescript
import { AuthProvider, useAuth, type Role } from '@template/shared'
```

---

### ADR-002: Configuração OIDC Centralizada

**Contexto:** Configuração de Keycloak/OIDC estava em dois arquivos diferentes.

**Decisão:** Manter apenas `packages/shared/src/auth/oidcConfig.ts`.

**Consequências:**

- ✅ Configuração única para todo o projeto
- ✅ Facilita mudança de provider OIDC
- ✅ Variáveis de ambiente centralizadas

---

### ADR-003: Estrutura de Módulos Feature-Based

**Contexto:** Necessidade de organizar código por funcionalidade ao invés de tipo técnico.

**Decisão:** Usar estrutura modular em `apps/web/src/modules/`:

```
modules/[nome]/
├── components/      # Componentes do módulo
├── hooks/           # Hooks do módulo
├── services/        # API calls do módulo
├── types.ts         # Tipos do módulo
├── routes.tsx       # Rotas do módulo
└── index.ts         # Barrel export
```

**Consequências:**

- ✅ Código relacionado fica junto
- ✅ Facilita encontrar arquivos
- ✅ Módulos podem ser extraídos para packages separados

---

## 5. Fluxo de Autenticação

### 5.1 Produção (Keycloak)

```
┌─────────┐     ┌───────────┐     ┌──────────┐
│  User   │────>│  App Web  │────>│ Keycloak │
└─────────┘     └───────────┘     └──────────┘
                     │                  │
                     │  redirect        │
                     │<─────────────────│
                     │                  │
                     │  code exchange   │
                     │─────────────────>│
                     │                  │
                     │  tokens (JWT)    │
                     │<─────────────────│
                     │                  │
                     ▼                  │
               AuthContext              │
               (user, roles)            │
```

### 5.2 Desenvolvimento (Demo Mode)

Com `VITE_DEMO_MODE=true`:

- Bypass completo de autenticação
- Usuário mock: `Demo User`
- Todas as roles disponíveis: `ADMIN`, `GESTOR`, `OPERADOR`, `VIEWER`

### 5.3 Testes E2E

Com `MODE=e2e`:

- Bypass de autenticação
- Roles configuráveis via query param: `?roles=ADMIN,GESTOR`
- Ou via localStorage: `e2e-roles`

---

## 6. Sistema de Roles

### Roles Disponíveis

| Role       | Descrição     | Acesso                    |
| ---------- | ------------- | ------------------------- |
| `ADMIN`    | Administrador | Acesso total              |
| `GESTOR`   | Gestor        | Configurações, relatórios |
| `OPERADOR` | Operador      | Operações do dia-a-dia    |
| `VIEWER`   | Visualizador  | Apenas leitura            |

### Uso no Código

```typescript
// Verificar role única
const { hasRole } = useAuth()
if (hasRole('ADMIN')) {
  /* ... */
}

// Verificar múltiplas roles (todas necessárias)
if (hasRole(['ADMIN', 'GESTOR'])) {
  /* ... */
}

// Verificar se tem alguma das roles
const { hasAnyRole } = useAuth()
if (hasAnyRole(['ADMIN', 'GESTOR'])) {
  /* ... */
}
```

### Protegendo Rotas

```tsx
<ProtectedRoute requiredRoles={['ADMIN']}>
  <AdminPage />
</ProtectedRoute>

// Exige TODAS as roles
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']} requireAll>
  <SpecialPage />
</ProtectedRoute>
```

---

## 7. Convenções de Código

### 7.1 Nomenclatura

| Tipo        | Convenção                | Exemplo                |
| ----------- | ------------------------ | ---------------------- |
| Componentes | PascalCase               | `UserCard.tsx`         |
| Hooks       | camelCase com `use`      | `useDebounce.ts`       |
| Services    | camelCase com `.service` | `users.service.ts`     |
| Types       | PascalCase               | `UserRole`, `AuthUser` |
| Constantes  | SCREAMING_SNAKE          | `ALL_ROLES`, `API_URL` |

### 7.2 Imports

Ordem preferencial:

1. React/libs externas
2. `@template/*` packages
3. `@/` aliases locais
4. Imports relativos

```typescript
// 1. External
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

// 2. Workspace packages
import { useAuth, type Role } from '@template/shared'
import { Button } from '@template/design-system'

// 3. Local aliases
import { usersService } from '@/services/users.service'

// 4. Relative
import { UserCard } from './UserCard'
```

### 7.3 Exports

Preferir **named exports** sobre default exports:

```typescript
// ✅ Preferido
export function UserCard() {}
export { UserCard } from './UserCard'

// ❌ Evitar
export default function UserCard() {}
```

---

## 8. Variáveis de Ambiente

### Frontend (`apps/web/.env`)

```bash
# API
VITE_API_URL=http://localhost:8000/api

# Keycloak/OIDC
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=template
VITE_KEYCLOAK_CLIENT_ID=template-web

# App
VITE_APP_URL=http://localhost:13000

# Development
VITE_DEMO_MODE=false
```

### Acesso no código

```typescript
const apiUrl = import.meta.env.VITE_API_URL
const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'
```

---

## 9. Scripts Disponíveis

### Raiz do projeto

```bash
pnpm dev          # Inicia dev server
pnpm build        # Build de produção
pnpm typecheck    # Verifica tipos
pnpm lint         # Executa linter
pnpm test:e2e     # Testes E2E
pnpm clean        # Limpa node_modules e dist
```

### Por package

```bash
pnpm --filter @template/web dev
pnpm --filter @template/shared build
pnpm -C apps/web test:e2e
```

---

## 10. Próximos Passos (Roadmap)

Consulte o arquivo `todo.md` para o plano detalhado de melhorias.

**Fases principais:**

1. ✅ Fase 0 — Fundamentos (concluída)
2. ⏳ Fase 1 — Arquitetura & Organização
3. ⏳ Fase 2 — Qualidade & Testes
4. ⏳ Fase 3 — Infraestrutura & CI/CD
5. ⏳ Fase 4 — Observabilidade
6. ⏳ Fase 5 — DX & Governança

---

_Última atualização: Dezembro/2024_

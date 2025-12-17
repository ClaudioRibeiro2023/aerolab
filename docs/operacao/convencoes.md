# Convenções de Código

> Padrões e convenções para desenvolvimento no Template Platform.

**Fonte:** Extraído de `ARCHITECTURE.md`

---

## 1. Nomenclatura

| Tipo        | Convenção                | Exemplo                |
| ----------- | ------------------------ | ---------------------- |
| Componentes | PascalCase               | `UserCard.tsx`         |
| Hooks       | camelCase com `use`      | `useDebounce.ts`       |
| Services    | camelCase com `.service` | `users.service.ts`     |
| Types       | PascalCase               | `UserRole`, `AuthUser` |
| Constantes  | SCREAMING_SNAKE          | `ALL_ROLES`, `API_URL` |

---

## 2. Imports

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

---

## 3. Exports

Preferir **named exports** sobre default exports:

```typescript
// ✅ Preferido
export function UserCard() {}
export { UserCard } from './UserCard'

// ❌ Evitar
export default function UserCard() {}
```

---

## 4. Estrutura de Módulos

Estrutura padrão para módulos em `apps/web/src/modules/`:

```
modules/[nome]/
├── components/      # Componentes do módulo
├── hooks/           # Hooks do módulo
├── services/        # API calls do módulo
├── types.ts         # Tipos do módulo
├── routes.tsx       # Rotas do módulo
└── index.ts         # Barrel export
```

---

## 5. Scripts Disponíveis

### Raiz do projeto

```bash
pnpm dev          # Inicia dev server (localhost:13000)
pnpm build        # Build de produção
pnpm typecheck    # Verifica tipos
pnpm lint         # Executa linter
pnpm lint:fix     # Lint + fix automático
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

## 6. Variáveis de Ambiente

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

**Ver também:**

- [Setup Local](./setup-local.md)
- [Variáveis de Ambiente](./variaveis-ambiente.md)

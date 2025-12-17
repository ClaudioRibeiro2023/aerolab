# Guia de Contribuição

Bem-vindo ao Template Platform! Este guia ajudará você a configurar o ambiente e contribuir com o projeto.

## Índice

- [Configuração do Ambiente](#configuração-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Criar um Módulo](#como-criar-um-módulo)
- [Convenções de Código](#convenções-de-código)
- [Processo de Pull Request](#processo-de-pull-request)
- [Commits](#commits)

---

## Configuração do Ambiente

### Pré-requisitos

- **Node.js** 20.x ou superior
- **pnpm** 9.x (`npm install -g pnpm`)
- **Docker** e **Docker Compose** (para infra local)
- **Git** 2.x ou superior

### Setup Inicial

```bash
# 1. Clone o repositório
git clone <repo-url>
cd template-platform

# 2. Instale as dependências
pnpm install

# 3. Configure as variáveis de ambiente
cp apps/web/.env.example apps/web/.env

# 4. (Opcional) Suba a infraestrutura
cd infra && docker-compose up -d

# 5. Inicie o dev server
pnpm dev
```

### Comandos Úteis

| Comando          | Descrição                   |
| ---------------- | --------------------------- |
| `pnpm dev`       | Inicia o dev server         |
| `pnpm build`     | Build de produção           |
| `pnpm lint`      | Executa ESLint              |
| `pnpm lint:fix`  | Corrige problemas de lint   |
| `pnpm format`    | Formata código com Prettier |
| `pnpm typecheck` | Verifica tipos TypeScript   |
| `pnpm test`      | Executa testes unitários    |

---

## Estrutura do Projeto

```
├── apps/
│   └── web/                 # Aplicação React principal
│       ├── src/
│       │   ├── components/  # Componentes reutilizáveis
│       │   ├── hooks/       # Custom hooks
│       │   ├── modules/     # Módulos de feature
│       │   ├── pages/       # Páginas da aplicação
│       │   └── routes/      # Configuração de rotas
│       └── ...
├── packages/
│   ├── shared/              # Código compartilhado (auth, api, utils)
│   ├── types/               # Tipos TypeScript compartilhados
│   └── design-system/       # Componentes de UI
├── api-template/            # API FastAPI
├── infra/                   # Docker e configurações de infra
└── docs/                    # Documentação
```

---

## Como Criar um Módulo

Os módulos ficam em `apps/web/src/modules/` e seguem uma estrutura padronizada:

### Estrutura de um Módulo

```
modules/
└── meu-modulo/
    ├── index.ts              # Barrel exports
    ├── types.ts              # Tipos específicos do módulo
    ├── MeuModuloPage.tsx     # Página principal
    ├── components/           # Componentes do módulo
    │   ├── index.ts
    │   └── MeuComponente.tsx
    ├── hooks/                # Hooks do módulo
    │   ├── index.ts
    │   └── useMeuDado.ts
    └── services/             # Serviços/API calls
        ├── index.ts
        └── meuModulo.service.ts
```

### Passo a Passo

1. **Crie a pasta do módulo:**

   ```bash
   mkdir -p apps/web/src/modules/meu-modulo/{components,hooks,services}
   ```

2. **Crie os arquivos base:**
   - `types.ts` — Defina interfaces e tipos
   - `MeuModuloPage.tsx` — Componente principal
   - `index.ts` — Exporte o módulo

3. **Registre a rota em `App.tsx`:**

   ```tsx
   const MeuModuloPage = lazy(() => import('./modules/meu-modulo/MeuModuloPage'))

   // Na configuração de rotas:
   <Route path="/meu-modulo" element={<MeuModuloPage />} />
   ```

4. **Adicione ao menu (se necessário)** em `navigation/map.ts`

---

## Convenções de Código

### Nomenclatura

| Tipo                | Convenção           | Exemplo          |
| ------------------- | ------------------- | ---------------- |
| Componentes         | PascalCase          | `UserCard.tsx`   |
| Hooks               | camelCase com `use` | `useUserData.ts` |
| Funções/variáveis   | camelCase           | `getUserById`    |
| Tipos/Interfaces    | PascalCase          | `UserProfile`    |
| Constantes          | UPPER_SNAKE_CASE    | `API_BASE_URL`   |
| Arquivos CSS/styles | kebab-case          | `user-card.css`  |

### Organização de Imports

```tsx
// 1. React e bibliotecas externas
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

// 2. Packages internos (@template/*)
import { useAuth } from '@template/shared'
import { Button } from '@template/design-system'

// 3. Imports relativos (componentes, hooks, etc)
import { UserCard } from './components'
import { useUserData } from './hooks'

// 4. Tipos (sempre por último)
import type { User } from './types'
```

### Boas Práticas

- ✅ Componentes funcionais com hooks
- ✅ TypeScript strict mode
- ✅ Props tipadas com interfaces
- ✅ Tratamento de erros com try/catch
- ✅ Loading states em operações assíncronas
- ❌ Evite `any` — use tipos específicos
- ❌ Evite lógica complexa em componentes — extraia para hooks

---

## Processo de Pull Request

### Antes de Abrir um PR

1. **Atualize sua branch:**

   ```bash
   git checkout main && git pull
   git checkout sua-branch && git rebase main
   ```

2. **Execute as verificações:**

   ```bash
   pnpm lint
   pnpm typecheck
   pnpm test
   pnpm build
   ```

3. **Resolva conflitos** se houver

### Criando o PR

1. Use o template de PR fornecido
2. Preencha todas as seções
3. Adicione reviewers apropriados
4. Vincule issues relacionadas

### Critérios de Aprovação

- [ ] Testes passando
- [ ] Lint sem erros
- [ ] Build sem erros
- [ ] Code review aprovado (mínimo 1)
- [ ] Documentação atualizada (se aplicável)

---

## Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/) para manter um histórico limpo.

### Formato

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos

| Tipo       | Descrição                     |
| ---------- | ----------------------------- |
| `feat`     | Nova funcionalidade           |
| `fix`      | Correção de bug               |
| `docs`     | Apenas documentação           |
| `style`    | Formatação (não afeta código) |
| `refactor` | Refatoração de código         |
| `test`     | Adição/correção de testes     |
| `chore`    | Tarefas de manutenção         |
| `perf`     | Melhoria de performance       |
| `ci`       | Mudanças em CI/CD             |

### Exemplos

```bash
feat(auth): adicionar login com Google
fix(api): corrigir timeout em requisições longas
docs(readme): atualizar instruções de instalação
refactor(modules): extrair lógica para hooks customizados
```

---

## Dúvidas?

- Consulte o [portal de documentação](./docs/INDEX.md)
- Abra uma issue com a label `question`
- Converse com a equipe no canal do projeto

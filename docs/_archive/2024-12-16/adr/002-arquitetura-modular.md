# ADR-002: Arquitetura Modular (Monorepo)

## Status

**ACEITO**

Data: 2024-12-16

Autores: Equipe de Arquitetura

## Contexto

O projeto Template Platform precisa de uma estrutura que permita:

- **Reutilização** - Componentes e lógica compartilhados entre aplicações
- **Escalabilidade** - Adicionar novos módulos/features sem refatoração massiva
- **Manutenibilidade** - Separação clara de responsabilidades
- **Consistência** - Design system e padrões únicos
- **Velocidade** - Desenvolvimento paralelo por múltiplas equipes
- **Deploy independente** - Possibilidade de deploy granular no futuro

### Restrições

- Equipe atual é pequena (< 10 devs)
- Necessidade de manter simplicidade operacional
- CI/CD deve ser eficiente (não rebuildar tudo sempre)
- Código compartilhado entre frontend e potenciais micro-frontends futuros

## Decisão

Decidimos adotar uma **arquitetura monorepo** utilizando **pnpm workspaces** com a seguinte estrutura:

```
template-platform/
├── apps/
│   └── web/                    # Aplicação principal (React SPA)
│       ├── src/
│       │   ├── components/     # Componentes específicos da app
│       │   ├── pages/          # Páginas/rotas
│       │   ├── modules/        # Módulos de features
│       │   ├── hooks/          # Hooks específicos
│       │   └── lib/            # Utilitários específicos
│       └── e2e/                # Testes E2E
│
├── packages/
│   ├── design-system/          # Componentes UI reutilizáveis
│   │   ├── src/
│   │   │   ├── components/     # Button, Input, Modal, etc.
│   │   │   ├── tokens/         # Design tokens (cores, spacing)
│   │   │   └── styles/         # Estilos base
│   │   └── .storybook/         # Documentação visual
│   │
│   ├── shared/                 # Lógica compartilhada
│   │   └── src/
│   │       ├── api/            # API client, interceptors
│   │       ├── auth/           # AuthContext, hooks de auth
│   │       ├── cache/          # Query client config
│   │       └── utils/          # Helpers, formatters, logger
│   │
│   └── types/                  # Tipos TypeScript compartilhados
│       └── src/
│           ├── api.ts          # Tipos de API responses
│           ├── auth.ts         # Tipos de autenticação
│           └── common.ts       # Tipos genéricos
│
├── api-template/               # Backend FastAPI
│   ├── app/
│   │   ├── routes/             # Endpoints
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic
│   └── alembic/                # Migrations
│
├── infra/
│   ├── docker-compose.yml      # Ambiente local
│   ├── keycloak/               # Configuração IdP
│   └── k8s/                    # Manifests Kubernetes
│
└── scripts/                    # Automação
```

### Princípios da Arquitetura

1. **Packages são independentes** - Cada package tem seu próprio `package.json`, build e testes
2. **Dependências explícitas** - Imports entre packages via aliases (`@template/shared`)
3. **Versionamento único** - Todos os packages versionados juntos (monorepo)
4. **Build incremental** - Apenas packages alterados são rebuilds

### Regras de Dependência

```
apps/web
    ↓ pode importar
packages/design-system
packages/shared
packages/types
    ↓ podem importar
(apenas libs externas)
```

**Proibido:** packages importarem de apps ou dependências circulares.

## Alternativas Consideradas

### Alternativa 1: Multi-repo (Polyrepo)

**Descrição:** Cada package em seu próprio repositório Git.

**Prós:**

- Isolamento completo entre projetos
- Permissões granulares por repo
- CI/CD independente
- Versionamento semântico por package

**Contras:**

- Overhead de manutenção (múltiplos repos)
- Sincronização de versões complexa
- Refatorações cross-repo difíceis
- DX fragmentada (múltiplos clones, branches)
- "Dependency hell" entre packages

### Alternativa 2: Monolito SPA único

**Descrição:** Todo código frontend em uma única estrutura sem packages.

**Prós:**

- Simplicidade inicial
- Sem overhead de configuração de workspaces
- Build único

**Contras:**

- Escalabilidade limitada
- Reutilização de código difícil
- Acoplamento alto entre features
- Testes mais lentos (tudo junto)
- Impossível evoluir para micro-frontends

### Alternativa 3: Nx/Turborepo

**Descrição:** Ferramentas avançadas de monorepo.

**Prós:**

- Cache distribuído de builds
- Execução paralela otimizada
- Geração de código (scaffolding)
- Grafos de dependência visuais

**Contras:**

- Complexidade adicional
- Curva de aprendizado
- Overhead para projetos menores
- Vendor lock-in potencial

**Decisão:** Optamos por pnpm workspaces nativos por simplicidade. Migração para Nx/Turborepo pode ser considerada quando a escala justificar.

## Consequências

### Positivas

- **Atomic commits** - Mudanças relacionadas em um único commit/PR
- **Refatoração fácil** - Renomear, mover código com confiança
- **Consistência** - Mesmas versões de dependências em todo projeto
- **Code review unificado** - Contexto completo em um PR
- **Onboarding simplificado** - Um clone, um setup
- **Shared tooling** - ESLint, Prettier, TypeScript config únicos

### Negativas

- **Build inicial maior** - Precisa buildar todos os packages
- **CI mais complexo** - Detectar o que mudou para otimizar
- **Conflitos de merge** - Mais frequentes em times grandes
- **Tamanho do repo** - Cresce com o tempo

### Riscos

| Risco                                | Probabilidade | Impacto | Mitigação                                         |
| ------------------------------------ | ------------- | ------- | ------------------------------------------------- |
| Acoplamento excessivo entre packages | Média         | Alto    | Code review rigoroso, regras de lint para imports |
| CI lento com crescimento             | Média         | Médio   | Implementar cache, builds incrementais            |
| Conflitos frequentes no package.json | Média         | Baixo   | Lockfile automático, merge strategy               |

## Padrões de Código

### Estrutura de um Package

```
packages/exemplo/
├── src/
│   ├── index.ts           # Barrel export (API pública)
│   ├── ComponenteA/
│   │   ├── ComponenteA.tsx
│   │   ├── ComponenteA.test.tsx
│   │   └── index.ts
│   └── __tests__/         # Testes de integração
├── package.json
├── tsconfig.json
├── vitest.config.ts
└── README.md
```

### Convenções de Import

```typescript
// ✅ Correto - import do barrel
import { Button, Input } from '@template/design-system'
import { useAuth, apiClient } from '@template/shared'
import type { User, ApiResponse } from '@template/types'

// ❌ Incorreto - import direto de arquivo interno
import { Button } from '@template/design-system/src/components/Button/Button'
```

### Package.json de um Package

```json
{
  "name": "@template/exemplo",
  "version": "0.1.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "lint": "eslint src/"
  },
  "dependencies": {
    "@template/types": "workspace:*"
  }
}
```

## Métricas de Sucesso

- **Tempo de CI** < 10min para PR típico
- **Tempo de build local** < 30s após cache
- **Cobertura de testes por package** > 80%
- **Zero dependências circulares**
- **Tamanho de bundle final** monitorado por package

## Referências

- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Monorepo Explained](https://monorepo.tools/)
- [Nx Documentation](https://nx.dev/concepts/mental-model)
- [Google Monorepo Paper](https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)

---

_Última revisão: Dezembro 2024_

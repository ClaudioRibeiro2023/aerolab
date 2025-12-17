---
id: 'ADR-002'
title: 'Arquitetura Modular (Monorepo)'
status: 'accepted'
date: '2024-12-16'
owners:
  - 'Equipe de Arquitetura'
tags:
  - 'arquitetura'
  - 'monorepo'
  - 'workspace'
related:
  - 'ADR-001'
supersedes: null
superseded_by: null
---

# ADR-002: Arquitetura Modular (Monorepo)

## 1. Contexto e Problema

O projeto AeroLab precisa de uma estrutura que permita:

- **Reutilização** - Componentes e lógica compartilhados entre aplicações
- **Escalabilidade** - Adicionar novos módulos sem refatoração massiva
- **Manutenibilidade** - Separação clara de responsabilidades
- **Consistência** - Design system e padrões únicos
- **Velocidade** - Desenvolvimento paralelo por múltiplas equipes

> **Problema central:** Como organizar o código para maximizar reutilização mantendo independência entre partes?

## 2. Drivers de Decisão

- **DR1:** Reutilização de código
- **DR2:** Facilidade de refatoração
- **DR3:** Velocidade de CI/CD
- **DR4:** Simplicidade operacional

Priorização: DR1 > DR2 > DR3 > DR4

## 3. Decisão

> **Decidimos:** Adotar arquitetura monorepo com pnpm workspaces, separando código em `apps/` e `packages/`.

### Estrutura Implementada

**Fonte:** Raiz do repositório

```
template-platform/
├── apps/
│   └── web/                    # Aplicação React SPA
│
├── packages/
│   ├── shared/                 # Auth, API client, utils
│   ├── design-system/          # Componentes UI
│   └── types/                  # Tipos TypeScript
│
├── api-template/               # Backend FastAPI
│
├── infra/                      # Docker, K8s
│
├── package.json                # Root workspace
└── pnpm-workspace.yaml         # Workspace config
```

### Configuração do Workspace

**Fonte:** `pnpm-workspace.yaml`

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

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

**Proibido:** Dependências circulares entre packages.

### Escopo

- **Afeta:** Toda a organização do código frontend
- **Não afeta:** Backend (api-template é independente)

## 4. Alternativas Consideradas

### Alternativa A: Multi-repo (Polyrepo)

| Aspecto | Avaliação                                |
| ------- | ---------------------------------------- |
| Prós    | Isolamento total, CI independente        |
| Contras | Sincronização difícil, "dependency hell" |
| Esforço | Alto (manutenção contínua)               |
| Risco   | Alto (drift entre repos)                 |

**Por que descartada:** Overhead de manutenção muito alto para time pequeno.

### Alternativa B: Monolito sem packages

| Aspecto | Avaliação                              |
| ------- | -------------------------------------- |
| Prós    | Simplicidade inicial                   |
| Contras | Acoplamento alto, difícil reutilização |
| Esforço | Baixo inicial, alto a longo prazo      |
| Risco   | Médio                                  |

**Por que descartada:** Não escala, impossibilita reutilização.

### Alternativa C: Nx/Turborepo

| Aspecto | Avaliação                            |
| ------- | ------------------------------------ |
| Prós    | Cache distribuído, execução paralela |
| Contras | Complexidade, curva de aprendizado   |
| Esforço | Médio                                |
| Risco   | Baixo                                |

**Por que descartada:** Overhead desnecessário para o tamanho atual do projeto. Pode ser adotado futuramente.

## 5. Consequências e Trade-offs

### Positivas

- ✅ Atomic commits - Mudanças relacionadas em um único PR
- ✅ Refatoração fácil - Renomear/mover com confiança
- ✅ Consistência - Mesmas versões de deps em todo projeto
- ✅ Onboarding simplificado - Um clone, um setup

### Negativas

- ⚠️ Build inicial rebuilda todos os packages
- ⚠️ CI precisa detectar o que mudou para otimizar
- ⚠️ Conflitos de merge mais frequentes em times grandes

### Riscos Identificados

| Risco                    | Probabilidade | Impacto | Mitigação                  |
| ------------------------ | ------------- | ------- | -------------------------- |
| Acoplamento excessivo    | Média         | Alto    | Code review, lint rules    |
| CI lento com crescimento | Média         | Médio   | Cache, builds incrementais |

## 6. Impacto em Integrações e Contratos

### Breaking Changes

- [x] Não aplicável (decisão estrutural interna)

### Para Integradores

Esta decisão é **interna** e não afeta consumidores externos da API.

### Exports dos Packages

| Package                   | Export                 | Uso                                                |
| ------------------------- | ---------------------- | -------------------------------------------------- |
| `@template/shared`        | `auth`, `api`, `utils` | `import { useAuth } from '@template/shared/auth'`  |
| `@template/design-system` | Componentes UI         | `import { Button } from '@template/design-system'` |
| `@template/types`         | Tipos TypeScript       | `import type { User } from '@template/types'`      |

### Compatibilidade

- Packages usam `workspace:*` para deps internas
- Versionamento único (todos packages na mesma versão)

## 7. Plano de Rollout/Migração

### Status

✅ **Implementado** - Estrutura em uso desde a criação do projeto.

### Evolução Futura

1. **Considerar Nx** quando CI > 10min
2. **Micro-frontends** se necessário deploy independente
3. **Package publishing** se packages forem compartilhados externamente

## 8. Referências

### Internas

- [Mapa do Repositório](../99-mapa-do-repo.md)
- [C4 Component Diagram](../arquitetura/c4-component.md)

### Externas

- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Monorepo Explained](https://monorepo.tools/)

---

## Histórico

| Data       | Autor                 | Mudança              |
| ---------- | --------------------- | -------------------- |
| 2024-12-16 | Equipe de Arquitetura | Criação              |
| 2024-12-16 | Cascade               | Migração para ADR v2 |

---

_Migrado de `/docs/adr/002-arquitetura-modular.md`_

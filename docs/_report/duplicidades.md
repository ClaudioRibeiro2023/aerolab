# Relatório de Duplicidades

> **Data:** 2024-12-16  
> **Objetivo:** Identificar sobreposição de conteúdo entre documentos

---

## Grupos de Duplicidade

### Grupo 1: Arquitetura

| Documento                           | Conteúdo                                       | Sobreposição |
| ----------------------------------- | ---------------------------------------------- | ------------ |
| `ARCHITECTURE.md`                   | Stack, estrutura, ADRs inline, roles, env vars | 70%          |
| `arquitetura/c4-context.md`         | Diagrama C4 L1                                 | Único        |
| `arquitetura/c4-container.md`       | Diagrama C4 L2, stack                          | 20%          |
| `arquitetura/c4-component.md`       | Diagrama C4 L3                                 | Único        |
| `adr_v2/001-stack-tecnologica.md`   | Stack detalhada                                | 30%          |
| `adr_v2/002-arquitetura-modular.md` | Estrutura monorepo                             | 40%          |

**Decisão:**

- **Canônico:** `arquitetura/` (C4) + `adr_v2/` (decisões)
- **Ação:** Arquivar `ARCHITECTURE.md`, extrair conteúdo único primeiro

**Conteúdo único em ARCHITECTURE.md a preservar:**

- Seção 7: Convenções de Código (nomenclatura, imports, exports)
- Seção 9: Scripts Disponíveis
- Seção 11: Features de Produção (tabelas de referência)

---

### Grupo 2: Setup/Onboarding

| Documento                        | Conteúdo                                | Sobreposição |
| -------------------------------- | --------------------------------------- | ------------ |
| `GETTING_STARTED.md`             | Clone, setup, primeiro módulo           | 80%          |
| `operacao/setup-local.md`        | Pré-requisitos, setup completo, scripts | 80%          |
| `DEPLOY.md`                      | Docker, staging, prod, env vars         | 40%          |
| `operacao/variaveis-ambiente.md` | Env vars detalhadas                     | 30%          |

**Decisão:**

- **Canônico:** `operacao/setup-local.md` (dev) + `operacao/deploy.md` (novo, para prod)
- **Ação:**
  1. Arquivar `GETTING_STARTED.md` (coberto por setup-local)
  2. Renomear/mover `DEPLOY.md` para `operacao/deploy.md`

---

### Grupo 3: Roles/RBAC/Auth

| Documento                             | Conteúdo                         | Sobreposição |
| ------------------------------------- | -------------------------------- | ------------ |
| `ROLES_E_ACESSO.md`                   | Roles, Keycloak, uso frontend    | 90%          |
| `seguranca/rbac.md`                   | RBAC completo, matriz permissões | 90%          |
| `contratos-integracao/auth.md`        | OIDC, JWT, validação             | 30%          |
| `adr_v2/003-autenticacao-jwt-rbac.md` | Decisão arquitetural auth        | 20%          |

**Decisão:**

- **Canônico:** `seguranca/rbac.md` (roles) + `contratos-integracao/auth.md` (integração)
- **Ação:** Arquivar `ROLES_E_ACESSO.md`

---

### Grupo 4: ADRs

| Documento               | Conteúdo               | Sobreposição |
| ----------------------- | ---------------------- | ------------ |
| `adr/README.md`         | Índice ADRs legado     | 100%         |
| `adr_v2/README.md`      | Índice ADRs v2         | Substitui    |
| `adr/000-template.md`   | Template legado        | 100%         |
| `adr_v2/template_v2.md` | Template v2            | Substitui    |
| `adr/001-*.md`          | ADR stack legado       | 100%         |
| `adr_v2/001-*.md`       | ADR stack v2           | Substitui    |
| `adr/002-*.md`          | ADR arquitetura legado | 100%         |
| `adr_v2/002-*.md`       | ADR arquitetura v2     | Substitui    |
| `adr/003-*.md`          | ADR auth legado        | 100%         |
| `adr_v2/003-*.md`       | ADR auth v2            | Substitui    |

**Decisão:**

- **Canônico:** `adr_v2/` inteiro
- **Ação:** Arquivar `adr/` inteiro

---

### Grupo 5: Backlog/Propostas

| Documento                 | Conteúdo                | Sobreposição |
| ------------------------- | ----------------------- | ------------ |
| `PROPOSTA_ARQUITETURA.md` | Análise, plano de fases | Histórico    |
| `UI_UX_IMPROVEMENTS.md`   | Melhorias UI/UX         | Backlog      |
| `VALIDATION_CHECKLIST.md` | Checklist fase 0        | Histórico    |

**Decisão:**

- **Canônico:** Nenhum (não são docs de referência)
- **Ação:** Arquivar todos (histórico de decisões passadas)

---

## Matriz de Consolidação

| Doc Fonte            | → Doc Destino                   | Seções a Migrar                  |
| -------------------- | ------------------------------- | -------------------------------- |
| `ARCHITECTURE.md`    | `operacao/convencoes.md` (novo) | Seção 7: Convenções de Código    |
| `ARCHITECTURE.md`    | `operacao/scripts.md` (novo)    | Seção 9: Scripts Disponíveis     |
| `DEPLOY.md`          | `operacao/deploy.md` (renomear) | Manter como está                 |
| `GETTING_STARTED.md` | -                               | Já coberto, arquivar direto      |
| `ROLES_E_ACESSO.md`  | -                               | Já coberto por seguranca/rbac.md |

---

## Resumo de Ações

### Arquivar Imediatamente (sem merge)

1. `adr/` inteiro → `_archive/2024-12-16/adr/`
2. `GETTING_STARTED.md` → `_archive/2024-12-16/`
3. `ROLES_E_ACESSO.md` → `_archive/2024-12-16/`
4. `PROPOSTA_ARQUITETURA.md` → `_archive/2024-12-16/`
5. `UI_UX_IMPROVEMENTS.md` → `_archive/2024-12-16/` ou `_backlog/`
6. `VALIDATION_CHECKLIST.md` → `_archive/2024-12-16/`

### Consolidar e Depois Arquivar

1. `ARCHITECTURE.md`:
   - Extrair convenções → `operacao/convencoes.md`
   - Arquivar original

### Mover (não arquivar)

1. `DEPLOY.md` → `operacao/deploy.md`

---

_Gerado em: 2024-12-16_

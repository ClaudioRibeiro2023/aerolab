# Inventário de Documentação - COMPLETO

> **Data:** 2024-12-16 (atualizado)  
> **Escopo:** TODOS os .md no repositório (não apenas docs/)

---

## Resumo Geral

| Localização         | Arquivos | Status                    |
| ------------------- | -------- | ------------------------- |
| Raiz (`/`)          | 3        | KEEP (entry points)       |
| `apps/web/src/`     | 3        | KEEP (convenções in-situ) |
| `infra/keycloak/`   | 1        | KEEP (setup específico)   |
| `docs/` (canônicos) | 20       | KEEP                      |
| `docs/_archive/`    | 11       | ARCHIVED                  |
| `docs/_backlog/`    | 2        | BACKLOG                   |
| `docs/_report/`     | 3        | META                      |
| **Total**           | **43**   | -                         |

---

## Arquivos FORA de docs/

### Raiz do Repositório

| Caminho            | Tipo        | Tema         | Referenciado? | Duplicado?      | Canônico | Ação | Motivo                    |
| ------------------ | ----------- | ------------ | ------------- | --------------- | -------- | ---- | ------------------------- |
| `/README.md`       | Entry point | Visão geral  | Sim (GitHub)  | Parcial c/ docs | Sim      | KEEP | Entry point do repo       |
| `/CONTRIBUTING.md` | Guia        | Contribuição | Sim (README)  | Não             | Sim      | KEEP | Guia de contribuição      |
| `/todo.md`         | Backlog     | Tarefas      | Não           | Não             | Não      | MOVE | Mover para docs/\_backlog |

### Apps (Convenções In-Situ)

| Caminho                           | Tipo      | Tema     | Referenciado? | Duplicado? | Canônico | Ação | Motivo               |
| --------------------------------- | --------- | -------- | ------------- | ---------- | -------- | ---- | -------------------- |
| `apps/web/src/hooks/README.md`    | Convenção | Hooks    | Não           | Parcial    | Sim      | KEEP | Convenção local (DX) |
| `apps/web/src/modules/README.md`  | Convenção | Módulos  | Não           | Parcial    | Sim      | KEEP | Convenção local (DX) |
| `apps/web/src/services/README.md` | Convenção | Services | Não           | Parcial    | Sim      | KEEP | Convenção local (DX) |

### Infra

| Caminho                    | Tipo  | Tema     | Referenciado? | Duplicado? | Canônico | Ação | Motivo                 |
| -------------------------- | ----- | -------- | ------------- | ---------- | -------- | ---- | ---------------------- |
| `infra/keycloak/README.md` | Setup | Keycloak | Não           | Parcial    | Sim      | KEEP | Setup específico local |

---

## Arquivos em docs/ (Canônicos)

### Índice e Referência

| Caminho              | Tipo       | Tema      | Ação | Motivo           |
| -------------------- | ---------- | --------- | ---- | ---------------- |
| `INDEX.md`           | Índice     | TOC       | KEEP | Índice mestre    |
| `99-mapa-do-repo.md` | Referência | Estrutura | KEEP | Mapa técnico     |
| `DESIGN_SYSTEM.md`   | Referência | UI/UX     | KEEP | Design System    |
| `BOOK_OF_TESTS.md`   | Referência | Testes    | KEEP | Matriz de testes |
| `TROUBLESHOOTING.md` | Referência | Suporte   | KEEP | Problemas comuns |

### Arquitetura (arquitetura/)

| Caminho                       | Tipo     | Tema  | Ação | Motivo      |
| ----------------------------- | -------- | ----- | ---- | ----------- |
| `arquitetura/c4-context.md`   | Diagrama | C4 L1 | KEEP | Contexto    |
| `arquitetura/c4-container.md` | Diagrama | C4 L2 | KEEP | Containers  |
| `arquitetura/c4-component.md` | Diagrama | C4 L3 | KEEP | Componentes |

### Contratos de Integração (contratos-integracao/)

| Caminho                           | Tipo     | Tema     | Ação | Motivo        |
| --------------------------------- | -------- | -------- | ---- | ------------- |
| `contratos-integracao/auth.md`    | Contrato | OIDC/JWT | KEEP | Auth contract |
| `contratos-integracao/api.md`     | Contrato | REST API | KEEP | API contract  |
| `contratos-integracao/openapi.md` | Contrato | OpenAPI  | KEEP | Swagger docs  |

### Operação (operacao/)

| Caminho                          | Tipo       | Tema     | Ação | Motivo           |
| -------------------------------- | ---------- | -------- | ---- | ---------------- |
| `operacao/setup-local.md`        | Guia       | Setup    | KEEP | Setup dev        |
| `operacao/deploy.md`             | Guia       | Deploy   | KEEP | Deploy guide     |
| `operacao/variaveis-ambiente.md` | Referência | Env vars | KEEP | Env reference    |
| `operacao/convencoes.md`         | Convenção  | Código   | KEEP | Code conventions |

### Segurança (seguranca/)

| Caminho                          | Tipo       | Tema    | Ação | Motivo           |
| -------------------------------- | ---------- | ------- | ---- | ---------------- |
| `seguranca/rbac.md`              | Referência | RBAC    | KEEP | Roles system     |
| `seguranca/headers-seguranca.md` | Referência | Headers | KEEP | Security headers |

### ADRs (adr_v2/)

| Caminho                               | Tipo     | Tema        | Ação | Motivo       |
| ------------------------------------- | -------- | ----------- | ---- | ------------ |
| `adr_v2/README.md`                    | Índice   | ADRs        | KEEP | ADR index    |
| `adr_v2/template_v2.md`               | Template | ADR         | KEEP | ADR template |
| `adr_v2/001-stack-tecnologica.md`     | ADR      | Stack       | KEEP | ADR aceito   |
| `adr_v2/002-arquitetura-modular.md`   | ADR      | Arquitetura | KEEP | ADR aceito   |
| `adr_v2/003-autenticacao-jwt-rbac.md` | ADR      | Auth        | KEEP | ADR aceito   |

---

## Arquivos Arquivados (\_archive/)

| Caminho                                       | Motivo do Arquivamento                      |
| --------------------------------------------- | ------------------------------------------- |
| `_archive/2024-12-16/ARCHITECTURE.md`         | Consolidado em arquitetura/ + convencoes.md |
| `_archive/2024-12-16/GETTING_STARTED.md`      | Coberto por operacao/setup-local.md         |
| `_archive/2024-12-16/ROLES_E_ACESSO.md`       | Coberto por seguranca/rbac.md               |
| `_archive/2024-12-16/PROPOSTA_ARQUITETURA.md` | Histórico - plano concluído                 |
| `_archive/2024-12-16/VALIDATION_CHECKLIST.md` | Histórico - fase 0 concluída                |
| `_archive/2024-12-16/MOTIVO.md`               | Meta - justificativa                        |
| `_archive/2024-12-16/adr/*.md` (5 arquivos)   | Migrados para adr_v2/                       |

---

## Arquivos em Backlog (\_backlog/)

| Caminho                          | Descrição                  |
| -------------------------------- | -------------------------- |
| `_backlog/README.md`             | Índice do backlog          |
| `_backlog/UI_UX_IMPROVEMENTS.md` | Melhorias UI/UX planejadas |

---

## Ações Pendentes

### MOVE (1 arquivo)

| Arquivo   | De         | Para                    | Motivo                    |
| --------- | ---------- | ----------------------- | ------------------------- |
| `todo.md` | `/` (raiz) | `docs/_backlog/todo.md` | Backlog não é entry point |

### UPDATE (1 arquivo)

| Arquivo      | Ação                                 | Motivo                              |
| ------------ | ------------------------------------ | ----------------------------------- |
| `/README.md` | Atualizar links para docs arquivados | Links apontam para arquivos movidos |

---

## Análise de Duplicidades com docs/

### README.md (raiz) vs docs/

| Seção no README      | Sobrepõe | Doc Canônico            |
| -------------------- | -------- | ----------------------- |
| Início Rápido        | ~60%     | operacao/setup-local.md |
| Autenticação e Roles | ~40%     | seguranca/rbac.md       |
| Estrutura do Projeto | ~30%     | 99-mapa-do-repo.md      |
| Scripts Disponíveis  | ~50%     | operacao/convencoes.md  |

**Decisão:** KEEP - README é entry point do GitHub, deve ter visão geral. Links devem apontar para docs/ canônicos para detalhes.

### CONTRIBUTING.md vs docs/

| Seção                | Sobrepõe | Doc Canônico                   |
| -------------------- | -------- | ------------------------------ |
| Setup do Ambiente    | ~50%     | operacao/setup-local.md        |
| Estrutura do Projeto | ~30%     | 99-mapa-do-repo.md             |
| Como Criar Módulo    | ~70%     | apps/web/src/modules/README.md |
| Convenções de Código | ~60%     | operacao/convencoes.md         |

**Decisão:** KEEP - Guia de contribuição é padrão OSS. Pode adicionar links para docs/ canônicos.

### infra/keycloak/README.md vs docs/

| Seção                 | Sobrepõe | Doc Canônico                   |
| --------------------- | -------- | ------------------------------ |
| Setup Keycloak        | ~30%     | contratos-integracao/auth.md   |
| Variáveis de Ambiente | ~20%     | operacao/variaveis-ambiente.md |

**Decisão:** KEEP - README local para quem trabalha em infra/keycloak. Adicionar link para docs/ no final.

---

## Conclusão

O repositório está **bem organizado** após a consolidação anterior. Ações restantes:

1. **Mover** `todo.md` para `docs/_backlog/`
2. **Atualizar** links no `README.md` para apontar para novos caminhos em docs/
3. **Adicionar** links cruzados nos READMEs fora de docs/ para docs/ canônicos

---

_Inventário atualizado em: 2024-12-16_

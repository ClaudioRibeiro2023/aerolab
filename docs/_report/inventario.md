# Inventário de Documentação

> **Data:** 2024-12-16  
> **Objetivo:** Mapear todos os .md em docs/ para consolidação

---

## Resumo

| Status     | Quantidade |
| ---------- | ---------- |
| KEEP       | 12         |
| CONSOLIDAR | 8          |
| ARCHIVE    | 12         |
| **Total**  | **32**     |

---

## Inventário Completo

### Raiz (`docs/`)

| Caminho                   | Título                  | Assunto     | Público   | Status         | Motivo                           |
| ------------------------- | ----------------------- | ----------- | --------- | -------------- | -------------------------------- |
| `INDEX.md`                | Índice da Documentação  | Índice/TOC  | todos     | **KEEP**       | Índice mestre - atualizar        |
| `99-mapa-do-repo.md`      | Mapa do Repositório     | Estrutura   | dev/ops   | **KEEP**       | Único - referência técnica       |
| `ARCHITECTURE.md`         | Arquitetura do Template | Arquitetura | dev       | **CONSOLIDAR** | Sobrepõe c4-\*.md e adr_v2       |
| `BOOK_OF_TESTS.md`        | Book de Testes          | Testes      | dev/qa    | **KEEP**       | Único - matriz de testes         |
| `DEPLOY.md`               | Guia de Deploy          | Operação    | ops/dev   | **CONSOLIDAR** | Sobrepõe operacao/setup-local.md |
| `DESIGN_SYSTEM.md`        | Design System           | UI/UX       | frontend  | **KEEP**       | Único - Design System completo   |
| `GETTING_STARTED.md`      | Guia de Início Rápido   | Onboarding  | dev       | **CONSOLIDAR** | Sobrepõe operacao/setup-local.md |
| `PROPOSTA_ARQUITETURA.md` | Proposta de Melhorias   | Backlog     | tech lead | **ARCHIVE**    | Histórico - tarefas concluídas   |
| `ROLES_E_ACESSO.md`       | Sistema de Roles        | Segurança   | dev       | **CONSOLIDAR** | Sobrepõe seguranca/rbac.md       |
| `TROUBLESHOOTING.md`      | Troubleshooting         | Operação    | todos     | **KEEP**       | Único - problemas comuns         |
| `UI_UX_IMPROVEMENTS.md`   | Melhorias UI/UX         | Backlog     | frontend  | **ARCHIVE**    | Backlog - mover para \_backlog   |
| `VALIDATION_CHECKLIST.md` | Checklist de Validação  | QA          | dev/qa    | **ARCHIVE**    | Histórico - fase 0 concluída     |

### ADR Legado (`docs/adr/`)

| Caminho                            | Título                | Assunto | Público | Status      | Motivo                                |
| ---------------------------------- | --------------------- | ------- | ------- | ----------- | ------------------------------------- |
| `adr/README.md`                    | ADR Index             | ADR     | dev     | **ARCHIVE** | Substituído por adr_v2/README.md      |
| `adr/000-template.md`              | Template ADR          | ADR     | dev     | **ARCHIVE** | Substituído por adr_v2/template_v2.md |
| `adr/001-stack-tecnologica.md`     | Stack Tecnológica     | ADR     | dev     | **ARCHIVE** | Migrado para adr_v2/001-\*.md         |
| `adr/002-arquitetura-modular.md`   | Arquitetura Modular   | ADR     | dev     | **ARCHIVE** | Migrado para adr_v2/002-\*.md         |
| `adr/003-autenticacao-jwt-rbac.md` | Autenticação JWT+RBAC | ADR     | dev     | **ARCHIVE** | Migrado para adr_v2/003-\*.md         |

### ADR v2 (`docs/adr_v2/`) ✅ Padrão

| Caminho                               | Título                   | Assunto | Público | Status   | Motivo              |
| ------------------------------------- | ------------------------ | ------- | ------- | -------- | ------------------- |
| `adr_v2/README.md`                    | ADR v2 Index             | ADR     | dev     | **KEEP** | Índice oficial ADRs |
| `adr_v2/template_v2.md`               | Template ADR v2          | ADR     | dev     | **KEEP** | Template oficial    |
| `adr_v2/001-stack-tecnologica.md`     | Stack Tecnológica v2     | ADR     | dev     | **KEEP** | ADR oficial         |
| `adr_v2/002-arquitetura-modular.md`   | Arquitetura Modular v2   | ADR     | dev     | **KEEP** | ADR oficial         |
| `adr_v2/003-autenticacao-jwt-rbac.md` | Autenticação JWT+RBAC v2 | ADR     | dev     | **KEEP** | ADR oficial         |

### Arquitetura (`docs/arquitetura/`)

| Caminho                       | Título               | Assunto     | Público | Status   | Motivo         |
| ----------------------------- | -------------------- | ----------- | ------- | -------- | -------------- |
| `arquitetura/c4-context.md`   | C4 Context Diagram   | Arquitetura | dev     | **KEEP** | Diagrama C4 L1 |
| `arquitetura/c4-container.md` | C4 Container Diagram | Arquitetura | dev     | **KEEP** | Diagrama C4 L2 |
| `arquitetura/c4-component.md` | C4 Component Diagram | Arquitetura | dev     | **KEEP** | Diagrama C4 L3 |

### Contratos de Integração (`docs/contratos-integracao/`)

| Caminho                           | Título           | Assunto    | Público | Status   | Motivo           |
| --------------------------------- | ---------------- | ---------- | ------- | -------- | ---------------- |
| `contratos-integracao/auth.md`    | Contrato de Auth | Integração | dev/ops | **KEEP** | Contrato oficial |
| `contratos-integracao/api.md`     | Contrato de API  | Integração | dev/ops | **KEEP** | Contrato oficial |
| `contratos-integracao/openapi.md` | OpenAPI/Swagger  | Integração | dev     | **KEEP** | Contrato oficial |

### Operação (`docs/operacao/`)

| Caminho                          | Título                | Assunto  | Público | Status   | Motivo                |
| -------------------------------- | --------------------- | -------- | ------- | -------- | --------------------- |
| `operacao/setup-local.md`        | Setup Local           | Operação | dev     | **KEEP** | Guia oficial de setup |
| `operacao/variaveis-ambiente.md` | Variáveis de Ambiente | Operação | dev/ops | **KEEP** | Referência env vars   |

### Segurança (`docs/seguranca/`)

| Caminho                          | Título               | Assunto   | Público | Status   | Motivo              |
| -------------------------------- | -------------------- | --------- | ------- | -------- | ------------------- |
| `seguranca/rbac.md`              | RBAC - Roles         | Segurança | dev     | **KEEP** | Doc oficial de RBAC |
| `seguranca/headers-seguranca.md` | Headers de Segurança | Segurança | dev/ops | **KEEP** | Doc oficial headers |

---

## Ações por Status

### KEEP (12 arquivos)

Manter como documentação canônica. Atualizar INDEX.md para apontar.

### CONSOLIDAR (4 arquivos)

Migrar conteúdo relevante para docs canônicos:

| De                   | Para                       | Ação                             |
| -------------------- | -------------------------- | -------------------------------- |
| `ARCHITECTURE.md`    | `arquitetura/` + `adr_v2/` | Extrair conteúdo único, arquivar |
| `DEPLOY.md`          | `operacao/setup-local.md`  | Merge seção deploy               |
| `GETTING_STARTED.md` | `operacao/setup-local.md`  | Já coberto, arquivar             |
| `ROLES_E_ACESSO.md`  | `seguranca/rbac.md`        | Já coberto, arquivar             |

### ARCHIVE (12 arquivos)

Mover para `docs/_archive/2024-12-16/`:

- `adr/` inteiro (5 arquivos) - Substituído por adr_v2
- `PROPOSTA_ARQUITETURA.md` - Histórico de proposta
- `UI_UX_IMPROVEMENTS.md` - Backlog/ideias
- `VALIDATION_CHECKLIST.md` - Histórico fase 0
- Consolidados após merge

---

_Gerado em: 2024-12-16_

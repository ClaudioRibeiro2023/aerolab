# Contrato Factory v1.1 — Criação de Workflows no AeroLab

> **Versão:** 1.1.0  
> **Status:** OFICIAL  
> **Última atualização:** Dezembro 2024

---

## 1. Objetivo

Este documento define o **contrato oficial** para criação, validação e publicação de workflows no AeroLab. Todo novo workflow **DEVE** seguir este padrão.

---

## 2. Estrutura Obrigatória

### 2.1 Documentação (`docs/workflows/<slug>/`)

```text
docs/workflows/<slug>/
├── README.md              # Obrigatório: documentação do workflow
└── schemas/
    ├── input.json         # Obrigatório: JSON Schema de entrada
    └── result.json        # Obrigatório: JSON Schema de saída
```

**README.md deve conter:**

- Slug, nome, domínio, versão
- Objetivo do workflow
- Tabela de entradas (campo, tipo, obrigatório, descrição)
- Tabela de saídas
- Fluxo de execução (diagrama ASCII ou Mermaid)
- Exemplos de uso
- Referências

### 2.2 Template Flow Studio (`apps/api/src/flow_studio/templates/<domain>/<slug>.json`)

```json
{
  "id": "<slug>",
  "name": "Nome do Workflow",
  "version": "1.0.0",
  "domain": "<domain>",
  "state_defaults": {
    "result": {
      "status": "init",
      "payload_json": "{}",
      "errors": []
    }
  },
  "inputs": { ... },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

**Regra crítica:** `state_defaults.result` é **OBRIGATÓRIO** com os campos `status`, `payload_json` e `errors`.

### 2.3 Runner Backend (`apps/api/src/workflows/<domain>/<slug>/`)

```text
apps/api/src/workflows/<domain>/<slug>/
├── __init__.py            # Exports públicos
├── models.py              # Pydantic models (Input/Result)
└── runner.py              # Lógica de execução
```

**Runner deve:**

- Validar inputs com Pydantic
- Executar nodes em sequência
- Gravar audit log por step (tokens, custo, tempo)
- Validar saída com schema
- Implementar repair loop (máx 2 tentativas)

### 2.4 Testes Golden (`apps/api/tests/golden/<slug>/`)

```text
apps/api/tests/golden/<slug>/
├── case_01.json           # Mínimo: 5 casos
├── case_02.json
├── ...
└── test_runner.py         # Testes pytest
```

**Mínimo de 5 golden cases + 1 arquivo de testes.**

---

## 3. Regras de Governança

### 3.1 Localização de Arquivos

| Tipo               | Local Permitido                       |
| ------------------ | ------------------------------------- |
| Documentação (.md) | `docs/`                               |
| Código Python      | `apps/api/src/`                       |
| Testes             | `apps/api/tests/`                     |
| Templates Flow     | `apps/api/src/flow_studio/templates/` |
| Prompts IA         | `windsurf/`                           |

**PROIBIDO:** Criar `.md` fora de `docs/` (exceto README.md na raiz e em módulos Python).

### 3.2 Convenções de Nomenclatura

- **slug:** `snake_case`, sem caracteres especiais
- **domain:** singular, lowercase (`licitacoes`, `vendas`, `rh`)
- **schemas:** `input.json` e `result.json` (exatos)
- **testes:** `case_NN.json` onde NN é número sequencial

### 3.3 Versionamento

- Workflows usam SemVer: `MAJOR.MINOR.PATCH`
- Breaking changes incrementam MAJOR
- Novas features incrementam MINOR
- Bugfixes incrementam PATCH

---

## 4. Validação

### 4.1 Comando

```bash
# Validar repositório
pnpm factory:validate

# Ou via Python diretamente
python scripts/factory_validate.py
```

### 4.2 Regras de Validação

| Regra            | Descrição                                  | Severidade |
| ---------------- | ------------------------------------------ | ---------- |
| MD_LOCATION      | Arquivos .md apenas em docs/               | ERROR      |
| WORKFLOW_README  | Cada workflow tem README.md                | ERROR      |
| WORKFLOW_SCHEMAS | Cada workflow tem input.json e result.json | ERROR      |
| GOLDEN_TESTS     | Mínimo 5 golden cases por workflow         | ERROR      |
| STATE_DEFAULTS   | Template tem state_defaults.result         | ERROR      |
| RUNNER_EXISTS    | Runner Python existe                       | WARNING    |

### 4.3 Integração CI

O comando `factory:validate` é executado automaticamente em:

- Pull Requests para `main`
- Push para `main`
- Pre-commit hook (opcional)

---

## 5. Fluxo de Criação

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. PROMPT_FACTORY_CREATE_WORKFLOW.md                        │
│    → Define slug, domain, inputs, outputs                   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Criar estrutura (docs + code + tests)                    │
│    → Seguir seção 2 deste contrato                          │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PROMPT_FACTORY_VALIDATE_REPO.md                          │
│    → Rodar factory:validate                                 │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PROMPT_FACTORY_PUBLISH_WORKFLOW.md                       │
│    → PR, review, merge, release                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Templates

### 6.1 Template de Documentação

Disponível em: `docs/_templates/workflow/README.md`

### 6.2 Template de Schemas

Disponível em: `docs/_templates/workflow/schemas/`

### 6.3 Prompts Oficiais

| Prompt                                        | Descrição           |
| --------------------------------------------- | ------------------- |
| `windsurf/PROMPT_FACTORY_CREATE_WORKFLOW.md`  | Criar novo workflow |
| `windsurf/PROMPT_FACTORY_VALIDATE_REPO.md`    | Validar repositório |
| `windsurf/PROMPT_FACTORY_PUBLISH_WORKFLOW.md` | Publicar workflow   |

---

## 7. Checklist DoD (Definition of Done)

Para um workflow ser considerado **DONE**, deve passar em TODOS os itens:

- [ ] README.md em `docs/workflows/<slug>/`
- [ ] Schema `input.json` válido
- [ ] Schema `result.json` válido
- [ ] Template Flow Studio com `state_defaults.result`
- [ ] Runner com validação Pydantic
- [ ] Audit log por step
- [ ] Mínimo 5 golden cases
- [ ] Testes pytest passando
- [ ] `factory:validate` PASS
- [ ] Endpoint(s) documentado(s)
- [ ] `docs/INDEX.md` atualizado

---

## 8. Referências

- [docs/INDEX.md](../INDEX.md) — Índice mestre
- [docs/\_templates/workflow/](../_templates/workflow/) — Templates
- [windsurf/PROMPT_MASTER_FACTORY_AEROLAB.md](../../windsurf/PROMPT_MASTER_FACTORY_AEROLAB.md) — Prompt mestre

---

_Factory v1.1 — Padrão oficial AeroLab para criação de workflows_

# Doc 03 — Arquitetura, Pastas e Passo a Passo (WindSurf) para o Núcleo Licitações

> **Objetivo**  
> Tornar a implementação “mecânica”: você segue o checklist e o núcleo nasce dentro da Agno sem bagunçar o repo.

---

## 1) Onde isso entra na Agno

Pelo TECHNICAL_REFERENCE, a plataforma é **modular por domínios**.  
Nossa recomendação é criar um domínio explícito:

```
src/
  domains/
    licitacoes/
      __init__.py
      models/
      services/
      tools/
      agents/
      flows/
      api/
      tests/
docs/
  LICITACOES_OVERVIEW.md
  SCHEMAS_LICITACOES.md
  ARQUITETURA_E_PASTAS_LICITACOES.md
```

### 1.1 Responsabilidade de cada pasta

- `models/`: Pydantic models + enums + schemas (Doc 02)
- `services/`: lógica pura (dedup, scoring, diff, parsing)
- `tools/`: integrações externas (PNCP, fetch HTML/PDF, storage)
- `agents/`: prompts/roles + orquestração (Watcher/Triage/Analyst/Compliance)
- `flows/`: definições de fluxo (Flow Studio templates + runners)
- `api/`: endpoints FastAPI do domínio (ex.: `/licitacoes/digest`, `/licitacoes/analyze`)
- `tests/`: testes unitários e “golden tests” (fixtures)

---

## 2) Interfaces do núcleo (contratos)

### 2.1 Entrada (MVP)

- `monitor()` → retorna `LicitacaoItem[]` + `ChangeEvent[]`
- `triage(items)` → retorna `TriageScore[]`
- `analyze(item)` → retorna `AnalysisPack`

### 2.2 Saídas

- `Digest` diário (markdown + json)
- `AnalysisPack` por item
- Eventos de alerta (ex.: prazo <= X)

---

## 3) Passo a passo no WindSurf (sem improviso)

### 3.1 Preparação

1. Abra o repo da Agno.
2. Crie um branch:
   - `git checkout -b feat/licitacoes-core`
3. Garanta que o ambiente roda (sanity check):
   - backend sobe (FastAPI)
   - frontend sobe (Next.js)
   - testes/lint passam (se existirem)

### 3.2 Criar a estrutura do domínio

Crie as pastas/arquivos vazios:

```
src/domains/licitacoes/__init__.py
src/domains/licitacoes/models/__init__.py
src/domains/licitacoes/services/__init__.py
src/domains/licitacoes/tools/__init__.py
src/domains/licitacoes/agents/__init__.py
src/domains/licitacoes/flows/__init__.py
src/domains/licitacoes/api/__init__.py
src/domains/licitacoes/tests/__init__.py
```

> **Dica WindSurf**: use “New File” e “New Folder” pelo Explorer.  
> Se preferir terminal:

- `mkdir -p src/domains/licitacoes/{models,services,tools,agents,flows,api,tests}`
- `touch src/domains/licitacoes/__init__.py ...`

### 3.3 Implementar os modelos (primeiro código real)

Crie:

- `src/domains/licitacoes/models/schemas.py`  
  Cole/implemente os schemas do Doc 02 como Pydantic.

Checklist:

- [ ] `ruff`/`mypy` não reclamam
- [ ] validação simples: criar um objeto `LicitacaoItem(...)` e rodar

### 3.4 Criar o primeiro tool (PNCP)

Crie:

- `src/domains/licitacoes/tools/pncp_client.py`

Checklist:

- [ ] função `search(query, filtros)` retorna `LicitacaoItem[]`
- [ ] cada item tem `sources[]` preenchido

### 3.5 Wire mínimo via API

Crie:

- `src/domains/licitacoes/api/routes.py` com endpoints:
  - `GET /licitacoes/health`
  - `POST /licitacoes/monitor` (debug)
  - `POST /licitacoes/analyze` (debug)

Checklist:

- [ ] rota aparece no OpenAPI
- [ ] payload valida schema

---

## 4) Prompts prontos (PROMPT-OS) para usar no WindSurf

### Prompt para criar `schemas.py`

**Cole no chat do WindSurf**:

- **Objetivo:** Implementar Pydantic models do Doc 02 em `src/domains/licitacoes/models/schemas.py`
- **Critérios de sucesso:** (a) imports corretos, (b) validação simples, (c) enums, (d) tipos opcionais claros
- **Restrições:** não criar outros arquivos, não inventar campos fora do Doc 02
- **Formato:** entregar o conteúdo completo do arquivo

### Prompt para criar `pncp_client.py`

- **Objetivo:** Implementar client PNCP com função `search()` e normalização p/ `LicitacaoItem`
- **Critérios:** timeouts, retries limitados, user-agent, logging mínimo
- **Restrições:** nada de scraping agressivo; preferir API

---

## 5) Definição de pronto (DoD) do Doc 03

Você está pronto para o Doc 04 quando:

- a estrutura do domínio existe
- `schemas.py` existe e valida
- existe pelo menos 1 tool funcional (PNCP)
- existe endpoint `/licitacoes/health`

---

## 6) Próximo documento

**Doc 04 — `docs/TOOLS_E_COLETA_LICITACOES.md`**  
Vai detalhar: PNCP, fetchers, parsing PDF/HTML, dedup e diff (com exemplos e casos de borda).

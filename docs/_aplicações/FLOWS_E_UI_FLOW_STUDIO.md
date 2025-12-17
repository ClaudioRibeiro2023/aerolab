# Doc 06 — Flows + UI no Flow Studio (Windsurf → Agno)

> **Objetivo**  
> Descrever como construir os **workflows completos** do núcleo Licitações no **Flow Studio** da Agno, com variáveis de estado, nós, validações e templates reaproveitáveis.

---

## 1) Princípio que evita 80% dos bugs

### 1.1 “Estado sempre válido”

No Flow Studio, **nunca** dependa de uma variável “vazia” para existir depois.  
Crie e inicialize o objeto `result` já no Start (ou no primeiro nó), com defaults.

Modelo recomendado:

```json
{
  "status": "init",
  "payload_json": "{}",
  "errors": []
}
```

> Isso resolve o problema clássico do builder: “não salva sem informação”.

---

## 2) Variáveis padrão do fluxo

### 2.1 Inputs (do usuário ou do agendamento)

- `mode` (string): `"monitor"` | `"analyze"`
- `input_as_text` (string): texto/URL/editais colados (só no `analyze`)
- `cfg` (object): config do domínio (janela_dias, filtros, etc.)

### 2.2 State (persistido durante execução)

- `items` (list): `LicitacaoItem[]`
- `changes` (list): `ChangeEvent[]`
- `scores` (list): `TriageScore[]`
- `analysis_pack` (object): `AnalysisPack`
- `result` (object): wrapper `{status, payload_json, errors}`

---

## 3) Workflow 1 — `daily_monitor` (P0)

### 3.1 Objetivo

Rodar diariamente e gerar o **Digest do Dia**.

### 3.2 Nós (ordem recomendada)

1. **Start**
   - inicializa `result` com defaults
2. **Guardrails (input)**
   - checa `cfg` + parâmetros (sanidade)
3. **Watcher: Monitor**
   - coleta + normaliza + dedup + diff
   - outputs: `items`, `changes`
4. **Triage: Score**
   - outputs: `scores`
5. **Gerar Digest**
   - compõe um markdown + json resumido
6. **Persistir**
   - grava `items`, `changes`, `scores`, `digest`
7. **Final**
   - `result.status="ok"`
   - `result.payload_json` com `{ digest_id, top_p0, top_p1, alerts }`

### 3.3 Saída mínima (payload_json)

```json
{
  "digest": {
    "date": "2025-12-15",
    "top_p0": ["lic:pncp:..."],
    "top_p1": ["lic:pncp:..."],
    "alerts": [{ "type": "prazo_curto", "item_id": "...", "days": 5 }]
  }
}
```

---

## 4) Workflow 2 — `on_demand_analyze` (P0)

### 4.1 Objetivo

Usuário cola edital/URL → recebe **AnalysisPack** completo.

### 4.2 Nós (ordem recomendada)

1. **Start** (init `result`)
2. **Guardrails (input)**
   - bloqueia PII, injection, conteúdo inadequado
3. **Resolver entrada**
   - se URL → baixar
   - se texto → tratar como raw text
4. **Watcher: Get Detail**
   - normaliza item + baixa anexos principais
5. **Analyst: Analyze**
   - extrai requisitos + riscos + evidências
6. **Guardrails (output)** (opcional)
   - valida se tem `sources[]` e `evidences[]`
7. **Persistir**
   - grava `analysis_pack`
8. **Final**
   - `result.status="ok"`
   - `result.payload_json` com referência do pack

---

## 5) Templates (reuso)

Crie templates para:

- `daily_monitor`
- `on_demand_analyze`
- `triage_only` (útil para debug)

Sugestão de pasta:

- `src/domains/licitacoes/flows/templates/`

Cada template contém:

- metadados (nome, descrição, versão)
- schema de inputs/outputs
- grafo de nós (nodes + edges)
- defaults de state variables

---

## 6) Passo a passo no WindSurf para criar os templates

1. Crie a pasta:
   - `src/domains/licitacoes/flows/templates/`
2. Crie arquivos:
   - `daily_monitor.template.json`
   - `on_demand_analyze.template.json`
3. Em cada template:
   - defina `inputs`
   - defina `state_defaults` (inclui `result`)
   - defina `nodes` e `edges`
4. Adicione um “registrador” (se a Agno tiver registry de templates):
   - `src/domains/licitacoes/flows/registry.py`
5. Faça o Flow Studio listar os templates:
   - via API `GET /flow-studio/templates?domain=licitacoes`

> Se a sua implementação atual do Flow Studio já tem outro formato, mantenha o mesmo:  
> o importante é **não deixar state sem default** e **não quebrar schema**.

---

## 7) UI (Next.js) — como expor o núcleo

Rotas sugeridas:

- `/flow-studio` → lista templates
- `/flow-studio/editor` → editor do grafo
- `/licitacoes` → painel do domínio (digest + buscas)
- `/licitacoes/item/[id]` → detalhes + análise

No MVP:

- uma tela simples `/licitacoes` com:
  - último digest
  - busca por palavra-chave
  - botão “analisar edital” (cola URL/texto)

---

## 8) Checklist de pronto (DoD) do Doc 06

- [ ] templates existem e são listados no Flow Studio
- [ ] `result` tem defaults e o fluxo salva sempre
- [ ] `daily_monitor` gera digest e persiste
- [ ] `on_demand_analyze` retorna analysis_pack rastreável

---

## 9) Próximo documento

**Doc 07 — `docs/TESTES_E_VALIDACAO_LICITACOES.md`**  
Vai trazer um plano de testes (golden files), avaliação, regressão e cenários de falha.

# Doc 05 — Agentes e Orquestração (PROMPT-OS) do Núcleo Licitações

> **Objetivo**  
> Definir **quem faz o quê** (agentes), **quais ferramentas podem usar**, **qual formato de saída** e **como o fluxo se encadeia** dentro da Agno.

---

## 1) Agentes (MVP) e responsabilidades

### 1.1 Watcher (Monitor)

**Responsabilidade:** coletar + normalizar + dedup + diff.

- **Input:** `SearchParams`, janela de datas, filtros
- **Output:** `{ items: LicitacaoItem[], changes: ChangeEvent[] }`
- **Tools permitidas:** `pncp_client`, `fetcher`, `dedup`, `diff`
- **Restrições:** sem interpretação jurídica; só coleta e sinaliza mudança

---

### 1.2 Triage (Priorização)

**Responsabilidade:** atribuir `priority` + `score` + razões + riscos preliminares.

- **Input:** `LicitacaoItem[]`
- **Output:** `TriageScore[]`
- **Tools:** (opcional) `keyword_rules`, `orgao_profile`, `history_db`
- **Restrições:** explicar motivos; não inventar fatos; se não tiver evidência, marcar como “incerto”

---

### 1.3 Analyst (Análise do edital)

**Responsabilidade:** extrair requisitos + produzir `AnalysisPack`.

- **Input:** `LicitacaoItem` + `raw_documents` (quando houver)
- **Output:** `AnalysisPack`
- **Tools:** `parser_pdf/html`, `rag_lei_14133`, `extractors` (prazos/anexos)
- **Restrições:** não emitir “parecer jurídico”; sempre citar evidências (trechos/páginas)

---

### 1.4 Compliance (Guardrails)

**Responsabilidade:** bloquear/limpar conteúdo perigoso e reforçar política.

- **Input:** texto do usuário + (opcional) saída do Analyst
- **Output:** `Pass/Fail` + mensagem segura
- **Tools:** guardrails internos, validação de schema, checks de injection
- **Restrições:** se falhar, responder com instrução segura (“remover PII”, “fornecer fonte”)

---

### 1.5 Orchestrator (Flow Controller)

**Responsabilidade:** encadear os agentes e publicar outputs.

- **Input:** `cfg` (FlowConfig) + `mode` (`monitor` / `analyze`)
- **Output:** `Digest` ou `AnalysisPack`
- **Tools:** chamar agentes + persistência + logs

---

## 2) Contrato de saída (para não quebrar o Flow)

### 2.1 Regra de ouro

Todo agente **sempre** retorna um objeto válido, mesmo em erro.

Formato recomendado:

```json
{
  "status": "ok|warning|error",
  "payload_json": "{}",
  "errors": []
}
```

- `status` default: `"init"`
- `payload_json` default: `"{}"`
- `errors` default: `[]`

> Isso evita o erro clássico: “não consigo salvar porque está vazio”.

---

## 3) PROMPT-OS — Template padrão por agente

Use este template como base (copiar/colar no WindSurf ao criar os prompts):

### 3.1 Estrutura (obrigatória)

1. **Objetivo + Critérios de sucesso**
2. **Público/uso**
3. **Contexto e definições**
4. **Dados de entrada (separados)**
5. **Papel (agent role)**
6. **Regras/restrições**
7. **Ferramentas permitidas**
8. **Formato de saída (schema-first)**
9. **Checklist de qualidade**
10. **Próximo passo**

---

## 4) Prompt pronto — Triage (exemplo)

**System/Instruction**

- **Objetivo:** Classificar oportunidades de licitação e devolver prioridade e riscos preliminares.
- **Critérios:** (a) `priority` e `score` coerentes, (b) `reasons` curtas e objetivas, (c) riscos com evidência quando possível.
- **Regras:** Não inventar dados. Se faltar informação, explicitar “incerto”.
- **Formato de saída:** `TriageScore[]` (JSON válido).

**Input:** lista de `LicitacaoItem[]`.

---

## 5) Prompt pronto — Analyst (exemplo)

- **Objetivo:** Extrair requisitos do edital e produzir `AnalysisPack`.
- **Ferramentas:** parser_pdf/html, rag_lei_14133.
- **Restrições:**
  - Não dar parecer jurídico.
  - Sempre incluir `evidences[]` com referência (página/trecho).
  - Se não achar trecho, registrar `evidences` como “não localizado”.

**Formato:** JSON (AnalysisPack) + `resumo_executivo_md` em Markdown.

---

## 6) Orquestração — Fluxos

### 6.1 `daily_monitor`

1. `Watcher.search()`
2. `Triage.score()`
3. Gerar `Digest` (top itens por prioridade)
4. Persistir `items`, `changes`, `scores`, `digest`

### 6.2 `on_demand_analyze`

1. `Compliance.check_input()`
2. `Watcher.get_detail()` + baixar anexos principais
3. `Analyst.analyze()`
4. `Compliance.check_output()` (opcional)
5. Persistir `analysis_pack`

---

## 7) Persistência e auditoria (mínimo)

Cada execução gera um `run_id` com:

- inputs (cfg)
- outputs (digest/analysis)
- fontes/evidências
- erros

---

## 8) Próximo documento

**Doc 06 — `docs/FLOWS_E_UI_FLOW_STUDIO.md`**  
Vai descrever a implementação do Flow Studio (templates, variáveis de estado, modos, validação e telas).

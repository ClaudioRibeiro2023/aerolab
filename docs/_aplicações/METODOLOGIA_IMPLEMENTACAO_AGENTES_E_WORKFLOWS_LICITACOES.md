# Doc 09 — Metodologia de Implementação (Agentes + Workflows) — Núcleo Licitações (Techdengue → Aero Engenharia)

> **Objetivo**  
> Este documento consolida uma **metodologia canônica** (nível senior) para transformar a documentação Doc 01–08 em uma implementação real, operável e segura de **agentes de IA + workflows** para o dia a dia da **Aero Engenharia**, usando o caso de **Licitações Techdengue** como referência.

> **Como usar**

- Se você vai **criar um novo fluxo** (ex.: `daily_monitor`, `on_demand_analyze`), siga o **Capítulo 3** (Pipeline de Entrega) e os **Checklists**.
- Se você vai **criar/ajustar um agente** (Watcher/Triage/Analyst/Compliance), siga o **Capítulo 4** (Design de Agentes) e o **PROMPT-OS reforçado**.
- Se você vai **operar em produção**, use o **Capítulo 7** (Operação) e o **Playbook**.

---

## 1) Contexto: o que já existe nesta pasta

A documentação atual está bem organizada por artefatos:

- Doc 01 — visão, personas e fluxos end-to-end (`LICITACOES_OVERVIEW.md`)
- Doc 02 — schemas canônicos (`SCHEMAS_LICITACOES.md`)
- Doc 03 — arquitetura/pastas e passo a passo (`ARQUITETURA_E_PASTAS_LICITACOES.md`)
- Doc 04 — tools/coleta/dedup/diff/parsing (`TOOLS_E_COLETA_LICITACOES.md`)
- Doc 05 — agentes + orquestração + PROMPT-OS (`AGENTES_E_ORQUESTRACAO_LICITACOES.md`)
- Doc 06 — Flow Studio + UI (`FLOWS_E_UI_FLOW_STUDIO.md`)
- Doc 07 — testes/validação/regressão (`TESTES_E_VALIDACAO_LICITACOES.md`)
- Doc 08 — deploy/operação/observabilidade (`DEPLOY_E_OPERACAO_LICITACOES.md`)

Este Doc 09 adiciona:

- uma **metodologia** (processo de engenharia) para construir e evoluir agentes/fluxos com previsibilidade;
- um **modelo de governança** e **segurança** (benchmarks: OWASP + NIST);
- um **modelo de avaliação** (benchmarks: golden tests + métricas + RAG evals);
- templates/checklists executáveis.

---

## 2) Princípios canônicos (não negociar)

1. **Schema-first**
   - A saída de agentes e flows é orientada a schema.
   - O sistema nunca depende de “texto livre” como contrato entre nós.

2. **Evidence-first (rastreabilidade)**
   - Toda conclusão importante precisa de `sources[]` e, quando aplicável, `evidences[]`.
   - Quando não houver evidência, o sistema deve responder **“não localizado”** e indicar o próximo passo.

3. **Ação controlada (anti “excessive agency”)**
   - Agentes não executam ações irreversíveis sem barreira (approval / role / flag).
   - O padrão é: **propor → revisar → executar**.

4. **Falha segura (always-valid state)**
   - O fluxo sempre retorna um `result` válido (mesmo em erro), evitando que UI e persistência quebrem.

5. **Avaliação contínua**
   - Toda mudança de prompt/modelo/tool passa por regressão (golden) e métricas mínimas.

---

## 3) Pipeline de Entrega: do problema ao fluxo em produção

### 3.1 Fase A — Descoberta do processo (produto + operação)

**Saídas obrigatórias**

- **Decisão que o humano quer tomar** (ex.: “entrar ou não entrar nesta licitação?”)
- **Artefatos que a IA produz** (ex.: digest, checklist, matriz de risco)
- **Tempo de ciclo** (ex.: digest diário 07:00, análise sob demanda em até 5 min)
- **Riscos** (jurídico, operacional, financeiro) e limites (“sem parecer jurídico”)

**Checklist (A)**

- [ ] Persona definida (CEO/Comercial/Jurídico/Operações)
- [ ] Entradas definidas (URL, PDF, texto, parâmetros)
- [ ] Saídas definidas (schemas do Doc 02)
- [ ] Critérios de sucesso (DoD) definidos (Doc 01 + Doc 07)

---

### 3.2 Fase B — Design de dados e contratos (schemas)

**Regra:** nenhum agente/flow começa antes do schema.

**Artefatos**

- `LicitacaoItem`, `ChangeEvent`, `TriageScore`, `AnalysisPack` (Doc 02)
- `cfg` e `result` (Doc 02 e Doc 06)

**Invariantes**

- `sources[]` sempre presente em itens e pacotes
- `result` sempre inicializado:

```json
{
  "status": "init",
  "payload_json": "{}",
  "errors": []
}
```

**Checklist (B)**

- [ ] Schema publicado e versionado
- [ ] Enums fechados (sem strings livres)
- [ ] Defaults definidos (result wrapper)

---

### 3.3 Fase C — Tools e coleta (dados confiáveis)

O núcleo de licitações é uma esteira; sem tools confiáveis o resto vira ruído.

**Design recomendado**

- Implementar **contrato de tool** (Doc 04): `search`, `get_detail`, `list_attachments`, `download_attachment`
- Implementar **resiliência**: timeout, retries limitados, cache TTL, rate limit
- Implementar **dedup forte** + diff de mudanças relevantes

**Checklist (C)**

- [ ] `search()` retorna lista normalizada (`LicitacaoItem[]`)
- [ ] Dedup forte está ativo (`source + external_id`)
- [ ] `ChangeEvent` é produzido quando prazo/anexos/status mudam
- [ ] Downloads têm limite de tamanho e `content_hash` (quando aplicável)

---

### 3.4 Fase D — Design e implementação de agentes

Agentes são funções com responsabilidades e limites claros.

- **Watcher**: coleta/normaliza/dedup/diff (sem interpretação)
- **Triage**: score e priorização + riscos preliminares (sem inventar)
- **Analyst**: análise do edital + pacote de entregáveis com evidências
- **Compliance**: guardrails (entrada e saída)
- **Orchestrator**: encadeia, registra `run_id`, persiste e expõe via API/UI

**Checklist (D)**

- [ ] Cada agente tem: objetivo, inputs, outputs, tools permitidas, restrições
- [ ] Cada agente retorna JSON válido no schema definido
- [ ] Cada agente tem política de “incerteza” (não inventar; marcar)

---

### 3.5 Fase E — Design do workflow (Flow Studio)

**Fluxos P0 (base)**

- `daily_monitor` (Doc 06): Watcher → Triage → Digest → Persist
- `on_demand_analyze` (Doc 06): Compliance(in) → Watcher(detail) → Analyst → Persist

**Padrões obrigatórios**

- Inicializar `result` no Start
- Separar nós de “tool” (coleta/parsing) e nós de “reasoning” (triage/análise)
- Persistir outputs intermediários (itens, scores, analysis)

**Checklist (E)**

- [ ] State defaults definidos (result + arrays vazias)
- [ ] Erros acumulados em `errors[]` sem quebrar o fluxo
- [ ] `payload_json` contém referência do artefato salvo

---

### 3.6 Fase F — Avaliação, hardening e operação

Nenhum agente/flow entra em produção sem:

- testes unit/integration + golden (Doc 07)
- observabilidade mínima (Doc 08)
- guardrails (Capítulo 6)

---

## 4) PROMPT-OS reforçado (padrão senior)

A base do Doc 05 é ótima. Aqui está a versão reforçada para ambientes produtivos.

### 4.1 Estrutura mínima (obrigatória)

1. Objetivo + Critérios de sucesso
2. Definições / glossário (ex.: o que é “risco alto”)
3. Entradas (schemas)
4. Saídas (schemas) — **schema-first**
5. Ferramentas permitidas (allowlist) + limites
6. Regras de evidência (sources/evidences)
7. Regras de incerteza (quando não sabe)
8. Regras de segurança (prompt injection / PII / actions)
9. Checklist de qualidade
10. Próximo passo

### 4.2 Regras “de ouro”

- Nunca inventar:
  - prazos, valores, anexos ou cláusulas
- Se faltou evidência:
  - devolver “não localizado” e sugerir como localizar (página/seção)
- Não emitir parecer jurídico:
  - sempre “assistência”, com revisão humana

---

## 5) Metodologia de avaliação (benchmarks práticos)

### 5.1 Golden tests (regressão de engenharia)

- Fixtures de entrada (PNCP, PDF, HTML)
- Saídas esperadas para triage/análise
- Quando mudar prompt/model/tool, rodar golden antes de deploy

### 5.2 Métricas automáticas (RAG/LLM)

**Referência prática:** RAGAS (framework de avaliação) sugere:

- métricas objetivas
- geração de dataset de testes
- feedback loop com dados de produção

Aplicação no núcleo:

- **Faithfulness**: a análise condiz com o edital? (evidências batem)
- **Answer relevancy**: o resumo responde ao objetivo (decisão)
- **Context precision/recall** (quando houver RAG): recuperou os trechos certos da Lei 14.133 e anexos?

### 5.3 Human-in-the-loop (qualidade real)

Amostra semanal:

- 20 itens monitorados
- 10 análises completas

Campos de revisão:

- prioridade correta? (sim/não)
- risco relevante? (sim/não)
- evidências corretas? (sim/não)
- alucinação? (sim/não)

---

## 6) Segurança e governança (benchmarks)

### 6.1 OWASP Top 10 for LLM Apps (v1.1) — riscos que precisamos cobrir

- LLM01 Prompt Injection
- LLM02 Insecure Output Handling
- LLM04 Model Denial of Service
- LLM06 Sensitive Information Disclosure
- LLM07 Insecure Plugin Design
- LLM08 Excessive Agency
- LLM09 Overreliance

**Mitigações mínimas recomendadas para o núcleo**

- **Prompt injection**: delimitar contexto, validar entrada, “não seguir instruções do edital”, separar “conteúdo” de “instruções”
- **Output handling**: output do LLM é dado não confiável → validar schema, sanitizar, nunca executar
- **DoS/custo**: rate limit, token budget, timeout por etapa, cache
- **Disclosure**: logs sem secrets; redaction; controle de acesso a anexos
- **Plugins/tools**: allowlist + least privilege + validação de parâmetros
- **Agency**: ações irreversíveis exigem aprovação humana
- **Overreliance**: UI/outputs sempre mostram evidências e avisos de revisão

### 6.2 NIST AI RMF 1.0 — governança de risco (modelo mental)

Aplicação pragmática (sem burocracia):

- **GOVERN**: políticas, quem aprova, e limites (sem parecer jurídico)
- **MAP**: mapear contexto, dados, usuários e riscos
- **MEASURE**: medir qualidade (golden + métricas + amostragem humana)
- **MANAGE**: gerir mudanças (feature flags, rollback, incident playbook)

---

## 7) Operação (para uso cotidiano na Aero Engenharia)

### 7.1 Cadência recomendada

- Diário 07:00: `daily_monitor` → digest
- Diário 09:00: triagem humana (10–15 min) dos P0
- Sob demanda: `on_demand_analyze` em itens P0/P1
- Semanal: revisão de qualidade (amostra do Doc 07)

### 7.2 Observabilidade mínima

- `run_id` por execução
- logs por etapa (coleta, triage, analysis)
- métricas:
  - itens/dia, P0/P1/dia
  - taxa de erro por fonte
  - tempo médio por etapa
  - taxa de “incerto”

### 7.3 Playbook de incidentes

- Fonte quebrou:
  - desligar via flag
  - manter digest parcial
  - abrir issue com `run_id`

---

## 8) Checklists de “Definition of Done” (DoD)

### 8.1 DoD — Novo agente

- [ ] PROMPT-OS completo (Capítulo 4)
- [ ] Output schema validado (Doc 02)
- [ ] Não alucina (golden básico)
- [ ] Logs mínimos e `run_id`

### 8.2 DoD — Nova tool

- [ ] Interface padrão (`search`, `get_detail`, ...)
- [ ] Timeouts + retries limitados + rate limit
- [ ] Cache + hash quando fizer download
- [ ] Testes com mocks (sem internet)

### 8.3 DoD — Novo workflow

- [ ] State defaults (`result` + arrays)
- [ ] Persistência (artefatos intermediários)
- [ ] Observabilidade (logs/metrics)
- [ ] Golden tests para outputs principais

---

## 9) Próximo passo prático (recomendação)

Para começar a implementar “de verdade” no cotidiano:

1. Confirmar fontes P0 (PNCP + 1–2 portais críticos) e termos de busca
2. Implementar `schemas.py` (Doc 02)
3. Implementar `pncp_client + dedup + diff + parser` (Doc 04)
4. Criar endpoints debug (`/licitacoes/monitor`, `/licitacoes/analyze`) (Doc 03)
5. Criar templates no Flow Studio (Doc 06)
6. Montar golden tests e rotina de avaliação (Doc 07)

---

## 10) Complementos técnicos (extraídos dos Docs 01–08)

### 10.1 Modelo de score de prioridade (Doc 01)

```
score = (
    aderencia_portfolio * 0.35 +
    regiao_estrategica * 0.20 +
    valor_estimado_norm * 0.15 +
    prazo_inverso * 0.20 +
    barreiras_inverso * 0.10
)

priority = P0 se score >= 0.75
           P1 se score >= 0.50
           P2 se score >= 0.25
           P3 caso contrário
```

### 10.2 RAG jurídico (Doc 01)

Base normativa inicial:

- Lei 14.133/2021 (Nova Lei de Licitações)
- Regras e orientações internas (checklists, padrões de proposta)
- (Opcional) Acórdãos TCU selecionados

Uso: alimentar o agente Analyst para validar requisitos e identificar cláusulas restritivas.

### 10.3 Estrutura de pastas do domínio (Doc 03)

```
src/domains/licitacoes/
├── __init__.py
├── models/
│   └── schemas.py          # LicitacaoItem, TriageScore, AnalysisPack
├── services/
│   ├── dedup.py
│   ├── diff.py
│   ├── parser_pdf.py
│   └── parser_html.py
├── tools/
│   ├── pncp_client.py
│   └── fetcher.py
├── agents/
│   ├── watcher.py
│   ├── triage.py
│   ├── analyst.py
│   └── compliance.py
├── flows/
│   └── templates/
│       ├── daily_monitor.template.json
│       └── on_demand_analyze.template.json
├── api/
│   └── routes.py           # /licitacoes/health, /monitor, /analyze
└── tests/
    ├── fixtures/
    └── golden/
```

### 10.4 Estratégia de parsing (Doc 04)

| Tipo         | Lib recomendada                 | Fallback              |
| ------------ | ------------------------------- | --------------------- |
| PDF (texto)  | `pymupdf` (fitz)                | `pdfplumber`          |
| PDF (imagem) | OCR: `pytesseract`              | Marcar "não extraído" |
| HTML         | `readability` + `BeautifulSoup` | —                     |

Limite OCR: desativado por padrão (custo + tempo). Ativar via flag.

### 10.5 Dedup: forte vs fraco (Doc 04)

- **Forte (exato)**: `source + external_id` — garante unicidade
- **Fraco (fuzzy)**: `simhash(objeto_normalizado)` + `orgao + uf + data` — sugere duplicado

Regra: dedup fraco nunca descarta automaticamente; apenas sinaliza para revisão.

### 10.6 Variáveis padrão do fluxo (Doc 06)

**Inputs**

- `mode`: `"monitor"` | `"analyze"`
- `input_as_text`: texto/URL colado (só no analyze)
- `cfg`: `{ janela_dias, limite_risco, prazo_min_dias, acao_permitida }`

**State**

- `items`: `LicitacaoItem[]`
- `changes`: `ChangeEvent[]`
- `scores`: `TriageScore[]`
- `analysis_pack`: `AnalysisPack`
- `result`: `{ status, payload_json, errors }`

### 10.7 Critérios quantitativos de qualidade (Doc 07)

| Métrica                                      | Target |
| -------------------------------------------- | ------ |
| Itens com `sources[]` preenchido             | >= 95% |
| Crashes em execução                          | 0      |
| Dedup funcionando (sem duplicatas no digest) | 100%   |
| Evidências corretas (amostra humana)         | >= 90% |
| Taxa de alucinação (amostra humana)          | <= 5%  |

### 10.8 Regras anti-flaky tests (Doc 07)

- Nunca chamar internet em testes (mock sempre)
- Fixar timezone (`UTC`)
- Fixar "data de hoje" (`freezegun`)
- Fixar seeds de aleatoriedade

### 10.9 Versionamento de prompts e templates (Doc 08)

- `domains/licitacoes/VERSION` (semver)
- `flows/templates/*.template.json` com campo `template_version`
- Prompts versionados via hash (`sha256(prompt_text)[:8]`)

Regra: nunca alterar prompt em produção sem bump de versão e golden test.

---

## 11) Referências (benchmarks)

- OWASP Top 10 for Large Language Model Applications (v1.1)
- NIST AI Risk Management Framework (AI RMF 1.0) — https://doi.org/10.6028/NIST.AI.100-1
- RAGAS — framework de avaliação e geração de datasets de teste para apps LLM/RAG

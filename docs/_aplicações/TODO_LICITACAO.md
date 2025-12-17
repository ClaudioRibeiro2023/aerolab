# TODO — Implementação do Núcleo Licitações (Techdengue → Aero Engenharia)

> **Objetivo deste arquivo**  
> Guia executável para implementar os agentes e workflows de licitações no AeroLab.  
> Cada item tem status, responsável sugerido e referência aos docs.

---

## Legenda de status

- `[ ]` Pendente
- `[~]` Em progresso
- `[x]` Concluído
- `[!]` Bloqueado (ver notas)

---

## Fase 0 — Configuração inicial ✅

### 0.1 Ambiente e dependências

- [x] Confirmar que backend (FastAPI) e frontend (Next.js) estão rodando
- [x] Adicionar dependências Python: `pymupdf`, `pdfplumber`, `httpx`, `deepdiff`
- [ ] Adicionar dependências Python (opcionais): `pytesseract` (OCR), `simhash`
- [x] Criar arquivo `domains/licitacoes/VERSION` com `0.1.0`

### 0.2 Configuração de fontes e filtros

- [ ] **Definir fontes P0**: PNCP (obrigatório) + portais adicionais (se aplicável)
- [ ] **Definir filtros iniciais**:
  - UFs: `_______________`
  - Municípios: `_______________`
  - Palavras-chave: `dengue, arbovirose, drone, geotecnologia, geoprocessamento, saúde pública`
  - Modalidades: `pregao_eletronico, concorrencia`
- [ ] **Definir responsável pela triagem diária**: `_______________`

---

## Fase 1 — Scaffolding do domínio (Doc 03) ✅

### 1.1 Estrutura de pastas

- [x] Criar `apps/api/src/domains/licitacoes/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/models/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/services/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/tools/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/agents/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/flows/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/api/__init__.py`
- [x] Criar `apps/api/src/domains/licitacoes/tests/__init__.py`

---

## Fase 2 — Schemas (Doc 02) ✅

### 2.1 Implementar schemas Pydantic

- [x] Criar `models/schemas.py` com:
  - [x] `SourceRef`
  - [x] `LicitacaoItem`
  - [x] `ChangeEvent`
  - [x] `TriageScore`
  - [x] `AnalysisPack`
  - [x] `FlowConfig` (cfg)
  - [x] `FlowResult` (result wrapper)
- [x] Criar `models/enums.py` com:
  - [x] `Modalidade`
  - [x] `Situacao`
  - [x] `Prioridade` (P0/P1/P2/P3)
  - [x] `NivelRisco` (baixo/medio/alto/critico)

### 2.2 Validação ✅ (19 testes passando)

- [x] Testar instanciação de `LicitacaoItem` com dados mock
- [x] Garantir que `sources[]` é obrigatório
- [x] Garantir que `result` tem defaults válidos

---

## Fase 3 — Tools e coleta (Doc 04) ✅

### 3.1 PNCP Client

- [x] Criar `tools/pncp_client.py` com:
  - [x] `search(params) -> list[LicitacaoItem]`
  - [x] `get_detail(external_id) -> LicitacaoItem`
  - [x] `list_attachments(external_id) -> list[AttachmentRef]`
- [x] Implementar resiliência: timeout (15s), retries (2), backoff
- [x] Normalizar resposta para `LicitacaoItem` com `sources[]` preenchido

### 3.2 Fetcher e download

- [x] Criar `tools/fetcher.py` com:
  - [x] `fetch_url(url) -> str` (HTML)
  - [x] `download_file(url) -> RawDocumentRef` com `content_hash`
- [x] Implementar cache TTL (6h)
- [x] Limite de tamanho: 50MB

### 3.3 Parsing

- [ ] Criar `services/parser_pdf.py` com:
  - [ ] `parse(file_path) -> ParsedDocument`
  - [ ] Retornar `text`, `page_map`, `metadata`
- [ ] Criar `services/parser_html.py` com:
  - [ ] `parse(html) -> ParsedDocument`

### 3.4 Dedup e diff ✅ (17 testes passando)

- [x] Criar `services/dedup.py` com:
  - [x] `dedup_strong(items) -> list[LicitacaoItem]` (source + external_id)
  - [x] `dedup_fuzzy(items) -> list[DuplicateSuggestion]` (simhash)
- [x] Criar `services/diff.py` com:
  - [x] `detect_changes(old, new) -> list[ChangeEvent]`

---

## Fase 4 — Agentes (Doc 05) ✅

### 4.1 Watcher ✅

- [x] Criar `agents/watcher.py`
- [x] Input: `SearchParams`
- [x] Output: `{ items: LicitacaoItem[], changes: ChangeEvent[] }`
- [x] Tools: `pncp_client`, `fetcher`, `dedup`, `diff`
- [x] Restrições: sem interpretação jurídica

### 4.2 Triage ✅

- [x] Criar `agents/triage.py`
- [x] Input: `LicitacaoItem[]`
- [x] Output: `TriageScore[]`
- [x] Implementar fórmula de score (Doc 09, seção 10.1)
- [x] Restrições: explicar motivos; não inventar

### 4.3 Analyst ✅

- [x] Criar `agents/analyst.py`
- [x] Input: `LicitacaoItem` + `raw_documents`
- [x] Output: `AnalysisPack`
- [x] Tools: `parser_pdf`, `parser_html`, `rag_lei_14133` (futuro)
- [x] Restrições: não emitir parecer jurídico; citar evidências

### 4.4 Compliance ✅

- [x] Criar `agents/compliance.py`
- [x] Input: texto/output de outro agente
- [x] Output: `Pass/Fail` + mensagem
- [x] Validações: PII, injection, schema

### 4.5 Testes ✅ (21 testes de agentes passando)

- [x] Testes Triage: score, priorização, riscos
- [x] Testes Analyst: análise, checklists, oportunidades
- [x] Testes Compliance: PII, injection, sanitização

---

## Fase 5 — API (Doc 03) ✅

### 5.1 Endpoints

- [x] Criar `api/routes.py` com:
  - [x] `GET /licitacoes/health`
  - [x] `POST /licitacoes/monitor` (debug)
  - [x] `POST /licitacoes/analyze` (debug)
  - [x] `GET /licitacoes/digest/{date}`
  - [x] `GET /licitacoes/search` (busca por keyword)
- [x] Registrar router no `server.py`

### 5.2 Validação

- [x] Endpoints aparecem no Swagger (`/docs`)
- [x] Payloads validam schema

---

## Fase 6 — Flows (Doc 06) ✅

### 6.1 Templates ✅

- [x] Criar `flows/templates/daily_monitor.template.json`
- [x] Criar `flows/templates/on_demand_analyze.template.json`
- [x] Definir `state_defaults` com `result` inicializado

### 6.2 Orquestração ✅

- [x] Implementar runner para `daily_monitor`:
  1. Watcher.search()
  2. Triage.score()
  3. Gerar Digest
  4. Persistir
- [x] Implementar runner para `on_demand_analyze`:
  1. Compliance.check_input()
  2. Watcher.get_detail()
  3. Analyst.analyze()
  4. Persistir

---

## Fase 7 — Testes (Doc 07) ✅

### 7.1 Fixtures ✅

- [x] Criar `tests/fixtures/pncp/sample_001.json`
- [x] Criar `tests/fixtures/pncp/sample_002.json`
- [x] Criar `tests/fixtures/pncp/sample_003.json`

### 7.2 Golden tests ✅ (9 testes)

- [x] Criar `tests/golden/triage/sample_001.expected.json`
- [x] Criar `tests/golden/triage/sample_002.expected.json`
- [x] Criar `tests/golden/triage/sample_003.expected.json`
- [x] Testes de normalização PNCP
- [x] Testes de batch triage
- [x] Testes de analyst

### 7.3 Unit tests ✅ (57 testes anteriores)

- [x] `test_dedup_strong()`
- [x] `test_diff_deadline_changed()`
- [x] `test_pncp_normalization_has_sources()`

### 7.4 Regras anti-flaky ✅

- [x] Usar mocks para chamadas HTTP
- [x] Fixtures locais sem dependência de rede

---

## Fase 8 — Operação (Doc 08) ✅

### 8.1 Agendamento ✅

- [x] Configurar job `daily_monitor` para rodar 07:00 (`scheduler.py`)
- [x] Implementar lock para evitar execução duplicada
- [x] Implementar retry com limite (3x)

### 8.2 Observabilidade ✅

- [x] Gerar `run_id` por execução
- [x] Logs estruturados por etapa (`observability.py`)
- [x] Métricas: itens/dia, P0/dia, taxa de erro
- [x] FlowObserver para callbacks

### 8.3 UI (Studio)

- [ ] Criar página `/licitacoes` com:
  - [ ] Último digest
  - [ ] Busca por palavra-chave
  - [ ] Botão "Analisar edital"
- [ ] Criar página `/licitacoes/item/[id]` com detalhes

---

## Fase 9 — RAG jurídico (Doc 01) — P1

- [ ] Ingerir Lei 14.133/2021 no RAG
- [ ] Ingerir checklists e padrões internos
- [ ] (Opcional) Ingerir acórdãos TCU selecionados
- [ ] Integrar no agente Analyst

---

## Fase 10 — Validação final e go-live

### 10.1 Checklist de qualidade (Doc 07/09)

- [ ] > = 95% dos itens com `sources[]`
- [ ] 0 crashes em execução
- [ ] Dedup funcionando (sem duplicatas)
- [ ] Evidências corretas (amostra >= 90%)
- [ ] Taxa de alucinação <= 5%

### 10.2 Go-live

- [ ] Deploy em ambiente de produção
- [ ] Documentar playbook de incidentes
- [ ] Comunicar equipe sobre cadência (digest 07:00, triagem 09:00)

---

## Referências

- **Doc 01**: `LICITACOES_OVERVIEW.md`
- **Doc 02**: `SCHEMAS_LICITACOES.md`
- **Doc 03**: `ARQUITETURA_E_PASTAS_LICITACOES.md`
- **Doc 04**: `TOOLS_E_COLETA_LICITACOES.md`
- **Doc 05**: `AGENTES_E_ORQUESTRACAO_LICITACOES.md`
- **Doc 06**: `FLOWS_E_UI_FLOW_STUDIO.md`
- **Doc 07**: `TESTES_E_VALIDACAO_LICITACOES.md`
- **Doc 08**: `DEPLOY_E_OPERACAO_LICITACOES.md`
- **Doc 09**: `METODOLOGIA_IMPLEMENTACAO_AGENTES_E_WORKFLOWS_LICITACOES.md`

---

## Histórico de atualizações

| Data       | Versão | Descrição              |
| ---------- | ------ | ---------------------- |
| 2025-12-17 | 0.1.0  | Versão inicial do TODO |

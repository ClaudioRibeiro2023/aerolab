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

## Fase 0 — Configuração inicial

### 0.1 Ambiente e dependências

- [ ] Confirmar que backend (FastAPI) e frontend (Next.js) estão rodando
- [ ] Adicionar dependências Python: `pymupdf`, `pdfplumber`, `httpx`, `deepdiff`
- [ ] Adicionar dependências Python (opcionais): `pytesseract` (OCR), `simhash`
- [ ] Criar arquivo `domains/licitacoes/VERSION` com `0.1.0`

### 0.2 Configuração de fontes e filtros

- [ ] **Definir fontes P0**: PNCP (obrigatório) + portais adicionais (se aplicável)
- [ ] **Definir filtros iniciais**:
  - UFs: `_______________`
  - Municípios: `_______________`
  - Palavras-chave: `dengue, arbovirose, drone, geotecnologia, geoprocessamento, saúde pública`
  - Modalidades: `pregao_eletronico, concorrencia`
- [ ] **Definir responsável pela triagem diária**: `_______________`

---

## Fase 1 — Scaffolding do domínio (Doc 03)

### 1.1 Estrutura de pastas

- [ ] Criar `apps/api/src/domains/licitacoes/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/models/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/services/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/tools/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/agents/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/flows/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/api/__init__.py`
- [ ] Criar `apps/api/src/domains/licitacoes/tests/__init__.py`

---

## Fase 2 — Schemas (Doc 02)

### 2.1 Implementar schemas Pydantic

- [ ] Criar `models/schemas.py` com:
  - [ ] `SourceRef`
  - [ ] `LicitacaoItem`
  - [ ] `ChangeEvent`
  - [ ] `TriageScore`
  - [ ] `AnalysisPack`
  - [ ] `FlowConfig` (cfg)
  - [ ] `FlowResult` (result wrapper)
- [ ] Criar `models/enums.py` com:
  - [ ] `Modalidade`
  - [ ] `Situacao`
  - [ ] `Prioridade` (P0/P1/P2/P3)
  - [ ] `NivelRisco` (baixo/medio/alto/critico)

### 2.2 Validação

- [ ] Testar instanciação de `LicitacaoItem` com dados mock
- [ ] Garantir que `sources[]` é obrigatório
- [ ] Garantir que `result` tem defaults válidos

---

## Fase 3 — Tools e coleta (Doc 04)

### 3.1 PNCP Client

- [ ] Criar `tools/pncp_client.py` com:
  - [ ] `search(params) -> list[LicitacaoItem]`
  - [ ] `get_detail(external_id) -> LicitacaoItem`
  - [ ] `list_attachments(external_id) -> list[AttachmentRef]`
- [ ] Implementar resiliência: timeout (15s), retries (2), backoff
- [ ] Normalizar resposta para `LicitacaoItem` com `sources[]` preenchido

### 3.2 Fetcher e download

- [ ] Criar `tools/fetcher.py` com:
  - [ ] `fetch_url(url) -> str` (HTML)
  - [ ] `download_file(url) -> RawDocumentRef` com `content_hash`
- [ ] Implementar cache TTL (6h)
- [ ] Limite de tamanho: 50MB

### 3.3 Parsing

- [ ] Criar `services/parser_pdf.py` com:
  - [ ] `parse(file_path) -> ParsedDocument`
  - [ ] Retornar `text`, `page_map`, `metadata`
- [ ] Criar `services/parser_html.py` com:
  - [ ] `parse(html) -> ParsedDocument`

### 3.4 Dedup e diff

- [ ] Criar `services/dedup.py` com:
  - [ ] `dedup_strong(items) -> list[LicitacaoItem]` (source + external_id)
  - [ ] `dedup_fuzzy(items) -> list[DuplicateSuggestion]` (simhash)
- [ ] Criar `services/diff.py` com:
  - [ ] `detect_changes(old, new) -> list[ChangeEvent]`

---

## Fase 4 — Agentes (Doc 05)

### 4.1 Watcher

- [ ] Criar `agents/watcher.py`
- [ ] Input: `SearchParams`
- [ ] Output: `{ items: LicitacaoItem[], changes: ChangeEvent[] }`
- [ ] Tools: `pncp_client`, `fetcher`, `dedup`, `diff`
- [ ] Restrições: sem interpretação jurídica

### 4.2 Triage

- [ ] Criar `agents/triage.py`
- [ ] Input: `LicitacaoItem[]`
- [ ] Output: `TriageScore[]`
- [ ] Implementar fórmula de score (Doc 09, seção 10.1)
- [ ] Restrições: explicar motivos; não inventar

### 4.3 Analyst

- [ ] Criar `agents/analyst.py`
- [ ] Input: `LicitacaoItem` + `raw_documents`
- [ ] Output: `AnalysisPack`
- [ ] Tools: `parser_pdf`, `parser_html`, `rag_lei_14133` (futuro)
- [ ] Restrições: não emitir parecer jurídico; citar evidências

### 4.4 Compliance

- [ ] Criar `agents/compliance.py`
- [ ] Input: texto/output de outro agente
- [ ] Output: `Pass/Fail` + mensagem
- [ ] Validações: PII, injection, schema

---

## Fase 5 — API (Doc 03)

### 5.1 Endpoints

- [ ] Criar `api/routes.py` com:
  - [ ] `GET /licitacoes/health`
  - [ ] `POST /licitacoes/monitor` (debug)
  - [ ] `POST /licitacoes/analyze` (debug)
  - [ ] `GET /licitacoes/digest/{date}`
- [ ] Registrar router no `server.py`

### 5.2 Validação

- [ ] Endpoints aparecem no Swagger (`/docs`)
- [ ] Payloads validam schema

---

## Fase 6 — Flows (Doc 06)

### 6.1 Templates

- [ ] Criar `flows/templates/daily_monitor.template.json`
- [ ] Criar `flows/templates/on_demand_analyze.template.json`
- [ ] Definir `state_defaults` com `result` inicializado

### 6.2 Orquestração

- [ ] Implementar runner para `daily_monitor`:
  1. Watcher.search()
  2. Triage.score()
  3. Gerar Digest
  4. Persistir
- [ ] Implementar runner para `on_demand_analyze`:
  1. Compliance.check_input()
  2. Watcher.get_detail()
  3. Analyst.analyze()
  4. Persistir

---

## Fase 7 — Testes (Doc 07)

### 7.1 Fixtures

- [ ] Criar `tests/fixtures/pncp/sample_001.json`
- [ ] Criar `tests/fixtures/editais/sample_001.pdf`

### 7.2 Golden tests

- [ ] Criar `tests/golden/triage/sample_001.expected.json`
- [ ] Criar `tests/golden/analysis/sample_001.expected.json`

### 7.3 Unit tests

- [ ] `test_dedup_strong()`
- [ ] `test_diff_deadline_changed()`
- [ ] `test_parser_pdf_extracts_text()`
- [ ] `test_pncp_normalization_has_sources()`

### 7.4 Regras anti-flaky

- [ ] Configurar `freezegun` para fixar data
- [ ] Configurar timezone UTC
- [ ] Usar mocks para chamadas HTTP

---

## Fase 8 — Operação (Doc 08)

### 8.1 Agendamento

- [ ] Configurar job `daily_monitor` para rodar 07:00
- [ ] Implementar lock para evitar execução duplicada
- [ ] Implementar retry com limite (3x)

### 8.2 Observabilidade

- [ ] Gerar `run_id` por execução
- [ ] Logs estruturados por etapa
- [ ] Métricas: itens/dia, P0/dia, taxa de erro

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

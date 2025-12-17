# Doc 04 — Tools e Coleta (PNCP/Portais) + Dedup + Diff

> **Objetivo**  
> Definir o “motor de coleta” do núcleo.  
> Aqui está o que transforma a Agno em uma esteira confiável de monitoramento: **coletar com limites**, normalizar, deduplicar e detectar mudança.

---

## 1) Filosofia de coleta (importante)

1. **Preferir fonte oficial com API** (quando existe).
2. **Scraping só quando inevitável** e sempre com:
   - rate limit,
   - backoff,
   - user-agent,
   - cache,
   - logs mínimos,
   - e possibilidade de desligar/limitar por ambiente.
3. **Rastreabilidade**: todo item produzido tem `sources[]` e, se baixou arquivo, tem `content_hash`.

---

## 2) Contrato de Tool (interface padrão)

Crie um contrato interno (Protocol / ABC) para cada fonte:

### 2.1 `LicitacoesSourceTool` (pseudo-interface)

- `search(params) -> list[LicitacaoItem]`
- `get_detail(external_id) -> LicitacaoItem`
- `list_attachments(external_id) -> list[AttachmentRef]`
- `download_attachment(url) -> RawDocumentRef`

> Isso permite: PNCP hoje, “Portal X” amanhã, sem reescrever o core.

---

## 3) PNCP (integração recomendada)

### 3.1 Parâmetros de busca (genérico)

Sem travar em endpoints específicos (porque podem mudar), defina uma camada de `SearchParams` que suporte:

- `q` (texto): termos como “dengue”, “drone”, “geoprocessamento”, “arbovirose”
- `uf`, `municipio`
- `orgao` / `cnpj` (se aplicável)
- `modalidade`
- `data_publicacao_ini`, `data_publicacao_fim`
- `status`
- `pagina`, `tamanho_pagina`

### 3.2 Normalização

O client PNCP deve mapear o retorno para `LicitacaoItem`, preenchendo no mínimo:

- `id` (com namespace `lic:pncp:`)
- `orgao`, `uf`, `modalidade`, `objeto`, `status`, `publicado_em`
- `sources[]` com `source="pncp"` e `url` do item

### 3.3 Resiliência

- timeouts curtos (ex.: 10–20s)
- retries limitados (ex.: 2)
- circuit breaker simples (se 5 falhas seguidas, “pausa” por N minutos)

---

## 4) Fetchers (HTML/PDF) e Cache

### 4.1 `fetch_url(url) -> str`

- cache por URL + ETag/Last-Modified quando possível
- fallback para cache TTL (ex.: 6h)

### 4.2 `download_file(url) -> bytes`

- salva em storage (S3/local) e retorna `raw_ref` + `content_hash`
- limita tamanho máximo (ex.: 50–100MB no MVP)

### 4.3 Storage

No MVP, pode ser:

- local: `./data/raw_documents/`
  Depois:
- S3 compatível: `s3://agno-raw/...`

---

## 5) Parsing (extração do edital/anexos)

### 5.1 Requisitos

- extrair texto “bom o suficiente” para:
  - detectar requisitos,
  - identificar prazos,
  - capturar trechos para evidência,
  - alimentar RAG (se aplicável)

### 5.2 Estratégia recomendada

1. PDF: `pymupdf` (fitz) **ou** `pdfplumber`
2. HTML: `readability` + `BeautifulSoup`
3. OCR: **último recurso** (só quando o PDF é imagem)

### 5.3 Saída do parser

Crie um schema simples:

- `ParsedDocument { text, sections?, metadata, page_map? }`
- `page_map` ajuda a citar “Edital.pdf#p12”.

---

## 6) Deduplicação (dedup)

### 6.1 Dedup forte (exato)

- chave: `source + external_id`
- fallback: `content_hash` do edital principal (quando baixado)

### 6.2 Dedup fraco (fuzzy)

Quando não há ID consistente:

- normalizar `objeto` (lower, remove pontuação)
- `simhash`/`minhash` (ou embeddings) para detectar repetidos
- considerar `orgao + uf + data_publicacao` como contexto

> Regra prática: dedup fraco só “sugere” duplicado; dedup forte “garante”.

---

## 7) Detecção de mudança (diff)

### 7.1 O que é “mudança relevante”

- prazo (abertura/entrega) alterado
- anexos alterados/novos
- objeto alterado
- status alterado (suspenso, revogado, etc.)
- valor estimado alterado

### 7.2 Como calcular

- comparar `LicitacaoItem` atual vs snapshot anterior
- gerar `ChangeEvent` com:
  - `change_type`
  - `diff` com from/to
  - `sources[]`

Sugestão de lib: `deepdiff` (ou implementação manual).

---

## 8) Checklist de implementação (WindSurf)

Arquivos sugeridos (MVP):

- `src/domains/licitacoes/tools/pncp_client.py`
- `src/domains/licitacoes/tools/fetcher.py`
- `src/domains/licitacoes/services/dedup.py`
- `src/domains/licitacoes/services/diff.py`
- `src/domains/licitacoes/services/parser_pdf.py`
- `src/domains/licitacoes/services/parser_html.py`

### Prompt WindSurf (para `fetcher.py`)

- **Objetivo:** criar fetcher com cache + download + hash
- **Restrições:** limite de tamanho, timeouts, retries
- **Formato:** arquivo completo + docstrings + logs mínimos

---

## 9) Testes mínimos (não pular)

- `test_dedup_strong()`: mesmo external_id → 1 item
- `test_diff_deadline_changed()`: abertura mudou → `ChangeEvent`
- `test_parser_pdf_extracts_text()`: retorna texto não vazio
- `test_pncp_normalization_has_sources()`: todo item tem `sources`

---

## 10) Próximo documento

**Doc 05 — `docs/AGENTES_E_ORQUESTRACAO_LICITACOES.md`**  
Vai especificar prompts (PROMPT-OS), papéis (Watcher/Triage/Analyst/Compliance), outputs e como compor o fluxo completo.

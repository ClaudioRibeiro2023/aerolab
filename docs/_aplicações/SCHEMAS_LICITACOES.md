# Doc 02 — Schemas do Núcleo Licitações (Pydantic/JSON)

> **Objetivo**  
> Definir os **schemas canônicos** que todo o núcleo usa (coleta → normalização → triagem → análise → entregáveis).  
> Isso evita “cada agente inventar um formato” e reduz bugs no Flow Studio / APIs.

---

## 1) Princípios

1. **Um item canônico**: tudo vira `LicitacaoItem`.
2. **Rastreável**: toda saída relevante carrega `sources[]` e `evidences[]`.
3. **Determinístico**: campos de “score/risco” sempre em enums/intervalos.
4. **Auditável**: armazenar `raw_ref` e `hash` do documento sempre que possível.

---

## 2) Enums (padrões)

### 2.1 Modalidade

- `pregao_eletronico`
- `concorrencia`
- `dispensa`
- `inexigibilidade`
- `chamada_publica`
- `rdc`
- `outros`

### 2.2 Situação (status do processo)

- `novo`
- `em_andamento`
- `suspenso`
- `revogado`
- `anulado`
- `homologado`
- `encerrado`
- `desconhecido`

### 2.3 Classificação de prioridade

- `P0` (urgente / janela curta / alto potencial)
- `P1` (relevante)
- `P2` (monitorar)
- `P3` (descartar por baixa aderência)

### 2.4 Risco (níveis)

- `baixo`
- `medio`
- `alto`
- `critico`

---

## 3) Schemas principais

## 3.1 `SourceRef`

Representa a origem do dado.

```json
{
  "source": "pncp",
  "url": "https://...",
  "retrieved_at": "2025-12-15T12:34:56Z",
  "external_id": "12345-2025",
  "raw_ref": "s3://.../raw.pdf",
  "content_hash": "sha256:..."
}
```

**Campos**

- `source` (str): ex. `pncp`, `comprasnet`, `diario_oficial`, `portal_orgaos`
- `url` (str): link do item
- `retrieved_at` (datetime)
- `external_id` (str): id/processo do sistema externo
- `raw_ref` (str, opcional): referência onde o arquivo bruto foi guardado
- `content_hash` (str, opcional): hash do conteúdo bruto

---

## 3.2 `LicitacaoItem` (canônico)

```json
{
  "id": "lic:pncp:12345-2025",
  "orgao": "Prefeitura Municipal X",
  "uf": "MG",
  "municipio": "Belo Horizonte",
  "modalidade": "pregao_eletronico",
  "objeto": "Contratação de ... (Techdengue/serviço ...)",
  "valor_estimado": 1200000.0,
  "moeda": "BRL",
  "status": "em_andamento",
  "publicado_em": "2025-12-10",
  "abertura_em": "2025-12-20T09:00:00-03:00",
  "prazo_min_dias": 10,
  "palavras_chave": ["dengue", "drone", "geoprocessamento"],
  "anexos": [{ "nome": "Edital.pdf", "url": "https://...", "tipo": "pdf" }],
  "sources": [{ "source": "pncp", "url": "https://...", "retrieved_at": "2025-12-15T12:34:56Z" }]
}
```

**Campos mínimos (recomendados como `required`)**

- `id`, `orgao`, `uf`, `modalidade`, `objeto`, `status`, `publicado_em`, `sources[]`

**Campos opcionais mas muito úteis**

- `valor_estimado`, `abertura_em`, `prazo_min_dias`, `anexos[]`, `municipio`

---

## 3.3 `ChangeEvent`

Usado para detectar “o que mudou” entre rodadas.

```json
{
  "item_id": "lic:pncp:12345-2025",
  "changed_at": "2025-12-15T12:40:00Z",
  "change_type": "prazo_alterado",
  "diff": {
    "abertura_em": { "from": "2025-12-20T09:00:00-03:00", "to": "2025-12-22T09:00:00-03:00" }
  },
  "sources": [{ "source": "pncp", "url": "https://...", "retrieved_at": "2025-12-15T12:34:56Z" }]
}
```

---

## 3.4 `TriageScore`

Resultado do agente de triagem.

```json
{
  "item_id": "lic:pncp:12345-2025",
  "priority": "P0",
  "score": 0.87,
  "reasons": [
    "objeto aderente ao portfólio Techdengue",
    "prazo curto (<= 10 dias)",
    "valor estimado alto"
  ],
  "risks": [{ "categoria": "juridico", "nivel": "medio", "evidencia": "cláusula X restringe..." }]
}
```

**Regras**

- `score`: 0.0 a 1.0
- `priority`: enum P0–P3
- `reasons`: lista curta (máx 10)

---

## 3.5 `AnalysisPack` (entregável)

```json
{
  "item_id": "lic:pncp:12345-2025",
  "resumo_executivo_md": "## Resumo...\n- ...",
  "checklist_documentos": [
    { "item": "Certidão X", "obrigatorio": true, "observacao": "validade 30 dias" }
  ],
  "perguntas_para_orgao": ["Confirmar se ...", "Esclarecer ... (item 4.2 do edital)"],
  "matriz_risco": [{ "tipo": "juridico", "nivel": "alto", "descricao": "...", "mitigacao": "..." }],
  "evidences": [{ "tipo": "trecho", "ref": "Edital.pdf#p12", "texto": "..." }],
  "sources": [{ "source": "pncp", "url": "https://...", "retrieved_at": "2025-12-15T12:34:56Z" }]
}
```

---

## 4) Schemas “de workflow” (Flow Studio)

### 4.1 `cfg` (configuração do fluxo)

Campos sugeridos (base do que você já vinha modelando no builder):

- `janela_dias` (number): janela de análise (ex.: 30)
- `limite_risco` (string): `baixo|medio|alto|critico` (mínimo aceitável)
- `prazo_min_dias` (number): mínimo de dias de antecedência
- `acao_permitida` (string): ex. `monitorar|investigar|preparar_resposta`

> Nota: em Agno, isso vira um Pydantic model (`LicitacoesFlowConfig`).

### 4.2 `result` (estado/saída do fluxo)

Recomendação prática (evita “não salva porque está vazio”):

- `status` (string) com default `"init"`
- `payload_json` (string) com default `"{}"`
- (opcional) `errors[]` (array) para acumular falhas sem quebrar o fluxo

---

## 5) Mapeamento sugerido para banco (mínimo)

- `licitacoes_items` (canonical)
- `licitacoes_changes` (diffs)
- `licitacoes_scores` (triage)
- `licitacoes_analysis` (analysis packs)
- `raw_documents` (refs para storage + hash + metadados)

---

## 6) Próximo documento

**Doc 03 — `docs/ARQUITETURA_E_PASTAS_LICITACOES.md`**  
Vai definir exatamente onde cada arquivo vive na Agno (domains/, tools/, agents/, flows/), e o passo a passo no WindSurf para gerar o scaffolding.

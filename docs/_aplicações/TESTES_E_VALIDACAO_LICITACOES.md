# Doc 07 — Testes, Validação e Regressão (Licitações)

> **Objetivo**  
> Garantir que o núcleo **não “deriva”** com o tempo (mudança de fonte, mudança de prompt, mudança de lib) e que as saídas continuem confiáveis.

---

## 1) Tipos de teste (mínimo obrigatório)

### 1.1 Unit tests (rápidos)

- `dedup.py`
- `diff.py`
- `score_rules.py`
- `parsers` (PDF/HTML)

### 1.2 Integration tests (com mocks)

- `pncp_client.search()` com respostas mockadas
- pipeline `Watcher → Triage` com fixtures

### 1.3 Golden tests (anti-regressão)

Arquivos de entrada + saída esperada, versão a versão.

Exemplo:

```
tests/fixtures/pncp/sample_001.json
tests/golden/triage/sample_001.expected.json
tests/golden/analysis/sample_001.expected.json
```

> Golden tests são o que te dá segurança para refatorar sem medo.

---

## 2) Regras para evitar flaky tests

- Não chamar internet em test (mock sempre)
- Fixar timezone
- Fixar “data de hoje” (freeze time)
- Fixar seeds (se houver ranking/aleatoriedade)

---

## 3) Critérios de qualidade (operacionais)

### 3.1 Para `daily_monitor`

- **0 crash** em execução
- **>= 95%** dos itens normalizados com `sources[]`
- Dedup funcionando (não duplicar no digest)

### 3.2 Para `triage`

- “Razões” curtas e rastreáveis
- `priority` consistente (P0/P1/P2/P3)
- Penalizar incerteza (não inventar valor/prazo)

### 3.3 Para `analysis_pack`

- Sempre produzir:
  - resumo executivo
  - checklist
  - matriz de risco
  - evidências mínimas (ou justificativa “não localizado”)

---

## 4) Plano de avaliação (humano no loop)

Crie uma amostra semanal:

- 20 itens de licitação (variados)
- 10 análises completas (P0/P1)

Para cada item, revisar:

- prioridade correta? (sim/não)
- riscos relevantes capturados? (sim/não)
- há alucinação? (sim/não)
- evidências batem com o edital? (sim/não)

Registrar em planilha/DB:

- `reviewer`
- `decision`
- `notes`

---

## 5) Checklist de regressão antes de deploy

1. Rodar unit + integration + golden
2. Rodar um “dry run” do monitor (mock)
3. Verificar logs: sem PII, sem secrets
4. Validar schemas (Doc 02)
5. Conferir “result defaults” (Doc 06)

---

## 6) Próximo documento

**Doc 08 — `docs/DEPLOY_E_OPERACAO_LICITACOES.md`**  
Vai cobrir: agendamento, observabilidade, limites, secrets, e operação segura.

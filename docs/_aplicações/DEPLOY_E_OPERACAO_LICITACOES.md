# Doc 08 — Deploy, Operação e Observabilidade (Licitações)

> **Objetivo**  
> Colocar o núcleo em produção com previsibilidade: **agendar**, **monitorar**, **limitar**, **auditar** e **corrigir rápido**.

---

## 1) Agendamento do `daily_monitor`

Opções comuns:

- cron (simples)
- job runner interno (Celery/RQ/Arq)
- scheduler no próprio backend

Requisitos mínimos:

- `run_id`
- lock (para não rodar duas vezes simultâneo)
- retry com limite
- alertar quando falhar N vezes

---

## 2) Observabilidade

### 2.1 Logs (mínimo)

- `run_id`, `mode`, `source`, `count_items`, `count_changes`, `count_p0`
- tempo por etapa (coleta, triage, analysis)
- erro com stacktrace (sem vazar secrets)

### 2.2 Métricas

- sucesso/falha por fonte
- tempo médio de execução
- itens coletados/dia
- P0/P1 por dia
- taxa de itens “incertos”

### 2.3 Tracing (P1)

Se usar OpenTelemetry, instrumentar:

- fetcher
- pncp_client
- parser

---

## 3) Limites e proteção (para não dar dor de cabeça)

- rate limit por fonte
- tamanho máximo de download
- timeout padrão (fetch/parsing)
- cache TTL
- desativar OCR por padrão (ligar só quando necessário)

---

## 4) Segurança e secrets

- secrets no `.env` / vault (nunca hardcode)
- logs sem tokens/chaves
- cuidado com anexos contendo dados sensíveis

---

## 5) Política de resposta (legal/jurídico)

Sempre comunicar como:

- “assistência à análise”
- “pontos de atenção e evidências”
- “revisão humana necessária”

---

## 6) Versionamento do núcleo

- versionar templates do Flow Studio
- versionar prompts (hash)
- versionar schemas (Doc 02)

Sugestão:

- `domains/licitacoes/VERSION`
- `flows/templates/*.template.json` com `template_version`

---

## 7) Playbook de incidente (mínimo)

Se a coleta começar a falhar:

1. identificar qual fonte quebrou
2. desligar temporariamente a fonte via flag
3. manter digest parcial (não parar tudo)
4. abrir issue e anexar logs do `run_id`

---

## 8) Encerramento

Com Doc 01–08, você tem:

- visão e escopo
- schemas
- arquitetura de pastas
- tools de coleta/dedup/diff
- agentes e prompts
- flows e UI
- testes e operação

Próximo passo prático no WindSurf:

1. criar a estrutura do domínio (Doc 03)
2. implementar schemas (Doc 02) em `schemas.py`
3. implementar PNCP client + dedup/diff (Doc 04)
4. ligar no Flow Studio com templates (Doc 06)

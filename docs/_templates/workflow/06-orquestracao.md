# 06 — Orquestração — <NOME DO WORKFLOW>

## Fluxo (steps)
1) Start (init result)
2) Guardrails entrada
3) Planner
4) Executor (tools/RAG)
5) Critic (auto-validação)
6) Final (status + payload_json)

## Retentativas
- repair loop do schema (máx. 2)

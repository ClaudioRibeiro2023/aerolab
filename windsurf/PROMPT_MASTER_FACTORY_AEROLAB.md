# PROMPT MESTRE — Factory AeroLab (v1.1) — Criar novo workflow

Você está no repositório AeroLab/Agno (backend FastAPI em `src/`, frontend em `apps/web/`).
Crie um NOVO workflow seguindo o padrão “Factory v1.1”.

## Inputs (preenchidos por mim)
- slug: <slug>
- nome: <nome legível>
- domínio: <domain>
- objetivo: <1 parágrafo>
- entradas: <lista>
- saídas: <lista>

## Tarefas (faça em ordem)
1) Criar docs em `docs/workflows/<slug>/` copiando `docs/_templates/workflow/`
2) Criar `schemas/` do workflow:
   - `schemas/input.json` (JSON Schema)
   - `schemas/result.json` (use `templates/result.schema.json`)
3) Criar template do Flow Studio:
   - `src/flow_studio/templates/<domain>/<slug>.json`
   - incluir `state_defaults.result` com:
     `{ "status":"init", "payload_json":"{}", "errors":[] }`
4) Implementar runner backend:
   - `src/workflows/<domain>/<slug>/runner.py`
   - valida inputs (Pydantic)
   - executa nodes
   - grava audit log por step (tokens/custo/tempo)
   - valida saída com schema + repair loop (máx 2)
5) Expor endpoints:
   - `POST /workflows/registry` (registrar)
   - `POST /workflows/registry/{name}/run` (executar)
   - `GET /workflows/registry` (listar)
   Se já existir infra, apenas integrar o novo workflow no registry.
6) Criar testes:
   - `tests/golden/<slug>/case_01.json` … `case_10.json`
   - smoke e2e do endpoint /run
7) Atualizar `docs/INDEX.md` adicionando link para o workflow e para `operacao/contribuicao/63-factory-workflows.md`.

## Regras
- Commits pequenos
- Não criar .md solto fora de `docs/`
- Não deixar `result` sem default (builder não salva)
- Não inventar endpoints se já existirem; adapte ao padrão atual do repo

Ao final, gere um checklist DoD (passou/pendente).

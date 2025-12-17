# Factory de Workflows e Agentes — padrão AeroLab (v1.1)

> Objetivo: garantir que **todo novo workflow** (licitações, pesquisa profunda, etc.)
> siga o mesmo caminho: **especificação clara → schemas → implementação → guardrails → testes → publicação**.

Este documento foi alinhado com as convenções já presentes no repositório:
- `docs/INDEX.md` é a **source of truth**.
- Backend em `src/` com módulos como `src/agents/`, `src/workflows/`, `src/memory/`, `src/rag/` (ver `arquitetura/agno2/13-modulos-e-limites.md`).
- API de agentes e workflows documentada em `contratos-integracao/agno2/21-api.md`.

---

## 1) Conceitos (sem “programadês”)

### 1.1 Agente
É uma “pessoa digital” com:
- **papel** (role)
- **instruções** (regras)
- **modelo** (LLM)
- **ferramentas** (tools: buscar web, ler PDF, acessar banco, etc.)
- **memória** (curto prazo + memória por projeto)
- **formato de saída** (schema)

### 1.2 Workflow
É uma **receita com passos** (etapas) que orquestra:
- 1+ agentes
- 0+ ferramentas
- decisões (if/else)
- validações (auto-check)
- logs/auditoria

### 1.3 Flow Studio
É o editor visual (grafo). A regra de ouro é:

> **Estado sempre válido.**  
> Nunca deixe variável “vazia” esperando existir depois.

Por isso, no **Start** do fluxo, você sempre inicializa o `result` com default (veja seção 3).

---

## 2) O que SEMPRE criamos em um novo workflow

Quando você cria um workflow novo, ele precisa nascer com 5 coisas:

1. **Docs do workflow** (pasta própria)
2. **Schemas** (inputs + outputs por etapa)
3. **Template do Flow Studio** (grafo + defaults)
4. **Runner backend** (executa o grafo e grava audit)
5. **Evals/Testes** (10 casos “golden set”)

Isso evita retrabalho e garante que o workflow evolua com segurança.

---

## 3) Padrão obrigatório do `result` (para não quebrar o builder)

O Flow Studio **não salva** se o `result` estiver “sem informação”.

Use este default mínimo (obrigatório):

```json
{
  "status": "init",
  "payload_json": "{}",
  "errors": []
}
```

- `status`: `"init" | "ok" | "needs_info" | "blocked" | "error"`
- `payload_json`: string JSON (sempre **string**, mesmo que contenha JSON dentro)
- `errors`: lista de mensagens

> Por que `payload_json` é string?  
> Porque simplifica persistência e compatibilidade com UI. Se no futuro você quiser, pode adicionar `payload` como objeto também — mas **não substitua** `payload_json` sem migrar.

---

## 4) Estrutura de arquivos recomendada (docs)

Crie a pasta do workflow em:

`docs/workflows/<slug>/`

Use os templates em `docs/_templates/workflow/`.

Arquivos recomendados:

- `00-visao-geral.md`
- `01-requisitos.md`
- `02-schemas.md`
- `03-agentes.md`
- `04-tools.md`
- `05-memoria-rag.md`
- `06-orquestracao.md`
- `07-guardrails.md`
- `08-testes-e-evals.md`
- `09-windsurf-playbook.md`

E **adicione o link** em `docs/INDEX.md`.

---

## 5) Specs: o que o AeroLab precisa saber (mínimo)

### 5.1 AgentSpec (mínimo)
Campos essenciais (compatíveis com exemplos do projeto):

- `name`
- `role`
- `instructions` (lista)
- `model_provider` (ex.: `openai`, `anthropic`, `groq`)
- `model_id` (ex.: `gpt-5`, `claude-4.5`, `llama-3.3-70b-versatile`)
- `tools` (lista de tools habilitadas)
- `rag` (opcional: collection + top_k)
- `memory` (short_term + project_memory)
- `output_schema_ref` (JSON schema do output)

### 5.2 WorkflowSpec (mínimo)
- `name`
- `domain`
- `input_schema_ref`
- `state_defaults` (inclui `result`)
- `graph` (nodes + edges)
- `version`
- `status` (draft|published)

---

## 6) Guardrails (sem travar seu produto)

Implementar em 2 camadas:

### 6.1 Pre-check (entrada)
Bloquear/alertar:
- prompt injection (instruções maliciosas dentro do input)
- URLs suspeitas (allowlist por domínio quando fizer sentido)
- PII desnecessária (LGPD)
- requests fora do escopo (ex.: “faça hacking”)

### 6.2 Post-check (saída)
- validar schema do output
- se inválido: **repair loop** (máx. 2 tentativas)
- redigir PII (quando necessário)
- exigir “evidências” quando houver afirmação jurídica (“cite a fonte/trecho”)

---

## 7) Auto-validação e “cognição intrínseca” (sem magia)

O padrão recomendado é sempre ter um passo “Crítico”:

- **Planner**: cria plano + checklist
- **Executor**: executa (web/RAG/tools)
- **Critic/Verifier**: valida:
  - schema ok?
  - evidências suficientes?
  - contradições?
  - risco jurídico?
  - custo/tempo ok?

E **gravar**:
- `assumptions[]`
- `risks[]`
- `evidence[]`
- `decision_log[]`

Isso vira sua “memória operacional” e ajuda o sistema a aprender via versões (não via auto-modificação solta).

---

## 8) Níveis de complexidade (para evoluir com segurança)

- **L0** — 1 agente, sem tools, saída em texto
- **L1** — 1 agente + output em schema + logs
- **L2** — multi-agentes (planner/executor/critic) + RAG
- **L3** — workflow no Flow Studio + templates + HITL (aprovação humana)
- **L4** — marketplace + versionamento forte + evals no CI + observabilidade de custo

Recomendação: comece em L2 (já dá MUITO valor) e evolua.

---

## 9) Checklist de pronto-para-publicar (DoD)

- [ ] Docs em `docs/workflows/<slug>/` preenchidas
- [ ] `result` inicializado no Start
- [ ] Inputs com schema definido
- [ ] Saída validada por schema
- [ ] Guardrails pre/post ativos
- [ ] 10 casos golden set em `tests/golden/`
- [ ] Smoke test passa
- [ ] Link adicionado no `docs/INDEX.md`

---

## 10) Próximo passo recomendado
Rodar o prompt do WindSurf (arquivo `windsurf/PROMPT_MASTER_FACTORY_AEROLAB.md`)
para criar um workflow novo por *scaffolding automático*.

# PROMPT — Factory: Criar Novo Workflow

> **Versão:** 1.1.0  
> **Tipo:** Prompt oficial Factory AeroLab

---

## Objetivo

Criar um novo workflow seguindo o padrão Factory v1.1.

---

## Instruções para a IA

Você deve criar um novo workflow com a seguinte estrutura:

### 1. Informações Obrigatórias

Solicite ao usuário:

- **slug:** identificador único (snake_case, sem espaços)
- **nome:** nome descritivo do workflow
- **domínio:** área do negócio (ex: licitacoes, vendas, rh)
- **objetivo:** descrição clara do que o workflow faz
- **entradas:** lista de campos de entrada com tipos
- **saídas:** lista de campos de saída com tipos

### 2. Estrutura a Criar

```text
docs/workflows/<slug>/
├── README.md
└── schemas/
    ├── input.json
    └── result.json

apps/api/src/flow_studio/templates/<domain>/
└── <slug>.json

apps/api/src/workflows/<domain>/<slug>/
├── __init__.py
├── models.py
└── runner.py

apps/api/tests/golden/<slug>/
├── case_01.json
├── case_02.json
├── case_03.json
├── case_04.json
├── case_05.json
└── test_runner.py
```

### 3. Regras

- **README.md** deve conter: slug, nome, domínio, versão, objetivo, tabelas de entradas/saídas, fluxo de execução
- **input.json** deve ser JSON Schema válido com todos os campos de entrada
- **result.json** deve ter `status`, `payload_json`, `errors` obrigatórios
- **Template Flow Studio** deve ter `state_defaults.result` com defaults
- **Runner** deve validar inputs com Pydantic e gravar audit log
- **Golden tests** mínimo 5 casos cobrindo cenários principais

### 4. Commits

Faça commits pequenos e incrementais:

1. `docs(workflows): add <slug> documentation`
2. `feat(flow-studio): add <slug> template`
3. `feat(workflows): add <slug> runner`
4. `test(golden): add <slug> test cases`

### 5. Validação

Ao final, execute:

```bash
pnpm factory:validate
```

Todos os checks devem passar (PASS).

---

## Template de Solicitação

Use este formato para solicitar a criação:

```markdown
Crie um novo workflow:
- slug: <slug>
- nome: <nome>
- domínio: <domain>
- objetivo: <descrição>
- entradas: [campo1: tipo, campo2: tipo, ...]
- saídas: [campo1: tipo, campo2: tipo, ...]
```

---

## Exemplo

```markdown
Crie um novo workflow:
- slug: vendas_forecast
- nome: Previsão de Vendas
- domínio: vendas
- objetivo: Gerar previsões de vendas baseadas em histórico e sazonalidade
- entradas: [periodo: string, produto_id: string, modelo: enum[linear,arima,ml]]
- saídas: [previsao: array, confianca: number, grafico_url: string]
```

---

## Referências

- [CONTRATO_FACTORY.md](../docs/operacao/factory/CONTRATO_FACTORY.md)
- [docs/_templates/workflow/](../docs/_templates/workflow/)

# PROMPT — Factory: Validar Repositório

> **Versão:** 1.1.0  
> **Tipo:** Prompt oficial Factory AeroLab

---

## Objetivo

Validar que o repositório segue todas as regras do padrão Factory v1.1.

---

## Instruções para a IA

Execute a validação completa do repositório usando o comando oficial:

```bash
pnpm factory:validate
```

### Regras de Validação

| Código | Regra | Severidade | Descrição |
|--------|-------|------------|-----------|
| MD_LOCATION | Arquivos .md em docs/ | ERROR | Nenhum .md fora de docs/ (exceto README.md raiz) |
| WORKFLOW_README | README existe | ERROR | Todo workflow em docs/workflows/ tem README.md |
| WORKFLOW_INPUT | input.json existe | ERROR | Todo workflow tem schemas/input.json |
| WORKFLOW_RESULT | result.json existe | ERROR | Todo workflow tem schemas/result.json |
| GOLDEN_MIN | Mínimo 5 golden cases | ERROR | Todo workflow tem pelo menos 5 case_*.json |
| STATE_DEFAULTS | Template tem defaults | ERROR | Template Flow Studio tem state_defaults.result |
| RUNNER_EXISTS | Runner Python existe | WARNING | Workflow tem runner.py implementado |

### Interpretação dos Resultados

**PASS** — Repositório está em conformidade com Factory v1.1.

```
✅ factory:validate PASS
   - MD_LOCATION: OK
   - WORKFLOW_README: OK (1 workflow)
   - WORKFLOW_SCHEMAS: OK
   - GOLDEN_TESTS: OK (5+ cases)
   - STATE_DEFAULTS: OK
```

**FAIL** — Há violações que precisam ser corrigidas.

```
❌ factory:validate FAIL
   - MD_LOCATION: FAIL
     → apps/api/src/NOTES.md (mover para docs/)
   - GOLDEN_TESTS: FAIL
     → workflow "vendas_forecast" tem apenas 2 casos (mínimo: 5)
```

### Ações de Correção

Se houver falhas:

1. **MD_LOCATION:** Mova arquivos .md para docs/ ou delete se desnecessário
2. **WORKFLOW_README:** Crie README.md seguindo template em docs/_templates/workflow/
3. **WORKFLOW_SCHEMAS:** Crie input.json e result.json válidos
4. **GOLDEN_TESTS:** Adicione casos de teste até atingir mínimo de 5
5. **STATE_DEFAULTS:** Adicione bloco `state_defaults.result` no template

---

## Execução Manual

Se o comando não estiver disponível, execute manualmente:

```bash
python scripts/factory_validate.py
```

Ou verifique cada regra individualmente:

```bash
# Verificar .md fora de docs/
find . -name "*.md" -not -path "./docs/*" -not -path "./node_modules/*" -not -name "README.md"

# Verificar workflows sem README
ls docs/workflows/*/README.md

# Verificar golden tests
ls apps/api/tests/golden/*/case_*.json | wc -l
```

---

## Integração CI

A validação é executada automaticamente em:

- Pull Requests para `main`
- Push para `main`
- Pre-commit hook (se habilitado)

---

## Referências

- [CONTRATO_FACTORY.md](../docs/operacao/factory/CONTRATO_FACTORY.md)
- [scripts/factory_validate.py](../scripts/factory_validate.py)

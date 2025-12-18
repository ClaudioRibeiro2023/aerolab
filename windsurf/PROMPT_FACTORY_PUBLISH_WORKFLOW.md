# PROMPT — Factory: Publicar Workflow

> **Versão:** 1.1.0  
> **Tipo:** Prompt oficial Factory AeroLab

---

## Objetivo

Publicar um workflow após passar em todas as validações da Factory v1.1.

---

## Pré-requisitos

Antes de publicar, verifique:

1. ✅ `pnpm factory:validate` passa (PASS)
2. ✅ Todos os testes passam (`pytest`)
3. ✅ Branch está atualizada com `main`
4. ✅ Código revisado (self-review ou pair)

---

## Instruções para a IA

### 1. Validação Final

```bash
# Executar validação Factory
pnpm factory:validate

# Executar testes do workflow
cd apps/api
pytest tests/golden/<slug>/ -v
```

### 2. Atualizar docs/INDEX.md

Adicione o novo workflow na tabela de workflows:

```markdown
| [<slug>](./workflows/<slug>/README.md) | <domain> | <descrição> |
```

### 3. Commit Final

```bash
git add -A
git commit -m "feat(workflows): publish <slug> workflow"
```

### 4. Criar Pull Request

```bash
git push origin feat/workflow-<slug>
```

Crie PR com:

- **Título:** `feat(workflows): add <nome> workflow`
- **Descrição:** Link para docs/workflows/<slug>/README.md
- **Labels:** `workflow`, `factory-v1.1`
- **Reviewers:** Mantenedores do projeto

### 5. Checklist do PR

```markdown
## Checklist Factory v1.1

- [ ] `pnpm factory:validate` PASS
- [ ] README.md em docs/workflows/<slug>/
- [ ] Schemas input.json e result.json válidos
- [ ] Template Flow Studio com state_defaults
- [ ] Runner com validação Pydantic
- [ ] Audit log por step
- [ ] Mínimo 5 golden cases
- [ ] Testes pytest passando
- [ ] docs/INDEX.md atualizado
- [ ] Endpoint(s) documentado(s)
```

### 6. Após Merge

1. **Tag de release** (se aplicável):

   ```bash
   git tag -a v<version> -m "Release <version>: add <slug> workflow"
   git push origin v<version>
   ```

2. **Comunicar** equipe sobre novo workflow disponível

3. **Monitorar** primeiras execuções em produção

---

## Fluxo Visual

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Validar    │────▶│  Criar PR   │────▶│   Review    │
│  factory    │     │             │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Monitorar  │◀────│   Deploy    │◀────│   Merge     │
│  produção   │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Troubleshooting

### PR com falha no CI

1. Verifique logs do CI
2. Execute `pnpm factory:validate` localmente
3. Corrija violações e faça push

### Conflitos com main

```bash
git fetch origin
git rebase origin/main
# Resolver conflitos
git push --force-with-lease
```

### Testes falhando

1. Execute testes localmente com `-v`
2. Verifique se mock data está atualizada
3. Ajuste golden cases se necessário

---

## Referências

- [CONTRATO_FACTORY.md](../docs/operacao/factory/CONTRATO_FACTORY.md)
- [PROMPT_FACTORY_CREATE_WORKFLOW.md](./PROMPT_FACTORY_CREATE_WORKFLOW.md)
- [PROMPT_FACTORY_VALIDATE_REPO.md](./PROMPT_FACTORY_VALIDATE_REPO.md)

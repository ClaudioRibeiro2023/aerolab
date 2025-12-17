# Convenções de Branch e PR

> Fluxo de trabalho Git para contribuições.

---

## Branches

### Principais

| Branch | Uso |
|--------|-----|
| `main` | Produção (deploy automático) |
| `staging` | Staging (deploy automático) |

### Feature Branches

```
feature/<nome-da-feature>
fix/<nome-do-bug>
docs/<nome-da-doc>
refactor/<nome-do-refactor>
```

### Exemplos

```bash
feature/add-graph-rag
fix/auth-token-expiration
docs/api-contracts
refactor/flow-studio-engine
```

---

## Fluxo de Trabalho

### 1. Criar Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/my-feature
```

### 2. Desenvolver

```bash
# Fazer commits pequenos e frequentes
git add .
git commit -m "feat(module): add new feature"
```

### 3. Push

```bash
git push origin feature/my-feature
```

### 4. Pull Request

1. Abra PR no GitHub
2. Preencha template
3. Aguarde review
4. Faça ajustes se necessário
5. Merge após aprovação

---

## Template de PR

```markdown
## Descrição

Breve descrição do que foi feito.

## Tipo de Mudança

- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Checklist

- [ ] Testes passando (`pytest tests/`)
- [ ] Lint passando (`ruff check .`)
- [ ] Documentação atualizada (se necessário)
- [ ] Changelog atualizado (se necessário)

## Screenshots (se aplicável)

## Notas para Revisores
```

---

## Code Review

### Critérios de Aprovação

- [ ] Código segue padrões do projeto
- [ ] Testes adequados
- [ ] Sem quebra de API (ou documentada)
- [ ] Performance aceitável
- [ ] Segurança considerada

### Feedback Construtivo

```markdown
# Bom
"Considere extrair essa lógica para uma função separada para melhorar testabilidade"

# Ruim
"Esse código está ruim"
```

---

## Merge

### Squash and Merge

Preferido para PRs com múltiplos commits de WIP:

```
feat(agents): add support for custom tools (#123)
```

### Merge Commit

Usado para branches de release ou merge de staging → main.

---

## Releases

### Versionamento

Seguimos [SemVer](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: Novas features (backward compatible)
- **PATCH**: Bug fixes

### Tags

```bash
git tag -a v2.2.0 -m "Release v2.2.0"
git push origin v2.2.0
```

### Changelog

Atualizar `CHANGELOG.md` com cada release:

```markdown
## [2.2.0] - 2024-12-16

### Added
- Feature X

### Fixed
- Bug Y

### Changed
- Behavior Z
```

---

## Referências

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)

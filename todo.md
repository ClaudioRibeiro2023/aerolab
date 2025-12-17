# AeroLab — Plano Mestre de Evolução

> **Data:** 2024-12-17  
> **Status:** Em Execução  
> **Versão:** 1.0.0

---

## 1. Visão Geral

### Objetivo Macro
Consolidar o AeroLab como plataforma corporativa de multi-agentes AI, integrando o código do Agno2 com o design system e padrões do Modelo.

### Princípios
- **AeroLab (Modelo) é lei** para: UI, design system, lint/format, estrutura de repo
- **Agno2 é lei** para: domínios AI (agents, flows, RAG, tools, auth/RBAC)
- **Porta 9000** como entrypoint principal local
- **Segurança primeiro**: sem segredos versionados

### Produto Principal
- `apps/studio` — AeroLab Studio (Next.js 15) — porta 9000
- `apps/api` — Backend FastAPI (Python 3.12) — porta 8000
- `apps/web` — Design System Web (Vite/React) — porta 5173

---

## 2. Status Atual (Baseline)

### ✅ Funcionando
- Estrutura monorepo com pnpm workspaces
- apps/api com 31 módulos de domínio do Agno2
- apps/studio com Next.js 15 e componentes do Agno2
- apps/web com design system base
- packages/design-system, shared, types
- .gitignore robusto (Python + Node + IDEs)
- .env.example em apps/api e apps/studio

### ⚠️ Pendente/Quebrando
- ESLint com conflitos de configuração (flat config vs legacy)
- Testes unitários/e2e não executados
- Health check do backend não validado
- Integração API ↔ Studio não testada
- CI/CD não configurado

### 🔴 Riscos
- Dependências desatualizadas (eslint@8 deprecated)
- Falta de testes automatizados
- Observabilidade não implementada
- Performance não mensurada

---

## 3. Plano Faseado

### FASE 1 — Estabilização / Segurança / Entrega Local 9000 (P0)

| ID | Título | Prioridade | Tamanho | Status |
|----|--------|------------|---------|--------|
| AL-001 | Configurar Studio na porta 9000 | P0 | S | ✅ Done |
| AL-002 | Remover .eslintrc.json duplicado do Studio | P0 | S | ✅ Done |
| AL-003 | Desabilitar standalone output no Next.js (Windows) | P0 | S | ✅ Done |
| AL-004 | Validar build do Studio sem erros | P0 | M | 🔄 Pending |
| AL-005 | Criar venv e instalar deps do apps/api | P0 | M | ⏳ Todo |
| AL-006 | Validar /health endpoint do backend | P0 | S | ⏳ Todo |
| AL-007 | Validar /api/docs (Swagger) acessível | P0 | S | ⏳ Todo |
| AL-008 | Criar script `pnpm dev:all` funcional | P0 | M | ⏳ Todo |
| AL-009 | Consolidar .env.example na raiz | P1 | M | ⏳ Todo |
| AL-010 | Atualizar .gitignore com padrões faltantes | P1 | S | ⏳ Todo |
| AL-011 | Remover package-lock.json do Studio (usar pnpm) | P1 | S | ⏳ Todo |
| AL-012 | Atualizar ESLint para v9 (flat config) | P1 | L | ⏳ Todo |
| AL-013 | Configurar proxy /api no Next.js → backend | P1 | M | ⏳ Todo |
| AL-014 | Smoke test: curl localhost:9000 + localhost:8000/health | P0 | S | ⏳ Todo |

### FASE 2 — Qualidade / Testes / Observabilidade / CI (P1)

| ID | Título | Prioridade | Tamanho | Status |
|----|--------|------------|---------|--------|
| AL-015 | Criar pytest básico para apps/api | P1 | M | ⏳ Todo |
| AL-016 | Criar test_health.py (smoke test API) | P1 | S | ⏳ Todo |
| AL-017 | Criar vitest para packages/shared | P1 | M | ⏳ Todo |
| AL-018 | Configurar Playwright para Studio | P1 | L | ⏳ Todo |
| AL-019 | Criar smoke test E2E (abrir /, criar agente) | P1 | L | ⏳ Todo |
| AL-020 | Configurar GitHub Actions CI básico | P1 | M | ⏳ Todo |
| AL-021 | Adicionar npm audit / pip audit no CI | P1 | S | ⏳ Todo |
| AL-022 | Configurar pre-commit hooks (lint + format) | P1 | M | ⏳ Todo |
| AL-023 | Implementar logging estruturado (JSON) | P2 | M | ⏳ Todo |
| AL-024 | Adicionar tracing com OpenTelemetry | P2 | L | ⏳ Todo |
| AL-025 | Configurar métricas Prometheus | P2 | L | ⏳ Todo |
| AL-026 | Criar dashboard Grafana básico | P2 | L | ⏳ Todo |
| AL-027 | Documentar cobertura de testes atual | P2 | S | ⏳ Todo |

### FASE 3 — Produto / UX / Performance / Escala (P2)

| ID | Título | Prioridade | Tamanho | Status |
|----|--------|------------|---------|--------|
| AL-028 | Medir bundle size do Studio | P2 | S | ⏳ Todo |
| AL-029 | Otimizar cold start do backend | P2 | M | ⏳ Todo |
| AL-030 | Implementar caching de RAG | P2 | L | ⏳ Todo |
| AL-031 | Revisar UX do Agent Builder | P2 | L | ⏳ Todo |
| AL-032 | Implementar onboarding wizard | P2 | L | ⏳ Todo |
| AL-033 | Adicionar estados empty/loading/error | P2 | M | ⏳ Todo |
| AL-034 | Melhorar acessibilidade (a11y) | P2 | L | ⏳ Todo |
| AL-035 | Consolidar UI duplicada (Agno2 → packages/ui) | P2 | L | ⏳ Todo |
| AL-036 | Criar Storybook para design system | P2 | L | ⏳ Todo |
| AL-037 | Implementar dark mode consistente | P2 | M | ⏳ Todo |
| AL-038 | Configurar deploy staging (Netlify/Vercel) | P2 | M | ⏳ Todo |
| AL-039 | Configurar deploy produção | P2 | L | ⏳ Todo |
| AL-040 | Documentar arquitetura C4 atualizada | P2 | M | ⏳ Todo |

---

## 4. Template de Tarefa

```markdown
### AL-XXX: [Título]

**Prioridade:** P0/P1/P2  
**Tamanho:** S (< 2h) / M (2-8h) / L (> 8h)  
**Owner:** Dev / DevOps / QA

#### Descrição
[O que precisa ser feito]

#### Passos de Execução
1. ...
2. ...

#### Critérios de Aceite
- [ ] ...
- [ ] ...

#### Comandos de Validação
\`\`\`bash
# comando para validar
\`\`\`

#### Riscos e Rollback
- Risco: ...
- Rollback: ...
```

---

## 5. Checklist de Validação Final

### Release Gate Local
- [ ] `pnpm dev` sobe Studio na porta 9000
- [ ] `pnpm dev:api` sobe backend na porta 8000
- [ ] `curl http://localhost:9000` retorna 200
- [ ] `curl http://localhost:8000/health` retorna 200
- [ ] `curl http://localhost:8000/api/docs` retorna Swagger UI
- [ ] Console sem erros críticos

### Release Gate CI
- [ ] `pnpm lint` passa
- [ ] `pnpm typecheck` passa
- [ ] `pnpm build` passa
- [ ] `pnpm test` passa
- [ ] Cobertura > 60%

### Security Gate
- [ ] Sem segredos versionados
- [ ] `npm audit` sem vulnerabilidades críticas
- [ ] `pip audit` sem vulnerabilidades críticas
- [ ] Headers de segurança configurados
- [ ] CORS restritivo em produção

---

## 6. Próximos Passos (Top 5)

1. **AL-005** — Criar venv e instalar deps do apps/api
2. **AL-006** — Validar /health endpoint do backend
3. **AL-014** — Smoke test: curl localhost:9000 + localhost:8000/health
4. **AL-011** — Remover package-lock.json do Studio
5. **AL-020** — Configurar GitHub Actions CI básico

---

## 7. Comandos Úteis

```bash
# Desenvolvimento
pnpm dev          # Studio na porta 9000
pnpm dev:api      # Backend na porta 8000
pnpm dev:web      # Design System na porta 5173
pnpm dev:all      # Todos em paralelo

# Build
pnpm build        # Build completo
pnpm build:studio # Build apenas Studio

# Qualidade
pnpm lint         # ESLint
pnpm format       # Prettier
pnpm typecheck    # TypeScript
pnpm test         # Testes

# Backend (apps/api)
cd apps/api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
uvicorn server:app --reload --port 8000
```

---

_Atualizado em 2024-12-17 — Auditoria Total AeroLab_

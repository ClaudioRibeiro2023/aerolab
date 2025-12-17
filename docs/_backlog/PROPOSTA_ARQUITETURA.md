# Proposta de Arquitetura e Melhorias – Agno Multi-Agent Platform

> **Versão:** 1.0
> **Data:** 2025-12-09
> **Autor:** Arquiteto de Software (análise automatizada)
> **Estado da aplicação:** Em crescimento ativo, com complexidade aumentando

---

## 1. Visão Geral do Projeto

### 1.1 Contexto

| Aspecto | Descrição |
|---------|-----------|
| **Tipo** | Plataforma fullstack (API + Frontend SPA) |
| **Stack Backend** | Python 3.12+, FastAPI, SQLAlchemy, Agno Framework |
| **Stack Frontend** | Next.js 15, React 18, TypeScript, TailwindCSS, Zustand |
| **Gerenciadores** | `pip`/`uv` (Python), `npm` (Node.js) |
| **Deploy** | Railway (backend), Netlify (frontend) |
| **Infraestrutura** | Docker Compose com profiles (RAG, Cache, Local LLM) |
| **CI/CD** | GitHub Actions (4 workflows existentes) |

### 1.2 Resumo Executivo

#### ✅ Pontos Fortes
- **Arquitetura modular bem definida** – 35+ módulos em `src/` com separação clara por domínio
- **Stack moderna e atualizada** – Python 3.13, Next.js 15, FastAPI, TypeScript strict
- **CI/CD funcional** – Lint, testes, build e security scan no GitHub Actions
- **Documentação existente** – README, TODO.md, docs/ com 50+ arquivos
- **Docker ready** – docker-compose com profiles para serviços opcionais
- **Testes automatizados** – 297+ testes passando, suítes de stress e validação
- **Observabilidade inicial** – Módulos de audit, observability e logging

#### ⚠️ Principais Riscos/Dívidas Técnicas
- **Validação de env vars frágil** – Sem fail-fast na inicialização; erros em runtime
- **CI com `|| true`** – Lint e typecheck ignoram falhas (erros silenciados)
- **Ausência de testes E2E** – Frontend sem Playwright/Cypress
- **Configuração duplicada** – `.env.master` (1300+ linhas) difícil de manter
- **Entry points múltiplos** – `server.py`, `app.py`, `start.py` confusos
- **Mypy ignorando erros** – `--ignore-missing-imports` e `|| true` no CI
- **Sem staging environment** – Deploy direto para produção

---

## 2. Diagnóstico Estruturado

### 2.1 Arquitetura & Organização

#### ✅ O que está bom
- **Estrutura feature-first** em `src/` com módulos coesos:
  - `agents/`, `flow_studio/`, `dashboard/`, `team_orchestrator/`
  - `billing/`, `marketplace/`, `enterprise/` (camada de negócios)
  - `auth/`, `audit/`, `compliance/` (segurança)
- **Separação backend/frontend** clara com diretórios independentes
- **Routers modulares** no FastAPI incluídos dinamicamente no `server.py`
- **Frontend com App Router** (Next.js 15) e estrutura organizada

#### ❌ Problemas identificados
- **Entry points confusos**: `server.py` (principal), `app.py` (legacy), `start.py` (híbrido)
  - Consequência: Documentação desatualizada, confusão sobre qual usar
- **Imports circulares potenciais** em módulos grandes como `flow_studio/` (15 subpastas)
- **Módulo `src/` sem `py.typed`** – SDK não distribui tipos

#### 📁 Exemplos concretos
```
src/
├── flow_studio/     # 15 subpastas – muito grande, candidato a split
├── dashboard/       # 54 items – verificar se há código morto
├── tools/           # 33 items – cada tool deveria ser independente?
```

### 2.2 Qualidade de Código

#### ✅ O que está bom
- **TypeScript strict** no frontend (`"strict": true` no tsconfig)
- **Black + Ruff** configurados para formatação Python
- **Tipagem parcial** em modelos Pydantic (FastAPI)
- **Path aliases** configurados (`@/*` no frontend)

#### ❌ Problemas identificados
- **Mypy ignorado no CI** – linha 54 do ci.yml: `mypy src/ --ignore-missing-imports || true`
  - Consequência: Erros de tipo não detectados, regressões silenciosas
- **ESLint/Typecheck com `|| true`** – linhas 110-113 do ci.yml
  - Consequência: Frontend pode ter erros de lint/tipo não corrigidos
- **Lints pendentes reportados** – 41+ warnings CSS inline, buttons sem texto acessível

#### 📁 Exemplos concretos
```yaml
# .github/workflows/ci.yml:54
- name: Run mypy
  run: mypy src/ --ignore-missing-imports || true  # ❌ Erros ignorados

# .github/workflows/ci.yml:110-113
- name: Run lint
  run: npm run lint || true  # ❌ Falhas silenciadas
```

### 2.3 Testes

#### ✅ O que está bom
- **297+ testes** organizados em suítes:
  - `test_v2_modules.py` (77 testes)
  - `test_billing_marketplace.py` (105 testes)
  - `test_enterprise.py` (62 testes)
  - `test_stress.py` (30+ testes)
- **Cobertura reportada em 93%** (conforme README)
- **Fixtures e mocks** implementados para API keys

#### ❌ Problemas identificados
- **Sem testes E2E** para frontend – listado como pendente no TODO.md
- **Sem testes de integração real** – mocks para todas as APIs externas
- **Ausência de coverage enforcement** no CI – não bloqueia merge se cair
- **Scripts de validação manuais** (`validate_*.py`) fora da suíte pytest

#### 📁 Exemplos concretos
```
tests/
├── test_api.py                 # Testes de API básicos
├── test_billing_marketplace.py # 50KB – muito grande, candidato a split
└── test_stress.py              # Stress tests separados ✅
```

### 2.4 Configuração & Ambientes

#### ✅ O que está bom
- **`.env.example`** presente com variáveis essenciais
- **`.gitignore` bem configurado** – ignora `.env`, `.env.local`
- **docker-compose** com variáveis parametrizadas (`${VAR:-default}`)
- **Separação por profiles** (rag, cache, local-llm)

#### ❌ Problemas identificados
- **`.env.master` com 1300+ linhas** – arquivo de documentação, não de configuração
  - Risco: Commitado acidentalmente com chaves reais
- **Sem validação de env vars** – aplicação não falha cedo se faltar variável crítica
- **Múltiplos arquivos .env** – `.env`, `.env.complete`, `.env.master`, `.env.production`
  - Consequência: Confusão sobre qual usar, risco de configuração inconsistente
- **Chaves reais em `.env.master`** – observado valores de Sentry, PostHog, Mapbox, etc.

#### 📁 Exemplos concretos
```
.env                 # 5KB - usado em runtime
.env.complete        # 56KB - referência?
.env.master          # 135KB - documentação com chaves reais ⚠️
.env.example         # 2.4KB - template para devs
.env.production      # 4.7KB - para Netlify?
```

### 2.5 Infraestrutura & Deploy

#### ✅ O que está bom
- **docker-compose.yml** bem estruturado com healthchecks
- **Profiles para serviços opcionais** – ChromaDB, Redis, Ollama
- **Scripts de deploy automatizados** – `auto_deploy_railway.ps1`, `auto_deploy_netlify.ps1`
- **GitHub Actions** com jobs paralelos (lint, test, build)
- **Netlify.toml** configurado para frontend

#### ❌ Problemas identificados
- **Sem ambiente de staging** – deploy direto para produção
  - Consequência: Bugs descobertos apenas em produção
- **Dockerfile sem multi-stage otimizado** – pode ser melhorado para cache
- **Dependência de scripts PowerShell** – não funciona em Linux/Mac sem adaptação
- **railway.json presente** mas deploy pode ser manual

#### 📁 Exemplos concretos
```yaml
# docker-compose.yml - Healthcheck ✅
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request..."]
  interval: 30s
  timeout: 10s
```

### 2.6 Observabilidade

#### ✅ O que está bom
- **Módulo `src/observability/`** com 6 arquivos
- **Módulo `src/audit/`** para logging de ações
- **Sentry configurado** (chaves em .env.master)
- **PostHog configurado** (analytics)
- **Langfuse/LangSmith** listados para LLM tracing

#### ❌ Problemas identificados
- **Logging básico** – `logging.basicConfig` sem estruturação JSON
- **Sem health checks detalhados** – apenas `/health` básico
- **Métricas não expostas** – sem Prometheus/OpenTelemetry
- **Sem alertas configurados** – Sentry existe mas sem rules definidas

#### 📁 Exemplos concretos
```python
# server.py:32-35 - Logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# ❌ Não é JSON estruturado, dificulta parsing em produção
```

### 2.7 DX & Governança

#### ✅ O que está bom
- **README.md** completo com badges, quick start, endpoints
- **TODO.md** com roadmap e métricas
- **docs/** com 50+ arquivos de documentação
- **Scripts úteis** – `auto_validate.ps1`, `smoke_test_api.ps1`
- **CHANGELOG.md** presente

#### ❌ Problemas identificados
- **Sem pre-commit hooks** – lint/format não rodado antes do commit
- **Sem template de PR/Issue** – `.github/PULL_REQUEST_TEMPLATE.md` ausente
- **Onboarding > 30 min** – múltiplos arquivos .env, entry points confusos
- **CONTRIBUTING.md ausente** – instruções de contribuição genéricas no README

---

## 3. Princípios Norteadores das Melhorias

1. **Fail Fast** – Validar configurações na inicialização, não em runtime
2. **Single Source of Truth** – Um `.env.example` autoritativo, demais como referência
3. **CI que Bloqueia** – Lint, tipos e testes devem falhar o build se houver erros
4. **Onboarding < 15min** – Dev novo deve conseguir rodar o projeto rapidamente
5. **Observabilidade desde o início** – Logs estruturados, métricas expostas
6. **Staging antes de Prod** – Nenhum deploy direto para produção
7. **Automação de Qualidade** – Pre-commit hooks, PR templates, CODEOWNERS

---

## 4. Plano Faseado de Implementação

### Fase 0 – Diagnóstico & Fundamentos Mínimos

**Objetivo:** Corrigir problemas críticos de configuração e CI que mascaram erros.

**Critérios de Sucesso:**
- [ ] CI falha se lint/typecheck tiver erros
- [ ] Variáveis de ambiente validadas na inicialização
- [ ] Entry point único e documentado
- [ ] `.env.master` sem chaves reais commitadas

**Escopo:** Configuração, CI, Segurança básica

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 0.1 | Remover `\|\| true` dos jobs de lint/typecheck no CI | P0 |
| 0.2 | Criar `src/config/env_validator.py` com validação fail-fast | P0 |
| 0.3 | Mover chaves reais do `.env.master` para vault/secrets | P0 |
| 0.4 | Definir `server.py` como único entry point, deprecar `app.py` | P1 |
| 0.5 | Atualizar `.env.example` como fonte autoritativa | P1 |

**Riscos:** Pode quebrar deploy se env vars não estiverem configuradas corretamente.

---

### Fase 1 – Organização & Arquitetura Básica

**Objetivo:** Simplificar estrutura de configuração e melhorar modularidade.

**Critérios de Sucesso:**
- [ ] Um único arquivo `.env.example` com todas as variáveis documentadas
- [ ] Módulos grandes divididos ou documentados
- [ ] Tipos Python verificados pelo mypy sem `|| true`

**Escopo:** Arquitetura, Configuração, Tipos

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 1.1 | Consolidar arquivos .env (manter .env + .env.example) | P1 |
| 1.2 | Criar referência de env vars (→ `docs/50-operacao/54-env-reference.md`) | P1 |
| 1.3 | Configurar mypy com `strict` e corrigir erros gradualmente | P2 |
| 1.4 | Adicionar `py.typed` ao `src/` para distribuição de tipos | P2 |
| 1.5 | Documentar arquitetura de `flow_studio/` (módulo mais complexo) | P2 |

**Riscos:** Refatoração de tipos pode ser trabalhosa em módulos legados.

---

### Fase 2 – Qualidade de Código & Testes

**Objetivo:** Garantir que erros sejam detectados antes de chegar em produção.

**Critérios de Sucesso:**
- [ ] Cobertura de testes > 85% com enforcement no CI
- [ ] Testes E2E básicos para fluxos críticos do frontend
- [ ] Zero warnings de lint no CI

**Escopo:** Testes, Lint, Coverage

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 2.1 | Configurar pytest-cov com threshold mínimo (80%) no CI | P1 |
| 2.2 | [OPCIONAL] Adicionar Playwright para testes E2E do frontend | P1 |
| 2.3 | Corrigir warnings de CSS inline e acessibilidade no frontend | P2 |
| 2.4 | Mover scripts `validate_*.py` para suíte pytest | P2 |
| 2.5 | Criar `tests/e2e/` com smoke tests de fluxos críticos | P2 |

**Riscos:** Testes E2E requerem ambiente de CI mais complexo.

---

### Fase 3 – Infraestrutura & Deploy

**Objetivo:** Criar ambiente de staging e melhorar pipeline de deploy.

**Critérios de Sucesso:**
- [ ] Ambiente de staging funcional
- [ ] Deploy automatizado via GitHub Actions (não scripts locais)
- [ ] Rollback documentado e testado

**Escopo:** CI/CD, Infraestrutura, Deploy

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 3.1 | Criar branch `staging` com deploy automático para ambiente de teste | P1 |
| 3.2 | Migrar deploy para GitHub Actions (remover dependência de PS1) | P1 |
| 3.3 | Documentar processo de rollback no Railway/Netlify | P2 |
| 3.4 | [OPCIONAL] Implementar deploy preview para PRs no Netlify | P2 |
| 3.5 | Otimizar Dockerfile com multi-stage build | P3 |

**Riscos:** Staging pode ter custo adicional dependendo do provider.

---

### Fase 4 – Observabilidade, Performance & Robustez

**Objetivo:** Garantir visibilidade do sistema em produção e melhorar resiliência.

**Critérios de Sucesso:**
- [ ] Logs estruturados em JSON
- [ ] Métricas básicas expostas (latência, erros, requests)
- [ ] Alertas configurados para erros críticos

**Escopo:** Observabilidade, Logging, Alertas

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 4.1 | Implementar logging JSON estruturado (python-json-logger) | P1 |
| 4.2 | Criar endpoint `/health/detailed` com status de dependências | P1 |
| 4.3 | Configurar alertas no Sentry para erros críticos | P2 |
| 4.4 | [OPCIONAL] Expor métricas Prometheus em `/metrics` | P2 |
| 4.5 | [OPCIONAL] Implementar tracing com OpenTelemetry | P3 |

**Riscos:** Overhead de observabilidade em ambientes com muitas requisições.

---

### Fase 5 – DX & Governança Técnica

**Objetivo:** Melhorar experiência do desenvolvedor e governança do código.

**Critérios de Sucesso:**
- [ ] Onboarding de dev novo < 15 minutos
- [ ] Pre-commit hooks rodando lint/format
- [ ] Templates de PR/Issue configurados

**Escopo:** DX, Governança, Documentação

**Entregáveis:**

| ID | Tarefa | Prioridade |
|----|--------|------------|
| 5.1 | Implementar pre-commit com black, ruff, mypy | P1 |
| 5.2 | Criar `.github/PULL_REQUEST_TEMPLATE.md` | P1 |
| 5.3 | Criar `CONTRIBUTING.md` com guia de contribuição | P2 |
| 5.4 | Adicionar `CODEOWNERS` para áreas críticas | P2 |
| 5.5 | [OPCIONAL] Configurar Renovate/Dependabot para updates automáticos | P3 |

**Riscos:** Pre-commit pode ser lento se incluir muitas verificações.

---

## 5. Roadmap Resumido

| Fase | Foco Principal | Impacto Esperado | Estimativa |
|------|----------------|------------------|------------|
| **0** | Fundamentos & CI | Alto – elimina erros silenciados | 1-2 dias |
| **1** | Organização | Médio – simplifica configuração | 2-3 dias |
| **2** | Testes | Alto – previne regressões | 3-5 dias |
| **3** | Deploy & Staging | Alto – segurança em releases | 2-3 dias |
| **4** | Observabilidade | Médio – visibilidade em prod | 2-4 dias |
| **5** | DX & Governança | Médio – produtividade do time | 1-2 dias |

---

## 6. Top 5 Ações Imediatas (Próximos 2 dias)

| # | Ação | Impacto | Arquivo/Local |
|---|------|---------|---------------|
| 1 | **Remover `\|\| true`** dos jobs de lint no CI | Crítico | `.github/workflows/ci.yml` |
| 2 | **Criar validador de env vars** com fail-fast | Crítico | `src/config/env_validator.py` |
| 3 | **Mover chaves reais** do `.env.master` para secrets | Segurança | `.env.master`, GitHub Secrets |
| 4 | **Definir entry point único** (`server.py`) | Clareza | `README.md`, `Procfile` |
| 5 | **Atualizar `.env.example`** como fonte autoritativa | Onboarding | `.env.example` |

---

## 7. Recomendações Finais

### 7.1 Governança
- **Code Review obrigatório** para branches `main` e `staging`
- **Squash merge** para manter histórico limpo
- **Branch protection** com checks obrigatórios (lint, test, build)

### 7.2 Ferramentas Recomendadas (respeitando stack existente)
- **pre-commit** – Já usa black/ruff, apenas automatizar
- **python-json-logger** – Logs estruturados compatíveis com FastAPI
- **Playwright** – E2E tests para Next.js (recomendação oficial)
- **Renovate** – Updates automáticos de dependências

### 7.3 Próximos Passos Além do Escopo
- **Internacionalização (i18n)** – Se houver plano de expansão
- **Rate limiting avançado** – Já existe básico, pode ser expandido
- **Multi-tenancy** – Módulo `enterprise/` sugere que pode ser necessário
- **SDK Python publicado no PyPI** – Listado no TODO.md como futuro

---

*Este documento é a visão macro/estratégica. Para execução diária, consulte `todo.md`.*

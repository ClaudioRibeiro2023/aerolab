# 📋 Proposta de Melhorias Arquiteturais - Template Platform

**Data:** Dezembro/2024  
**Versão:** 1.0  
**Autor:** Análise Arquitetural Automatizada

---

## 1. Visão Geral do Projeto

### 1.1 Identificação

| Atributo                   | Valor                                                     |
| -------------------------- | --------------------------------------------------------- |
| **Tipo de Aplicação**      | Monorepo (Frontend React + API Template FastAPI)          |
| **Stack Principal**        | React 18, TypeScript, Vite, TailwindCSS, FastAPI (Python) |
| **Gerenciador de Pacotes** | pnpm 9.x com workspaces                                   |
| **Autenticação**           | Keycloak/OIDC com bypass para desenvolvimento             |
| **Infraestrutura**         | Docker Compose (PostgreSQL, Redis, Keycloak)              |
| **Testes**                 | Playwright (E2E)                                          |

### 1.2 Propósito

Template corporativo para criação de aplicações web com:

- Sistema de roles (ADMIN, GESTOR, OPERADOR, VIEWER)
- Design System compartilhado
- Autenticação OIDC pronta para produção
- Stack Docker completa

### 1.3 Estado Atual: Resumo Executivo

#### ✅ Pontos Fortes

1. **Estrutura de Monorepo Sólida** — Separação clara entre `apps/`, `packages/`, `infra/`
2. **TypeScript Bem Configurado** — Strict mode ativo, configuração base compartilhada
3. **Sistema de Autenticação Flexível** — OIDC real + bypass para desenvolvimento/E2E
4. **Docker Compose Completo** — PostgreSQL, Redis, Keycloak configurados
5. **Testes E2E Configurados** — Playwright com setup funcional
6. **Documentação Inicial** — README detalhado, docs básicas presentes
7. **Design System Estruturado** — Package dedicado para componentes UI
8. **Build de Produção Funcional** — Vite com code-splitting configurado

#### ⚠️ Principais Riscos e Dívidas Técnicas

1. **Duplicação de Código de Auth** — `AuthContext` existe em dois lugares (`apps/web/src/contexts/` e `packages/shared/src/auth/`)
2. **Pastas Estruturais Vazias** — `src/hooks/`, `src/services/`, `src/modules/`, `src/types/` sem implementação
3. **Ausência de Testes Unitários** — Apenas E2E configurado
4. **API Template Minimalista** — Sem autenticação real, estrutura básica
5. **Falta de CI/CD** — Nenhum pipeline configurado (`.github/workflows/` ausente)
6. **Configurações de Lint/Format Implícitas** — Sem `.eslintrc`, `.prettierrc` explícitos na raiz
7. **Rotas Placeholder** — Várias rotas apontam para a mesma página (`HomePage`)
8. **Falta de Error Boundary** — Sem tratamento global de erros no React
9. **Observabilidade Ausente** — Sem logging estruturado ou métricas

---

## 2. Diagnóstico Estruturado

### 2.1 Arquitetura & Organização

#### ✅ O que está bom

- **Monorepo bem estruturado** com separação clara:
  ```
  apps/web/          → Aplicação principal
  packages/
    design-system/   → Componentes UI
    shared/          → Lógica compartilhada
    types/           → Tipos TypeScript
  infra/             → Docker e configurações
  ```
- **Packages com exports bem definidos** via `package.json`
- **Aliases configurados** (`@/`, `@design-system/`) no Vite
- **Separação de contextos** (auth, navigation) começando a emergir

#### ⚠️ O que precisa melhorar

| Problema                       | Localização                                                                           | Impacto                               |
| ------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------- |
| Duplicação de AuthContext      | `apps/web/src/contexts/AuthContext.tsx` vs `packages/shared/src/auth/AuthContext.tsx` | Confusão, manutenção duplicada        |
| Pastas vazias sem utilidade    | `src/hooks/`, `src/services/`, `src/modules/`, `src/types/`                           | Estrutura incompleta, falta de padrão |
| Lógica no App.tsx              | Rotas e imports concentrados em `App.tsx`                                             | Difícil manutenção quando escalar     |
| Config de auth em dois lugares | `src/config/auth.ts` + `packages/shared/src/auth/oidcConfig.ts`                       | Duplicação de configuração            |

#### 🚨 Riscos

- **Escalar sem padrão definido** levará a inconsistências entre módulos
- **Novos desenvolvedores** não saberão qual AuthContext usar

### 2.2 Qualidade de Código

#### ✅ O que está bom

- **TypeScript strict** habilitado com regras rigorosas
- **Nomes de arquivos e componentes** claros e em PascalCase
- **Hooks de autenticação** bem implementados (`useAuth`, `hasRole`, `hasAnyRole`)
- **Componentes funcionais** com React moderno (hooks, context)

#### ⚠️ O que precisa melhorar

| Problema                             | Exemplo                                                     | Recomendação                           |
| ------------------------------------ | ----------------------------------------------------------- | -------------------------------------- |
| Tipos inline                         | Tipos definidos dentro de `AuthContext.tsx`                 | Extrair para `@template/types`         |
| API client básico                    | `packages/shared/src/api/client.ts` sem retry, interceptors | Implementar estratégias de resiliência |
| Formatters/Helpers genéricos         | `packages/shared/src/utils/` pouco populado                 | Adicionar utilities comuns             |
| Falta de barrel exports consistentes | Alguns `index.ts` incompletos                               | Padronizar exports                     |

### 2.3 Testes

#### ✅ O que está bom

- **Playwright configurado** com projetos para Chrome e Firefox
- **WebServer integrado** no config (inicia dev server automaticamente)
- **9 testes E2E funcionais** cobrindo navegação e auth demo
- **Scripts prontos** (`test:e2e`, `test:e2e:ui`, `test:e2e:headed`)

#### ⚠️ O que precisa melhorar

| Problema                       | Impacto                                     | Prioridade |
| ------------------------------ | ------------------------------------------- | ---------- |
| Zero testes unitários          | Regressões não detectadas em lógica isolada | Alta       |
| Sem teste de integração de API | API client não testado                      | Média      |
| Cobertura desconhecida         | Sem métricas de cobertura configuradas      | Média      |
| Testes E2E não testam erros    | Apenas happy path                           | Baixa      |

#### 🎯 Recomendação

- Adicionar **Vitest** para testes unitários (integração nativa com Vite)
- Configurar **coverage** com threshold mínimo
- Criar testes para hooks (`useAuth`) e utils (`formatters`)

### 2.4 Configuração & Ambientes

#### ✅ O que está bom

- **`.env.example`** presente com todas as variáveis documentadas
- **Variáveis de ambiente tipadas** via `import.meta.env`
- **Demo mode** bem implementado para desenvolvimento
- **`.gitignore`** completo e bem organizado

#### ⚠️ O que precisa melhorar

| Problema                  | Arquivo                                   | Ação                                       |
| ------------------------- | ----------------------------------------- | ------------------------------------------ |
| `.env` commitado          | `apps/web/.env` (336 bytes)               | Remover do git, usar apenas `.env.example` |
| Sem validação de env vars | Startup não valida variáveis obrigatórias | Usar `zod` ou similar para validar         |
| Sem env para staging      | Apenas dev/prod implícitos                | Criar `.env.staging.example`               |

### 2.5 Infraestrutura & Deploy

#### ✅ O que está bom

- **Docker Compose completo** com healthchecks
- **Dockerfile para web** com nginx
- **Dockerfile para API** presente
- **Volumes persistentes** para dados (PostgreSQL, Redis)
- **Proxy configurado** no Vite para desenvolvimento

#### ⚠️ O que precisa melhorar

| Problema                         | Impacto                               | Ação                             |
| -------------------------------- | ------------------------------------- | -------------------------------- |
| Sem CI/CD                        | Deploy manual, sem automação          | Criar workflows GitHub Actions   |
| Pasta `db/` vazia                | Sem migrations ou seeds SQL           | Definir estratégia de migrations |
| Sem multi-stage build            | Imagens Docker maiores que necessário | Otimizar Dockerfiles             |
| Credenciais hardcoded no compose | `admin/admin`, `template/template`    | Usar env vars ou secrets         |

#### 🎯 Recomendação Prioritária

Criar pipelines para:

1. **CI** — Lint, typecheck, testes em cada PR
2. **CD** — Build e push de imagens Docker
3. **Preview** — Ambientes efêmeros para PRs

### 2.6 Observabilidade

#### ⚠️ Estado Atual: Insuficiente

| Aspecto        | Estado                     | Necessidade                          |
| -------------- | -------------------------- | ------------------------------------ |
| Logging        | `console.log/error` básico | Logger estruturado (JSON)            |
| Error tracking | Inexistente                | Sentry ou similar                    |
| Métricas       | Inexistente                | Prometheus/Grafana                   |
| Tracing        | Inexistente                | OpenTelemetry                        |
| Error Boundary | Inexistente                | Componente React para catch de erros |

#### 🎯 Recomendação

- Implementar **Error Boundary** global no React
- Adicionar **logging estruturado** na API (structlog/loguru)
- Configurar **health checks** mais detalhados

### 2.7 DX (Developer Experience) & Governança

#### ✅ O que está bom

- **Scripts úteis** no `package.json` raiz (`dev`, `build`, `lint`, `typecheck`)
- **Script de clean** para limpar node_modules e dist
- **Script de setup** presente (embora básico)
- **Documentação** inicial presente em `docs/`
- **README** detalhado com quick start

#### ⚠️ O que precisa melhorar

| Problema                      | Impacto                                 | Ação                           |
| ----------------------------- | --------------------------------------- | ------------------------------ |
| Sem Prettier config explícita | Formatação inconsistente                | Criar `.prettierrc`            |
| Sem ESLint config na raiz     | Cada package configura individualmente  | Centralizar config             |
| Sem husky/lint-staged         | Código não formatado pode ser commitado | Adicionar pre-commit hooks     |
| Sem commitlint                | Mensagens de commit inconsistentes      | Adicionar conventional commits |
| Sem CONTRIBUTING.md           | Novos devs sem guia de contribuição     | Criar documento                |
| Sem template de PR/Issue      | PRs sem padrão                          | Criar templates GitHub         |

---

## 3. Princípios Norteadores das Melhorias

Os seguintes princípios guiarão todas as melhorias propostas:

1. **Single Source of Truth** — Eliminar duplicações, centralizar configurações
2. **Convenção sobre Configuração** — Padrões claros reduzem decisões e inconsistências
3. **Fail Fast** — Validar configs, tipos e erros o mais cedo possível
4. **Testabilidade** — Código deve ser facilmente testável (injeção de dependências, separação de concerns)
5. **Observabilidade desde o Início** — Logs, métricas e error tracking não são opcionais
6. **Onboarding < 30min** — Um novo dev deve conseguir rodar o projeto em menos de 30 minutos
7. **Automação > Documentação** — Preferir CI/CD e scripts a processos manuais documentados

---

## 4. Plano Faseado de Implementação

### Fase 0 – Diagnóstico & Fundamentos Mínimos

**Objetivo:** Eliminar dívidas críticas e estabelecer base sólida para evoluções.

**Critérios de Sucesso:**

- [x] Nenhum arquivo sensível (`.env`) no repositório
- [x] AuthContext único e documentado
- [x] Pastas vazias removidas ou com README explicativo
- [x] Scripts de validação rodando corretamente

**Escopo:** Limpeza, padronização mínima, documentação de decisões.

**Entregáveis Principais:**

| #   | Entregável                                                                                            | Prioridade |
| --- | ----------------------------------------------------------------------------------------------------- | ---------- |
| 0.1 | Remover `apps/web/.env` do git, adicionar ao `.gitignore`                                             | P0         |
| 0.2 | Unificar AuthContext (manter apenas em `packages/shared`)                                             | P0         |
| 0.3 | Unificar config de OIDC (remover `src/config/auth.ts`, usar `packages/shared/src/auth/oidcConfig.ts`) | P0         |
| 0.4 | Remover ou documentar pastas vazias (`src/hooks/`, `src/services/`, etc.)                             | P1         |
| 0.5 | Validar e atualizar `VALIDATION_CHECKLIST.md`                                                         | P1         |
| 0.6 | Criar arquivo `ARCHITECTURE.md` documentando decisões                                                 | P2         |

**Riscos & Dependências:**

- Mudança no AuthContext pode quebrar imports em `apps/web`

---

### Fase 1 – Organização & Arquitetura Básica

**Objetivo:** Estabelecer estrutura escalável e padrões claros para novos módulos.

**Critérios de Sucesso:**

- [x] Estrutura de módulos definida e documentada
- [x] Pelo menos um módulo de exemplo seguindo o padrão
- [x] Tipos centralizados em `@template/types`
- [x] Router refatorado para lazy loading

**Escopo:** Arquitetura de pastas, tipagem, roteamento.

**Entregáveis Principais:**

| #   | Entregável                                                                | Prioridade |
| --- | ------------------------------------------------------------------------- | ---------- |
| 1.1 | Definir e documentar estrutura padrão de módulos em `src/modules/[nome]/` | P0         |
| 1.2 | Migrar tipos de `AuthContext.tsx` para `@template/types`                  | P0         |
| 1.3 | Implementar lazy loading nas rotas (`React.lazy` + `Suspense`)            | P1         |
| 1.4 | Criar módulo de exemplo completo com estrutura padrão                     | P1         |
| 1.5 | Implementar Error Boundary global                                         | P1         |
| 1.6 | Refatorar `App.tsx` para usar route config object                         | P2         |

**Riscos & Dependências:**

- Depende da Fase 0 (AuthContext unificado)
- Lazy loading pode afetar testes E2E (aguardar loading states)

---

### Fase 2 – Qualidade de Código & Testes

**Objetivo:** Garantir qualidade através de automação e cobertura de testes.

**Critérios de Sucesso:**

- [x] ESLint e Prettier configurados na raiz
- [x] Husky + lint-staged rodando em pre-commit
- [x] Vitest configurado com pelo menos 5 testes unitários
- [x] Coverage mínimo de 40% em `packages/shared`

**Escopo:** Linting, formatação, testes unitários.

**Entregáveis Principais:**

| #   | Entregável                                                 | Prioridade |
| --- | ---------------------------------------------------------- | ---------- |
| 2.1 | Criar `.eslintrc.cjs` na raiz com config compartilhada     | P0         |
| 2.2 | Criar `.prettierrc` e `.prettierignore` na raiz            | P0         |
| 2.3 | Instalar e configurar Husky + lint-staged                  | P0         |
| 2.4 | Instalar e configurar Vitest em `packages/shared`          | P1         |
| 2.5 | Criar testes unitários para `formatters.ts` e `helpers.ts` | P1         |
| 2.6 | Criar testes para `apiClient` (com mocks)                  | P1         |
| 2.7 | Configurar coverage report e definir thresholds            | P2         |
| 2.8 | Adicionar testes para hooks de autenticação                | P2         |

**Riscos & Dependências:**

- Vitest precisa de config específica para monorepo

---

### Fase 3 – Infraestrutura & Deploy

**Objetivo:** Automatizar CI/CD e garantir deploys confiáveis.

**Critérios de Sucesso:**

- [x] Pipeline de CI rodando em cada PR (lint, typecheck, test)
- [x] Pipeline de CD para build de imagens Docker
- [x] Credenciais removidas do docker-compose (usar env vars)
- [x] Documentação de deploy atualizada

**Escopo:** GitHub Actions, Docker, documentação de deploy.

**Entregáveis Principais:**

| #   | Entregável                                                         | Prioridade |
| --- | ------------------------------------------------------------------ | ---------- |
| 3.1 | Criar `.github/workflows/ci.yml` (lint, typecheck, test)           | P0         |
| 3.2 | Criar `.github/workflows/docker.yml` (build images)                | P1         |
| 3.3 | Refatorar `docker-compose.yml` para usar env vars                  | P1         |
| 3.4 | Criar `docker-compose.override.yml` para desenvolvimento           | P1         |
| 3.5 | Otimizar Dockerfiles com multi-stage build                         | P2         |
| 3.6 | Criar templates de PR e Issue (`.github/PULL_REQUEST_TEMPLATE.md`) | P2         |
| 3.7 | Documentar processo de deploy em `docs/DEPLOY.md`                  | P2         |

**Riscos & Dependências:**

- CI precisa de secrets configurados no GitHub
- Testes E2E no CI requerem setup de Playwright

---

### Fase 4 – Observabilidade, Performance & Robustez

**Objetivo:** Garantir visibilidade em produção e resiliência a falhas.

**Critérios de Sucesso:**

- [x] Error Boundary capturando erros não tratados
- [x] Logging estruturado na API
- [x] Health checks detalhados implementados
- [x] API client com retry e timeout configuráveis

**Escopo:** Error handling, logging, resiliência.

**Entregáveis Principais:**

| #   | Entregável                                                      | Prioridade |
| --- | --------------------------------------------------------------- | ---------- |
| 4.1 | Implementar Error Boundary com fallback UI                      | P0         |
| 4.2 | Adicionar logging estruturado na API FastAPI (loguru/structlog) | P1         |
| 4.3 | Implementar retry com backoff exponencial no apiClient          | P1         |
| 4.4 | Criar health check detalhado (`/health/ready`, `/health/live`)  | P1         |
| 4.5 | Configurar Sentry ou similar para error tracking (opcional)     | P2         |
| 4.6 | Adicionar request/response logging no apiClient                 | P2         |
| 4.7 | Implementar circuit breaker pattern (opcional)                  | P3         |

**Riscos & Dependências:**

- Sentry requer conta e configuração de DSN

---

### Fase 5 – DX & Governança Técnica

**Objetivo:** Maximizar produtividade do time e padronizar contribuições.

**Critérios de Sucesso:**

- [x] Onboarding de novo dev em < 30 minutos
- [x] Conventional commits enforçados
- [x] ADRs documentando decisões arquiteturais
- [x] Scripts de automação para tarefas comuns

**Escopo:** Documentação, convenções, automação.

**Entregáveis Principais:**

| #   | Entregável                                                         | Prioridade |
| --- | ------------------------------------------------------------------ | ---------- |
| 5.1 | Criar `CONTRIBUTING.md` com guia de contribuição                   | P0         |
| 5.2 | Configurar commitlint + conventional commits                       | P1         |
| 5.3 | Criar script `scripts/new-module.js` para scaffolding de módulos   | P1         |
| 5.4 | Criar pasta `docs/adr/` com template de ADR                        | P2         |
| 5.5 | Adicionar script de validação de ambiente (`scripts/check-env.js`) | P2         |
| 5.6 | Criar `docs/TROUBLESHOOTING.md` com problemas comuns               | P2         |
| 5.7 | Configurar Renovate/Dependabot para updates de deps                | P3         |

**Riscos & Dependências:**

- Commitlint pode frustrar desenvolvedores não familiarizados

---

## 5. Roadmap Resumido

| Fase  | Foco Principal                    | Impacto Esperado                    | Estimativa |
| ----- | --------------------------------- | ----------------------------------- | ---------- |
| **0** | Diagnóstico + Fundamentos Mínimos | Base estável, sem duplicações       | 1-2 dias   |
| **1** | Arquitetura & Organização         | Código modular e escalável          | 2-3 dias   |
| **2** | Testes & Qualidade de Código      | Menos bugs, regressões detectadas   | 3-4 dias   |
| **3** | Infraestrutura & Deploy           | Deploy automatizado e confiável     | 2-3 dias   |
| **4** | Observabilidade & Robustez        | Visibilidade em prod, resiliência   | 2-3 dias   |
| **5** | DX & Governança                   | Time mais produtivo, padrões claros | 2-3 dias   |

**Total Estimado:** 12-18 dias de trabalho (1 desenvolvedor)

---

## 6. Recomendações Finais

### 6.1 Governança de Código

- **Code Review obrigatório** — Nenhum PR mergeado sem aprovação
- **Branch protection** — `main` protegida, merge apenas via PR
- **Squash merge** — Histórico limpo, um commit por feature

### 6.2 Ferramentas Recomendadas

| Categoria        | Ferramenta                  | Motivo                             |
| ---------------- | --------------------------- | ---------------------------------- |
| Testes Unitários | Vitest                      | Integração nativa com Vite, rápido |
| Formatação       | Prettier                    | Padrão de mercado, zero config     |
| Linting          | ESLint + @typescript-eslint | Catch de bugs em tempo de dev      |
| Pre-commit       | Husky + lint-staged         | Garantir qualidade antes do commit |
| Commits          | Commitlint                  | Mensagens padronizadas             |
| Error Tracking   | Sentry                      | Padrão de mercado, bom free tier   |
| Deps Updates     | Renovate                    | Mais configurável que Dependabot   |

### 6.3 Próximos Passos Além do Escopo

Após completar as 5 fases, considerar:

1. **Storybook** — Documentação visual do Design System
2. **OpenAPI/Swagger** — Documentação automática da API
3. **Feature Flags** — LaunchDarkly ou similar para releases graduais
4. **i18n** — Internacionalização se necessário
5. **PWA** — Service Worker para offline support
6. **Microfrontends** — Se o projeto escalar para múltiplos times

---

## 7. Conclusão

O **Template Platform** possui uma base sólida, com escolhas tecnológicas modernas e estrutura de monorepo bem pensada. As principais dívidas técnicas são gerenciáveis e concentram-se em:

1. **Duplicações** que precisam ser eliminadas
2. **Testes unitários** que precisam ser implementados
3. **CI/CD** que precisa ser criado
4. **Observabilidade** que precisa ser adicionada

O plano faseado proposto permite evolução incremental, onde **cada fase entrega valor independente**. Recomenda-se iniciar pela **Fase 0** imediatamente, pois elimina riscos de segurança (`.env` no git) e confusão arquitetural (AuthContext duplicado).

---

_Documento gerado como parte da análise arquitetural do repositório Template Platform._

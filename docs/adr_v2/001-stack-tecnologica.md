---
id: 'ADR-001'
title: 'Stack Tecnológica'
status: 'accepted'
date: '2024-12-16'
owners:
  - 'Equipe de Arquitetura'
tags:
  - 'stack'
  - 'frontend'
  - 'backend'
  - 'infraestrutura'
related: []
supersedes: null
superseded_by: null
---

# ADR-001: Stack Tecnológica

## 1. Contexto e Problema

O projeto AeroLab necessita de uma stack tecnológica moderna que atenda aos seguintes requisitos:

- **Produtividade** - Desenvolvimento rápido com boa DX (Developer Experience)
- **Manutenibilidade** - Código tipado e fácil de manter a longo prazo
- **Performance** - Carregamento rápido e boa experiência do usuário
- **Escalabilidade** - Suporte a crescimento de funcionalidades e usuários
- **Ecossistema** - Bibliotecas maduras e comunidade ativa
- **Contratação** - Tecnologias com boa disponibilidade de profissionais

> **Problema central:** Definir a stack tecnológica que maximize produtividade sem comprometer qualidade e manutenibilidade.

## 2. Drivers de Decisão

- **DR1:** Developer Experience (DX) - Velocidade de desenvolvimento
- **DR2:** Type Safety - Redução de bugs em runtime
- **DR3:** Performance - Experiência do usuário final
- **DR4:** Talent Pool - Facilidade de contratação

Priorização: DR1 > DR2 > DR3 > DR4

## 3. Decisão

> **Decidimos:** Adotar React 18 + TypeScript + Vite no frontend, FastAPI + Python no backend, e pnpm como gerenciador de pacotes em um monorepo.

### Stack Completa

**Frontend:**

| Tecnologia     | Versão | Arquivo de Referência          |
| -------------- | ------ | ------------------------------ |
| React          | 18.2.x | `apps/web/package.json`        |
| TypeScript     | 5.3.x  | `tsconfig.base.json`           |
| Vite           | 5.x    | `apps/web/vite.config.ts`      |
| TailwindCSS    | 3.3.x  | `apps/web/tailwind.config.js`  |
| TanStack Query | 5.12.x | `apps/web/package.json`        |
| React Router   | 6.20.x | `apps/web/package.json`        |
| oidc-client-ts | 2.4.x  | `packages/shared/package.json` |

**Backend:**

| Tecnologia | Versão | Arquivo de Referência           |
| ---------- | ------ | ------------------------------- |
| FastAPI    | ≥0.104 | `api-template/requirements.txt` |
| Python     | 3.11+  | Runtime requirement             |
| Pydantic   | ≥2.5   | `api-template/requirements.txt` |
| SQLAlchemy | ≥2.0   | `api-template/requirements.txt` |
| Alembic    | ≥1.13  | `api-template/requirements.txt` |
| Redis      | ≥5.0   | `api-template/requirements.txt` |
| Structlog  | ≥24.1  | `api-template/requirements.txt` |

**Infraestrutura:**

| Tecnologia     | Versão | Arquivo de Referência       |
| -------------- | ------ | --------------------------- |
| PostgreSQL     | 15     | `infra/docker-compose.yml`  |
| Redis          | 7      | `infra/docker-compose.yml`  |
| Keycloak       | 23     | `infra/docker-compose.yml`  |
| Docker Compose | 2.x    | `infra/docker-compose.yml`  |
| Kubernetes     | -      | `infra/k8s/deployment.yaml` |

**Tooling:**

| Tecnologia | Versão | Arquivo de Referência           |
| ---------- | ------ | ------------------------------- |
| pnpm       | 9.15.x | `package.json` (packageManager) |
| ESLint     | 8.55.x | `package.json`                  |
| Prettier   | 3.x    | `package.json`                  |
| Playwright | 1.56.x | `apps/web/package.json`         |
| Vitest     | 4.x    | `apps/web/package.json`         |

### Escopo

- **Afeta:** Todo o projeto
- **Não afeta:** Infraestrutura de rede/DNS externa

## 4. Alternativas Consideradas

### Alternativa A: Vue.js 3 + Nuxt

| Aspecto | Avaliação                                       |
| ------- | ----------------------------------------------- |
| Prós    | Curva de aprendizado menor, SFCs intuitivos     |
| Contras | Ecossistema menor, menos componentes enterprise |
| Esforço | Médio                                           |
| Risco   | Médio (menos profissionais disponíveis)         |

**Por que descartada:** Menor disponibilidade de profissionais no mercado brasileiro.

### Alternativa B: Angular

| Aspecto | Avaliação                           |
| ------- | ----------------------------------- |
| Prós    | TypeScript nativo, solução completa |
| Contras | Verbosidade, bundle size maior      |
| Esforço | Alto                                |
| Risco   | Baixo                               |

**Por que descartada:** Curva de aprendizado íngreme, overhead para o escopo do projeto.

### Alternativa C: Node.js/NestJS no Backend

| Aspecto | Avaliação                                                    |
| ------- | ------------------------------------------------------------ |
| Prós    | Mesma linguagem frontend/backend                             |
| Contras | Performance inferior para CPU-bound, menos libs data science |
| Esforço | Médio                                                        |
| Risco   | Médio                                                        |

**Por que descartada:** FastAPI oferece melhor performance async e documentação automática OpenAPI.

## 5. Consequências e Trade-offs

### Positivas

- ✅ DX excepcional com Vite HMR + TypeScript
- ✅ Type safety end-to-end
- ✅ OpenAPI automático via FastAPI
- ✅ Grande pool de talentos React
- ✅ Comunidades ativas para todas as tecnologias

### Negativas

- ⚠️ Duas linguagens diferentes (TypeScript + Python)
- ⚠️ Overhead de setup inicial do monorepo
- ⚠️ Manter dependências de dois ecossistemas

### Riscos Identificados

| Risco                    | Probabilidade | Impacto | Mitigação                                   |
| ------------------------ | ------------- | ------- | ------------------------------------------- |
| Breaking changes em deps | Média         | Alto    | Lockfiles, CI com testes, upgrades graduais |
| Abandono de biblioteca   | Baixa         | Alto    | Preferir libs com grande comunidade         |

## 6. Impacto em Integrações e Contratos

### Breaking Changes

- [x] Não aplicável (decisão fundacional)

### Contratos Definidos

| Contrato | Especificação | Documentação                        |
| -------- | ------------- | ----------------------------------- |
| API REST | OpenAPI 3.1   | `http://localhost:8000/docs`        |
| Auth     | OIDC/JWT      | `docs/contratos-integracao/auth.md` |
| Tipos    | TypeScript    | `packages/types/`                   |

### Para Integradores

- **API:** FastAPI gera OpenAPI automaticamente em `/docs`
- **Tipos:** Disponíveis em `packages/types/` para clientes TypeScript
- **Auth:** JWT padrão, validar via JWKS em Keycloak

## 7. Plano de Rollout/Migração

### Status

✅ **Implementado** - Stack em uso desde a criação do projeto.

### Atualizações Futuras

1. Avaliar React 19 quando estável
2. Considerar Bun como runtime alternativo
3. Avaliar migração para Pydantic v3 quando disponível

## 8. Referências

### Internas

- [Arquitetura](../arquitetura/c4-container.md)
- [Setup Local](../operacao/setup-local.md)

### Externas

- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Guide](https://vitejs.dev/guide/)
- [pnpm Workspaces](https://pnpm.io/workspaces)

---

## Histórico

| Data       | Autor                 | Mudança              |
| ---------- | --------------------- | -------------------- |
| 2024-12-16 | Equipe de Arquitetura | Criação              |
| 2024-12-16 | Cascade               | Migração para ADR v2 |

---

_Migrado de `/docs/adr/001-stack-tecnologica.md`_

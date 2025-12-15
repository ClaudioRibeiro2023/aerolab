# Book de Testes - Template Platform

Este documento define a cobertura de testes mínima recomendada para a plataforma.

---

## 1. Mapeamento Funcional

### 1.1 Módulos Principais

| Módulo           | Descrição                           | Prioridade |
| ---------------- | ----------------------------------- | ---------- |
| **Autenticação** | Login, logout, refresh token, roles | P0         |
| **Dashboard**    | Home, métricas, widgets             | P1         |
| **ETL**          | Catálogo, execução, logs, qualidade | P1         |
| **Configuração** | Módulos, filtros, parâmetros        | P1         |
| **Usuários**     | CRUD, permissões, perfil            | P1         |
| **LGPD**         | Consentimento, meus dados, export   | P2         |
| **Analytics**    | Métricas, tracking, dashboard       | P2         |
| **Admin**        | Logs, health, API docs              | P2         |

### 1.2 Roles e Permissões

| Role       | Acesso                              |
| ---------- | ----------------------------------- |
| `ADMIN`    | Acesso total                        |
| `GESTOR`   | Configurações, usuários, relatórios |
| `OPERADOR` | ETL, execução, logs                 |
| `VIEWER`   | Somente leitura                     |

---

## 2. Testes de API (Backend)

### 2.1 Endpoints de Autenticação

| Endpoint            | Método | Cenário               | Resultado Esperado    |
| ------------------- | ------ | --------------------- | --------------------- |
| `/api/auth/login`   | POST   | Credenciais válidas   | 200, token JWT        |
| `/api/auth/login`   | POST   | Credenciais inválidas | 401, erro             |
| `/api/auth/login`   | POST   | Campos faltando       | 422, validação        |
| `/api/auth/refresh` | POST   | Token válido          | 200, novo token       |
| `/api/auth/refresh` | POST   | Token expirado        | 401, erro             |
| `/api/auth/logout`  | POST   | Sessão ativa          | 200, sessão encerrada |

### 2.2 Endpoints de Health

| Endpoint        | Método | Cenário     | Resultado Esperado           |
| --------------- | ------ | ----------- | ---------------------------- |
| `/health`       | GET    | Sistema ok  | 200, `{ status: "healthy" }` |
| `/health/live`  | GET    | App rodando | 200                          |
| `/health/ready` | GET    | Deps ok     | 200                          |
| `/health/ready` | GET    | DB offline  | 503                          |

### 2.3 Endpoints de Usuários

| Endpoint          | Método | Cenário           | Resultado Esperado     |
| ----------------- | ------ | ----------------- | ---------------------- |
| `/api/users`      | GET    | Admin autenticado | 200, lista de usuários |
| `/api/users`      | GET    | Sem autenticação  | 401                    |
| `/api/users`      | GET    | Role VIEWER       | 403                    |
| `/api/users/{id}` | GET    | ID válido         | 200, dados do usuário  |
| `/api/users/{id}` | GET    | ID inválido       | 404                    |
| `/api/users`      | POST   | Dados válidos     | 201, usuário criado    |
| `/api/users`      | POST   | Email duplicado   | 409, conflito          |
| `/api/users/{id}` | PUT    | Dados válidos     | 200, atualizado        |
| `/api/users/{id}` | DELETE | Admin             | 204, removido          |

### 2.4 Rate Limiting

| Cenário           | Resultado Esperado                       |
| ----------------- | ---------------------------------------- |
| < 100 req/min     | 200, normal                              |
| > 100 req/min     | 429, Too Many Requests                   |
| Headers presentes | X-RateLimit-Limit, X-RateLimit-Remaining |

### 2.5 CSRF Protection

| Cenário                 | Resultado Esperado |
| ----------------------- | ------------------ |
| POST com token válido   | 200                |
| POST sem token          | 403                |
| POST com token inválido | 403                |

---

## 3. Testes E2E (Frontend)

### 3.1 Navegação

| Teste         | Ação                       | Resultado Esperado      |
| ------------- | -------------------------- | ----------------------- |
| Home carrega  | Navegar para `/`           | Sidebar e main visíveis |
| Menu funciona | Clicar em itens do sidebar | Navegação correta       |
| Breadcrumbs   | Verificar breadcrumbs      | Caminho correto         |
| 404           | Acessar rota inexistente   | Página 404 exibida      |

### 3.2 Autenticação

| Teste          | Ação                  | Resultado Esperado     |
| -------------- | --------------------- | ---------------------- |
| Login válido   | Submeter credenciais  | Redireciona para home  |
| Login inválido | Credenciais erradas   | Mensagem de erro       |
| Logout         | Clicar em sair        | Redireciona para login |
| Rota protegida | Acessar sem auth      | Redireciona para login |
| Demo mode      | `VITE_DEMO_MODE=true` | Login automático       |

### 3.3 Formulários

| Teste            | Ação                    | Resultado Esperado |
| ---------------- | ----------------------- | ------------------ |
| Validação client | Campo obrigatório vazio | Erro de validação  |
| Validação email  | Email inválido          | Erro de formato    |
| Submit válido    | Dados corretos          | Sucesso, feedback  |
| Erro server      | Simular 500             | Toast de erro      |

### 3.4 Acessibilidade

| Teste         | Verificação                               |
| ------------- | ----------------------------------------- |
| Landmarks     | `<header>`, `<main>`, `<aside>` presentes |
| Headings      | Hierarquia h1 > h2 > h3                   |
| Focus         | Tab navigation funciona                   |
| Labels        | Inputs com labels associados              |
| Contraste     | WCAG AA compliance                        |
| Screen reader | aria-labels presentes                     |

### 3.5 Performance

| Teste       | Métrica            | Limite       |
| ----------- | ------------------ | ------------ |
| First load  | DOM Content Loaded | < 3s         |
| Navigation  | SPA transition     | < 500ms      |
| Bundle size | Main JS            | < 200KB gzip |
| Images      | Lazy loading       | Implementado |

---

## 4. Testes Unitários

### 4.1 packages/shared

| Módulo                  | Cobertura Mínima | Cenários                        |
| ----------------------- | ---------------- | ------------------------------- |
| `auth/AuthContext`      | 80%              | Login, logout, roles, demo mode |
| `api/client`            | 80%              | GET, POST, erros, retry         |
| `utils/formatters`      | 90%              | Datas, números, moeda           |
| `utils/helpers`         | 90%              | Strings, arrays, objetos        |
| `utils/logger`          | 70%              | Log levels, context             |
| `features/featureFlags` | 80%              | Flags, ambiente                 |

### 4.2 packages/design-system

| Componente    | Testes                               |
| ------------- | ------------------------------------ |
| `Button`      | Variants, disabled, loading, onClick |
| `Input`       | Value, onChange, error, disabled     |
| `Alert`       | Types, dismissible                   |
| `StatusBadge` | Variants, colors                     |
| `PageHeader`  | Title, breadcrumbs, actions          |

---

## 5. Matriz de Cobertura

### 5.1 Por Tipo de Teste

| Tipo               | Quantidade | Status         |
| ------------------ | ---------- | -------------- |
| E2E (Playwright)   | 96         | ✅ 95 passing  |
| Unit (Vitest)      | 75         | ✅ 75 passing  |
| API (pytest)       | -          | ⚠️ Implementar |
| Visual (Storybook) | 8          | ✅ Configurado |

### 5.2 Por Funcionalidade

| Funcionalidade | Unit | E2E | API | Status |
| -------------- | ---- | --- | --- | ------ |
| Autenticação   | ✅   | ✅  | ⚠️  | 80%    |
| Navegação      | -    | ✅  | -   | 100%   |
| Formulários    | ✅   | ✅  | -   | 90%    |
| ETL            | ⚠️   | ✅  | -   | 70%    |
| Configuração   | -    | ✅  | -   | 80%    |
| LGPD           | -    | ⚠️  | -   | 50%    |

---

## 6. Comandos de Execução

```bash
# Testes unitários
pnpm -C packages/shared test
pnpm -C packages/design-system test

# Testes E2E
pnpm -C apps/web test:e2e

# Testes E2E em modo headed
pnpm -C apps/web test:e2e:headed

# Cobertura
pnpm -C packages/shared test:coverage

# Storybook
pnpm -C packages/design-system storybook

# Validação completa
pnpm lint && pnpm typecheck && pnpm build && pnpm test
```

---

## 7. CI/CD Integration

### 7.1 GitHub Actions

```yaml
# .github/workflows/ci.yml
- Lint check
- Type check
- Unit tests
- Build
- E2E tests (demo mode)
```

### 7.2 Pre-commit Hooks

```bash
# lint-staged
- ESLint fix
- Prettier format
- Commitlint
```

---

## 8. Próximos Passos

### 8.1 Melhorias Prioritárias

1. [ ] Implementar testes de API com pytest
2. [ ] Aumentar cobertura de unit tests para 80%+
3. [ ] Adicionar testes de integração para ETL
4. [ ] Configurar visual regression tests
5. [ ] Implementar contract tests (API)

### 8.2 Métricas Alvo

| Métrica        | Atual | Alvo   |
| -------------- | ----- | ------ |
| Cobertura Unit | ~70%  | 80%    |
| E2E Passing    | 99%   | 100%   |
| Build Time     | ~3s   | < 5s   |
| Test Time      | ~2min | < 3min |

---

## 9. Referências

- [Playwright Docs](https://playwright.dev/)
- [Vitest Docs](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Storybook](https://storybook.js.org/)

---

_Última atualização: 2024-12-15_

# 🚀 Template Platform

Um template moderno e robusto para criar aplicações web corporativas com React, TypeScript, TailwindCSS e autenticação via Keycloak.

## ✨ Características

- **Monorepo** com pnpm workspaces
- **React 18** + TypeScript + Vite
- **TailwindCSS** para estilização
- **Autenticação OIDC** com Keycloak (bypass para modo demo/dev)
- **Sistema de Roles** (ADMIN, GESTOR, OPERADOR, VIEWER)
- **Design System** compartilhado
- **Docker** pronto para produção
- **Playwright** para testes E2E
- **Dark Mode** suportado

## 📁 Estrutura do Projeto

```
├── apps/
│   └── web/                    # Aplicação frontend principal
│       ├── src/
│       │   ├── components/     # Componentes React
│       │   ├── contexts/       # Contexts (Auth, etc.)
│       │   ├── pages/          # Páginas da aplicação
│       │   ├── modules/        # Módulos de funcionalidades
│       │   └── config/         # Configurações
│       └── e2e/                # Testes E2E
│
├── packages/
│   ├── design-system/          # Componentes UI compartilhados
│   ├── shared/                 # Utilitários compartilhados
│   └── types/                  # Tipos TypeScript
│
├── infra/
│   ├── docker-compose.yml      # Stack Docker
│   └── keycloak/               # Config Keycloak
│
├── api-template/               # Template de API (FastAPI)
├── docs/                       # Documentação
└── scripts/                    # Scripts de automação
```

## 🚀 Início Rápido

### Pré-requisitos

- Node.js >= 18
- pnpm >= 8
- Docker (opcional, para stack completa)

### Instalação

```bash
# Clone o template
git clone <repo-url> meu-projeto
cd meu-projeto

# Instale dependências
pnpm install

# Inicie o dev server (modo demo - sem auth)
pnpm dev
```

### Modo Demo (Desenvolvimento)

Para desenvolver sem depender do Keycloak:

```bash
# Crie um arquivo .env na pasta apps/web
echo "VITE_DEMO_MODE=true" > apps/web/.env

# Inicie o dev server
pnpm dev
```

### Stack Completa com Docker

```bash
# Suba todos os serviços
docker compose -f infra/docker-compose.yml up -d

# Acesse:
# - Frontend: http://localhost:13000
# - Keycloak: http://localhost:8080 (admin/admin)
# - API: http://localhost:8000
```

## 🔐 Autenticação e Roles

O sistema suporta 4 roles padrão:

| Role | Descrição |
|------|-----------|
| ADMIN | Acesso total ao sistema |
| GESTOR | Gestão de módulos e usuários |
| OPERADOR | Operações do dia-a-dia |
| VIEWER | Apenas visualização |

### Protegendo Rotas

```tsx
// Exige qualquer uma das roles
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']}>
  <MinhaPage />
</ProtectedRoute>

// Exige TODAS as roles
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']} requireAll>
  <MinhaPage />
</ProtectedRoute>
```

### Verificando Roles no Código

```tsx
const { hasRole, hasAnyRole } = useAuth()

if (hasRole('ADMIN')) {
  // Apenas ADMIN
}

if (hasAnyRole(['ADMIN', 'GESTOR'])) {
  // ADMIN ou GESTOR
}
```

## 📦 Criando Novos Módulos

1. Crie a pasta do módulo em `src/modules/`:

```
src/modules/meu-modulo/
├── components/
├── hooks/
├── services/
├── types.ts
└── index.ts
```

2. Adicione a rota em `App.tsx`:

```tsx
<Route path="/meu-modulo/*" element={<MeuModuloRoutes />} />
```

3. Adicione o item no menu em `AppSidebar.tsx`:

```tsx
const navItems = [
  // ...
  { label: 'Meu Módulo', path: '/meu-modulo', icon: <Icon /> },
]
```

## 🎨 Personalização

### Cores (TailwindCSS)

Edite as variáveis CSS em `src/styles/index.css`:

```css
:root {
  --brand-primary: #0087A8;
  --brand-secondary: #005F73;
  --brand-accent: #94D2BD;
}
```

### Logo e Nome

Edite `AppSidebar.tsx` e `LoginPage.tsx` para alterar logo e nome.

## 🧪 Testes

```bash
# Testes E2E
pnpm test:e2e

# Com interface visual
pnpm test:e2e:ui
```

## 📝 Scripts Disponíveis

| Comando | Descrição |
|---------|-----------|
| `pnpm dev` | Inicia dev server |
| `pnpm build` | Build de produção |
| `pnpm lint` | Executa linter |
| `pnpm typecheck` | Verifica tipos |
| `pnpm test:e2e` | Testes E2E |

## 📄 Licença

MIT

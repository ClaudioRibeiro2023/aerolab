# Sistema de Roles e Controle de Acesso

Este documento descreve o sistema de controle de acesso baseado em roles (RBAC) do template.

## Visão Geral

O sistema utiliza Keycloak como Identity Provider (IdP) e implementa OIDC/OAuth2 para autenticação. O controle de acesso é baseado em **roles** atribuídas aos usuários no Keycloak.

## Roles Disponíveis

| Role         | Descrição                                          | Nível      |
| ------------ | -------------------------------------------------- | ---------- |
| **ADMIN**    | Administrador com acesso total                     | 1 (máximo) |
| **GESTOR**   | Gerente com acesso a relatórios e configurações    | 2          |
| **OPERADOR** | Operador com acesso a funcionalidades do dia-a-dia | 3          |
| **VIEWER**   | Apenas visualização                                | 4 (mínimo) |

## Configuração no Keycloak

### 1. Criar Roles no Realm

```
Keycloak Admin → Realm → Realm Roles → Create Role
```

Criar cada role: ADMIN, GESTOR, OPERADOR, VIEWER

### 2. Atribuir Roles a Usuários

```
Users → [Selecionar Usuário] → Role Mappings → Assign Role
```

### 3. Incluir Roles no Token

O client já está configurado para incluir roles no token. Verifique:

```
Clients → template-web → Client Scopes → Dedicated Scopes → Mappers
```

## Uso no Frontend

### Verificar Roles

```tsx
import { useAuth } from '@template/shared'

function MyComponent() {
  const { hasRole, hasAnyRole } = useAuth()

  // Verificar uma role específica
  if (hasRole('ADMIN')) {
    // Apenas admin
  }

  // Verificar qualquer uma das roles
  if (hasAnyRole(['ADMIN', 'GESTOR'])) {
    // Admin OU gestor
  }
}
```

### Proteger Rotas

```tsx
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

;<Route
  path="/admin"
  element={
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <AdminPage />
    </ProtectedRoute>
  }
/>
```

### Ocultar Elementos na UI

```tsx
function Sidebar() {
  const { hasAnyRole } = useAuth()

  return (
    <nav>
      <Link to="/">Home</Link>

      {hasAnyRole(['ADMIN', 'GESTOR']) && <Link to="/reports">Relatórios</Link>}

      {hasRole('ADMIN') && <Link to="/admin">Administração</Link>}
    </nav>
  )
}
```

## Mapa de Navegação

As roles podem ser configuradas no mapa de navegação para controlar visibilidade de módulos e funções:

```ts
// navigation/map.ts
export const NAVIGATION: NavigationMap = {
  modules: [
    {
      id: 'dashboard',
      name: 'Dashboard',
      path: '/dashboard',
      icon: 'LayoutDashboard',
      // Sem roles = visível para todos
    },
    {
      id: 'admin',
      name: 'Administração',
      path: '/admin',
      icon: 'Settings',
      roles: ['ADMIN'], // Apenas ADMIN
      functions: [
        {
          id: 'users',
          name: 'Usuários',
          path: '/admin/users',
          roles: ['ADMIN'],
        },
      ],
    },
  ],
}
```

## Demo Mode

Para desenvolvimento sem Keycloak, configure:

```env
VITE_DEMO_MODE=true
```

Em demo mode:

- Usuário é automaticamente autenticado
- Todas as roles são concedidas
- Nenhuma requisição ao Keycloak

## E2E Testing

Para testes E2E com roles específicas:

```ts
// Via URL
await page.goto('/?roles=ADMIN,GESTOR')

// Via localStorage
await page.evaluate(() => {
  localStorage.setItem('e2e-roles', 'ADMIN,GESTOR')
})
```

## Troubleshooting

### Usuário não tem acesso

1. Verifique se a role está atribuída no Keycloak
2. Faça logout/login para renovar o token
3. Verifique o token no DevTools → Application → Local Storage

### Roles não aparecem no token

1. Verifique os mappers do client no Keycloak
2. Certifique-se que `realm_access` está incluído no token
3. Verifique o scope `roles` na configuração OIDC

### Debug de roles

```ts
// No console do browser
const token = localStorage.getItem('oidc.user:...')
const parsed = JSON.parse(token)
console.log(parsed.profile.realm_access?.roles)
```

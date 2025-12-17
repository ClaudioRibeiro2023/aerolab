# RBAC - Role-Based Access Control

> Sistema de controle de acesso baseado em roles do AeroLab.

**Fonte:** `packages/shared/src/auth/types.ts`, `docs/ROLES_E_ACESSO.md`

---

## Visão Geral

O AeroLab implementa RBAC (Role-Based Access Control) com integração ao Keycloak. As roles são definidas no Keycloak e propagadas via JWT.

### Roles Disponíveis

**Fonte:** `packages/shared/src/auth/types.ts:2`

```typescript
export type UserRole = 'ADMIN' | 'GESTOR' | 'OPERADOR' | 'VIEWER'
```

| Role       | Nível | Descrição      | Permissões Típicas                 |
| ---------- | ----- | -------------- | ---------------------------------- |
| `ADMIN`    | 1     | Administrador  | Tudo: config, usuários, dados      |
| `GESTOR`   | 2     | Gestor de área | CRUD em módulos, relatórios        |
| `OPERADOR` | 3     | Operador       | Operações diárias, edição limitada |
| `VIEWER`   | 4     | Visualizador   | Apenas leitura                     |

---

## Configuração no Keycloak

### 1. Criar Roles no Realm

1. Keycloak Admin → Realm Settings → Realm Roles
2. Create role para cada: `ADMIN`, `GESTOR`, `OPERADOR`, `VIEWER`

### 2. Atribuir Roles a Usuários

1. Users → Selecionar usuário → Role mapping
2. Assign role(s) do realm

### 3. Incluir Roles no Token

Por padrão, Keycloak inclui realm roles em `realm_access.roles`. Verificar em:

- Clients → template-web → Client scopes → Dedicated scope → Mappers

---

## Uso no Frontend

### AuthContext

**Fonte:** `packages/shared/src/auth/AuthContext.tsx`

```typescript
import { useAuth } from '@template/shared/auth'

function MyComponent() {
  const { user, hasRole, hasAnyRole, isAuthenticated } = useAuth()

  // Usuário atual
  console.log(user?.roles) // ['ADMIN', 'GESTOR']

  // Verificar role única
  if (hasRole('ADMIN')) {
    // Acesso admin
  }

  // Verificar múltiplas (todas necessárias)
  if (hasRole(['ADMIN', 'GESTOR'])) {
    // Precisa ADMIN E GESTOR
  }

  // Verificar qualquer uma
  if (hasAnyRole(['ADMIN', 'GESTOR'])) {
    // ADMIN OU GESTOR
  }
}
```

### Proteção de Rotas

```tsx
// Componente ProtectedRoute
<Route
  path="/admin/config"
  element={
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <ConfigPage />
    </ProtectedRoute>
  }
/>

// Múltiplas roles (qualquer uma)
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']}>
  <ManagementPage />
</ProtectedRoute>
```

### Esconder Elementos UI

```tsx
function Sidebar() {
  const { hasRole, hasAnyRole } = useAuth()

  return (
    <nav>
      <Link to="/">Home</Link>

      {hasAnyRole(['ADMIN', 'GESTOR']) && <Link to="/users">Usuários</Link>}

      {hasRole('ADMIN') && <Link to="/config">Configurações</Link>}
    </nav>
  )
}
```

---

## Uso no Backend

### Decorator para Endpoints

```python
from fastapi import Depends, HTTPException
from functools import wraps

def require_roles(*required_roles: str):
    """Decorator para exigir roles específicas."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user=Depends(get_current_user), **kwargs):
            user_roles = set(user.get("roles", []))
            required = set(required_roles)

            if not required.intersection(user_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required roles: {required_roles}"
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# Uso
@app.get("/admin/config")
@require_roles("ADMIN")
async def get_config(user: dict = Depends(get_current_user)):
    return {"config": "..."}

@app.get("/management/reports")
@require_roles("ADMIN", "GESTOR")  # Qualquer uma
async def get_reports(user: dict = Depends(get_current_user)):
    return {"reports": [...]}
```

### Extrair Roles do JWT

**Fonte:** `packages/shared/src/auth/AuthContext.tsx:34-73`

```python
def extract_roles_from_token(payload: dict) -> list[str]:
    """Extrai roles do payload JWT."""
    roles = []

    # Realm roles
    realm_access = payload.get("realm_access", {})
    roles.extend(realm_access.get("roles", []))

    # Client roles (opcional)
    resource_access = payload.get("resource_access", {})
    client_roles = resource_access.get("template-web", {}).get("roles", [])
    roles.extend(client_roles)

    # Filtrar apenas roles válidas
    valid_roles = {"ADMIN", "GESTOR", "OPERADOR", "VIEWER"}
    return [r.upper() for r in roles if r.upper() in valid_roles]
```

---

## Matriz de Permissões

### Por Módulo

| Módulo                  | ADMIN | GESTOR | OPERADOR | VIEWER |
| ----------------------- | ----- | ------ | -------- | ------ |
| Dashboard               | ✅    | ✅     | ✅       | ✅     |
| Usuários (listar)       | ✅    | ✅     | ✅       | ✅     |
| Usuários (criar/editar) | ✅    | ✅     | ❌       | ❌     |
| Usuários (deletar)      | ✅    | ❌     | ❌       | ❌     |
| Configurações           | ✅    | ❌     | ❌       | ❌     |
| Relatórios              | ✅    | ✅     | ✅       | ✅     |
| ETL (executar)          | ✅    | ✅     | ✅       | ❌     |
| ETL (configurar)        | ✅    | ✅     | ❌       | ❌     |
| Logs de Auditoria       | ✅    | ✅     | ❌       | ❌     |

### Por Ação

| Ação                  | Roles Necessárias |
| --------------------- | ----------------- |
| Visualizar dados      | VIEWER+           |
| Criar registros       | OPERADOR+         |
| Editar registros      | OPERADOR+         |
| Deletar registros     | GESTOR+           |
| Configurar sistema    | ADMIN             |
| Gerenciar usuários    | ADMIN             |
| Exportar dados        | GESTOR+           |
| Ver logs de auditoria | GESTOR+           |

---

## Hierarquia de Roles

### Modelo Atual (Flat)

No código atual, **não há hierarquia automática**. Cada role é independente.

```typescript
// hasRole(['ADMIN']) retorna true APENAS se user tem ADMIN
// Mesmo que tenha GESTOR, OPERADOR, VIEWER
```

### Implementar Hierarquia (Opcional)

Se desejar que ADMIN herde permissões de GESTOR:

```typescript
const ROLE_HIERARCHY: Record<UserRole, UserRole[]> = {
  ADMIN: ['ADMIN', 'GESTOR', 'OPERADOR', 'VIEWER'],
  GESTOR: ['GESTOR', 'OPERADOR', 'VIEWER'],
  OPERADOR: ['OPERADOR', 'VIEWER'],
  VIEWER: ['VIEWER'],
}

function hasEffectiveRole(userRoles: UserRole[], requiredRole: UserRole): boolean {
  return userRoles.some(role => ROLE_HIERARCHY[role]?.includes(requiredRole))
}
```

---

## Modo Demo / E2E

### Todas as Roles

No modo demo (`VITE_DEMO_MODE=true`), o usuário mock tem todas as roles:

```typescript
const mockUser: AuthUser = {
  id: 'demo-user-001',
  roles: ['ADMIN', 'GESTOR', 'OPERADOR', 'VIEWER'],
}
```

### Testar com Roles Específicas

```bash
# Via query params
http://localhost:13000?e2e-roles=VIEWER

# Via localStorage
localStorage.setItem('e2e-roles', '["OPERADOR"]')
```

---

## Auditoria

Todas as ações de alteração devem incluir o user ID para auditoria:

```python
# api-template/app/audit.py
async def log_action(
    user_id: str,
    action: str,
    resource: str,
    details: dict = None
):
    logger.info(
        "audit_log",
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        timestamp=datetime.utcnow().isoformat()
    )
```

---

## Troubleshooting

### Usuário não tem roles esperadas

1. Verificar roles no Keycloak Admin
2. Inspecionar JWT em jwt.io
3. Verificar se mapper está configurado no client scope

### 403 mesmo com role correta

1. Verificar case sensitivity (ADMIN vs admin)
2. Verificar se role está em `realm_access.roles`
3. Logs do backend para ver roles extraídas

### Roles não aparecem no frontend

1. Verificar `loadUserInfo: true` no oidcConfig
2. Verificar `scope: 'openid profile email roles'`
3. Console do browser: `useAuth().user?.roles`

---

**Arquivos relacionados:**

- `packages/shared/src/auth/types.ts`
- `packages/shared/src/auth/AuthContext.tsx`
- `docs/ROLES_E_ACESSO.md`

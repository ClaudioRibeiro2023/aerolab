# RBAC e Permissões

> Controle de acesso baseado em papéis na plataforma Agno.

---

## Visão Geral

O sistema implementa **RBAC (Role-Based Access Control)** com dois níveis:

1. **Papéis (Roles)** - admin, user
2. **Permissões** - Por endpoint/recurso

---

## Papéis

### admin

Acesso completo a todos os recursos.

```json
{
  "role": "admin",
  "permissions": ["*"]
}
```

### user

Acesso de leitura e execução, sem criar/deletar.

```json
{
  "role": "user",
  "permissions": ["read", "execute"]
}
```

---

## Matriz de Permissões

| Recurso | Operação | admin | user |
|---------|----------|-------|------|
| **Agents** | list | ✅ | ✅ |
| | get | ✅ | ✅ |
| | create | ✅ | ❌ |
| | update | ✅ | ❌ |
| | delete | ✅ | ❌ |
| | run | ✅ | ✅ |
| **Teams** | list | ✅ | ✅ |
| | get | ✅ | ✅ |
| | create | ✅ | ❌ |
| | delete | ✅ | ❌ |
| | run | ✅ | ✅ |
| **Workflows** | list | ✅ | ✅ |
| | get | ✅ | ✅ |
| | create | ✅ | ❌ |
| | delete | ✅ | ❌ |
| | execute | ✅ | ✅ |
| **RAG** | query | ✅ | ✅ |
| | ingest | ✅ | ❌ |
| | delete collection | ✅ | ❌ |
| **Admin** | * | ✅ | ❌ |
| **Audit** | read | ✅ | ❌ |

---

## Implementação

### Dependency Injection

```python
# src/auth/deps.py
from fastapi import Depends, HTTPException
from .jwt import decode_token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    return payload

async def require_admin(user = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin required")
    return user
```

### Uso em Endpoints

```python
# Qualquer usuário autenticado
@router.get("/agents")
async def list_agents(user = Depends(get_current_user)):
    return {"agents": [...]}

# Apenas admin
@router.post("/agents")
async def create_agent(
    data: AgentCreate,
    user = Depends(require_admin)
):
    return {"agent": {...}}
```

---

## Configuração de Admins

### Via Variável de Ambiente

```bash
# .env
ADMIN_USERS=admin@local,admin@example.com,superuser@company.com
```

### Como Funciona

Usuários na lista `ADMIN_USERS` recebem automaticamente `role: admin` no token JWT.

---

## Fluxo de Autorização

```
Request → JWT Validation → Role Check → Permission Check → Handler
            ↓                  ↓              ↓
         401 Unauthorized  403 Forbidden  200 OK
```

---

## Multi-Tenancy

### Isolamento por Tenant

```python
# src/auth/multitenancy.py
class TenantManager:
    def get_tenant(self, user_email: str) -> Tenant:
        # Retorna tenant do usuário
        ...

    def check_access(self, user: dict, resource_id: str) -> bool:
        # Verifica se recurso pertence ao tenant do usuário
        ...
```

### Uso

```python
@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    user = Depends(get_current_user),
    tenant_manager = Depends(get_tenant_manager)
):
    tenant = tenant_manager.get_tenant(user["sub"])
    if not tenant_manager.check_access(user, agent_id):
        raise HTTPException(403, "Access denied")
    ...
```

---

## Auditoria

Ações sensíveis são logadas:

```python
# src/audit/service.py
async def log_action(
    user: str,
    action: str,
    resource: str,
    details: dict
):
    await audit_repo.create({
        "user": user,
        "action": action,
        "resource": resource,
        "details": details,
        "timestamp": datetime.utcnow()
    })
```

### Eventos Auditados

- Login/logout
- Criação/deleção de agentes
- Execução de workflows
- Ingest de documentos
- Alterações de configuração

---

## Referências

- [ADR-003: Autenticação JWT + RBAC](../adr_v2/decisions/30-security/003-autenticacao-jwt-rbac.md)
- [Autenticação](../20-contratos-para-integracao/20-auth.md)
- [Código: src/auth/](../../src/auth/)

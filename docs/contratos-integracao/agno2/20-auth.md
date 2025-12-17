# Autenticação para Integração

> Como autenticar em APIs da plataforma Agno.

---

## Visão Geral

A plataforma usa **JWT (JSON Web Tokens)** para autenticação stateless.

| Aspecto | Valor |
|---------|-------|
| **Tipo** | Bearer Token |
| **Algoritmo** | HS256 |
| **Expiração** | 24 horas (configurável) |
| **Header** | `Authorization: Bearer <token>` |

---

## Obtendo um Token

### Endpoint

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

### Resposta de Sucesso

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Resposta de Erro

```json
{
  "detail": "Invalid credentials"
}
```

---

## Usando o Token

Inclua o token no header `Authorization` de todas as requisições:

```http
GET /agents
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Exemplo cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"admin"}' \
  | jq -r '.access_token')

# Request autenticado
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/agents
```

### Exemplo Python

```python
import httpx

# Login
response = httpx.post(
    "http://localhost:8000/auth/login",
    json={"email": "admin@local", "password": "admin"}
)
token = response.json()["access_token"]

# Request autenticado
client = httpx.Client(headers={"Authorization": f"Bearer {token}"})
agents = client.get("http://localhost:8000/agents").json()
```

### Exemplo JavaScript/TypeScript

```typescript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'admin@local', password: 'admin' })
});
const { access_token } = await response.json();

// Request autenticado
const agents = await fetch('http://localhost:8000/agents', {
  headers: { 'Authorization': `Bearer ${access_token}` }
}).then(r => r.json());
```

---

## Estrutura do Token

O payload do JWT contém:

```json
{
  "sub": "user@example.com",
  "role": "admin",
  "exp": 1702234567,
  "iat": 1702148167
}
```

| Campo | Descrição |
|-------|-----------|
| `sub` | Subject (email do usuário) |
| `role` | Papel do usuário (`admin` ou `user`) |
| `exp` | Timestamp de expiração |
| `iat` | Timestamp de emissão |

---

## Papéis (Roles)

| Papel | Permissões |
|-------|------------|
| `admin` | CRUD completo em todos os recursos |
| `user` | Leitura e execução, sem criar/deletar |

### Endpoints por Papel

| Endpoint | `admin` | `user` |
|----------|---------|--------|
| `GET /agents` | ✅ | ✅ |
| `POST /agents` | ✅ | ❌ |
| `DELETE /agents/{id}` | ✅ | ❌ |
| `GET /workflows` | ✅ | ✅ |
| `POST /workflows/execute` | ✅ | ✅ |
| `GET /admin/*` | ✅ | ❌ |

---

## Expiração e Renovação

### Token Expirado

Quando o token expira, a API retorna:

```json
{
  "detail": "Token has expired"
}
```

**Status:** `401 Unauthorized`

### Renovação

Atualmente não há refresh tokens. Para renovar:

1. Faça login novamente com `/auth/login`
2. Obtenha um novo `access_token`

> **[TODO: confirmar]** Refresh tokens podem ser implementados em versões futuras.

---

## Endpoints Públicos

Alguns endpoints não requerem autenticação:

| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Health check |
| `GET /health/live` | Liveness probe |
| `GET /health/ready` | Readiness probe |
| `GET /metrics` | Métricas Prometheus |
| `GET /docs` | Swagger UI |
| `GET /redoc` | ReDoc |
| `POST /auth/login` | Login |

---

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `JWT_SECRET` | Secret para assinatura (obrigatório) | - |
| `JWT_ALGORITHM` | Algoritmo de assinatura | `HS256` |
| `JWT_EXPIRATION_HOURS` | Horas até expiração | `24` |
| `ADMIN_USERS` | Emails de admins (vírgula) | `admin@localhost` |

### Exemplo .env

```bash
JWT_SECRET=sua-chave-secreta-muito-longa-e-segura
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_USERS=admin@local,admin@example.com
```

---

## Rate Limiting

Endpoints de autenticação têm rate limiting mais restritivo:

| Grupo | Limite |
|-------|--------|
| `auth` | 5 requests / 10 segundos |

Se exceder:

```json
{
  "detail": "Rate limit exceeded. Retry after 10 seconds."
}
```

**Status:** `429 Too Many Requests`

---

## Segurança

### Boas Práticas

1. **HTTPS obrigatório em produção** - Tokens podem ser interceptados em HTTP
2. **Não armazene tokens em localStorage** - Prefira cookies httpOnly
3. **Rotacione JWT_SECRET periodicamente** - Invalida todos os tokens
4. **Use expiração curta** - Reduz janela de ataque

### Headers de Segurança

A API retorna headers de segurança:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

---

## Troubleshooting

### "Invalid credentials"

- Verifique email/password
- Verifique se usuário está em `ADMIN_USERS`

### "Token has expired"

- Faça login novamente
- Aumente `JWT_EXPIRATION_HOURS` se apropriado

### "Could not validate credentials"

- Token malformado ou assinatura inválida
- Verifique se `JWT_SECRET` é o mesmo usado na criação

---

## Referências

- [ADR-003: Autenticação JWT + RBAC](../adr_v2/decisions/30-security/003-autenticacao-jwt-rbac.md)
- [Código: src/auth/](../../src/auth/)
- [JWT.io](https://jwt.io/)

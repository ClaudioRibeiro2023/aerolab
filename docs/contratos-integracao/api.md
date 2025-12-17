# Contrato de Integração: API REST

> Padrões, convenções e contratos da API REST do AeroLab.

**Fonte:** `api-template/app/main.py`

---

## Visão Geral

| Item             | Valor                               |
| ---------------- | ----------------------------------- |
| **Base URL**     | `http://localhost:8000` (dev)       |
| **Versão**       | `0.1.0`                             |
| **Formato**      | JSON                                |
| **Autenticação** | Bearer Token (JWT)                  |
| **Documentação** | `/docs` (Swagger), `/redoc` (ReDoc) |

---

## Autenticação

### Header Obrigatório

```http
Authorization: Bearer <access_token>
```

### Endpoints Públicos (sem autenticação)

| Endpoint            | Descrição           |
| ------------------- | ------------------- |
| `GET /`             | Health check básico |
| `GET /health`       | Health check        |
| `GET /health/live`  | Liveness probe      |
| `GET /health/ready` | Readiness probe     |
| `GET /docs`         | Swagger UI          |
| `GET /redoc`        | ReDoc               |

### Endpoints Protegidos

Todos os endpoints sob `/api/*` requerem autenticação JWT válido.

---

## Rate Limiting

**Fonte:** `api-template/app/rate_limit.py`

### Limites Padrão

| Categoria   | Limite     | Configuração         |
| ----------- | ---------- | -------------------- |
| **Default** | 100/minute | `RATE_LIMIT_DEFAULT` |
| **Auth**    | 10/minute  | `RATE_LIMIT_AUTH`    |
| **API**     | 60/minute  | `RATE_LIMIT_API`     |
| **Health**  | 300/minute | `RATE_LIMIT_HEALTH`  |

### Headers de Resposta

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702756800
```

### Resposta 429 (Too Many Requests)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "detail": "100 per 1 minute",
  "retry_after": 60
}
```

Headers adicionais:

```http
Retry-After: 60
```

---

## Padrão de Respostas

### Sucesso (2xx)

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-12-16T20:00:00Z",
    "request_id": "uuid-here"
  }
}
```

### Erro (4xx/5xx)

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "detail": "Technical details (optional)",
  "field_errors": {
    "email": ["Invalid email format"]
  }
}
```

### Códigos de Status

| Código | Significado           | Quando Usar                       |
| ------ | --------------------- | --------------------------------- |
| `200`  | OK                    | GET, PUT, PATCH bem-sucedidos     |
| `201`  | Created               | POST que cria recurso             |
| `204`  | No Content            | DELETE bem-sucedido               |
| `400`  | Bad Request           | Validação falhou                  |
| `401`  | Unauthorized          | Token ausente ou inválido         |
| `403`  | Forbidden             | Sem permissão (role insuficiente) |
| `404`  | Not Found             | Recurso não existe                |
| `409`  | Conflict              | Conflito (ex: duplicata)          |
| `422`  | Unprocessable Entity  | Dados inválidos (Pydantic)        |
| `429`  | Too Many Requests     | Rate limit excedido               |
| `500`  | Internal Server Error | Erro não tratado                  |
| `503`  | Service Unavailable   | Dependência indisponível          |

---

## Paginação

### Request

```http
GET /api/resources?page=1&page_size=20&sort=-created_at
```

| Parâmetro   | Tipo   | Default | Descrição                       |
| ----------- | ------ | ------- | ------------------------------- |
| `page`      | int    | 1       | Número da página (1-indexed)    |
| `page_size` | int    | 20      | Itens por página (max: 100)     |
| `sort`      | string | -       | Campo de ordenação (`-` = desc) |

### Response

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Versionamento

### Estratégia Atual

**Sem versionamento explícito na URL.** A API é considerada v1 implicitamente.

### Versionamento Futuro (Planejado)

```http
GET /api/v2/resources
Accept: application/vnd.template.v2+json
```

---

## CORS

**Fonte:** `api-template/app/main.py:43-55`

### Origens Permitidas

```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:13000",
    os.getenv("FRONTEND_URL", "http://localhost:13000"),
]
```

### Headers Expostos

```python
expose_headers=[
    "X-Request-ID",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset"
]
```

---

## Endpoints Disponíveis

### Health Checks

#### GET /

```http
GET / HTTP/1.1
Host: localhost:8000
```

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

#### GET /health

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

#### GET /health/live

Kubernetes liveness probe.

```json
{
  "status": "alive",
  "timestamp": "2024-12-16T20:00:00.000000"
}
```

#### GET /health/ready

Kubernetes readiness probe. Verifica dependências.

```json
{
  "status": "ready",
  "version": "0.1.0",
  "timestamp": "2024-12-16T20:00:00.000000",
  "checks": {
    "database": { "status": "ok", "latency_ms": 1 },
    "redis": { "status": "ok", "latency_ms": 1 },
    "keycloak": { "status": "ok" }
  }
}
```

Se algum check falhar:

```http
HTTP/1.1 503 Service Unavailable
```

```json
{
  "status": "not_ready",
  "checks": {
    "database": { "status": "error", "message": "Connection refused" }
  }
}
```

### User Info

#### GET /api/me

Retorna informações do usuário autenticado.

```http
GET /api/me HTTP/1.1
Authorization: Bearer <token>
```

```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "User Name",
  "roles": ["ADMIN", "GESTOR"]
}
```

### Configuration

#### GET /api/config

Retorna configurações do frontend.

```json
{
  "appName": "Template Platform",
  "version": "0.1.0",
  "features": {
    "darkMode": true,
    "notifications": true
  }
}
```

---

## Headers de Request

### Obrigatórios

| Header          | Valor              | Quando               |
| --------------- | ------------------ | -------------------- |
| `Authorization` | `Bearer <token>`   | Endpoints protegidos |
| `Content-Type`  | `application/json` | POST, PUT, PATCH     |

### Recomendados

| Header            | Valor   | Propósito             |
| ----------------- | ------- | --------------------- |
| `X-Request-ID`    | UUID    | Correlação de logs    |
| `Accept-Language` | `pt-BR` | Mensagens localizadas |

---

## Headers de Response

### Sempre Presentes

| Header                      | Descrição                           |
| --------------------------- | ----------------------------------- |
| `X-Request-ID`              | ID único da requisição (para debug) |
| `X-Content-Type-Options`    | `nosniff`                           |
| `X-Frame-Options`           | `DENY`                              |
| `Strict-Transport-Security` | HSTS em produção                    |

### Rate Limiting

| Header                  | Descrição             |
| ----------------------- | --------------------- |
| `X-RateLimit-Limit`     | Limite total          |
| `X-RateLimit-Remaining` | Requisições restantes |
| `X-RateLimit-Reset`     | Timestamp de reset    |

---

## Exemplos de Integração

### cURL

```bash
# Health check
curl -X GET http://localhost:8000/health

# Endpoint protegido
curl -X GET http://localhost:8000/api/me \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# POST com dados
curl -X POST http://localhost:8000/api/resources \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "value": 123}'
```

### JavaScript/TypeScript

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar token
api.interceptors.request.use(config => {
  const token = getAccessToken() // Sua função
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Uso
const response = await api.get('/api/me')
console.log(response.data)
```

### Python

```python
import httpx

async def get_user_info(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
```

---

## Tratamento de Erros

### Erros de Validação (422)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {}
    },
    {
      "type": "string_type",
      "loc": ["body", "name"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

### Retry Strategy

| Código         | Retry? | Delay                        |
| -------------- | ------ | ---------------------------- |
| `429`          | Sim    | Usar `Retry-After` header    |
| `500`          | Sim    | Exponential backoff (max 3x) |
| `502`, `503`   | Sim    | Exponential backoff          |
| `4xx` (outros) | Não    | Erro do cliente              |

---

## OpenAPI/Swagger

### URLs

| Ferramenta   | URL                                  |
| ------------ | ------------------------------------ |
| Swagger UI   | `http://localhost:8000/docs`         |
| ReDoc        | `http://localhost:8000/redoc`        |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

### Gerar Schema

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

---

**Arquivos relacionados:**

- `api-template/app/main.py` - Entry point
- `api-template/app/rate_limit.py` - Rate limiting
- `api-template/app/middleware.py` - Request logging

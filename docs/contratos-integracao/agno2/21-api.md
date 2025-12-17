# Contratos de API

> Padrões REST, versionamento, erros e paginação da API Agno.

---

## Base URL

| Ambiente | URL |
|----------|-----|
| **Local** | `http://localhost:8000` |
| **Staging** | `https://agno-staging.railway.app` |
| **Production** | `https://agno.railway.app` |

> **[TODO: confirmar]** URLs de staging/production podem variar.

---

## Padrões REST

### Métodos HTTP

| Método | Uso |
|--------|-----|
| `GET` | Ler recursos |
| `POST` | Criar recursos ou executar ações |
| `PUT` | Atualizar recurso completo |
| `PATCH` | Atualizar parcialmente |
| `DELETE` | Remover recursos |

### Status Codes

| Código | Significado |
|--------|-------------|
| `200` | OK - Sucesso |
| `201` | Created - Recurso criado |
| `204` | No Content - Sucesso sem body |
| `400` | Bad Request - Input inválido |
| `401` | Unauthorized - Token ausente/inválido |
| `403` | Forbidden - Sem permissão |
| `404` | Not Found - Recurso não existe |
| `422` | Unprocessable Entity - Validação falhou |
| `429` | Too Many Requests - Rate limit |
| `500` | Internal Server Error - Erro do servidor |

---

## Endpoints Principais

### Health & Monitoring

```http
GET /health              # Status geral
GET /health/live         # Liveness probe (Kubernetes)
GET /health/ready        # Readiness probe (Kubernetes)
GET /metrics             # Métricas Prometheus
GET /api/status          # Status detalhado da API
```

### Agents

```http
GET    /agents           # Listar agentes
POST   /agents           # Criar agente
GET    /agents/{id}      # Obter agente
PUT    /agents/{id}      # Atualizar agente
DELETE /agents/{id}      # Remover agente
POST   /agents/{id}/run  # Executar agente
```

### Teams

```http
GET    /teams                    # Listar times
POST   /teams                    # Criar time
GET    /teams/{id}               # Obter time
DELETE /teams/{id}               # Remover time
POST   /teams/{id}/run           # Executar time
POST   /teams/content/run        # Pipeline de conteúdo
POST   /teams/research/run       # Pipeline de pesquisa
```

### Workflows

```http
GET    /workflows/registry       # Listar workflows
POST   /workflows/registry       # Criar workflow
GET    /workflows/registry/{id}  # Obter workflow
DELETE /workflows/registry/{id}  # Remover workflow
POST   /workflows/research-write # Workflow pesquisa+escrita
```

### RAG

```http
POST   /rag/ingest      # Indexar documentos
POST   /rag/query       # Buscar e responder
GET    /rag/collections # Listar collections
DELETE /rag/collections/{name}  # Remover collection
```

### Flow Studio

```http
GET    /api/flow-studio/health   # Health check
GET    /api/flow-studio/stats    # Estatísticas
POST   /api/flow-studio/execute  # Executar workflow
```

### Dashboard

```http
GET    /api/dashboard/health     # Health check
GET    /api/dashboard/stats      # Estatísticas
GET    /api/dashboard/insights   # Insights e recomendações
```

---

## Formato de Request

### Headers Obrigatórios

```http
Content-Type: application/json
Authorization: Bearer <token>
```

### Headers Opcionais

```http
X-Request-ID: uuid       # ID para tracing
Accept-Language: pt-BR   # Idioma de resposta
```

### Body (JSON)

```json
{
  "field": "value",
  "nested": {
    "key": "value"
  }
}
```

---

## Formato de Response

### Sucesso (Objeto)

```json
{
  "id": "uuid",
  "name": "Agent Name",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

### Sucesso (Lista)

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Erro

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

---

## Paginação

### Query Parameters

| Param | Descrição | Default |
|-------|-----------|---------|
| `page` | Número da página (1-based) | `1` |
| `page_size` | Itens por página | `20` |
| `sort` | Campo para ordenar | - |
| `order` | `asc` ou `desc` | `asc` |

### Exemplo

```http
GET /agents?page=2&page_size=10&sort=name&order=desc
```

### Response

```json
{
  "items": [...],
  "total": 45,
  "page": 2,
  "page_size": 10,
  "pages": 5
}
```

---

## Filtros

### Query Parameters Comuns

| Param | Descrição |
|-------|-----------|
| `q` | Busca textual |
| `status` | Filtro por status |
| `created_after` | Data mínima de criação |
| `created_before` | Data máxima de criação |

### Exemplo

```http
GET /agents?q=researcher&status=active&created_after=2024-01-01
```

---

## Rate Limiting

### Limites por Grupo

| Grupo | Limite |
|-------|--------|
| `default` | 10 requests / 10s |
| `auth` | 5 requests / 10s |
| `rag_query` | 3 requests / 10s |
| `rag_ingest` | 2 requests / 10s |

### Headers de Rate Limit

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1702234567
```

### Resposta de Rate Limit

```json
{
  "detail": "Rate limit exceeded. Retry after 10 seconds."
}
```

**Status:** `429 Too Many Requests`

---

## Versionamento

Atualmente a API **não tem versionamento explícito**.

Todas as rotas estão na versão implícita v1.

> **[TODO: confirmar]** Versionamento via header ou path (`/v1/`, `/v2/`) pode ser implementado.

---

## Exemplos Completos

### Criar e Executar Agente

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"admin"}' \
  | jq -r '.access_token')

# 2. Criar agente
curl -X POST http://localhost:8000/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "researcher",
    "model": "groq:llama-3.3-70b-versatile",
    "instructions": "You are a research assistant"
  }'

# 3. Executar agente
curl -X POST http://localhost:8000/agents/researcher/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the latest AI trends?"}'
```

### Query RAG

```bash
# Indexar documentos
curl -X POST http://localhost:8000/rag/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "docs",
    "texts": ["Text 1...", "Text 2..."],
    "metadatas": [{"source": "doc1"}, {"source": "doc2"}]
  }'

# Buscar
curl -X POST http://localhost:8000/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "docs",
    "query": "What is X?",
    "top_k": 5
  }'
```

---

## Referências

- [OpenAPI Spec](22-openapi.md)
- [Schemas](24-schemas/)
- [Autenticação](20-auth.md)

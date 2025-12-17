# OpenAPI / Swagger

> Como acessar e usar a documentação OpenAPI da API Agno.

---

## Endpoints de Documentação

| Endpoint | Descrição |
|----------|-----------|
| `/docs` | Swagger UI (interativo) |
| `/redoc` | ReDoc (leitura) |
| `/openapi.json` | Spec OpenAPI em JSON |

---

## Swagger UI

Acesse `http://localhost:8000/docs` para interface interativa:

- Visualizar todos os endpoints
- Testar requests diretamente
- Ver schemas de request/response
- Autenticar com token JWT

### Autenticação no Swagger

1. Clique em "Authorize" (cadeado)
2. Cole seu token JWT
3. Clique em "Authorize"
4. Todos os requests incluirão o token

---

## ReDoc

Acesse `http://localhost:8000/redoc` para documentação em formato de leitura:

- Navegação por seções
- Schemas expandíveis
- Melhor para documentação

---

## OpenAPI Spec

### Download da Spec

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

### Estrutura da Spec

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Agno Multi-Agent Platform API",
    "version": "2.2.0"
  },
  "paths": {
    "/health": {...},
    "/agents": {...},
    ...
  },
  "components": {
    "schemas": {...},
    "securitySchemes": {...}
  }
}
```

---

## Gerando Clientes

### TypeScript (openapi-typescript)

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o api-types.ts
```

### Python (openapi-python-client)

```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json
```

### Outros Geradores

- [OpenAPI Generator](https://openapi-generator.tech/)
- [Swagger Codegen](https://swagger.io/tools/swagger-codegen/)

---

## Customização

### Metadados da API

Configurados em `server.py`:

```python
app = FastAPI(
    title="Agno Multi-Agent Platform API",
    description="API for multi-agent AI systems",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

### Tags

Endpoints são organizados por tags:

| Tag | Descrição |
|-----|-----------|
| `Health` | Health checks |
| `Auth` | Autenticação |
| `Agents` | Gerenciamento de agentes |
| `Teams` | Times multi-agente |
| `Workflows` | Pipelines e workflows |
| `RAG` | Retrieval-Augmented Generation |
| `HITL` | Human-in-the-Loop |
| `Storage` | File storage |
| `Memory` | Memory management |
| `Admin` | Administração |
| `Audit` | Audit logs |

---

## Validação

### Validar Spec

```bash
# Usando swagger-cli
npx swagger-cli validate openapi.json

# Usando openapi-spec-validator
pip install openapi-spec-validator
openapi-spec-validator openapi.json
```

---

## Referências

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/redoc/)

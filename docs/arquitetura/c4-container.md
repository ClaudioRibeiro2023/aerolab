# C4 Model - Nível 2: Container Diagram

> Visão dos containers (unidades deployáveis) do AeroLab.

## Diagrama de Containers

```mermaid
C4Container
    title Container Diagram - AeroLab

    Person(user, "Usuário", "Acessa via browser")

    System_Boundary(platform, "AeroLab") {
        Container(spa, "Frontend SPA", "React 18, TypeScript, Vite", "Interface web responsiva com Design System")
        Container(api, "API Backend", "FastAPI, Python 3.11+", "API REST com autenticação e RBAC")
        ContainerDb(db, "Database", "PostgreSQL 15", "Dados da aplicação")
        ContainerDb(cache, "Cache/Sessions", "Redis 7", "Cache, sessões, rate limiting")
    }

    System_Ext(keycloak, "Keycloak", "Identity Provider OIDC")
    System_Ext(cdn, "CDN", "Assets estáticos (opcional)")

    Rel(user, spa, "Acessa", "HTTPS/443")
    Rel(user, cdn, "Assets", "HTTPS")
    Rel(spa, api, "Consome", "REST/JSON")
    Rel(spa, keycloak, "Autentica", "OIDC/PKCE")
    Rel(api, db, "Lê/Escreve", "asyncpg")
    Rel(api, cache, "Cache/Sessões", "redis-py")
    Rel(api, keycloak, "Valida JWT", "JWKS")
```

## Containers

### Frontend SPA

| Atributo         | Valor                              |
| ---------------- | ---------------------------------- |
| **Tecnologia**   | React 18.2, TypeScript 5.3, Vite 5 |
| **Localização**  | `apps/web/`                        |
| **Build output** | `apps/web/dist/`                   |
| **Porta (dev)**  | 13000                              |
| **Porta (prod)** | 80 (nginx)                         |

**Responsabilidades:**

- Interface de usuário responsiva
- Roteamento SPA (React Router)
- Autenticação OIDC (oidc-client-ts)
- Gerenciamento de estado (TanStack Query)
- Design System compartilhado

**Dependências de runtime:**

```
@tanstack/react-query ^5.12.2
oidc-client-ts ^2.4.0
react-router-dom ^6.20.0
axios ^1.6.2
```

### API Backend

| Atributo        | Valor                                       |
| --------------- | ------------------------------------------- |
| **Tecnologia**  | FastAPI 0.104+, Python 3.11+, Pydantic 2.5+ |
| **Localização** | `api-template/`                             |
| **Entry point** | `api-template/app/main.py`                  |
| **Porta**       | 8000                                        |
| **Docs**        | `/docs` (Swagger), `/redoc` (ReDoc)         |

**Responsabilidades:**

- API REST com validação de schema (Pydantic)
- Autenticação JWT (python-jose)
- Rate limiting (slowapi)
- CSRF protection
- Audit logging (structlog)
- Database migrations (Alembic)

**Dependências de runtime:**

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-jose[cryptography]>=3.3.0
sqlalchemy>=2.0.0
redis>=5.0.0
slowapi>=0.1.9
structlog>=24.1.0
```

### Database (PostgreSQL)

| Atributo       | Valor                |
| -------------- | -------------------- |
| **Tecnologia** | PostgreSQL 15 Alpine |
| **Porta**      | 5432                 |
| **Database**   | `template`           |
| **Driver**     | asyncpg (async)      |

**Schema gerenciado por:**

- Alembic migrations (`api-template/alembic/`)
- SQLAlchemy 2.0 models

### Cache/Sessions (Redis)

| Atributo         | Valor            |
| ---------------- | ---------------- |
| **Tecnologia**   | Redis 7 Alpine   |
| **Porta**        | 6379             |
| **Persistência** | AOF (appendonly) |

**Usos:**

- Cache de queries
- Sessões distribuídas
- Rate limiting storage
- Pub/Sub para WebSockets

## Comunicação entre Containers

### Frontend → API

```
Protocolo: HTTPS (REST/JSON)
Autenticação: Bearer token (JWT)
Headers:
  - Authorization: Bearer <access_token>
  - Content-Type: application/json
  - X-Request-ID: <uuid> (correlação)
```

### Frontend → Keycloak

```
Protocolo: HTTPS (OIDC)
Fluxo: Authorization Code + PKCE
Endpoints usados:
  - /protocol/openid-connect/auth
  - /protocol/openid-connect/token
  - /protocol/openid-connect/userinfo
  - /protocol/openid-connect/logout
```

### API → PostgreSQL

```
Protocolo: TCP (asyncpg)
Connection string: postgresql://user:pass@host:5432/db
Pool: min=5, max=20 (configurável)
SSL: obrigatório em produção
```

### API → Redis

```
Protocolo: TCP (redis-py async)
Connection string: redis://host:6379
SSL: opcional
```

## Deploy Configurations

### Desenvolvimento Local

```yaml
# infra/docker-compose.yml
services:
  frontend: localhost:13000
  api: localhost:8000
  keycloak: localhost:8080
  db: localhost:5432
  redis: localhost:6379
```

### Produção (Kubernetes)

```yaml
# infra/k8s/deployment.yaml
Deployments:
  - api (replicas: 2-10, HPA)
  - web (replicas: 2-5)
Services:
  - api-service (ClusterIP)
  - web-service (ClusterIP)
Ingress:
  - api.domain.com → api-service
  - app.domain.com → web-service
```

---

**Próximo nível:** [C4 Component Diagram](./c4-component.md)

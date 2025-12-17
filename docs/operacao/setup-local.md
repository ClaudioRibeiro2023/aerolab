# Setup Local

> Guia completo para configurar o ambiente de desenvolvimento local.

---

## Pré-requisitos

| Ferramenta         | Versão Mínima           | Verificar                |
| ------------------ | ----------------------- | ------------------------ |
| **Node.js**        | 18.0.0                  | `node --version`         |
| **pnpm**           | 8.0.0 (recomendado 9.x) | `pnpm --version`         |
| **Python**         | 3.11+                   | `python --version`       |
| **Docker**         | 20.10+                  | `docker --version`       |
| **Docker Compose** | 2.0+                    | `docker compose version` |
| **Git**            | 2.30+                   | `git --version`          |

### Instalar pnpm

```bash
# Via npm
npm install -g pnpm@9

# Via corepack (Node.js 16.13+)
corepack enable
corepack prepare pnpm@9.15.9 --activate
```

---

## Setup Rápido

### 1. Clonar o Repositório

```bash
git clone https://github.com/ClaudioRibeiro2023/aerolab.git aerolab
cd aerolab
```

### 2. Instalar Dependências (Frontend)

```bash
pnpm install
```

### 3. Subir Infraestrutura (Docker)

```bash
cd infra
docker compose up -d
```

Serviços iniciados:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Keycloak: `localhost:8080`

### 4. Iniciar API (Backend)

```bash
cd api-template
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 5. Iniciar Frontend

```bash
# Na raiz do projeto
pnpm dev
```

Acesse: **http://localhost:13000**

---

## Configuração por Ambiente

### Variáveis de Ambiente (Frontend)

Criar arquivo `apps/web/.env.local`:

```bash
# API
VITE_API_URL=http://localhost:8000/api

# Keycloak
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=template
VITE_KEYCLOAK_CLIENT_ID=template-web

# Desenvolvimento
VITE_DEMO_MODE=true  # Bypass auth para dev rápido
```

### Variáveis de Ambiente (Backend)

Criar arquivo `api-template/.env`:

```bash
# Database
DATABASE_URL=postgresql://template:template@localhost:5432/template

# Redis
REDIS_URL=redis://localhost:6379

# Security
API_SECRET_KEY=dev-secret-key-change-in-production

# Environment
ENVIRONMENT=development

# Rate Limiting
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=10/minute
RATE_LIMIT_API=60/minute
```

### Variáveis Docker Compose

Copiar template:

```bash
cd infra
cp .env.example .env
```

Editar conforme necessário.

---

## Portas Utilizadas

| Serviço    | Porta | URL                    |
| ---------- | ----- | ---------------------- |
| Frontend   | 13000 | http://localhost:13000 |
| API        | 8000  | http://localhost:8000  |
| Keycloak   | 8080  | http://localhost:8080  |
| PostgreSQL | 5432  | -                      |
| Redis      | 6379  | -                      |
| Storybook  | 6006  | http://localhost:6006  |

---

## Modo Demo (Sem Keycloak)

Para desenvolver sem configurar Keycloak:

```bash
# Terminal 1: API
cd api-template
uvicorn app.main:app --reload

# Terminal 2: Frontend em modo demo
cd apps/web
VITE_DEMO_MODE=true pnpm dev
```

Usuário mock:

- **Email:** demo@template.com
- **Roles:** ADMIN, GESTOR, OPERADOR, VIEWER

---

## Configurar Keycloak

### Credenciais Admin

- **URL:** http://localhost:8080
- **Username:** admin
- **Password:** admin

### Criar Realm (se necessário)

1. Admin Console → Create Realm
2. Name: `template`
3. Enabled: ON

### Criar Client

1. Clients → Create client
2. **Client ID:** `template-web`
3. **Client Protocol:** openid-connect
4. **Root URL:** http://localhost:13000
5. **Valid redirect URIs:**
   - http://localhost:13000/\*
   - http://localhost:13000/auth/callback
6. **Web origins:** http://localhost:13000
7. **Access Type:** public (para PKCE)

### Criar Roles

1. Realm roles → Create role
2. Criar: `ADMIN`, `GESTOR`, `OPERADOR`, `VIEWER`

### Criar Usuário de Teste

1. Users → Add user
2. **Username:** test@example.com
3. **Email:** test@example.com
4. **Email Verified:** ON
5. Credentials → Set password
6. Role mapping → Assign roles

---

## Scripts Disponíveis

### Root (pnpm)

```bash
pnpm dev          # Frontend em localhost:13000
pnpm build        # Build de produção
pnpm lint         # Lint (ESLint)
pnpm lint:fix     # Lint + fix
pnpm typecheck    # TypeScript check
pnpm test         # Testes unitários
pnpm test:e2e     # Testes E2E
pnpm format       # Prettier
pnpm clean        # Remove node_modules e dist
```

### API (Python)

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Migrations
alembic upgrade head              # Aplicar migrations
alembic revision --autogenerate -m "desc"  # Criar migration
alembic downgrade -1              # Reverter última

# Testes
pytest                            # Rodar testes
pytest --cov=app                  # Com cobertura
```

### Docker

```bash
cd infra

# Subir todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f [service]

# Parar tudo
docker compose down

# Limpar volumes
docker compose down -v
```

---

## Verificação do Setup

### 1. Frontend

```bash
curl http://localhost:13000
# Deve retornar HTML
```

### 2. API

```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"0.1.0"}
```

### 3. Keycloak

```bash
curl http://localhost:8080/realms/template/.well-known/openid-configuration
# Deve retornar JSON com endpoints OIDC
```

### 4. PostgreSQL

```bash
docker exec -it infra-db-1 psql -U template -d template -c "SELECT 1"
```

### 5. Redis

```bash
docker exec -it infra-redis-1 redis-cli ping
# PONG
```

---

## Troubleshooting

### pnpm install falha

```bash
# Limpar cache
pnpm store prune
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Porta em uso

```bash
# Windows
netstat -ano | findstr :13000
taskkill /PID <pid> /F

# Linux/Mac
lsof -i :13000
kill -9 <pid>
```

### Docker não sobe

```bash
# Verificar logs
docker compose logs

# Resetar containers
docker compose down -v
docker compose up -d
```

### Keycloak não conecta

1. Verificar se container está rodando: `docker ps`
2. Verificar logs: `docker compose logs keycloak`
3. Aguardar inicialização completa (~30s)

---

**Próximos passos:**

- [Deploy](./deploy.md)
- [Variáveis de Ambiente](./variaveis-ambiente.md)

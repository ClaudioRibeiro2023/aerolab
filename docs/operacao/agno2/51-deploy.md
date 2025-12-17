# Deploy

> Como deployar a plataforma Agno em produção.

---

## Arquitetura de Deploy

```
┌─────────────────┐    ┌─────────────────┐
│    Netlify      │    │    Railway      │
│   (Frontend)    │    │   (Backend)     │
│                 │    │                 │
│  Next.js SSR    │───►│  FastAPI + DB   │
│  CDN Global     │    │  ChromaDB       │
└─────────────────┘    └─────────────────┘
```

---

## Deploy Backend (Railway)

### 1. Configuração

O arquivo `railway.json` já está configurado:

```json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

### 2. Variáveis de Ambiente

Configure no Railway Dashboard:

| Variável | Obrigatória |
|----------|-------------|
| `JWT_SECRET` | Sim |
| `GROQ_API_KEY` | Sim* |
| `OPENAI_API_KEY` | Sim* |
| `ADMIN_USERS` | Sim |
| `DATABASE_URL` | Não (usa SQLite) |

*Pelo menos uma API key de LLM.

### 3. Deploy via GitHub

1. Conecte repositório no Railway
2. Configure variáveis de ambiente
3. Deploy automático em cada push para `main`

### 4. Deploy Manual

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

---

## Deploy Frontend (Netlify)

### 1. Configuração

O arquivo `netlify.toml` já está configurado:

```toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

### 2. Variáveis de Ambiente

Configure no Netlify Dashboard:

| Variável | Valor |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | URL do backend Railway |

### 3. Deploy via GitHub

1. Conecte repositório no Netlify
2. Configure build settings (base: `frontend`)
3. Adicione variáveis de ambiente
4. Deploy automático em cada push

### 4. Deploy Manual

```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy preview
netlify deploy

# Deploy production
netlify deploy --prod
```

---

## CI/CD (GitHub Actions)

### Workflow de Staging

`.github/workflows/deploy-staging.yml`:

```yaml
on:
  push:
    branches: [staging]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @railway/cli
      - run: railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Workflow de Production

`.github/workflows/deploy-production.yml`:

```yaml
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # ... testes e deploy
```

---

## Checklist de Deploy

### Antes do Deploy

- [ ] Testes passando (`pytest tests/`)
- [ ] Lint passando (`ruff check .`)
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets não expostos

### Após Deploy

- [ ] Health check OK (`/health`)
- [ ] Swagger acessível (`/docs`)
- [ ] Login funcionando
- [ ] Frontend conectando ao backend

---

## Rollback

### Railway

```bash
# Listar deployments
railway deployments

# Rollback para versão anterior
railway rollback
```

### Netlify

1. Acesse Netlify Dashboard → Deploys
2. Clique no deploy anterior
3. "Publish deploy"

---

## Monitoramento

### Logs

```bash
# Railway
railway logs

# Netlify
netlify functions:log
```

### Métricas

Acesse `/metrics` para métricas Prometheus.

---

## Referências

- [Railway Docs](https://docs.railway.app/)
- [Netlify Docs](https://docs.netlify.com/)
- [Observabilidade](52-observabilidade.md)

# Setup Local

> Como rodar a plataforma Agno do zero ao "funcionando".

---

## Pré-requisitos

| Requisito | Versão | Verificar |
|-----------|--------|-----------|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Git | 2.x | `git --version` |

---

## 1. Clone o Repositório

```bash
git clone https://github.com/ClaudioRibeiro2023/agno-multi-agent-platform.git
cd agno-multi-agent-platform
```

---

## 2. Configure o Backend

### Criar ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Instalar dependências

```bash
pip install -e ".[dev,rag]"
```

### Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas configurações mínimas:

```bash
# OBRIGATÓRIO: Pelo menos uma API key de LLM
GROQ_API_KEY=gsk_your_key_here

# OBRIGATÓRIO: Secret para JWT (gere com: openssl rand -hex 32)
JWT_SECRET=your-secret-key-here

# OBRIGATÓRIO: Admin users
ADMIN_USERS=admin@local
```

### Iniciar o servidor

```bash
python server.py
```

Ou com hot reload:

```bash
uvicorn server:app --reload --port 8000
```

### Verificar

```bash
curl http://localhost:8000/health
# {"status": "healthy", ...}
```

---

## 3. Configure o Frontend

### Instalar dependências

```bash
cd frontend
npm install
```

### Configurar ambiente

```bash
cp .env.example .env.development.local
```

Edite com:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Iniciar o frontend

```bash
npm run dev
```

### Verificar

Acesse http://localhost:3000

---

## 4. Verificação Completa

### Health checks

```bash
# Backend
curl http://localhost:8000/health
curl http://localhost:8000/api/status

# Docs
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

### Teste de integração

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"admin"}' \
  | jq -r '.access_token')

# Listar agentes
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/agents
```

---

## 5. Rodar Testes

```bash
# Testes unitários
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html
```

---

## Docker (Alternativa)

### Backend + ChromaDB

```bash
docker-compose up -d
```

### Apenas Backend

```bash
docker build -t agno-backend .
docker run -p 8000:8000 --env-file .env agno-backend
```

---

## Troubleshooting

### "No module named 'agno'"

```bash
pip install agno
```

### "JWT_SECRET not set"

Adicione ao `.env`:
```bash
JWT_SECRET=qualquer-string-secreta
```

### "Connection refused" no frontend

Verifique se o backend está rodando na porta 8000.

### ChromaDB erro

```bash
pip install chromadb
```

---

## Estrutura de Diretórios Gerada

Após setup, você terá:

```
agno-multi-agent-platform/
├── .venv/              # Ambiente virtual Python
├── data/               # Dados persistentes (SQLite, ChromaDB)
├── frontend/
│   └── node_modules/   # Dependências Node
└── ...
```

---

## Próximos Passos

1. [Explorar a API](http://localhost:8000/docs)
2. [Criar primeiro agente](../20-contratos-para-integracao/21-api.md)
3. [Configurar deploy](51-deploy.md)

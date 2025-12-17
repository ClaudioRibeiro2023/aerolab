# Stack Tecnológica e Racional

> Decisões de stack e suas implicações para a plataforma.

---

## Resumo da Stack

| Camada | Tecnologia | Versão | Justificativa |
|--------|------------|--------|---------------|
| **Backend Runtime** | Python | 3.12+ | Tipagem avançada, async nativo, ecossistema AI |
| **Backend Framework** | FastAPI | 0.115+ | Performance, async, OpenAPI automático |
| **AI Framework** | Agno | 2.0+ | Multi-agent nativo, ferramentas built-in |
| **Frontend Framework** | Next.js | 15.x | App Router, SSR, performance |
| **Frontend UI** | React | 18.x | Concurrent features, ecosystem |
| **Styling** | TailwindCSS | 3.4+ | Utility-first, bundle otimizado |
| **Components** | shadcn/ui | - | Acessível, customizável |
| **State (Client)** | Zustand | 4.5+ | Simples, sem boilerplate |
| **Data Fetching** | TanStack Query | 5.x | Cache, sync, devtools |
| **Database** | SQLite/PostgreSQL | - | Dev simples, prod robusto |
| **Vector Store** | ChromaDB | 1.0+ | RAG, embeddings |
| **Deploy Backend** | Railway | - | Python/Docker simplificado |
| **Deploy Frontend** | Netlify | - | CDN global, CI/CD |

---

## Backend: Python + FastAPI

### Por que Python?

```
✅ Ecossistema dominante em AI/ML
✅ Tipagem forte com type hints (3.12+)
✅ Async/await nativo
✅ Bibliotecas maduras (numpy, pandas, etc.)
✅ Comunidade ativa
```

### Por que FastAPI?

```
✅ Performance comparável a Node.js/Go
✅ Documentação automática (OpenAPI/Swagger)
✅ Validação com Pydantic
✅ Dependency injection nativo
✅ WebSockets suportado
```

**Alternativas descartadas:**
- **Django:** Mais pesado, menos async-native
- **Flask:** Menos features built-in
- **Node.js:** Ecossistema AI menos maduro

### Configuração

```python
# pyproject.toml
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.13",
    "uvicorn[standard]>=0.34.3",
    "pydantic>=2.0.0",
    ...
]
```

---

## AI: Agno Framework

### Por que Agno?

```
✅ Multi-agent nativo (teams, workflows)
✅ Suporte a múltiplos LLM providers
✅ Ferramentas built-in (RAG, memory, tools)
✅ AgentOS para deployment
✅ Open source
```

### Funcionalidades Usadas

| Feature | Uso |
|---------|-----|
| `Agent` | Base para todos os agentes |
| `Team` | Orquestração multi-agente |
| `Tool` | 30+ ferramentas integradas |
| `Memory` | Short/long-term memory |
| `Storage` | Persistência de sessões |

**Alternativas descartadas:**
- **LangChain:** Mais verbose, abstração excessiva
- **AutoGen:** Menos flexível para customização
- **CrewAI:** Menos maduro

---

## Frontend: Next.js + React

### Por que Next.js 15?

```
✅ App Router para melhor performance
✅ Server Components para SSR
✅ Streaming e Suspense
✅ API Routes para BFF
✅ Otimização automática de imagens
```

### Por que React 18?

```
✅ Concurrent Features
✅ Suspense para data fetching
✅ Ecosystem massivo
✅ Devtools excelentes
```

**Alternativas descartadas:**
- **Vue.js:** Ecosystem menor
- **Svelte:** Menos bibliotecas enterprise
- **Angular:** Mais pesado, curva maior

### Configuração

```json
// package.json
{
  "dependencies": {
    "next": "^15.0.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }
}
```

---

## Styling: TailwindCSS + shadcn/ui

### Por que TailwindCSS?

```
✅ Utility-first = produtividade
✅ Bundle size otimizado (purge)
✅ Design system consistente
✅ Responsivo built-in
```

### Por que shadcn/ui?

```
✅ Componentes acessíveis (Radix)
✅ Customizável (não é biblioteca, é copy-paste)
✅ TypeScript nativo
✅ Não adiciona dependência
```

**Alternativas descartadas:**
- **Material UI:** Bundle grande, estilo opinionated
- **Chakra UI:** Menos customizável
- **Styled Components:** Runtime overhead

---

## State Management

### Zustand (Client State)

```typescript
// store/app-store.ts
import { create } from 'zustand'

interface AppState {
  user: User | null
  setUser: (user: User) => void
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}))
```

**Por que Zustand?**
```
✅ API minimalista
✅ Sem boilerplate
✅ Middleware (persist, devtools)
✅ TypeScript nativo
```

### TanStack Query (Server State)

```typescript
// hooks/use-agents.ts
import { useQuery } from '@tanstack/react-query'

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents'),
  })
}
```

**Por que TanStack Query?**
```
✅ Cache inteligente
✅ Background refetch
✅ Optimistic updates
✅ Devtools
```

---

## Database

### SQLite (Desenvolvimento)

```
✅ Zero configuração
✅ Arquivo único
✅ Perfeito para dev/teste
```

### PostgreSQL (Produção)

```
✅ ACID compliant
✅ Escalável
✅ JSON support
✅ Full-text search
```

### Migração

```python
# Configurado via DATABASE_URL
# Dev: sqlite:///./data/agents.db
# Prod: postgresql://user:pass@host/db
```

---

## Vector Store: ChromaDB

### Por que ChromaDB?

```
✅ Open source
✅ Embeddings nativos
✅ Persistência local ou servidor
✅ API simples
```

### Configuração

```python
# src/rag/service.py
import chromadb

# Local (dev)
client = chromadb.PersistentClient(path="./data/chroma")

# Server (prod)
client = chromadb.HttpClient(host="chroma-host", port=8000)
```

**Alternativas:**
- **Pinecone:** Managed, mas vendor lock-in
- **Weaviate:** Mais complexo
- **Milvus:** Overhead para uso atual

---

## Deploy

### Railway (Backend)

```json
// railway.json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

**Por que Railway?**
```
✅ Deploy de Python simplificado
✅ Nixpacks auto-detecta stack
✅ CI/CD integrado ao GitHub
✅ Scaling automático
```

### Netlify (Frontend)

```toml
# netlify.toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

**Por que Netlify?**
```
✅ CDN global
✅ Next.js otimizado
✅ Preview deploys
✅ CI/CD integrado
```

---

## Implicações da Stack

### Vantagens

1. **Tipagem end-to-end:** Python type hints + TypeScript
2. **Performance:** FastAPI async + Next.js SSR
3. **Developer Experience:** Hot reload, devtools, documentação
4. **Ecosystem:** Bibliotecas maduras em ambas as pontas

### Desvantagens

1. **Duas linguagens:** Python + TypeScript (requer conhecimento de ambas)
2. **Complexidade de deploy:** Backend e frontend separados
3. **Dependência do Agno:** Core depende do framework

### Mitigações

- Documentação clara de ambas as partes
- Docker Compose para dev local unificado
- Abstração do Agno em camada de serviço

---

## Referências

- [ADR-001: Stack Tecnológica](../adr_v2/decisions/10-architecture/001-stack-tecnologica.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Agno Framework](https://docs.agno.com/)

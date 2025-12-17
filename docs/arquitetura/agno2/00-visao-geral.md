# Visão Geral

> **Agno Multi-Agent Platform** é uma plataforma completa para construção, orquestração e deploy de sistemas multi-agente de IA.

---

## O que é

Uma plataforma **full-stack** que permite:

1. **Criar agentes de IA** com acesso a 30+ ferramentas (web search, code execution, APIs, etc.)
2. **Orquestrar times** de múltiplos agentes trabalhando em conjunto
3. **Construir workflows visuais** com o Flow Studio (drag & drop)
4. **Integrar RAG** (Retrieval-Augmented Generation) com ChromaDB
5. **Monitorar e observar** via dashboards em tempo real
6. **Deployar** com um clique para Railway/Netlify

---

## Para quem

| Persona | Caso de uso |
|---------|-------------|
| **Desenvolvedores** | Integrar agentes de IA em aplicações existentes via API REST |
| **Data Scientists** | Criar pipelines de processamento com RAG e multi-agents |
| **Product Managers** | Prototipar assistentes e automações sem código (Flow Studio) |
| **Enterprises** | Deploy on-premise com SSO, RBAC, compliance (LGPD/GDPR) |

---

## Casos de Uso Principais

### 1. Assistente de Pesquisa
```
Usuário → Agente Pesquisador → Web Search → Agente Escritor → Relatório
```

### 2. Análise de Documentos (RAG)
```
Upload PDF → Chunking → Embeddings → ChromaDB → Query com contexto → Resposta
```

### 3. Automação de Tarefas
```
Trigger (webhook/cron) → Workflow → Múltiplos agentes → Notificação
```

### 4. Atendimento ao Cliente
```
Chat → Roteamento inteligente → Agente especializado → Escalação HITL se necessário
```

---

## Conceitos Fundamentais

### Agente
Entidade autônoma com:
- **Modelo LLM** (Groq, OpenAI, Anthropic)
- **Ferramentas** (web search, code execution, APIs)
- **Memória** (short-term, long-term, episódica)
- **Instruções** (system prompt, role)

### Time (Team)
Conjunto de agentes que colaboram:
- **Coordinator** - Agente que delega tarefas
- **Workers** - Agentes que executam tarefas
- **Modes** - Sequential, parallel, hierarchical, swarm

### Workflow
Pipeline visual de execução:
- **Nós** - Agentes, condicionais, loops, transformadores
- **Conexões** - Fluxo de dados entre nós
- **Triggers** - Manual, webhook, cron

### RAG (Retrieval-Augmented Generation)
Técnica que combina:
- **Indexação** - Documentos → chunks → embeddings → vector store
- **Retrieval** - Query → busca semântica → contexto relevante
- **Generation** - Contexto + query → LLM → resposta fundamentada

### HITL (Human-in-the-Loop)
Intervenção humana em pontos críticos:
- **Aprovação** - Humano aprova antes de continuar
- **Correção** - Humano corrige output do agente
- **Escalação** - Agente não consegue resolver, escala para humano

---

## Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  Next.js 15 + React 18 + TailwindCSS + shadcn/ui            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Chat   │ │Dashboard│ │  Flow   │ │  Team   │           │
│  │   UI    │ │   UI    │ │ Studio  │ │ Orch.   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                        BACKEND                               │
│  FastAPI + Python 3.12+ + Agno Framework                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Agents  │ │  Teams  │ │Workflows│ │   RAG   │           │
│  │  API    │ │   API   │ │   API   │ │   API   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Auth   │ │  HITL   │ │ Storage │ │ Metrics │           │
│  │  JWT    │ │  Repo   │ │  S3/FS  │ │ Prom.   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ SQLite/ │ │ChromaDB │ │  Redis  │ │   S3    │           │
│  │Postgres │ │ Vectors │ │ (opt.)  │ │ (opt.)  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    LLM PROVIDERS                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Groq   │ │ OpenAI  │ │Anthropic│ │ Ollama  │           │
│  │(llama3) │ │(gpt-4o) │ │(claude) │ │ (local) │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| **Backend** | Python + FastAPI | 3.12+ / 0.115+ |
| **Framework AI** | Agno | 2.0+ |
| **Frontend** | Next.js + React | 15.x / 18.x |
| **Styling** | TailwindCSS + shadcn/ui | 3.4+ |
| **State** | Zustand + TanStack Query | 4.5+ / 5.x |
| **Vector DB** | ChromaDB | 1.0+ |
| **Database** | SQLite / PostgreSQL | 3.x / 15+ |
| **Deploy** | Railway + Netlify | - |

---

## Próximos Passos

1. **[Setup Local](../50-operacao/50-setup-local.md)** - Rodar a plataforma localmente
2. **[Arquitetura](../10-arquitetura/10-contexto-e-objetivos.md)** - Entender a arquitetura em detalhes
3. **[API](../20-contratos-para-integracao/21-api.md)** - Integrar via API REST
4. **[Glossário](01-glossario.md)** - Termos e definições

---

## Links Úteis

- **Repositório:** `https://github.com/ClaudioRibeiro2023/agno-multi-agent-platform`
- **API Docs:** `/docs` (Swagger) ou `/redoc` (ReDoc)
- **Changelog:** `CHANGELOG.md`

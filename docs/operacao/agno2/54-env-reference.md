# Referência de Variáveis de Ambiente

> **Fonte autoritativa:** `.env.example`
> **Última atualização:** 2025-12-09

Este documento descreve todas as variáveis de ambiente utilizadas pela Agno Multi-Agent Platform.

---

## Índice

- [Variáveis Obrigatórias](#variáveis-obrigatórias)
- [Configuração do Servidor](#configuração-do-servidor)
- [LLM Providers](#llm-providers)
- [Segurança & Autenticação](#segurança--autenticação)
- [Serviços de Busca](#serviços-de-busca)
- [Vector Store & RAG](#vector-store--rag)
- [Observabilidade](#observabilidade)
- [Docker](#docker)
- [APIs Externas](#apis-externas)

---

## Variáveis Obrigatórias

Estas variáveis **devem** estar configuradas para a aplicação funcionar:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `JWT_SECRET` | Secret para assinatura de tokens JWT | `openssl rand -hex 32` |
| `GROQ_API_KEY` **ou** `OPENAI_API_KEY` **ou** `ANTHROPIC_API_KEY` | Pelo menos uma API key de LLM | `gsk_...` |

---

## Configuração do Servidor

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `AGENTOS_HOST` | Host do servidor | `0.0.0.0` | Não |
| `AGENTOS_PORT` | Porta do servidor | `8000` | Não |
| `DEBUG` | Modo debug | `false` | Não |
| `LOG_LEVEL` | Nível de log | `INFO` | Não |
| `CORS_ALLOW_ORIGINS` | Origens permitidas (vírgula) | `http://localhost:3000` | Não |

---

## LLM Providers

### Groq (Recomendado - Gratuito)

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `GROQ_API_KEY` | API Key do Groq | [console.groq.com/keys](https://console.groq.com/keys) |

**Modelos disponíveis:**
- `llama-3.3-70b-versatile` (recomendado)
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

### OpenAI

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `OPENAI_API_KEY` | API Key da OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) |
| `OPENAI_ORG_ID` | Organization ID (opcional) | Dashboard OpenAI |

**Modelos disponíveis:**
- `gpt-4o` (recomendado)
- `gpt-4o-mini`
- `gpt-3.5-turbo`

### Anthropic

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `ANTHROPIC_API_KEY` | API Key da Anthropic | [console.anthropic.com](https://console.anthropic.com/) |

**Modelos disponíveis:**
- `claude-3-5-sonnet-20241022` (recomendado)
- `claude-3-haiku-20240307`
- `claude-3-opus-20240229`

### Google AI

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `GOOGLE_API_KEY` | API Key do Google AI | [aistudio.google.com](https://aistudio.google.com/app/apikey) |

### Ollama (Local)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OLLAMA_BASE_URL` | URL do Ollama | `http://localhost:11434` |

### Modelo Padrão

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DEFAULT_MODEL_PROVIDER` | Provider padrão | `groq` |
| `DEFAULT_MODEL_ID` | Modelo padrão | `llama-3.3-70b-versatile` |

---

## Segurança & Autenticação

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `JWT_SECRET` | Secret para JWT | - | **Sim** |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` | Não |
| `JWT_EXPIRATION_HOURS` | Expiração do token | `24` | Não |
| `ADMIN_USERS` | Emails de admins (vírgula) | - | Não |
| `RATE_LIMIT_REQUESTS` | Limite de requisições | `100` | Não |
| `RATE_LIMIT_WINDOW` | Janela em segundos | `60` | Não |

---

## Serviços de Busca

### Tavily (Recomendado)

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `TAVILY_API_KEY` | API Key do Tavily | [tavily.com](https://tavily.com/) |

### SerpAPI

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `SERP_API_KEY` | API Key do SerpAPI | [serpapi.com](https://serpapi.com/) |

### Exa

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `EXA_API_KEY` | API Key do Exa | [exa.ai](https://exa.ai/) |

---

## Vector Store & RAG

### ChromaDB

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `CHROMA_HOST` | Host do ChromaDB | - (usa local) |
| `CHROMA_DB_PATH` | Caminho do banco local | `data/vectorstore` |

### Embeddings

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `EMBEDDING_PROVIDER` | Provider de embeddings | `openai` |
| `OPENAI_EMBED_MODEL` | Modelo de embedding | `text-embedding-3-large` |

---

## Observabilidade

### Sentry (Error Tracking)

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `NEXT_PUBLIC_SENTRY_DSN` | DSN do Sentry | [sentry.io](https://sentry.io/) |
| `SENTRY_AUTH_TOKEN` | Token de autenticação | Dashboard Sentry |
| `SENTRY_ORG` | Nome da organização | Dashboard Sentry |
| `SENTRY_PROJECT` | Nome do projeto | Dashboard Sentry |

### PostHog (Analytics)

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `NEXT_PUBLIC_POSTHOG_KEY` | API Key do PostHog | [posthog.com](https://posthog.com/) |
| `NEXT_PUBLIC_POSTHOG_HOST` | Host do PostHog | `https://us.i.posthog.com` |

### LangSmith (LLM Tracing)

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `LANGSMITH_API_KEY` | API Key | [smith.langchain.com](https://smith.langchain.com/) |
| `LANGSMITH_PROJECT` | Nome do projeto | Dashboard LangSmith |

---

## Docker

Ao usar `docker-compose`, ajuste as seguintes variáveis:

| Variável | Valor para Docker | Descrição |
|----------|-------------------|-----------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:4000` | URL do backend |
| `CORS_ALLOW_ORIGINS` | `http://localhost:4001,...` | Incluir frontend |
| `CHROMA_HOST` | `http://chromadb:8000` | ChromaDB no Docker |
| `REDIS_URL` | `redis://redis:6379` | Redis no Docker |

### Portas Docker (série 4xxx)

| Serviço | Porta |
|---------|-------|
| Backend | `4000` |
| Frontend | `4001` |
| ChromaDB | `4002` |
| Ollama | `4003` |
| Redis | `4004` |

---

## APIs Externas

### Geolocalização

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `MAPBOX_ACCESS_TOKEN` | Token do Mapbox | [mapbox.com](https://mapbox.com/) |
| `GOOGLE_MAPS_API_KEY` | API Key Google Maps | [console.cloud.google.com](https://console.cloud.google.com/) |

### Clima

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `OPENWEATHER_API_KEY` | API Key OpenWeather | [openweathermap.org](https://openweathermap.org/) |

### Comunicação

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `SLACK_BOT_TOKEN` | Token do bot Slack | [api.slack.com](https://api.slack.com/) |
| `DISCORD_BOT_TOKEN` | Token do bot Discord | [discord.com/developers](https://discord.com/developers) |
| `TWILIO_ACCOUNT_SID` | SID da conta Twilio | [twilio.com](https://twilio.com/) |
| `TWILIO_AUTH_TOKEN` | Token Twilio | Dashboard Twilio |

### Produtividade

| Variável | Descrição | Obter em |
|----------|-----------|----------|
| `NOTION_API_KEY` | API Key do Notion | [developers.notion.com](https://developers.notion.com/) |
| `GITHUB_TOKEN` | Personal Access Token | [github.com/settings/tokens](https://github.com/settings/tokens) |

---

## Validação

A aplicação valida variáveis críticas na inicialização. Para testar:

```bash
# Ver resumo de configuração
python -c "from src.config import print_environment_summary; print_environment_summary()"

# Validar (falha se críticas ausentes)
python -c "from src.config import validate_environment; validate_environment()"
```

---

## Arquivos Relacionados

| Arquivo | Propósito |
|---------|-----------|
| `.env.example` | Template para novos ambientes |
| `.env` | Variáveis de runtime (não commitar) |
| `src/config/env_validator.py` | Lógica de validação |
| `src/config/settings.py` | Carregamento de settings |

---

*Para referência histórica de integrações, consulte `docs/archive/env-reference.md`*

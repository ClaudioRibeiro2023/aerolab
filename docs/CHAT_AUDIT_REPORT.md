# 🔍 Auditoria do Módulo de Chat - AeroLab Platform

**Data:** 2025-01-17  
**Versão:** 1.0  
**Autor:** Arquiteto de Software Sênior

---

## 1) Mapa do Módulo de Chat (Inventário)

### 📁 Frontend (Next.js/React)

| Arquivo | Descrição | Linhas |
|---------|-----------|--------|
| `apps/studio/app/chat/page.tsx` | Página principal do chat | 928 |
| `apps/studio/components/EnhancedChat.tsx` | Componente de chat com progress | 348 |
| `apps/studio/lib/chatTypes.ts` | Tipos TypeScript para Chat v2 | 387 |
| `apps/studio/lib/api.ts` | Cliente Axios para API | 134 |
| `apps/studio/store/auth.ts` | Store Zustand (apenas auth) | 53 |

### 📁 Backend (FastAPI/Python)

| Arquivo | Descrição | Linhas |
|---------|-----------|--------|
| `apps/api/server.py` | Servidor principal com endpoints `/chat`, `/agents/{name}/run` | 1050 |
| `apps/api/src/chat/service.py` | ChatService - orquestração | 586 |
| `apps/api/src/chat/core/conversation.py` | Modelo Conversation | 340 |
| `apps/api/src/chat/core/message.py` | Modelo Message | 378 |
| `apps/api/src/config/llm_models.py` | Configuração dinâmica de modelos | 493 |

### 📁 Estrutura Backend Chat

```
apps/api/src/chat/
├── __init__.py
├── service.py          # ChatService principal
├── analytics/          # (vazio)
├── core/
│   ├── conversation.py # Conversation, Branch, Collaborator
│   ├── message.py      # Message, Attachment, Citation, ToolCall
│   ├── session.py      # SessionManager
│   └── context.py      # ContextBuilder
├── multiagent/         # (vazio)
├── multimodal/         # (vazio)
├── personalization/    # (vazio)
├── search/             # (vazio)
├── streaming/
│   ├── streamer.py     # ChatStreamer
│   └── events.py       # StreamEvent
└── workbench/          # (vazio)
```

### 🔌 Endpoints Atuais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/chat` | Chat simples (sem persistência) |
| POST | `/agents/{name}/run` | Executa agente com prompt |
| GET | `/agents` | Lista agentes |
| GET | `/models` | Lista modelos LLM |

### ⚙️ Fluxo de Dados Atual

```
[Frontend]                    [Backend]
    │                             │
    ├─ useState(messages)         │
    │  (local, não persistido)    │
    │                             │
    ├─────POST /agents/{name}/run──►
    │                             │
    │                        call_llm()
    │                        (Groq/OpenAI/Anthropic/Mistral)
    │                             │
    ◄────────JSON response────────┤
    │                             │
    ├─ setMessages([...])         │
    │  (adiciona ao state local)  │
```

---

## 2) Diagnóstico do Problema "Chat Zera ao Trocar de Tela"

### 🔴 Causa Raiz

**Evidência no código** (`apps/studio/app/chat/page.tsx:286`):

```typescript
const [messages, setMessages] = useState<Message[]>([]);
```

O estado das mensagens é mantido **apenas em `useState` local** dentro do componente `ChatContent`. Quando o usuário navega para outra página:

1. O componente é **desmontado** (unmount)
2. Todo o state local é **destruído**
3. Ao voltar, o componente é **remontado** com state vazio

### ❌ Problemas Identificados

| Problema | Localização | Impacto |
|----------|-------------|---------|
| State local não persistido | `chat/page.tsx:286` | Chat zera ao navegar |
| Sem store global para chat | `store/` (só tem `auth.ts`) | Não há compartilhamento de estado |
| Backend não persiste conversas | `server.py` (endpoint `/chat`) | Histórico perdido ao reiniciar |
| Sem identificador de conversa | API retorna apenas resposta | Impossível recuperar histórico |
| `ChatService` não é usado | `src/chat/service.py` | Código morto |

### ✅ Correção Mínima (Quick Fix)

Criar store Zustand para persistir mensagens:

```typescript
// apps/studio/store/chat.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ChatState {
  conversations: Record<string, Message[]>;
  activeConversationId: string | null;
  addMessage: (convId: string, msg: Message) => void;
  getMessages: (convId: string) => Message[];
  setActiveConversation: (id: string) => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: {},
      activeConversationId: null,
      addMessage: (convId, msg) => set(state => ({
        conversations: {
          ...state.conversations,
          [convId]: [...(state.conversations[convId] || []), msg]
        }
      })),
      getMessages: (convId) => get().conversations[convId] || [],
      setActiveConversation: (id) => set({ activeConversationId: id }),
    }),
    { name: 'aerolab-chat' }
  )
);
```

**Impacto:** Médio  
**Complexidade:** Baixa (2-4h)  
**Risco:** Baixo

### ✅ Correção Ideal (Arquitetural)

1. Persistir conversas no backend (PostgreSQL/Supabase)
2. Usar o `ChatService` já implementado
3. Criar endpoints REST para CRUD de conversas
4. Implementar streaming via SSE
5. Sincronizar frontend com backend

---

## 3) Arquitetura Proposta (Visão Macro)

### 🏗️ Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  ChatStore   │  │  React Query │  │  SSE Client  │              │
│  │  (Zustand)   │  │  (cache)     │  │  (streaming) │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────────────┼─────────────────┘                       │
│                          │                                          │
│                    ┌─────▼─────┐                                    │
│                    │  api.ts   │                                    │
│                    │  (Axios)  │                                    │
│                    └─────┬─────┘                                    │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   HTTPS     │
                    └──────┬──────┘
                           │
┌──────────────────────────┼──────────────────────────────────────────┐
│                         BACKEND (FastAPI)                           │
├──────────────────────────┼──────────────────────────────────────────┤
│                    ┌─────▼─────┐                                    │
│                    │  Router   │                                    │
│                    │  /chat/*  │                                    │
│                    └─────┬─────┘                                    │
│         ┌────────────────┼────────────────┐                        │
│         │                │                │                        │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐                │
│  │ ChatService │  │ LLMRouter   │  │ StreamMgr   │                │
│  │             │  │             │  │ (SSE)       │                │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘                │
│         │                │                                          │
│  ┌──────▼──────┐  ┌──────▼──────┐                                  │
│  │ Repository  │  │ Providers   │                                  │
│  │ (CRUD)      │  │ Groq/OpenAI │                                  │
│  └──────┬──────┘  │ Anthropic   │                                  │
│         │         │ Mistral     │                                  │
│         │         └─────────────┘                                  │
└─────────┼───────────────────────────────────────────────────────────┘
          │
   ┌──────▼──────┐
   │  PostgreSQL │
   │  (Supabase) │
   └─────────────┘
```

### 🔧 Componentes

#### Frontend

| Componente | Responsabilidade |
|------------|------------------|
| **ChatStore** | Estado global (Zustand + persist) |
| **React Query** | Cache de conversas, invalidação |
| **SSE Client** | Receber streaming de tokens |
| **ChatPage** | UI principal |
| **ConversationSidebar** | Lista de conversas/projetos |

#### Backend

| Componente | Responsabilidade |
|------------|------------------|
| **ChatRouter** | Endpoints REST + SSE |
| **ChatService** | Orquestração (já existe) |
| **LLMRouter** | Seleção de provider/modelo |
| **StreamManager** | Gerenciar conexões SSE |
| **Repository** | CRUD PostgreSQL |

### 🔌 Endpoints Propostos

```
# Conversas
GET    /api/v2/conversations                    # Listar conversas do usuário
POST   /api/v2/conversations                    # Criar conversa
GET    /api/v2/conversations/{id}               # Obter conversa
PATCH  /api/v2/conversations/{id}               # Atualizar (título, pin, archive)
DELETE /api/v2/conversations/{id}               # Soft delete

# Mensagens
GET    /api/v2/conversations/{id}/messages      # Listar mensagens
POST   /api/v2/conversations/{id}/messages      # Enviar mensagem (retorna SSE)
DELETE /api/v2/conversations/{id}/messages/{mid}# Deletar mensagem

# Streaming
GET    /api/v2/conversations/{id}/stream        # SSE endpoint

# Projetos
GET    /api/v2/projects                         # Listar projetos
POST   /api/v2/projects                         # Criar projeto
PATCH  /api/v2/projects/{id}                    # Atualizar projeto

# Personas
GET    /api/v2/personas                         # Listar personas
POST   /api/v2/personas                         # Criar persona
```

---

## 4) Modelagem de Dados (Schema SQL)

```sql
-- ============================================
-- AEROLAB CHAT - DATABASE SCHEMA
-- PostgreSQL / Supabase
-- ============================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- USERS (já deve existir no sistema)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PERSONAS
-- ============================================
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    avatar_emoji VARCHAR(10) DEFAULT '🤖',
    is_public BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Configurações
    default_model VARCHAR(100),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_personas_user ON personas(user_id);
CREATE INDEX idx_personas_public ON personas(is_public) WHERE is_public = TRUE;

-- ============================================
-- PROJECTS (Agrupamento de conversas)
-- ============================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_emoji VARCHAR(10) DEFAULT '📁',
    color VARCHAR(7) DEFAULT '#3B82F6',
    
    -- Configurações padrão para conversas do projeto
    default_persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    default_model VARCHAR(100),
    custom_instructions TEXT,
    
    -- Arquivos/contexto do projeto
    context_files JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, archived, deleted
    pinned BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);

-- ============================================
-- CONVERSATIONS
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    
    -- Info
    title VARCHAR(500) DEFAULT 'Nova Conversa',
    auto_title BOOLEAN DEFAULT TRUE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, archived, deleted
    pinned BOOLEAN DEFAULT FALSE,
    
    -- Configurações
    model VARCHAR(100) NOT NULL DEFAULT 'llama-3.1-8b-instant',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    system_prompt TEXT,
    
    -- Features
    web_search_enabled BOOLEAN DEFAULT FALSE,
    code_execution_enabled BOOLEAN DEFAULT FALSE,
    
    -- Branches (para edit/regenerate)
    active_branch_id UUID,
    
    -- Métricas
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10,6) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_project ON conversations(project_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
CREATE INDEX idx_conversations_last_msg ON conversations(last_message_at DESC NULLS LAST);

-- ============================================
-- BRANCHES (Para edit/regenerate)
-- ============================================
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    name VARCHAR(100) DEFAULT 'main',
    parent_branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    parent_message_id UUID, -- Ponto de bifurcação
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_branches_conversation ON branches(conversation_id);

-- ============================================
-- MESSAGES
-- ============================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Autor
    role VARCHAR(20) NOT NULL, -- user, assistant, system, tool
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_id VARCHAR(100),
    
    -- Conteúdo
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, markdown, code, image, etc
    
    -- Rich content (JSONB)
    attachments JSONB DEFAULT '[]',
    citations JSONB DEFAULT '[]',
    tool_calls JSONB DEFAULT '[]',
    reasoning_steps JSONB DEFAULT '[]',
    
    -- Modelo usado
    model VARCHAR(100),
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'done', -- pending, streaming, done, error
    error_message TEXT,
    
    -- Interações
    feedback VARCHAR(10), -- good, bad
    regenerated_from UUID REFERENCES messages(id),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    edited_at TIMESTAMPTZ
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_branch ON messages(branch_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- ============================================
-- CONVERSATION SUMMARIES (Para contexto longo)
-- ============================================
CREATE TABLE conversation_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Range de mensagens sumarizadas
    start_message_id UUID REFERENCES messages(id),
    end_message_id UUID REFERENCES messages(id),
    message_count INTEGER,
    
    -- Sumário
    summary TEXT NOT NULL,
    key_points JSONB DEFAULT '[]',
    
    -- Tokens
    original_tokens INTEGER,
    summary_tokens INTEGER,
    compression_ratio DECIMAL(5,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_summaries_conversation ON conversation_summaries(conversation_id);

-- ============================================
-- ATTACHMENTS (Arquivos enviados)
-- ============================================
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    
    -- Storage
    storage_path TEXT,
    url TEXT,
    thumbnail_url TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attachments_message ON attachments(message_id);

-- ============================================
-- LLM USAGE (Custos e métricas)
-- ============================================
CREATE TABLE llm_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Provider/Model
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    
    -- Tokens
    tokens_prompt INTEGER NOT NULL,
    tokens_completion INTEGER NOT NULL,
    
    -- Custos (USD)
    cost_input DECIMAL(10,6),
    cost_output DECIMAL(10,6),
    cost_total DECIMAL(10,6),
    
    -- Performance
    latency_ms INTEGER,
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_user ON llm_usage(user_id);
CREATE INDEX idx_llm_usage_date ON llm_usage(created_at);
CREATE INDEX idx_llm_usage_model ON llm_usage(provider, model);

-- ============================================
-- VIEWS ÚTEIS
-- ============================================

-- Lista de conversas com última mensagem
CREATE OR REPLACE VIEW v_conversations_list AS
SELECT 
    c.id,
    c.user_id,
    c.project_id,
    c.title,
    c.status,
    c.pinned,
    c.model,
    c.message_count,
    c.total_tokens,
    c.estimated_cost_usd,
    c.created_at,
    c.updated_at,
    c.last_message_at,
    p.name as project_name,
    per.name as persona_name,
    per.avatar_emoji as persona_emoji
FROM conversations c
LEFT JOIN projects p ON c.project_id = p.id
LEFT JOIN personas per ON c.persona_id = per.id
WHERE c.status != 'deleted';

-- Uso mensal por usuário
CREATE OR REPLACE VIEW v_monthly_usage AS
SELECT 
    user_id,
    DATE_TRUNC('month', created_at) as month,
    provider,
    model,
    SUM(tokens_prompt) as total_prompt_tokens,
    SUM(tokens_completion) as total_completion_tokens,
    SUM(cost_total) as total_cost,
    COUNT(*) as request_count
FROM llm_usage
GROUP BY user_id, DATE_TRUNC('month', created_at), provider, model;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER tr_users_updated BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_personas_updated BEFORE UPDATE ON personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_projects_updated BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_conversations_updated BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_messages_updated BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Atualizar métricas da conversa ao inserir mensagem
CREATE OR REPLACE FUNCTION update_conversation_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations SET
        message_count = message_count + 1,
        total_tokens = total_tokens + NEW.tokens_prompt + NEW.tokens_completion,
        last_message_at = NEW.created_at,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_messages_metrics AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_metrics();
```

---

## 5) Estratégia de Contexto e Tokens (Token Budgeting)

### 📊 Limites por Modelo

| Modelo | Context Window | Recomendado Output |
|--------|---------------|-------------------|
| llama-3.1-8b-instant | 128k | 4k |
| gpt-5-mini | 128k | 8k |
| claude-haiku-4-5 | 200k | 8k |
| gemini-2.5-flash-lite | 1M | 8k |

### 🧮 Fórmula de Token Budget

```
TOTAL_BUDGET = context_window - reserved_output
AVAILABLE = TOTAL_BUDGET - system_prompt - persona_instructions - project_context

Distribuição:
├── System Prompt:        ~500 tokens (fixo)
├── Persona Instructions: ~1000 tokens (fixo)
├── Project Context:      ~2000 tokens (variável)
├── Conversation Summary: ~1000 tokens (se necessário)
├── Recent Messages:      (AVAILABLE - acima)
└── Reserved Output:      4096-8192 tokens
```

### 📋 Regras de Seleção de Mensagens

```python
def select_context_messages(
    conversation: Conversation,
    model: str,
    persona: Persona = None,
    project: Project = None
) -> List[Message]:
    """
    Seleciona mensagens para contexto respeitando token budget.
    """
    budget = get_model_context_window(model)
    reserved_output = 4096
    available = budget - reserved_output
    
    # 1. System prompt (obrigatório)
    system_tokens = count_tokens(get_system_prompt())
    available -= system_tokens
    
    # 2. Persona instructions
    if persona:
        persona_tokens = count_tokens(persona.system_prompt)
        available -= persona_tokens
    
    # 3. Project context
    if project and project.custom_instructions:
        project_tokens = count_tokens(project.custom_instructions)
        available -= min(project_tokens, 2000)  # Cap em 2k
    
    # 4. Últimas N mensagens (prioridade)
    messages = conversation.messages[-50:]  # Últimas 50
    selected = []
    tokens_used = 0
    
    for msg in reversed(messages):
        msg_tokens = count_tokens(msg.content)
        if tokens_used + msg_tokens > available * 0.7:
            break
        selected.insert(0, msg)
        tokens_used += msg_tokens
    
    # 5. Se sobraram muitas mensagens antigas, usar summary
    remaining = available - tokens_used
    if len(conversation.messages) > len(selected) + 10 and remaining > 500:
        summary = get_or_create_summary(
            conversation, 
            end_before=selected[0].id
        )
        if summary:
            selected.insert(0, Message.system(f"[Resumo anterior]: {summary}"))
    
    return selected
```

### 🔄 Política de Sumarização Incremental

```python
SUMMARIZATION_CONFIG = {
    "trigger_threshold": 30,      # Sumarizar a cada 30 mensagens
    "min_messages_to_keep": 10,   # Sempre manter últimas 10
    "summary_model": "gpt-4o-mini",  # Modelo para sumarização
    "max_summary_tokens": 1000,
    "compression_target": 0.2,    # 20% do tamanho original
}

async def maybe_summarize(conversation: Conversation):
    """Verifica e executa sumarização se necessário."""
    unsummarized = get_unsummarized_messages(conversation)
    
    if len(unsummarized) >= SUMMARIZATION_CONFIG["trigger_threshold"]:
        # Manter últimas N mensagens sem sumarizar
        to_summarize = unsummarized[:-SUMMARIZATION_CONFIG["min_messages_to_keep"]]
        
        summary = await generate_summary(
            messages=to_summarize,
            model=SUMMARIZATION_CONFIG["summary_model"],
            max_tokens=SUMMARIZATION_CONFIG["max_summary_tokens"]
        )
        
        await save_summary(
            conversation_id=conversation.id,
            start_message_id=to_summarize[0].id,
            end_message_id=to_summarize[-1].id,
            summary=summary
        )
```

### 🎯 Roteamento de Modelos por Tarefa

| Tarefa | Modelo Recomendado | Justificativa |
|--------|-------------------|---------------|
| Chat geral | llama-3.1-8b-instant | Grátis, rápido |
| Código | claude-haiku-4-5 | Melhor para code |
| Análise longa | gemini-1.5-pro | 2M context |
| Sumarização | gpt-4o-mini | Bom custo-benefício |
| Raciocínio complexo | o1-mini | Chain-of-thought |

---

## 6) Melhorias UX (Estilo ChatGPT)

### 🎨 Layout Proposto

```
┌────────────────────────────────────────────────────────────────────┐
│  🚀 AeroLab                                    [👤 User] [⚙️]      │
├──────────────┬─────────────────────────────────────────────────────┤
│              │                                                     │
│  PROJETOS    │  💬 Conversa: Análise de Dados                     │
│  ───────────│  ─────────────────────────────────────────────────  │
│              │                                                     │
│  📁 Marketing│  [👤] Analise os dados do Q4                       │
│    └ Conv 1  │  ─────────────────────────────────────────────────  │
│    └ Conv 2  │                                                     │
│              │  [🤖] Baseado nos dados fornecidos, identifiquei    │
│  📁 DevOps   │  3 tendências principais:                          │
│    └ Conv 3  │                                                     │
│              │  1. **Crescimento de 23%** em conversões...         │
│  ───────────│  2. **Redução de 15%** em CAC...                    │
│              │  3. **Aumento de 45%** em retenção...               │
│  CONVERSAS   │                                                     │
│  ───────────│  ─────────────────────────────────────────────────  │
│              │                                                     │
│  📌 Pinned   │  [🔄 Regenerar] [👍] [👎] [📋 Copiar]              │
│  🕐 Hoje     │                                                     │
│  🕐 Ontem    │                                                     │
│  🕐 Semana   │  ─────────────────────────────────────────────────  │
│              │                                                     │
│              │  ┌─────────────────────────────────────────────┐   │
│  [+ Nova]    │  │ Digite sua mensagem...              📎 🎤 ➤│   │
│              │  └─────────────────────────────────────────────┘   │
└──────────────┴─────────────────────────────────────────────────────┘
```

### ✨ Features UX

| Feature | Descrição | Prioridade |
|---------|-----------|------------|
| **Sidebar colapsável** | Projetos → Conversas hierárquico | P0 |
| **Busca global** | Buscar em todas as conversas | P1 |
| **Tags/Labels** | Categorizar conversas | P2 |
| **Pin/Unpin** | Fixar conversas importantes | P0 |
| **Archive** | Arquivar conversas antigas | P1 |
| **Rename** | Renomear conversas | P0 |
| **Soft delete** | Lixeira com recuperação | P1 |
| **Streaming indicator** | Animação durante geração | P0 |
| **Thinking indicator** | "Pensando..." com animação | P0 |
| **Error/Retry** | Botão retry em erros | P0 |
| **Cost estimate** | Mostrar custo estimado | P2 |
| **Drafts** | Salvar rascunhos | P2 |
| **Multi-line input** | Shift+Enter para nova linha | P0 |
| **Keyboard shortcuts** | Ctrl+Enter enviar, etc | P1 |
| **Copy code block** | Botão copiar em código | P0 |
| **Feedback thumbs** | 👍👎 em respostas | P1 |
| **Regenerate** | Regenerar resposta | P1 |
| **Edit message** | Editar e reenviar | P2 |

### ⌨️ Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+Enter` | Enviar mensagem |
| `Shift+Enter` | Nova linha |
| `Ctrl+N` | Nova conversa |
| `Ctrl+K` | Busca global |
| `Ctrl+/` | Ajuda/atalhos |
| `Esc` | Cancelar geração |

---

## 7) Plano Faseado (Backlog Executável)

### 📍 Fase 0: Correção do Reset + Persistência Mínima

**Objetivo:** Chat não zera ao navegar  
**Duração:** 1-2 dias

| # | Tarefa | Arquivos | Critérios de Aceite | Risco |
|---|--------|----------|---------------------|-------|
| 0.1 | Criar `store/chat.ts` com Zustand + persist | `apps/studio/store/chat.ts` | Store criado e exportado | Baixo |
| 0.2 | Refatorar `chat/page.tsx` para usar store | `apps/studio/app/chat/page.tsx` | Mensagens persistem no localStorage | Baixo |
| 0.3 | Adicionar ID de conversa | `chat/page.tsx`, `store/chat.ts` | Cada conversa tem UUID único | Baixo |
| 0.4 | Testar navegação | E2E tests | Navegar e voltar mantém histórico | Baixo |

### 📍 Fase 1: Projetos/Assuntos + UI/Rotas

**Objetivo:** Organização por projetos  
**Duração:** 3-5 dias

| # | Tarefa | Arquivos | Critérios de Aceite | Risco |
|---|--------|----------|---------------------|-------|
| 1.1 | Schema SQL para projects/conversations | `migrations/001_chat.sql` | Tabelas criadas no Supabase | Médio |
| 1.2 | Endpoints CRUD projetos | `apps/api/src/chat/api/projects.py` | GET/POST/PATCH/DELETE funcionando | Médio |
| 1.3 | Endpoints CRUD conversas | `apps/api/src/chat/api/conversations.py` | Listar, criar, atualizar, deletar | Médio |
| 1.4 | Componente ConversationSidebar | `apps/studio/components/chat/Sidebar.tsx` | Lista projetos e conversas | Médio |
| 1.5 | Página /chat/[id] | `apps/studio/app/chat/[id]/page.tsx` | Rota dinâmica por conversa | Baixo |
| 1.6 | Busca, pin, archive, rename | Sidebar + API | Funcionalidades implementadas | Médio |

### 📍 Fase 2: Personas + Contexto/Tokens

**Objetivo:** Personalização e contexto inteligente  
**Duração:** 3-5 dias

| # | Tarefa | Arquivos | Critérios de Aceite | Risco |
|---|--------|----------|---------------------|-------|
| 2.1 | Schema SQL personas | `migrations/002_personas.sql` | Tabela personas criada | Baixo |
| 2.2 | CRUD personas | `apps/api/src/chat/api/personas.py` | Criar, editar, deletar personas | Médio |
| 2.3 | Selector de persona no chat | `apps/studio/components/chat/PersonaSelector.tsx` | Dropdown funcional | Médio |
| 2.4 | Implementar ContextBuilder | `apps/api/src/chat/core/context.py` | Token budgeting funcionando | Alto |
| 2.5 | Sumarização incremental | `apps/api/src/chat/services/summarizer.py` | Resumos sendo criados | Alto |
| 2.6 | UI exibir custo/tokens | `apps/studio/components/chat/TokenCounter.tsx` | Contador visível | Baixo |

### 📍 Fase 3: Roteamento de LLM + Observabilidade

**Objetivo:** Multi-provider otimizado  
**Duração:** 3-5 dias

| # | Tarefa | Arquivos | Critérios de Aceite | Risco |
|---|--------|----------|---------------------|-------|
| 3.1 | LLMRouter com fallback | `apps/api/src/llm/router.py` | Fallback automático | Médio |
| 3.2 | Streaming SSE | `apps/api/src/chat/streaming/` | Tokens chegando em tempo real | Alto |
| 3.3 | SSE client no frontend | `apps/studio/hooks/useSSE.ts` | Renderização progressiva | Médio |
| 3.4 | Tabela llm_usage | `migrations/003_usage.sql` | Logs de uso salvos | Baixo |
| 3.5 | Dashboard de custos | `apps/studio/app/settings/usage/page.tsx` | Gráficos de uso | Médio |
| 3.6 | Tracing com OpenTelemetry | `apps/api/src/observability/` | Traces no Jaeger/similar | Alto |

---

## 8) Checklist Final de Validação

### ✅ Testes

- [ ] Unit tests para ChatService
- [ ] Unit tests para ContextBuilder
- [ ] Integration tests para endpoints
- [ ] E2E tests: criar conversa, enviar mensagem, navegar
- [ ] E2E tests: streaming funcionando
- [ ] Load test: 100 conversas simultâneas

### ✅ Migrações

- [ ] Schema SQL revisado por DBA
- [ ] Migrations testadas em staging
- [ ] Rollback plan documentado
- [ ] Índices otimizados

### ✅ Performance

- [ ] Latência p95 < 200ms para listar conversas
- [ ] Time to first token < 500ms
- [ ] Payload de mensagens < 50KB
- [ ] Lazy loading para conversas antigas

### ✅ Segurança

- [ ] Auth obrigatório em todos endpoints
- [ ] RBAC: usuário só vê suas conversas
- [ ] Rate limiting: 60 req/min por usuário
- [ ] Input sanitization (XSS)
- [ ] Prompt injection protection
- [ ] PII não logado em plain text

### ✅ Observabilidade

- [ ] Logs estruturados (JSON)
- [ ] Métricas Prometheus
- [ ] Traces OpenTelemetry
- [ ] Alertas configurados
- [ ] Dashboard Grafana

---

## 📎 Anexos

### A. Referências

- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [Anthropic Messages API](https://docs.anthropic.com/claude/reference/messages)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [Supabase Realtime](https://supabase.com/docs/guides/realtime)

### B. Decisões Arquiteturais (ADRs)

| ADR | Decisão | Justificativa |
|-----|---------|---------------|
| ADR-001 | Zustand + persist para state | Simples, funciona com SSR |
| ADR-002 | PostgreSQL para persistência | Supabase já configurado |
| ADR-003 | SSE para streaming | Mais simples que WebSocket |
| ADR-004 | Token budgeting no backend | Centralizado, consistente |
| ADR-005 | Soft delete | Permitir recuperação |

---

**Fim do Relatório de Auditoria**

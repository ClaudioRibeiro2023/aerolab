# Fluxos Principais

> Documentação dos fluxos críticos end-to-end da plataforma.

---

## 1. Fluxo de Chat com Agente

### Descrição
Usuário envia mensagem, agente processa e responde.

### Diagrama

```mermaid
sequenceDiagram
    participant U as Usuário
    participant F as Frontend
    participant B as Backend
    participant A as Agente
    participant L as LLM Provider

    U->>F: Envia mensagem
    F->>B: POST /chat/message
    B->>B: Valida JWT
    B->>A: Processa mensagem
    A->>L: Inference request
    L-->>A: Resposta LLM
    A-->>B: Resposta processada
    B-->>F: JSON response
    F-->>U: Exibe resposta
```

### Diagrama ASCII

```
Usuário    Frontend    Backend    Agente    LLM
   │           │           │         │        │
   │──mensagem─►           │         │        │
   │           │──POST────►│         │        │
   │           │           │──proc.──►        │
   │           │           │         │──req.──►
   │           │           │         │◄─resp.─│
   │           │           │◄─resp.──│        │
   │           │◄──JSON────│         │        │
   │◄─display──│           │         │        │
```

### Código Relevante

- **Frontend:** `frontend/app/chat/page.tsx`
- **Backend:** `src/chat/api/routes.py`
- **Agente:** `src/agents/base_agent.py`

---

## 2. Fluxo de RAG Query

### Descrição
Usuário faz pergunta, sistema busca contexto relevante e gera resposta.

### Diagrama

```mermaid
sequenceDiagram
    participant U as Usuário
    participant B as Backend
    participant R as RAG Service
    participant C as ChromaDB
    participant L as LLM

    U->>B: POST /rag/query
    B->>R: query(collection, text)
    R->>R: Gera embedding
    R->>C: Busca similares
    C-->>R: Chunks relevantes
    R->>L: Contexto + Query
    L-->>R: Resposta
    R-->>B: Resultado
    B-->>U: JSON response
```

### Diagrama ASCII

```
Usuário    Backend    RAGService    ChromaDB    LLM
   │          │            │            │         │
   │──query──►│            │            │         │
   │          │──query────►│            │         │
   │          │            │──embed────►│         │
   │          │            │◄─chunks────│         │
   │          │            │──context──────────►│
   │          │            │◄──response────────│
   │          │◄─result────│            │         │
   │◄─JSON────│            │            │         │
```

### Código Relevante

- **Router:** `src/os/routes/rag.py`
- **Service:** `src/rag/service.py`
- **Chunking:** `src/rag/chunking.py`

---

## 3. Fluxo de Execução de Workflow (Flow Studio)

### Descrição
Usuário executa workflow visual, sistema processa nós sequencialmente.

### Diagrama

```mermaid
sequenceDiagram
    participant U as Usuário
    participant F as Flow Studio
    participant E as Engine
    participant X as Executor
    participant A as Agente

    U->>F: Clica "Execute"
    F->>E: execute(workflow)
    loop Para cada nó
        E->>X: execute_node(node)
        alt Se nó é agente
            X->>A: run(input)
            A-->>X: output
        else Se nó é condição
            X->>X: avaliar condição
        end
        X-->>E: node_result
    end
    E-->>F: workflow_result
    F-->>U: Exibe resultado
```

### Diagrama ASCII

```
Usuário    FlowStudio    Engine    Executor    Agente
   │           │            │          │          │
   │──execute──►            │          │          │
   │           │──execute──►│          │          │
   │           │            │──node───►│          │
   │           │            │          │──run────►│
   │           │            │          │◄─output──│
   │           │            │◄─result──│          │
   │           │            │   (loop) │          │
   │           │◄─result────│          │          │
   │◄─display──│            │          │          │
```

### Código Relevante

- **API:** `src/flow_studio/api/`
- **Engine:** `src/flow_studio/engine.py`
- **Executor:** `src/flow_studio/executor.py`

---

## 4. Fluxo de Autenticação JWT

### Descrição
Usuário faz login, recebe token JWT, usa para acessar recursos protegidos.

### Diagrama

```mermaid
sequenceDiagram
    participant U as Usuário
    participant F as Frontend
    participant B as Backend

    Note over U,B: Login
    U->>F: Email + Senha
    F->>B: POST /auth/login
    B->>B: Valida credenciais
    B->>B: Gera JWT
    B-->>F: {token: "eyJ..."}
    F->>F: Salva token

    Note over U,B: Request Autenticado
    U->>F: Acessa /agents
    F->>B: GET /agents + Bearer token
    B->>B: Valida JWT
    B->>B: Extrai user/role
    B-->>F: Lista de agentes
    F-->>U: Exibe agentes
```

### Diagrama ASCII

```
                    LOGIN
Usuário    Frontend    Backend
   │           │          │
   │──creds───►│          │
   │           │──POST───►│
   │           │          │──valida
   │           │          │──gera JWT
   │           │◄─token───│
   │           │──salva   │

               REQUEST AUTENTICADO
   │──acessa──►│          │
   │           │──GET+JWT►│
   │           │          │──valida JWT
   │           │◄─data────│
   │◄─display──│          │
```

### Código Relevante

- **Router:** `src/os/routes/auth.py`
- **JWT:** `src/auth/jwt.py`
- **Dependencies:** `src/auth/deps.py`

---

## 5. Fluxo de Orquestração de Time

### Descrição
Time de agentes executa tarefa complexa com coordenador delegando para workers.

### Diagrama

```mermaid
sequenceDiagram
    participant U as Usuário
    participant O as Orchestrator
    participant C as Coordinator
    participant W1 as Worker 1
    participant W2 as Worker 2

    U->>O: execute(task)
    O->>C: delegate(task)
    C->>C: Planeja subtarefas

    par Execução paralela
        C->>W1: subtask_1
        W1-->>C: result_1
    and
        C->>W2: subtask_2
        W2-->>C: result_2
    end

    C->>C: Combina resultados
    C-->>O: final_result
    O-->>U: response
```

### Diagrama ASCII

```
Usuário    Orchestrator    Coordinator    Worker1    Worker2
   │            │               │            │          │
   │──execute──►│               │            │          │
   │            │──delegate────►│            │          │
   │            │               │──plan      │          │
   │            │               │            │          │
   │            │               │──task1────►│          │
   │            │               │──task2───────────────►│
   │            │               │◄─result1──│          │
   │            │               │◄─result2─────────────│
   │            │               │──combine   │          │
   │            │◄──result──────│            │          │
   │◄─response──│               │            │          │
```

### Código Relevante

- **API:** `src/team_orchestrator/api/`
- **Engine:** `src/team_orchestrator/engine.py`
- **Modes:** `src/team_orchestrator/modes/`

---

## Resumo dos Fluxos

| Fluxo | Complexidade | Latência Típica | Componentes |
|-------|--------------|-----------------|-------------|
| Chat simples | Baixa | 1-3s | Frontend → Backend → LLM |
| RAG Query | Média | 2-5s | Backend → ChromaDB → LLM |
| Workflow | Alta | 5-30s | Engine → Executors → Agents |
| Auth | Baixa | <100ms | Backend (JWT) |
| Team Orchestration | Alta | 10-60s | Coordinator → Workers |

---

## Referências

- [Visão C4](11-visao-c4.md)
- [Módulos e Limites](13-modulos-e-limites.md)

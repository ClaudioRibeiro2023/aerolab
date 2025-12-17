# Glossário

> Termos e definições usados na plataforma Agno Multi-Agent Platform.

---

## A

### Agente (Agent)
Entidade autônoma de IA que pode perceber seu ambiente, tomar decisões e executar ações. No contexto Agno, um agente tem modelo LLM, ferramentas, memória e instruções.

### Agno Framework
Framework Python open-source para construção de sistemas multi-agente. Fornece abstrações para agentes, times, workflows e integração com LLM providers.

### AgentOS
Runtime do Agno que gerencia execução de agentes em produção. Inclui routers modulares, autenticação, rate limiting e observabilidade.

### API Key
Chave de autenticação para acessar serviços externos (ex: `GROQ_API_KEY`, `OPENAI_API_KEY`).

---

## C

### ChromaDB
Banco de dados vetorial open-source usado para armazenar embeddings no sistema RAG.

### Chunking
Processo de dividir documentos grandes em pedaços menores (chunks) para indexação e retrieval eficiente.

### Coordinator
Agente central em um time que delega tarefas para outros agentes (workers).

### CORS
Cross-Origin Resource Sharing. Política de segurança que controla quais origens podem acessar a API.

---

## D

### Domain Studio
Módulo que permite criar domínios especializados com RAG engines customizados (Agentic RAG, Graph RAG, etc.).

### Dashboard
Interface de observabilidade que mostra métricas, logs e insights sobre o sistema.

---

## E

### Embedding
Representação vetorial densa de texto/imagem. Usado para busca semântica no RAG.

### Executor
Componente do Flow Studio que executa um tipo específico de nó (agent, condition, loop, etc.).

---

## F

### FastAPI
Framework Python assíncrono para construção de APIs REST. Base do backend Agno.

### Flow Studio
Editor visual drag-and-drop para construir workflows de agentes.

### Function Calling
Capacidade de LLMs de chamar funções/ferramentas estruturadas durante a geração.

---

## G

### GDPR/LGPD
Regulamentações de proteção de dados (Europa/Brasil). O módulo `compliance/gdpr.py` implementa consentimento e direitos do titular.

### Groq
Provedor de LLM com inferência ultrarrápida. Recomendado para começar (API gratuita).

---

## H

### HITL (Human-in-the-Loop)
Padrão onde humanos intervêm em pontos críticos do workflow para aprovação, correção ou escalação.

### Health Check
Endpoint que retorna status de saúde do serviço (`/health`, `/health/live`, `/health/ready`).

---

## J

### JWT (JSON Web Token)
Token auto-contido usado para autenticação stateless. Contém claims como `sub` (subject), `role`, `exp` (expiração).

---

## L

### LLM (Large Language Model)
Modelo de linguagem grande treinado em texto massivo. Ex: GPT-4, Claude, Llama 3.

### Lifespan
Contexto de ciclo de vida do FastAPI que gerencia startup/shutdown da aplicação.

---

## M

### MCP (Model Context Protocol)
Protocolo padrão para expor ferramentas e recursos para LLMs. Implementado em `src/mcp/`.

### Memory
Sistema de memória de agentes:
- **Short-term:** Contexto da conversa atual
- **Long-term:** Conhecimento persistido entre sessões
- **Episodic:** Memória de eventos específicos

### Metrics
Métricas do sistema expostas em formato Prometheus (`/metrics`).

### Middleware
Componente que processa requests/responses antes/depois dos handlers. Ex: rate limiting, logging.

### Multi-tenancy
Suporte a múltiplos inquilinos (tenants) isolados na mesma instância.

---

## N

### Next.js
Framework React para aplicações web. Usado no frontend com App Router (v15).

### Node (Nó)
Elemento de um workflow no Flow Studio. Tipos: agent, condition, loop, transform, etc.

---

## O

### OpenAPI
Especificação para documentar APIs REST. Gerada automaticamente pelo FastAPI em `/openapi.json`.

### Orchestration Mode
Modo de coordenação de times:
- **Sequential:** Agentes executam em ordem
- **Parallel:** Agentes executam simultaneamente
- **Hierarchical:** Estrutura de delegação
- **Swarm:** Auto-organização emergente

---

## P

### Pipeline
Sequência de operações de processamento. Ex: RAG pipeline (ingest → chunk → embed → store).

### Pydantic
Biblioteca Python para validação de dados com tipagem. Usada em models e configurações.

---

## R

### RAG (Retrieval-Augmented Generation)
Técnica que combina busca em base de conhecimento com geração LLM para respostas fundamentadas.

### Rate Limiting
Limitação de requisições por tempo para prevenir abuso. Configurado por tipo de endpoint.

### RBAC (Role-Based Access Control)
Controle de acesso baseado em papéis. Papéis: `admin`, `user`.

### Router
Agrupamento de endpoints relacionados no FastAPI. Ex: `auth_router`, `agents_router`.

---

## S

### shadcn/ui
Biblioteca de componentes React acessíveis e customizáveis. Base do design system.

### SSO (Single Sign-On)
Login único via provedores externos (Google, GitHub, Microsoft).

### Swagger
Interface interativa para documentação de API. Disponível em `/docs`.

---

## T

### TailwindCSS
Framework CSS utility-first. Usado para styling no frontend.

### Team (Time)
Conjunto de agentes que colaboram para completar tarefas complexas.

### TanStack Query
Biblioteca para gerenciamento de estado assíncrono no React. Substitui useEffect para data fetching.

### Tool (Ferramenta)
Capacidade que um agente pode usar. Ex: web_search, code_executor, file_read.

---

## V

### Vector Store
Banco de dados otimizado para busca por similaridade vetorial. ChromaDB é o padrão.

---

## W

### Webhook
Callback HTTP para notificar sistemas externos sobre eventos.

### Workflow
Sequência de passos que define um processo de negócio. Pode ser visual (Flow Studio) ou código.

### Worker
Agente em um time que executa tarefas delegadas pelo coordinator.

---

## Z

### Zustand
Biblioteca de gerenciamento de estado para React. Usado no frontend.

---

## Siglas Comuns

| Sigla | Significado |
|-------|-------------|
| API | Application Programming Interface |
| CI/CD | Continuous Integration / Continuous Deployment |
| CRUD | Create, Read, Update, Delete |
| DB | Database |
| ENV | Environment Variables |
| HTTP | HyperText Transfer Protocol |
| JSON | JavaScript Object Notation |
| REST | Representational State Transfer |
| SDK | Software Development Kit |
| SQL | Structured Query Language |
| SSR | Server-Side Rendering |
| UI/UX | User Interface / User Experience |
| URL | Uniform Resource Locator |
| UUID | Universally Unique Identifier |

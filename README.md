# 🚀 AeroLab

> **Plataforma Multi-Agente de IA** | **Versão:** 5.1.0 | **Dezembro 2024**

AeroLab é uma plataforma completa para criação, orquestração e gerenciamento de agentes de inteligência artificial. Combine múltiplos agentes em times, automatize workflows complexos e potencialize sua equipe com IA.

## ✨ Características

### 🤖 Agentes de IA

- **Agentes Especializados** - Crie agentes com instruções personalizadas
- **15+ Domínios** - Legal, Finance, DevOps, Data Science, Corporate e mais
- **Multi-Provider** - OpenAI, Anthropic, Google, Groq, Ollama
- **Memória Persistente** - Agentes que lembram contexto entre conversas
- **Tools Integration** - Conecte agentes a ferramentas externas

### 👥 Times & Orquestração

- **Team Orchestrator** - 15+ modos de orquestração
- **Agent Personas** - 20+ personas pré-configuradas
- **Conflict Resolution** - Resolução automática de conflitos
- **NL Team Builder** - Crie times com linguagem natural

### 🔄 Workflows & Automação

- **Flow Studio** - Visual workflow builder com 60+ tipos de nós
- **NL to Workflow** - Descreva em português, gere o workflow
- **Real-time Execution** - Execute e monitore em tempo real
- **Templates** - Workflows prontos para casos comuns

### 📚 RAG & Conhecimento

- **Agentic RAG** - Retrieval-augmented generation inteligente
- **Multi-format Ingestion** - PDF, DOCX, TXT, MD, código
- **Collections** - Organize documentos em coleções
- **Hybrid Search** - Busca semântica + keyword

### 🎨 Interface Moderna

- **Next.js 15** + React 19 + TypeScript
- **Design System v5** - 25+ componentes premium
- **Dark Mode** - Suporte completo
- **Command Palette** - Navegação rápida com ⌘K
- **Responsive** - Mobile, tablet e desktop

## 📁 Estrutura do Projeto

```text
├── apps/
│   ├── studio/                 # Frontend Next.js (AeroLab Studio)
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities, API client
│   │   └── e2e/                # Playwright E2E tests
│   │
│   └── api/                    # Backend FastAPI (AeroLab API)
│       ├── server.py           # Main server
│       └── src/
│           ├── agents/         # Agent management
│           ├── teams/          # Team orchestration
│           ├── workflows/      # Workflow engine
│           ├── rag/            # RAG system
│           ├── chat/           # Chat system
│           └── observability/  # Metrics, tracing
│
├── packages/
│   ├── design-system/          # UI components + Storybook
│   ├── shared/                 # Shared utilities
│   └── types/                  # TypeScript types
│
├── docs/                       # Documentation
└── .github/workflows/          # CI/CD (GitHub Actions)
```

## 🚀 Início Rápido

### Pré-requisitos

- Node.js >= 18
- pnpm >= 9
- Python >= 3.11

### Instalação

```bash
# Clone o repositório
git clone https://github.com/ClaudioRibeiro2023/aerolab.git
cd aerolab

# Instale dependências do frontend
pnpm install

# Crie ambiente Python para a API
cd apps/api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Desenvolvimento

```bash
# Terminal 1 - API Backend (porta 8000)
cd apps/api
python server.py

# Terminal 2 - Studio Frontend (porta 3000)
pnpm dev:studio
```

### Produção Local

```bash
# Build do Studio
pnpm build:studio

# Iniciar API
cd apps/api && uvicorn server:app --host 0.0.0.0 --port 8000

# Iniciar Studio (porta 9000)
pnpm --filter @aerolab/studio run start -p 9000
```

### URLs

| Serviço      | URL                        |
| ------------ | -------------------------- |
| **Studio**   | http://localhost:9000      |
| **API**      | http://localhost:8000      |
| **API Docs** | http://localhost:8000/docs |

## 🔐 Autenticação

Login simples com JWT. Para desenvolvimento, use `admin` como usuário.

| Role      | Descrição               |
| --------- | ----------------------- |
| **admin** | Acesso total ao sistema |
| **user**  | Acesso padrão           |

## 🧪 Testes

```bash
# Testes E2E do Studio
cd apps/studio
pnpm test:e2e

# Com interface visual
pnpm test:e2e:ui

# Testes da API
cd apps/api
pytest
```

## 📝 Scripts Disponíveis

| Comando             | Descrição                      |
| ------------------- | ------------------------------ |
| `pnpm dev:studio`   | Studio em modo desenvolvimento |
| `pnpm dev:all`      | API + Studio em paralelo       |
| `pnpm build:studio` | Build de produção do Studio    |
| `pnpm lint`         | Executa ESLint                 |
| `pnpm typecheck`    | Verifica tipos TypeScript      |
| `pnpm test:e2e`     | Testes E2E (Playwright)        |

## 🛠️ Tecnologias

| Camada              | Tecnologia     | Versão |
| ------------------- | -------------- | ------ |
| **Frontend**        | Next.js        | 15.x   |
| **UI**              | React          | 19.x   |
| **Linguagem**       | TypeScript     | 5.x    |
| **Estilização**     | TailwindCSS    | 3.x    |
| **Estado**          | TanStack Query | 5.x    |
| **Backend**         | FastAPI        | 0.115+ |
| **AI Framework**    | Agno           | latest |
| **Testes E2E**      | Playwright     | 1.x    |
| **Package Manager** | pnpm           | 9.x    |

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Commit suas mudanças: `git commit -m 'feat: minha feature'`
4. Push para a branch: `git push origin feature/minha-feature`
5. Abra um Pull Request

## 📄 Licença

MIT © 2025 AeroLab

---

**AeroLab** - Potencialize sua equipe com IA 🚀

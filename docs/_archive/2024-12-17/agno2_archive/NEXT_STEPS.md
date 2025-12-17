# 📌 Próximos Passos – Agno Multi‑Agent Platform

**Data de referência:** 2025‑12‑05  
**Responsável:** Cascade (assistente via IDE)  
**Contexto:** Plataforma Agno com backend + frontend validados, scripts de deploy/validação automáticos e UX avançada implementada (Fases 1 e 2 do frontend, conforme `FASE1_COMPLETA.md`, `IMPLEMENTACAO_COMPLETA.md`, `TODAS_FASES_COMPLETAS.md` e `SUMMARY.md`).

---

## 1. Estado atual (onde paramos)

- **Backend (FastAPI / AgentOS)**
  - App principal em `app.py` usando `src/os/builder_new.py` (routers modulares: agents, teams, workflows, RAG, HITL, storage, auth, memory, metrics, admin, audit).
  - RAG integrado com ChromaDB (local ou HTTP) via `src/rag/service.py`.
  - HITL ajustado (prefixo `/hitl`, payload padronizado) e RAG sem auth desnecessária.
  - Configurações centralizadas em `src/config/settings.py` com suporte a `.env`, diretórios de dados e validação básica.
  - Testes automatizados de API em `scripts/debug_full_platform.py` cobrindo 15 cenários principais (ver `SUMMARY.md`).

- **Frontend (Next.js / Netlify)**
  - App em `frontend/` com autenticação via `/auth/login`, store corrigido e `Protected` com hidratação e loading (ver `ANALISE_COMPLETA_PERMISSOES.md`).
  - UX Fase 1 concluída: biblioteca de templates, wizard visual de criação de agentes, preview em tempo real, empty states inteligentes, widget de feedback (ver `FASE1_COMPLETA.md`).
  - Fase 2 iniciada/avançada: sistema de analytics no frontend (`lib/analytics.ts`) e `AnalyticsDashboard` (ver `IMPLEMENTACAO_COMPLETA.md` e `TODAS_FASES_COMPLETAS.md`).
  - Páginas principais: `/agents`, `/agents/new`, `/agents/[name]/edit`, `/chat`, dashboard etc., já integradas com os componentes novos conforme docs.

- **Deploy & Automação**
  - **Backend** preparado para Railway (ou Render/VPS) com Dockerfile, `docker-compose.yml` e variáveis em `railway_env*.txt`.
  - **Frontend** preparado para Netlify com `netlify.toml` e guia `frontend/DEPLOY_NETLIFY.md`.
  - Scripts de automação PowerShell na raiz:
    - `DEPLOY_AUTOMATICO_COMPLETO.ps1` → orquestra deploy/atualização Railway + Netlify + validação.
    - `auto_deploy_railway.ps1`, `auto_deploy_netlify.ps1`, `auto_validate.ps1`, `deploy_auto.ps1` (legacy).
  - `README_AUTOMACAO.md` descreve o fluxo completo, tokens necessários e URLs atuais de backend/frontend.

- **Documentação & Roadmap**
  - `SUMMARY.md` → status do debugging e preparação para deploy (15/15 testes passando, RAG/HITL/Teams validados).
  - `ANALISE_MELHORIAS.md` e `ROADMAP_EVOLUCAO.md` → visão de produto (fases, UX avançada, RAG avançado, workflow builder visual, analytics, etc.).
  - Diversos guias de deploy (`DEPLOY.md`, `GUIA_DEPLOY_DIDATICO.md`, `PASSO_A_PASSO_DEPLOY.md`, `CHECKLIST_DEPLOY.md`).

> **Em resumo:** código e UX estão em ponto de "production ready" com forte documentação e scripts de automação. O foco dos próximos passos é: consolidar observabilidade/analytics, testar com usuários reais, evoluir integrações externas e preparar para escala/enterprise.

---

## 2. Prioridades imediatas (0–2 dias) ✅ CONCLUÍDO

> **Última atualização:** 2025-12-05 14:46 UTC-3  
> **Status:** Todos os itens validados e funcionando.

### 2.1. Confirmar estado atual dos ambientes (Railway + Netlify) ✅

- [x] **Rodar validação automática** (local, PowerShell):
  - `./auto_validate.ps1` executado com sucesso
  - Health do backend: ✅ OK
  - Auth (login admin + user): ✅ OK
  - Agents/workflows/RAG/HITL/Teams: ✅ Respondendo
  - Frontend acessível: ✅ OK
- [x] **Deploy completo automatizado executado**:
  - `./DEPLOY_AUTOMATICO_COMPLETO.ps1` executado
  - Scripts de CLI corrigidos (Railway e Netlify nova sintaxe)
  - Variáveis Railway alinhadas com `railway_env_FINAL.txt`
  - `NEXT_PUBLIC_API_URL` apontando para backend correto

### 2.2. Sincronizar variáveis de ambiente locais ✅

- [x] `.env` na raiz alinhado com `railway_env_FINAL.txt`:
  - `DEFAULT_MODEL_PROVIDER=groq` ✅
  - `DEFAULT_MODEL_ID=llama-3.3-70b-versatile` ✅
  - `CORS_ALLOW_ORIGINS=https://agno-multi-agent.netlify.app` ✅ (atualizado)
- [x] `.env.local` em `frontend/` conforme `frontend/README.md` ✅

### 2.3. Smoke test automatizado via API ✅

Script criado: `scripts/smoke_test_api.ps1`

**Resultado:** 18/20 testes passando (90%), 0 falhas, 2 skips esperados

| Categoria | Testes | Status |
|-----------|--------|--------|
| Health Check | 2 | ✅ OK |
| Autenticação (admin + user) | 2 | ✅ OK |
| Agents CRUD | 3 | ✅ OK |
| Execução de Agente | 1 | ✅ OK |
| Workflows | 1 | ✅ OK |
| RAG (ingest + query) | 3 | ✅ OK |
| HITL (start + complete) | 3 | ✅ OK |
| Teams | 1 | ✅ OK |
| RBAC (permissões) | 2 | ✅ OK |
| Frontend | 1 | ✅ OK |
| Limpeza | 1 | ✅ OK |

**URLs validadas:**
- Backend: https://web-production-940ab.up.railway.app
- Frontend: https://agno-multi-agent.netlify.app

**Correções aplicadas durante validação:**
1. `auto_deploy_railway.ps1` - sintaxe Railway CLI v3+ (`--set` em vez de `set`)
2. `auto_deploy_netlify.ps1` - sintaxe Netlify CLI (`--site` em vez de `--site-id`)
3. `scripts/smoke_test_api.ps1` - criado do zero para validação automatizada

---

## 3. Curto prazo (3–10 dias) – Produto e UX

### 3.1. Consolidar e expor Analytics na UI ✅

> **Implementado em:** 2025-12-05

- [x] Revisar `frontend/lib/analytics.ts` e `components/AnalyticsDashboard.tsx`:
  - ✅ Tracking integrado em `/chat`, `/agents` (execução rápida) e `/teams/[name]/run`
  - ✅ Cálculo de custos por provedor/modelo funcionando (OpenAI, Anthropic, Groq)
- [x] Integrar o dashboard no fluxo principal (`/dashboard`):
  - ✅ `AnalyticsDashboard` já integrado na página dashboard (linha 441)
  - ✅ Cards de métricas: execuções, taxa de sucesso, custo total, agentes ativos
  - ✅ Tabela de top agentes por performance
- [x] Funcionalidades adicionais:
  - ✅ Seletor de período (7d, 30d, 90d)
  - ✅ Botão para gerar dados de exemplo
  - ✅ Tracking de execuções com sucesso e erro

### 3.2. Chat de agentes mais rico (streaming & contexto)

- [ ] Avaliar uso do `EnhancedChat` em vez do chat atual de `/chat`:
  - Reaproveitar progress bar, anexos, sugestões contextuais e feedback inline.
- [ ] Planejar suporte a streaming (SSE ou Vercel AI SDK):
  - Checar se o backend/AgentOS já está com endpoints SSE prontos (AgentOS suporta SSE via Agno).
  - Ajustar `frontend/lib/api.ts` e componentes para lidar com streaming.
- [ ] Garantir histórico persistente de conversas no frontend (localStorage) como MVP.

### 3.3. Onboarding guiado e ajuda contextual

- [ ] Implementar/validar tour de onboarding (conforme `ANALISE_MELHORIAS.md`):
  - Usar `react-joyride` ou similar.
  - Pelo menos 5 passos: dashboard, agents, workflows, RAG, settings.
- [ ] Adicionar empty states e tooltips em pontos críticos:
  - Criação de agente.
  - Lista vazia de workflows.
  - RAG sem coleções.
- [ ] Página `/help` simples explicando conceitos principais (Agente, Workflow, RAG, HITL).

---

## 4. Médio prazo (2–4 semanas) – Inteligência, memória e custo

### 4.1. Memória de longo prazo para agentes

- [ ] Derivar um `MemoryEnhancedAgent` (esqueleto já descrito em `ANALISE_MELHORIAS.md`):
  - Persistência de interações relevantes (DB Sqlite via Agno DB ou tabela dedicada).
  - API HTTP para recuperar preferências e histórico relevante.
- [ ] Expor configuração de "memória" na UI de agentes:
  - Flag habilitar/desabilitar memória.
  - Nível de "profundidade" (quanto histórico considerar).

### 4.2. Cache inteligente de respostas

- [ ] Implementar camada de cache (ex.: Redis ou SQLite + embeddings) conforme esboço em `ANALISE_MELHORIAS.md`:
  - Chave baseada em similaridade semântica da pergunta.
  - TTL configurável.
- [ ] Adicionar métricas de cache no dashboard:
  - Taxa de acerto (% de requisições servidas pelo cache).
  - Economia de tokens estimada.

### 4.3. RAG avançado (ROADMAP_EVOLUCAO – Fase 5)

- [ ] Estender `src/rag/service.py` e rotas RAG para:
  - Upload de múltiplos arquivos simultaneamente (PDF, DOCX, planilhas).
  - Preview dos documentos/indexados na UI.
  - Visualização de chunks individuais.
- [ ] UI de RAG:
  - Página dedicada a coleções com lista, detalhes, documentos e ações (ingest, delete, preview).

---

## 5. Integracões externas e automação (4–8 semanas)

### 5.1. Conectores nativos prioritários

- [ ] Implementar integrações mínimas viáveis (MVP):
  - Gmail (envio/leitura básica) – foco em 1 ou 2 casos de uso por vez.
  - Google Calendar (criar eventos a partir de agentes).
  - Notion/Slack via webhooks simples.
- [ ] Expor essas integrações como "recursos" dos templates de agentes:
  - Ajustar `agentTemplates.ts` para indicar quais integrações cada template usa.

### 5.2. Marketplace interno de agentes (MVP)

- [ ] Criar uma página "Templates" listando:
  - Templates padrão embutidos.
  - Templates salvos pelo usuário.
- [ ] Permitir importar/exportar template como JSON.
- [ ] (Opcional) Campo de rating simples (apenas local, sem backend ainda).

---

## 6. Observabilidade, segurança e governança

### 6.1. Logs, métricas e tracing

- [ ] Revisar `src/os/routes/metrics.py` e `setup_metrics_middleware`:
  - Confirmar export de métricas padrão (latência, contagem de requisições, erros por rota).
- [ ] Integrar com uma stack de observabilidade (a escolher):
  - Prometheus + Grafana, ou serviço gerenciado.
- [ ] Adicionar page simples de "System status" no frontend consumindo `/metrics` agregadas.

### 6.2. RBAC avançado e auditoria

- [ ] Revisar `src/auth/rbac.py` e docs de roles/domínios:
  - Garantir que rotas críticas usam checks de permissão corretos.
- [ ] Completar/validar rotas de auditoria em `src/os/routes/audit.py` (se aplicável):
  - Registrar ações sensíveis: criação/edição de agentes, workflows, credenciais.
- [ ] Adicionar visão de auditoria no frontend (lista filtrável de eventos recentes).

---

## 7. Processo de desenvolvimento e automação contínua

### 7.1. Padronizar checklist antes de cada deploy

- [ ] Criar/usar checklist leve baseado em `CHECKLIST_DEPLOY.md` e `SUMMARY.md`:
  - Testes automatizados `scripts/debug_full_platform.py`.
  - `npm run build` em `frontend/`.
  - `auto_validate.ps1` após deploy.

### 7.2. CI/CD (GitHub Actions ou similar)

- [ ] Pipeline mínimo:
  - Lint/format (se configurado), typecheck frontend, testes críticos de backend.
  - Build do frontend e do backend (docker build).
- [ ] Pipeline de deploy opcional:
  - Disparar scripts de deploy Railway/Netlify ou usar CLIs diretamente no CI.

---

## 8. Como usar este arquivo

- Use esta lista como **fonte de verdade** de alto nível.
- Os detalhes mais profundos de cada feature já estão nos arquivos:
  - `ANALISE_MELHORIAS.md`
  - `ROADMAP_EVOLUCAO.md`
  - `FASE1_COMPLETA.md`, `IMPLEMENTACAO_COMPLETA.md`, `TODAS_FASES_COMPLETAS.md`
  - `SUMMARY.md`, `README_AUTOMACAO.md`, guias de deploy.
- Ao iniciar um ciclo de trabalho novo, escolha 1–3 itens das seções 2–4, detalhe em issues/tarefas menores e execute.

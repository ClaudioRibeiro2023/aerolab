# ADR-001: Stack Tecnológica

**Data:** 2025-12-10
**Status:** Aceito

## Contexto

Precisávamos definir a stack tecnológica para uma plataforma de agentes de IA que:

- Suporte múltiplos provedores de LLM (OpenAI, Anthropic, Groq)
- Tenha frontend moderno e responsivo
- Seja facilmente deployável em cloud
- Permita extensibilidade e manutenção
- Suporte execução em tempo real (streaming, WebSockets)

## Decisão

**Backend: Python 3.12+ com FastAPI**

- FastAPI oferece alta performance e suporte nativo a async
- Tipagem forte com Pydantic
- Documentação automática (OpenAPI/Swagger)
- Ecossistema Python dominante em AI/ML

**Framework de Agentes: Agno**

- Framework moderno para multi-agent systems
- Suporte nativo a múltiplos LLM providers
- Ferramentas built-in (RAG, memory, tools)
- AgentOS para deployment simplificado

**Frontend: Next.js 15 com TypeScript**

- App Router para melhor performance
- Server Components para SSR
- TypeScript strict para type safety
- React 18 com Suspense e Concurrent Features

**Styling: TailwindCSS + shadcn/ui**

- Utility-first para produtividade
- Componentes pré-construídos e acessíveis
- Bundle size otimizado

**State Management: Zustand**

- API simples e intuitiva
- Sem boilerplate
- Suporte a middleware (persist, devtools)

**Deploy: Railway (backend) + Netlify (frontend)**

- Railway: Deploy de Python/Docker simplificado
- Netlify: CDN global para Next.js
- Ambos com CI/CD integrado ao GitHub

## Consequências

### Positivas

- Desenvolvimento rápido com tipagem forte em ambas as pontas
- Ecossistema maduro para AI/ML no Python
- Performance excelente no frontend com SSR
- Deploy simplificado com ferramentas modernas

### Negativas

- Requer conhecimento de duas linguagens (Python + TypeScript)
- FastAPI é menos maduro que Django/Flask em alguns aspectos
- Next.js tem curva de aprendizado com App Router

### Neutras

- Dependência do framework Agno para funcionalidades core

## Alternativas Consideradas

### Backend: Django + DRF

- **Prós:** Ecossistema maduro, ORM robusto
- **Contras:** Mais pesado, menos async-native
- **Por que não:** FastAPI é mais adequado para APIs de alta performance

### Backend: Node.js + Express

- **Prós:** JavaScript full-stack
- **Contras:** Ecossistema AI/ML menos maduro em JS
- **Por que não:** Python domina em AI/ML

### Frontend: Vue.js ou Svelte

- **Prós:** Curva de aprendizado menor
- **Contras:** Ecossistema menor, menos bibliotecas
- **Por que não:** Next.js/React tem mais recursos para projetos enterprise

## Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Agno Framework](https://docs.agno.com/)

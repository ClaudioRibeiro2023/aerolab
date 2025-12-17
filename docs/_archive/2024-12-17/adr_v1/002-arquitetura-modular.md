# ADR-002: Arquitetura Modular

**Data:** 2025-12-10
**Status:** Aceito

## Contexto

A plataforma cresceu para 150+ arquivos Python e 50+ componentes React. Precisávamos de uma arquitetura que:

- Permita desenvolvimento paralelo por múltiplos desenvolvedores
- Facilite testes unitários e de integração
- Suporte adição de novos domínios (Geo, Finance, Legal, etc.)
- Mantenha baixo acoplamento entre módulos

## Decisão

Adotamos arquitetura **feature-first** no backend com separação clara de camadas:

```
src/
├── agents/           # Core: Agentes base e especializados
├── auth/             # Autenticação e autorização
├── billing/          # Sistema de billing
├── chat/             # Módulo de chat
├── compliance/       # LGPD/GDPR
├── config/           # Configurações centralizadas
├── dashboard/        # Observabilidade
├── domain_studio/    # Domínios especializados
├── enterprise/       # Features enterprise
├── flow_studio/      # Visual workflow builder
├── marketplace/      # Marketplace de agentes
├── mcp/              # Model Context Protocol
├── memory/           # Gestão de memória
├── observability/    # Métricas e tracing
├── os/               # AgentOS runtime
├── rag/              # Retrieval-Augmented Generation
├── rules/            # Rules engine
├── sdk/              # SDK Python
├── studio/           # Agent studio
├── team_orchestrator/# Orquestração de times
├── teams/            # Times multi-agente
├── tools/            # 25+ ferramentas
├── utils/            # Utilitários compartilhados
└── workflows/        # Workflows e pipelines
```

Cada módulo segue a estrutura:

```
modulo/
├── __init__.py       # Exports públicos
├── api/              # Routers FastAPI
├── models/           # Pydantic models
├── services/         # Lógica de negócio
└── tests/            # Testes do módulo
```

## Consequências

### Positivas

- Cada módulo pode ser desenvolvido/testado independentemente
- Imports claros e explícitos
- Fácil adição de novos domínios
- Código organizado por funcionalidade, não por tipo

### Negativas

- Pode haver duplicação de código entre módulos similares
- Navegação inicial pode ser complexa para novos devs
- Imports relativos podem ficar longos

### Neutras

- Requer disciplina para manter separação de concerns

## Alternativas Consideradas

### Arquitetura em Camadas (layers)

```
src/
├── api/        # Todos os routers
├── services/   # Toda lógica
├── models/     # Todos os models
└── utils/      # Utilitários
```

- **Prós:** Estrutura familiar
- **Contras:** Difícil navegar em projetos grandes
- **Por que não:** Feature-first escala melhor

### Microservices

- **Prós:** Isolamento total, deploy independente
- **Contras:** Complexidade operacional, latência de rede
- **Por que não:** Overhead excessivo para o tamanho atual

## Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Feature-Sliced Design](https://feature-sliced.design/)

# Architecture Decision Records (ADRs)

Este diretório contém os registros de decisões arquiteturais do projeto Agno Multi-Agent Platform.

## O que são ADRs?

ADRs são documentos curtos que capturam decisões arquiteturais importantes junto com seu contexto e consequências. Eles servem como:

- **Memória institucional** - Por que fizemos certas escolhas
- **Onboarding** - Novos devs entendem a arquitetura rapidamente
- **Referência** - Base para decisões futuras similares

## Formato

Cada ADR segue o template em `000-template.md`:

1. **Título** - Nome descritivo da decisão
2. **Status** - Proposto, Aceito, Deprecado, Supersedido
3. **Contexto** - Situação que levou à decisão
4. **Decisão** - O que foi decidido
5. **Consequências** - Impactos positivos e negativos
6. **Alternativas** - Opções consideradas

## Índice de ADRs

| ID | Título | Status | Data |
|----|--------|--------|------|
| [001](001-stack-tecnologica.md) | Stack Tecnológica | Aceito | 2025-12-10 |
| [002](002-arquitetura-modular.md) | Arquitetura Modular | Aceito | 2025-12-10 |
| [003](003-autenticacao-jwt-rbac.md) | Autenticação JWT + RBAC | Aceito | 2025-12-10 |

## Como criar um novo ADR

1. Copie `000-template.md` para `NNN-titulo-descritivo.md`
2. Preencha todas as seções
3. Atualize o índice neste README
4. Abra um PR para revisão

## Referências

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

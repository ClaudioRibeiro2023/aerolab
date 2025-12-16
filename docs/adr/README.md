# 📋 Architecture Decision Records (ADR)

> Registro formal das decisões arquiteturais significativas do projeto Template Platform.

## O que são ADRs?

Architecture Decision Records são documentos curtos que capturam decisões arquiteturais importantes junto com seu contexto e consequências. Eles servem como:

- **Memória institucional** - Preservam o "porquê" das decisões
- **Onboarding** - Ajudam novos membros a entender a arquitetura
- **Governança** - Fornecem rastreabilidade das decisões técnicas

## Índice de ADRs

| ADR                                   | Título                         | Status   | Data       |
| ------------------------------------- | ------------------------------ | -------- | ---------- |
| [000](./000-template.md)              | Template para novos ADRs       | Template | -          |
| [001](./001-stack-tecnologica.md)     | Stack Tecnológica              | Aceito   | 2024-12-16 |
| [002](./002-arquitetura-modular.md)   | Arquitetura Modular (Monorepo) | Aceito   | 2024-12-16 |
| [003](./003-autenticacao-jwt-rbac.md) | Autenticação JWT + RBAC        | Aceito   | 2024-12-16 |

## Status dos ADRs

- **PROPOSTO** - Decisão em discussão, aguardando aprovação
- **ACEITO** - Decisão aprovada e em vigor
- **DEPRECIADO** - Decisão não mais aplicável, mantida para histórico
- **SUBSTITUÍDO** - Decisão substituída por outro ADR (referenciado)

## Como Criar um Novo ADR

1. Copie o template `000-template.md`
2. Renomeie para `NNN-titulo-em-kebab-case.md`
3. Preencha todas as seções obrigatórias
4. Submeta um PR para revisão
5. Após aprovação, atualize este README

## Estrutura de um ADR

```markdown
# ADR-NNN: Título

## Status

[PROPOSTO | ACEITO | DEPRECIADO | SUBSTITUÍDO]

## Contexto

Problema ou necessidade que motivou a decisão

## Decisão

A decisão tomada e suas razões

## Alternativas Consideradas

Outras opções avaliadas com prós/contras

## Consequências

Impactos positivos, negativos e riscos

## Referências

Links para documentação, issues, discussões
```

## Boas Práticas

1. **Seja conciso** - ADRs devem ser lidos rapidamente
2. **Foque no "porquê"** - O contexto é mais importante que o "como"
3. **Documente alternativas** - Mostra que a decisão foi ponderada
4. **Liste consequências** - Tanto positivas quanto negativas
5. **Mantenha atualizado** - Marque como DEPRECIADO quando não aplicável

## Referências

- [Michael Nygard - Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)

---

_Última atualização: Dezembro 2024_

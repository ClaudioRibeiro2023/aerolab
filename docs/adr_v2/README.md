# 📋 Architecture Decision Records v2

> Registro formal das decisões arquiteturais do AeroLab.

---

## O que são ADRs?

Architecture Decision Records (ADRs) são documentos curtos que capturam decisões arquiteturais importantes junto com seu contexto, alternativas consideradas e consequências.

### Por que usar ADRs?

- **Memória institucional** - Preservam o "porquê" das decisões
- **Onboarding** - Ajudam novos membros a entender a arquitetura
- **Governança** - Fornecem rastreabilidade de decisões técnicas
- **Integração** - Documentam impactos em sistemas externos

---

## Índice de ADRs

### Por Status

#### ✅ Aceitos

| ID                                        | Título                         | Tags                           | Data       |
| ----------------------------------------- | ------------------------------ | ------------------------------ | ---------- |
| [ADR-001](./001-stack-tecnologica.md)     | Stack Tecnológica              | `stack`, `frontend`, `backend` | 2024-12-16 |
| [ADR-002](./002-arquitetura-modular.md)   | Arquitetura Modular (Monorepo) | `arquitetura`, `monorepo`      | 2024-12-16 |
| [ADR-003](./003-autenticacao-jwt-rbac.md) | Autenticação JWT + RBAC        | `segurança`, `auth`, `rbac`    | 2024-12-16 |

#### 📝 Propostos

_Nenhum ADR proposto no momento._

#### 🗄️ Deprecados/Substituídos

_Nenhum ADR deprecado no momento._

### Por Categoria

#### Arquitetura

- [ADR-002](./002-arquitetura-modular.md) - Arquitetura Modular (Monorepo)

#### Stack Tecnológica

- [ADR-001](./001-stack-tecnologica.md) - Stack Tecnológica

#### Segurança

- [ADR-003](./003-autenticacao-jwt-rbac.md) - Autenticação JWT + RBAC

---

## Status dos ADRs

| Status       | Descrição                                          |
| ------------ | -------------------------------------------------- |
| `proposed`   | Decisão em discussão, aguardando aprovação         |
| `accepted`   | Decisão aprovada e em vigor                        |
| `deprecated` | Decisão não mais aplicável, mantida para histórico |
| `superseded` | Decisão substituída por outro ADR                  |

---

## Como Contribuir

### Criar Novo ADR

1. Copie o template: `cp template_v2.md XXX-titulo.md`
2. Substitua `XXX` pelo próximo número sequencial
3. Preencha **todas** as seções obrigatórias
4. Especialmente a seção **6. Impacto em Integrações**
5. Submeta um PR para revisão
6. Após aprovação, atualize este README

### Estrutura do Template v2

```yaml
---
id: 'ADR-XXX'
title: 'Título Descritivo'
status: 'proposed|accepted|deprecated|superseded'
date: 'YYYY-MM-DD'
owners: ['autor1', 'autor2']
tags: ['tag1', 'tag2']
related: ['ADR-YYY']
supersedes: 'ADR-ZZZ' # Se substituir outro
superseded_by: 'ADR-WWW' # Se foi substituído
---
```

### Seções Obrigatórias

1. **Contexto e Problema** - O que motivou a decisão
2. **Drivers** - Fatores que influenciam
3. **Decisão** - O que foi decidido
4. **Alternativas** - O que foi considerado
5. **Consequências** - Trade-offs
6. **Impacto em Integrações** - ⚠️ **OBRIGATÓRIO** para outras apps
7. **Plano de Rollout** - Como implementar
8. **Referências** - Links úteis

### Revisão de ADRs

- Pelo menos **2 aprovações** de membros do time
- Tech Lead ou Arquiteto deve aprovar ADRs com `breaking changes`
- ADRs afetando integrações devem notificar times consumidores

---

## Boas Práticas

### DO ✅

- Seja conciso - ADRs devem ser lidos em 5-10 minutos
- Foque no "porquê" mais que no "como"
- Documente alternativas descartadas
- Liste trade-offs honestamente
- Mantenha atualizado quando o contexto mudar

### DON'T ❌

- Não escreva dissertações
- Não omita alternativas por "óbvias"
- Não ignore impactos em integrações
- Não deixe ADRs "propostos" por muito tempo
- Não delete ADRs - marque como deprecated/superseded

---

## Migração de ADRs Legados

Os ADRs originais em `/docs/adr/` foram migrados para este formato v2:

| ADR Legado                         | ADR v2                                | Status  |
| ---------------------------------- | ------------------------------------- | ------- |
| `adr/001-stack-tecnologica.md`     | `adr_v2/001-stack-tecnologica.md`     | Migrado |
| `adr/002-arquitetura-modular.md`   | `adr_v2/002-arquitetura-modular.md`   | Migrado |
| `adr/003-autenticacao-jwt-rbac.md` | `adr_v2/003-autenticacao-jwt-rbac.md` | Migrado |

Os ADRs legados em `/docs/adr/` permanecem para histórico, com nota apontando para a versão v2.

---

## Referências

- [Michael Nygard - Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [MADR - Markdown ADR](https://adr.github.io/madr/)

---

_Última atualização: Dezembro 2024_

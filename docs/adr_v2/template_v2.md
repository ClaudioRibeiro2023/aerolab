---
id: 'ADR-000'
title: 'Template para ADRs v2'
status: 'template'
date: 'YYYY-MM-DD'
owners:
  - 'Nome do autor'
tags:
  - 'categoria'
related:
  - 'ADR-XXX'
supersedes: null
superseded_by: null
---

# ADR-000: Template para ADRs v2

## 1. Contexto e Problema

Descreva o contexto que motivou esta decisão:

- Qual é o problema ou necessidade de negócio/técnica?
- Quais são as restrições existentes?
- Qual é o escopo da decisão?

> **Problema central:** [Resumo em uma frase]

## 2. Drivers de Decisão

Fatores que influenciam a decisão:

- **DR1:** [Driver 1 - ex: Performance]
- **DR2:** [Driver 2 - ex: Manutenibilidade]
- **DR3:** [Driver 3 - ex: Time-to-market]
- **DR4:** [Driver 4 - ex: Custo]

Priorização: DR1 > DR2 > DR3 > DR4

## 3. Decisão

> **Decidimos:** [Escolha feita em uma frase clara]

### Detalhamento

Explicação detalhada da decisão:

```text
[Código, diagrama ou configuração relevante]
```

### Escopo

- **Afeta:** [Componentes/módulos afetados]
- **Não afeta:** [O que está fora do escopo]

## 4. Alternativas Consideradas

### Alternativa A: [Nome]

**Descrição:** Breve descrição.

| Aspecto | Avaliação            |
| ------- | -------------------- |
| Prós    | - Item 1<br>- Item 2 |
| Contras | - Item 1<br>- Item 2 |
| Esforço | [Baixo/Médio/Alto]   |
| Risco   | [Baixo/Médio/Alto]   |

**Por que descartada:** [Razão]

### Alternativa B: [Nome]

**Descrição:** Breve descrição.

| Aspecto | Avaliação          |
| ------- | ------------------ |
| Prós    | - Item 1           |
| Contras | - Item 1           |
| Esforço | [Baixo/Médio/Alto] |
| Risco   | [Baixo/Médio/Alto] |

**Por que descartada:** [Razão]

## 5. Consequências e Trade-offs

### Positivas

- ✅ [Benefício 1]
- ✅ [Benefício 2]

### Negativas

- ⚠️ [Trade-off 1]
- ⚠️ [Trade-off 2]

### Riscos Identificados

| Risco     | Probabilidade    | Impacto          | Mitigação |
| --------- | ---------------- | ---------------- | --------- |
| [Risco 1] | Baixa/Média/Alta | Baixo/Médio/Alto | [Ação]    |

## 6. Impacto em Integrações e Contratos

> **Seção obrigatória** - Descreva como esta decisão afeta sistemas integradores.

### Breaking Changes

- [ ] Sim / [x] Não

Se sim, detalhar:

- Endpoints afetados
- Schemas alterados
- Período de depreciação

### Contratos Afetados

| Contrato | Mudança     | Ação Necessária |
| -------- | ----------- | --------------- |
| API REST | [Descrição] | [Ação]          |
| Auth/JWT | [Descrição] | [Ação]          |
| Eventos  | [Descrição] | [Ação]          |

### Compatibilidade

- **Backward compatible:** Sim/Não
- **Versão mínima cliente:** [Se aplicável]

## 7. Plano de Rollout/Migração

### Fases

1. **Fase 1 - [Nome]** (Semana X)
   - [ ] Tarefa 1
   - [ ] Tarefa 2

2. **Fase 2 - [Nome]** (Semana Y)
   - [ ] Tarefa 1

### Rollback

Plano de rollback caso necessário:

```bash
# Comandos ou passos para reverter
```

### Métricas de Sucesso

- [ ] [Métrica 1]
- [ ] [Métrica 2]

## 8. Referências

### Internas

- Documento interno: `../caminho/documento.md`
- ADR relacionado: `./ADR-XXX.md`

### Externas

- [Documentação oficial](https://example.com)
- [RFC/Especificação](https://example.com)

---

## Histórico

| Data       | Autor | Mudança |
| ---------- | ----- | ------- |
| YYYY-MM-DD | Nome  | Criação |

---

_Template v2.0 - Template Platform_

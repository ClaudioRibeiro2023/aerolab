# 📚 Índice da Documentação

> Template Platform v1.0.0 | Última atualização: Dezembro 2024

Este arquivo serve como índice central para toda a documentação do projeto.

---

## 🎯 Por Onde Começar

| Seu Objetivo           | Documento                                  |
| ---------------------- | ------------------------------------------ |
| Configurar o ambiente  | [GETTING_STARTED.md](./GETTING_STARTED.md) |
| Entender a arquitetura | [ARCHITECTURE.md](./ARCHITECTURE.md)       |
| Contribuir com código  | [../CONTRIBUTING.md](../CONTRIBUTING.md)   |
| Fazer deploy           | [DEPLOY.md](./DEPLOY.md)                   |
| Resolver problemas     | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |

---

## 📖 Documentação Completa

### Entrada e Configuração

| Documento                                  | Descrição                         | Audiência      |
| ------------------------------------------ | --------------------------------- | -------------- |
| [README.md](../README.md)                  | Visão geral do projeto            | Todos          |
| [GETTING_STARTED.md](./GETTING_STARTED.md) | Setup inicial e primeiro módulo   | Novos devs     |
| [CONTRIBUTING.md](../CONTRIBUTING.md)      | Guia de contribuição e convenções | Contribuidores |

### Arquitetura e Design

| Documento                                            | Descrição                       | Audiência          |
| ---------------------------------------------------- | ------------------------------- | ------------------ |
| [ARCHITECTURE.md](./ARCHITECTURE.md)                 | Estrutura, stack, ADRs          | Desenvolvedores    |
| [PROPOSTA_ARQUITETURA.md](./PROPOSTA_ARQUITETURA.md) | Proposta detalhada de melhorias | Tech Leads         |
| [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)               | Tokens, componentes, Storybook  | Frontend devs      |
| [UI_UX_IMPROVEMENTS.md](./UI_UX_IMPROVEMENTS.md)     | Melhorias de UI/UX planejadas   | Designers/Frontend |

### Funcionalidades

| Documento                                | Descrição                    | Audiência |
| ---------------------------------------- | ---------------------------- | --------- |
| [ROLES_E_ACESSO.md](./ROLES_E_ACESSO.md) | Sistema de permissões RBAC   | Todos     |
| [BOOK_OF_TESTS.md](./BOOK_OF_TESTS.md)   | Matriz de testes e cobertura | QA/Devs   |

### Operações

| Documento                                            | Descrição                       | Audiência   |
| ---------------------------------------------------- | ------------------------------- | ----------- |
| [DEPLOY.md](./DEPLOY.md)                             | Deploy local, staging, produção | DevOps/Devs |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)           | Resolução de problemas comuns   | Todos       |
| [VALIDATION_CHECKLIST.md](./VALIDATION_CHECKLIST.md) | Checklist de validação          | QA/Devs     |

### Decisões Arquiteturais (ADR)

| Documento                                    | Descrição                |
| -------------------------------------------- | ------------------------ |
| [adr/000-template.md](./adr/000-template.md) | Template para novos ADRs |

---

## 🗂️ Estrutura da Documentação

```text
docs/
├── INDEX.md                    # Este arquivo (índice)
├── ARCHITECTURE.md             # Arquitetura e decisões técnicas
├── GETTING_STARTED.md          # Guia de início rápido
├── DEPLOY.md                   # Guia de deploy
├── DESIGN_SYSTEM.md            # Design System completo
├── ROLES_E_ACESSO.md           # Sistema de permissões
├── BOOK_OF_TESTS.md            # Matriz de testes
├── TROUBLESHOOTING.md          # Resolução de problemas
├── VALIDATION_CHECKLIST.md     # Checklist de validação
├── PROPOSTA_ARQUITETURA.md     # Proposta de melhorias
├── UI_UX_IMPROVEMENTS.md       # Melhorias UI/UX
└── adr/                        # Architecture Decision Records
    └── 000-template.md
```

---

## 📋 Status da Documentação

| Documento          | Status        | Última Atualização |
| ------------------ | ------------- | ------------------ |
| README.md          | ✅ Atualizado | Dez/2024           |
| ARCHITECTURE.md    | ✅ Atualizado | Dez/2024           |
| GETTING_STARTED.md | ✅ Atualizado | Dez/2024           |
| DEPLOY.md          | ✅ Atualizado | Dez/2024           |
| DESIGN_SYSTEM.md   | ✅ Atualizado | Dez/2024           |
| ROLES_E_ACESSO.md  | ✅ Atualizado | Dez/2024           |
| BOOK_OF_TESTS.md   | ✅ Novo       | Dez/2024           |
| TROUBLESHOOTING.md | ✅ Atualizado | Dez/2024           |
| CONTRIBUTING.md    | ✅ Atualizado | Dez/2024           |

---

## 🔗 Links Úteis

### Desenvolvimento

- **Dev Server:** http://localhost:13000
- **API:** http://localhost:8000
- **Keycloak:** http://localhost:8080
- **Storybook:** http://localhost:6006
- **API Docs:** http://localhost:8000/docs

### Repositório

- **GitHub:** [ClaudioRibeiro2023/Modelo](https://github.com/ClaudioRibeiro2023/Modelo)
- **Issues:** Abra uma issue para bugs ou sugestões
- **Pull Requests:** Siga o guia em CONTRIBUTING.md

---

## 📝 Como Manter a Documentação

### Ao Adicionar Funcionalidades

1. Atualize o documento relevante (ex: ARCHITECTURE.md para mudanças de arquitetura)
2. Adicione entrada no BOOK_OF_TESTS.md se criar novos testes
3. Atualize este INDEX.md se criar novos documentos

### Ao Tomar Decisões Arquiteturais

1. Crie um novo ADR em `docs/adr/` usando o template
2. Referencie o ADR no ARCHITECTURE.md

### Convenções

- Use **pt-BR** em toda a documentação
- Mantenha títulos consistentes (H1 para título principal, H2 para seções)
- Adicione data de última atualização em documentos importantes
- Use tabelas para informações estruturadas
- Inclua exemplos de código quando relevante

---

_Documentação gerada e mantida pela equipe de desenvolvimento._

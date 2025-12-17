# Plano de Ação - Documentação

> **Data:** 2024-12-16  
> **Status:** Pós-consolidação

---

## Ações Concluídas (Esta Sessão)

### Stubs de Compatibilidade Criados

| Arquivo Original             | Stub Criado | Aponta Para                          |
| ---------------------------- | ----------- | ------------------------------------ |
| docs/ARCHITECTURE.md         | ✅ Criado   | arquitetura/, adr_v2/, convencoes.md |
| docs/GETTING_STARTED.md      | ✅ Criado   | operacao/setup-local.md              |
| docs/DEPLOY.md               | ✅ Criado   | operacao/deploy.md                   |
| docs/ROLES_E_ACESSO.md       | ✅ Criado   | seguranca/rbac.md                    |
| docs/PROPOSTA_ARQUITETURA.md | ✅ Criado   | \_archive/2024-12-16/                |
| docs/VALIDATION_CHECKLIST.md | ✅ Criado   | \_report/validacao-final.md          |

### Estrutura Final Estabelecida

- [x] INDEX.md como portal canônico
- [x] Pastas temáticas organizadas (arquitetura/, contratos/, operacao/, seguranca/, adr_v2/)
- [x] \_archive/ para histórico
- [x] \_backlog/ para ideias futuras
- [x] 00-auditoria/ para relatórios oficiais

---

## Ações Pendentes

### P0 — Crítico (Fazer agora)

| #   | Ação                                | Responsável | Status      |
| --- | ----------------------------------- | ----------- | ----------- |
| 1   | Commit das mudanças de documentação | Dev         | ⏳ Pendente |
| 2   | Comunicar nova estrutura ao time    | Lead        | ⏳ Pendente |

### P1 — Alta Prioridade (Esta sprint)

| #   | Ação                                        | Responsável | Status      |
| --- | ------------------------------------------- | ----------- | ----------- |
| 1   | Revisar [TODO: confirmar] em docs           | Equipe      | ⏳ Pendente |
| 2   | Atualizar links no README.md raiz           | Dev         | ⏳ Pendente |
| 3   | Adicionar link para docs/ em READMEs locais | Dev         | ⏳ Pendente |

### P2 — Importante (Próximas 2 sprints)

| #   | Ação                                        | Responsável | Status      |
| --- | ------------------------------------------- | ----------- | ----------- |
| 1   | Criar pasta contratos-integracao/exemplos/  | Dev         | ⏳ Pendente |
| 2   | Adicionar exemplos de código para auth/api  | Dev         | ⏳ Pendente |
| 3   | Validar todos os comandos em setup-local.md | Dev         | ⏳ Pendente |

### P3 — Nice to Have (Backlog)

| #   | Ação                                       | Responsável | Status      |
| --- | ------------------------------------------ | ----------- | ----------- |
| 1   | Configurar CI para validar links markdown  | DevOps      | ⏳ Pendente |
| 2   | Avaliar TypeDoc para docs automáticos      | Dev         | ⏳ Pendente |
| 3   | Adicionar diagrama de sequência em auth.md | Dev         | ⏳ Pendente |

---

## Manutenção Contínua

### Ao Criar Novo Documento

1. Verificar se já existe doc similar (evitar duplicidade)
2. Colocar na pasta temática correta
3. Atualizar `docs/INDEX.md`
4. Seguir convenções pt-BR

### Ao Modificar Código

| Mudança                   | Atualizar                      |
| ------------------------- | ------------------------------ |
| Adicionar env var         | operacao/variaveis-ambiente.md |
| Modificar endpoint API    | contratos-integracao/api.md    |
| Mudar fluxo de auth       | contratos-integracao/auth.md   |
| Nova decisão arquitetural | Criar ADR em adr_v2/           |
| Comandos de setup         | README.md + setup-local.md     |

### Ao Arquivar Documento

1. Mover para `_archive/YYYY-MM-DD/`
2. Criar/atualizar `MOTIVO.md` na pasta
3. Criar stub no local original (se tinha inlinks)
4. Atualizar INDEX.md se necessário

---

## Próximos Passos Imediatos

```bash
# 1. Verificar mudanças
git status

# 2. Commit
git add docs/
git commit -m "docs: consolidar documentação e criar stubs de compatibilidade"

# 3. Push
git push origin master
```

---

_Plano atualizado em: 2024-12-16_

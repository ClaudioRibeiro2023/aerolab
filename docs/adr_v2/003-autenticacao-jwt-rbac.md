---
id: 'ADR-003'
title: 'Autenticação JWT + RBAC'
status: 'accepted'
date: '2024-12-16'
owners:
  - 'Equipe de Arquitetura'
tags:
  - 'segurança'
  - 'auth'
  - 'rbac'
  - 'oidc'
  - 'keycloak'
related:
  - 'ADR-001'
supersedes: null
superseded_by: null
---

# ADR-003: Autenticação JWT + RBAC

## 1. Contexto e Problema

O AeroLab requer um sistema de autenticação e autorização que atenda:

- **Segurança** - Proteção robusta contra ataques comuns
- **Escalabilidade** - Stateless para múltiplas instâncias
- **Integração** - Compatível com SSO corporativo
- **Granularidade** - Controle de acesso por funcionalidade
- **Auditoria** - Rastreabilidade de ações

> **Problema central:** Como implementar autenticação segura e escalável com controle de acesso granular?

## 2. Drivers de Decisão

- **DR1:** Segurança - Proteção contra ataques
- **DR2:** Escalabilidade - Suporte a múltiplas instâncias
- **DR3:** Integração - SSO e IdPs externos
- **DR4:** Developer Experience - Facilidade de uso

Priorização: DR1 > DR2 > DR3 > DR4

## 3. Decisão

> **Decidimos:** Implementar autenticação via OIDC com Keycloak, usando JWT para autorização stateless e RBAC para controle de acesso.

### Especificações

| Item           | Valor                     | Arquivo de Referência                    |
| -------------- | ------------------------- | ---------------------------------------- |
| Protocolo      | OIDC 1.0                  | -                                        |
| Fluxo          | Authorization Code + PKCE | `packages/shared/src/auth/oidcConfig.ts` |
| Token          | JWT RS256                 | -                                        |
| IdP            | Keycloak 23+              | `infra/docker-compose.yml`               |
| Client Library | oidc-client-ts 2.4+       | `packages/shared/package.json`           |

### Roles Implementadas

**Fonte:** `packages/shared/src/auth/types.ts:2`

```typescript
export type UserRole = 'ADMIN' | 'GESTOR' | 'OPERADOR' | 'VIEWER'
```

| Role       | Descrição                     |
| ---------- | ----------------------------- |
| `ADMIN`    | Administrador - acesso total  |
| `GESTOR`   | Gestor - CRUD em módulos      |
| `OPERADOR` | Operador - operações diárias  |
| `VIEWER`   | Visualizador - apenas leitura |

### Fluxo de Autenticação

```
1. Usuário acessa aplicação
2. Frontend redireciona para Keycloak (PKCE)
3. Usuário autentica no Keycloak
4. Keycloak retorna authorization code
5. Frontend troca code por tokens
6. Requisições incluem JWT no header Authorization
7. Backend valida JWT via JWKS
```

### Escopo

- **Afeta:** Frontend (auth flow), Backend (validação), Infraestrutura (Keycloak)
- **Não afeta:** Lógica de negócio específica de módulos

## 4. Alternativas Consideradas

### Alternativa A: Session-based Auth

| Aspecto | Avaliação                                           |
| ------- | --------------------------------------------------- |
| Prós    | Revogação instantânea, menor superfície XSS         |
| Contras | Stateful, requer Redis compartilhado, CORS complexo |
| Esforço | Alto                                                |
| Risco   | Médio                                               |

**Por que descartada:** Complexidade de escalabilidade horizontal.

### Alternativa B: Auth0/Okta (SaaS)

| Aspecto | Avaliação                                                 |
| ------- | --------------------------------------------------------- |
| Prós    | Zero manutenção, features avançadas                       |
| Contras | Custo por usuário, vendor lock-in, dados em cloud externa |
| Esforço | Baixo                                                     |
| Risco   | Médio (dependência externa)                               |

**Por que descartada:** Requisitos de compliance podem impedir uso de SaaS externo.

### Alternativa C: JWT em localStorage

| Aspecto | Avaliação                            |
| ------- | ------------------------------------ |
| Prós    | Simples, persiste entre abas         |
| Contras | Vulnerável a XSS, OWASP desrecomenda |
| Esforço | Baixo                                |
| Risco   | Alto                                 |

**Por que descartada:** Risco de segurança inaceitável.

## 5. Consequências e Trade-offs

### Positivas

- ✅ Stateless - Escala horizontalmente sem estado compartilhado
- ✅ Padrão aberto - OIDC é amplamente documentado
- ✅ SSO ready - Integração com IdPs corporativos
- ✅ Self-hosted - Sem dependência de SaaS

### Negativas

- ⚠️ Complexidade do OIDC
- ⚠️ Manutenção do Keycloak
- ⚠️ Revogação não instantânea (depende de TTL)

### Riscos Identificados

| Risco                         | Probabilidade | Impacto | Mitigação                |
| ----------------------------- | ------------- | ------- | ------------------------ |
| Token theft via XSS           | Baixa         | Alto    | CSP, tokens em memória   |
| Keycloak indisponível         | Baixa         | Alto    | HA, graceful degradation |
| JWT expirado durante operação | Média         | Baixo   | Silent refresh           |

## 6. Impacto em Integrações e Contratos

### Breaking Changes

- [x] Não (decisão fundacional)

### Contratos para Integradores

#### Obter Token (Client Credentials)

```bash
curl -X POST \
  "http://localhost:8080/realms/template/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=<client_id>" \
  -d "client_secret=<client_secret>"
```

#### Usar Token na API

```bash
curl -X GET "http://localhost:8000/api/resource" \
  -H "Authorization: Bearer <access_token>"
```

#### Validar Token (JWKS)

```
GET http://localhost:8080/realms/template/protocol/openid-connect/certs
```

### Claims Obrigatórias no JWT

| Claim                | Tipo     | Descrição           |
| -------------------- | -------- | ------------------- |
| `sub`                | string   | ID único do usuário |
| `email`              | string   | E-mail              |
| `realm_access.roles` | string[] | Roles do usuário    |

### Documentação Completa

Ver: [Contrato de Autenticação](../contratos-integracao/auth.md)

## 7. Plano de Rollout/Migração

### Status

✅ **Implementado** - Sistema em uso.

### Configurações de Segurança Recomendadas

**Keycloak:**

```yaml
accessTokenLifespan: 5m
ssoSessionIdleTimeout: 30m
ssoSessionMaxLifespan: 8h
bruteForceProtected: true
failureFactor: 5
```

### Evolução Futura

1. **MFA** - Adicionar autenticação multi-fator
2. **Passwordless** - WebAuthn/passkeys
3. **Fine-grained permissions** - Além de roles, permissões por recurso

## 8. Referências

### Internas

- [Contrato de Auth](../contratos-integracao/auth.md)
- [RBAC](../seguranca/rbac.md)
- [Headers de Segurança](../seguranca/headers-seguranca.md)

### Externas

- [OIDC Core Spec](https://openid.net/specs/openid-connect-core-1_0.html)
- [PKCE RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OWASP Auth Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## Histórico

| Data       | Autor                 | Mudança                                            |
| ---------- | --------------------- | -------------------------------------------------- |
| 2024-12-16 | Equipe de Arquitetura | Criação                                            |
| 2024-12-16 | Cascade               | Migração para ADR v2, adicionar seção de contratos |

---

_Migrado de `/docs/adr/003-autenticacao-jwt-rbac.md`_

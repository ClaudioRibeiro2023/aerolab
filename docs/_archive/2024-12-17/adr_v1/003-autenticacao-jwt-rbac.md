# ADR-003: Autenticação JWT + RBAC

**Data:** 2025-12-10
**Status:** Aceito

## Contexto

A plataforma precisa de:

- Autenticação stateless para APIs
- Controle de acesso baseado em papéis (RBAC)
- Suporte a múltiplos usuários/organizações
- Auditoria de ações sensíveis

## Decisão

Implementamos autenticação JWT com RBAC em dois níveis:

### JWT (JSON Web Tokens)

```python
# Estrutura do token
{
    "sub": "user@example.com",      # Subject (email)
    "role": "admin",                 # Papel do usuário
    "exp": 1702234567,               # Expiração
    "iat": 1702148167                # Emissão
}
```

Configuração via variáveis de ambiente:

- `JWT_SECRET` - Secret para assinatura (obrigatório)
- `JWT_ALGORITHM` - Algoritmo (default: HS256)
- `JWT_EXPIRATION_HOURS` - Expiração (default: 24h)

### RBAC (Role-Based Access Control)

Dois papéis principais:

| Papel | Permissões |
|-------|------------|
| `admin` | CRUD completo em todos os recursos |
| `user` | Leitura e execução, sem criar/deletar |

Endpoints protegidos:

```python
# Exemplo de proteção
@router.post("/agents")
async def create_agent(
    user: User = Depends(require_admin)  # Requer admin
):
    ...

@router.get("/agents")
async def list_agents(
    user: User = Depends(get_current_user)  # Qualquer usuário autenticado
):
    ...
```

### Rate Limiting

Proteção adicional por tipo de endpoint:

- Auth: 5 requests/10s
- RAG Query: 3 requests/10s
- RAG Ingest: 2 requests/10s
- Default: 10 requests/10s

## Consequências

### Positivas

- Stateless: fácil de escalar horizontalmente
- Tokens auto-contidos: não precisa consultar DB a cada request
- RBAC simples e efetivo para o tamanho atual
- Rate limiting previne abuso

### Negativas

- Tokens não podem ser invalidados antes da expiração
- Sem refresh tokens (requer novo login após expiração)
- RBAC simples pode ser limitante para casos complexos

### Neutras

- Requer HTTPS em produção para segurança dos tokens

## Alternativas Consideradas

### Session-based Authentication

- **Prós:** Revogação imediata, familiar
- **Contras:** Stateful, requer storage de sessão
- **Por que não:** JWT é mais adequado para APIs

### OAuth2 / OpenID Connect

- **Prós:** Standard, suporte a SSO
- **Contras:** Complexidade adicional
- **Por que não:** Overkill para uso atual (pode ser adicionado depois)

### API Keys

- **Prós:** Simples de implementar
- **Contras:** Sem identidade de usuário, difícil de rotacionar
- **Por que não:** JWT oferece mais informações e segurança

## Referências

- [JWT.io](https://jwt.io/)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

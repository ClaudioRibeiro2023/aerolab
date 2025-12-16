# ADR-003: Autenticação JWT + RBAC

## Status

**ACEITO**

Data: 2024-12-16

Autores: Equipe de Arquitetura

## Contexto

O Template Platform requer um sistema de autenticação e autorização que atenda:

- **Segurança** - Proteção robusta contra ataques comuns (CSRF, XSS, token theft)
- **Escalabilidade** - Stateless para permitir múltiplas instâncias
- **Integração** - Compatível com SSO corporativo e IdPs externos
- **Granularidade** - Controle de acesso por funcionalidade/recurso
- **Auditoria** - Rastreabilidade de ações por usuário
- **UX** - Login único, sessões duradouras com refresh transparente

### Restrições

- Deve suportar ambientes on-premise e cloud
- Deve permitir modo demo/desenvolvimento sem IdP
- Deve ser compatível com LGPD (consentimento, auditoria)
- Latência de validação < 50ms

## Decisão

Decidimos implementar autenticação via **OpenID Connect (OIDC)** com **Keycloak** como Identity Provider, utilizando **JWT (JSON Web Tokens)** para autorização stateless e **RBAC (Role-Based Access Control)** para controle de acesso.

### Arquitetura de Autenticação

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Frontend   │────▶│   Keycloak  │
│             │◀────│   (React)   │◀────│    (IdP)    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           │ JWT (Authorization: Bearer)
                           ▼
                    ┌─────────────┐
                    │   Backend   │
                    │  (FastAPI)  │
                    └─────────────┘
```

### Fluxo de Autenticação (Authorization Code + PKCE)

```
1. Usuário acessa aplicação
2. Frontend redireciona para Keycloak /auth
3. Usuário faz login no Keycloak
4. Keycloak redireciona de volta com authorization code
5. Frontend troca code por tokens (via PKCE)
6. Frontend armazena tokens em memória
7. Requisições à API incluem Access Token no header
8. Backend valida JWT e extrai claims (roles, permissions)
```

### Estrutura do JWT

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id"
  },
  "payload": {
    "iss": "https://keycloak.example.com/realms/template",
    "sub": "user-uuid",
    "aud": "template-platform",
    "exp": 1702756800,
    "iat": 1702753200,
    "auth_time": 1702753200,
    "preferred_username": "usuario@email.com",
    "email": "usuario@email.com",
    "name": "Nome Completo",
    "realm_access": {
      "roles": ["ADMIN", "GESTOR"]
    },
    "resource_access": {
      "template-platform": {
        "roles": ["etl-read", "users-write"]
      }
    }
  }
}
```

### Sistema de Roles (RBAC)

| Role         | Descrição                | Permissões                                            |
| ------------ | ------------------------ | ----------------------------------------------------- |
| **ADMIN**    | Administrador do sistema | Todas as operações, configurações, gestão de usuários |
| **GESTOR**   | Gestor de área/módulo    | CRUD em módulos permitidos, relatórios, aprovações    |
| **OPERADOR** | Usuário operacional      | Operações do dia-a-dia, visualização de dados         |
| **VIEWER**   | Visualizador             | Apenas leitura, dashboards, relatórios                |

### Hierarquia de Permissões

```
ADMIN
  └── GESTOR
       └── OPERADOR
            └── VIEWER
```

Roles superiores herdam permissões das inferiores.

### Implementação Frontend

```typescript
// packages/shared/src/auth/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: Role) => boolean;
  hasAnyRole: (roles: Role[]) => boolean;
  hasAllRoles: (roles: Role[]) => boolean;
}

// Uso em componentes
const { hasRole } = useAuth();

if (hasRole('ADMIN')) {
  // Renderiza opções de admin
}

// Proteção de rotas
<ProtectedRoute requiredRoles={['ADMIN', 'GESTOR']}>
  <ConfigPage />
</ProtectedRoute>
```

### Implementação Backend

```python
# api-template/app/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

async def get_current_user(token: str = Depends(HTTPBearer())):
    """Valida JWT e retorna usuário."""
    payload = verify_jwt(token)
    return User(**payload)

def require_roles(*roles: str):
    """Decorator para exigir roles específicas."""
    async def validator(user: User = Depends(get_current_user)):
        if not any(role in user.roles for role in roles):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return validator

# Uso em endpoints
@router.get("/admin/config")
async def get_config(user: User = Depends(require_roles("ADMIN"))):
    return {"config": "..."}
```

### Modo Demo/Desenvolvimento

Para facilitar desenvolvimento e demonstrações, implementamos um **Demo Mode**:

```typescript
// Ativado via VITE_AUTH_DEMO_MODE=true
const DEMO_USER: User = {
  id: 'demo-user',
  name: 'Usuário Demo',
  email: 'demo@template.local',
  roles: ['ADMIN', 'GESTOR', 'OPERADOR', 'VIEWER'],
}
```

## Alternativas Consideradas

### Alternativa 1: Session-based Authentication

**Descrição:** Sessões armazenadas no servidor com cookie httpOnly.

**Prós:**

- Revogação instantânea de sessão
- Sem exposição de tokens ao JavaScript
- Menor superfície de ataque XSS

**Contras:**

- Stateful - requer storage compartilhado (Redis)
- Escalabilidade horizontal mais complexa
- CORS e cookies cross-origin problemáticos
- Não adequado para SPAs modernas

### Alternativa 2: OAuth2 sem OIDC

**Descrição:** Apenas OAuth2 para autorização, sem camada de identidade.

**Prós:**

- Mais simples de implementar
- Amplamente suportado

**Contras:**

- Não padroniza claims de identidade
- Cada IdP implementa user info diferente
- Menos interoperabilidade

### Alternativa 3: Auth0/Okta (SaaS)

**Descrição:** Identity Provider como serviço gerenciado.

**Prós:**

- Zero manutenção de infraestrutura
- Features avançadas (MFA, passwordless)
- Compliance certifications

**Contras:**

- Custo por usuário ativo
- Vendor lock-in
- Dados em cloud externa
- Requisitos de compliance podem impedir uso

### Alternativa 4: JWT armazenado em localStorage

**Descrição:** Tokens persistidos em localStorage do browser.

**Prós:**

- Persiste entre abas
- Simples de implementar

**Contras:**

- Vulnerável a XSS (JavaScript pode ler)
- OWASP desrecomenda fortemente
- Não há como "expirar" do servidor

**Decisão:** Tokens são mantidos apenas em memória (variável JavaScript). Refresh tokens são armazenados em httpOnly cookies quando possível.

## Consequências

### Positivas

- **Stateless** - Backend não mantém estado de sessão, escala horizontalmente
- **Padrão aberto** - OIDC é amplamente adotado e documentado
- **SSO ready** - Integração com IdPs corporativos facilitada
- **Auditável** - Cada ação tem user ID no token
- **Flexível** - Keycloak permite customização extensiva
- **Self-hosted** - Sem dependência de SaaS externo

### Negativas

- **Complexidade** - OIDC tem curva de aprendizado
- **Infraestrutura** - Keycloak requer manutenção
- **Token size** - JWTs podem ser grandes com muitas claims
- **Revogação** - Não instantânea (depende do TTL do token)

### Riscos

| Risco                         | Probabilidade | Impacto | Mitigação                                      |
| ----------------------------- | ------------- | ------- | ---------------------------------------------- |
| Token theft via XSS           | Baixa         | Alto    | CSP restritiva, sanitização, tokens em memória |
| Keycloak indisponível         | Baixa         | Alto    | Alta disponibilidade, graceful degradation     |
| JWT expirado durante operação | Média         | Baixo   | Silent refresh, retry com novo token           |
| Brute force em login          | Média         | Médio   | Rate limiting, account lockout, MFA            |

## Configuração de Segurança

### Headers de Segurança (Backend)

```python
# Content Security Policy
CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",
    "img-src": "'self' data: https:",
    "connect-src": "'self' https://keycloak.example.com"
}

# Outros headers
X_CONTENT_TYPE_OPTIONS = "nosniff"
X_FRAME_OPTIONS = "DENY"
STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"
```

### Configuração Keycloak

```yaml
# Realm settings recomendados
realm: template
accessTokenLifespan: 5m # Access token curto
ssoSessionIdleTimeout: 30m # Sessão idle
ssoSessionMaxLifespan: 8h # Sessão máxima
refreshTokenMaxReuse: 0 # Refresh token single-use
bruteForceProtected: true
failureFactor: 5 # Lockout após 5 falhas
```

## Métricas de Sucesso

- **Tempo de login** < 2s (incluindo redirect)
- **Taxa de refresh silencioso** > 99%
- **Incidentes de segurança** = 0
- **Uptime Keycloak** > 99.9%
- **Latência de validação JWT** < 10ms

## Referências

- [OpenID Connect Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP JWT Security](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

_Última revisão: Dezembro 2024_

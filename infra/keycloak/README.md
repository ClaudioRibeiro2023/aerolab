# Keycloak Setup

Este diretório contém scripts para configurar o Keycloak para autenticação.

## Pré-requisitos

- Python 3.8+
- `pip install requests`

## Scripts

### seed-keycloak.py

Cria automaticamente:

- Realm `template`
- Client `template-web` (público, com PKCE)
- Roles: ADMIN, GESTOR, OPERADOR, VIEWER
- Usuário admin de teste

```bash
# Instalar dependência
pip install requests

# Executar (Keycloak deve estar rodando)
python seed-keycloak.py

# Ou com URL customizada
python seed-keycloak.py --keycloak-url http://localhost:8080
```

## Configuração Manual

Se preferir configurar manualmente:

### 1. Criar Realm

1. Acesse http://localhost:8080/admin
2. Login com `admin/admin`
3. Clique em "Create Realm"
4. Nome: `template`

### 2. Criar Client

1. Clients → Create client
2. Client ID: `template-web`
3. Client Protocol: `openid-connect`
4. Access Type: `public`
5. Valid Redirect URIs: `http://localhost:13000/*`
6. Web Origins: `http://localhost:13000`

### 3. Criar Roles

1. Realm roles → Create role
2. Criar: ADMIN, GESTOR, OPERADOR, VIEWER

### 4. Criar Usuário de Teste

1. Users → Add user
2. Email: `admin@template.com`
3. Email Verified: ON
4. Credentials → Set Password: `admin123`
5. Role Mappings → Assign all roles

## Variáveis de Ambiente

Configure no frontend:

```env
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=template
VITE_KEYCLOAK_CLIENT_ID=template-web
```

## Produção

Para produção, altere:

1. `sslRequired: "external"` no realm
2. Remova `http://localhost` dos redirect URIs
3. Use senhas seguras
4. Configure HTTPS

# Guia de Deploy

Este documento descreve como fazer deploy da Template Platform em diferentes ambientes.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Deploy Local (Docker)](#deploy-local-docker)
- [Deploy em Staging](#deploy-em-staging)
- [Deploy em Produção](#deploy-em-produção)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- Docker 24+ e Docker Compose 2.20+
- Node.js 20+ e pnpm 9+
- Acesso ao registry de containers (GitHub Container Registry)
- Credenciais de acesso aos serviços externos (Keycloak, PostgreSQL, Redis)

---

## Deploy Local (Docker)

### 1. Configurar variáveis de ambiente

```bash
cd infra
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 2. Iniciar os serviços

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 3. Acessar a aplicação

- **Frontend:** http://localhost:13000
- **API:** http://localhost:8000
- **Keycloak:** http://localhost:8080
- **API Docs:** http://localhost:8000/docs

### 4. Parar os serviços

```bash
docker-compose down

# Remover volumes (dados)
docker-compose down -v
```

---

## Deploy em Staging

### Via GitHub Actions

1. Faça push para a branch `develop`
2. O workflow de CI será executado automaticamente
3. Após passar nos testes, as imagens serão buildadas
4. Deploy manual via workflow dispatch ou auto-deploy configurado

### Manualmente

```bash
# Build das imagens
docker build -t ghcr.io/seu-org/template-web:staging -f apps/web/Dockerfile .
docker build -t ghcr.io/seu-org/template-api:staging -f api-template/Dockerfile --target production ./api-template

# Push para o registry
docker push ghcr.io/seu-org/template-web:staging
docker push ghcr.io/seu-org/template-api:staging
```

---

## Deploy em Produção

### Via GitHub Actions (Recomendado)

1. Crie uma tag de release:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. O workflow de Docker será executado automaticamente
3. As imagens serão taggeadas com a versão semântica
4. Deploy via CD configurado no seu provedor de cloud

### Checklist de Produção

- [ ] Variáveis de ambiente configuradas
- [ ] SSL/TLS habilitado
- [ ] Rate limiting configurado
- [ ] Logs centralizados
- [ ] Monitoramento ativo
- [ ] Backup de banco configurado
- [ ] Health checks funcionando
- [ ] Rollback testado

---

## Variáveis de Ambiente

### Frontend (Web)

| Variável                  | Descrição               | Exemplo                    |
| ------------------------- | ----------------------- | -------------------------- |
| `VITE_API_URL`            | URL base da API         | `https://api.exemplo.com`  |
| `VITE_KEYCLOAK_URL`       | URL do Keycloak         | `https://auth.exemplo.com` |
| `VITE_KEYCLOAK_REALM`     | Realm do Keycloak       | `template`                 |
| `VITE_KEYCLOAK_CLIENT_ID` | Client ID               | `template-web`             |
| `VITE_DEMO_MODE`          | Modo demo (bypass auth) | `false`                    |

### Backend (API)

| Variável         | Descrição                 | Exemplo                               |
| ---------------- | ------------------------- | ------------------------------------- |
| `DATABASE_URL`   | URL de conexão PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL`      | URL de conexão Redis      | `redis://host:6379`                   |
| `SECRET_KEY`     | Chave secreta para JWT    | `sua-chave-secreta-aqui`              |
| `KEYCLOAK_URL`   | URL do Keycloak           | `https://auth.exemplo.com`            |
| `KEYCLOAK_REALM` | Realm do Keycloak         | `template`                            |
| `LOG_LEVEL`      | Nível de log              | `info`                                |
| `CORS_ORIGINS`   | Origens permitidas        | `https://app.exemplo.com`             |

### Infraestrutura

| Variável                  | Descrição             | Default       |
| ------------------------- | --------------------- | ------------- |
| `POSTGRES_USER`           | Usuário do PostgreSQL | `template`    |
| `POSTGRES_PASSWORD`       | Senha do PostgreSQL   | -             |
| `POSTGRES_DB`             | Nome do banco         | `template_db` |
| `REDIS_PASSWORD`          | Senha do Redis        | -             |
| `KEYCLOAK_ADMIN`          | Admin do Keycloak     | `admin`       |
| `KEYCLOAK_ADMIN_PASSWORD` | Senha admin Keycloak  | -             |

---

## Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs <service-name>

# Verificar configuração
docker-compose config

# Recriar container
docker-compose up -d --force-recreate <service-name>
```

### Problemas de conexão com banco

1. Verifique se o PostgreSQL está rodando:

   ```bash
   docker-compose ps postgres
   ```

2. Teste a conexão:
   ```bash
   docker-compose exec postgres psql -U template -d template_db
   ```

### Problemas com Keycloak

1. Verifique os logs:

   ```bash
   docker-compose logs keycloak
   ```

2. Acesse o admin console: http://localhost:8080/admin

3. Verifique se o realm e client estão configurados

### API retornando 500

1. Verifique os logs da API:

   ```bash
   docker-compose logs api
   ```

2. Verifique variáveis de ambiente:

   ```bash
   docker-compose exec api env
   ```

3. Teste o health check:
   ```bash
   curl http://localhost:8000/health
   ```

---

## Contato

Em caso de problemas, abra uma issue no repositório ou entre em contato com a equipe de DevOps.

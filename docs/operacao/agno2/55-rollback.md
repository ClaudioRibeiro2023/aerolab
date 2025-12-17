# Guia de Rollback – Agno Multi-Agent Platform

Este documento descreve como reverter deployments em caso de problemas.

---

## Índice

- [Railway (Backend)](#railway-backend)
- [Netlify (Frontend)](#netlify-frontend)
- [Rollback Completo](#rollback-completo)
- [Verificação Pós-Rollback](#verificação-pós-rollback)

---

## Railway (Backend)

### Via Dashboard

1. Acesse [railway.app](https://railway.app)
2. Navegue até o projeto Agno
3. Clique no serviço `backend`
4. Vá em **Deployments**
5. Encontre o deployment anterior estável
6. Clique nos **3 pontos** → **Redeploy**

### Via CLI

```bash
# Listar deployments recentes
railway deployments list

# Fazer rollback para um deployment específico
railway rollback <deployment-id>

# Ou reverter para o último commit estável
git revert HEAD
git push origin main
```

### Rollback de Variáveis de Ambiente

Se o problema for em variáveis de ambiente:

```bash
# Listar variáveis atuais
railway variables

# Reverter uma variável específica
railway variables set VARIAVEL=valor_anterior
```

---

## Netlify (Frontend)

### Via Dashboard

1. Acesse [app.netlify.com](https://app.netlify.com)
2. Selecione o site `agno-multi-agent`
3. Vá em **Deploys**
4. Encontre o deploy anterior estável (badge verde)
5. Clique no deploy → **Publish deploy**

### Via CLI

```bash
# Instalar Netlify CLI se necessário
npm install -g netlify-cli

# Listar deploys recentes
netlify deploy:list

# Fazer rollback para um deploy específico
netlify deploy:rollback <deploy-id>
```

### Rollback Instantâneo

Netlify mantém todos os deploys. Para rollback instantâneo:

1. Dashboard → Deploys → Deploy anterior
2. Clique **Publish deploy**
3. O site volta ao ar em ~10 segundos

---

## Rollback Completo

Para reverter backend E frontend simultaneamente:

### 1. Identificar a versão estável

```bash
# Ver tags de release
git tag -l "v*" --sort=-version:refname | head -5

# Ver commits recentes
git log --oneline -10
```

### 2. Criar branch de hotfix

```bash
git checkout -b hotfix/rollback-to-v1.2.3
git reset --hard v1.2.3  # ou commit específico
git push origin hotfix/rollback-to-v1.2.3 --force
```

### 3. Fazer merge em main

```bash
git checkout main
git merge hotfix/rollback-to-v1.2.3
git push origin main
```

### 4. Disparar redeploy manual (se necessário)

```bash
# Railway
railway up --service backend

# Netlify
netlify deploy --prod
```

---

## Verificação Pós-Rollback

Após qualquer rollback, verifique:

### Backend

```bash
# Health check
curl https://api.agno.app/health

# Verificar versão
curl https://api.agno.app/api/status

# Testar endpoint crítico
curl https://api.agno.app/api/agents
```

### Frontend

```bash
# Verificar se o site carrega
curl -I https://agno-multi-agent.netlify.app

# Verificar se API está acessível do frontend
# (abrir DevTools → Network → verificar chamadas)
```

### Checklist de Verificação

- [ ] Health check backend retorna 200
- [ ] Frontend carrega sem erros de console
- [ ] Login/autenticação funciona
- [ ] Criação de agentes funciona
- [ ] Flow Studio abre corretamente
- [ ] Sem erros novos no Sentry

---

## Contatos de Emergência

| Serviço | Status Page | Suporte |
|---------|-------------|---------|
| Railway | [status.railway.app](https://status.railway.app) | Discord |
| Netlify | [netlifystatus.com](https://www.netlifystatus.com) | Support ticket |

---

## Prevenção

Para evitar a necessidade de rollbacks:

1. **Sempre testar em staging** antes de produção
2. **Deploy gradual**: main → staging → production
3. **Feature flags** para funcionalidades arriscadas
4. **Monitoramento ativo** com Sentry/PostHog

---

*Última atualização: 2025-12-09*

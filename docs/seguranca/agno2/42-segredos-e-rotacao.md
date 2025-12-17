# Segredos e Rotação

> Gerenciamento de secrets e chaves de API.

---

## Tipos de Secrets

| Secret | Uso | Rotação |
|--------|-----|---------|
| `JWT_SECRET` | Assinatura de tokens | Anual ou sob demanda |
| `GROQ_API_KEY` | API Groq | Sob demanda |
| `OPENAI_API_KEY` | API OpenAI | Sob demanda |
| `ANTHROPIC_API_KEY` | API Anthropic | Sob demanda |
| `DATABASE_URL` | Conexão DB | Sob demanda |

---

## Armazenamento

### Desenvolvimento

```bash
# .env (NÃO commitar)
JWT_SECRET=dev-secret-change-in-production
GROQ_API_KEY=gsk_...
```

### Produção (Railway)

Secrets configurados no dashboard:

1. Acesse Railway → Project → Variables
2. Adicione cada secret
3. Secrets são injetados como env vars

### Produção (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
env:
  JWT_SECRET: ${{ secrets.JWT_SECRET }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```

---

## Rotação de Secrets

### JWT_SECRET

**Impacto:** Todos os tokens existentes são invalidados.

**Processo:**
1. Gere novo secret: `openssl rand -hex 32`
2. Atualize no ambiente de produção
3. Reinicie o servidor
4. Usuários precisam fazer login novamente

### API Keys (LLM Providers)

**Impacto:** Mínimo se feito corretamente.

**Processo:**
1. Gere nova key no provider
2. Atualize no ambiente
3. Teste funcionamento
4. Revogue key antiga no provider

---

## Boas Práticas

### DO

- ✅ Use secrets manager em produção
- ✅ Diferentes secrets por ambiente
- ✅ Rotação periódica
- ✅ Audit log de acesso a secrets
- ✅ Princípio do menor privilégio

### DON'T

- ❌ Secrets em código
- ❌ Secrets em logs
- ❌ Compartilhar secrets entre ambientes
- ❌ Secrets em URLs
- ❌ Commitar .env

---

## Verificação

### Verificar Vazamentos

```bash
# Buscar secrets no código
grep -r "sk-" --include="*.py" .
grep -r "gsk_" --include="*.py" .
grep -r "secret" --include="*.py" . | grep -v "JWT_SECRET"
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
```

---

## Referências

- [12 Factor App - Config](https://12factor.net/config)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)

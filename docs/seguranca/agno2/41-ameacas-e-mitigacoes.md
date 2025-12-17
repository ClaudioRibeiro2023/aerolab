# Ameaças e Mitigações

> Modelo de ameaças e controles de segurança da plataforma.

---

## Ameaças Identificadas

### 1. Injection de Prompt

**Descrição:** Usuário manipula input para fazer o agente executar ações não autorizadas.

**Mitigação:**
- Validação de inputs
- Sanitização de prompts
- Limites de contexto
- Monitoramento de outputs

### 2. Vazamento de Dados via RAG

**Descrição:** Documentos sensíveis são expostos via queries RAG.

**Mitigação:**
- Isolamento de collections por tenant
- Filtragem de metadados sensíveis
- Audit logs de queries
- Rate limiting

### 3. Token JWT Comprometido

**Descrição:** Token roubado usado para acesso não autorizado.

**Mitigação:**
- Expiração curta (24h)
- HTTPS obrigatório em produção
- Não armazenar em localStorage
- Monitoramento de uso anômalo

### 4. API Abuse / DDoS

**Descrição:** Excesso de requisições para sobrecarregar o sistema.

**Mitigação:**
- Rate limiting por IP/usuário
- Limites diferenciados por endpoint
- WAF em produção
- Auto-scaling

### 5. Code Execution Escape

**Descrição:** Código malicioso escapa do sandbox de execução.

**Mitigação:**
- Sandbox isolado (Docker)
- Timeout de execução
- Whitelist de operações
- Sem acesso a rede/filesystem

---

## Controles Implementados

### Rate Limiting

```python
# src/middleware/rate_limit.py
RATE_LIMITS = {
    "default": {"requests": 10, "window": 10},
    "auth": {"requests": 5, "window": 10},
    "rag_query": {"requests": 3, "window": 10},
    "rag_ingest": {"requests": 2, "window": 10},
}
```

### Validação de Input

```python
# Pydantic models para validação
from pydantic import BaseModel, validator

class AgentCreate(BaseModel):
    name: str
    model: str

    @validator('name')
    def validate_name(cls, v):
        if not v.isalnum():
            raise ValueError('Name must be alphanumeric')
        return v
```

### Headers de Segurança

```python
# Aplicados automaticamente
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
```

### Logging de Segurança

```python
# Eventos de segurança logados
logger.warning(f"auth_failure user={email} ip={ip}")
logger.warning(f"rate_limit_exceeded user={user} endpoint={path}")
logger.info(f"admin_action user={user} action={action}")
```

---

## Checklist de Segurança

### Desenvolvimento

- [ ] Secrets nunca em código
- [ ] Inputs validados com Pydantic
- [ ] SQL parametrizado (SQLAlchemy)
- [ ] CORS configurado corretamente

### Deploy

- [ ] HTTPS habilitado
- [ ] JWT_SECRET forte e único
- [ ] Variáveis sensíveis como secrets
- [ ] Logs não expõem dados sensíveis

### Operação

- [ ] Monitoramento de erros 401/403
- [ ] Alertas de rate limit
- [ ] Backup de dados criptografado
- [ ] Rotação periódica de secrets

---

## Referências

- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP API Security](https://owasp.org/API-Security/)

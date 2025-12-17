# Runbooks

> Procedimentos para incidentes comuns.

---

## Índice

1. [Backend não responde](#1-backend-não-responde)
2. [Erro de autenticação em massa](#2-erro-de-autenticação-em-massa)
3. [Rate limiting excessivo](#3-rate-limiting-excessivo)
4. [ChromaDB indisponível](#4-chromadb-indisponível)
5. [LLM Provider com erro](#5-llm-provider-com-erro)
6. [Disk full](#6-disk-full)

---

## 1. Backend não responde

### Sintomas
- `/health` retorna timeout ou erro
- Frontend mostra "Connection refused"

### Diagnóstico

```bash
# Verificar se processo está rodando
ps aux | grep uvicorn

# Verificar logs
railway logs  # ou docker logs

# Verificar porta
netstat -an | grep 8000
```

### Resolução

```bash
# Reiniciar serviço
railway redeploy

# Ou local
pkill -f uvicorn
python server.py
```

### Prevenção
- Configurar health checks
- Auto-restart no Railway/Docker

---

## 2. Erro de autenticação em massa

### Sintomas
- Múltiplos 401 Unauthorized
- Usuários não conseguem logar

### Diagnóstico

```bash
# Verificar logs de auth
grep "auth_failure" logs.json

# Verificar JWT_SECRET
echo $JWT_SECRET  # deve estar definido
```

### Resolução

**Se JWT_SECRET foi alterado:**
- Todos os tokens existentes são inválidos
- Usuários precisam fazer login novamente

**Se JWT_SECRET não está definido:**
```bash
# Adicionar ao ambiente
export JWT_SECRET=$(openssl rand -hex 32)
railway variables set JWT_SECRET=$JWT_SECRET
railway redeploy
```

### Prevenção
- Não alterar JWT_SECRET sem aviso
- Monitorar auth failures

---

## 3. Rate limiting excessivo

### Sintomas
- Muitos 429 Too Many Requests
- Usuários legítimos bloqueados

### Diagnóstico

```bash
# Verificar métricas de rate limit
curl localhost:8000/metrics | grep rate_limit

# Verificar IPs com mais hits
grep "rate_limit" logs.json | jq '.ip' | sort | uniq -c
```

### Resolução

**Ajustar limites (temporário):**
```python
# src/middleware/rate_limit.py
RATE_LIMITS = {
    "default": {"requests": 20, "window": 10},  # dobrar
}
```

**Bloquear IP abusivo:**
```python
BLOCKED_IPS = ["1.2.3.4"]
```

### Prevenção
- Limites diferenciados por usuário autenticado
- WAF para proteção adicional

---

## 4. ChromaDB indisponível

### Sintomas
- Queries RAG falham
- Erro "Connection refused" para ChromaDB

### Diagnóstico

```bash
# Verificar se ChromaDB está rodando
docker ps | grep chroma

# Testar conexão
curl http://localhost:8000/rag/collections
```

### Resolução

**ChromaDB local:**
```bash
# Reiniciar container
docker restart chromadb

# Ou iniciar novo
docker run -d -p 8000:8000 chromadb/chroma
```

**ChromaDB em modo arquivo:**
```bash
# Verificar path
ls -la data/chroma/

# Se corrompido, restaurar backup
cp -r data/backups/chroma_latest data/chroma
```

### Prevenção
- Backups regulares do diretório ChromaDB
- Monitorar health do ChromaDB

---

## 5. LLM Provider com erro

### Sintomas
- Agentes não respondem
- Erro "API Error" ou "Rate limit" do provider

### Diagnóstico

```bash
# Verificar status do provider
curl -I https://api.groq.com/health
curl -I https://api.openai.com/v1/models

# Verificar API key
echo $GROQ_API_KEY | head -c 10
```

### Resolução

**Se rate limit do provider:**
- Aguardar reset (geralmente 1 minuto)
- Considerar upgrade de plano

**Se API key inválida:**
```bash
# Gerar nova key no provider
# Atualizar no ambiente
railway variables set GROQ_API_KEY=new_key
railway redeploy
```

**Se provider fora:**
- Alternar para outro provider configurado
- Verificar status page do provider

### Prevenção
- Configurar múltiplos providers
- Monitorar uso de quota

---

## 6. Disk full

### Sintomas
- Erros de escrita
- Logs param de ser gravados
- SQLite falha

### Diagnóstico

```bash
# Verificar espaço
df -h

# Maiores diretórios
du -sh data/* | sort -h
```

### Resolução

```bash
# Limpar backups antigos
find data/backups -mtime +30 -delete

# Limpar logs antigos
find logs/ -name "*.log" -mtime +7 -delete

# Compactar ChromaDB (se possível)
# ...
```

### Prevenção
- Configurar retenção de backups
- Alertas de espaço em disco
- Auto-cleanup de logs antigos

---

## Template de Incidente

```markdown
## Incidente: [Título]

**Data:** YYYY-MM-DD HH:MM
**Severidade:** P1/P2/P3
**Status:** Investigando/Mitigado/Resolvido

### Sintomas
- ...

### Timeline
- HH:MM - Alerta recebido
- HH:MM - Investigação iniciada
- HH:MM - Causa identificada
- HH:MM - Mitigação aplicada
- HH:MM - Resolvido

### Causa Raiz
...

### Resolução
...

### Ações Preventivas
- [ ] ...
```

---

## Contatos de Escalação

| Nível | Contato | Quando |
|-------|---------|--------|
| L1 | On-call | Primeiro responder |
| L2 | Tech Lead | Se L1 não resolver em 30min |
| L3 | CTO | Incidentes P1 |

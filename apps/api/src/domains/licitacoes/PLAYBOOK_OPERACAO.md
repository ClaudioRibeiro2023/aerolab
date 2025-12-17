# Playbook de Operação — Núcleo Licitações

> **Objetivo:** Guia operacional para monitoramento e resposta a incidentes do sistema de licitações.

---

## 1. Visão Geral do Sistema

### Componentes
- **Backend API:** FastAPI em `/api/v1/licitacoes/*`
- **Frontend UI:** Next.js em `/licitacoes`
- **Scheduler:** Job `daily_monitor` às 07:00 UTC
- **RAG Jurídico:** Base de conhecimento Lei 14.133/2021

### Fluxos
1. **daily_monitor:** Coleta → Dedup → Triage → Digest
2. **on_demand_analyze:** Compliance → Fetch → Analyst → Output

---

## 2. Monitoramento Diário

### Horários Chave
| Horário | Ação | Responsável |
|---------|------|-------------|
| 07:00 | Execução automática `daily_monitor` | Sistema |
| 08:00 | Verificar logs de execução | Ops |
| 09:00 | Triagem manual de P0/P1 | Analista |
| 17:00 | Review de análises do dia | Coordenador |

### Verificações
```bash
# Verificar status do scheduler
curl http://localhost:8000/api/v1/licitacoes/health

# Verificar último digest
curl http://localhost:8000/api/v1/licitacoes/digest/$(date +%Y-%m-%d)
```

---

## 3. Métricas e Alertas

### KPIs
- **Itens processados/dia:** >= 50
- **Taxa P0:** ~5-10% do total
- **Taxa de erro:** < 5%
- **Latência de coleta:** < 30s

### Alertas Críticos
| Condição | Severidade | Ação |
|----------|-----------|------|
| 0 itens coletados | CRÍTICO | Verificar API PNCP |
| Erro em 3+ execuções | ALTO | Verificar logs, reiniciar |
| > 50% P0 | MÉDIO | Ajustar thresholds de triage |
| Latência > 60s | BAIXO | Verificar rede/infraestrutura |

---

## 4. Troubleshooting

### Problema: Job não executa
```bash
# 1. Verificar logs
tail -f logs/licitacoes.log | grep daily_monitor

# 2. Verificar lock
# Se lock travado por > 30min, reiniciar serviço

# 3. Executar manualmente
curl -X POST http://localhost:8000/api/v1/licitacoes/monitor
```

### Problema: API PNCP indisponível
```bash
# 1. Verificar status PNCP
curl -I https://pncp.gov.br/api/consulta/v1/contratacoes

# 2. Se 503/504, aguardar e retry
# 3. Se persistir > 1h, ativar modo fallback (cache)
```

### Problema: Muitos falsos positivos em P0
```python
# Ajustar thresholds em agents/triage.py
# Linha ~190: _classify_priority()
# P0 threshold: 0.75 -> 0.80
```

### Problema: RAG não retorna resultados
```bash
# 1. Verificar ChromaDB
# 2. Verificar se coleção existe
# 3. Reingerir dados se necessário
```

---

## 5. Rollback

### Procedimento
1. Identificar versão estável anterior
2. Parar scheduler: `systemctl stop licitacoes-scheduler`
3. Deploy da versão anterior
4. Reiniciar: `systemctl start licitacoes-scheduler`
5. Verificar health check

### Comandos
```bash
# Listar versões
git tag -l "licitacoes-v*"

# Rollback
git checkout licitacoes-v0.1.0
docker-compose up -d --build api
```

---

## 6. Contatos

| Função | Responsável | Contato |
|--------|-------------|---------|
| Ops | TBD | - |
| Dev Lead | TBD | - |
| Analista Jurídico | TBD | - |

---

## 7. Checklist de Qualidade

### Pré-deploy
- [ ] 88+ testes passando
- [ ] Health check OK
- [ ] Logs sem erros críticos
- [ ] Métricas baseline capturadas

### Pós-deploy
- [ ] Health check OK em produção
- [ ] Primeiro digest executado com sucesso
- [ ] UI carregando corretamente
- [ ] Busca funcionando

---

## 8. Links Úteis

- **Documentação:** `docs/_aplicações/`
- **TODO:** `docs/_aplicações/TODO_LICITACAO.md`
- **API Docs:** `/docs` (Swagger)
- **PNCP API:** `https://pncp.gov.br/api/`

---

*Última atualização: Dezembro 2025*

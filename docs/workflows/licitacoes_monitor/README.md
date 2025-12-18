# Workflow: Monitoramento & Análise de Licitações (Techdengue)

> **Slug:** `licitacoes_monitor`  
> **Domínio:** `licitacoes`  
> **Versão:** 1.0.0

## Objetivo

Monitorar, coletar, classificar, analisar e validar juridicamente processos licitatórios relacionados ao Techdengue, gerando relatórios auditáveis com evidências e recomendações práticas.

---

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `fonte` | string | Sim | Fonte de dados: "pncp", "diarios_oficiais", "portais" |
| `termo_busca` | string | Sim | Termo principal de busca |
| `uf` | string | Não | Estado (sigla UF) |
| `municipio` | string | Não | Município específico |
| `periodo_inicio` | string (date) | Não | Data início (default: últimos 30 dias) |
| `periodo_fim` | string (date) | Não | Data fim (default: hoje) |
| `palavras_chave` | array[string] | Não | Palavras-chave adicionais |
| `modo_execucao` | string | Sim | "one_shot" ou "monitor" |

---

## Saídas

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `runs` | array | Histórico de execuções |
| `itens_encontrados` | array | Licitações encontradas |
| `triagem` | object | Resultado da triagem (scores, prioridades) |
| `analise_juridica` | object | Análise jurídica com base na Lei 14.133 |
| `evidencias` | array | Evidências coletadas (URLs, documentos) |
| `recomendacoes` | array | Recomendações de ação |
| `alertas` | array | Alertas P0/P1 |
| `export_json` | string | JSON exportável do resultado |

---

## Fluxo de Execução

```
[Input] → [Coleta] → [Dedup] → [Triagem] → [Análise] → [Compliance] → [Output]
    │         │          │          │           │            │
    └─────────┴──────────┴──────────┴───────────┴────────────┴─→ Audit Log
```

### Nodes

1. **input** - Validação de parâmetros de entrada
2. **coleta** - Busca em fontes (PNCP, diários, portais)
3. **dedup** - Deduplicação de itens
4. **triagem** - Classificação por prioridade (P0-P3)
5. **analise** - Análise detalhada com RAG jurídico
6. **compliance** - Validação de conformidade
7. **output** - Formatação e exportação

---

## Modos de Execução

### One-shot
Execução única para período específico. Ideal para análise pontual.

```json
{
  "fonte": "pncp",
  "termo_busca": "drone dengue",
  "modo_execucao": "one_shot",
  "periodo_inicio": "2025-01-01",
  "periodo_fim": "2025-01-31"
}
```

### Monitor
Execução contínua via scheduler (07:00 UTC diário).

```json
{
  "fonte": "pncp",
  "termo_busca": "drone dengue",
  "modo_execucao": "monitor",
  "uf": "SP"
}
```

---

## Integração

### API Endpoints

```
POST /workflows/registry/licitacoes_monitor/run
GET  /workflows/registry/licitacoes_monitor/runs
GET  /workflows/registry/licitacoes_monitor/runs/{run_id}
```

### Flow Studio

Template disponível em: `src/flow_studio/templates/licitacoes/licitacoes_monitor.json`

---

## Referências

- [Lei 14.133/2021](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm)
- [API PNCP](https://pncp.gov.br/api/)
- [TODO_LICITACAO.md](../../_aplicações/TODO_LICITACAO.md)

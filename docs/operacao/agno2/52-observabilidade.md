# Observabilidade

> Logs, métricas e monitoramento da plataforma.

---

## Pilares

| Pilar | Implementação |
|-------|---------------|
| **Logs** | Structured JSON logging |
| **Métricas** | Prometheus-style |
| **Health** | Liveness/Readiness probes |
| **Tracing** | Request IDs |

---

## Logs

### Formato

Logs são emitidos em JSON para fácil parsing:

```json
{
  "timestamp": "2024-12-16T10:00:00Z",
  "level": "INFO",
  "logger": "server",
  "message": "[OK] Flow Studio API loaded",
  "data": null,
  "source": {
    "file": "server.py",
    "line": 95
  }
}
```

### Níveis

| Nível | Uso |
|-------|-----|
| `DEBUG` | Informações de debug |
| `INFO` | Eventos normais |
| `WARNING` | Situações inesperadas não-críticas |
| `ERROR` | Erros que precisam atenção |
| `CRITICAL` | Falhas críticas do sistema |

### Configuração

```bash
# .env
LOG_LEVEL=INFO
LOG_FORMAT=json  # ou "text" para desenvolvimento
```

### Uso no Código

```python
from src.observability.logging import get_logger

logger = get_logger(__name__)

logger.info("Operation completed", duration=1.5, user="admin")
logger.error("Operation failed", error=str(e), exc_info=True)
```

---

## Métricas

### Endpoint

```
GET /metrics
```

### Formato (Prometheus)

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/health",status="200"} 1234

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 100
http_request_duration_seconds_bucket{le="0.5"} 200
```

### Métricas Disponíveis

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `http_requests_total` | Counter | Total de requests |
| `http_request_duration_seconds` | Histogram | Latência |
| `http_requests_by_status` | Counter | Requests por status |
| `http_requests_by_route` | Counter | Requests por rota |

### Integração Prometheus/Grafana

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agno'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## Health Checks

### Endpoints

| Endpoint | Uso |
|----------|-----|
| `GET /health` | Status geral detalhado |
| `GET /health/live` | Liveness probe (Kubernetes) |
| `GET /health/ready` | Readiness probe (Kubernetes) |

### Response `/health`

```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "version": "2.2.0",
  "components": [
    {"name": "database", "status": "healthy"},
    {"name": "chromadb", "status": "healthy"}
  ]
}
```

### Response `/health/live`

```json
{
  "status": "ok",
  "timestamp": "2024-12-16T10:00:00Z"
}
```

### Response `/health/ready`

```json
{
  "ready": true,
  "status": "healthy",
  "timestamp": "2024-12-16T10:00:00Z"
}
```

---

## Request Tracing

### Request ID

Cada request recebe um ID único:

```python
# Middleware adiciona automaticamente
request.state.request_id = str(uuid.uuid4())

# Disponível em logs
logger.info("Processing", request_id=request.state.request_id)
```

### Header de Response

```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

---

## Alertas Recomendados

### Críticos

| Condição | Ação |
|----------|------|
| `/health` não-200 por 1 min | Alerta imediato |
| Error rate > 5% | Alerta imediato |
| P99 latency > 10s | Alerta imediato |

### Warnings

| Condição | Ação |
|----------|------|
| Rate limit hits > 100/min | Investigar |
| Auth failures > 10/min | Investigar |
| Memory > 80% | Planejar scaling |

---

## Dashboard Interno

O módulo Dashboard (`/api/dashboard/*`) fornece:

- Estatísticas de uso
- Insights e recomendações
- Métricas agregadas

```http
GET /api/dashboard/stats
GET /api/dashboard/insights
```

---

## Referências

- [Código: src/observability/](../../src/observability/)
- [Setup Local](50-setup-local.md)

# SDKs e Clientes

> Como consumir a API Agno via SDKs e clientes.

---

## SDK Python

### Instalação

```bash
# Via pip (quando publicado)
pip install agno-client

# Via source
pip install -e ./src/sdk
```

### Uso Básico

```python
from src.sdk.client import AgnoClient

# Inicializar cliente
client = AgnoClient(
    base_url="http://localhost:8000",
    token="your-jwt-token"
)

# Listar agentes
agents = client.agents.list()

# Criar agente
agent = client.agents.create(
    name="researcher",
    model="groq:llama-3.3-70b-versatile",
    instructions="You are a research assistant"
)

# Executar agente
response = client.agents.run("researcher", "What are AI trends?")
print(response.content)
```

### Classes Disponíveis

| Classe | Métodos |
|--------|---------|
| `AgnoClient` | Cliente principal |
| `AgentsAPI` | `list()`, `get()`, `create()`, `update()`, `delete()`, `run()` |
| `TeamsAPI` | `list()`, `get()`, `create()`, `delete()`, `run()` |
| `WorkflowsAPI` | `list()`, `get()`, `create()`, `delete()`, `execute()` |
| `RAGAPI` | `ingest()`, `query()`, `collections()` |

### Código

- **Localização:** `src/sdk/client.py`

---

## Cliente HTTP Genérico

### Python (httpx)

```python
import httpx

class AgnoAPI:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    def list_agents(self):
        return self.client.get("/agents").json()

    def run_agent(self, agent_id: str, message: str):
        return self.client.post(
            f"/agents/{agent_id}/run",
            json={"message": message}
        ).json()

# Uso
api = AgnoAPI("http://localhost:8000", "your-token")
agents = api.list_agents()
```

### TypeScript/JavaScript

```typescript
class AgnoAPI {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request(path: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return response.json();
  }

  async listAgents() {
    return this.request('/agents');
  }

  async runAgent(agentId: string, message: string) {
    return this.request(`/agents/${agentId}/run`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
}

// Uso
const api = new AgnoAPI('http://localhost:8000', 'your-token');
const agents = await api.listAgents();
```

### cURL

```bash
# Variáveis
BASE_URL="http://localhost:8000"
TOKEN="your-jwt-token"

# Listar agentes
curl -H "Authorization: Bearer $TOKEN" $BASE_URL/agents

# Executar agente
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are AI trends?"}' \
  $BASE_URL/agents/researcher/run
```

---

## Gerando Clientes Tipados

### TypeScript (openapi-typescript)

```bash
# Gerar tipos
npx openapi-typescript http://localhost:8000/openapi.json -o api-types.ts

# Usar com fetch
import type { paths } from './api-types';

type AgentsResponse = paths['/agents']['get']['responses']['200']['content']['application/json'];
```

### Python (openapi-python-client)

```bash
# Instalar
pip install openapi-python-client

# Gerar cliente
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output-path ./agno-client
```

---

## Integração com Frontend

O frontend Next.js já possui hooks configurados:

```typescript
// frontend/hooks/use-agents.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents').then(r => r.data)
  });
}

export function useRunAgent() {
  return useMutation({
    mutationFn: ({ agentId, message }: { agentId: string; message: string }) =>
      api.post(`/agents/${agentId}/run`, { message })
  });
}
```

---

## Referências

- [Contratos API](21-api.md)
- [OpenAPI](22-openapi.md)
- [Código SDK](../../src/sdk/)

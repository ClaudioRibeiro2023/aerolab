# Guia de Domínios Especializados

Este documento descreve os domínios especializados disponíveis no template e como usá-los.

---

## Visão Geral

O template suporta 6 domínios especializados:

| Domínio | Descrição | Instalação |
|---------|-----------|------------|
| **Geo** | Geolocalização e análise espacial | `pip install -e .[geo]` |
| **Database** | SQL e analytics de dados | `pip install -e .[database]` |
| **DevOps** | GitHub, Netlify, Supabase | `pip install -e .[devops]` |
| **Finance** | Mercado financeiro e análise | `pip install -e .[finance]` |
| **Legal** | Análise jurídica | `pip install -e .[legal]` |
| **Corporate** | Estratégia empresarial | `pip install -e .[corporate]` |

Para instalar todos:

```bash
pip install -e .[all-domains]
```

---

## 1. Domínio Geo (Geolocalização)

### Ferramentas

#### MapboxTool

Integração com Mapbox API para geocoding, rotas e isócronas.

```python
from src.tools.geo.mapbox import MapboxTool

tool = MapboxTool()

# Geocoding
result = tool.run(action="geocode", address="Av. Paulista, 1000, São Paulo")
print(result.data)  # {"lat": -23.56, "lon": -46.65, ...}

# Rota
result = tool.run(
    action="directions",
    origin=(-23.56, -46.65),
    destination=(-23.55, -46.63),
)
print(result.data)  # {"distance_km": 1.2, "duration_min": 5, ...}
```

#### SpatialTool

Análise espacial com Shapely/GeoPandas.

```python
from src.tools.geo.spatial import SpatialTool

tool = SpatialTool()

# Distância entre pontos
result = tool.run(
    action="distance",
    point1=(-23.56, -46.65),
    point2=(-23.55, -46.63),
)
print(result.data)  # {"distance_km": 1.2}
```

### Agente GeoAgent

```python
from src.agents.domains import GeoAgent

agent = GeoAgent.create(name="MeuGeoAnalista")
agent.print_response("Analise a mobilidade urbana na região central de São Paulo")
```

### Variáveis de Ambiente

```bash
MAPBOX_API_KEY=pk.xxx
```

---

## 2. Domínio Database (Dados)

### Ferramentas

#### SQLTool

Execução segura de queries SQL.

```python
from src.tools.database.sql import SQLTool

tool = SQLTool(config={"db_url": "sqlite:///data.db", "read_only": True})

# Query
result = tool.run(action="query", sql="SELECT * FROM users LIMIT 10")
print(result.data)  # {"rows": [...], "count": 10}

# Schema
result = tool.run(action="schema", table="users")
print(result.data)  # {"columns": [...], "primary_key": [...]}
```

#### AnalyticsTool

Análise de dados com Pandas.

```python
from src.tools.database.analytics import AnalyticsTool

tool = AnalyticsTool()

data = [
    {"name": "A", "value": 10},
    {"name": "B", "value": 20},
]

# Estatísticas
result = tool.run(action="describe", data=data)

# Agregação
result = tool.run(
    action="aggregate",
    data=data,
    group_by=["name"],
    aggregations={"value": "sum"},
)
```

### Agente DataAgent

```python
from src.agents.domains import DataAgent

agent = DataAgent.create(name="MeuDataAnalyst")
agent.print_response("Analise os dados de vendas do último trimestre")
```

### Variáveis de Ambiente

```bash
DATABASE_URL=sqlite:///data/databases/agents.db
```

---

## 3. Domínio DevOps

### Ferramentas

#### GitHubTool

```python
from src.tools.devops.github import GitHubTool

tool = GitHubTool()

# Listar repos
result = tool.run(action="repos")

# Criar issue
result = tool.run(
    action="create_issue",
    repo="user/repo",
    title="Bug encontrado",
    body="Descrição do bug",
)
```

#### SupabaseTool

```python
from src.tools.devops.supabase import SupabaseTool

tool = SupabaseTool()

# Select
result = tool.run(action="select", table="users", limit=10)

# Insert
result = tool.run(action="insert", table="users", data={"name": "John"})
```

### Agente DevAgent

```python
from src.agents.domains import DevAgent

agent = DevAgent.create(name="MeuDevOps")
agent.print_response("Crie uma issue no repositório X para o bug Y")
```

### Variáveis de Ambiente

```bash
GITHUB_TOKEN=ghp_xxx
NETLIFY_AUTH_TOKEN=xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
```

---

## 4. Domínio Finance (Financeiro)

### Ferramentas

#### MarketTool

```python
from src.tools.finance.market import MarketTool

tool = MarketTool()

# Cotação
result = tool.run(action="quote", symbol="PETR4.SA")
print(result.data)  # {"price": 35.50, "change": 0.02, ...}

# Histórico
result = tool.run(action="history", symbol="PETR4.SA", period="1mo")

# Fundamentals
result = tool.run(action="fundamentals", symbol="PETR4.SA")
```

#### FinancialAnalysisTool

```python
from src.tools.finance.analysis import FinancialAnalysisTool

tool = FinancialAnalysisTool()

# DCF
result = tool.run(
    action="dcf",
    cash_flows=[100, 110, 120, 130],
    discount_rate=0.10,
)

# Indicadores
result = tool.run(
    action="ratios",
    financials={
        "revenue": 1000000,
        "net_income": 150000,
        "total_assets": 500000,
        "total_equity": 300000,
    },
)
```

### Agente FinanceAgent

```python
from src.agents.domains import FinanceAgent

agent = FinanceAgent.create(name="MeuAnalista")
agent.print_response("Analise a ação PETR4 para investimento de longo prazo")
```

---

## 5. Domínio Legal (Jurídico)

### Ferramentas

#### LegalSearchTool

```python
from src.tools.legal.search import LegalSearchTool

tool = LegalSearchTool()

# Buscar legislação (stub - integração futura)
result = tool.run(action="search_legislation", query="LGPD")
```

### Agente LegalAgent

```python
from src.agents.domains import LegalAgent

agent = LegalAgent.create(name="MeuAdvogado")
agent.print_response("Analise os riscos de compliance neste contrato")
```

**Nota:** Este domínio requer integração com bases jurídicas específicas.

---

## 6. Domínio Corporate (Corporativo)

### Ferramentas

#### StrategyTool

```python
from src.tools.corporate.strategy import StrategyTool

tool = StrategyTool()

# Template SWOT
result = tool.run(action="swot", context="Empresa de tecnologia")

# Template Porter
result = tool.run(action="porter", industry="E-commerce")

# Template PESTEL
result = tool.run(action="pestel", market="Brasil")
```

### Agente CorporateAgent

```python
from src.agents.domains import CorporateAgent

agent = CorporateAgent.create(name="MeuConsultor")
agent.print_response("Faça uma análise SWOT da empresa X")
```

---

## Times Pré-configurados

### Time de Conteúdo

```python
from src.teams.presets import create_content_team

team = create_content_team(agents_map)
team.print_response("Escreva um artigo sobre IA")
```

### Time Geoespacial

```python
from src.teams.presets import create_geo_team

team = create_geo_team(model_provider="groq")
team.print_response("Analise a região metropolitana de São Paulo")
```

### Time de Dados

```python
from src.teams.presets import create_data_team

team = create_data_team(model_provider="groq")
team.print_response("Analise os dados de vendas")
```

### Time Financeiro

```python
from src.teams.presets import create_finance_team

team = create_finance_team(model_provider="groq")
team.print_response("Analise o portfólio de investimentos")
```

---

## RBAC por Domínio

O sistema suporta controle de acesso granular por domínio:

### Papéis Disponíveis

| Papel | Descrição | Domínios |
|-------|-----------|----------|
| `admin` | Acesso total | Todos |
| `analyst` | Leitura e execução | Todos |
| `viewer` | Apenas leitura | Todos |
| `geo_analyst` | Especialista geo | Geo, General |
| `finance_analyst` | Especialista finance | Finance, General |
| `legal_analyst` | Especialista legal | Legal, General |
| `developer` | Dev e DevOps | DevOps, Data, General |

### Exemplo de Uso

```python
from src.auth.rbac import check_permission, Resource, Action, Domain

# Verificar permissão
allowed = check_permission(
    user_role="geo_analyst",
    resource=Resource.AGENTS,
    action=Action.RUN,
    domain=Domain.GEO,
)
print(allowed)  # True
```

---

## Audit Logging

Todas as ações são registradas para compliance:

```python
from src.audit import get_audit_logger, AuditEvent, EventType

audit = get_audit_logger()

# Registrar evento
audit.log(AuditEvent(
    event_type=EventType.AGENT_RUN,
    user="user@example.com",
    resource="agents",
    action="run",
    domain="finance",
    details={"agent": "FinanceAgent", "prompt": "..."},
))

# Consultar logs
logs = audit.query(user="user@example.com", limit=10)
```

### Endpoints de Audit

- `GET /audit/logs` - Lista logs (admin)
- `GET /audit/logs/stats` - Estatísticas (admin)
- `GET /audit/logs/user/{username}` - Atividade do usuário
- `GET /audit/logs/security` - Eventos de segurança

---

## Criando um Novo Domínio

1. Criar diretório em `src/tools/{dominio}/`
2. Implementar ferramentas herdando de `BaseTool`
3. Criar agente em `src/agents/domains/{dominio}.py`
4. Criar time em `src/teams/presets/{dominio}.py`
5. Adicionar papel em `src/auth/rbac.py`
6. Adicionar dependências em `pyproject.toml`

### Exemplo: Domínio de Marketing

```python
# src/tools/marketing/__init__.py
from .analytics import MarketingAnalyticsTool
from .social import SocialMediaTool

__all__ = ["MarketingAnalyticsTool", "SocialMediaTool"]
```

```python
# src/agents/domains/marketing.py
from src.agents import BaseAgent

class MarketingAgent:
    @classmethod
    def create(cls, name: str = "MarketingAnalyst", **kwargs):
        return BaseAgent.create(
            name=name,
            role="Especialista em marketing digital",
            instructions=[
                "Analise métricas de marketing",
                "Sugira estratégias de crescimento",
            ],
            **kwargs,
        )
```

---

## Próximos Passos

1. **Integrar APIs reais** nos domínios Legal e Corporate
2. **Criar dashboards** específicos por domínio no frontend
3. **Implementar mais ferramentas** em cada domínio
4. **Adicionar testes** para cada ferramenta

# Flow Studio - Arquitetura Técnica

> Versão: 3.0.0
> Última atualização: 2025-12-09

## Visão Geral

O Flow Studio é um sistema de workflows visuais AI-native composto por 4 camadas principais:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│   routes.py (REST) │ websocket.py (Real-time)          │
├─────────────────────────────────────────────────────────┤
│                   AI Layer                              │
│   nl_designer.py │ optimizer.py │ predictor.py         │
├─────────────────────────────────────────────────────────┤
│                 Execution Layer                         │
│   engine.py (Orchestration) │ executor.py (Nodes)      │
├─────────────────────────────────────────────────────────┤
│                   Core Layer                            │
│   types.py (Models) │ validation.py (Rules)            │
└─────────────────────────────────────────────────────────┘
```

---

## Módulos e Responsabilidades

### `types.py` - Modelos de Domínio

Define todas as estruturas de dados do sistema:

| Classe | Propósito |
|--------|-----------|
| `NodeType` | Enum com 60+ tipos de nós |
| `NodeCategory` | Categorias: agents, logic, data, memory, integrations, governance |
| `Port` | Definição de entrada/saída de um nó |
| `Node` | Representação de um nó no workflow |
| `Connection` | Ligação entre dois nós (edge) |
| `Workflow` | Container de nós e conexões |
| `Execution` | Instância de execução |
| `ExecutionStep` | Resultado de um nó executado |

**Dependências:** Nenhuma (módulo puro)

### `validation.py` - Validação de Workflows

Responsável por garantir integridade antes da execução:

- Validação de conexões (tipos compatíveis)
- Detecção de ciclos
- Verificação de nós obrigatórios
- Validação de configuração por tipo de nó

**Dependências:** `types.py`

### `engine.py` - Motor de Execução

Orquestra a execução de workflows:

- Resolução de ordem topológica
- Execução paralela de nós independentes
- Gerenciamento de estado
- Propagação de dados entre nós
- Suporte a debug (step, pause, resume)

**Dependências:** `types.py`, `executor.py`, `validation.py`

### `executor.py` - Executores de Nós

Implementa a lógica específica de cada tipo de nó:

```python
# Registro de executores
EXECUTORS: dict[NodeType, Callable] = {
    NodeType.AGENT: execute_agent_node,
    NodeType.CONDITION: execute_condition_node,
    NodeType.HTTP: execute_http_node,
    # ...
}
```

**Dependências:** `types.py`, bibliotecas externas (requests, etc.)

### `ai/nl_designer.py` - Designer por Linguagem Natural

Converte descrições em texto para workflows:

```
"Crie um bot de atendimento" → Workflow com nós configurados
```

**Dependências:** `types.py`, LLM (Groq/OpenAI)

### `ai/optimizer.py` - Otimizador de Workflows

Analisa workflows e sugere melhorias:

- Performance (paralelização)
- Custo (modelos mais baratos)
- Confiabilidade (retry, fallback)

**Dependências:** `types.py`

### `ai/predictor.py` - Preditor de Custo/Tempo

Estima recursos necessários antes da execução:

- Custo estimado em USD (baseado em tokens)
- Tempo estimado de execução
- Confiança da estimativa

**Dependências:** `types.py`, pricing data

### `api/routes.py` - REST API

Endpoints FastAPI para CRUD e execução:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/workflows` | GET/POST | Listar/Criar |
| `/workflows/{id}` | GET/PUT/DELETE | CRUD |
| `/workflows/{id}/execute` | POST | Executar |
| `/ai/design` | POST | Gerar de NL |
| `/ai/optimize` | POST | Otimizar |

**Dependências:** Todos os módulos

### `api/websocket.py` - Real-time Updates

WebSocket para atualizações de execução em tempo real:

- `node_started` / `node_completed` / `node_error`
- `progress` (% conclusão)
- Comandos: `pause`, `resume`, `step`

**Dependências:** `engine.py`

---

## Fluxo de Dados

### Criação de Workflow (NL)

```
1. Cliente envia descrição em texto
2. nl_designer.py chama LLM para gerar estrutura
3. validation.py valida o workflow gerado
4. routes.py persiste e retorna o workflow
```

### Execução de Workflow

```
1. Cliente solicita execução via REST
2. engine.py cria Execution e resolve ordem
3. Para cada nó na ordem:
   a. executor.py executa lógica específica
   b. websocket.py notifica progresso
   c. Dados propagados para próximos nós
4. Resultado final retornado/armazenado
```

---

## Decisões de Design

### Por que não usar Celery/Workers?

- **Simplicidade:** Workflows típicos são curtos (<1min)
- **Latência:** Feedback em tempo real é crítico
- **Escopo:** Escala atual não justifica complexidade

### Por que tipagem forte (Pydantic)?

- Validação automática de dados
- Serialização JSON consistente
- Documentação via OpenAPI

### Por que WebSocket vs SSE?

- Comunicação bidirecional (pause/resume)
- Melhor suporte cross-browser
- Integração natural com FastAPI

---

## Pontos de Extensão

### Adicionar novo tipo de nó

1. Adicionar em `NodeType` (types.py)
2. Implementar executor em `executor.py`
3. Registrar no `EXECUTORS` dict

### Adicionar nova integração

1. Criar nó em `NodeType.INTEGRATION_*`
2. Implementar executor com SDK/API
3. Adicionar configuração em `Node.config`

---

## Testes

```bash
# Unit tests
pytest src/flow_studio/tests/ -v

# Com cobertura
pytest src/flow_studio/tests/ --cov=src/flow_studio
```

### Áreas cobertas

- `TestWorkflowCreation` - Criação de workflows
- `TestValidation` - Regras de validação
- `TestExecution` - Execução básica
- `TestAI` - Geração NL (mocked)

---

## Métricas e Observabilidade

| Métrica | Descrição |
|---------|-----------|
| `workflow_executions_total` | Total de execuções |
| `workflow_execution_duration` | Tempo de execução |
| `node_execution_errors` | Erros por tipo de nó |

---

## Referências

- [README.md](./README.md) - Guia de uso
- [types.py](./types.py) - Definições de tipos
- [Frontend Flow Studio](../../frontend/app/flow-studio/) - Interface visual

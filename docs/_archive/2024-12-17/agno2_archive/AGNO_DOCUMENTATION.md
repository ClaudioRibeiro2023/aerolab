# Documentação Agno

**Última atualização:** 2025-11-10  
**Fonte:** https://docs.agno.com/introduction

---

## O que é Agno?

**Agno é um framework multi-agente incrivelmente rápido, runtime e control plane.**

Agno fornece:
- O framework mais rápido para construir agentes, times multi-agente e workflows agênticos.
- Um aplicativo FastAPI pronto para uso que permite começar a construir produtos de IA desde o primeiro dia.
- Um control plane para testar, monitorar e gerenciar seu sistema.

### Exemplo Básico

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

# ************* Create Agent *************
agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    add_history_to_context=True,
    markdown=True,
)

# ************* Create AgentOS *************
agent_os = AgentOS(agents=[agno_agent])
app = agent_os.get_app()

# ************* Run AgentOS *************
if __name__ == "__main__":
    agent_os.serve(app="agno_agent:app", reload=True)
```

---

## O que é o AgentOS?

### 1. Runtime FastAPI Pré-construído
AgentOS vem com um aplicativo FastAPI pronto para uso para orquestrar seus agentes, times e workflows. Isso oferece uma grande vantagem inicial na construção do seu produto de IA.

### 2. Control Plane Integrado
A interface do usuário do [AgentOS](https://os.agno.com) se conecta diretamente ao seu runtime, permitindo testar, monitorar e gerenciar seu sistema em tempo real. Isso oferece visibilidade e controle incomparáveis sobre seu sistema.

### 3. Privado por Design
AgentOS é executado inteiramente na sua nuvem, garantindo privacidade completa dos dados. Nenhum dado jamais sai do seu sistema. Isso é ideal para empresas com preocupações de segurança.

---

## Instalação e Setup

### Instalar SDK Agno

```bash
# Criar ambiente virtual
python3 -m venv ~/.venvs/agno
source ~/.venvs/agno/bin/activate

# Instalar agno
pip install -U agno
```

### Atualizar Agno

```bash
pip install -U agno --no-cache-dir
```

---

## Quickstart

### Build your first Agent

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    markdown=True,
)

agent.print_response("Write a report on trending startups and products.", stream=True)
```

### Criar AgentOS Completo

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

# Create the Agent
agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-5"),
    # Add a database to the Agent
    db=SqliteDb(db_file="agno.db"),
    # Add the Agno MCP server to the Agent
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    # Add the previous session history to the context
    add_history_to_context=True,
    markdown=True,
)

# Create the AgentOS
agent_os = AgentOS(agents=[agno_agent])

# Get the FastAPI app for the AgentOS
app = agent_os.get_app()
```

### Run your AgentOS

```bash
# Setup virtual environment
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv pip install -U agno anthropic mcp 'fastapi[standard]' sqlalchemy

# Export your Anthropic API key
export ANTHROPIC_API_KEY=sk-***

# Run your AgentOS
fastapi dev agno_agent.py
```

Acesse http://localhost:8000

### Conectar ao AgentOS UI

1. Acesse [os.agno.com](https://os.agno.com)
2. Clique em "Add new OS" na barra de navegação superior
3. Selecione "Local" para conectar a um AgentOS local rodando na sua máquina
4. Digite a URL do endpoint do seu AgentOS (padrão: http://localhost:8000)
5. Dê um nome descritivo ao seu AgentOS (ex: "Development OS" ou "Local 8000")
6. Clique em "Connect"

### Chat com seu Agent

- Pergunte "What is Agno?" e o Agent responderá usando o servidor MCP do Agno
- Agentes mantêm seu próprio histórico, ferramentas e instruções; trocar de usuário não misturará o contexto

### Endpoints de API Pré-construídos

Acesse `/docs` em http://localhost:8000/docs para ver a documentação interativa da API.

---

## Key Features

### Core Intelligence

- **Model Agnostic:** Funciona com qualquer provedor de modelo, permitindo usar seus LLMs favoritos
- **Type Safe:** Impõe E/S estruturada através de `input_schema` e `output_schema` para comportamento previsível e componível
- **Dynamic Context Engineering:** Injeta variáveis, estado e dados recuperados dinamicamente no contexto. Perfeito para agentes orientados por dependências

### Memory, Knowledge, and Persistence

- **Persistent Storage:** Dê aos seus Agentes, Times e Workflows um banco de dados para persistir histórico de sessões, estado e mensagens
- **User Memory:** Sistema de memória integrado que permite aos Agentes relembrar contexto específico do usuário entre sessões
- **Agentic RAG:** Conecte-se a mais de 20 vector stores (chamadas de Knowledge no Agno) com busca híbrida + reranking pronto para uso
- **Culture (Collective Memory):** Conhecimento compartilhado que se acumula entre agentes e ao longo do tempo

### Execution & Control

- **Human-in-the-Loop:** Suporte nativo para confirmações, substituições manuais e execução de ferramentas externas
- **Guardrails:** Proteções integradas para validação, segurança e proteção de prompt
- **Agent Lifecycle Hooks:** Hooks pré e pós-execução para validar ou transformar entradas e saídas
- **MCP Integration:** Suporte de primeira classe para o Model Context Protocol (MCP) para conectar Agentes com sistemas externos
- **Toolkits:** Mais de 113 toolkits integrados com milhares de ferramentas — prontos para uso em domínios como dados, código, web e APIs empresariais

### Runtime & Evaluation

- **Runtime:** Runtime pré-construído baseado em FastAPI com endpoints compatíveis com SSE, pronto para produção desde o dia 1
- **Control Plane (UI):** Interface integrada para visualizar, monitorar e depurar a atividade do agente em tempo real
- **Natively Multimodal:** Agentes podem processar e gerar texto, imagens, áudio, vídeo e arquivos
- **Evals:** Meça a Acurácia, Performance e Confiabilidade dos seus Agentes

### Security & Privacy

- **Private by Design:** Roda inteiramente na sua nuvem. A UI se conecta diretamente ao seu AgentOS a partir do seu navegador — nenhum dado é enviado externamente
- **Data Governance:** Seus dados residem com segurança no banco de dados do seu Agent, sem compartilhamento externo de dados ou vendor lock-in
- **Access Control:** Controle de acesso baseado em função (RBAC) e permissões por agente para proteger contextos e ferramentas sensíveis

---

## Links Úteis

- **Website:** https://agno.com
- **Documentação:** https://docs.agno.com/introduction
- **GitHub:** https://github.com/agno-agi/agno
- **Discord:** https://agno.link/discord
- **YouTube:** https://agno.link/youtube
- **AgentOS UI:** https://os.agno.com
- **Documentação v1:** https://docs-v1.agno.com
- **Migration Guide v2:** https://docs.agno.com/how-to/v2-migration

---

## Recursos Adicionais

- **Quickstart:** https://docs.agno.com/introduction/quickstart
- **Examples Gallery:** https://docs.agno.com/examples/introduction
- **Performance:** https://docs.agno.com/introduction/performance
- **Getting Help:** https://docs.agno.com/introduction/getting-help
- **v2.0 Changelog:** https://docs.agno.com/how-to/v2-changelog
- **Workflows 2.0 Migration:** https://docs.agno.com/how-to/workflows-migration
- **Cursor Rules:** https://docs.agno.com/how-to/cursor-rules
- **Contributing:** https://docs.agno.com/how-to/contribute

---

## Telemetria

Agno coleta dados anônimos de telemetria para melhorar o produto. Veja mais detalhes em: https://docs.agno.com/concepts/telemetry

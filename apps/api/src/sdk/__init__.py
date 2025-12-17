"""
Agno SDK - Python SDK para desenvolvedores

O Agno SDK permite criar, configurar e executar agentes de IA
de forma simples e programática.

Instalação:
```bash
pip install agno-sdk
```

Uso básico:
```python
from agno import Agent, Tool

# Criar agente simples
agent = Agent(
    name="assistant",
    model="gpt-4o",
    instructions="You are a helpful assistant."
)

# Executar
response = agent.run("Hello!")
print(response.content)

# Com streaming
for chunk in agent.stream("Tell me a story"):
    print(chunk, end="")
```

Uso avançado com tools:
```python
from agno import Agent, Tool, Memory

# Definir tool customizada
@Tool
def search_database(query: str) -> str:
    '''Search the database for information.'''
    return f"Results for: {query}"

# Criar agente com tools e memória
agent = Agent(
    name="researcher",
    model="gpt-4o",
    tools=[search_database],
    memory=Memory(type="long_term")
)

# Executar com contexto
response = agent.run(
    "Search for AI trends",
    context={"user_id": "123"}
)
```

Multi-agent:
```python
from agno import Team, Agent

researcher = Agent(name="researcher", model="gpt-4o")
writer = Agent(name="writer", model="gpt-4o")

team = Team(
    agents=[researcher, writer],
    workflow="sequential"
)

result = team.run("Write a report about AI")
```
"""

from .agent import Agent, AgentConfig
from .tool import Tool, tool, ToolResult
from .memory import Memory, MemoryConfig
from .team import Team, TeamConfig
from .client import AgnoClient
from .types import (
    Message,
    Response,
    StreamChunk,
    Context,
    AgentState
)

__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    # Tools
    "Tool",
    "tool",
    "ToolResult",
    # Memory
    "Memory",
    "MemoryConfig",
    # Multi-agent
    "Team",
    "TeamConfig",
    # Client
    "AgnoClient",
    # Types
    "Message",
    "Response",
    "StreamChunk",
    "Context",
    "AgentState"
]

__version__ = "2.0.0"

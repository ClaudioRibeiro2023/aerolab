# 🚀 Agno Team Orchestrator v2.0

Advanced multi-agent team orchestration system.

## Features

### 🎭 15+ Orchestration Modes
- **Sequential** - Execute agents one after another
- **Parallel** - Execute all agents simultaneously
- **Hierarchical** - Supervisor delegates to workers
- **Pipeline** - Process data through agent pipeline
- **Debate** - Agents debate to find best solution
- **Consensus** - Agents work towards agreement
- **Voting** - Agents vote on proposals
- **Expert Panel** - Panel of experts contribute perspectives
- **Swarm** - Emergent intelligence from agent swarm
- And more...

### 🤖 20+ Agent Personas
Pre-built personas with goals, backstory, skills:
- **Research**: Senior Researcher, Data Analyst, Fact Checker
- **Content**: Content Writer, Copywriter, Technical Writer
- **Development**: Senior Developer, Code Reviewer, Architect
- **Business**: Product Manager, Business Analyst, Project Manager
- **Specialists**: Legal Advisor, Financial Analyst, Marketing Strategist
- **Critics**: Devil's Advocate, Quality Assurer, Risk Assessor

### 🧠 AI-Powered Features
- **NL Team Builder** - Create teams from natural language
- **Auto-Optimizer** - Automatic team optimization
- **Agent Learning** - Continuous improvement from feedback
- **Conflict Resolution** - 6+ resolution strategies

### 📝 Task System
- 15+ task templates
- Dependencies and scheduling
- Quality criteria
- Auto-assignment strategies

### 💬 Communication Layer
- Inter-agent messaging
- Conversation management
- Thread support
- Protocol handlers

### 🧠 Shared Memory
- Working memory (ephemeral)
- Episodic memory (history)
- Semantic memory (RAG)
- Procedural memory

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Create Team from Natural Language

```python
from src.team_orchestrator.ai.nl_builder import NLTeamBuilder

builder = NLTeamBuilder()
team = await builder.build_team(
    "Create a team for writing blog articles about AI"
)

print(f"Team: {team.name}")
print(f"Agents: {len(team.agents)}")
print(f"Mode: {team.mode.value}")
```

### Execute Team

```python
from src.team_orchestrator.engine import get_orchestration_engine

engine = get_orchestration_engine()
execution = await engine.execute(team, {"topic": "AI Trends 2024"})

print(f"Status: {execution.status.value}")
print(f"Output: {execution.output}")
```

### Create Custom Team

```python
from src.team_orchestrator.profiles import AgentProfileManager
from src.team_orchestrator.types import TeamConfiguration, OrchestrationMode

manager = AgentProfileManager()

# Create agents from personas
researcher = manager.from_persona("senior_researcher")
writer = manager.from_persona("content_writer")
reviewer = manager.from_persona("quality_assurer")

# Create team configuration
team = TeamConfiguration(
    name="Content Team",
    agents=[researcher, writer, reviewer],
    mode=OrchestrationMode.PIPELINE,
)
```

### Optimize Team

```python
from src.team_orchestrator.ai.optimizer import TeamOptimizer, OptimizationObjective

optimizer = TeamOptimizer()
result = await optimizer.optimize(team, OptimizationObjective.PERFORMANCE)

for suggestion in result.suggestions:
    print(f"- {suggestion.description} ({suggestion.impact} impact)")
```

## API Endpoints

### Teams
- `POST /api/teams/create` - Create team
- `POST /api/teams/create-from-nl` - Create from natural language
- `POST /api/teams/{id}/execute` - Execute team
- `POST /api/teams/{id}/optimize` - Get optimization suggestions
- `GET /api/teams/{id}/executions` - Get team executions

### Agents
- `GET /api/teams/agents/personas` - List available personas
- `POST /api/teams/agents/create` - Create agent

### Tasks
- `GET /api/teams/tasks/templates` - List task templates
- `POST /api/teams/tasks/create` - Create task

### Orchestration
- `GET /api/teams/modes` - List orchestration modes
- `GET /api/teams/templates` - List team templates

## Architecture

```
src/team_orchestrator/
├── __init__.py          # Package exports
├── types.py             # Type definitions
├── profiles.py          # Agent profile management
├── tasks.py             # Task management
├── engine.py            # Orchestration engine
├── communication.py     # Messaging layer
├── memory.py            # Shared memory
├── ai/
│   ├── __init__.py
│   ├── nl_builder.py    # NL Team Builder
│   ├── optimizer.py     # Team Optimizer
│   ├── conflict_resolver.py
│   └── learning.py      # Agent Learning
├── api/
│   ├── __init__.py
│   ├── routes.py        # REST API
│   └── websocket.py     # WebSocket API
└── tests/
    ├── __init__.py
    └── test_team_orchestrator.py
```

## Validation

Run validation script:

```bash
python validate_team_orchestrator.py
```

## Testing

```bash
pytest src/team_orchestrator/tests/ -v
```

## Comparison

| Feature | CrewAI | AutoGen | LangGraph | **Agno Teams v2.0** |
|---------|--------|---------|-----------|---------------------|
| Orchestration Modes | 2 | 3 | 4 | **15+** |
| NL Team Builder | ❌ | ❌ | ❌ | **✅** |
| Agent Learning | ❌ | ❌ | ❌ | **✅** |
| Auto-Optimizer | ❌ | ❌ | ❌ | **✅** |
| Conflict Resolution | ❌ | ⚠️ | ❌ | **✅** |
| Shared Memory | ⚠️ | ⚠️ | ⚠️ | **✅** |

## License

MIT

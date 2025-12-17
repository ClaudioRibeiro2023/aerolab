# Agno Flow Studio v3.0

**AI-Native Visual Workflow Builder**

## 🚀 Overview

Agno Flow Studio is a cutting-edge visual workflow builder designed for AI-native applications. It enables users to create, execute, and manage complex workflows through an intuitive drag-and-drop interface.

## ✨ Features

### Core Features (Implemented)

- **Visual Canvas** - React Flow-based canvas with minimap, grid, and zoom controls
- **60+ Node Types** - Comprehensive library covering agents, logic, data, memory, integrations, and governance
- **Smart Connections** - Type-safe connections with visual validation
- **Real-time Execution** - Live status updates via WebSocket
- **Natural Language Design** - Generate workflows from descriptions
- **AI Optimization** - Get intelligent suggestions for performance, cost, and reliability
- **Cost/Time Prediction** - Estimate execution costs and duration
- **Comprehensive Validation** - Validate workflows before execution

### Node Categories

| Category | Node Types | Description |
|----------|-----------|-------------|
| **Agents** | agent, team, supervisor, critic, planner, researcher, coder | AI agent orchestration |
| **Logic** | condition, switch, loop, parallel, join, delay, retry | Flow control |
| **Data** | transform, map, filter, merge, split, cache | Data processing |
| **Memory** | memory-read, memory-write, rag-search, vector-store | Knowledge management |
| **Integrations** | http, graphql, database, slack, webhook, mcp-tool | External services |
| **Governance** | human-approval, audit-log, cost-guard, pii-detector | Security & compliance |

## 📦 Installation

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## 🔧 Usage

### Python API

```python
from flow_studio import Workflow, Node, WorkflowEngine
from flow_studio.ai import NLWorkflowDesigner, WorkflowOptimizer

# Create from natural language
designer = NLWorkflowDesigner()
suggestion = await designer.design_workflow(
    "Create a customer service bot that routes inquiries"
)
workflow = suggestion.workflow

# Validate
from flow_studio import WorkflowValidator
validator = WorkflowValidator()
result = validator.validate(workflow)
print(f"Valid: {result.is_valid}")

# Optimize
optimizer = WorkflowOptimizer()
suggestions = optimizer.analyze(workflow)
for s in suggestions:
    print(f"{s.priority}: {s.title}")

# Execute
engine = WorkflowEngine()
execution = await engine.execute(workflow, {"query": "Hello"})
print(f"Result: {execution.output_data}")
```

### REST API

```bash
# Create workflow
curl -X POST http://localhost:8000/api/flow-studio/workflows \
  -H "Content-Type: application/json" \
  -d '{"name": "My Workflow", "nodes": [], "edges": []}'

# Generate from NL
curl -X POST http://localhost:8000/api/flow-studio/ai/design \
  -H "Content-Type: application/json" \
  -d '{"description": "Create an AI chatbot"}'

# Execute
curl -X POST http://localhost:8000/api/flow-studio/workflows/{id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"message": "Hello"}}'
```

### WebSocket

```javascript
// Connect to execution updates
const ws = new WebSocket('ws://localhost:8000/ws/execution/{execution_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'node_started':
      console.log(`Node ${data.nodeId} started`);
      break;
    case 'node_completed':
      console.log(`Node ${data.nodeId} completed`, data.output);
      break;
    case 'progress':
      console.log(`Progress: ${data.progress * 100}%`);
      break;
  }
};
```

## 🏗️ Architecture

```
flow_studio/
├── __init__.py          # Package exports
├── types.py             # Type definitions
├── engine.py            # Execution engine
├── executor.py          # Node executors
├── validation.py        # Workflow validation
├── ai/
│   ├── nl_designer.py   # Natural language designer
│   ├── optimizer.py     # Workflow optimizer
│   └── predictor.py     # Cost/time predictor
├── api/
│   ├── routes.py        # REST API
│   └── websocket.py     # WebSocket API
└── tests/
    └── test_workflow.py # Unit tests
```

## 🧪 Testing

```bash
# Run all tests
pytest src/flow_studio/tests/ -v

# Run specific test class
pytest src/flow_studio/tests/test_workflow.py::TestValidation -v

# Run with coverage
pytest src/flow_studio/tests/ --cov=flow_studio
```

## 📊 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flow-studio/workflows` | List workflows |
| POST | `/api/flow-studio/workflows` | Create workflow |
| GET | `/api/flow-studio/workflows/{id}` | Get workflow |
| PUT | `/api/flow-studio/workflows/{id}` | Update workflow |
| DELETE | `/api/flow-studio/workflows/{id}` | Delete workflow |
| POST | `/api/flow-studio/workflows/{id}/validate` | Validate workflow |
| POST | `/api/flow-studio/workflows/{id}/execute` | Execute workflow |
| GET | `/api/flow-studio/executions/{id}` | Get execution status |
| POST | `/api/flow-studio/ai/design` | Generate from NL |
| POST | `/api/flow-studio/ai/optimize` | Get optimizations |
| POST | `/api/flow-studio/ai/predict-cost` | Predict cost |
| POST | `/api/flow-studio/ai/predict-time` | Predict execution time |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `node_started` | Server→Client | Node execution started |
| `node_completed` | Server→Client | Node execution completed |
| `node_error` | Server→Client | Node encountered error |
| `progress` | Server→Client | Execution progress update |
| `pause` | Client→Server | Pause execution |
| `resume` | Client→Server | Resume execution |
| `step` | Client→Server | Step debug (single step) |

## 🎯 Roadmap

### Completed ✅
- [x] Sprint 1-3: Canvas, Nodes, Connections
- [x] Sprint 4-6: AI Features (NL Designer, Optimizer, Predictor)
- [x] Sprint 7: Live Execution Mode
- [x] Sprint 8: Debug Support

### In Progress 🚧
- [ ] Sprint 9: Testing & Simulation
- [ ] Sprint 10: Human-in-the-Loop

### Planned 📋
- [ ] Sprint 11-12: Security & Resilience
- [ ] Sprint 13-14: Plugins & Collaboration
- [ ] Sprint 15: Enterprise Features

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

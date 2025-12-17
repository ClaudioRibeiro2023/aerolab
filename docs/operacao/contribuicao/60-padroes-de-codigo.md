# Padrões de Código

> Convenções e estilos de código para o projeto Agno.

---

## Python (Backend)

### Formatação

| Ferramenta | Configuração |
|------------|--------------|
| **Black** | Line length: 100 |
| **Ruff** | Line length: 100, Python 3.12 |

### Executar

```bash
# Formatar
black src/ tests/

# Lint
ruff check src/ tests/

# Lint com fix
ruff check --fix src/ tests/
```

### Configuração

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.ruff]
line-length = 100
target-version = "py312"
```

### Convenções

```python
# Imports: stdlib, third-party, local (separados por linha em branco)
import os
import sys

from fastapi import FastAPI
import httpx

from src.config import get_settings
from src.auth import get_current_user

# Type hints obrigatórios para funções públicas
def process_request(data: dict, user_id: str) -> dict:
    ...

# Docstrings para módulos, classes e funções públicas
def create_agent(name: str, model: str) -> Agent:
    """Create a new agent with the given configuration.

    Args:
        name: Agent identifier
        model: LLM model ID (e.g., 'groq:llama-3.3-70b-versatile')

    Returns:
        Configured Agent instance

    Raises:
        ValueError: If model is not supported
    """
    ...

# Classes com PascalCase
class AgentService:
    ...

# Funções e variáveis com snake_case
def get_agent_by_id(agent_id: str) -> Agent:
    ...

# Constantes em UPPER_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

---

## TypeScript (Frontend)

### Formatação

| Ferramenta | Configuração |
|------------|--------------|
| **ESLint** | Next.js config |
| **Prettier** | (via ESLint) |

### Executar

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run typecheck
```

### Convenções

```typescript
// Imports: react, third-party, local
import { useState, useEffect } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';

import { api } from '@/lib/api';
import type { Agent } from '@/types';

// Interfaces com PascalCase
interface AgentCardProps {
  agent: Agent;
  onSelect: (id: string) => void;
}

// Componentes com PascalCase
export function AgentCard({ agent, onSelect }: AgentCardProps) {
  // Hooks no topo
  const [isLoading, setIsLoading] = useState(false);

  // Handlers com handle* prefix
  const handleClick = () => {
    onSelect(agent.id);
  };

  return (
    <div onClick={handleClick}>
      {agent.name}
    </div>
  );
}

// Hooks customizados com use* prefix
export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/agents'),
  });
}

// Constantes em UPPER_CASE
const API_TIMEOUT = 30000;
```

---

## Git Commits

### Formato

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Uso |
|------|-----|
| `feat` | Nova feature |
| `fix` | Bug fix |
| `docs` | Documentação |
| `style` | Formatação (não muda código) |
| `refactor` | Refatoração |
| `test` | Testes |
| `chore` | Tarefas de manutenção |

### Exemplos

```bash
feat(agents): add support for custom tools
fix(auth): handle expired token gracefully
docs(api): update endpoint documentation
refactor(rag): extract chunking logic
test(teams): add integration tests
```

---

## Estrutura de Arquivos

### Backend

```
src/
└── module_name/
    ├── __init__.py      # Exports públicos
    ├── api/             # Routers FastAPI
    │   └── routes.py
    ├── models.py        # Pydantic models
    ├── services.py      # Lógica de negócio
    └── tests/           # Testes do módulo
        └── test_services.py
```

### Frontend

```
frontend/
├── app/
│   └── feature/
│       ├── page.tsx      # Página
│       └── layout.tsx    # Layout
├── components/
│   └── feature/
│       ├── FeatureCard.tsx
│       └── FeatureList.tsx
└── hooks/
    └── use-feature.ts
```

---

## Pre-commit Hooks

Configurados em `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
```

### Instalar

```bash
pip install pre-commit
pre-commit install
```

---

## Referências

- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://airbnb.io/javascript/)

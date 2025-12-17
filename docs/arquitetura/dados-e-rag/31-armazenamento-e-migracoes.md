# Armazenamento e Migrações

> Configuração de bancos de dados e estratégias de migração.

---

## Bancos de Dados

### SQLite (Desenvolvimento)

**Uso:** Desenvolvimento local e testes.

**Arquivos:**
- `data/agents.db` - Agentes e configurações
- `data/hitl.db` - Sessões HITL

**Configuração:**
```bash
# .env (desenvolvimento)
DATABASE_URL=sqlite:///./data/agents.db
```

### PostgreSQL (Produção)

**Uso:** Ambientes de produção.

**Configuração:**
```bash
# .env (produção)
DATABASE_URL=postgresql://user:pass@host:5432/agno
```

### ChromaDB (Vector Store)

**Uso:** Armazenamento de embeddings para RAG.

**Local:**
```bash
CHROMA_DB_PATH=./data/chroma
```

**Servidor:**
```bash
CHROMA_HOST=http://chroma-server:8000
```

---

## Estrutura de Tabelas

### agents

```sql
CREATE TABLE agents (
    name TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    instructions TEXT,
    tools JSON,
    memory JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### hitl_sessions

```sql
CREATE TABLE hitl_sessions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    step_id TEXT,
    status TEXT DEFAULT 'pending',
    request_data JSON,
    response_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### hitl_actions

```sql
CREATE TABLE hitl_actions (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES hitl_sessions(id),
    action_type TEXT,
    data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Migrações

### SQLAlchemy

O projeto usa SQLAlchemy para ORM. Migrações são gerenciadas manualmente.

**Exemplo de modelo:**
```python
# src/hitl/repo.py
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HITLSession(Base):
    __tablename__ = "hitl_sessions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String)
    status = Column(String, default="pending")
    request_data = Column(JSON)
    created_at = Column(DateTime)
```

### Criação de Tabelas

```python
# Criar tabelas automaticamente
from sqlalchemy import create_engine
from src.hitl.repo import Base

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
```

---

## Backup e Restore

### Backup SQLite

```bash
# Backup
cp data/agents.db data/backups/agents_$(date +%Y%m%d).db

# Restore
cp data/backups/agents_20241216.db data/agents.db
```

### Backup PostgreSQL

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Backup ChromaDB

```bash
# ChromaDB local
cp -r data/chroma data/backups/chroma_$(date +%Y%m%d)
```

---

## Sistema de Backup Automático

O módulo `src/persistence/backup.py` implementa backups automáticos:

```python
from src.persistence.backup import BackupManager

manager = BackupManager(
    backup_path="./data/backups",
    retention_days=30
)

# Backup de dados
metadata = await manager.backup_data(
    data={"agents": agents_dict},
    backup_type="full"
)

# Cleanup de backups antigos
removed = await manager.cleanup_old_backups()
```

---

## Referências

- [Modelo de Dados](30-modelo-de-dados.md)
- [Código: src/persistence/](../../src/persistence/)

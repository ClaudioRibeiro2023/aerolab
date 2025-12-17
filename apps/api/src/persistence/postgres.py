"""
Store PostgreSQL para persistência de dados.

Gerencia conexões, queries e migrações.
"""

import os
import json
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


T = TypeVar("T")


@dataclass
class AgentRecord:
    """Registro de agente no banco."""
    name: str
    role: Optional[str]
    instructions: List[str]
    model_provider: str
    model_id: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class ExecutionRecord:
    """Registro de execução de agente."""
    id: Optional[int]
    agent_name: str
    prompt: str
    result: str
    duration: float
    tokens: int
    cost: float
    success: bool
    error: Optional[str]
    created_at: datetime


class PostgresStore:
    """
    Store PostgreSQL para persistência.
    
    Features:
    - Pool de conexões assíncrono
    - CRUD para agentes
    - Histórico de execuções
    - Queries customizadas
    - Migrações automáticas
    
    Configuração:
        DATABASE_URL ou variáveis individuais:
        POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        min_pool_size: int = 2,
        max_pool_size: int = 10
    ):
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg não instalado. Instale com: pip install asyncpg"
            )
        
        self.database_url = database_url or self._build_url()
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool: Optional[asyncpg.Pool] = None
    
    def _build_url(self) -> str:
        """Constrói URL do banco a partir de variáveis de ambiente."""
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "agentos")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    async def connect(self):
        """Inicializa pool de conexões."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size
            )
            await self._run_migrations()
    
    async def disconnect(self):
        """Fecha pool de conexões."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    @asynccontextmanager
    async def connection(self):
        """Context manager para conexão."""
        if not self._pool:
            await self.connect()
        async with self._pool.acquire() as conn:
            yield conn
    
    async def _run_migrations(self):
        """Executa migrações do schema."""
        async with self.connection() as conn:
            # Tabela de agentes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    name VARCHAR(255) PRIMARY KEY,
                    role TEXT,
                    instructions JSONB DEFAULT '[]',
                    model_provider VARCHAR(50),
                    model_id VARCHAR(100),
                    config JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tabela de execuções
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(255) REFERENCES agents(name) ON DELETE CASCADE,
                    prompt TEXT NOT NULL,
                    result TEXT,
                    duration FLOAT,
                    tokens INTEGER DEFAULT 0,
                    cost FLOAT DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Índices
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_agent ON executions(agent_name)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_created ON executions(created_at DESC)
            """)
            
            # Tabela de memória de agentes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(255),
                    memory_type VARCHAR(50),
                    content TEXT NOT NULL,
                    importance INTEGER DEFAULT 3,
                    tags JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
    
    # CRUD de Agentes
    async def create_agent(self, agent: AgentRecord) -> AgentRecord:
        """Cria um novo agente."""
        async with self.connection() as conn:
            await conn.execute("""
                INSERT INTO agents (name, role, instructions, model_provider, model_id, config, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, agent.name, agent.role, json.dumps(agent.instructions),
                agent.model_provider, agent.model_id, json.dumps(agent.config),
                agent.created_at, agent.updated_at)
        return agent
    
    async def get_agent(self, name: str) -> Optional[AgentRecord]:
        """Obtém um agente pelo nome."""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agents WHERE name = $1", name
            )
            if row:
                return AgentRecord(
                    name=row["name"],
                    role=row["role"],
                    instructions=json.loads(row["instructions"]) if row["instructions"] else [],
                    model_provider=row["model_provider"],
                    model_id=row["model_id"],
                    config=json.loads(row["config"]) if row["config"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    async def list_agents(self) -> List[AgentRecord]:
        """Lista todos os agentes."""
        async with self.connection() as conn:
            rows = await conn.fetch("SELECT * FROM agents ORDER BY name")
            return [
                AgentRecord(
                    name=row["name"],
                    role=row["role"],
                    instructions=json.loads(row["instructions"]) if row["instructions"] else [],
                    model_provider=row["model_provider"],
                    model_id=row["model_id"],
                    config=json.loads(row["config"]) if row["config"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    async def update_agent(self, name: str, **updates) -> Optional[AgentRecord]:
        """Atualiza um agente."""
        async with self.connection() as conn:
            sets = []
            values = [name]
            idx = 2
            
            for key, value in updates.items():
                if key in ["instructions", "config"]:
                    value = json.dumps(value)
                sets.append(f"{key} = ${idx}")
                values.append(value)
                idx += 1
            
            sets.append(f"updated_at = ${idx}")
            values.append(datetime.utcnow())
            
            await conn.execute(
                f"UPDATE agents SET {', '.join(sets)} WHERE name = $1",
                *values
            )
        return await self.get_agent(name)
    
    async def delete_agent(self, name: str) -> bool:
        """Deleta um agente."""
        async with self.connection() as conn:
            result = await conn.execute(
                "DELETE FROM agents WHERE name = $1", name
            )
            return "DELETE 1" in result
    
    # Execuções
    async def log_execution(self, execution: ExecutionRecord) -> ExecutionRecord:
        """Registra uma execução."""
        async with self.connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO executions (agent_name, prompt, result, duration, tokens, cost, success, error, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, execution.agent_name, execution.prompt, execution.result,
                execution.duration, execution.tokens, execution.cost,
                execution.success, execution.error, execution.created_at)
            execution.id = row["id"]
        return execution
    
    async def get_executions(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100,
        success_only: bool = False
    ) -> List[ExecutionRecord]:
        """Lista execuções."""
        async with self.connection() as conn:
            query = "SELECT * FROM executions WHERE 1=1"
            params = []
            idx = 1
            
            if agent_name:
                query += f" AND agent_name = ${idx}"
                params.append(agent_name)
                idx += 1
            
            if success_only:
                query += " AND success = TRUE"
            
            query += f" ORDER BY created_at DESC LIMIT ${idx}"
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            return [
                ExecutionRecord(
                    id=row["id"],
                    agent_name=row["agent_name"],
                    prompt=row["prompt"],
                    result=row["result"],
                    duration=row["duration"],
                    tokens=row["tokens"],
                    cost=row["cost"],
                    success=row["success"],
                    error=row["error"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
    
    # Query genérico
    async def query(self, sql: str, *args) -> List[Dict[str, Any]]:
        """Executa query customizada."""
        async with self.connection() as conn:
            rows = await conn.fetch(sql, *args)
            return [dict(row) for row in rows]
    
    async def execute(self, sql: str, *args) -> str:
        """Executa comando SQL."""
        async with self.connection() as conn:
            return await conn.execute(sql, *args)


# Singleton
_store: Optional[PostgresStore] = None


def get_postgres_store() -> PostgresStore:
    """Obtém instância singleton do store."""
    global _store
    if _store is None:
        _store = PostgresStore()
    return _store

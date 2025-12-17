"""
Data Sources - Conectores de dados para dashboards.

Suporta múltiplas fontes de dados.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class DataSourceType(str, Enum):
    """Tipos de data source."""
    # Internal
    AGENT_METRICS = "agent_metrics"
    WORKFLOW_METRICS = "workflow_metrics"
    LLM_METRICS = "llm_metrics"
    RAG_METRICS = "rag_metrics"
    SYSTEM_METRICS = "system_metrics"
    AUDIT_LOGS = "audit_logs"
    
    # Databases
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    
    # Time Series
    PROMETHEUS = "prometheus"
    INFLUXDB = "influxdb"
    TIMESCALEDB = "timescaledb"
    
    # APIs
    HTTP_API = "http_api"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    
    # Files
    CSV = "csv"
    JSON = "json"
    
    # Custom
    PYTHON = "python"
    CUSTOM = "custom"


@dataclass
class ConnectionConfig:
    """Configuração de conexão."""
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""  # Em produção: vault/secrets
    ssl: bool = False
    
    # Connection pool
    pool_size: int = 5
    max_overflow: int = 10
    
    # Timeout
    connect_timeout: int = 10
    query_timeout: int = 30
    
    def to_dict(self) -> Dict:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "ssl": self.ssl,
            "poolSize": self.pool_size,
            "connectTimeout": self.connect_timeout,
        }


@dataclass
class HTTPConfig:
    """Configuração de API HTTP."""
    base_url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    auth_type: str = "none"  # none, basic, bearer, api_key
    auth_token: str = ""
    
    # Retry
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # Timeout
    timeout: int = 30
    
    def to_dict(self) -> Dict:
        return {
            "baseUrl": self.base_url,
            "authType": self.auth_type,
            "timeout": self.timeout,
            "retryCount": self.retry_count,
        }


@dataclass
class PrometheusConfig:
    """Configuração de Prometheus."""
    url: str = "http://localhost:9090"
    auth_type: str = "none"
    username: str = ""
    password: str = ""
    
    # Query defaults
    default_step: str = "15s"
    max_points: int = 11000
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "authType": self.auth_type,
            "defaultStep": self.default_step,
        }


@dataclass
class DataSourceConfig:
    """Configuração completa de data source."""
    connection: Optional[ConnectionConfig] = None
    http: Optional[HTTPConfig] = None
    prometheus: Optional[PrometheusConfig] = None
    
    # Custom Python function
    python_function: Optional[str] = None  # Nome da função
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    def to_dict(self) -> Dict:
        result = {
            "cacheEnabled": self.cache_enabled,
            "cacheTtl": self.cache_ttl_seconds,
        }
        
        if self.connection:
            result["connection"] = self.connection.to_dict()
        if self.http:
            result["http"] = self.http.to_dict()
        if self.prometheus:
            result["prometheus"] = self.prometheus.to_dict()
        
        return result


@dataclass
class QueryResult:
    """Resultado de uma query."""
    data: Any = None
    columns: List[str] = field(default_factory=list)
    rows: int = 0
    execution_time_ms: float = 0
    cached: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "data": self.data,
            "columns": self.columns,
            "rows": self.rows,
            "executionTimeMs": self.execution_time_ms,
            "cached": self.cached,
            "error": self.error,
        }


@dataclass
class DataSource:
    """
    Data Source para dashboards.
    
    Abstração para conectar com diferentes fontes de dados.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Data Source"
    description: str = ""
    type: DataSourceType = DataSourceType.AGENT_METRICS
    
    # Config
    config: DataSourceConfig = field(default_factory=DataSourceConfig)
    
    # Status
    is_connected: bool = False
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    # Handlers
    _query_handler: Optional[Callable] = field(default=None, repr=False)
    
    async def connect(self) -> bool:
        """Testa conexão com o data source."""
        try:
            if self.type in (
                DataSourceType.AGENT_METRICS,
                DataSourceType.WORKFLOW_METRICS,
                DataSourceType.LLM_METRICS,
                DataSourceType.RAG_METRICS,
                DataSourceType.SYSTEM_METRICS
            ):
                # Internal: sempre conectado
                self.is_connected = True
            
            elif self.type == DataSourceType.PROMETHEUS:
                # Testar conexão Prometheus
                self.is_connected = True  # Placeholder
            
            elif self.type == DataSourceType.HTTP_API:
                # Testar endpoint
                self.is_connected = True  # Placeholder
            
            else:
                # Database connections
                self.is_connected = True  # Placeholder
            
            self.last_check = datetime.now()
            self.error_message = None
            return True
            
        except Exception as e:
            self.is_connected = False
            self.error_message = str(e)
            logger.error(f"Connection failed for {self.name}: {e}")
            return False
    
    async def query(
        self,
        query: str,
        params: Optional[Dict] = None,
        time_range: Optional[Dict] = None
    ) -> QueryResult:
        """Executa query no data source."""
        import time
        start = time.time()
        
        try:
            if self._query_handler:
                data = await self._query_handler(query, params, time_range)
            else:
                data = await self._execute_query(query, params, time_range)
            
            execution_time = (time.time() - start) * 1000
            
            return QueryResult(
                data=data,
                rows=len(data) if isinstance(data, list) else 1,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(error=str(e))
    
    async def _execute_query(
        self,
        query: str,
        params: Optional[Dict],
        time_range: Optional[Dict]
    ) -> Any:
        """Executa query específica por tipo."""
        if self.type == DataSourceType.AGENT_METRICS:
            return await self._query_agent_metrics(query, params, time_range)
        
        elif self.type == DataSourceType.PROMETHEUS:
            return await self._query_prometheus(query, params, time_range)
        
        elif self.type == DataSourceType.HTTP_API:
            return await self._query_http(query, params)
        
        # Placeholder para outros tipos
        return []
    
    async def _query_agent_metrics(
        self,
        query: str,
        params: Optional[Dict],
        time_range: Optional[Dict]
    ) -> List[Dict]:
        """Query métricas de agentes."""
        # Integrar com src/observability e src/agents/telemetry
        from src.observability.metrics import registry
        
        # Placeholder: retornar sample data
        return [
            {"agent": "assistant", "executions": 150, "success_rate": 0.95},
            {"agent": "researcher", "executions": 80, "success_rate": 0.92},
        ]
    
    async def _query_prometheus(
        self,
        query: str,
        params: Optional[Dict],
        time_range: Optional[Dict]
    ) -> List[Dict]:
        """Query Prometheus."""
        # Em produção: usar httpx para query Prometheus API
        return []
    
    async def _query_http(
        self,
        query: str,
        params: Optional[Dict]
    ) -> Any:
        """Query HTTP API."""
        # Em produção: usar httpx
        return {}
    
    def set_query_handler(
        self,
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Define handler customizado de query."""
        self._query_handler = handler
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "config": self.config.to_dict(),
            "isConnected": self.is_connected,
            "lastCheck": self.last_check.isoformat() if self.last_check else None,
            "errorMessage": self.error_message,
            "createdAt": self.created_at.isoformat(),
        }
    
    @classmethod
    def agent_metrics(cls, name: str = "Agent Metrics") -> "DataSource":
        """Cria data source de métricas de agentes."""
        return cls(
            name=name,
            type=DataSourceType.AGENT_METRICS,
            is_connected=True
        )
    
    @classmethod
    def prometheus(cls, url: str, name: str = "Prometheus") -> "DataSource":
        """Cria data source Prometheus."""
        return cls(
            name=name,
            type=DataSourceType.PROMETHEUS,
            config=DataSourceConfig(
                prometheus=PrometheusConfig(url=url)
            )
        )
    
    @classmethod
    def http_api(cls, base_url: str, name: str = "HTTP API") -> "DataSource":
        """Cria data source HTTP."""
        return cls(
            name=name,
            type=DataSourceType.HTTP_API,
            config=DataSourceConfig(
                http=HTTPConfig(base_url=base_url)
            )
        )


class DataSourceRegistry:
    """Registry de data sources."""
    
    def __init__(self):
        self._sources: Dict[str, DataSource] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self) -> None:
        """Inicializa data sources padrão."""
        defaults = [
            DataSource.agent_metrics("Agent Metrics"),
            DataSource(
                name="Workflow Metrics",
                type=DataSourceType.WORKFLOW_METRICS,
                is_connected=True
            ),
            DataSource(
                name="LLM Metrics",
                type=DataSourceType.LLM_METRICS,
                is_connected=True
            ),
            DataSource(
                name="RAG Metrics",
                type=DataSourceType.RAG_METRICS,
                is_connected=True
            ),
            DataSource(
                name="System Metrics",
                type=DataSourceType.SYSTEM_METRICS,
                is_connected=True
            ),
        ]
        
        for ds in defaults:
            self._sources[ds.id] = ds
    
    def register(self, source: DataSource) -> None:
        """Registra um data source."""
        self._sources[source.id] = source
    
    def get(self, source_id: str) -> Optional[DataSource]:
        """Obtém data source por ID."""
        return self._sources.get(source_id)
    
    def get_by_type(self, source_type: DataSourceType) -> List[DataSource]:
        """Obtém data sources por tipo."""
        return [s for s in self._sources.values() if s.type == source_type]
    
    def list_all(self) -> List[DataSource]:
        """Lista todos os data sources."""
        return list(self._sources.values())
    
    def remove(self, source_id: str) -> bool:
        """Remove um data source."""
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False


# Singleton
_registry: Optional[DataSourceRegistry] = None


def get_datasource_registry() -> DataSourceRegistry:
    """Obtém registry de data sources."""
    global _registry
    if _registry is None:
        _registry = DataSourceRegistry()
    return _registry

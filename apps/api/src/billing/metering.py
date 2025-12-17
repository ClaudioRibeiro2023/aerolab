"""
Metering Service - Rastreamento de Uso

Responsável por rastrear e agregar uso da plataforma.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import asyncio
import threading

from .types import UsageType, UsageRecord, UsageSummary


class MeteringService:
    """
    Serviço de metering para rastrear uso.
    
    Features:
    - Rastreamento de tokens, API calls, storage
    - Agregação por período
    - Buffers para batch inserts
    - Thread-safe
    """
    
    # Preços por modelo (em centavos por 1K tokens) - Atualizado Dez/2025
    # Estrutura alinhada com llm_catalog.json - preços estimados (preencher com valores oficiais)
    MODEL_PRICES: Dict[str, Dict[str, float]] = {
        # OpenAI - Novos modelos GPT-5.1 e O3
        "gpt-5.1": {"input": 0.5, "output": 1.5},
        "gpt-5.1-codex-max": {"input": 0.8, "output": 2.4},
        "gpt-5.1-codex-mini": {"input": 0.2, "output": 0.6},
        "o3-pro": {"input": 2.0, "output": 8.0},
        # OpenAI - Legacy (para compatibilidade)
        "gpt-4o": {"input": 0.25, "output": 1.0},
        "gpt-4o-mini": {"input": 0.015, "output": 0.06},
        "gpt-4-turbo": {"input": 1.0, "output": 3.0},
        # Anthropic - Claude 4.5
        "claude-sonnet-4.5": {"input": 0.3, "output": 1.5},
        "claude-opus-4.5": {"input": 1.5, "output": 7.5},
        "claude-haiku-4.5": {"input": 0.025, "output": 0.125},
        # Anthropic - Legacy (para compatibilidade)
        "claude-3-5-sonnet-20241022": {"input": 0.3, "output": 1.5},
        "claude-3-opus-20240229": {"input": 1.5, "output": 7.5},
        "claude-3-haiku-20240307": {"input": 0.025, "output": 0.125},
        # Google Gemini - 2.5 e 3.0
        "gemini-2.5-pro": {"input": 0.125, "output": 0.5},
        "gemini-2.5-flash": {"input": 0.0075, "output": 0.03},
        "gemini-2.5-flash-lite": {"input": 0.005, "output": 0.015},
        "gemini-3-pro": {"input": 0.2, "output": 0.8},
        # Google - Legacy
        "gemini-1.5-pro": {"input": 0.125, "output": 0.5},
        "gemini-1.5-flash": {"input": 0.0075, "output": 0.03},
        # Mistral - Large/Medium/Small 3.x
        "mistral-large-3": {"input": 0.4, "output": 1.2},
        "mistral-medium-3.1": {"input": 0.15, "output": 0.45},
        "mistral-small-3.1": {"input": 0.05, "output": 0.15},
        # Groq/Meta - Open models (geralmente gratuitos via Groq)
        "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
        "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
        "mixtral-8x7b-32768": {"input": 0.0, "output": 0.0},
    }
    
    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval_seconds: int = 60,
        markup_percent: float = 20.0
    ):
        """
        Args:
            buffer_size: Tamanho do buffer antes de flush
            flush_interval_seconds: Intervalo para flush automático
            markup_percent: Percentual de markup sobre preços
        """
        self._buffer: List[UsageRecord] = []
        self._buffer_lock = threading.Lock()
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval_seconds
        self._markup = markup_percent
        
        # Storage para persistência (in-memory para demo)
        self._records: List[UsageRecord] = []
        self._records_lock = threading.Lock()
        
        # Cache de agregações
        self._daily_cache: Dict[str, UsageSummary] = {}
        
    def track_tokens(
        self,
        user_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "gpt-4o-mini",
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> List[UsageRecord]:
        """
        Rastreia uso de tokens.
        
        Args:
            user_id: ID do usuário
            input_tokens: Tokens de entrada
            output_tokens: Tokens de saída
            model: Modelo utilizado
            agent_id: ID do agente (opcional)
            tenant_id: ID do tenant (opcional)
            metadata: Metadados adicionais
            
        Returns:
            Lista de UsageRecords criados
        """
        records = []
        prices = self.MODEL_PRICES.get(model, {"input": 0.1, "output": 0.3})
        
        if input_tokens > 0:
            unit_cost = (prices["input"] / 1000) * (1 + self._markup / 100)
            record = UsageRecord(
                user_id=user_id,
                tenant_id=tenant_id,
                usage_type=UsageType.TOKENS_INPUT,
                quantity=input_tokens,
                model=model,
                agent_id=agent_id,
                unit_cost=unit_cost,
                total_cost=input_tokens * unit_cost,
                metadata=metadata or {}
            )
            records.append(record)
            self._add_to_buffer(record)
        
        if output_tokens > 0:
            unit_cost = (prices["output"] / 1000) * (1 + self._markup / 100)
            record = UsageRecord(
                user_id=user_id,
                tenant_id=tenant_id,
                usage_type=UsageType.TOKENS_OUTPUT,
                quantity=output_tokens,
                model=model,
                agent_id=agent_id,
                unit_cost=unit_cost,
                total_cost=output_tokens * unit_cost,
                metadata=metadata or {}
            )
            records.append(record)
            self._add_to_buffer(record)
        
        return records
    
    def track_api_call(
        self,
        user_id: str,
        endpoint: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia chamada de API.
        
        Args:
            user_id: ID do usuário
            endpoint: Endpoint chamado
            tenant_id: ID do tenant
            metadata: Metadados adicionais
            
        Returns:
            UsageRecord criado
        """
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.API_CALLS,
            quantity=1,
            endpoint=endpoint,
            unit_cost=0,  # API calls geralmente não têm custo direto
            total_cost=0,
            metadata=metadata or {}
        )
        self._add_to_buffer(record)
        return record
    
    def track_agent_execution(
        self,
        user_id: str,
        agent_id: str,
        execution_time_ms: float = 0,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia execução de agente.
        """
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.AGENT_EXECUTIONS,
            quantity=1,
            agent_id=agent_id,
            metadata={
                **(metadata or {}),
                "execution_time_ms": execution_time_ms
            }
        )
        self._add_to_buffer(record)
        return record
    
    def track_workflow_run(
        self,
        user_id: str,
        workflow_id: str,
        nodes_executed: int = 0,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia execução de workflow.
        """
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.WORKFLOW_RUNS,
            quantity=1,
            workflow_id=workflow_id,
            metadata={
                **(metadata or {}),
                "nodes_executed": nodes_executed
            }
        )
        self._add_to_buffer(record)
        return record
    
    def track_storage(
        self,
        user_id: str,
        size_mb: float,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia uso de storage.
        """
        # Storage: $0.02 per GB per month = $0.00002 per MB
        unit_cost = 0.00002 * (1 + self._markup / 100)
        
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.STORAGE_MB,
            quantity=size_mb,
            unit_cost=unit_cost,
            total_cost=size_mb * unit_cost,
            metadata=metadata or {}
        )
        self._add_to_buffer(record)
        return record
    
    def track_rag_query(
        self,
        user_id: str,
        chunks_retrieved: int = 0,
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia query RAG.
        """
        # RAG queries: pequeno custo por query
        unit_cost = 0.001 * (1 + self._markup / 100)
        
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.RAG_QUERIES,
            quantity=1,
            unit_cost=unit_cost,
            total_cost=unit_cost,
            metadata={
                **(metadata or {}),
                "chunks_retrieved": chunks_retrieved
            }
        )
        self._add_to_buffer(record)
        return record
    
    def track_embeddings(
        self,
        user_id: str,
        tokens: int,
        model: str = "text-embedding-3-small",
        tenant_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> UsageRecord:
        """
        Rastreia criação de embeddings.
        """
        # Embedding prices (per 1K tokens)
        embedding_prices = {
            "text-embedding-3-small": 0.002,
            "text-embedding-3-large": 0.013,
            "text-embedding-ada-002": 0.01,
        }
        
        base_price = embedding_prices.get(model, 0.01)
        unit_cost = (base_price / 1000) * (1 + self._markup / 100)
        
        record = UsageRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            usage_type=UsageType.EMBEDDINGS,
            quantity=tokens,
            model=model,
            unit_cost=unit_cost,
            total_cost=tokens * unit_cost,
            metadata=metadata or {}
        )
        self._add_to_buffer(record)
        return record
    
    def _add_to_buffer(self, record: UsageRecord) -> None:
        """Adiciona record ao buffer."""
        with self._buffer_lock:
            self._buffer.append(record)
            
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self) -> None:
        """Flush buffer para storage."""
        with self._buffer_lock:
            if not self._buffer:
                return
                
            records_to_flush = self._buffer.copy()
            self._buffer.clear()
        
        with self._records_lock:
            self._records.extend(records_to_flush)
    
    def flush(self) -> int:
        """
        Força flush do buffer.
        
        Returns:
            Número de records flushed
        """
        with self._buffer_lock:
            count = len(self._buffer)
            if not self._buffer:
                return 0
            records_to_flush = self._buffer.copy()
            self._buffer.clear()
        
        with self._records_lock:
            self._records.extend(records_to_flush)
        
        return count
    
    def get_usage_summary(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime,
        tenant_id: Optional[str] = None
    ) -> UsageSummary:
        """
        Obtém resumo de uso para um período.
        
        Args:
            user_id: ID do usuário
            period_start: Início do período
            period_end: Fim do período
            tenant_id: ID do tenant (opcional)
            
        Returns:
            UsageSummary agregado
        """
        self.flush()  # Garantir que tudo está persistido
        
        summary = UsageSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        
        cost_by_model: Dict[str, float] = defaultdict(float)
        
        with self._records_lock:
            for record in self._records:
                # Filtrar por usuário e tenant
                if record.user_id != user_id:
                    continue
                if tenant_id and record.tenant_id != tenant_id:
                    continue
                if record.timestamp < period_start or record.timestamp > period_end:
                    continue
                
                # Agregar por tipo
                if record.usage_type == UsageType.TOKENS_INPUT:
                    summary.tokens_input += int(record.quantity)
                elif record.usage_type == UsageType.TOKENS_OUTPUT:
                    summary.tokens_output += int(record.quantity)
                elif record.usage_type == UsageType.API_CALLS:
                    summary.api_calls += int(record.quantity)
                elif record.usage_type == UsageType.STORAGE_MB:
                    summary.storage_mb += record.quantity
                elif record.usage_type == UsageType.AGENT_EXECUTIONS:
                    summary.agent_executions += int(record.quantity)
                elif record.usage_type == UsageType.WORKFLOW_RUNS:
                    summary.workflow_runs += int(record.quantity)
                elif record.usage_type == UsageType.RAG_QUERIES:
                    summary.rag_queries += int(record.quantity)
                elif record.usage_type == UsageType.EMBEDDINGS:
                    summary.embeddings += int(record.quantity)
                
                # Custo total
                summary.total_cost += record.total_cost
                
                # Custo por modelo
                if record.model:
                    cost_by_model[record.model] += record.total_cost
        
        summary.cost_by_model = dict(cost_by_model)
        return summary
    
    def get_daily_usage(
        self,
        user_id: str,
        date: datetime,
        tenant_id: Optional[str] = None
    ) -> UsageSummary:
        """
        Obtém uso de um dia específico.
        """
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        return self.get_usage_summary(user_id, start, end, tenant_id)
    
    def get_monthly_usage(
        self,
        user_id: str,
        year: int,
        month: int,
        tenant_id: Optional[str] = None
    ) -> UsageSummary:
        """
        Obtém uso de um mês específico.
        """
        start = datetime(year, month, 1)
        
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        return self.get_usage_summary(user_id, start, end, tenant_id)
    
    def get_records(
        self,
        user_id: str,
        usage_type: Optional[UsageType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UsageRecord]:
        """
        Obtém records individuais.
        """
        self.flush()
        
        with self._records_lock:
            filtered = [
                r for r in self._records
                if r.user_id == user_id
                and (usage_type is None or r.usage_type == usage_type)
            ]
            
            # Ordenar por timestamp desc
            filtered.sort(key=lambda r: r.timestamp, reverse=True)
            
            return filtered[offset:offset + limit]


# Singleton instance
_metering_service: Optional[MeteringService] = None


def get_metering_service() -> MeteringService:
    """Obtém instância singleton do MeteringService."""
    global _metering_service
    if _metering_service is None:
        _metering_service = MeteringService()
    return _metering_service

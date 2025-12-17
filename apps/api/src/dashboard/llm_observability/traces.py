"""
LLM Traces - Rastreamento de chamadas LLM.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import threading
import logging

logger = logging.getLogger(__name__)


class SpanType(str, Enum):
    """Tipo de span."""
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    RETRIEVAL = "retrieval"
    EMBEDDING = "embedding"
    CHAIN = "chain"
    AGENT = "agent"


class SpanStatus(str, Enum):
    """Status do span."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class LLMSpan:
    """
    Span de uma chamada LLM.
    
    Representa uma unidade de trabalho (chamada LLM, tool, etc.).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    parent_id: Optional[str] = None
    
    # Identificação
    name: str = ""
    type: SpanType = SpanType.LLM_CALL
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    
    # LLM específico
    model: str = ""
    provider: str = ""
    
    # Input/Output
    input_messages: List[Dict] = field(default_factory=list)
    output_message: Optional[Dict] = None
    
    # Tokens
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    
    # Cost
    cost_usd: float = 0
    
    # Performance
    time_to_first_token_ms: Optional[float] = None
    tokens_per_second: Optional[float] = None
    
    # Status
    status: SpanStatus = SpanStatus.PENDING
    error: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def end(self, success: bool = True, error: Optional[str] = None) -> None:
        """Finaliza o span."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = SpanStatus.SUCCESS if success else SpanStatus.ERROR
        self.error = error
        
        # Calcular tokens por segundo
        if self.tokens_output > 0 and self.duration_ms > 0:
            self.tokens_per_second = (self.tokens_output / self.duration_ms) * 1000
    
    def set_tokens(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """Define contagem de tokens."""
        self.tokens_input = input_tokens
        self.tokens_output = output_tokens
        self.tokens_total = input_tokens + output_tokens
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "traceId": self.trace_id,
            "parentId": self.parent_id,
            "name": self.name,
            "type": self.type.value,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "durationMs": self.duration_ms,
            "model": self.model,
            "provider": self.provider,
            "tokensInput": self.tokens_input,
            "tokensOutput": self.tokens_output,
            "tokensTotal": self.tokens_total,
            "costUsd": self.cost_usd,
            "timeToFirstTokenMs": self.time_to_first_token_ms,
            "tokensPerSecond": self.tokens_per_second,
            "status": self.status.value,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class LLMTrace:
    """
    Trace completo de uma interação LLM.
    
    Contém múltiplos spans representando cada etapa.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Contexto
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # Spans
    spans: List[LLMSpan] = field(default_factory=list)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0
    
    # Aggregates
    total_tokens: int = 0
    total_cost_usd: float = 0
    
    # Input/Output
    input: str = ""
    output: str = ""
    
    # Status
    status: SpanStatus = SpanStatus.PENDING
    
    # Tags
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_span(self, span: LLMSpan) -> None:
        """Adiciona span ao trace."""
        span.trace_id = self.id
        self.spans.append(span)
    
    def start_span(
        self,
        name: str,
        type: SpanType = SpanType.LLM_CALL,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> LLMSpan:
        """Cria e adiciona novo span."""
        span = LLMSpan(
            name=name,
            type=type,
            parent_id=parent_id,
            **kwargs
        )
        self.add_span(span)
        return span
    
    def end(self) -> None:
        """Finaliza o trace."""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        # Agregar métricas
        self.total_tokens = sum(s.tokens_total for s in self.spans)
        self.total_cost_usd = sum(s.cost_usd for s in self.spans)
        
        # Status baseado nos spans
        has_error = any(s.status == SpanStatus.ERROR for s in self.spans)
        self.status = SpanStatus.ERROR if has_error else SpanStatus.SUCCESS
    
    def get_llm_spans(self) -> List[LLMSpan]:
        """Obtém apenas spans de LLM."""
        return [s for s in self.spans if s.type == SpanType.LLM_CALL]
    
    def get_tool_spans(self) -> List[LLMSpan]:
        """Obtém spans de tool calls."""
        return [s for s in self.spans if s.type == SpanType.TOOL_CALL]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "conversationId": self.conversation_id,
            "spans": [s.to_dict() for s in self.spans],
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "totalDurationMs": self.total_duration_ms,
            "totalTokens": self.total_tokens,
            "totalCostUsd": self.total_cost_usd,
            "input": self.input,
            "output": self.output,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    def to_timeline(self) -> List[Dict]:
        """Converte para formato timeline/waterfall."""
        timeline = []
        
        for span in sorted(self.spans, key=lambda s: s.start_time):
            offset_ms = (span.start_time - self.start_time).total_seconds() * 1000
            
            timeline.append({
                "id": span.id,
                "name": span.name,
                "type": span.type.value,
                "offsetMs": offset_ms,
                "durationMs": span.duration_ms,
                "status": span.status.value,
                "model": span.model,
                "tokens": span.tokens_total,
            })
        
        return timeline


class LLMTraceCollector:
    """
    Coletor de traces LLM.
    """
    
    def __init__(self, max_traces: int = 10000):
        self._traces: Dict[str, LLMTrace] = {}
        self._active_traces: Dict[str, LLMTrace] = {}
        self._max_traces = max_traces
        self._lock = threading.RLock()
    
    def start_trace(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        input: str = "",
        **kwargs
    ) -> LLMTrace:
        """Inicia novo trace."""
        with self._lock:
            trace = LLMTrace(
                session_id=session_id,
                user_id=user_id,
                input=input,
                **kwargs
            )
            
            self._active_traces[trace.id] = trace
            return trace
    
    def end_trace(self, trace_id: str, output: str = "") -> Optional[LLMTrace]:
        """Finaliza trace."""
        with self._lock:
            trace = self._active_traces.pop(trace_id, None)
            if trace:
                trace.output = output
                trace.end()
                
                # Mover para traces finalizados
                self._traces[trace.id] = trace
                
                # Limpar traces antigos
                if len(self._traces) > self._max_traces:
                    oldest = sorted(self._traces.values(), key=lambda t: t.start_time)[:1000]
                    for t in oldest:
                        del self._traces[t.id]
                
                return trace
            return None
    
    def get_trace(self, trace_id: str) -> Optional[LLMTrace]:
        """Obtém trace por ID."""
        return self._traces.get(trace_id) or self._active_traces.get(trace_id)
    
    def list_traces(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LLMTrace]:
        """Lista traces."""
        traces = list(self._traces.values())
        
        if user_id:
            traces = [t for t in traces if t.user_id == user_id]
        if session_id:
            traces = [t for t in traces if t.session_id == session_id]
        
        # Ordenar por tempo desc
        traces = sorted(traces, key=lambda t: t.start_time, reverse=True)
        
        return traces[offset:offset + limit]
    
    def get_stats(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtém estatísticas."""
        traces = self.list_traces(user_id=user_id, limit=10000)
        
        if not traces:
            return {
                "totalTraces": 0,
                "totalTokens": 0,
                "totalCostUsd": 0,
                "avgDurationMs": 0,
            }
        
        return {
            "totalTraces": len(traces),
            "totalTokens": sum(t.total_tokens for t in traces),
            "totalCostUsd": sum(t.total_cost_usd for t in traces),
            "avgDurationMs": sum(t.total_duration_ms for t in traces) / len(traces),
            "successRate": len([t for t in traces if t.status == SpanStatus.SUCCESS]) / len(traces),
        }


# Singleton
_collector: Optional[LLMTraceCollector] = None


def get_trace_collector() -> LLMTraceCollector:
    """Obtém coletor de traces."""
    global _collector
    if _collector is None:
        _collector = LLMTraceCollector()
    return _collector

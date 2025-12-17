"""
Agent Traces - Rastreamento de execução de agentes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentSpanType(str, Enum):
    """Tipos de span de agente."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    RETRIEVAL = "retrieval"
    DECISION = "decision"
    DELEGATION = "delegation"
    ERROR = "error"
    CUSTOM = "custom"


class AgentSpanStatus(str, Enum):
    """Status do span."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class AgentSpan:
    """Span de execução de agente."""
    id: str = ""
    trace_id: str = ""
    parent_id: Optional[str] = None
    
    # Identificação
    name: str = ""
    type: AgentSpanType = AgentSpanType.CUSTOM
    agent_name: str = ""
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    
    # Input/Output
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    
    # Status
    status: AgentSpanStatus = AgentSpanStatus.PENDING
    error: Optional[str] = None
    
    # Métricas
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    # Metadata
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self, status: AgentSpanStatus = AgentSpanStatus.SUCCESS, error: Optional[str] = None):
        """Finaliza o span."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        if error:
            self.error = error
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Adiciona evento ao span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {},
        })
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "traceId": self.trace_id,
            "parentId": self.parent_id,
            "name": self.name,
            "type": self.type.value,
            "agentName": self.agent_name,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "durationMs": round(self.duration_ms, 2),
            "input": self.input_data,
            "output": self.output_data,
            "status": self.status.value,
            "error": self.error,
            "tokensUsed": self.tokens_used,
            "costUsd": round(self.cost_usd, 6),
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class AgentTrace:
    """Trace completo de execução de agente."""
    id: str = ""
    
    # Contexto
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # Agente
    agent_name: str = ""
    agent_version: Optional[str] = None
    
    # Spans
    spans: List[AgentSpan] = field(default_factory=list)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0
    
    # Input/Output
    input_message: str = ""
    output_message: str = ""
    
    # Métricas agregadas
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    llm_calls_count: int = 0
    tool_calls_count: int = 0
    
    # Status
    status: AgentSpanStatus = AgentSpanStatus.PENDING
    error: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_span(self, span: AgentSpan):
        """Adiciona span ao trace."""
        span.trace_id = self.id
        self.spans.append(span)
        
        # Atualizar métricas
        self.total_tokens += span.tokens_used
        self.total_cost_usd += span.cost_usd
        
        if span.type == AgentSpanType.LLM_CALL:
            self.llm_calls_count += 1
        elif span.type == AgentSpanType.TOOL_CALL:
            self.tool_calls_count += 1
    
    def finish(self, status: AgentSpanStatus = AgentSpanStatus.SUCCESS, error: Optional[str] = None):
        """Finaliza o trace."""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        if error:
            self.error = error
    
    def get_span_tree(self) -> List[Dict]:
        """Retorna spans como árvore hierárquica."""
        span_map = {s.id: s for s in self.spans}
        roots = []
        
        for span in self.spans:
            if not span.parent_id or span.parent_id not in span_map:
                roots.append(self._build_tree(span, span_map))
        
        return roots
    
    def _build_tree(self, span: AgentSpan, span_map: Dict[str, AgentSpan]) -> Dict:
        """Constrói subárvore de spans."""
        children = [
            self._build_tree(s, span_map)
            for s in self.spans
            if s.parent_id == span.id
        ]
        
        return {
            **span.to_dict(),
            "children": children,
        }
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "conversationId": self.conversation_id,
            "agentName": self.agent_name,
            "agentVersion": self.agent_version,
            "spans": [s.to_dict() for s in self.spans],
            "spanTree": self.get_span_tree(),
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "totalDurationMs": round(self.total_duration_ms, 2),
            "inputMessage": self.input_message,
            "outputMessage": self.output_message,
            "totalTokens": self.total_tokens,
            "totalCostUsd": round(self.total_cost_usd, 6),
            "llmCallsCount": self.llm_calls_count,
            "toolCallsCount": self.tool_calls_count,
            "status": self.status.value,
            "error": self.error,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class AgentTraceCollector:
    """Coletor de traces de agentes."""
    
    def __init__(self, max_traces: int = 10000):
        self._traces: Dict[str, AgentTrace] = {}
        self._active_traces: Dict[str, AgentTrace] = {}
        self._max_traces = max_traces
    
    def start_trace(
        self,
        agent_name: str,
        input_message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> AgentTrace:
        """Inicia novo trace."""
        trace = AgentTrace(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            input_message=input_message,
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
        )
        
        self._active_traces[trace.id] = trace
        return trace
    
    def start_span(
        self,
        trace_id: str,
        name: str,
        span_type: AgentSpanType,
        parent_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
    ) -> Optional[AgentSpan]:
        """Inicia novo span em um trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            logger.warning(f"Trace {trace_id} not found")
            return None
        
        span = AgentSpan(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            type=span_type,
            agent_name=trace.agent_name,
            input_data=input_data,
            status=AgentSpanStatus.RUNNING,
        )
        
        trace.add_span(span)
        return span
    
    def finish_span(
        self,
        trace_id: str,
        span_id: str,
        output_data: Optional[Dict] = None,
        status: AgentSpanStatus = AgentSpanStatus.SUCCESS,
        error: Optional[str] = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ):
        """Finaliza um span."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return
        
        for span in trace.spans:
            if span.id == span_id:
                span.output_data = output_data
                span.tokens_used = tokens_used
                span.cost_usd = cost_usd
                span.finish(status, error)
                
                # Atualizar métricas do trace
                trace.total_tokens += tokens_used
                trace.total_cost_usd += cost_usd
                break
    
    def finish_trace(
        self,
        trace_id: str,
        output_message: str,
        status: AgentSpanStatus = AgentSpanStatus.SUCCESS,
        error: Optional[str] = None,
    ):
        """Finaliza um trace."""
        trace = self._active_traces.pop(trace_id, None)
        if not trace:
            return
        
        trace.output_message = output_message
        trace.finish(status, error)
        
        # Armazenar trace finalizado
        self._traces[trace.id] = trace
        
        # Limpar traces antigos se necessário
        if len(self._traces) > self._max_traces:
            oldest = sorted(
                self._traces.values(),
                key=lambda t: t.start_time
            )[:len(self._traces) - self._max_traces]
            
            for t in oldest:
                del self._traces[t.id]
    
    def get_trace(self, trace_id: str) -> Optional[AgentTrace]:
        """Obtém trace por ID."""
        return self._traces.get(trace_id) or self._active_traces.get(trace_id)
    
    def list_traces(
        self,
        agent_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        status: Optional[AgentSpanStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AgentTrace]:
        """Lista traces com filtros."""
        traces = list(self._traces.values())
        
        if agent_name:
            traces = [t for t in traces if t.agent_name == agent_name]
        if user_id:
            traces = [t for t in traces if t.user_id == user_id]
        if session_id:
            traces = [t for t in traces if t.session_id == session_id]
        if status:
            traces = [t for t in traces if t.status == status]
        
        # Ordenar por data decrescente
        traces.sort(key=lambda t: t.start_time, reverse=True)
        
        return traces[offset:offset + limit]
    
    def get_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtém estatísticas de traces."""
        traces = list(self._traces.values())
        
        if agent_name:
            traces = [t for t in traces if t.agent_name == agent_name]
        
        if not traces:
            return {"count": 0}
        
        success_count = len([t for t in traces if t.status == AgentSpanStatus.SUCCESS])
        
        return {
            "count": len(traces),
            "successCount": success_count,
            "errorCount": len(traces) - success_count,
            "successRate": success_count / len(traces) if traces else 0,
            "avgDurationMs": sum(t.total_duration_ms for t in traces) / len(traces),
            "totalTokens": sum(t.total_tokens for t in traces),
            "totalCostUsd": sum(t.total_cost_usd for t in traces),
            "avgTokensPerTrace": sum(t.total_tokens for t in traces) / len(traces),
            "avgLlmCalls": sum(t.llm_calls_count for t in traces) / len(traces),
            "avgToolCalls": sum(t.tool_calls_count for t in traces) / len(traces),
        }


# Singleton
_collector: Optional[AgentTraceCollector] = None


def get_agent_trace_collector() -> AgentTraceCollector:
    """Obtém coletor de traces de agentes."""
    global _collector
    if _collector is None:
        _collector = AgentTraceCollector()
    return _collector

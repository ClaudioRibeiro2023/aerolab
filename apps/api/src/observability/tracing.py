"""
Observability - Sistema de Tracing Distribuído

Implementa tracing para acompanhar execuções de agentes,
workflows e chamadas de ferramentas.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                     Tracing System                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Trace       │  │ Span        │  │ Exporter    │         │
│  │ Context     │  │ Processor   │  │             │         │
│  │             │  │             │  │ - Console   │         │
│  │ - Trace ID  │→│ - Collect   │→│ - File      │         │
│  │ - Span ID   │  │ - Process   │  │ - OpenTel   │         │
│  │ - Baggage   │  │ - Export    │  │ - Custom    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘

Uso:
```python
from observability.tracing import Tracer, span

tracer = Tracer()

# Criar span
with tracer.start_span("agent_execution") as span:
    span.set_attribute("agent_name", "assistant")
    result = await agent.run(message)
    span.set_attribute("tokens", result.usage.total_tokens)

# Decorator
@span("tool_call")
async def execute_tool(name: str, args: dict):
    ...
```
"""

import asyncio
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict, List, Callable
from enum import Enum
import uuid
import json
import logging
import time
import threading


logger = logging.getLogger(__name__)


class SpanKind(str, Enum):
    """Tipo de span."""
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Status do span."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Contexto de um span para propagação."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SpanContext":
        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id"),
            baggage=data.get("baggage", {})
        )


@dataclass
class SpanEvent:
    """Evento dentro de um span."""
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes
        }


@dataclass
class Span:
    """
    Representa um span de tracing.
    
    Um span representa uma unidade de trabalho ou operação.
    """
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Status
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None
    
    # Atributos
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Eventos
    events: List[SpanEvent] = field(default_factory=list)
    
    # Links para outros spans
    links: List[SpanContext] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        """Duração em milissegundos."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0
    
    @property
    def is_recording(self) -> bool:
        """Se o span está gravando."""
        return self.end_time is None
    
    def set_attribute(self, key: str, value: Any) -> "Span":
        """Define um atributo."""
        self.attributes[key] = value
        return self
    
    def set_attributes(self, attributes: Dict[str, Any]) -> "Span":
        """Define múltiplos atributos."""
        self.attributes.update(attributes)
        return self
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> "Span":
        """Adiciona um evento."""
        event = SpanEvent(name=name, attributes=attributes or {})
        self.events.append(event)
        return self
    
    def set_status(
        self,
        status: SpanStatus,
        message: Optional[str] = None
    ) -> "Span":
        """Define status do span."""
        self.status = status
        self.status_message = message
        return self
    
    def record_exception(
        self,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ) -> "Span":
        """Registra uma exceção."""
        self.set_status(SpanStatus.ERROR, str(exception))
        
        event_attrs = {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
            **(attributes or {})
        }
        
        self.add_event("exception", event_attrs)
        return self
    
    def end(self) -> None:
        """Finaliza o span."""
        if self.is_recording:
            self.end_time = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "context": self.context.to_dict(),
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [e.to_dict() for e in self.events],
            "links": [l.to_dict() for l in self.links]
        }


@dataclass
class Trace:
    """
    Representa um trace completo.
    
    Um trace é uma coleção de spans relacionados.
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    spans: List[Span] = field(default_factory=list)
    
    # Metadados
    service_name: str = "agno"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def root_span(self) -> Optional[Span]:
        """Retorna span raiz."""
        for span in self.spans:
            if not span.context.parent_span_id:
                return span
        return self.spans[0] if self.spans else None
    
    @property
    def duration_ms(self) -> float:
        """Duração total do trace."""
        if not self.spans:
            return 0
        
        start = min(s.start_time for s in self.spans)
        end = max(s.end_time or datetime.now() for s in self.spans)
        return (end - start).total_seconds() * 1000
    
    def add_span(self, span: Span) -> None:
        """Adiciona span ao trace."""
        self.spans.append(span)
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "service_name": self.service_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans]
        }


class SpanExporter:
    """Base class para exportadores de spans."""
    
    def export(self, spans: List[Span]) -> None:
        """Exporta spans."""
        raise NotImplementedError
    
    def shutdown(self) -> None:
        """Finaliza exportador."""
        pass


class ConsoleSpanExporter(SpanExporter):
    """Exporta spans para console."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def export(self, spans: List[Span]) -> None:
        for span in spans:
            status_icon = "✓" if span.status == SpanStatus.OK else "✗" if span.status == SpanStatus.ERROR else "○"
            print(f"[{status_icon}] {span.name} ({span.duration_ms:.2f}ms)")
            
            if self.verbose:
                for key, value in span.attributes.items():
                    print(f"    {key}: {value}")


class FileSpanExporter(SpanExporter):
    """Exporta spans para arquivo JSON."""
    
    def __init__(self, file_path: str = "traces.jsonl"):
        self.file_path = file_path
    
    def export(self, spans: List[Span]) -> None:
        with open(self.file_path, "a") as f:
            for span in spans:
                f.write(json.dumps(span.to_dict(), default=str) + "\n")


class InMemorySpanExporter(SpanExporter):
    """Armazena spans em memória para consulta."""
    
    def __init__(self, max_spans: int = 1000):
        self.max_spans = max_spans
        self.spans: List[Span] = []
        self._lock = threading.Lock()
    
    def export(self, spans: List[Span]) -> None:
        with self._lock:
            self.spans.extend(spans)
            # Manter apenas os últimos N spans
            if len(self.spans) > self.max_spans:
                self.spans = self.spans[-self.max_spans:]
    
    def get_spans(
        self,
        trace_id: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 100
    ) -> List[Span]:
        """Obtém spans filtrados."""
        with self._lock:
            result = self.spans
            
            if trace_id:
                result = [s for s in result if s.context.trace_id == trace_id]
            
            if name:
                result = [s for s in result if name in s.name]
            
            return result[-limit:]
    
    def get_traces(self, limit: int = 10) -> List[Trace]:
        """Agrupa spans em traces."""
        with self._lock:
            traces_dict: Dict[str, Trace] = {}
            
            for span in self.spans:
                trace_id = span.context.trace_id
                if trace_id not in traces_dict:
                    traces_dict[trace_id] = Trace(trace_id=trace_id)
                traces_dict[trace_id].add_span(span)
            
            return list(traces_dict.values())[-limit:]
    
    def clear(self) -> None:
        """Limpa spans armazenados."""
        with self._lock:
            self.spans.clear()


# Thread-local para contexto atual
_current_context = threading.local()


class Tracer:
    """
    Tracer principal para criação de spans.
    
    Uso:
    ```python
    tracer = Tracer()
    
    with tracer.start_span("operation") as span:
        span.set_attribute("key", "value")
        # ... operação ...
    
    # Async
    async with tracer.start_async_span("async_op") as span:
        await async_operation()
    ```
    """
    
    def __init__(
        self,
        service_name: str = "agno",
        exporters: Optional[List[SpanExporter]] = None
    ):
        self.service_name = service_name
        self.exporters = exporters or [InMemorySpanExporter()]
        
        # Traces ativos
        self._active_traces: Dict[str, Trace] = {}
    
    def _generate_id(self) -> str:
        """Gera ID único."""
        return str(uuid.uuid4()).replace("-", "")[:16]
    
    def get_current_span(self) -> Optional[Span]:
        """Obtém span atual do contexto."""
        return getattr(_current_context, "span", None)
    
    def get_current_context(self) -> Optional[SpanContext]:
        """Obtém contexto atual."""
        span = self.get_current_span()
        return span.context if span else None
    
    @contextmanager
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        links: Optional[List[SpanContext]] = None
    ):
        """
        Inicia um novo span.
        
        Args:
            name: Nome do span
            kind: Tipo do span
            attributes: Atributos iniciais
            links: Links para outros spans
            
        Yields:
            Span ativo
        """
        # Contexto pai
        parent_context = self.get_current_context()
        
        # Criar contexto do span
        if parent_context:
            context = SpanContext(
                trace_id=parent_context.trace_id,
                span_id=self._generate_id(),
                parent_span_id=parent_context.span_id,
                baggage=parent_context.baggage.copy()
            )
        else:
            context = SpanContext(
                trace_id=self._generate_id(),
                span_id=self._generate_id()
            )
        
        # Criar span
        span = Span(
            name=name,
            context=context,
            kind=kind,
            attributes=attributes or {},
            links=links or []
        )
        
        # Definir como span atual
        previous_span = getattr(_current_context, "span", None)
        _current_context.span = span
        
        try:
            yield span
            if span.status == SpanStatus.UNSET:
                span.set_status(SpanStatus.OK)
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.end()
            _current_context.span = previous_span
            
            # Exportar
            for exporter in self.exporters:
                try:
                    exporter.export([span])
                except Exception as e:
                    logger.error(f"Failed to export span: {e}")
    
    @asynccontextmanager
    async def start_async_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Versão assíncrona de start_span."""
        with self.start_span(name, kind, attributes) as span:
            yield span
    
    def create_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL
    ) -> Span:
        """Cria span sem context manager."""
        parent_context = self.get_current_context()
        
        if parent_context:
            context = SpanContext(
                trace_id=parent_context.trace_id,
                span_id=self._generate_id(),
                parent_span_id=parent_context.span_id
            )
        else:
            context = SpanContext(
                trace_id=self._generate_id(),
                span_id=self._generate_id()
            )
        
        return Span(name=name, context=context, kind=kind)
    
    def get_memory_exporter(self) -> Optional[InMemorySpanExporter]:
        """Obtém exportador em memória se existir."""
        for exp in self.exporters:
            if isinstance(exp, InMemorySpanExporter):
                return exp
        return None


def span(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator para criar span automaticamente.
    
    Uso:
    ```python
    @span("my_operation")
    def my_function():
        ...
    
    @span()  # Usa nome da função
    async def async_function():
        ...
    ```
    """
    def decorator(func: Callable):
        span_name = name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer()
                async with tracer.start_async_span(span_name, kind, attributes) as s:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                tracer = get_tracer()
                with tracer.start_span(span_name, kind, attributes) as s:
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


# Singleton
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Retorna o tracer singleton."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(
            exporters=[
                InMemorySpanExporter(max_spans=10000),
                ConsoleSpanExporter(verbose=False)
            ]
        )
    return _tracer


def configure_tracer(
    service_name: str = "agno",
    exporters: Optional[List[SpanExporter]] = None
) -> Tracer:
    """Configura o tracer global."""
    global _tracer
    _tracer = Tracer(service_name=service_name, exporters=exporters)
    return _tracer

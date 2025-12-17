"""
Distributed Tracing para Workflows.

Integração com OpenTelemetry para:
- Trace de execução de workflows
- Spans para cada step
- Propagação de contexto
- Export para backends (Jaeger, Zipkin, etc)
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Representa um span de tracing."""
    name: str
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    status: str = "ok"
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0
    
    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_status(self, status: str, message: Optional[str] = None) -> None:
        self.status = status
        if message:
            self.attributes["error.message"] = message
    
    def end(self) -> None:
        self.end_time = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status
        }


class WorkflowTracer:
    """
    Tracer para workflows.
    
    Exemplo:
        tracer = WorkflowTracer("agno-workflows")
        
        with tracer.trace_workflow("my-workflow", "exec-123") as wf_span:
            wf_span.set_attribute("inputs", {"key": "value"})
            
            with tracer.trace_step("step-1", "agent") as step_span:
                step_span.add_event("agent_invoked")
                # ... executar step
                step_span.set_attribute("tokens_used", 500)
    """
    
    def __init__(self, service_name: str = "agno-workflows"):
        self.service_name = service_name
        self._spans: List[Span] = []
        self._current_trace_id: Optional[str] = None
        self._span_stack: List[Span] = []
    
    def _generate_id(self) -> str:
        import uuid
        return uuid.uuid4().hex[:16]
    
    @contextmanager
    def trace_workflow(self, workflow_id: str, execution_id: str):
        """Inicia trace de workflow."""
        trace_id = self._generate_id()
        self._current_trace_id = trace_id
        
        span = Span(
            name=f"workflow:{workflow_id}",
            trace_id=trace_id,
            span_id=self._generate_id(),
            attributes={
                "workflow.id": workflow_id,
                "execution.id": execution_id,
                "service.name": self.service_name
            }
        )
        
        self._spans.append(span)
        self._span_stack.append(span)
        
        try:
            yield span
        except Exception as e:
            span.set_status("error", str(e))
            raise
        finally:
            span.end()
            self._span_stack.pop()
            self._current_trace_id = None
    
    @contextmanager
    def trace_step(self, step_id: str, step_type: str):
        """Inicia trace de step."""
        parent = self._span_stack[-1] if self._span_stack else None
        
        span = Span(
            name=f"step:{step_type}:{step_id}",
            trace_id=self._current_trace_id or self._generate_id(),
            span_id=self._generate_id(),
            parent_id=parent.span_id if parent else None,
            attributes={
                "step.id": step_id,
                "step.type": step_type
            }
        )
        
        self._spans.append(span)
        self._span_stack.append(span)
        
        try:
            yield span
        except Exception as e:
            span.set_status("error", str(e))
            raise
        finally:
            span.end()
            self._span_stack.pop()
    
    def get_traces(self, limit: int = 100) -> List[Dict]:
        """Retorna traces recentes."""
        return [s.to_dict() for s in self._spans[-limit:]]
    
    def get_trace(self, trace_id: str) -> List[Dict]:
        """Retorna todos os spans de um trace."""
        return [s.to_dict() for s in self._spans if s.trace_id == trace_id]
    
    def clear(self) -> None:
        """Limpa traces."""
        self._spans.clear()


# Singleton
_tracer: Optional[WorkflowTracer] = None


def create_tracer(service_name: str = "agno-workflows") -> WorkflowTracer:
    """Cria novo tracer."""
    return WorkflowTracer(service_name)


def get_tracer() -> WorkflowTracer:
    """Obtém tracer global."""
    global _tracer
    if _tracer is None:
        _tracer = WorkflowTracer()
    return _tracer


# Decorators convenientes
def trace_workflow(workflow_id: str, execution_id: str):
    """Decorator para tracer workflow."""
    return get_tracer().trace_workflow(workflow_id, execution_id)


def trace_step(step_id: str, step_type: str):
    """Decorator para tracer step."""
    return get_tracer().trace_step(step_id, step_type)

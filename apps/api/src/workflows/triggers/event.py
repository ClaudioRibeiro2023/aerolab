"""
Event Trigger - Dispara workflows via eventos do sistema.

Features:
- Event bus in-memory e Redis
- Pattern matching de eventos
- Filtros por payload
- Debounce/throttle
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable, Awaitable, Set
from dataclasses import dataclass, field
import logging
import re
import threading

from .base import BaseTrigger, TriggerConfig, TriggerResult, TriggerType

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEvent:
    """Representa um evento do sistema."""
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowEvent":
        return cls(
            id=data.get("id", f"evt_{datetime.now().timestamp()}"),
            event_type=data.get("event_type", ""),
            data=data.get("data", {}),
            source=data.get("source", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        )


@dataclass
class EventFilter:
    """Filtro para eventos."""
    event_types: List[str] = field(default_factory=list)  # Patterns (suporta *)
    source_pattern: Optional[str] = None
    data_conditions: Dict[str, Any] = field(default_factory=dict)  # data.field == value
    
    def matches(self, event: WorkflowEvent) -> bool:
        """Verifica se evento match o filtro."""
        # Verificar tipo
        if self.event_types:
            type_matched = any(
                self._pattern_matches(pattern, event.event_type)
                for pattern in self.event_types
            )
            if not type_matched:
                return False
        
        # Verificar source
        if self.source_pattern:
            if not self._pattern_matches(self.source_pattern, event.source):
                return False
        
        # Verificar condições de data
        for key, expected in self.data_conditions.items():
            actual = event.data.get(key)
            if actual != expected:
                return False
        
        return True
    
    def _pattern_matches(self, pattern: str, value: str) -> bool:
        """Match pattern com suporte a wildcards."""
        if pattern == "*":
            return True
        if "*" in pattern:
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex}$", value))
        return pattern == value
    
    def to_dict(self) -> Dict:
        return {
            "event_types": self.event_types,
            "source_pattern": self.source_pattern,
            "data_conditions": self.data_conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EventFilter":
        return cls(
            event_types=data.get("event_types", []),
            source_pattern=data.get("source_pattern"),
            data_conditions=data.get("data_conditions", {})
        )


EventHandler = Callable[[WorkflowEvent], Awaitable[None]]


class EventBus:
    """
    Event bus para comunicação entre componentes.
    
    Suporta:
    - Pub/Sub de eventos
    - Pattern matching
    - Múltiplos subscribers
    - Histórico de eventos
    
    Exemplo:
        bus = EventBus()
        
        # Subscribe
        async def on_user_created(event):
            print(f"User created: {event.data}")
        
        bus.subscribe("user.created", on_user_created)
        
        # Publish
        await bus.emit(WorkflowEvent(
            event_type="user.created",
            data={"user_id": "123", "email": "user@example.com"}
        ))
    """
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "EventBus":
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._filters: Dict[str, EventFilter] = {}
        self._history: List[WorkflowEvent] = []
        self._max_history = 1000
        self._initialized = True
    
    def subscribe(
        self,
        event_pattern: str,
        handler: EventHandler,
        event_filter: Optional[EventFilter] = None
    ) -> str:
        """
        Subscribe a um padrão de evento.
        
        Args:
            event_pattern: Padrão de evento (suporta *)
            handler: Função async a chamar
            event_filter: Filtro adicional opcional
        
        Returns:
            Subscription ID
        """
        sub_id = f"sub_{len(self._subscribers)}_{datetime.now().timestamp()}"
        
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        
        self._subscribers[event_pattern].append(handler)
        
        if event_filter:
            self._filters[sub_id] = event_filter
        
        logger.debug(f"Subscribed to {event_pattern}: {sub_id}")
        return sub_id
    
    def unsubscribe(self, pattern: str, handler: EventHandler) -> bool:
        """Remove subscription."""
        if pattern in self._subscribers:
            try:
                self._subscribers[pattern].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    async def emit(self, event: WorkflowEvent) -> int:
        """
        Emite um evento.
        
        Args:
            event: Evento a emitir
            
        Returns:
            Número de handlers notificados
        """
        # Adicionar ao histórico
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        notified = 0
        
        for pattern, handlers in self._subscribers.items():
            if self._matches_pattern(pattern, event.event_type):
                for handler in handlers:
                    try:
                        await handler(event)
                        notified += 1
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
        
        logger.debug(f"Event {event.event_type} emitted to {notified} handlers")
        return notified
    
    def emit_sync(self, event: WorkflowEvent) -> None:
        """Emite evento de forma síncrona (cria task)."""
        asyncio.create_task(self.emit(event))
    
    async def wait_for(
        self,
        event_type: str,
        timeout: Optional[float] = None,
        filter_fn: Optional[Callable[[WorkflowEvent], bool]] = None
    ) -> Optional[WorkflowEvent]:
        """
        Aguarda um evento específico.
        
        Args:
            event_type: Tipo de evento
            timeout: Timeout em segundos
            filter_fn: Função para filtrar eventos
            
        Returns:
            Evento recebido ou None se timeout
        """
        event_received: Optional[WorkflowEvent] = None
        event_flag = asyncio.Event()
        
        async def handler(event: WorkflowEvent):
            nonlocal event_received
            if filter_fn is None or filter_fn(event):
                event_received = event
                event_flag.set()
        
        self.subscribe(event_type, handler)
        
        try:
            await asyncio.wait_for(event_flag.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        finally:
            self.unsubscribe(event_type, handler)
        
        return event_received
    
    def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowEvent]:
        """Retorna histórico de eventos."""
        events = self._history
        
        if event_type:
            events = [e for e in events if self._matches_pattern(event_type, e.event_type)]
        
        return events[-limit:]
    
    def _matches_pattern(self, pattern: str, event_type: str) -> bool:
        """Verifica se event_type matches pattern."""
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix)
        if "*" in pattern:
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex}$", event_type))
        return pattern == event_type
    
    def clear_history(self) -> None:
        """Limpa histórico de eventos."""
        self._history.clear()


# Singleton
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Obtém event bus global."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


class EventTrigger(BaseTrigger):
    """
    Trigger que dispara quando eventos específicos ocorrem.
    
    Exemplo:
        trigger = EventTrigger(TriggerConfig(
            id="on-user-signup",
            name="On User Signup",
            workflow_id="welcome-email",
            config={
                "event_types": ["user.created", "user.registered"],
                "data_conditions": {"source": "website"}
            }
        ))
    """
    
    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.event_filter = EventFilter.from_dict(config.config)
        self._bus = get_event_bus()
        self._handler: Optional[EventHandler] = None
    
    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.EVENT
    
    async def start(self) -> None:
        """Inicia listening de eventos."""
        async def handler(event: WorkflowEvent):
            if self.event_filter.matches(event):
                await self.trigger(
                    inputs=event.data,
                    metadata={
                        "event_id": event.id,
                        "event_type": event.event_type,
                        "source": event.source
                    }
                )
        
        self._handler = handler
        
        # Subscribe a todos os patterns
        for pattern in self.event_filter.event_types or ["*"]:
            self._bus.subscribe(pattern, handler)
        
        logger.info(f"Event trigger {self.config.id} started for types: {self.event_filter.event_types}")
    
    async def stop(self) -> None:
        """Para listening de eventos."""
        if self._handler:
            for pattern in self.event_filter.event_types or ["*"]:
                self._bus.unsubscribe(pattern, self._handler)
            self._handler = None
        
        logger.info(f"Event trigger {self.config.id} stopped")
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.event_filter.event_types:
            errors.append("event_types is required")
        return errors


# Event types padrão
class SystemEvents:
    """Eventos padrão do sistema."""
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # Step events
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    
    # Agent events
    AGENT_INVOKED = "agent.invoked"
    AGENT_RESPONSE = "agent.response"
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"

"""
Base classes para Triggers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class TriggerType(Enum):
    """Tipos de trigger."""
    MANUAL = "manual"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EVENT = "event"
    FILE_WATCH = "file_watch"
    API_POLL = "api_poll"


class TriggerStatus(Enum):
    """Status do trigger."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class TriggerConfig:
    """Configuração base de trigger."""
    id: str = field(default_factory=lambda: f"trigger_{uuid.uuid4().hex[:8]}")
    name: str = ""
    workflow_id: str = ""
    trigger_type: TriggerType = TriggerType.MANUAL
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "trigger_type": self.trigger_type.value,
            "enabled": self.enabled,
            "config": self.config,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TriggerConfig":
        return cls(
            id=data.get("id", f"trigger_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", ""),
            workflow_id=data.get("workflow_id", ""),
            trigger_type=TriggerType(data.get("trigger_type", "manual")),
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )


@dataclass
class TriggerResult:
    """Resultado de um trigger."""
    trigger_id: str
    workflow_id: str
    triggered_at: datetime = field(default_factory=datetime.now)
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "trigger_id": self.trigger_id,
            "workflow_id": self.workflow_id,
            "triggered_at": self.triggered_at.isoformat(),
            "inputs": self.inputs,
            "metadata": self.metadata,
            "execution_id": self.execution_id,
            "success": self.success,
            "error": self.error
        }


class BaseTrigger(ABC):
    """
    Classe base para triggers.
    
    Um trigger monitora alguma condição e dispara
    a execução de um workflow quando a condição é satisfeita.
    """
    
    def __init__(self, config: TriggerConfig):
        self.config = config
        self._status = TriggerStatus.ACTIVE if config.enabled else TriggerStatus.DISABLED
        self._callback: Optional[Callable[[TriggerResult], Awaitable[None]]] = None
        self._history: List[TriggerResult] = []
    
    @property
    @abstractmethod
    def trigger_type(self) -> TriggerType:
        """Tipo do trigger."""
        pass
    
    @property
    def status(self) -> TriggerStatus:
        """Status atual do trigger."""
        return self._status
    
    @property
    def is_active(self) -> bool:
        """Se o trigger está ativo."""
        return self._status == TriggerStatus.ACTIVE
    
    def set_callback(self, callback: Callable[[TriggerResult], Awaitable[None]]) -> None:
        """Define callback para quando trigger disparar."""
        self._callback = callback
    
    @abstractmethod
    async def start(self) -> None:
        """Inicia o trigger."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Para o trigger."""
        pass
    
    async def trigger(self, inputs: Optional[Dict] = None, metadata: Optional[Dict] = None) -> TriggerResult:
        """Dispara o trigger manualmente."""
        result = TriggerResult(
            trigger_id=self.config.id,
            workflow_id=self.config.workflow_id,
            inputs=inputs or {},
            metadata=metadata or {}
        )
        
        self._history.append(result)
        
        if self._callback:
            try:
                await self._callback(result)
            except Exception as e:
                result.success = False
                result.error = str(e)
        
        return result
    
    def pause(self) -> None:
        """Pausa o trigger."""
        self._status = TriggerStatus.PAUSED
    
    def resume(self) -> None:
        """Resume o trigger."""
        if self.config.enabled:
            self._status = TriggerStatus.ACTIVE
    
    def disable(self) -> None:
        """Desabilita o trigger."""
        self._status = TriggerStatus.DISABLED
        self.config.enabled = False
    
    def enable(self) -> None:
        """Habilita o trigger."""
        self._status = TriggerStatus.ACTIVE
        self.config.enabled = True
    
    def get_history(self, limit: int = 10) -> List[TriggerResult]:
        """Retorna histórico de disparos."""
        return self._history[-limit:]
    
    def validate(self) -> List[str]:
        """Valida configuração do trigger."""
        errors = []
        if not self.config.workflow_id:
            errors.append("workflow_id is required")
        return errors

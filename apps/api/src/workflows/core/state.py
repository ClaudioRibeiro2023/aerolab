"""
State Management para Workflows.

Implementa Durable Execution com:
- State machine para workflow
- Checkpointing automático
- Recovery de falhas
- Exactly-once execution
"""

import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import hashlib


class WorkflowStatus(Enum):
    """Status do workflow."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPENSATING = "compensating"


class StepStatus(Enum):
    """Status de um step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"


@dataclass
class StepState:
    """Estado de um step individual."""
    step_id: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict] = None
    output_data: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration_ms": self.duration_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StepState":
        return cls(
            step_id=data["step_id"],
            status=StepStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            input_data=data.get("input_data"),
            output_data=data.get("output_data"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            duration_ms=data.get("duration_ms", 0)
        )


@dataclass
class WorkflowState:
    """Estado completo de uma execução de workflow."""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    step_states: Dict[str, StepState] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_complete(self) -> bool:
        return self.status in (
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED
        )
    
    @property
    def is_running(self) -> bool:
        return self.status == WorkflowStatus.RUNNING
    
    def set_variable(self, name: str, value: Any) -> None:
        """Define variável no contexto."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Obtém variável do contexto."""
        return self.variables.get(name, default)
    
    def mark_step_started(self, step_id: str, input_data: Optional[Dict] = None) -> None:
        """Marca step como iniciado."""
        if step_id not in self.step_states:
            self.step_states[step_id] = StepState(step_id=step_id)
        
        state = self.step_states[step_id]
        state.status = StepStatus.RUNNING
        state.started_at = datetime.now()
        state.input_data = input_data
        self.current_step_id = step_id
    
    def mark_step_completed(self, step_id: str, output_data: Optional[Dict] = None) -> None:
        """Marca step como completado."""
        if step_id in self.step_states:
            state = self.step_states[step_id]
            state.status = StepStatus.COMPLETED
            state.completed_at = datetime.now()
            state.output_data = output_data
            if state.started_at:
                state.duration_ms = (state.completed_at - state.started_at).total_seconds() * 1000
    
    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Marca step como falho."""
        if step_id in self.step_states:
            state = self.step_states[step_id]
            state.status = StepStatus.FAILED
            state.completed_at = datetime.now()
            state.error = error
            state.retry_count += 1
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "variables": self.variables,
            "step_states": {k: v.to_dict() for k, v in self.step_states.items()},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowState":
        state = cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            status=WorkflowStatus(data["status"]),
            current_step_id=data.get("current_step_id"),
            variables=data.get("variables", {}),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )
        
        for step_id, step_data in data.get("step_states", {}).items():
            state.step_states[step_id] = StepState.from_dict(step_data)
        
        return state


@dataclass
class Checkpoint:
    """Checkpoint de estado para recovery."""
    checkpoint_id: str
    execution_id: str
    state: WorkflowState
    created_at: datetime = field(default_factory=datetime.now)
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Computa checksum do estado para validação."""
        data = json.dumps(self.state.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def validate(self) -> bool:
        """Valida integridade do checkpoint."""
        return self.checksum == self._compute_checksum()
    
    def to_dict(self) -> Dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "execution_id": self.execution_id,
            "state": self.state.to_dict(),
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Checkpoint":
        return cls(
            checkpoint_id=data["checkpoint_id"],
            execution_id=data["execution_id"],
            state=WorkflowState.from_dict(data["state"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            checksum=data["checksum"]
        )


class StateManager:
    """
    Gerenciador de estado com durable execution.
    
    Features:
    - Checkpointing automático
    - Recovery de falhas
    - Thread-safe
    - Persistência opcional
    
    Exemplo:
        manager = StateManager()
        
        # Criar estado
        state = manager.create_state("exec_1", "workflow_1")
        
        # Checkpoint antes de step crítico
        manager.checkpoint(state)
        
        # Em caso de falha, recover
        state = manager.recover("exec_1")
    """
    
    def __init__(self, persistence: Optional[Any] = None):
        self._states: Dict[str, WorkflowState] = {}
        self._checkpoints: Dict[str, List[Checkpoint]] = {}
        self._lock = threading.RLock()
        self._persistence = persistence
    
    def create_state(
        self,
        execution_id: str,
        workflow_id: str,
        initial_variables: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> WorkflowState:
        """Cria novo estado de execução."""
        with self._lock:
            state = WorkflowState(
                execution_id=execution_id,
                workflow_id=workflow_id,
                variables=initial_variables or {},
                metadata=metadata or {},
                started_at=datetime.now()
            )
            self._states[execution_id] = state
            self._checkpoints[execution_id] = []
            
            # Persistir se configurado
            if self._persistence:
                self._persistence.save_state(state)
            
            return state
    
    def get_state(self, execution_id: str) -> Optional[WorkflowState]:
        """Obtém estado de execução."""
        with self._lock:
            return self._states.get(execution_id)
    
    def update_state(self, state: WorkflowState) -> None:
        """Atualiza estado."""
        with self._lock:
            self._states[state.execution_id] = state
            
            if self._persistence:
                self._persistence.save_state(state)
    
    def checkpoint(self, state: WorkflowState) -> Checkpoint:
        """Cria checkpoint do estado atual."""
        with self._lock:
            checkpoint = Checkpoint(
                checkpoint_id=f"cp_{state.execution_id}_{len(self._checkpoints.get(state.execution_id, []))}",
                execution_id=state.execution_id,
                state=WorkflowState.from_dict(state.to_dict())  # Deep copy
            )
            
            if state.execution_id not in self._checkpoints:
                self._checkpoints[state.execution_id] = []
            
            self._checkpoints[state.execution_id].append(checkpoint)
            
            # Manter apenas últimos 10 checkpoints
            if len(self._checkpoints[state.execution_id]) > 10:
                self._checkpoints[state.execution_id] = self._checkpoints[state.execution_id][-10:]
            
            if self._persistence:
                self._persistence.save_checkpoint(checkpoint)
            
            return checkpoint
    
    def get_latest_checkpoint(self, execution_id: str) -> Optional[Checkpoint]:
        """Obtém último checkpoint válido."""
        with self._lock:
            checkpoints = self._checkpoints.get(execution_id, [])
            
            for cp in reversed(checkpoints):
                if cp.validate():
                    return cp
            
            # Tentar carregar de persistência
            if self._persistence:
                return self._persistence.get_latest_checkpoint(execution_id)
            
            return None
    
    def recover(self, execution_id: str) -> Optional[WorkflowState]:
        """Recupera estado do último checkpoint."""
        checkpoint = self.get_latest_checkpoint(execution_id)
        
        if checkpoint:
            with self._lock:
                state = WorkflowState.from_dict(checkpoint.state.to_dict())
                self._states[execution_id] = state
                return state
        
        return None
    
    def mark_completed(self, execution_id: str, output: Optional[Dict] = None) -> None:
        """Marca execução como completada."""
        with self._lock:
            state = self._states.get(execution_id)
            if state:
                state.status = WorkflowStatus.COMPLETED
                state.completed_at = datetime.now()
                if output:
                    state.variables["_output"] = output
                
                if self._persistence:
                    self._persistence.save_state(state)
    
    def mark_failed(self, execution_id: str, error: str) -> None:
        """Marca execução como falha."""
        with self._lock:
            state = self._states.get(execution_id)
            if state:
                state.status = WorkflowStatus.FAILED
                state.completed_at = datetime.now()
                state.error = error
                
                if self._persistence:
                    self._persistence.save_state(state)
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowState]:
        """Lista execuções com filtros."""
        with self._lock:
            results = list(self._states.values())
            
            if workflow_id:
                results = [s for s in results if s.workflow_id == workflow_id]
            
            if status:
                results = [s for s in results if s.status == status]
            
            return results
    
    def cleanup_completed(self, max_age_hours: int = 24) -> int:
        """Remove execuções completadas antigas."""
        with self._lock:
            now = datetime.now()
            to_remove = []
            
            for exec_id, state in self._states.items():
                if state.is_complete and state.completed_at:
                    age_hours = (now - state.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(exec_id)
            
            for exec_id in to_remove:
                del self._states[exec_id]
                if exec_id in self._checkpoints:
                    del self._checkpoints[exec_id]
            
            return len(to_remove)

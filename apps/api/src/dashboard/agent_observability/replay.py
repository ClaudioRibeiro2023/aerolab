"""
Execution Replay - Replay de execuções de agentes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReplayStepType(str, Enum):
    """Tipos de step de replay."""
    INPUT = "input"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    DECISION = "decision"
    OUTPUT = "output"
    ERROR = "error"


@dataclass
class ReplayStep:
    """Step de replay."""
    id: str = ""
    index: int = 0
    type: ReplayStepType = ReplayStepType.INPUT
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    
    # Conteúdo
    title: str = ""
    content: Any = None
    
    # Contexto
    agent_name: Optional[str] = None
    span_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "index": self.index,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "durationMs": round(self.duration_ms, 2),
            "title": self.title,
            "content": self.content,
            "agentName": self.agent_name,
            "spanId": self.span_id,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionReplay:
    """Replay de uma execução de agente."""
    id: str = ""
    trace_id: str = ""
    
    # Agente
    agent_name: str = ""
    
    # Steps
    steps: List[ReplayStep] = field(default_factory=list)
    current_step: int = 0
    
    # Timing
    total_duration_ms: float = 0
    
    # Input/Output
    input_message: str = ""
    output_message: str = ""
    
    # Status
    is_playing: bool = False
    playback_speed: float = 1.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_step(
        self,
        step_type: ReplayStepType,
        title: str,
        content: Any,
        duration_ms: float = 0,
        metadata: Optional[Dict] = None,
    ):
        """Adiciona step ao replay."""
        step = ReplayStep(
            id=f"step_{len(self.steps)}",
            index=len(self.steps),
            type=step_type,
            title=title,
            content=content,
            duration_ms=duration_ms,
            agent_name=self.agent_name,
            metadata=metadata or {},
        )
        self.steps.append(step)
        self.total_duration_ms += duration_ms
    
    def get_step(self, index: int) -> Optional[ReplayStep]:
        """Obtém step por índice."""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None
    
    def next_step(self) -> Optional[ReplayStep]:
        """Avança para próximo step."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            return self.steps[self.current_step]
        return None
    
    def previous_step(self) -> Optional[ReplayStep]:
        """Volta para step anterior."""
        if self.current_step > 0:
            self.current_step -= 1
            return self.steps[self.current_step]
        return None
    
    def go_to_step(self, index: int) -> Optional[ReplayStep]:
        """Vai para step específico."""
        if 0 <= index < len(self.steps):
            self.current_step = index
            return self.steps[index]
        return None
    
    def reset(self):
        """Reseta replay para início."""
        self.current_step = 0
        self.is_playing = False
    
    def get_progress(self) -> float:
        """Obtém progresso (0-1)."""
        if len(self.steps) == 0:
            return 0
        return self.current_step / (len(self.steps) - 1)
    
    def get_elapsed_time_ms(self) -> float:
        """Obtém tempo decorrido até step atual."""
        return sum(
            s.duration_ms for s in self.steps[:self.current_step + 1]
        )
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "traceId": self.trace_id,
            "agentName": self.agent_name,
            "steps": [s.to_dict() for s in self.steps],
            "currentStep": self.current_step,
            "totalSteps": len(self.steps),
            "totalDurationMs": round(self.total_duration_ms, 2),
            "elapsedTimeMs": round(self.get_elapsed_time_ms(), 2),
            "progress": round(self.get_progress(), 4),
            "inputMessage": self.input_message,
            "outputMessage": self.output_message,
            "isPlaying": self.is_playing,
            "playbackSpeed": self.playback_speed,
            "createdAt": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_trace(cls, trace: Any) -> "ExecutionReplay":
        """Cria replay a partir de um trace de agente."""
        replay = cls(
            id=f"replay_{trace.id}",
            trace_id=trace.id,
            agent_name=trace.agent_name,
            input_message=trace.input_message,
            output_message=trace.output_message,
            total_duration_ms=trace.total_duration_ms,
        )
        
        # Adicionar step de input
        replay.add_step(
            ReplayStepType.INPUT,
            "User Input",
            trace.input_message,
            0,
        )
        
        # Converter spans em steps
        for span in trace.spans:
            step_type = cls._span_type_to_step_type(span.type.value)
            
            content = {
                "input": span.input_data,
                "output": span.output_data,
            }
            
            if span.type.value == "llm_call":
                # Separar request e response
                replay.add_step(
                    ReplayStepType.LLM_REQUEST,
                    f"LLM Request: {span.name}",
                    span.input_data,
                    span.duration_ms / 2,
                    {"model": span.attributes.get("model")},
                )
                replay.add_step(
                    ReplayStepType.LLM_RESPONSE,
                    f"LLM Response: {span.name}",
                    span.output_data,
                    span.duration_ms / 2,
                    {"tokens": span.tokens_used},
                )
            elif span.type.value == "tool_call":
                replay.add_step(
                    ReplayStepType.TOOL_CALL,
                    f"Tool Call: {span.name}",
                    span.input_data,
                    span.duration_ms / 2,
                )
                replay.add_step(
                    ReplayStepType.TOOL_RESULT,
                    f"Tool Result: {span.name}",
                    span.output_data,
                    span.duration_ms / 2,
                )
            else:
                replay.add_step(
                    step_type,
                    span.name,
                    content,
                    span.duration_ms,
                    span.attributes,
                )
        
        # Adicionar step de output
        replay.add_step(
            ReplayStepType.OUTPUT,
            "Agent Output",
            trace.output_message,
            0,
        )
        
        return replay
    
    @staticmethod
    def _span_type_to_step_type(span_type: str) -> ReplayStepType:
        """Converte tipo de span para tipo de step."""
        mapping = {
            "thinking": ReplayStepType.THINKING,
            "tool_call": ReplayStepType.TOOL_CALL,
            "tool_result": ReplayStepType.TOOL_RESULT,
            "llm_call": ReplayStepType.LLM_REQUEST,
            "decision": ReplayStepType.DECISION,
            "error": ReplayStepType.ERROR,
        }
        return mapping.get(span_type, ReplayStepType.THINKING)


class ReplayManager:
    """Gerenciador de replays."""
    
    def __init__(self):
        self._replays: Dict[str, ExecutionReplay] = {}
    
    def create_replay(self, trace: Any) -> ExecutionReplay:
        """Cria replay a partir de trace."""
        replay = ExecutionReplay.from_trace(trace)
        self._replays[replay.id] = replay
        return replay
    
    def get_replay(self, replay_id: str) -> Optional[ExecutionReplay]:
        """Obtém replay por ID."""
        return self._replays.get(replay_id)
    
    def delete_replay(self, replay_id: str) -> bool:
        """Remove replay."""
        if replay_id in self._replays:
            del self._replays[replay_id]
            return True
        return False
    
    def list_replays(self) -> List[ExecutionReplay]:
        """Lista todos os replays."""
        return list(self._replays.values())


# Singleton
_manager: Optional[ReplayManager] = None


def get_replay_manager() -> ReplayManager:
    """Obtém gerenciador de replays."""
    global _manager
    if _manager is None:
        _manager = ReplayManager()
    return _manager

"""
Quality Metrics - Métricas de qualidade.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Métricas de qualidade."""
    # Feedback
    total_feedback: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    feedback_rate: float = 0.0
    positive_rate: float = 0.0
    
    # Regeneração
    total_regenerations: int = 0
    regeneration_rate: float = 0.0
    
    # Edições
    total_edits: int = 0
    edit_rate: float = 0.0
    
    # Tempo
    avg_response_time_ms: float = 0
    
    # Erros
    error_count: int = 0
    error_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_feedback": self.total_feedback,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
            "feedback_rate": round(self.feedback_rate, 2),
            "positive_rate": round(self.positive_rate, 2),
            "total_regenerations": self.total_regenerations,
            "regeneration_rate": round(self.regeneration_rate, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "error_count": self.error_count,
            "error_rate": round(self.error_rate, 2)
        }


class QualityTracker:
    """
    Rastreador de qualidade.
    """
    
    def __init__(self):
        self._feedback: List[Dict] = []
        self._regenerations: List[Dict] = []
        self._errors: List[Dict] = []
        self._response_times: List[float] = []
        self._total_messages = 0
    
    async def record_message(self, latency_ms: float) -> None:
        """Registra uma mensagem."""
        self._total_messages += 1
        self._response_times.append(latency_ms)
    
    async def record_feedback(
        self,
        message_id: str,
        feedback: str,
        user_id: Optional[str] = None
    ) -> None:
        """Registra feedback."""
        self._feedback.append({
            "message_id": message_id,
            "feedback": feedback,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def record_regeneration(
        self,
        message_id: str,
        original_message_id: str
    ) -> None:
        """Registra regeneração."""
        self._regenerations.append({
            "message_id": message_id,
            "original_message_id": original_message_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def record_error(
        self,
        error_type: str,
        error_message: str,
        conversation_id: Optional[str] = None
    ) -> None:
        """Registra erro."""
        self._errors.append({
            "type": error_type,
            "message": error_message,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_metrics(self) -> QualityMetrics:
        """Calcula métricas de qualidade."""
        metrics = QualityMetrics()
        
        # Feedback
        metrics.total_feedback = len(self._feedback)
        metrics.positive_feedback = len([f for f in self._feedback if f["feedback"] == "good"])
        metrics.negative_feedback = len([f for f in self._feedback if f["feedback"] == "bad"])
        
        if self._total_messages > 0:
            metrics.feedback_rate = metrics.total_feedback / self._total_messages
        
        if metrics.total_feedback > 0:
            metrics.positive_rate = metrics.positive_feedback / metrics.total_feedback
        
        # Regeneração
        metrics.total_regenerations = len(self._regenerations)
        if self._total_messages > 0:
            metrics.regeneration_rate = metrics.total_regenerations / self._total_messages
        
        # Tempo de resposta
        if self._response_times:
            metrics.avg_response_time_ms = sum(self._response_times) / len(self._response_times)
        
        # Erros
        metrics.error_count = len(self._errors)
        if self._total_messages > 0:
            metrics.error_rate = metrics.error_count / self._total_messages
        
        return metrics
    
    async def get_feedback_summary(self) -> Dict:
        """Resumo de feedback."""
        by_type = {"good": 0, "bad": 0}
        
        for f in self._feedback:
            feedback = f.get("feedback", "unknown")
            by_type[feedback] = by_type.get(feedback, 0) + 1
        
        return {
            "total": len(self._feedback),
            "by_type": by_type,
            "recent": self._feedback[-10:]
        }


# Singleton
_quality_tracker: Optional[QualityTracker] = None


def get_quality_tracker() -> QualityTracker:
    global _quality_tracker
    if _quality_tracker is None:
        _quality_tracker = QualityTracker()
    return _quality_tracker

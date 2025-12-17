"""
Usage Tracking - Rastreamento de uso.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Métricas de uso."""
    # Período
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # Contadores
    total_messages: int = 0
    total_conversations: int = 0
    total_tokens: int = 0
    total_tokens_prompt: int = 0
    total_tokens_completion: int = 0
    
    # Por modelo
    messages_by_model: Dict[str, int] = field(default_factory=dict)
    tokens_by_model: Dict[str, int] = field(default_factory=dict)
    
    # Por agente
    messages_by_agent: Dict[str, int] = field(default_factory=dict)
    
    # Performance
    avg_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0
    
    # Qualidade
    positive_feedback_rate: float = 0
    regeneration_rate: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_messages": self.total_messages,
            "total_conversations": self.total_conversations,
            "total_tokens": self.total_tokens,
            "messages_by_model": self.messages_by_model,
            "tokens_by_model": self.tokens_by_model,
            "messages_by_agent": self.messages_by_agent,
            "avg_latency_ms": self.avg_latency_ms,
            "positive_feedback_rate": self.positive_feedback_rate
        }


class UsageTracker:
    """
    Rastreador de uso.
    """
    
    def __init__(self):
        self._events: List[Dict] = []
        self._daily_stats: Dict[str, UsageMetrics] = {}  # date_str -> metrics
    
    async def track_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        model: str,
        agent_id: Optional[str] = None,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        latency_ms: float = 0
    ) -> None:
        """Rastreia uma mensagem."""
        event = {
            "type": "message",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "model": model,
            "agent_id": agent_id,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        self._events.append(event)
        await self._update_daily_stats(event)
    
    async def track_feedback(
        self,
        message_id: str,
        feedback: str
    ) -> None:
        """Rastreia feedback."""
        event = {
            "type": "feedback",
            "message_id": message_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        self._events.append(event)
    
    async def track_regeneration(
        self,
        message_id: str,
        original_message_id: str
    ) -> None:
        """Rastreia regeneração."""
        event = {
            "type": "regeneration",
            "message_id": message_id,
            "original_message_id": original_message_id,
            "timestamp": datetime.now().isoformat()
        }
        self._events.append(event)
    
    async def _update_daily_stats(self, event: Dict) -> None:
        """Atualiza estatísticas diárias."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        if date_str not in self._daily_stats:
            self._daily_stats[date_str] = UsageMetrics(
                period_start=datetime.now().replace(hour=0, minute=0, second=0),
                period_end=datetime.now().replace(hour=23, minute=59, second=59)
            )
        
        stats = self._daily_stats[date_str]
        
        if event["type"] == "message":
            stats.total_messages += 1
            stats.total_tokens += event["tokens_prompt"] + event["tokens_completion"]
            stats.total_tokens_prompt += event["tokens_prompt"]
            stats.total_tokens_completion += event["tokens_completion"]
            
            model = event.get("model", "unknown")
            stats.messages_by_model[model] = stats.messages_by_model.get(model, 0) + 1
            stats.tokens_by_model[model] = stats.tokens_by_model.get(model, 0) + event["tokens_prompt"] + event["tokens_completion"]
            
            if event.get("agent_id"):
                stats.messages_by_agent[event["agent_id"]] = stats.messages_by_agent.get(event["agent_id"], 0) + 1
    
    async def get_metrics(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageMetrics:
        """Obtém métricas agregadas."""
        # Agregar por período
        metrics = UsageMetrics()
        
        for date_str, daily in self._daily_stats.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            
            metrics.total_messages += daily.total_messages
            metrics.total_tokens += daily.total_tokens
            
            for model, count in daily.messages_by_model.items():
                metrics.messages_by_model[model] = metrics.messages_by_model.get(model, 0) + count
        
        return metrics
    
    async def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Obtém estatísticas diárias."""
        result = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self._daily_stats:
                result.append({
                    "date": date,
                    **self._daily_stats[date].to_dict()
                })
            else:
                result.append({
                    "date": date,
                    "total_messages": 0,
                    "total_tokens": 0
                })
        
        return result


# Singleton
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker

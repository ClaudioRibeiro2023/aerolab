"""
Métricas para Workflows.

Coleta e expõe métricas:
- Contadores: execuções, sucesso, falha
- Histogramas: latência, tokens
- Gauges: execuções ativas
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class WorkflowMetrics:
    """Métricas de um workflow."""
    workflow_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0
    total_tokens: int = 0
    total_cost_usd: float = 0
    step_counts: Dict[str, int] = field(default_factory=dict)
    latency_samples: List[float] = field(default_factory=list)
    last_execution: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0
        return self.successful_executions / self.total_executions
    
    @property
    def avg_latency_ms(self) -> float:
        if not self.latency_samples:
            return 0
        return statistics.mean(self.latency_samples[-100:])
    
    @property
    def p95_latency_ms(self) -> float:
        samples = self.latency_samples[-100:]
        if len(samples) < 2:
            return self.avg_latency_ms
        sorted_samples = sorted(samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]
    
    def record_execution(
        self,
        success: bool,
        duration_ms: float,
        tokens: int = 0,
        cost_usd: float = 0,
        steps: Optional[List[str]] = None
    ) -> None:
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        self.total_duration_ms += duration_ms
        self.total_tokens += tokens
        self.total_cost_usd += cost_usd
        self.latency_samples.append(duration_ms)
        
        # Manter últimas 1000 amostras
        if len(self.latency_samples) > 1000:
            self.latency_samples = self.latency_samples[-1000:]
        
        if steps:
            for step_type in steps:
                self.step_counts[step_type] = self.step_counts.get(step_type, 0) + 1
        
        self.last_execution = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "step_counts": self.step_counts,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None
        }


class MetricsCollector:
    """
    Coletor central de métricas.
    
    Exemplo:
        collector = MetricsCollector()
        
        # Registrar execução
        collector.record_execution(
            workflow_id="my-workflow",
            success=True,
            duration_ms=1500,
            tokens=500
        )
        
        # Obter métricas
        metrics = collector.get_metrics("my-workflow")
        print(f"Success rate: {metrics.success_rate:.0%}")
    """
    
    def __init__(self):
        self._metrics: Dict[str, WorkflowMetrics] = {}
        self._step_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "duration": 0})
        self._active_executions: int = 0
        self._lock = threading.RLock()
    
    def record_execution(
        self,
        workflow_id: str,
        success: bool,
        duration_ms: float,
        tokens: int = 0,
        cost_usd: float = 0,
        steps: Optional[List[str]] = None
    ) -> None:
        """Registra uma execução."""
        with self._lock:
            if workflow_id not in self._metrics:
                self._metrics[workflow_id] = WorkflowMetrics(workflow_id=workflow_id)
            
            self._metrics[workflow_id].record_execution(
                success=success,
                duration_ms=duration_ms,
                tokens=tokens,
                cost_usd=cost_usd,
                steps=steps
            )
    
    def record_step(
        self,
        workflow_id: str,
        step_id: str,
        step_type: str,
        duration_ms: float,
        success: bool
    ) -> None:
        """Registra execução de um step."""
        with self._lock:
            key = f"{workflow_id}:{step_id}"
            self._step_metrics[key]["count"] += 1
            self._step_metrics[key]["duration"] += duration_ms
            self._step_metrics[key]["type"] = step_type
            self._step_metrics[key]["success"] = self._step_metrics[key].get("success", 0) + (1 if success else 0)
    
    def increment_active(self) -> None:
        """Incrementa contador de execuções ativas."""
        with self._lock:
            self._active_executions += 1
    
    def decrement_active(self) -> None:
        """Decrementa contador de execuções ativas."""
        with self._lock:
            self._active_executions = max(0, self._active_executions - 1)
    
    @property
    def active_executions(self) -> int:
        """Retorna número de execuções ativas."""
        return self._active_executions
    
    def get_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Obtém métricas de um workflow."""
        with self._lock:
            return self._metrics.get(workflow_id)
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Obtém métricas de todos os workflows."""
        with self._lock:
            return {wf_id: m.to_dict() for wf_id, m in self._metrics.items()}
    
    def get_summary(self) -> Dict:
        """Obtém resumo geral."""
        with self._lock:
            total_execs = sum(m.total_executions for m in self._metrics.values())
            total_success = sum(m.successful_executions for m in self._metrics.values())
            total_tokens = sum(m.total_tokens for m in self._metrics.values())
            total_cost = sum(m.total_cost_usd for m in self._metrics.values())
            
            return {
                "workflows_count": len(self._metrics),
                "total_executions": total_execs,
                "success_rate": total_success / total_execs if total_execs > 0 else 0,
                "active_executions": self._active_executions,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost
            }
    
    def reset(self, workflow_id: Optional[str] = None) -> None:
        """Reseta métricas."""
        with self._lock:
            if workflow_id:
                if workflow_id in self._metrics:
                    del self._metrics[workflow_id]
            else:
                self._metrics.clear()
                self._step_metrics.clear()


# Singleton
_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Obtém coletor global."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector

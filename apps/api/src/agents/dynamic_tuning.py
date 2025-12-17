"""
Sistema de Dynamic Tuning para Agentes.

Ajusta automaticamente parâmetros do agente em tempo real baseado em:
- Performance histórica
- Feedback do usuário
- Métricas de qualidade
- Custos

Estratégias de tuning:
- Adaptive Temperature: Ajusta criatividade baseado no contexto
- Dynamic Token Budget: Otimiza uso de tokens
- Model Selection: Escolhe modelo ideal por tarefa
- Prompt Optimization: Refina prompts automaticamente

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Dynamic Tuning System                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Monitor      │  │ Optimizer    │  │ Applier      │      │
│  │              │  │              │  │              │      │
│  │ - Metrics    │  │ - Analyze    │  │ - Apply      │      │
│  │ - Feedback   │  │ - Suggest    │  │ - Rollback   │      │
│  │ - History    │  │ - Learn      │  │ - Validate   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading
import random


class TuningStrategy(Enum):
    """Estratégias de tuning."""
    CONSERVATIVE = "conservative"   # Mudanças pequenas e graduais
    MODERATE = "moderate"           # Balanço entre estabilidade e otimização
    AGGRESSIVE = "aggressive"       # Busca rápida pelo ótimo


class ParameterType(Enum):
    """Tipos de parâmetros tunáveis."""
    TEMPERATURE = "temperature"
    TOP_P = "top_p"
    MAX_TOKENS = "max_tokens"
    FREQUENCY_PENALTY = "frequency_penalty"
    PRESENCE_PENALTY = "presence_penalty"
    MODEL = "model"


@dataclass
class ParameterConfig:
    """Configuração de um parâmetro tunável."""
    name: str
    param_type: ParameterType
    current_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: float = 0.1
    allowed_values: Optional[List[Any]] = None  # Para parâmetros discretos
    
    def validate(self, value: Any) -> bool:
        """Valida se o valor é permitido."""
        if self.allowed_values:
            return value in self.allowed_values
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True
    
    def clamp(self, value: float) -> float:
        """Limita valor ao range permitido."""
        if self.min_value is not None:
            value = max(self.min_value, value)
        if self.max_value is not None:
            value = min(self.max_value, value)
        return value


@dataclass
class TuningMetrics:
    """Métricas para decisões de tuning."""
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    quality_score: float = 0.0
    user_satisfaction: Optional[float] = None
    error_occurred: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TuningDecision:
    """Decisão de tuning."""
    parameter: str
    old_value: Any
    new_value: Any
    reason: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCollector:
    """
    Coletor de métricas para tuning.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._metrics: List[TuningMetrics] = []
        self._lock = threading.Lock()
    
    def record(self, metrics: TuningMetrics) -> None:
        """Registra métricas."""
        with self._lock:
            self._metrics.append(metrics)
            if len(self._metrics) > self.window_size:
                self._metrics = self._metrics[-self.window_size:]
    
    def get_recent(self, n: int = 10) -> List[TuningMetrics]:
        """Retorna métricas recentes."""
        with self._lock:
            return self._metrics[-n:]
    
    def get_averages(self, n: Optional[int] = None) -> Dict[str, float]:
        """Calcula médias das métricas."""
        with self._lock:
            metrics = self._metrics[-n:] if n else self._metrics
            
            if not metrics:
                return {
                    "avg_latency_ms": 0,
                    "avg_tokens": 0,
                    "avg_cost_usd": 0,
                    "avg_quality": 0,
                    "error_rate": 0
                }
            
            return {
                "avg_latency_ms": statistics.mean(m.latency_ms for m in metrics),
                "avg_tokens": statistics.mean(m.tokens_used for m in metrics),
                "avg_cost_usd": statistics.mean(m.cost_usd for m in metrics),
                "avg_quality": statistics.mean(m.quality_score for m in metrics),
                "error_rate": sum(1 for m in metrics if m.error_occurred) / len(metrics)
            }
    
    def get_trend(self, metric: str, window: int = 20) -> str:
        """Identifica tendência de uma métrica."""
        with self._lock:
            if len(self._metrics) < window:
                return "stable"
            
            recent = self._metrics[-window:]
            first_half = recent[:window//2]
            second_half = recent[window//2:]
            
            def get_metric_value(m: TuningMetrics) -> float:
                if metric == "latency":
                    return m.latency_ms
                elif metric == "quality":
                    return m.quality_score
                elif metric == "cost":
                    return m.cost_usd
                return 0
            
            avg_first = statistics.mean(get_metric_value(m) for m in first_half)
            avg_second = statistics.mean(get_metric_value(m) for m in second_half)
            
            diff_pct = (avg_second - avg_first) / max(avg_first, 0.001) * 100
            
            if diff_pct > 10:
                return "increasing"
            elif diff_pct < -10:
                return "decreasing"
            return "stable"


class TemperatureOptimizer:
    """
    Otimizador adaptativo de temperatura.
    
    Ajusta temperatura baseado em:
    - Tipo de tarefa (criativa vs factual)
    - Histórico de qualidade
    - Feedback do usuário
    """
    
    def __init__(self, initial_temp: float = 0.7):
        self.current_temp = initial_temp
        self.min_temp = 0.0
        self.max_temp = 1.5
        self._history: List[Tuple[float, float]] = []  # (temp, quality)
    
    def suggest(
        self,
        task_type: str,
        quality_history: List[float],
        target_quality: float = 0.8
    ) -> Tuple[float, str]:
        """
        Sugere nova temperatura.
        
        Returns:
            (new_temperature, reason)
        """
        # Temperaturas base por tipo de tarefa
        task_temps = {
            "factual": 0.2,
            "coding": 0.3,
            "analysis": 0.5,
            "general": 0.7,
            "creative": 1.0,
            "brainstorm": 1.2
        }
        
        base_temp = task_temps.get(task_type, 0.7)
        
        # Ajuste baseado em qualidade
        if len(quality_history) >= 5:
            recent_quality = statistics.mean(quality_history[-5:])
            
            if recent_quality < target_quality - 0.1:
                # Qualidade baixa: reduzir temperatura para mais foco
                adjustment = -0.1
                reason = f"Qualidade baixa ({recent_quality:.2f}), reduzindo temperatura"
            elif recent_quality > target_quality + 0.1:
                # Qualidade alta: pode aumentar para mais variação
                adjustment = 0.05
                reason = f"Qualidade alta ({recent_quality:.2f}), permitindo mais variação"
            else:
                adjustment = 0
                reason = "Qualidade dentro do target"
        else:
            adjustment = 0
            reason = "Dados insuficientes, usando base"
        
        new_temp = max(self.min_temp, min(self.max_temp, base_temp + adjustment))
        self.current_temp = new_temp
        
        return new_temp, reason
    
    def record_outcome(self, temperature: float, quality: float) -> None:
        """Registra resultado para aprendizado."""
        self._history.append((temperature, quality))
        # Manter apenas últimos 100
        if len(self._history) > 100:
            self._history = self._history[-100:]


class TokenBudgetOptimizer:
    """
    Otimizador de budget de tokens.
    
    Balanceia qualidade vs custo ajustando max_tokens dinamicamente.
    """
    
    def __init__(self, initial_budget: int = 1000):
        self.current_budget = initial_budget
        self.min_budget = 100
        self.max_budget = 8000
        self._usage_history: List[int] = []
    
    def suggest(
        self,
        task_complexity: str,
        cost_sensitivity: float = 0.5  # 0 = ignorar custo, 1 = priorizar economia
    ) -> Tuple[int, str]:
        """
        Sugere budget de tokens.
        
        Returns:
            (new_budget, reason)
        """
        # Budgets base por complexidade
        complexity_budgets = {
            "simple": 500,
            "medium": 1000,
            "complex": 2000,
            "very_complex": 4000
        }
        
        base_budget = complexity_budgets.get(task_complexity, 1000)
        
        # Ajuste baseado em uso histórico
        if len(self._usage_history) >= 5:
            avg_usage = statistics.mean(self._usage_history[-5:])
            usage_ratio = avg_usage / self.current_budget
            
            if usage_ratio > 0.9:
                # Usando quase todo o budget, aumentar
                adjustment = 1.2
                reason = f"Uso alto ({usage_ratio:.0%}), aumentando budget"
            elif usage_ratio < 0.3:
                # Usando pouco, pode reduzir
                adjustment = 0.8
                reason = f"Uso baixo ({usage_ratio:.0%}), otimizando custo"
            else:
                adjustment = 1.0
                reason = "Uso adequado"
        else:
            adjustment = 1.0
            reason = "Dados insuficientes"
        
        # Aplicar sensibilidade a custo
        cost_factor = 1 - (cost_sensitivity * 0.3)  # Reduz até 30%
        
        new_budget = int(base_budget * adjustment * cost_factor)
        new_budget = max(self.min_budget, min(self.max_budget, new_budget))
        self.current_budget = new_budget
        
        return new_budget, reason
    
    def record_usage(self, tokens_used: int) -> None:
        """Registra uso de tokens."""
        self._usage_history.append(tokens_used)
        if len(self._usage_history) > 100:
            self._usage_history = self._usage_history[-100:]


class ModelSelector:
    """
    Seletor dinâmico de modelo.
    
    Escolhe modelo ideal baseado em:
    - Tipo de tarefa
    - Requisitos de latência
    - Budget de custo
    - Histórico de performance
    """
    
    def __init__(self):
        # Catálogo de modelos com características
        self.models = {
            "gpt-5.1": {
                "quality": 0.95,
                "speed": 0.7,
                "cost_per_1k": 0.03,
                "strengths": ["general", "reasoning", "creative"]
            },
            "gpt-5.1-mini": {
                "quality": 0.85,
                "speed": 0.9,
                "cost_per_1k": 0.0015,
                "strengths": ["general", "fast"]
            },
            "claude-sonnet-4.5": {
                "quality": 0.93,
                "speed": 0.75,
                "cost_per_1k": 0.015,
                "strengths": ["analysis", "coding", "long_context"]
            },
            "gemini-2.5-flash": {
                "quality": 0.88,
                "speed": 0.95,
                "cost_per_1k": 0.001,
                "strengths": ["fast", "multimodal"]
            },
            "gpt-5.1-codex-max": {
                "quality": 0.97,
                "speed": 0.6,
                "cost_per_1k": 0.05,
                "strengths": ["coding", "reasoning"]
            }
        }
        
        self._performance_history: Dict[str, List[float]] = defaultdict(list)
    
    def suggest(
        self,
        task_type: str,
        priority: str = "balanced",  # quality, speed, cost, balanced
        max_cost_per_1k: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        Sugere modelo ideal.
        
        Returns:
            (model_id, reason)
        """
        candidates = []
        
        for model_id, specs in self.models.items():
            # Filtrar por custo se especificado
            if max_cost_per_1k and specs["cost_per_1k"] > max_cost_per_1k:
                continue
            
            # Calcular score baseado em prioridade
            if priority == "quality":
                score = specs["quality"]
            elif priority == "speed":
                score = specs["speed"]
            elif priority == "cost":
                score = 1 - (specs["cost_per_1k"] / 0.05)  # Normalizar
            else:  # balanced
                score = (specs["quality"] * 0.4 + 
                        specs["speed"] * 0.3 + 
                        (1 - specs["cost_per_1k"] / 0.05) * 0.3)
            
            # Bonus se especializado no tipo de tarefa
            if task_type in specs["strengths"]:
                score *= 1.2
            
            # Ajuste por histórico de performance
            if model_id in self._performance_history:
                history = self._performance_history[model_id]
                if history:
                    avg_perf = statistics.mean(history[-10:])
                    score *= (0.5 + avg_perf * 0.5)
            
            candidates.append((model_id, score))
        
        if not candidates:
            return "gpt-5.1-mini", "Fallback - nenhum modelo no budget"
        
        # Ordenar por score e selecionar o melhor
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_model = candidates[0][0]
        
        specs = self.models[best_model]
        reason = f"Melhor para {task_type} ({priority}): quality={specs['quality']:.0%}, speed={specs['speed']:.0%}"
        
        return best_model, reason
    
    def record_performance(self, model_id: str, quality: float) -> None:
        """Registra performance do modelo."""
        if model_id in self.models:
            self._performance_history[model_id].append(quality)
            # Manter últimos 50
            if len(self._performance_history[model_id]) > 50:
                self._performance_history[model_id] = self._performance_history[model_id][-50:]


class DynamicTuner:
    """
    Sistema completo de Dynamic Tuning.
    
    Exemplo:
        tuner = DynamicTuner(agent_id="my_agent")
        
        # Antes de cada execução
        params = tuner.get_optimized_params(task_type="coding")
        
        # Após execução
        tuner.record_execution(
            latency_ms=850,
            tokens_used=500,
            quality_score=0.9
        )
        
        # Ver recomendações
        recommendations = tuner.get_recommendations()
    """
    
    def __init__(
        self,
        agent_id: str,
        strategy: TuningStrategy = TuningStrategy.MODERATE,
        initial_params: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.strategy = strategy
        
        # Parâmetros atuais
        self.params = initial_params or {
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 1000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "model": "gpt-5.1"
        }
        
        # Componentes
        self.metrics_collector = MetricsCollector()
        self.temp_optimizer = TemperatureOptimizer(self.params["temperature"])
        self.token_optimizer = TokenBudgetOptimizer(self.params["max_tokens"])
        self.model_selector = ModelSelector()
        
        # Histórico de decisões
        self._decisions: List[TuningDecision] = []
        self._lock = threading.Lock()
    
    def get_optimized_params(
        self,
        task_type: str = "general",
        task_complexity: str = "medium",
        priority: str = "balanced",
        cost_sensitivity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Retorna parâmetros otimizados para a tarefa.
        """
        with self._lock:
            params = self.params.copy()
            quality_history = [m.quality_score for m in self.metrics_collector.get_recent(10)]
            
            # Otimizar temperatura
            new_temp, temp_reason = self.temp_optimizer.suggest(
                task_type=task_type,
                quality_history=quality_history
            )
            if new_temp != params["temperature"]:
                self._record_decision("temperature", params["temperature"], new_temp, temp_reason)
                params["temperature"] = new_temp
            
            # Otimizar tokens
            new_tokens, token_reason = self.token_optimizer.suggest(
                task_complexity=task_complexity,
                cost_sensitivity=cost_sensitivity
            )
            if new_tokens != params["max_tokens"]:
                self._record_decision("max_tokens", params["max_tokens"], new_tokens, token_reason)
                params["max_tokens"] = new_tokens
            
            # Selecionar modelo (se estratégia agressiva)
            if self.strategy == TuningStrategy.AGGRESSIVE:
                new_model, model_reason = self.model_selector.suggest(
                    task_type=task_type,
                    priority=priority
                )
                if new_model != params["model"]:
                    self._record_decision("model", params["model"], new_model, model_reason)
                    params["model"] = new_model
            
            self.params = params
            return params
    
    def record_execution(
        self,
        latency_ms: float,
        tokens_used: int,
        quality_score: float,
        cost_usd: float = 0.0,
        user_satisfaction: Optional[float] = None,
        error: bool = False
    ) -> None:
        """
        Registra resultado de uma execução.
        """
        metrics = TuningMetrics(
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            quality_score=quality_score,
            user_satisfaction=user_satisfaction,
            error_occurred=error
        )
        
        self.metrics_collector.record(metrics)
        self.temp_optimizer.record_outcome(self.params["temperature"], quality_score)
        self.token_optimizer.record_usage(tokens_used)
        self.model_selector.record_performance(self.params["model"], quality_score)
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Retorna recomendações de tuning.
        """
        recommendations = []
        averages = self.metrics_collector.get_averages(20)
        
        # Análise de latência
        latency_trend = self.metrics_collector.get_trend("latency")
        if latency_trend == "increasing":
            recommendations.append({
                "type": "warning",
                "parameter": "latency",
                "message": "Latência aumentando. Considere reduzir max_tokens ou usar modelo mais rápido.",
                "suggested_action": "reduce_tokens"
            })
        
        # Análise de qualidade
        quality_trend = self.metrics_collector.get_trend("quality")
        if quality_trend == "decreasing":
            recommendations.append({
                "type": "warning",
                "parameter": "quality",
                "message": "Qualidade diminuindo. Considere aumentar temperatura ou trocar modelo.",
                "suggested_action": "adjust_temperature"
            })
        
        # Análise de custo
        if averages["avg_cost_usd"] > 0.01:
            recommendations.append({
                "type": "info",
                "parameter": "cost",
                "message": f"Custo médio: ${averages['avg_cost_usd']:.4f}/exec. Considere modelo mais econômico.",
                "suggested_action": "consider_cheaper_model"
            })
        
        # Análise de erros
        if averages["error_rate"] > 0.1:
            recommendations.append({
                "type": "critical",
                "parameter": "errors",
                "message": f"Taxa de erro alta: {averages['error_rate']:.0%}. Revisar configurações.",
                "suggested_action": "review_config"
            })
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do tuner.
        """
        averages = self.metrics_collector.get_averages()
        
        return {
            "agent_id": self.agent_id,
            "strategy": self.strategy.value,
            "current_params": self.params,
            "metrics": averages,
            "trends": {
                "latency": self.metrics_collector.get_trend("latency"),
                "quality": self.metrics_collector.get_trend("quality"),
                "cost": self.metrics_collector.get_trend("cost")
            },
            "decisions_count": len(self._decisions),
            "recent_decisions": [d.to_dict() for d in self._decisions[-5:]]
        }
    
    def _record_decision(
        self,
        parameter: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ) -> None:
        """Registra decisão de tuning."""
        confidence = {
            TuningStrategy.CONSERVATIVE: 0.9,
            TuningStrategy.MODERATE: 0.7,
            TuningStrategy.AGGRESSIVE: 0.5
        }.get(self.strategy, 0.7)
        
        decision = TuningDecision(
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            confidence=confidence
        )
        self._decisions.append(decision)
        
        # Manter últimas 100 decisões
        if len(self._decisions) > 100:
            self._decisions = self._decisions[-100:]
    
    def reset(self) -> None:
        """Reseta o tuner para valores padrão."""
        self.params = {
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 1000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "model": "gpt-5.1"
        }
        self._decisions = []


# Factory
_tuners: Dict[str, DynamicTuner] = {}


def get_tuner(
    agent_id: str,
    strategy: TuningStrategy = TuningStrategy.MODERATE
) -> DynamicTuner:
    """
    Obtém ou cria tuner para um agente.
    """
    if agent_id not in _tuners:
        _tuners[agent_id] = DynamicTuner(agent_id, strategy)
    return _tuners[agent_id]


def create_tuner(
    agent_id: str,
    strategy: str = "moderate",
    initial_params: Optional[Dict[str, Any]] = None
) -> DynamicTuner:
    """
    Cria novo tuner.
    
    Exemplo:
        tuner = create_tuner(
            "my_agent",
            strategy="aggressive",
            initial_params={"temperature": 0.5, "max_tokens": 2000}
        )
    """
    strat = TuningStrategy(strategy)
    tuner = DynamicTuner(agent_id, strat, initial_params)
    _tuners[agent_id] = tuner
    return tuner

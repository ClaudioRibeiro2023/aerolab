"""
Decision Analyzer - Análise de decisões de agentes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Tipos de decisão."""
    TOOL_SELECTION = "tool_selection"
    RESPONSE_GENERATION = "response_generation"
    DELEGATION = "delegation"
    RETRY = "retry"
    FALLBACK = "fallback"
    TERMINATION = "termination"
    CLARIFICATION = "clarification"
    ESCALATION = "escalation"


class DecisionOutcome(str, Enum):
    """Resultado da decisão."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class DecisionOption:
    """Opção considerada em uma decisão."""
    id: str = ""
    name: str = ""
    description: str = ""
    confidence: float = 0.0  # 0-1
    was_selected: bool = False
    reasoning: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "confidence": round(self.confidence, 4),
            "wasSelected": self.was_selected,
            "reasoning": self.reasoning,
        }


@dataclass
class Decision:
    """Decisão tomada por um agente."""
    id: str = ""
    trace_id: str = ""
    span_id: str = ""
    
    # Contexto
    agent_name: str = ""
    type: DecisionType = DecisionType.TOOL_SELECTION
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    
    # Decisão
    question: str = ""  # O que estava sendo decidido
    context: str = ""   # Contexto da decisão
    
    # Opções
    options: List[DecisionOption] = field(default_factory=list)
    selected_option: Optional[str] = None
    
    # Resultado
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    outcome_reasoning: str = ""
    
    # Métricas
    confidence: float = 0.0
    impact_score: float = 0.0  # Impacto da decisão (0-1)
    
    # Feedback
    user_feedback: Optional[str] = None
    feedback_score: Optional[float] = None  # -1 a 1
    
    def add_option(
        self,
        name: str,
        confidence: float,
        description: str = "",
        reasoning: str = "",
    ) -> DecisionOption:
        """Adiciona opção à decisão."""
        option = DecisionOption(
            id=f"opt_{len(self.options)}",
            name=name,
            confidence=confidence,
            description=description,
            reasoning=reasoning,
        )
        self.options.append(option)
        return option
    
    def select_option(self, option_id: str, reasoning: str = ""):
        """Seleciona uma opção."""
        for opt in self.options:
            opt.was_selected = (opt.id == option_id)
            if opt.was_selected:
                self.selected_option = option_id
                self.confidence = opt.confidence
    
    def set_outcome(self, outcome: DecisionOutcome, reasoning: str = ""):
        """Define resultado da decisão."""
        self.outcome = outcome
        self.outcome_reasoning = reasoning
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "agentName": self.agent_name,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "durationMs": round(self.duration_ms, 2),
            "question": self.question,
            "context": self.context,
            "options": [o.to_dict() for o in self.options],
            "selectedOption": self.selected_option,
            "outcome": self.outcome.value,
            "outcomeReasoning": self.outcome_reasoning,
            "confidence": round(self.confidence, 4),
            "impactScore": round(self.impact_score, 4),
            "userFeedback": self.user_feedback,
            "feedbackScore": self.feedback_score,
        }


class DecisionAnalyzer:
    """
    Analisador de decisões de agentes.
    
    Rastreia e analisa padrões de decisão.
    """
    
    def __init__(self, max_decisions: int = 10000):
        self._decisions: Dict[str, Decision] = {}
        self._max_decisions = max_decisions
    
    def record_decision(self, decision: Decision):
        """Registra uma decisão."""
        self._decisions[decision.id] = decision
        
        # Limpar decisões antigas
        if len(self._decisions) > self._max_decisions:
            oldest = sorted(
                self._decisions.values(),
                key=lambda d: d.timestamp
            )[:len(self._decisions) - self._max_decisions]
            
            for d in oldest:
                del self._decisions[d.id]
    
    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Obtém decisão por ID."""
        return self._decisions.get(decision_id)
    
    def get_decisions_for_trace(self, trace_id: str) -> List[Decision]:
        """Obtém decisões de um trace."""
        return [
            d for d in self._decisions.values()
            if d.trace_id == trace_id
        ]
    
    def analyze_tool_selection(
        self,
        agent_name: Optional[str] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Analisa padrões de seleção de ferramentas."""
        decisions = [
            d for d in self._decisions.values()
            if d.type == DecisionType.TOOL_SELECTION
        ]
        
        if agent_name:
            decisions = [d for d in decisions if d.agent_name == agent_name]
        
        decisions = decisions[-limit:]
        
        if not decisions:
            return {"count": 0}
        
        # Ferramentas mais usadas
        tool_counts = {}
        tool_success = {}
        
        for d in decisions:
            for opt in d.options:
                if opt.was_selected:
                    tool_counts[opt.name] = tool_counts.get(opt.name, 0) + 1
                    if d.outcome == DecisionOutcome.SUCCESS:
                        tool_success[opt.name] = tool_success.get(opt.name, 0) + 1
        
        # Taxa de sucesso por ferramenta
        tool_success_rate = {
            tool: (tool_success.get(tool, 0) / count) if count > 0 else 0
            for tool, count in tool_counts.items()
        }
        
        # Confiança média
        avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
        
        # Decisões com múltiplas opções de alta confiança
        close_decisions = [
            d for d in decisions
            if len([o for o in d.options if o.confidence > 0.7]) > 1
        ]
        
        return {
            "count": len(decisions),
            "toolUsage": tool_counts,
            "toolSuccessRate": tool_success_rate,
            "avgConfidence": avg_confidence,
            "closeDecisions": len(close_decisions),
            "closeDecisionRate": len(close_decisions) / len(decisions) if decisions else 0,
        }
    
    def analyze_decision_quality(
        self,
        agent_name: Optional[str] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Analisa qualidade das decisões."""
        decisions = list(self._decisions.values())
        
        if agent_name:
            decisions = [d for d in decisions if d.agent_name == agent_name]
        
        decisions = decisions[-limit:]
        
        if not decisions:
            return {"count": 0}
        
        # Outcomes
        outcomes = {}
        for d in decisions:
            outcomes[d.outcome.value] = outcomes.get(d.outcome.value, 0) + 1
        
        # Confiança vs sucesso
        high_confidence = [d for d in decisions if d.confidence >= 0.8]
        high_conf_success = len([
            d for d in high_confidence
            if d.outcome == DecisionOutcome.SUCCESS
        ])
        
        low_confidence = [d for d in decisions if d.confidence < 0.5]
        low_conf_success = len([
            d for d in low_confidence
            if d.outcome == DecisionOutcome.SUCCESS
        ])
        
        # Feedback analysis
        with_feedback = [d for d in decisions if d.feedback_score is not None]
        avg_feedback = (
            sum(d.feedback_score for d in with_feedback) / len(with_feedback)
            if with_feedback else None
        )
        
        return {
            "count": len(decisions),
            "outcomes": outcomes,
            "successRate": outcomes.get("success", 0) / len(decisions),
            "highConfidenceCount": len(high_confidence),
            "highConfidenceSuccessRate": high_conf_success / len(high_confidence) if high_confidence else 0,
            "lowConfidenceCount": len(low_confidence),
            "lowConfidenceSuccessRate": low_conf_success / len(low_confidence) if low_confidence else 0,
            "avgFeedbackScore": avg_feedback,
            "feedbackCount": len(with_feedback),
        }
    
    def get_decision_patterns(
        self,
        agent_name: str,
        decision_type: Optional[DecisionType] = None,
    ) -> List[Dict[str, Any]]:
        """Identifica padrões de decisão."""
        decisions = [
            d for d in self._decisions.values()
            if d.agent_name == agent_name
        ]
        
        if decision_type:
            decisions = [d for d in decisions if d.type == decision_type]
        
        # Agrupar por contexto similar
        patterns = []
        
        # Pattern: Decisões frequentes com alta confiança
        high_conf = [d for d in decisions if d.confidence >= 0.9]
        if len(high_conf) >= 5:
            patterns.append({
                "type": "high_confidence",
                "description": "Agent frequently makes high-confidence decisions",
                "count": len(high_conf),
                "examples": [d.question for d in high_conf[:3]],
            })
        
        # Pattern: Decisões que frequentemente falham
        failed = [d for d in decisions if d.outcome == DecisionOutcome.FAILURE]
        if len(failed) >= 3:
            patterns.append({
                "type": "frequent_failure",
                "description": "Some decision types frequently fail",
                "count": len(failed),
                "failureRate": len(failed) / len(decisions) if decisions else 0,
            })
        
        # Pattern: Confiança baixa mas sucesso
        low_conf_success = [
            d for d in decisions
            if d.confidence < 0.5 and d.outcome == DecisionOutcome.SUCCESS
        ]
        if len(low_conf_success) >= 3:
            patterns.append({
                "type": "uncertain_success",
                "description": "Agent succeeds despite low confidence",
                "count": len(low_conf_success),
                "suggestion": "Consider investigating confidence calibration",
            })
        
        return patterns
    
    def add_feedback(
        self,
        decision_id: str,
        feedback: str,
        score: float,
    ) -> bool:
        """Adiciona feedback a uma decisão."""
        decision = self._decisions.get(decision_id)
        if not decision:
            return False
        
        decision.user_feedback = feedback
        decision.feedback_score = max(-1, min(1, score))  # Clamp -1 to 1
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas gerais."""
        decisions = list(self._decisions.values())
        
        if not decisions:
            return {"count": 0}
        
        by_type = {}
        for d in decisions:
            by_type[d.type.value] = by_type.get(d.type.value, 0) + 1
        
        by_agent = {}
        for d in decisions:
            by_agent[d.agent_name] = by_agent.get(d.agent_name, 0) + 1
        
        return {
            "totalDecisions": len(decisions),
            "byType": by_type,
            "byAgent": by_agent,
            "avgConfidence": sum(d.confidence for d in decisions) / len(decisions),
            "successRate": len([d for d in decisions if d.outcome == DecisionOutcome.SUCCESS]) / len(decisions),
        }


# Singleton
_analyzer: Optional[DecisionAnalyzer] = None


def get_decision_analyzer() -> DecisionAnalyzer:
    """Obtém analisador de decisões."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DecisionAnalyzer()
    return _analyzer

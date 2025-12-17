"""
Recommendations - Recomendações inteligentes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Tipos de recomendação."""
    OPTIMIZATION = "optimization"    # Otimização de performance
    COST_SAVING = "cost_saving"      # Economia de custos
    RELIABILITY = "reliability"       # Melhoria de confiabilidade
    SECURITY = "security"            # Segurança
    SCALING = "scaling"              # Escalabilidade
    CONFIGURATION = "configuration"  # Configuração


class RecommendationPriority(str, Enum):
    """Prioridade da recomendação."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Recommendation:
    """Recomendação inteligente."""
    id: str = ""
    type: RecommendationType = RecommendationType.OPTIMIZATION
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    
    # Conteúdo
    title: str = ""
    description: str = ""
    rationale: str = ""
    
    # Ação
    action: str = ""
    action_url: Optional[str] = None
    
    # Impacto esperado
    expected_impact: str = ""
    estimated_savings: Optional[float] = None  # USD
    estimated_improvement: Optional[float] = None  # %
    
    # Contexto
    affected_resources: List[str] = field(default_factory=list)
    related_metrics: List[str] = field(default_factory=list)
    
    # Status
    dismissed: bool = False
    implemented: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "action": self.action,
            "actionUrl": self.action_url,
            "expectedImpact": self.expected_impact,
            "estimatedSavings": self.estimated_savings,
            "estimatedImprovement": self.estimated_improvement,
            "affectedResources": self.affected_resources,
            "relatedMetrics": self.related_metrics,
            "dismissed": self.dismissed,
            "implemented": self.implemented,
            "createdAt": self.created_at.isoformat(),
            "confidence": round(self.confidence, 2),
        }


class RecommendationEngine:
    """
    Engine de recomendações.
    
    Analisa métricas e gera recomendações acionáveis.
    """
    
    def __init__(self):
        self._recommendations: Dict[str, Recommendation] = {}
        self._rules: List[Dict] = self._load_rules()
    
    def _load_rules(self) -> List[Dict]:
        """Carrega regras de recomendação."""
        return [
            # Custos
            {
                "id": "high_cost_model",
                "type": RecommendationType.COST_SAVING,
                "condition": lambda m: m.get("avg_cost_per_request", 0) > 0.05,
                "title": "Consider using a more cost-effective model",
                "description": "Your average cost per request is high. Consider using GPT-4o-mini or Claude Haiku for simpler tasks.",
                "action": "Review model selection for different use cases",
                "impact": "Could reduce costs by 50-80%",
            },
            {
                "id": "unused_agents",
                "type": RecommendationType.COST_SAVING,
                "condition": lambda m: m.get("inactive_agents", 0) > 3,
                "title": "Remove or consolidate inactive agents",
                "description": "You have agents that haven't been used recently.",
                "action": "Review and remove unused agents",
                "impact": "Reduce maintenance overhead",
            },
            
            # Performance
            {
                "id": "high_latency",
                "type": RecommendationType.OPTIMIZATION,
                "condition": lambda m: m.get("p95_latency_ms", 0) > 5000,
                "title": "Optimize high latency requests",
                "description": "Your P95 latency is above 5 seconds. Consider optimizing prompts or using caching.",
                "action": "Review slow requests and implement caching",
                "impact": "Improve user experience by reducing wait times",
            },
            {
                "id": "low_cache_hit",
                "type": RecommendationType.OPTIMIZATION,
                "condition": lambda m: m.get("cache_hit_rate", 1) < 0.3,
                "title": "Improve cache hit rate",
                "description": "Your cache hit rate is low. Consider implementing semantic caching.",
                "action": "Enable and configure response caching",
                "impact": "Reduce latency and costs by 30-50%",
            },
            
            # Reliability
            {
                "id": "high_error_rate",
                "type": RecommendationType.RELIABILITY,
                "condition": lambda m: m.get("error_rate", 0) > 0.05,
                "title": "Address high error rate",
                "description": "Your error rate is above 5%. Review error logs and implement retry logic.",
                "action": "Analyze error patterns and implement fixes",
                "impact": "Improve success rate and user satisfaction",
            },
            {
                "id": "missing_fallback",
                "type": RecommendationType.RELIABILITY,
                "condition": lambda m: not m.get("has_fallback", False) and m.get("is_critical", False),
                "title": "Add fallback for critical agents",
                "description": "Critical agents should have fallback models configured.",
                "action": "Configure fallback models for critical agents",
                "impact": "Improve availability during provider outages",
            },
            
            # Scaling
            {
                "id": "approaching_rate_limit",
                "type": RecommendationType.SCALING,
                "condition": lambda m: m.get("rate_limit_usage", 0) > 0.8,
                "title": "Rate limit approaching",
                "description": "You're using 80%+ of your rate limit. Consider upgrading or implementing queuing.",
                "action": "Request rate limit increase or implement request queuing",
                "impact": "Prevent throttling and maintain service quality",
            },
        ]
    
    def analyze(self, metrics: Dict[str, Any]) -> List[Recommendation]:
        """
        Analisa métricas e gera recomendações.
        
        Args:
            metrics: Dicionário de métricas
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        for rule in self._rules:
            try:
                if rule["condition"](metrics):
                    rec = Recommendation(
                        id=rule["id"],
                        type=rule["type"],
                        priority=self._determine_priority(rule, metrics),
                        title=rule["title"],
                        description=rule["description"],
                        action=rule["action"],
                        expected_impact=rule.get("impact", ""),
                        confidence=0.8
                    )
                    recommendations.append(rec)
                    self._recommendations[rec.id] = rec
                    
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['id']}: {e}")
        
        return sorted(recommendations, key=lambda r: self._priority_order(r.priority), reverse=True)
    
    def _determine_priority(self, rule: Dict, metrics: Dict) -> RecommendationPriority:
        """Determina prioridade baseado no impacto."""
        rule_type = rule["type"]
        
        if rule_type == RecommendationType.RELIABILITY:
            error_rate = metrics.get("error_rate", 0)
            if error_rate > 0.2:
                return RecommendationPriority.CRITICAL
            elif error_rate > 0.1:
                return RecommendationPriority.HIGH
        
        if rule_type == RecommendationType.COST_SAVING:
            monthly_cost = metrics.get("estimated_monthly_cost", 0)
            if monthly_cost > 1000:
                return RecommendationPriority.HIGH
        
        return RecommendationPriority.MEDIUM
    
    def _priority_order(self, priority: RecommendationPriority) -> int:
        """Ordem numérica de prioridade."""
        return {
            RecommendationPriority.LOW: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.CRITICAL: 4,
        }.get(priority, 0)
    
    def get_recommendation(self, rec_id: str) -> Optional[Recommendation]:
        """Obtém recomendação por ID."""
        return self._recommendations.get(rec_id)
    
    def dismiss(self, rec_id: str) -> bool:
        """Dispensa recomendação."""
        if rec_id in self._recommendations:
            self._recommendations[rec_id].dismissed = True
            return True
        return False
    
    def mark_implemented(self, rec_id: str) -> bool:
        """Marca recomendação como implementada."""
        if rec_id in self._recommendations:
            self._recommendations[rec_id].implemented = True
            return True
        return False
    
    def get_active_recommendations(self) -> List[Recommendation]:
        """Lista recomendações ativas (não dispensadas)."""
        return [
            r for r in self._recommendations.values()
            if not r.dismissed and not r.implemented
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Resumo de recomendações."""
        all_recs = list(self._recommendations.values())
        active = self.get_active_recommendations()
        
        return {
            "total": len(all_recs),
            "active": len(active),
            "dismissed": len([r for r in all_recs if r.dismissed]),
            "implemented": len([r for r in all_recs if r.implemented]),
            "byType": {
                t.value: len([r for r in active if r.type == t])
                for t in RecommendationType
            },
            "byPriority": {
                p.value: len([r for r in active if r.priority == p])
                for p in RecommendationPriority
            },
            "estimatedSavings": sum(r.estimated_savings or 0 for r in active),
        }


# Singleton
_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Obtém engine de recomendações."""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine

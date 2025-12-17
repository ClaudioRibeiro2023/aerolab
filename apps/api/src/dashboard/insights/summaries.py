"""
Insight Summaries - Resumos em linguagem natural.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class InsightSummary:
    """Resumo de insights."""
    period: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Resumo geral
    headline: str = ""
    summary: str = ""
    
    # Key metrics
    key_metrics: List[Dict[str, Any]] = field(default_factory=list)
    
    # Highlights
    highlights: List[str] = field(default_factory=list)
    
    # Concerns
    concerns: List[str] = field(default_factory=list)
    
    # Recommendations
    top_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "period": self.period,
            "generatedAt": self.generated_at.isoformat(),
            "headline": self.headline,
            "summary": self.summary,
            "keyMetrics": self.key_metrics,
            "highlights": self.highlights,
            "concerns": self.concerns,
            "topRecommendations": self.top_recommendations,
        }


class InsightSummarizer:
    """
    Gerador de resumos em linguagem natural.
    
    Transforma métricas em insights acionáveis.
    """
    
    def __init__(self):
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Templates de texto."""
        return {
            "headline_positive": "Strong performance this {period} with {highlight}",
            "headline_neutral": "Stable performance this {period}",
            "headline_negative": "Performance issues detected this {period}",
            
            "metric_up": "{metric} increased by {change}% compared to last {period}",
            "metric_down": "{metric} decreased by {change}% compared to last {period}",
            "metric_stable": "{metric} remained stable this {period}",
            
            "highlight_success": "Success rate improved to {value}%",
            "highlight_cost": "Cost per request reduced by {value}%",
            "highlight_latency": "P95 latency improved by {value}ms",
            
            "concern_error": "Error rate increased to {value}%",
            "concern_latency": "P95 latency increased to {value}ms",
            "concern_cost": "Costs increased by {value}%",
        }
    
    def generate_summary(
        self,
        metrics: Dict[str, Any],
        period: str = "week",
        previous_metrics: Optional[Dict[str, Any]] = None
    ) -> InsightSummary:
        """
        Gera resumo de insights.
        
        Args:
            metrics: Métricas atuais
            period: Período (day, week, month)
            previous_metrics: Métricas do período anterior
        """
        summary = InsightSummary(period=period)
        
        # Extrair métricas chave
        total_requests = metrics.get("total_requests", 0)
        success_rate = metrics.get("success_rate", 0) * 100
        avg_latency = metrics.get("avg_latency_ms", 0)
        p95_latency = metrics.get("p95_latency_ms", 0)
        total_cost = metrics.get("total_cost_usd", 0)
        error_rate = metrics.get("error_rate", 0) * 100
        
        # Key metrics
        summary.key_metrics = [
            {"name": "Total Requests", "value": total_requests, "format": "number"},
            {"name": "Success Rate", "value": success_rate, "format": "percent"},
            {"name": "Avg Latency", "value": avg_latency, "format": "ms"},
            {"name": "Total Cost", "value": total_cost, "format": "currency"},
        ]
        
        # Comparar com período anterior
        if previous_metrics:
            changes = self._calculate_changes(metrics, previous_metrics)
            summary.key_metrics = [
                {**m, "change": changes.get(m["name"].lower().replace(" ", "_"), 0)}
                for m in summary.key_metrics
            ]
        
        # Determinar sentiment
        sentiment = self._determine_sentiment(metrics, previous_metrics)
        
        # Gerar headline
        if sentiment == "positive":
            highlight = self._get_top_highlight(metrics, previous_metrics)
            summary.headline = f"Strong performance this {period} with {highlight}"
        elif sentiment == "negative":
            summary.headline = f"Performance issues detected this {period}"
        else:
            summary.headline = f"Stable performance this {period}"
        
        # Gerar highlights
        summary.highlights = self._generate_highlights(metrics, previous_metrics)
        
        # Gerar concerns
        summary.concerns = self._generate_concerns(metrics)
        
        # Gerar summary text
        summary.summary = self._generate_summary_text(
            metrics, previous_metrics, period
        )
        
        # Top recommendations
        summary.top_recommendations = self._generate_quick_recommendations(metrics)
        
        return summary
    
    def _calculate_changes(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcula mudanças percentuais."""
        changes = {}
        
        mappings = {
            "total_requests": "total_requests",
            "success_rate": "success_rate",
            "avg_latency": "avg_latency_ms",
            "total_cost": "total_cost_usd",
        }
        
        for key, metric_key in mappings.items():
            curr_val = current.get(metric_key, 0)
            prev_val = previous.get(metric_key, 0)
            
            if prev_val > 0:
                change = ((curr_val - prev_val) / prev_val) * 100
                changes[key] = round(change, 1)
            else:
                changes[key] = 0
        
        return changes
    
    def _determine_sentiment(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]]
    ) -> str:
        """Determina sentiment geral."""
        success_rate = current.get("success_rate", 0)
        error_rate = current.get("error_rate", 0)
        
        if success_rate > 0.95 and error_rate < 0.02:
            return "positive"
        elif success_rate < 0.90 or error_rate > 0.05:
            return "negative"
        
        if previous:
            curr_success = current.get("success_rate", 0)
            prev_success = previous.get("success_rate", 0)
            
            if curr_success > prev_success + 0.02:
                return "positive"
            elif curr_success < prev_success - 0.02:
                return "negative"
        
        return "neutral"
    
    def _get_top_highlight(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]]
    ) -> str:
        """Obtém highlight principal."""
        success_rate = current.get("success_rate", 0) * 100
        
        if success_rate >= 99:
            return f"{success_rate:.1f}% success rate"
        
        if previous:
            curr_cost = current.get("total_cost_usd", 0)
            prev_cost = previous.get("total_cost_usd", 0)
            
            if prev_cost > 0 and curr_cost < prev_cost * 0.8:
                savings = (1 - curr_cost / prev_cost) * 100
                return f"{savings:.0f}% cost reduction"
        
        return f"{success_rate:.1f}% success rate"
    
    def _generate_highlights(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Gera lista de highlights."""
        highlights = []
        
        success_rate = current.get("success_rate", 0) * 100
        if success_rate >= 98:
            highlights.append(f"Excellent success rate of {success_rate:.1f}%")
        
        p95_latency = current.get("p95_latency_ms", 0)
        if p95_latency > 0 and p95_latency < 1000:
            highlights.append(f"Fast response times with P95 at {p95_latency:.0f}ms")
        
        if previous:
            curr_cost = current.get("total_cost_usd", 0)
            prev_cost = previous.get("total_cost_usd", 0)
            
            if prev_cost > 0 and curr_cost < prev_cost:
                savings = prev_cost - curr_cost
                highlights.append(f"Saved ${savings:.2f} compared to previous period")
        
        total_requests = current.get("total_requests", 0)
        if total_requests > 0:
            highlights.append(f"Processed {total_requests:,} requests")
        
        return highlights[:4]
    
    def _generate_concerns(self, current: Dict[str, Any]) -> List[str]:
        """Gera lista de preocupações."""
        concerns = []
        
        error_rate = current.get("error_rate", 0) * 100
        if error_rate > 5:
            concerns.append(f"High error rate of {error_rate:.1f}% needs attention")
        elif error_rate > 2:
            concerns.append(f"Error rate of {error_rate:.1f}% is above target")
        
        p95_latency = current.get("p95_latency_ms", 0)
        if p95_latency > 5000:
            concerns.append(f"P95 latency of {p95_latency:.0f}ms may impact user experience")
        elif p95_latency > 3000:
            concerns.append(f"P95 latency of {p95_latency:.0f}ms is higher than recommended")
        
        cost_per_request = current.get("avg_cost_per_request", 0)
        if cost_per_request > 0.1:
            concerns.append(f"Average cost per request (${cost_per_request:.4f}) is high")
        
        return concerns[:3]
    
    def _generate_summary_text(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]],
        period: str
    ) -> str:
        """Gera texto de resumo."""
        parts = []
        
        total_requests = current.get("total_requests", 0)
        success_rate = current.get("success_rate", 0) * 100
        total_cost = current.get("total_cost_usd", 0)
        
        parts.append(
            f"This {period}, your system processed {total_requests:,} requests "
            f"with a {success_rate:.1f}% success rate."
        )
        
        if total_cost > 0:
            parts.append(f"Total LLM costs were ${total_cost:.2f}.")
        
        if previous:
            changes = self._calculate_changes(current, previous)
            req_change = changes.get("total_requests", 0)
            
            if abs(req_change) > 10:
                direction = "increased" if req_change > 0 else "decreased"
                parts.append(
                    f"Request volume {direction} by {abs(req_change):.0f}% "
                    f"compared to the previous {period}."
                )
        
        return " ".join(parts)
    
    def _generate_quick_recommendations(
        self,
        current: Dict[str, Any]
    ) -> List[str]:
        """Gera recomendações rápidas."""
        recommendations = []
        
        error_rate = current.get("error_rate", 0)
        if error_rate > 0.03:
            recommendations.append("Review and address the top error patterns")
        
        p95_latency = current.get("p95_latency_ms", 0)
        if p95_latency > 3000:
            recommendations.append("Consider implementing response caching")
        
        cache_hit = current.get("cache_hit_rate", 0)
        if cache_hit < 0.3:
            recommendations.append("Enable semantic caching to reduce costs and latency")
        
        cost_per_request = current.get("avg_cost_per_request", 0)
        if cost_per_request > 0.05:
            recommendations.append("Evaluate using smaller models for simple tasks")
        
        return recommendations[:3]
    
    def generate_daily_digest(
        self,
        metrics: Dict[str, Any],
        anomalies: List[Dict] = None,
        alerts: List[Dict] = None
    ) -> str:
        """Gera digest diário em texto."""
        lines = []
        lines.append("# Daily Dashboard Digest\n")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # Overview
        lines.append("## Overview")
        summary = self.generate_summary(metrics, "day")
        lines.append(f"{summary.headline}\n")
        lines.append(f"{summary.summary}\n")
        
        # Key Metrics
        lines.append("\n## Key Metrics")
        for metric in summary.key_metrics:
            change_str = ""
            if "change" in metric:
                change = metric["change"]
                arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                change_str = f" ({arrow}{abs(change):.1f}%)"
            lines.append(f"- **{metric['name']}**: {metric['value']}{change_str}")
        
        # Highlights
        if summary.highlights:
            lines.append("\n## Highlights")
            for h in summary.highlights:
                lines.append(f"- ✅ {h}")
        
        # Concerns
        if summary.concerns:
            lines.append("\n## Concerns")
            for c in summary.concerns:
                lines.append(f"- ⚠️ {c}")
        
        # Anomalies
        if anomalies:
            lines.append("\n## Anomalies Detected")
            for a in anomalies[:5]:
                lines.append(f"- 🔍 {a.get('description', 'Unknown anomaly')}")
        
        # Recommendations
        if summary.top_recommendations:
            lines.append("\n## Recommendations")
            for r in summary.top_recommendations:
                lines.append(f"- 💡 {r}")
        
        return "\n".join(lines)


# Singleton
_summarizer: Optional[InsightSummarizer] = None


def get_summarizer() -> InsightSummarizer:
    """Obtém summarizer."""
    global _summarizer
    if _summarizer is None:
        _summarizer = InsightSummarizer()
    return _summarizer

"""
Workflow Optimizer - Otimização de workflows com AI.

Features:
- Análise de performance
- Sugestões de otimização
- Detecção de gargalos
- Recomendações de paralelização
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class OptimizationType(Enum):
    """Tipos de otimização."""
    PERFORMANCE = "performance"       # Reduzir latência
    COST = "cost"                     # Reduzir custos
    RELIABILITY = "reliability"       # Aumentar confiabilidade
    PARALLELIZATION = "parallelization"  # Paralelizar steps
    CACHING = "caching"               # Adicionar cache


class Priority(Enum):
    """Prioridade da recomendação."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationRecommendation:
    """Recomendação de otimização."""
    id: str
    type: OptimizationType
    priority: Priority
    title: str
    description: str
    impact: str
    steps_affected: List[str] = field(default_factory=list)
    estimated_improvement: Optional[float] = None  # Percentual
    implementation_effort: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "steps_affected": self.steps_affected,
            "estimated_improvement": self.estimated_improvement,
            "implementation_effort": self.implementation_effort
        }


@dataclass
class PerformanceMetrics:
    """Métricas de performance para análise."""
    total_duration_ms: float = 0
    step_durations: Dict[str, float] = field(default_factory=dict)
    bottleneck_step: Optional[str] = None
    parallelizable_steps: List[List[str]] = field(default_factory=list)
    token_usage: int = 0
    estimated_cost_usd: float = 0


class WorkflowOptimizer:
    """
    Otimizador de workflows.
    
    Exemplo:
        optimizer = WorkflowOptimizer()
        
        # Analisar workflow
        recommendations = optimizer.analyze(workflow_definition, execution_history)
        
        for rec in recommendations:
            print(f"{rec.priority.value}: {rec.title}")
            print(f"  Impact: {rec.impact}")
    """
    
    def __init__(self):
        self._recommendation_counter = 0
    
    def analyze(
        self,
        workflow: Dict[str, Any],
        execution_history: Optional[List[Dict]] = None
    ) -> List[OptimizationRecommendation]:
        """
        Analisa workflow e retorna recomendações.
        
        Args:
            workflow: Definição do workflow
            execution_history: Histórico de execuções para análise
        """
        recommendations = []
        
        # Análise estrutural
        recommendations.extend(self._analyze_structure(workflow))
        
        # Análise de paralelização
        recommendations.extend(self._analyze_parallelization(workflow))
        
        # Análise de performance (se tiver histórico)
        if execution_history:
            recommendations.extend(self._analyze_performance(workflow, execution_history))
        
        # Análise de custos
        recommendations.extend(self._analyze_costs(workflow))
        
        # Análise de confiabilidade
        recommendations.extend(self._analyze_reliability(workflow))
        
        # Ordenar por prioridade
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority.value, 2))
        
        return recommendations
    
    def _generate_id(self) -> str:
        self._recommendation_counter += 1
        return f"opt_{self._recommendation_counter}"
    
    def _analyze_structure(self, workflow: Dict) -> List[OptimizationRecommendation]:
        """Analisa estrutura do workflow."""
        recommendations = []
        steps = workflow.get("steps", [])
        
        # Verificar steps sequenciais que poderiam ser paralelos
        sequential_agents = []
        for step in steps:
            if step.get("type") == "agent":
                sequential_agents.append(step.get("id"))
            else:
                if len(sequential_agents) >= 3:
                    recommendations.append(OptimizationRecommendation(
                        id=self._generate_id(),
                        type=OptimizationType.PARALLELIZATION,
                        priority=Priority.MEDIUM,
                        title="Considerar paralelização de agentes",
                        description=f"{len(sequential_agents)} agentes sequenciais poderiam rodar em paralelo",
                        impact=f"Redução potencial de {(len(sequential_agents)-1)*30}% no tempo",
                        steps_affected=sequential_agents.copy(),
                        estimated_improvement=30.0
                    ))
                sequential_agents = []
        
        # Verificar workflow muito longo
        if len(steps) > 10:
            recommendations.append(OptimizationRecommendation(
                id=self._generate_id(),
                type=OptimizationType.PERFORMANCE,
                priority=Priority.LOW,
                title="Workflow extenso",
                description=f"Workflow tem {len(steps)} steps. Considere dividir em sub-workflows",
                impact="Melhor manutenibilidade e possibilidade de reuso",
                implementation_effort="high"
            ))
        
        return recommendations
    
    def _analyze_parallelization(self, workflow: Dict) -> List[OptimizationRecommendation]:
        """Identifica oportunidades de paralelização."""
        recommendations = []
        steps = workflow.get("steps", [])
        
        # Identificar steps independentes
        step_deps = self._build_dependency_graph(steps)
        independent_groups = self._find_independent_groups(step_deps)
        
        for group in independent_groups:
            if len(group) >= 2:
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_id(),
                    type=OptimizationType.PARALLELIZATION,
                    priority=Priority.HIGH,
                    title="Steps independentes podem rodar em paralelo",
                    description=f"Steps {', '.join(group)} não têm dependências entre si",
                    impact="Execução paralela pode reduzir tempo total significativamente",
                    steps_affected=list(group),
                    estimated_improvement=min(50.0, len(group) * 20.0)
                ))
        
        return recommendations
    
    def _analyze_performance(
        self,
        workflow: Dict,
        history: List[Dict]
    ) -> List[OptimizationRecommendation]:
        """Analisa performance baseado no histórico."""
        recommendations = []
        
        if not history:
            return recommendations
        
        # Calcular métricas
        step_times: Dict[str, List[float]] = {}
        
        for execution in history:
            for step_result in execution.get("step_results", []):
                step_id = step_result.get("step_id")
                duration = step_result.get("duration_ms", 0)
                
                if step_id not in step_times:
                    step_times[step_id] = []
                step_times[step_id].append(duration)
        
        # Identificar gargalos
        for step_id, times in step_times.items():
            avg_time = sum(times) / len(times)
            
            if avg_time > 5000:  # > 5 segundos
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_id(),
                    type=OptimizationType.PERFORMANCE,
                    priority=Priority.HIGH,
                    title=f"Gargalo de performance: {step_id}",
                    description=f"Step tem latência média de {avg_time/1000:.1f}s",
                    impact="Otimizar este step pode reduzir tempo total significativamente",
                    steps_affected=[step_id],
                    estimated_improvement=20.0
                ))
            
            # Verificar variabilidade alta
            if len(times) >= 3:
                avg = sum(times) / len(times)
                variance = sum((t - avg) ** 2 for t in times) / len(times)
                if variance > avg * 0.5:
                    recommendations.append(OptimizationRecommendation(
                        id=self._generate_id(),
                        type=OptimizationType.RELIABILITY,
                        priority=Priority.MEDIUM,
                        title=f"Alta variabilidade: {step_id}",
                        description="Tempo de execução varia muito entre execuções",
                        impact="Adicionar timeout e retry pode melhorar previsibilidade",
                        steps_affected=[step_id]
                    ))
        
        return recommendations
    
    def _analyze_costs(self, workflow: Dict) -> List[OptimizationRecommendation]:
        """Analisa custos do workflow."""
        recommendations = []
        steps = workflow.get("steps", [])
        
        # Contar steps de agente (que usam tokens)
        agent_steps = [s for s in steps if s.get("type") == "agent"]
        
        if len(agent_steps) > 5:
            recommendations.append(OptimizationRecommendation(
                id=self._generate_id(),
                type=OptimizationType.COST,
                priority=Priority.MEDIUM,
                title="Muitos steps de agente",
                description=f"{len(agent_steps)} agentes podem gerar alto custo de tokens",
                impact="Consolidar prompts ou usar modelos mais baratos pode reduzir custos",
                steps_affected=[s.get("id") for s in agent_steps],
                estimated_improvement=30.0
            ))
        
        # Verificar agentes sem limite de tokens
        for step in agent_steps:
            config = step.get("config", {})
            if not config.get("max_tokens"):
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_id(),
                    type=OptimizationType.COST,
                    priority=Priority.LOW,
                    title=f"Sem limite de tokens: {step.get('id')}",
                    description="Definir max_tokens pode evitar custos inesperados",
                    impact="Controle de custos mais previsível",
                    steps_affected=[step.get("id")]
                ))
        
        return recommendations
    
    def _analyze_reliability(self, workflow: Dict) -> List[OptimizationRecommendation]:
        """Analisa confiabilidade do workflow."""
        recommendations = []
        steps = workflow.get("steps", [])
        
        for step in steps:
            # Verificar retry policy
            if not step.get("retry_policy"):
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_id(),
                    type=OptimizationType.RELIABILITY,
                    priority=Priority.MEDIUM,
                    title=f"Sem retry policy: {step.get('id')}",
                    description="Adicionar retry policy pode melhorar resiliência",
                    impact="Reduz falhas por erros transientes",
                    steps_affected=[step.get("id")]
                ))
            
            # Verificar timeout
            if not step.get("timeout_seconds"):
                step_type = step.get("type", "")
                if step_type in ("agent", "action"):
                    recommendations.append(OptimizationRecommendation(
                        id=self._generate_id(),
                        type=OptimizationType.RELIABILITY,
                        priority=Priority.LOW,
                        title=f"Sem timeout: {step.get('id')}",
                        description="Definir timeout evita execuções travadas",
                        impact="Previne workflows pendurados",
                        steps_affected=[step.get("id")]
                    ))
        
        return recommendations
    
    def _build_dependency_graph(self, steps: List[Dict]) -> Dict[str, set]:
        """Constrói grafo de dependências."""
        deps = {s.get("id"): set() for s in steps}
        
        for i, step in enumerate(steps):
            step_id = step.get("id")
            
            # Dependência implícita do step anterior
            if i > 0:
                prev_id = steps[i-1].get("id")
                if not step.get("parallel"):  # Se não for explicitamente paralelo
                    deps[step_id].add(prev_id)
            
            # Dependências explícitas
            depends_on = step.get("depends_on", [])
            for dep in depends_on:
                deps[step_id].add(dep)
        
        return deps
    
    def _find_independent_groups(self, deps: Dict[str, set]) -> List[set]:
        """Encontra grupos de steps independentes."""
        groups = []
        processed = set()
        
        for step_id, step_deps in deps.items():
            if step_id in processed:
                continue
            
            # Encontrar steps que não dependem deste
            independent = {step_id}
            
            for other_id, other_deps in deps.items():
                if other_id == step_id or other_id in processed:
                    continue
                
                # Verificar independência mútua
                if step_id not in other_deps and other_id not in deps[step_id]:
                    independent.add(other_id)
            
            if len(independent) >= 2:
                groups.append(independent)
                processed.update(independent)
        
        return groups
    
    def get_quick_wins(
        self,
        recommendations: List[OptimizationRecommendation]
    ) -> List[OptimizationRecommendation]:
        """Retorna quick wins (alto impacto, baixo esforço)."""
        return [
            r for r in recommendations
            if r.priority == Priority.HIGH and r.implementation_effort == "low"
        ]

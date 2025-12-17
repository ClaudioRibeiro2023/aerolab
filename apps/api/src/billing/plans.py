"""
Plan Manager - Gerenciamento de Planos

Gerencia planos de assinatura e features.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from .types import Plan, PlanFeatures


class PlanManager:
    """
    Gerenciador de planos de assinatura.
    
    Features:
    - Planos predefinidos (Free, Pro, Team, Enterprise)
    - Verificação de limites
    - Upgrade/downgrade
    - Comparação de planos
    """
    
    def __init__(self):
        """Inicializa com planos padrão."""
        self._plans: Dict[str, Plan] = {}
        self._user_plans: Dict[str, str] = {}  # user_id -> plan_id
        self._load_default_plans()
    
    def _load_default_plans(self) -> None:
        """Carrega planos padrão."""
        
        # Free Plan
        self._plans["free"] = Plan(
            id="free",
            name="Free",
            description="Perfeito para começar e explorar a plataforma",
            price_monthly=0,
            price_yearly=0,
            features=PlanFeatures(
                max_agents=3,
                max_workflows=5,
                max_api_calls_per_day=100,
                max_tokens_per_month=50000,
                max_storage_mb=100,
                max_team_members=1,
                custom_models=False,
                priority_support=False,
                sso_enabled=False,
                audit_logs=False,
                api_access=True,
                webhooks=False
            ),
            trial_days=0
        )
        
        # Pro Plan
        self._plans["pro"] = Plan(
            id="pro",
            name="Pro",
            description="Para desenvolvedores e pequenas equipes",
            price_monthly=2900,  # $29/mês
            price_yearly=29000,  # $290/ano (2 meses grátis)
            features=PlanFeatures(
                max_agents=20,
                max_workflows=50,
                max_api_calls_per_day=10000,
                max_tokens_per_month=1000000,
                max_storage_mb=5000,
                max_team_members=5,
                custom_models=True,
                priority_support=True,
                sso_enabled=False,
                audit_logs=True,
                api_access=True,
                webhooks=True
            ),
            trial_days=14
        )
        
        # Team Plan
        self._plans["team"] = Plan(
            id="team",
            name="Team",
            description="Para equipes em crescimento",
            price_monthly=9900,  # $99/mês
            price_yearly=99000,  # $990/ano
            features=PlanFeatures(
                max_agents=100,
                max_workflows=200,
                max_api_calls_per_day=100000,
                max_tokens_per_month=10000000,
                max_storage_mb=50000,
                max_team_members=25,
                custom_models=True,
                priority_support=True,
                sso_enabled=True,
                audit_logs=True,
                api_access=True,
                webhooks=True,
                custom_domain=True
            ),
            trial_days=14
        )
        
        # Enterprise Plan
        self._plans["enterprise"] = Plan(
            id="enterprise",
            name="Enterprise",
            description="Para grandes organizações com necessidades customizadas",
            price_monthly=0,  # Custom pricing
            price_yearly=0,
            features=PlanFeatures(
                max_agents=-1,  # Ilimitado
                max_workflows=-1,
                max_api_calls_per_day=-1,
                max_tokens_per_month=-1,
                max_storage_mb=-1,
                max_team_members=-1,
                custom_models=True,
                priority_support=True,
                sso_enabled=True,
                audit_logs=True,
                api_access=True,
                webhooks=True,
                custom_domain=True,
                dedicated_support=True
            ),
            trial_days=30,
            metadata={"contact_sales": True}
        )
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Obtém plano pelo ID."""
        return self._plans.get(plan_id)
    
    def get_all_plans(self, include_inactive: bool = False) -> List[Plan]:
        """Lista todos os planos."""
        plans = list(self._plans.values())
        if not include_inactive:
            plans = [p for p in plans if p.is_active and p.is_public]
        return plans
    
    def add_plan(self, plan: Plan) -> None:
        """Adiciona um novo plano."""
        self._plans[plan.id] = plan
    
    def update_plan(self, plan_id: str, **kwargs) -> Optional[Plan]:
        """Atualiza um plano existente."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        return plan
    
    def assign_plan(
        self,
        user_id: str,
        plan_id: str,
        start_date: Optional[datetime] = None
    ) -> bool:
        """
        Atribui um plano a um usuário.
        
        Args:
            user_id: ID do usuário
            plan_id: ID do plano
            start_date: Data de início (default: agora)
            
        Returns:
            True se atribuição foi bem sucedida
        """
        if plan_id not in self._plans:
            return False
        
        self._user_plans[user_id] = plan_id
        return True
    
    def get_user_plan(self, user_id: str) -> Plan:
        """
        Obtém plano do usuário.
        
        Returns:
            Plano do usuário ou Free se não tiver
        """
        plan_id = self._user_plans.get(user_id, "free")
        return self._plans.get(plan_id, self._plans["free"])
    
    def check_limit(
        self,
        user_id: str,
        limit_type: str,
        current_value: int
    ) -> Dict[str, Any]:
        """
        Verifica se usuário está dentro dos limites.
        
        Args:
            user_id: ID do usuário
            limit_type: Tipo de limite (max_agents, max_workflows, etc)
            current_value: Valor atual
            
        Returns:
            Dict com status e detalhes
        """
        plan = self.get_user_plan(user_id)
        features = plan.features
        
        limit = getattr(features, limit_type, 0)
        
        # -1 significa ilimitado
        if limit == -1:
            return {
                "allowed": True,
                "limit": "unlimited",
                "current": current_value,
                "remaining": "unlimited",
                "plan": plan.name
            }
        
        allowed = current_value < limit
        remaining = max(0, limit - current_value)
        
        return {
            "allowed": allowed,
            "limit": limit,
            "current": current_value,
            "remaining": remaining,
            "plan": plan.name,
            "upgrade_available": not allowed and plan.id != "enterprise"
        }
    
    def can_use_feature(self, user_id: str, feature: str) -> bool:
        """
        Verifica se usuário pode usar uma feature.
        
        Args:
            user_id: ID do usuário
            feature: Nome da feature
            
        Returns:
            True se feature está disponível
        """
        plan = self.get_user_plan(user_id)
        return getattr(plan.features, feature, False)
    
    def compare_plans(
        self,
        plan_id_1: str,
        plan_id_2: str
    ) -> Dict[str, Any]:
        """
        Compara dois planos.
        
        Args:
            plan_id_1: ID do primeiro plano
            plan_id_2: ID do segundo plano
            
        Returns:
            Comparação detalhada
        """
        plan1 = self._plans.get(plan_id_1)
        plan2 = self._plans.get(plan_id_2)
        
        if not plan1 or not plan2:
            return {"error": "Plan not found"}
        
        comparison = {
            "plans": [plan1.name, plan2.name],
            "price_difference_monthly": plan2.price_monthly - plan1.price_monthly,
            "features": {}
        }
        
        # Comparar features
        for attr in dir(plan1.features):
            if attr.startswith("_"):
                continue
            
            val1 = getattr(plan1.features, attr)
            val2 = getattr(plan2.features, attr)
            
            if val1 != val2:
                comparison["features"][attr] = {
                    plan1.name: val1,
                    plan2.name: val2
                }
        
        return comparison
    
    def get_upgrade_options(self, user_id: str) -> List[Plan]:
        """
        Lista opções de upgrade para usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de planos disponíveis para upgrade
        """
        current_plan = self.get_user_plan(user_id)
        
        plan_order = ["free", "pro", "team", "enterprise"]
        current_index = plan_order.index(current_plan.id) if current_plan.id in plan_order else 0
        
        upgrades = []
        for plan_id in plan_order[current_index + 1:]:
            plan = self._plans.get(plan_id)
            if plan and plan.is_active:
                upgrades.append(plan)
        
        return upgrades
    
    def calculate_proration(
        self,
        user_id: str,
        new_plan_id: str,
        days_remaining: int
    ) -> Dict[str, Any]:
        """
        Calcula proration para upgrade/downgrade.
        
        Args:
            user_id: ID do usuário
            new_plan_id: ID do novo plano
            days_remaining: Dias restantes no ciclo atual
            
        Returns:
            Valores de proration
        """
        current_plan = self.get_user_plan(user_id)
        new_plan = self._plans.get(new_plan_id)
        
        if not new_plan:
            return {"error": "New plan not found"}
        
        days_in_month = 30
        
        # Valor restante do plano atual
        current_daily_rate = current_plan.price_monthly / days_in_month
        current_credit = current_daily_rate * days_remaining
        
        # Valor do novo plano para dias restantes
        new_daily_rate = new_plan.price_monthly / days_in_month
        new_charge = new_daily_rate * days_remaining
        
        # Diferença
        proration_amount = new_charge - current_credit
        
        return {
            "current_plan": current_plan.name,
            "new_plan": new_plan.name,
            "days_remaining": days_remaining,
            "current_credit": round(current_credit, 2),
            "new_charge": round(new_charge, 2),
            "proration_amount": round(proration_amount, 2),
            "is_upgrade": proration_amount > 0
        }


# Singleton instance
_plan_manager: Optional[PlanManager] = None


def get_plan_manager() -> PlanManager:
    """Obtém instância singleton do PlanManager."""
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
    return _plan_manager

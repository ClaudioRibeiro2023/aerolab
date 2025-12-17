"""
Governance - Políticas e governança para dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class PolicyType(str, Enum):
    """Tipos de política."""
    DATA_RETENTION = "data_retention"
    NAMING_CONVENTION = "naming_convention"
    ACCESS_CONTROL = "access_control"
    QUERY_LIMIT = "query_limit"
    CONTENT_POLICY = "content_policy"
    COST_LIMIT = "cost_limit"
    RATE_LIMIT = "rate_limit"


class PolicyAction(str, Enum):
    """Ações quando política é violada."""
    WARN = "warn"
    BLOCK = "block"
    LOG = "log"
    NOTIFY = "notify"


class PolicyScope(str, Enum):
    """Escopo de aplicação da política."""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    DASHBOARD = "dashboard"


@dataclass
class PolicyCondition:
    """Condição de uma política."""
    field: str
    operator: str  # eq, neq, contains, regex, gt, lt, gte, lte
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Avalia condição."""
        actual = context.get(self.field)
        
        if self.operator == "eq":
            return actual == self.value
        elif self.operator == "neq":
            return actual != self.value
        elif self.operator == "contains":
            return self.value in str(actual)
        elif self.operator == "regex":
            return bool(re.match(self.value, str(actual)))
        elif self.operator == "gt":
            return actual > self.value
        elif self.operator == "lt":
            return actual < self.value
        elif self.operator == "gte":
            return actual >= self.value
        elif self.operator == "lte":
            return actual <= self.value
        
        return False


@dataclass
class Policy:
    """Política de governança."""
    id: str
    name: str
    description: str = ""
    
    # Tipo e escopo
    type: PolicyType = PolicyType.ACCESS_CONTROL
    scope: PolicyScope = PolicyScope.GLOBAL
    
    # Condições
    conditions: List[PolicyCondition] = field(default_factory=list)
    condition_logic: str = "and"  # and, or
    
    # Ações
    action: PolicyAction = PolicyAction.WARN
    action_params: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    enabled: bool = True
    
    # Aplicação
    applies_to_tenants: List[str] = field(default_factory=list)  # vazio = todos
    applies_to_roles: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    priority: int = 0  # maior = maior prioridade
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Avalia se política é violada."""
        if not self.enabled:
            return False
        
        # Verificar tenant
        if self.applies_to_tenants:
            tenant_id = context.get("tenant_id")
            if tenant_id and tenant_id not in self.applies_to_tenants:
                return False
        
        # Verificar role
        if self.applies_to_roles:
            user_roles = context.get("user_roles", [])
            if not any(r in self.applies_to_roles for r in user_roles):
                return False
        
        # Avaliar condições
        if not self.conditions:
            return False
        
        results = [c.evaluate(context) for c in self.conditions]
        
        if self.condition_logic == "and":
            return all(results)
        else:  # or
            return any(results)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "scope": self.scope.value,
            "conditions": [
                {"field": c.field, "operator": c.operator, "value": c.value}
                for c in self.conditions
            ],
            "conditionLogic": self.condition_logic,
            "action": self.action.value,
            "actionParams": self.action_params,
            "enabled": self.enabled,
            "appliesToTenants": self.applies_to_tenants,
            "appliesToRoles": self.applies_to_roles,
            "createdAt": self.created_at.isoformat(),
            "createdBy": self.created_by,
            "priority": self.priority,
        }


@dataclass
class PolicyViolation:
    """Violação de política."""
    policy_id: str
    policy_name: str
    action: PolicyAction
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""


class GovernanceManager:
    """
    Gerenciador de governança.
    
    Aplica políticas e regras de governança sobre recursos.
    """
    
    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._violations: List[PolicyViolation] = []
        self._action_handlers: Dict[PolicyAction, Callable] = {}
        
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Carrega políticas padrão."""
        # Política de nomenclatura de dashboard
        self.add_policy(Policy(
            id="naming_dashboard",
            name="Dashboard Naming Convention",
            description="Dashboard names must be descriptive",
            type=PolicyType.NAMING_CONVENTION,
            conditions=[
                PolicyCondition("dashboard_name", "regex", r"^[A-Z][\w\s-]{2,49}$"),
            ],
            action=PolicyAction.WARN,
            priority=10,
        ))
        
        # Política de limite de widgets
        self.add_policy(Policy(
            id="widget_limit",
            name="Widget Limit per Dashboard",
            description="Limit widgets per dashboard for performance",
            type=PolicyType.QUERY_LIMIT,
            conditions=[
                PolicyCondition("widget_count", "gt", 50),
            ],
            action=PolicyAction.BLOCK,
            action_params={"message": "Maximum 50 widgets per dashboard"},
            priority=20,
        ))
        
        # Política de custo
        self.add_policy(Policy(
            id="daily_cost_limit",
            name="Daily Cost Limit",
            description="Alert when daily cost exceeds threshold",
            type=PolicyType.COST_LIMIT,
            conditions=[
                PolicyCondition("daily_cost_usd", "gt", 100),
            ],
            action=PolicyAction.NOTIFY,
            action_params={"channel": "admin"},
            priority=30,
        ))
    
    def add_policy(self, policy: Policy):
        """Adiciona política."""
        self._policies[policy.id] = policy
        logger.debug(f"Added policy: {policy.id}")
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Obtém política por ID."""
        return self._policies.get(policy_id)
    
    def list_policies(
        self,
        policy_type: Optional[PolicyType] = None,
        enabled_only: bool = True,
    ) -> List[Policy]:
        """Lista políticas."""
        policies = list(self._policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.type == policy_type]
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        
        return sorted(policies, key=lambda p: p.priority, reverse=True)
    
    def update_policy(
        self,
        policy_id: str,
        **kwargs
    ) -> Optional[Policy]:
        """Atualiza política."""
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        return policy
    
    def enable_policy(self, policy_id: str) -> bool:
        """Habilita política."""
        policy = self._policies.get(policy_id)
        if policy:
            policy.enabled = True
            return True
        return False
    
    def disable_policy(self, policy_id: str) -> bool:
        """Desabilita política."""
        policy = self._policies.get(policy_id)
        if policy:
            policy.enabled = False
            return True
        return False
    
    def delete_policy(self, policy_id: str) -> bool:
        """Remove política."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False
    
    def check_policies(
        self,
        context: Dict[str, Any],
        policy_type: Optional[PolicyType] = None,
    ) -> List[PolicyViolation]:
        """
        Verifica políticas contra contexto.
        
        Args:
            context: Dicionário com informações do contexto
            policy_type: Tipo específico de política a verificar
            
        Returns:
            Lista de violações encontradas
        """
        violations = []
        policies = self.list_policies(policy_type=policy_type)
        
        for policy in policies:
            if policy.evaluate(context):
                violation = PolicyViolation(
                    policy_id=policy.id,
                    policy_name=policy.name,
                    action=policy.action,
                    context=context,
                    message=policy.action_params.get("message", f"Policy '{policy.name}' violated"),
                )
                
                violations.append(violation)
                self._violations.append(violation)
                
                # Executar action handler
                self._handle_violation(policy, violation)
        
        return violations
    
    def _handle_violation(self, policy: Policy, violation: PolicyViolation):
        """Trata violação de política."""
        action = policy.action
        
        if action == PolicyAction.LOG:
            logger.warning(f"Policy violation: {violation.message}")
        elif action == PolicyAction.WARN:
            logger.warning(f"Policy warning: {violation.message}")
        elif action == PolicyAction.NOTIFY:
            # Em implementação real, enviaria notificação
            logger.info(f"Would notify: {violation.message}")
        elif action == PolicyAction.BLOCK:
            logger.error(f"Policy blocked: {violation.message}")
        
        # Handler customizado
        if action in self._action_handlers:
            try:
                self._action_handlers[action](violation)
            except Exception as e:
                logger.error(f"Error in action handler: {e}")
    
    def set_action_handler(self, action: PolicyAction, handler: Callable):
        """Define handler para ação."""
        self._action_handlers[action] = handler
    
    def should_block(
        self,
        context: Dict[str, Any],
        policy_type: Optional[PolicyType] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica se operação deve ser bloqueada.
        
        Returns:
            (should_block, message)
        """
        violations = self.check_policies(context, policy_type)
        
        for v in violations:
            if v.action == PolicyAction.BLOCK:
                return True, v.message
        
        return False, None
    
    def get_violations(
        self,
        policy_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PolicyViolation]:
        """Obtém violações recentes."""
        violations = self._violations
        
        if policy_id:
            violations = [v for v in violations if v.policy_id == policy_id]
        
        return sorted(
            violations,
            key=lambda v: v.timestamp,
            reverse=True
        )[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas de governança."""
        return {
            "totalPolicies": len(self._policies),
            "enabledPolicies": len([p for p in self._policies.values() if p.enabled]),
            "totalViolations": len(self._violations),
            "violationsByPolicy": {
                p.name: len([v for v in self._violations if v.policy_id == p.id])
                for p in self._policies.values()
            },
            "violationsByAction": {
                action.value: len([v for v in self._violations if v.action == action])
                for action in PolicyAction
            },
        }


# Singleton
_manager: Optional[GovernanceManager] = None


def get_governance_manager() -> GovernanceManager:
    """Obtém gerenciador de governança."""
    global _manager
    if _manager is None:
        _manager = GovernanceManager()
    return _manager

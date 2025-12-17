"""
Rules Engine - Tipos e Estruturas de Dados

Define todas as estruturas para o sistema de regras.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Union, Callable
from enum import Enum
import uuid
import re


class RuleSeverity(str, Enum):
    """Severidade de uma regra/violação."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleCategory(str, Enum):
    """Categoria de regra."""
    COMPLIANCE = "compliance"
    SECURITY = "security"
    QUALITY = "quality"
    BUSINESS = "business"
    CUSTOM = "custom"


class RuleAction(str, Enum):
    """Ação a tomar quando regra é violada."""
    LOG = "log"           # Apenas registrar
    WARN = "warn"         # Avisar mas permitir
    BLOCK = "block"       # Bloquear output
    FIX = "fix"           # Tentar corrigir automaticamente
    REGENERATE = "regenerate"  # Solicitar regeneração


class ConditionOperator(str, Enum):
    """Operadores para condições."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"       # Regex
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    LENGTH_GREATER = "length_greater"
    LENGTH_LESS = "length_less"
    # Composição
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class RuleCondition:
    """
    Condição de uma regra.
    
    Pode ser:
    - Simples: target_field + operator + value
    - Composta: operator (AND/OR) + conditions
    """
    target_field: Optional[str] = None
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Any = None
    
    # Para condições compostas
    sub_conditions: list["RuleCondition"] = field(default_factory=list)
    
    # Função customizada
    custom_fn: Optional[Callable[[Any], bool]] = None
    
    def evaluate(self, data: dict) -> bool:
        """
        Avalia a condição contra os dados.
        
        Args:
            data: Dicionário com dados a avaliar
            
        Returns:
            True se condição é satisfeita
        """
        # Função customizada
        if self.custom_fn:
            return self.custom_fn(data)
        
        # Condições compostas
        if self.operator == ConditionOperator.AND:
            return all(c.evaluate(data) for c in self.sub_conditions)
        
        if self.operator == ConditionOperator.OR:
            return any(c.evaluate(data) for c in self.sub_conditions)
        
        if self.operator == ConditionOperator.NOT:
            return not self.sub_conditions[0].evaluate(data) if self.sub_conditions else False
        
        # Condições simples
        if not self.target_field:
            return False
        
        # Obter valor do campo (suporta nested fields com dot notation)
        field_value = self._get_field_value(data, self.target_field)
        
        return self._evaluate_operator(field_value)
    
    def _get_field_value(self, data: dict, field_path: str) -> Any:
        """Obtém valor de campo com suporte a dot notation."""
        parts = field_path.split(".")
        value = data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def _evaluate_operator(self, field_value: Any) -> bool:
        """Avalia operador contra valor do campo."""
        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        
        elif self.operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, str):
                return self.value in field_value
            elif isinstance(field_value, (list, tuple)):
                return self.value in field_value
            return False
        
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, str):
                return self.value not in field_value
            elif isinstance(field_value, (list, tuple)):
                return self.value not in field_value
            return True
        
        elif self.operator == ConditionOperator.MATCHES:
            if isinstance(field_value, str) and isinstance(self.value, str):
                return bool(re.search(self.value, field_value))
            return False
        
        elif self.operator == ConditionOperator.STARTS_WITH:
            return str(field_value).startswith(str(self.value)) if field_value else False
        
        elif self.operator == ConditionOperator.ENDS_WITH:
            return str(field_value).endswith(str(self.value)) if field_value else False
        
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value if field_value is not None else False
        
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value if field_value is not None else False
        
        elif self.operator == ConditionOperator.IN:
            return field_value in self.value if self.value else False
        
        elif self.operator == ConditionOperator.NOT_IN:
            return field_value not in self.value if self.value else True
        
        elif self.operator == ConditionOperator.EXISTS:
            return field_value is not None
        
        elif self.operator == ConditionOperator.NOT_EXISTS:
            return field_value is None
        
        elif self.operator == ConditionOperator.LENGTH_GREATER:
            return len(field_value) > self.value if field_value else False
        
        elif self.operator == ConditionOperator.LENGTH_LESS:
            return len(field_value) < self.value if field_value else True
        
        return False
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result = {"operator": self.operator.value}
        
        if self.field:
            result["field"] = self.field
        if self.value is not None:
            result["value"] = self.value
        if self.conditions:
            result["conditions"] = [c.to_dict() for c in self.conditions]
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "RuleCondition":
        """Cria RuleCondition a partir de dicionário."""
        conditions = [
            cls.from_dict(c) for c in data.get("conditions", [])
        ]
        
        return cls(
            field=data.get("field"),
            operator=ConditionOperator(data.get("operator", "equals")),
            value=data.get("value"),
            conditions=conditions
        )
    
    # Factory methods para facilitar criação
    
    @classmethod
    def equals(cls, field: str, value: Any) -> "RuleCondition":
        return cls(field=field, operator=ConditionOperator.EQUALS, value=value)
    
    @classmethod
    def contains(cls, field: str, value: str) -> "RuleCondition":
        return cls(field=field, operator=ConditionOperator.CONTAINS, value=value)
    
    @classmethod
    def matches(cls, field: str, pattern: str) -> "RuleCondition":
        return cls(field=field, operator=ConditionOperator.MATCHES, value=pattern)
    
    @classmethod
    def and_(*conditions: "RuleCondition") -> "RuleCondition":
        return cls(operator=ConditionOperator.AND, conditions=list(conditions))
    
    @classmethod
    def or_(*conditions: "RuleCondition") -> "RuleCondition":
        return cls(operator=ConditionOperator.OR, conditions=list(conditions))
    
    @classmethod
    def custom(cls, fn: Callable[[Any], bool]) -> "RuleCondition":
        return cls(custom_fn=fn)


@dataclass
class Rule:
    """
    Definição de uma regra.
    
    Uma regra consiste em:
    - Condição: quando a regra se aplica
    - Ação: o que fazer quando violada
    - Metadata: informações adicionais
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Condição
    condition: Optional[RuleCondition] = None
    
    # Ação
    action: RuleAction = RuleAction.WARN
    
    # Classificação
    category: RuleCategory = RuleCategory.CUSTOM
    severity: RuleSeverity = RuleSeverity.WARNING
    
    # Estado
    enabled: bool = True
    
    # Tags para filtragem
    tags: list[str] = field(default_factory=list)
    
    # Mensagem de violação
    violation_message: str = ""
    
    # Sugestão de correção
    fix_suggestion: str = ""
    
    # Prioridade (maior = mais importante)
    priority: int = 0
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def evaluate(self, data: dict) -> bool:
        """
        Avalia se a regra foi violada.
        
        Args:
            data: Dados a avaliar
            
        Returns:
            True se regra foi VIOLADA (condição satisfeita)
        """
        if not self.enabled:
            return False
        
        if not self.condition:
            return False
        
        return self.condition.evaluate(data)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition.to_dict() if self.condition else None,
            "action": self.action.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "tags": self.tags,
            "violation_message": self.violation_message,
            "fix_suggestion": self.fix_suggestion,
            "priority": self.priority,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        """Cria Rule a partir de dicionário."""
        condition = None
        if data.get("condition"):
            condition = RuleCondition.from_dict(data["condition"])
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            condition=condition,
            action=RuleAction(data.get("action", "warn")),
            category=RuleCategory(data.get("category", "custom")),
            severity=RuleSeverity(data.get("severity", "warning")),
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
            violation_message=data.get("violation_message", ""),
            fix_suggestion=data.get("fix_suggestion", ""),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class Violation:
    """
    Representa uma violação de regra.
    """
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    category: RuleCategory
    action: RuleAction = RuleAction.WARN
    
    # Detalhes
    message: str = ""
    matched_field: Optional[str] = None
    matched_content: Optional[str] = None
    value: Any = None
    
    # Correção
    suggestion: str = ""
    auto_fix: Optional[str] = None
    
    # Contexto
    extra_context: Optional[dict] = None
    
    # Timestamp
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.extra_context is None:
            self.extra_context = {}
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "action": self.action.value,
            "message": self.message,
            "matched_field": self.matched_field,
            "matched_content": self.matched_content,
            "value": str(self.value)[:100] if self.value else None,
            "suggestion": self.suggestion,
            "detected_at": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class ValidationResult:
    """
    Resultado de validação.
    """
    passed: bool = True
    violations: list[Violation] = field(default_factory=list)
    
    # Ações recomendadas
    should_block: bool = False
    should_regenerate: bool = False
    
    # Output corrigido (se auto-fix aplicado)
    fixed_output: Optional[str] = None
    
    # Métricas
    rules_evaluated: int = 0
    evaluation_time_ms: float = 0
    
    # Metadados
    metadata: dict = field(default_factory=dict)
    
    def add_violation(self, violation: Violation) -> None:
        """Adiciona uma violação."""
        self.violations.append(violation)
        self.passed = False
        
        if violation.action == RuleAction.BLOCK:
            self.should_block = True
        elif violation.action == RuleAction.REGENERATE:
            self.should_regenerate = True
    
    @property
    def critical_count(self) -> int:
        """Número de violações críticas."""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.CRITICAL)
    
    @property
    def error_count(self) -> int:
        """Número de violações error."""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Número de violações warning."""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.WARNING)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "should_block": self.should_block,
            "should_regenerate": self.should_regenerate,
            "summary": {
                "critical": self.critical_count,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "total": len(self.violations)
            },
            "rules_evaluated": self.rules_evaluated,
            "evaluation_time_ms": self.evaluation_time_ms
        }


@dataclass
class RuleSet:
    """
    Conjunto de regras agrupadas.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    rules: list[Rule] = field(default_factory=list)
    
    # Estado
    enabled: bool = True
    
    # Configurações
    fail_fast: bool = False  # Parar na primeira violação
    
    # Metadados
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    
    def add_rule(self, rule: Rule) -> None:
        """Adiciona uma regra."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove uma regra pelo ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Obtém regra pelo ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_rules_by_category(self, category: RuleCategory) -> list[Rule]:
        """Filtra regras por categoria."""
        return [r for r in self.rules if r.category == category]
    
    def get_rules_by_tag(self, tag: str) -> list[Rule]:
        """Filtra regras por tag."""
        return [r for r in self.rules if tag in r.tags]
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
            "enabled": self.enabled,
            "fail_fast": self.fail_fast,
            "version": self.version,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RuleSet":
        """Cria RuleSet a partir de dicionário."""
        rules = [Rule.from_dict(r) for r in data.get("rules", [])]
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            rules=rules,
            enabled=data.get("enabled", True),
            fail_fast=data.get("fail_fast", False),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", [])
        )

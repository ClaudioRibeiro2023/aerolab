"""
Rules Engine - Motor de Regras Principal

Coordena validação de regras e validadores.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, Any
import logging
import os

from .types import (
    Rule, RuleCondition, RuleAction, RuleSeverity, RuleCategory,
    ValidationResult, Violation, RuleSet
)
from .validators import (
    BaseValidator, PIIValidator, SecurityValidator,
    FormatValidator, ComplianceValidator, ToxicityValidator,
    create_default_validators
)


logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Motor de regras principal.
    
    Gerencia:
    - Regras customizadas
    - Validadores especializados
    - Pipeline de validação
    - Histórico e métricas
    
    Uso:
    ```python
    engine = RulesEngine()
    
    # Adicionar regra customizada
    engine.add_rule(Rule(
        name="no_code",
        condition=RuleCondition.matches("content", r"```"),
        action=RuleAction.WARN,
        violation_message="Code blocks not allowed"
    ))
    
    # Validar
    result = engine.validate("Hello world")
    print(result.passed)  # True
    
    result = engine.validate("```python\\nprint()\\n```")
    print(result.violations)  # [Violation(...)]
    ```
    """
    
    def __init__(
        self,
        use_default_validators: bool = True,
        config_path: Optional[str] = None
    ):
        # Regras customizadas
        self._rules: dict[str, Rule] = {}
        
        # Rule sets
        self._rule_sets: dict[str, RuleSet] = {}
        
        # Validadores
        self._validators: list[BaseValidator] = []
        
        if use_default_validators:
            self._validators = create_default_validators()
        
        # Configuração
        self.config_path = config_path
        
        # Hooks
        self._pre_validate_hooks: list[Callable] = []
        self._post_validate_hooks: list[Callable] = []
        
        # Métricas
        self.total_validations = 0
        self.total_violations = 0
        self.violations_by_category: dict[str, int] = {}
        
        # Carregar regras do arquivo se existir
        if config_path and os.path.exists(config_path):
            self.load_rules(config_path)
    
    # ==================== Rule Management ====================
    
    def add_rule(self, rule: Rule) -> None:
        """
        Adiciona uma regra.
        
        Args:
            rule: Regra a adicionar
        """
        self._rules[rule.id] = rule
        logger.debug(f"Regra adicionada: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove uma regra."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Obtém regra por ID."""
        return self._rules.get(rule_id)
    
    def list_rules(self) -> list[Rule]:
        """Lista todas as regras."""
        return list(self._rules.values())
    
    def enable_rule(self, rule_id: str) -> bool:
        """Habilita uma regra."""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Desabilita uma regra."""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False
    
    # ==================== Rule Sets ====================
    
    def add_rule_set(self, rule_set: RuleSet) -> None:
        """Adiciona um conjunto de regras."""
        self._rule_sets[rule_set.id] = rule_set
    
    def get_rule_set(self, rule_set_id: str) -> Optional[RuleSet]:
        """Obtém conjunto de regras."""
        return self._rule_sets.get(rule_set_id)
    
    def enable_rule_set(self, rule_set_id: str) -> bool:
        """Habilita um conjunto de regras."""
        rule_set = self._rule_sets.get(rule_set_id)
        if rule_set:
            rule_set.enabled = True
            return True
        return False
    
    # ==================== Validators ====================
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Adiciona um validador."""
        self._validators.append(validator)
    
    def remove_validator(self, name: str) -> bool:
        """Remove validador pelo nome."""
        for i, v in enumerate(self._validators):
            if v.name == name:
                self._validators.pop(i)
                return True
        return False
    
    # ==================== Hooks ====================
    
    def add_pre_validate_hook(self, hook: Callable[[str, dict], tuple[str, dict]]) -> None:
        """
        Adiciona hook pré-validação.
        
        Hook recebe (content, context) e retorna (content, context) modificados.
        """
        self._pre_validate_hooks.append(hook)
    
    def add_post_validate_hook(self, hook: Callable[[ValidationResult], ValidationResult]) -> None:
        """
        Adiciona hook pós-validação.
        
        Hook recebe ValidationResult e retorna modificado.
        """
        self._post_validate_hooks.append(hook)
    
    # ==================== Validation ====================
    
    def validate(
        self,
        content: str,
        context: Optional[dict] = None,
        rule_set_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida conteúdo contra regras e validadores.
        
        Args:
            content: Conteúdo a validar
            context: Contexto adicional
            rule_set_id: ID do rule set a usar (opcional)
            
        Returns:
            ValidationResult com resultado
        """
        start = datetime.now()
        context = context or {}
        
        # Hooks pré-validação
        for hook in self._pre_validate_hooks:
            content, context = hook(content, context)
        
        result = ValidationResult()
        
        # Preparar dados para avaliação de regras
        data = {
            "content": content,
            "length": len(content),
            **context
        }
        
        # Obter regras a avaliar
        rules_to_evaluate = []
        
        if rule_set_id:
            rule_set = self._rule_sets.get(rule_set_id)
            if rule_set and rule_set.enabled:
                rules_to_evaluate = [r for r in rule_set.rules if r.enabled]
        else:
            rules_to_evaluate = [r for r in self._rules.values() if r.enabled]
            
            # Adicionar regras de todos os rule sets habilitados
            for rs in self._rule_sets.values():
                if rs.enabled:
                    rules_to_evaluate.extend([r for r in rs.rules if r.enabled])
        
        # Ordenar por prioridade
        rules_to_evaluate.sort(key=lambda r: r.priority, reverse=True)
        
        # Avaliar regras customizadas
        for rule in rules_to_evaluate:
            if rule.evaluate(data):
                violation = Violation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    action=rule.action,
                    message=rule.violation_message or rule.description,
                    suggestion=rule.fix_suggestion
                )
                result.add_violation(violation)
                
                # Fail fast se configurado
                if rule_set_id:
                    rule_set = self._rule_sets.get(rule_set_id)
                    if rule_set and rule_set.fail_fast:
                        break
        
        result.rules_evaluated += len(rules_to_evaluate)
        
        # Executar validadores
        for validator in self._validators:
            violations = validator.validate(content, context)
            for v in violations:
                result.add_violation(v)
        
        # Hooks pós-validação
        for hook in self._post_validate_hooks:
            result = hook(result)
        
        # Métricas
        elapsed = (datetime.now() - start).total_seconds() * 1000
        result.evaluation_time_ms = elapsed
        
        self.total_validations += 1
        self.total_violations += len(result.violations)
        
        for v in result.violations:
            cat = v.category.value
            self.violations_by_category[cat] = self.violations_by_category.get(cat, 0) + 1
        
        return result
    
    async def avalidate(
        self,
        content: str,
        context: Optional[dict] = None,
        rule_set_id: Optional[str] = None
    ) -> ValidationResult:
        """Versão assíncrona de validate."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.validate(content, context, rule_set_id)
        )
    
    def validate_batch(
        self,
        contents: list[str],
        context: Optional[dict] = None
    ) -> list[ValidationResult]:
        """Valida múltiplos conteúdos."""
        return [self.validate(c, context) for c in contents]
    
    # ==================== Persistence ====================
    
    def load_rules(self, path: str) -> int:
        """
        Carrega regras de arquivo JSON.
        
        Args:
            path: Caminho do arquivo
            
        Returns:
            Número de regras carregadas
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            count = 0
            
            # Carregar regras individuais
            for rule_data in data.get("rules", []):
                rule = Rule.from_dict(rule_data)
                self.add_rule(rule)
                count += 1
            
            # Carregar rule sets
            for rs_data in data.get("rule_sets", []):
                rule_set = RuleSet.from_dict(rs_data)
                self.add_rule_set(rule_set)
                count += len(rule_set.rules)
            
            logger.info(f"Carregadas {count} regras de {path}")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {e}")
            return 0
    
    def save_rules(self, path: str) -> bool:
        """
        Salva regras para arquivo JSON.
        
        Args:
            path: Caminho do arquivo
            
        Returns:
            True se salvo com sucesso
        """
        try:
            data = {
                "rules": [r.to_dict() for r in self._rules.values()],
                "rule_sets": [rs.to_dict() for rs in self._rule_sets.values()]
            }
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Regras salvas em {path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar regras: {e}")
            return False
    
    # ==================== Metrics ====================
    
    def get_metrics(self) -> dict:
        """Retorna métricas do engine."""
        return {
            "total_validations": self.total_validations,
            "total_violations": self.total_violations,
            "violations_by_category": self.violations_by_category,
            "rules_count": len(self._rules),
            "rule_sets_count": len(self._rule_sets),
            "validators_count": len(self._validators),
            "avg_violations_per_validation": self.total_violations / max(self.total_validations, 1)
        }
    
    def reset_metrics(self) -> None:
        """Reseta métricas."""
        self.total_validations = 0
        self.total_violations = 0
        self.violations_by_category.clear()


# ==================== Regras Pré-definidas ====================

def create_no_pii_rule() -> Rule:
    """Cria regra para bloquear PII."""
    return Rule(
        name="no_pii",
        description="Block outputs containing PII",
        condition=RuleCondition.custom(lambda d: False),  # PII verificado por validator
        action=RuleAction.BLOCK,
        category=RuleCategory.SECURITY,
        severity=RuleSeverity.CRITICAL,
        violation_message="PII detected in output"
    )


def create_max_length_rule(max_length: int = 10000) -> Rule:
    """Cria regra de comprimento máximo."""
    return Rule(
        name="max_length",
        description=f"Limit output to {max_length} characters",
        condition=RuleCondition(
            field="length",
            operator=ConditionOperator.GREATER_THAN,
            value=max_length
        ),
        action=RuleAction.WARN,
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.WARNING,
        violation_message=f"Output exceeds {max_length} characters"
    )


def create_no_code_rule() -> Rule:
    """Cria regra para bloquear código."""
    return Rule(
        name="no_code_blocks",
        description="Block code blocks in output",
        condition=RuleCondition.matches("content", r"```[\s\S]*```"),
        action=RuleAction.WARN,
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.INFO,
        violation_message="Code blocks detected"
    )


def create_professional_tone_rule() -> Rule:
    """Cria regra para tom profissional."""
    return Rule(
        name="professional_tone",
        description="Ensure professional tone",
        condition=RuleCondition.or_(
            RuleCondition.matches("content", r"\b(lol|lmao|rofl|omg)\b"),
            RuleCondition.matches("content", r"!!!+"),
            RuleCondition.matches("content", r"\?\?\?+")
        ),
        action=RuleAction.WARN,
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.INFO,
        violation_message="Informal language detected"
    )


def create_default_rule_set() -> RuleSet:
    """Cria conjunto padrão de regras."""
    return RuleSet(
        name="default",
        description="Default rule set for general use",
        rules=[
            create_max_length_rule(),
            create_professional_tone_rule()
        ],
        enabled=True
    )


def create_strict_rule_set() -> RuleSet:
    """Cria conjunto estrito de regras."""
    return RuleSet(
        name="strict",
        description="Strict rules for sensitive contexts",
        rules=[
            create_no_pii_rule(),
            create_max_length_rule(5000),
            create_no_code_rule(),
            create_professional_tone_rule()
        ],
        enabled=True,
        fail_fast=True
    )


# Singleton
_rules_engine: Optional[RulesEngine] = None


def get_rules_engine() -> RulesEngine:
    """Retorna o rules engine singleton."""
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = RulesEngine()
        # Adicionar rule sets padrão
        _rules_engine.add_rule_set(create_default_rule_set())
    return _rules_engine

"""
Rules Engine - Sistema de Regras Simbólicas

Implementa validação baseada em regras para outputs de LLM,
garantindo compliance, segurança e qualidade.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                     Rules Engine                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Rule        │  │ Validator   │  │ Feedback    │         │
│  │ Definitions │  │ Pipeline    │  │ Generator   │         │
│  │             │  │             │  │             │         │
│  │ - JSON      │→│ - Parse     │→│ - Explain   │         │
│  │ - DSL       │  │ - Validate  │  │ - Suggest   │         │
│  │ - Python    │  │ - Report    │  │ - Fix       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Actions  │                            │
│                    │  - Block  │                            │
│                    │  - Warn   │                            │
│                    │  - Fix    │                            │
│                    │  - Log    │                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘

Tipos de Regras:
- Compliance: GDPR, HIPAA, SOC2
- Security: Injeção, PII, secrets
- Quality: Formato, consistência, completude
- Business: Domínio específico

Uso:
```python
from rules import RulesEngine, Rule

# Criar engine
engine = RulesEngine()

# Adicionar regra
engine.add_rule(Rule(
    name="no_pii",
    description="Block PII in responses",
    condition={"contains_pii": True},
    action="block"
))

# Validar output
result = engine.validate(output)
if not result.passed:
    print(result.violations)
```
"""

from .types import (
    Rule,
    RuleCondition,
    RuleAction,
    RuleSeverity,
    RuleCategory,
    ValidationResult,
    Violation,
    RuleSet
)
from .engine import RulesEngine, get_rules_engine
from .validators import (
    PIIValidator,
    SecurityValidator,
    FormatValidator,
    ComplianceValidator,
    CustomValidator
)
from .feedback import FeedbackGenerator, get_feedback_generator

__all__ = [
    # Types
    "Rule",
    "RuleCondition",
    "RuleAction",
    "RuleSeverity",
    "RuleCategory",
    "ValidationResult",
    "Violation",
    "RuleSet",
    # Engine
    "RulesEngine",
    "get_rules_engine",
    # Validators
    "PIIValidator",
    "SecurityValidator",
    "FormatValidator",
    "ComplianceValidator",
    "CustomValidator",
    # Feedback
    "FeedbackGenerator",
    "get_feedback_generator"
]

__version__ = "2.0.0"

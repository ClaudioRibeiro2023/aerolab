"""
Rules Engine - Validadores Especializados

Validadores pré-construídos para casos comuns:
- PII: Dados pessoais identificáveis
- Security: Injeção, secrets, vulnerabilidades
- Format: Estrutura, formato, encoding
- Compliance: GDPR, HIPAA, etc
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
import logging

from .types import (
    Rule, RuleCondition, RuleAction, RuleSeverity, RuleCategory,
    ValidationResult, Violation, ConditionOperator
)


logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """Base class para validadores."""
    
    name: str = "base"
    category: RuleCategory = RuleCategory.CUSTOM
    
    @abstractmethod
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """
        Valida conteúdo e retorna violações.
        
        Args:
            content: Conteúdo a validar
            context: Contexto adicional
            
        Returns:
            Lista de violações encontradas
        """
        pass
    
    def _create_violation(
        self,
        rule_name: str,
        message: str,
        severity: RuleSeverity = RuleSeverity.WARNING,
        action: RuleAction = RuleAction.WARN,
        matched: Optional[str] = None,
        value: Any = None,
        suggestion: str = ""
    ) -> Violation:
        """Helper para criar violação."""
        return Violation(
            rule_id=f"{self.name}_{rule_name}",
            rule_name=f"{self.name}.{rule_name}",
            severity=severity,
            category=self.category,
            action=action,
            message=message,
            matched_content=matched,
            value=value,
            suggestion=suggestion
        )


class PIIValidator(BaseValidator):
    """
    Validador de PII (Personally Identifiable Information).
    
    Detecta:
    - Emails
    - Telefones
    - CPF/CNPJ
    - Cartões de crédito
    - SSN (US)
    - Endereços
    """
    
    name = "pii"
    category = RuleCategory.SECURITY
    
    # Padrões de PII
    PATTERNS = {
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "message": "Email address detected",
            "severity": RuleSeverity.ERROR
        },
        "phone_br": {
            "pattern": r'\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4}\b',
            "message": "Brazilian phone number detected",
            "severity": RuleSeverity.ERROR
        },
        "phone_us": {
            "pattern": r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "message": "US phone number detected",
            "severity": RuleSeverity.ERROR
        },
        "cpf": {
            "pattern": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
            "message": "Brazilian CPF detected",
            "severity": RuleSeverity.CRITICAL
        },
        "cnpj": {
            "pattern": r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
            "message": "Brazilian CNPJ detected",
            "severity": RuleSeverity.ERROR
        },
        "credit_card": {
            "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "message": "Credit card number detected",
            "severity": RuleSeverity.CRITICAL
        },
        "ssn": {
            "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
            "message": "US Social Security Number detected",
            "severity": RuleSeverity.CRITICAL
        },
        "ip_address": {
            "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "message": "IP address detected",
            "severity": RuleSeverity.WARNING
        },
        "date_of_birth": {
            "pattern": r'\b(?:nascimento|birth|dob|born)[\s:]+\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
            "message": "Date of birth detected",
            "severity": RuleSeverity.WARNING
        }
    }
    
    def __init__(
        self,
        enabled_patterns: Optional[list[str]] = None,
        action: RuleAction = RuleAction.BLOCK
    ):
        self.enabled_patterns = enabled_patterns or list(self.PATTERNS.keys())
        self.default_action = action
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida conteúdo para PII."""
        violations = []
        
        for pattern_name in self.enabled_patterns:
            if pattern_name not in self.PATTERNS:
                continue
            
            config = self.PATTERNS[pattern_name]
            matches = re.findall(config["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                # Mascarar valor encontrado
                masked = self._mask_value(match)
                
                violations.append(self._create_violation(
                    rule_name=pattern_name,
                    message=config["message"],
                    severity=config["severity"],
                    action=self.default_action,
                    value=masked,
                    suggestion=f"Remove or mask the {pattern_name.replace('_', ' ')}"
                ))
        
        return violations
    
    def _mask_value(self, value: str) -> str:
        """Mascara valor sensível."""
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]


class SecurityValidator(BaseValidator):
    """
    Validador de segurança.
    
    Detecta:
    - SQL Injection
    - XSS
    - Command Injection
    - Path Traversal
    - Secrets/API Keys
    """
    
    name = "security"
    category = RuleCategory.SECURITY
    
    PATTERNS = {
        "sql_injection": {
            "pattern": r"(?:--|;|'|\"|\bOR\b|\bAND\b|\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b|\bEXEC\b).*(?:--|;|'|\"|\bOR\b|\bAND\b)",
            "message": "Potential SQL injection pattern detected",
            "severity": RuleSeverity.CRITICAL
        },
        "xss": {
            "pattern": r"<script[^>]*>|javascript:|on\w+\s*=|<iframe|<embed|<object",
            "message": "Potential XSS attack pattern detected",
            "severity": RuleSeverity.CRITICAL
        },
        "command_injection": {
            "pattern": r"[;&|`$]|\b(?:rm|cat|wget|curl|chmod|chown|sudo|exec|eval)\b",
            "message": "Potential command injection pattern detected",
            "severity": RuleSeverity.CRITICAL
        },
        "path_traversal": {
            "pattern": r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\./",
            "message": "Potential path traversal pattern detected",
            "severity": RuleSeverity.ERROR
        },
        "aws_key": {
            "pattern": r"(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "message": "AWS Access Key detected",
            "severity": RuleSeverity.CRITICAL
        },
        "aws_secret": {
            "pattern": r"(?i)aws.{0,20}secret.{0,20}['\"][A-Za-z0-9/+=]{40}['\"]",
            "message": "AWS Secret Key detected",
            "severity": RuleSeverity.CRITICAL
        },
        "github_token": {
            "pattern": r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "message": "GitHub token detected",
            "severity": RuleSeverity.CRITICAL
        },
        "api_key": {
            "pattern": r"(?i)(?:api[_-]?key|apikey|api_secret|access_token)[\s:=]+['\"]?[A-Za-z0-9_-]{20,}['\"]?",
            "message": "API key pattern detected",
            "severity": RuleSeverity.ERROR
        },
        "private_key": {
            "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "message": "Private key detected",
            "severity": RuleSeverity.CRITICAL
        },
        "password_plain": {
            "pattern": r"(?i)(?:password|senha|pwd)[\s:=]+['\"]?[^\s'\"]{8,}['\"]?",
            "message": "Plain text password pattern detected",
            "severity": RuleSeverity.ERROR
        }
    }
    
    def __init__(
        self,
        enabled_checks: Optional[list[str]] = None,
        action: RuleAction = RuleAction.BLOCK
    ):
        self.enabled_checks = enabled_checks or list(self.PATTERNS.keys())
        self.default_action = action
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida conteúdo para problemas de segurança."""
        violations = []
        
        for check_name in self.enabled_checks:
            if check_name not in self.PATTERNS:
                continue
            
            config = self.PATTERNS[check_name]
            
            if re.search(config["pattern"], content, re.IGNORECASE):
                violations.append(self._create_violation(
                    rule_name=check_name,
                    message=config["message"],
                    severity=config["severity"],
                    action=self.default_action,
                    suggestion=f"Remove or sanitize the {check_name.replace('_', ' ')}"
                ))
        
        return violations


class FormatValidator(BaseValidator):
    """
    Validador de formato e estrutura.
    
    Valida:
    - Comprimento
    - Encoding
    - JSON válido
    - Estrutura esperada
    """
    
    name = "format"
    category = RuleCategory.QUALITY
    
    def __init__(
        self,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        required_fields: Optional[list[str]] = None,
        forbidden_chars: Optional[str] = None,
        must_be_json: bool = False
    ):
        self.max_length = max_length
        self.min_length = min_length
        self.required_fields = required_fields or []
        self.forbidden_chars = forbidden_chars
        self.must_be_json = must_be_json
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida formato do conteúdo."""
        violations = []
        
        # Comprimento
        if self.max_length and len(content) > self.max_length:
            violations.append(self._create_violation(
                rule_name="max_length",
                message=f"Content exceeds maximum length ({len(content)} > {self.max_length})",
                severity=RuleSeverity.WARNING,
                action=RuleAction.WARN,
                suggestion=f"Reduce content length to {self.max_length} characters"
            ))
        
        if self.min_length and len(content) < self.min_length:
            violations.append(self._create_violation(
                rule_name="min_length",
                message=f"Content below minimum length ({len(content)} < {self.min_length})",
                severity=RuleSeverity.WARNING,
                action=RuleAction.WARN,
                suggestion=f"Expand content to at least {self.min_length} characters"
            ))
        
        # Caracteres proibidos
        if self.forbidden_chars:
            found = [c for c in self.forbidden_chars if c in content]
            if found:
                violations.append(self._create_violation(
                    rule_name="forbidden_chars",
                    message=f"Forbidden characters found: {found}",
                    severity=RuleSeverity.ERROR,
                    action=RuleAction.BLOCK,
                    value=found,
                    suggestion="Remove forbidden characters"
                ))
        
        # JSON válido
        if self.must_be_json:
            import json
            try:
                parsed = json.loads(content)
                
                # Campos obrigatórios
                if self.required_fields and isinstance(parsed, dict):
                    missing = [f for f in self.required_fields if f not in parsed]
                    if missing:
                        violations.append(self._create_violation(
                            rule_name="required_fields",
                            message=f"Missing required fields: {missing}",
                            severity=RuleSeverity.ERROR,
                            action=RuleAction.BLOCK,
                            value=missing,
                            suggestion=f"Add required fields: {missing}"
                        ))
                        
            except json.JSONDecodeError as e:
                violations.append(self._create_violation(
                    rule_name="invalid_json",
                    message=f"Invalid JSON: {e}",
                    severity=RuleSeverity.ERROR,
                    action=RuleAction.BLOCK,
                    suggestion="Fix JSON syntax"
                ))
        
        # Encoding
        try:
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            violations.append(self._create_violation(
                rule_name="encoding",
                message=f"Invalid UTF-8 encoding: {e}",
                severity=RuleSeverity.ERROR,
                action=RuleAction.BLOCK
            ))
        
        return violations


class ComplianceValidator(BaseValidator):
    """
    Validador de compliance.
    
    Verifica conformidade com:
    - GDPR
    - HIPAA
    - SOC2
    - PCI-DSS
    """
    
    name = "compliance"
    category = RuleCategory.COMPLIANCE
    
    # Termos sensíveis por regulamentação
    SENSITIVE_TERMS = {
        "gdpr": [
            r"\b(?:personal data|dados pessoais)\b",
            r"\b(?:consent|consentimento)\b",
            r"\b(?:right to erasure|direito ao esquecimento)\b",
            r"\b(?:data subject|titular dos dados)\b"
        ],
        "hipaa": [
            r"\b(?:PHI|protected health information)\b",
            r"\b(?:medical record|prontuário)\b",
            r"\b(?:diagnosis|diagnóstico)\b",
            r"\b(?:treatment|tratamento médico)\b",
            r"\b(?:health insurance|plano de saúde)\b"
        ],
        "pci": [
            r"\b(?:cardholder|titular do cartão)\b",
            r"\b(?:CVV|CVC|security code)\b",
            r"\b(?:card number|número do cartão)\b",
            r"\b(?:expiration date|data de validade)\b"
        ],
        "financial": [
            r"\b(?:bank account|conta bancária)\b",
            r"\b(?:routing number)\b",
            r"\b(?:swift|iban)\b",
            r"\b(?:salary|salário)\b"
        ]
    }
    
    def __init__(
        self,
        regulations: Optional[list[str]] = None,
        action: RuleAction = RuleAction.WARN
    ):
        self.regulations = regulations or ["gdpr", "hipaa", "pci"]
        self.default_action = action
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida compliance."""
        violations = []
        
        for regulation in self.regulations:
            if regulation not in self.SENSITIVE_TERMS:
                continue
            
            for pattern in self.SENSITIVE_TERMS[regulation]:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(self._create_violation(
                        rule_name=f"{regulation}_sensitive",
                        message=f"Content may contain {regulation.upper()}-sensitive information",
                        severity=RuleSeverity.WARNING,
                        action=self.default_action,
                        suggestion=f"Review content for {regulation.upper()} compliance"
                    ))
                    break  # Uma violação por regulamentação
        
        return violations


class CustomValidator(BaseValidator):
    """
    Validador customizado via função.
    
    Permite definir validação customizada.
    """
    
    name = "custom"
    category = RuleCategory.CUSTOM
    
    def __init__(
        self,
        validator_fn,
        name: str = "custom",
        category: RuleCategory = RuleCategory.CUSTOM
    ):
        """
        Args:
            validator_fn: Função (content, context) -> list[Violation]
            name: Nome do validador
            category: Categoria
        """
        self._validator_fn = validator_fn
        self.name = name
        self.category = category
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Executa validação customizada."""
        return self._validator_fn(content, context or {})


class ToxicityValidator(BaseValidator):
    """
    Validador de conteúdo tóxico/ofensivo.
    
    Detecta linguagem:
    - Ofensiva
    - Discriminatória
    - Violenta
    - Sexual explícito
    """
    
    name = "toxicity"
    category = RuleCategory.QUALITY
    
    # Padrões simplificados (em produção, usar modelo ML)
    PATTERNS = {
        "profanity": {
            "words": ["merda", "porra", "caralho", "fuck", "shit", "damn"],
            "message": "Profanity detected",
            "severity": RuleSeverity.WARNING
        },
        "hate_speech": {
            "patterns": [
                r"\b(?:morte a|kill all|exterminate)\b",
                r"\b(?:inferior|subhuman)\b.*\b(?:race|raça|people|povo)\b"
            ],
            "message": "Potential hate speech detected",
            "severity": RuleSeverity.CRITICAL
        },
        "threats": {
            "patterns": [
                r"\b(?:vou te matar|I will kill you|gonna kill)\b",
                r"\b(?:ameaço|threaten|threat)\b"
            ],
            "message": "Threat detected",
            "severity": RuleSeverity.CRITICAL
        }
    }
    
    def __init__(self, action: RuleAction = RuleAction.BLOCK):
        self.default_action = action
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida conteúdo tóxico."""
        violations = []
        content_lower = content.lower()
        
        # Profanidade (palavras)
        config = self.PATTERNS["profanity"]
        for word in config["words"]:
            if word in content_lower:
                violations.append(self._create_violation(
                    rule_name="profanity",
                    message=config["message"],
                    severity=config["severity"],
                    action=RuleAction.WARN,
                    suggestion="Remove or mask profanity"
                ))
                break
        
        # Padrões de hate speech e threats
        for check_name in ["hate_speech", "threats"]:
            config = self.PATTERNS[check_name]
            for pattern in config["patterns"]:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(self._create_violation(
                        rule_name=check_name,
                        message=config["message"],
                        severity=config["severity"],
                        action=self.default_action,
                        suggestion="Remove harmful content"
                    ))
                    break
        
        return violations


class CustomValidator(BaseValidator):
    """
    Validador customizável.
    
    Permite criar validadores com regras customizadas via padrões regex.
    """
    
    name = "custom"
    category = RuleCategory.CUSTOM
    
    def __init__(
        self,
        patterns: dict[str, dict] = None,
        action: RuleAction = RuleAction.WARN
    ):
        """
        Args:
            patterns: Dict de padrões {name: {pattern, message, severity}}
            action: Ação padrão
        """
        self.patterns = patterns or {}
        self.default_action = action
    
    def add_pattern(
        self,
        name: str,
        pattern: str,
        message: str,
        severity: RuleSeverity = RuleSeverity.WARNING
    ) -> None:
        """Adiciona padrão de validação."""
        self.patterns[name] = {
            "pattern": pattern,
            "message": message,
            "severity": severity
        }
    
    def validate(self, content: str, context: Optional[dict] = None) -> list[Violation]:
        """Valida conteúdo com padrões customizados."""
        violations = []
        
        for name, config in self.patterns.items():
            pattern = config.get("pattern", "")
            if pattern and re.search(pattern, content, re.IGNORECASE):
                violations.append(self._create_violation(
                    rule_name=f"custom_{name}",
                    message=config.get("message", f"Pattern '{name}' matched"),
                    severity=config.get("severity", RuleSeverity.WARNING),
                    action=self.default_action,
                    matched=re.search(pattern, content, re.IGNORECASE).group()
                ))
        
        return violations


# Factory function para criar validadores comuns
def create_default_validators() -> list[BaseValidator]:
    """Cria conjunto padrão de validadores."""
    return [
        PIIValidator(),
        SecurityValidator(),
        FormatValidator(max_length=10000),
        ComplianceValidator(),
        ToxicityValidator()
    ]

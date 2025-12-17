"""
Sistema de Guardrails para Agentes.

Implementa validações e proteções para inputs/outputs de agentes:
- Input sanitization
- Output validation (JSON schema, content policy)
- Rate limiting
- Token budget enforcement
- PII detection
- Toxic content filtering

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Guardrails System                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Input        │  │ Process      │  │ Output       │      │
│  │ Guards       │  │ Guards       │  │ Guards       │      │
│  │              │  │              │  │              │      │
│  │ - Sanitize   │  │ - Rate limit │  │ - Validate   │      │
│  │ - PII detect │  │ - Token cap  │  │ - Filter     │      │
│  │ - Length     │  │ - Timeout    │  │ - Schema     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

import re
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading


class GuardAction(Enum):
    """Ações que os guards podem tomar."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    MODIFY = "modify"
    ESCALATE = "escalate"


class ViolationType(Enum):
    """Tipos de violação."""
    INPUT_TOO_LONG = "input_too_long"
    OUTPUT_TOO_LONG = "output_too_long"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"
    PII_DETECTED = "pii_detected"
    TOXIC_CONTENT = "toxic_content"
    BLOCKED_PATTERN = "blocked_pattern"
    SCHEMA_VIOLATION = "schema_violation"
    TIMEOUT = "timeout"


@dataclass
class GuardResult:
    """Resultado de uma verificação de guard."""
    action: GuardAction
    passed: bool
    violations: List[ViolationType] = field(default_factory=list)
    message: Optional[str] = None
    modified_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "passed": self.passed,
            "violations": [v.value for v in self.violations],
            "message": self.message,
            "metadata": self.metadata
        }


@dataclass
class GuardrailsConfig:
    """Configuração de guardrails."""
    # Input limits
    max_input_length: int = 50000
    max_input_tokens: int = 8000
    
    # Output limits
    max_output_length: int = 100000
    max_output_tokens: int = 4000
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Token budget
    token_budget_enabled: bool = False
    token_budget_daily: int = 100000
    
    # Content filtering
    pii_detection_enabled: bool = True
    toxic_filter_enabled: bool = True
    blocked_patterns: List[str] = field(default_factory=list)
    
    # Output validation
    require_json_output: bool = False
    json_schema: Optional[Dict] = None
    
    # Tool restrictions
    max_tool_calls: int = 10
    allowed_tools: Optional[List[str]] = None
    blocked_tools: List[str] = field(default_factory=list)
    
    # Timeouts
    max_execution_time: int = 300  # seconds


class PIIDetector:
    """
    Detector de Informações Pessoais Identificáveis (PII).
    """
    
    # Padrões de PII
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone_br": r'\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4}\b',
        "cpf": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        "cnpj": r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
        "credit_card": r'\b(?:\d{4}[\s.-]?){3}\d{4}\b',
        "ssn_us": r'\b\d{3}-\d{2}-\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    def detect(self, text: str) -> List[Dict[str, Any]]:
        """
        Detecta PII no texto.
        
        Returns:
            Lista de detecções com tipo, posição e conteúdo mascarado
        """
        findings = []
        
        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "masked": self._mask(match.group(), pii_type)
                })
        
        return findings
    
    def mask(self, text: str) -> str:
        """
        Mascara todo PII encontrado no texto.
        """
        findings = sorted(self.detect(text), key=lambda x: x["start"], reverse=True)
        
        result = text
        for finding in findings:
            result = result[:finding["start"]] + finding["masked"] + result[finding["end"]:]
        
        return result
    
    def _mask(self, value: str, pii_type: str) -> str:
        """Gera versão mascarada do valor."""
        if pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
        elif pii_type in ("cpf", "cnpj", "ssn_us"):
            return "***-***-" + value[-4:]
        elif pii_type == "credit_card":
            return "**** **** **** " + value[-4:]
        elif pii_type == "phone_br":
            return "(**) ****-" + value[-4:]
        
        return "***REDACTED***"


class ToxicContentFilter:
    """
    Filtro de conteúdo tóxico/inapropriado.
    """
    
    # Palavras e padrões bloqueados (simplificado)
    TOXIC_PATTERNS = [
        r'\b(hack|exploit|bypass)\s+(security|firewall|password)\b',
        r'\b(create|generate|make)\s+(virus|malware|ransomware)\b',
        r'\b(illegal|illicit)\s+(drug|substance|weapon)\b',
    ]
    
    def __init__(self, custom_patterns: Optional[List[str]] = None):
        self.patterns = self.TOXIC_PATTERNS + (custom_patterns or [])
    
    def check(self, text: str) -> Tuple[bool, List[str]]:
        """
        Verifica se o texto contém conteúdo tóxico.
        
        Returns:
            (is_clean, matched_patterns)
        """
        matches = []
        text_lower = text.lower()
        
        for pattern in self.patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern)
        
        return len(matches) == 0, matches


class RateLimiter:
    """
    Rate limiter por chave (user, agent, etc).
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def check(self, key: str) -> Tuple[bool, int]:
        """
        Verifica se a chave está dentro do limite.
        
        Returns:
            (is_allowed, remaining_requests)
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        with self._lock:
            # Limpar requests antigos
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]
            
            current_count = len(self._requests[key])
            remaining = max(0, self.max_requests - current_count)
            
            return current_count < self.max_requests, remaining
    
    def record(self, key: str) -> None:
        """Registra uma requisição."""
        with self._lock:
            self._requests[key].append(time.time())
    
    def reset(self, key: str) -> None:
        """Reseta o contador para uma chave."""
        with self._lock:
            self._requests[key] = []


class TokenBudgetTracker:
    """
    Rastreador de orçamento de tokens.
    """
    
    def __init__(self, daily_budget: int = 100000):
        self.daily_budget = daily_budget
        self._usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._lock = threading.Lock()
    
    def _get_date_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_usage(self, key: str) -> int:
        """Retorna uso do dia atual."""
        date_key = self._get_date_key()
        return self._usage[key][date_key]
    
    def get_remaining(self, key: str) -> int:
        """Retorna tokens restantes."""
        return max(0, self.daily_budget - self.get_usage(key))
    
    def can_spend(self, key: str, tokens: int) -> bool:
        """Verifica se pode gastar tokens."""
        return self.get_remaining(key) >= tokens
    
    def spend(self, key: str, tokens: int) -> bool:
        """Registra gasto de tokens."""
        if not self.can_spend(key, tokens):
            return False
        
        date_key = self._get_date_key()
        with self._lock:
            self._usage[key][date_key] += tokens
        return True
    
    def reset(self, key: str) -> None:
        """Reseta o uso de uma chave."""
        date_key = self._get_date_key()
        with self._lock:
            self._usage[key][date_key] = 0


class InputGuard:
    """
    Guard para validação de inputs.
    """
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.pii_detector = PIIDetector()
        self.toxic_filter = ToxicContentFilter(config.blocked_patterns)
    
    def validate(self, input_text: str, user_id: Optional[str] = None) -> GuardResult:
        """Valida o input."""
        violations = []
        message = None
        modified = None
        
        # Check length
        if len(input_text) > self.config.max_input_length:
            violations.append(ViolationType.INPUT_TOO_LONG)
            message = f"Input excede limite de {self.config.max_input_length} caracteres"
        
        # Check tokens (estimativa)
        estimated_tokens = len(input_text) // 4
        if estimated_tokens > self.config.max_input_tokens:
            violations.append(ViolationType.TOKEN_BUDGET_EXCEEDED)
            message = f"Input excede limite de {self.config.max_input_tokens} tokens"
        
        # Check PII
        if self.config.pii_detection_enabled:
            pii_findings = self.pii_detector.detect(input_text)
            if pii_findings:
                violations.append(ViolationType.PII_DETECTED)
                modified = self.pii_detector.mask(input_text)
        
        # Check toxic content
        if self.config.toxic_filter_enabled:
            is_clean, matches = self.toxic_filter.check(input_text)
            if not is_clean:
                violations.append(ViolationType.TOXIC_CONTENT)
                message = "Conteúdo potencialmente inapropriado detectado"
        
        # Check blocked patterns
        for pattern in self.config.blocked_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                violations.append(ViolationType.BLOCKED_PATTERN)
                break
        
        # Determine action
        if ViolationType.TOXIC_CONTENT in violations:
            action = GuardAction.BLOCK
            passed = False
        elif ViolationType.INPUT_TOO_LONG in violations:
            action = GuardAction.BLOCK
            passed = False
        elif ViolationType.PII_DETECTED in violations:
            action = GuardAction.MODIFY
            passed = True
        elif violations:
            action = GuardAction.WARN
            passed = True
        else:
            action = GuardAction.ALLOW
            passed = True
        
        return GuardResult(
            action=action,
            passed=passed,
            violations=violations,
            message=message,
            modified_content=modified,
            metadata={"estimated_tokens": estimated_tokens}
        )


class OutputGuard:
    """
    Guard para validação de outputs.
    """
    
    def __init__(self, config: GuardrailsConfig):
        self.config = config
        self.pii_detector = PIIDetector()
        self.toxic_filter = ToxicContentFilter()
    
    def validate(self, output_text: str) -> GuardResult:
        """Valida o output."""
        violations = []
        message = None
        modified = None
        
        # Check length
        if len(output_text) > self.config.max_output_length:
            violations.append(ViolationType.OUTPUT_TOO_LONG)
            message = f"Output excede limite de {self.config.max_output_length} caracteres"
        
        # Check PII leakage
        if self.config.pii_detection_enabled:
            pii_findings = self.pii_detector.detect(output_text)
            if pii_findings:
                violations.append(ViolationType.PII_DETECTED)
                modified = self.pii_detector.mask(output_text)
        
        # Check JSON schema
        if self.config.require_json_output:
            try:
                parsed = json.loads(output_text)
                if self.config.json_schema:
                    # Validação básica de schema (simplificada)
                    if not self._validate_schema(parsed, self.config.json_schema):
                        violations.append(ViolationType.SCHEMA_VIOLATION)
            except json.JSONDecodeError:
                violations.append(ViolationType.SCHEMA_VIOLATION)
                message = "Output não é JSON válido"
        
        # Determine action
        if ViolationType.SCHEMA_VIOLATION in violations:
            action = GuardAction.BLOCK
            passed = False
        elif ViolationType.PII_DETECTED in violations:
            action = GuardAction.MODIFY
            passed = True
        elif violations:
            action = GuardAction.WARN
            passed = True
        else:
            action = GuardAction.ALLOW
            passed = True
        
        return GuardResult(
            action=action,
            passed=passed,
            violations=violations,
            message=message,
            modified_content=modified
        )
    
    def _validate_schema(self, data: Any, schema: Dict) -> bool:
        """Validação básica de schema JSON."""
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(data, dict):
                return False
            if expected_type == "array" and not isinstance(data, list):
                return False
            if expected_type == "string" and not isinstance(data, str):
                return False
            if expected_type == "number" and not isinstance(data, (int, float)):
                return False
        
        if "required" in schema and isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    return False
        
        return True


class Guardrails:
    """
    Sistema completo de guardrails.
    
    Exemplo:
        guardrails = Guardrails(config)
        
        # Validar input
        input_result = guardrails.check_input(user_input, user_id="user123")
        if not input_result.passed:
            return f"Bloqueado: {input_result.message}"
        
        # Usar input modificado se necessário
        safe_input = input_result.modified_content or user_input
        
        # Processar...
        output = agent.run(safe_input)
        
        # Validar output
        output_result = guardrails.check_output(output)
        safe_output = output_result.modified_content or output
    """
    
    def __init__(self, config: Optional[GuardrailsConfig] = None):
        self.config = config or GuardrailsConfig()
        
        self.input_guard = InputGuard(self.config)
        self.output_guard = OutputGuard(self.config)
        self.rate_limiter = RateLimiter(
            max_requests=self.config.rate_limit_requests,
            window_seconds=self.config.rate_limit_window_seconds
        )
        self.token_tracker = TokenBudgetTracker(
            daily_budget=self.config.token_budget_daily
        )
        
        self._tool_call_counts: Dict[str, int] = defaultdict(int)
    
    def check_input(
        self, 
        input_text: str, 
        user_id: Optional[str] = None
    ) -> GuardResult:
        """
        Verifica input antes de processar.
        """
        # Rate limit check
        if self.config.rate_limit_enabled and user_id:
            allowed, remaining = self.rate_limiter.check(user_id)
            if not allowed:
                return GuardResult(
                    action=GuardAction.BLOCK,
                    passed=False,
                    violations=[ViolationType.RATE_LIMIT_EXCEEDED],
                    message=f"Limite de requisições excedido. Tente novamente em breve.",
                    metadata={"remaining": remaining}
                )
            self.rate_limiter.record(user_id)
        
        # Token budget check
        if self.config.token_budget_enabled and user_id:
            estimated_tokens = len(input_text) // 4
            if not self.token_tracker.can_spend(user_id, estimated_tokens):
                return GuardResult(
                    action=GuardAction.BLOCK,
                    passed=False,
                    violations=[ViolationType.TOKEN_BUDGET_EXCEEDED],
                    message="Orçamento diário de tokens excedido.",
                    metadata={"remaining": self.token_tracker.get_remaining(user_id)}
                )
        
        return self.input_guard.validate(input_text, user_id)
    
    def check_output(self, output_text: str) -> GuardResult:
        """
        Verifica output antes de retornar.
        """
        return self.output_guard.validate(output_text)
    
    def check_tool_call(
        self, 
        tool_name: str, 
        execution_id: str
    ) -> GuardResult:
        """
        Verifica se uma chamada de ferramenta é permitida.
        """
        # Check blocked tools
        if tool_name in self.config.blocked_tools:
            return GuardResult(
                action=GuardAction.BLOCK,
                passed=False,
                violations=[ViolationType.BLOCKED_PATTERN],
                message=f"Ferramenta '{tool_name}' está bloqueada"
            )
        
        # Check allowed tools
        if self.config.allowed_tools and tool_name not in self.config.allowed_tools:
            return GuardResult(
                action=GuardAction.BLOCK,
                passed=False,
                violations=[ViolationType.BLOCKED_PATTERN],
                message=f"Ferramenta '{tool_name}' não está na lista permitida"
            )
        
        # Check tool call limit
        self._tool_call_counts[execution_id] += 1
        if self._tool_call_counts[execution_id] > self.config.max_tool_calls:
            return GuardResult(
                action=GuardAction.BLOCK,
                passed=False,
                violations=[ViolationType.RATE_LIMIT_EXCEEDED],
                message=f"Limite de {self.config.max_tool_calls} chamadas de ferramenta excedido"
            )
        
        return GuardResult(action=GuardAction.ALLOW, passed=True)
    
    def record_tokens(self, user_id: str, tokens: int) -> bool:
        """Registra consumo de tokens."""
        if self.config.token_budget_enabled:
            return self.token_tracker.spend(user_id, tokens)
        return True
    
    def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Retorna resumo de uso."""
        return {
            "tokens_used_today": self.token_tracker.get_usage(user_id),
            "tokens_remaining": self.token_tracker.get_remaining(user_id),
            "rate_limit_remaining": self.rate_limiter.check(user_id)[1]
        }
    
    def reset_execution(self, execution_id: str) -> None:
        """Reseta contadores de uma execução."""
        if execution_id in self._tool_call_counts:
            del self._tool_call_counts[execution_id]


# Factory
def create_guardrails(
    max_input_tokens: int = 8000,
    max_output_tokens: int = 4000,
    enable_pii_detection: bool = True,
    enable_rate_limiting: bool = True,
    blocked_patterns: Optional[List[str]] = None
) -> Guardrails:
    """
    Cria instância de guardrails com configuração.
    """
    config = GuardrailsConfig(
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
        pii_detection_enabled=enable_pii_detection,
        rate_limit_enabled=enable_rate_limiting,
        blocked_patterns=blocked_patterns or []
    )
    return Guardrails(config)

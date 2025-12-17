"""Agente Compliance — Guardrails de entrada e saída."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import re
import logging

logger = logging.getLogger(__name__)

PII_PATTERNS = [
    (r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "CPF"),
    (r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", "CNPJ"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email"),
    (r"\b\(\d{2}\)\s*\d{4,5}-?\d{4}\b", "Telefone"),
]

INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"pretend\s+to\s+be",
    r"act\s+as\s+if",
    r"disregard\s+(all|previous)",
    r"system\s*:\s*",
    r"<\s*system\s*>",
]

FORBIDDEN_ACTIONS = [
    "delete", "drop", "truncate", "execute", "eval",
    "rm -rf", "format", "shutdown",
]


@dataclass
class ComplianceResult:
    """Resultado da verificação de compliance."""

    passed: bool
    issues: list[str]
    warnings: list[str]
    checked_at: datetime
    input_sanitized: str | None = None

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ComplianceAgent:
    """
    Agente responsável por guardrails de segurança.

    Responsabilidades:
    - Validar entrada (detectar PII, injection)
    - Validar saída (schema, conteúdo proibido)
    - Sanitizar dados quando necessário
    - Bloquear ações perigosas

    Modos:
    - check_input: valida entrada do usuário
    - check_output: valida saída de agentes
    - sanitize: remove conteúdo sensível
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def check_input(self, text: str) -> ComplianceResult:
        """
        Verifica entrada do usuário.

        Args:
            text: Texto de entrada

        Returns:
            ComplianceResult com status e issues
        """
        issues: list[str] = []
        warnings: list[str] = []
        checked_at = datetime.now(timezone.utc)

        pii_found = self._detect_pii(text)
        if pii_found:
            for pii_type, match in pii_found:
                if self.strict_mode:
                    issues.append(f"PII detectado ({pii_type}): {self._mask(match)}")
                else:
                    warnings.append(f"Possível PII ({pii_type}): {self._mask(match)}")

        injection_found = self._detect_injection(text)
        if injection_found:
            issues.append(f"Possível prompt injection detectado: {injection_found[:50]}...")

        forbidden = self._detect_forbidden_actions(text)
        if forbidden:
            issues.append(f"Ação proibida detectada: {forbidden}")

        passed = len(issues) == 0

        return ComplianceResult(
            passed=passed,
            issues=issues,
            warnings=warnings,
            checked_at=checked_at,
        )

    def check_output(self, data: dict[str, Any]) -> ComplianceResult:
        """
        Verifica saída de agentes.

        Args:
            data: Dados de saída (dict)

        Returns:
            ComplianceResult com status e issues
        """
        issues: list[str] = []
        warnings: list[str] = []
        checked_at = datetime.now(timezone.utc)

        text_content = self._extract_text_from_dict(data)

        pii_found = self._detect_pii(text_content)
        if pii_found:
            for pii_type, match in pii_found:
                warnings.append(f"PII na saída ({pii_type}): {self._mask(match)}")

        if "parecer jurídico" in text_content.lower():
            issues.append("Saída contém termo 'parecer jurídico' - revisar para compliance")

        if "garantia" in text_content.lower() and "legal" in text_content.lower():
            warnings.append("Saída menciona garantias legais - verificar disclaimer")

        passed = len(issues) == 0

        return ComplianceResult(
            passed=passed,
            issues=issues,
            warnings=warnings,
            checked_at=checked_at,
        )

    def sanitize(self, text: str) -> ComplianceResult:
        """
        Sanitiza texto removendo conteúdo sensível.

        Args:
            text: Texto para sanitizar

        Returns:
            ComplianceResult com texto sanitizado
        """
        issues: list[str] = []
        warnings: list[str] = []
        checked_at = datetime.now(timezone.utc)

        sanitized = text

        for pattern, pii_type in PII_PATTERNS:
            matches = re.findall(pattern, sanitized, re.IGNORECASE)
            for match in matches:
                sanitized = sanitized.replace(match, f"[{pii_type}_REDACTED]")
                warnings.append(f"Removido {pii_type}")

        return ComplianceResult(
            passed=True,
            issues=issues,
            warnings=warnings,
            checked_at=checked_at,
            input_sanitized=sanitized,
        )

    def _detect_pii(self, text: str) -> list[tuple[str, str]]:
        """Detecta PII no texto."""
        found: list[tuple[str, str]] = []

        for pattern, pii_type in PII_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                found.append((pii_type, match))

        return found

    def _detect_injection(self, text: str) -> str | None:
        """Detecta tentativas de prompt injection."""
        text_lower = text.lower()

        for pattern in INJECTION_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _detect_forbidden_actions(self, text: str) -> str | None:
        """Detecta ações proibidas."""
        text_lower = text.lower()

        for action in FORBIDDEN_ACTIONS:
            if action in text_lower:
                return action

        return None

    def _mask(self, text: str) -> str:
        """Mascara texto sensível."""
        if len(text) <= 4:
            return "****"
        return text[:2] + "*" * (len(text) - 4) + text[-2:]

    def _extract_text_from_dict(self, data: dict[str, Any]) -> str:
        """Extrai texto de um dict recursivamente."""
        texts: list[str] = []

        def extract(obj: Any):
            if isinstance(obj, str):
                texts.append(obj)
            elif isinstance(obj, dict):
                for v in obj.values():
                    extract(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)

        extract(data)
        return " ".join(texts)


async def create_compliance_agent(strict_mode: bool = False) -> ComplianceAgent:
    """Factory function para criar ComplianceAgent."""
    return ComplianceAgent(strict_mode=strict_mode)

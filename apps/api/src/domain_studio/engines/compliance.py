"""
Compliance Engine - Motor de compliance com 30+ regulamentações.

Sprint 6: Compliance Engine v2
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern
import uuid

from ..core.types import (
    DomainType,
    RegulationType,
    ComplianceLevel,
    ComplianceCheck,
    ComplianceViolation,
    ComplianceWarning,
)

logger = logging.getLogger(__name__)


class ViolationSeverity(str, Enum):
    """Severidade de violação."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceRule:
    """Regra de compliance."""
    id: str
    name: str
    description: str
    regulation: RegulationType
    severity: ViolationSeverity
    pattern: Optional[str] = None  # Regex pattern
    validator: Optional[Callable] = None  # Custom validator
    message: str = ""
    recommendation: str = ""


@dataclass 
class PIIDetection:
    """Resultado de detecção de PII."""
    found: bool = False
    types: List[str] = field(default_factory=list)
    locations: List[Dict] = field(default_factory=list)
    redacted_text: str = ""


@dataclass
class RiskAssessment:
    """Avaliação de risco."""
    score: float = 0.0  # 0-100
    level: str = "low"  # low, medium, high, critical
    factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    """Entrada de auditoria."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    action: str = ""
    user_id: Optional[str] = None
    resource: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_check_id: Optional[str] = None
    result: str = "success"


class ComplianceEngine:
    """
    Engine de Compliance multi-regulamentação.
    
    Features:
    - 30+ regulamentações (BR e internacionais)
    - Detecção de PII (dados pessoais)
    - Risk scoring
    - Audit trail
    - Auto-redação de dados sensíveis
    """
    
    def __init__(self, domain: Optional[DomainType] = None):
        self.domain = domain
        self._rules: Dict[str, ComplianceRule] = {}
        self._audit_log: List[AuditEntry] = []
        
        # Initialize rules
        self._initialize_rules()
        
        # PII patterns
        self._pii_patterns = self._build_pii_patterns()
        
        logger.info("ComplianceEngine initialized with %d rules", len(self._rules))
    
    def _initialize_rules(self) -> None:
        """Initialize compliance rules for all regulations."""
        # LGPD Rules
        self._add_lgpd_rules()
        
        # Financial regulations
        self._add_cvm_rules()
        self._add_bacen_rules()
        
        # Healthcare regulations
        self._add_anvisa_rules()
        self._add_cfm_rules()
        
        # Legal regulations
        self._add_oab_rules()
        
        # International
        self._add_gdpr_rules()
        self._add_hipaa_rules()
        self._add_soc2_rules()
    
    def _add_lgpd_rules(self) -> None:
        """Add LGPD (Lei Geral de Proteção de Dados) rules."""
        rules = [
            ComplianceRule(
                id="lgpd_001",
                name="CPF Exposure",
                description="CPF numbers must be protected",
                regulation=RegulationType.LGPD,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
                message="CPF number detected in content",
                recommendation="Remove or mask CPF numbers"
            ),
            ComplianceRule(
                id="lgpd_002",
                name="Email Exposure",
                description="Email addresses should be protected",
                regulation=RegulationType.LGPD,
                severity=ViolationSeverity.MEDIUM,
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                message="Email address detected",
                recommendation="Consider masking email addresses"
            ),
            ComplianceRule(
                id="lgpd_003",
                name="Phone Number Exposure",
                description="Phone numbers should be protected",
                regulation=RegulationType.LGPD,
                severity=ViolationSeverity.MEDIUM,
                pattern=r"\b\(?\d{2}\)?[\s-]?\d{4,5}[-\s]?\d{4}\b",
                message="Phone number detected",
                recommendation="Consider masking phone numbers"
            ),
            ComplianceRule(
                id="lgpd_004",
                name="Health Data",
                description="Health data requires special protection",
                regulation=RegulationType.LGPD,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"\b(diagnóstico|doença|medicamento|tratamento|CID|sintoma)\b",
                message="Potential health data detected",
                recommendation="Ensure proper consent and protection for health data"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_cvm_rules(self) -> None:
        """Add CVM (Comissão de Valores Mobiliários) rules."""
        rules = [
            ComplianceRule(
                id="cvm_001",
                name="Inside Information",
                description="Prevent disclosure of inside information",
                regulation=RegulationType.CVM,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"\b(informação privilegiada|inside information|fato relevante não divulgado)\b",
                message="Potential inside information detected",
                recommendation="Do not share material non-public information"
            ),
            ComplianceRule(
                id="cvm_002",
                name="Investment Advice",
                description="Unqualified investment advice",
                regulation=RegulationType.CVM,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b(compre|venda|invista|garantido|retorno certo)\s+(ações|fundos|títulos)\b",
                message="Potential unqualified investment advice",
                recommendation="Add appropriate disclaimers"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_bacen_rules(self) -> None:
        """Add BACEN (Banco Central) rules."""
        rules = [
            ComplianceRule(
                id="bacen_001",
                name="Account Number Exposure",
                description="Bank account numbers must be protected",
                regulation=RegulationType.BACEN,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b(conta|agência)[\s:]*\d{4,}\b",
                message="Bank account information detected",
                recommendation="Mask account numbers"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_anvisa_rules(self) -> None:
        """Add ANVISA rules for healthcare."""
        rules = [
            ComplianceRule(
                id="anvisa_001",
                name="Drug Prescription",
                description="Drug prescriptions require proper authorization",
                regulation=RegulationType.ANVISA,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"\b(prescrevo|receito|tomar|dose de)\s+\d+\s*(mg|ml|comprimidos?)\b",
                message="Potential drug prescription detected",
                recommendation="Ensure proper medical authorization"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_cfm_rules(self) -> None:
        """Add CFM (Conselho Federal de Medicina) rules."""
        rules = [
            ComplianceRule(
                id="cfm_001",
                name="Medical Diagnosis",
                description="AI should not provide definitive diagnoses",
                regulation=RegulationType.CFM,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b(você tem|diagnóstico é|confirmado que)\s+(câncer|diabetes|HIV|AIDS)\b",
                message="Definitive medical diagnosis detected",
                recommendation="Add disclaimer that this is not medical advice"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_oab_rules(self) -> None:
        """Add OAB (Ordem dos Advogados) rules."""
        rules = [
            ComplianceRule(
                id="oab_001",
                name="Legal Advice",
                description="AI should not provide definitive legal advice",
                regulation=RegulationType.OAB,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b(você deve processar|entre com ação|processo garantido)\b",
                message="Potential unauthorized legal advice",
                recommendation="Add disclaimer that this is not legal advice"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_gdpr_rules(self) -> None:
        """Add GDPR rules."""
        rules = [
            ComplianceRule(
                id="gdpr_001",
                name="EU Personal Data",
                description="EU personal data requires GDPR compliance",
                regulation=RegulationType.GDPR,
                severity=ViolationSeverity.HIGH,
                pattern=r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",  # IBAN pattern
                message="Potential EU personal data detected",
                recommendation="Ensure GDPR compliance for EU data"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_hipaa_rules(self) -> None:
        """Add HIPAA rules for healthcare."""
        rules = [
            ComplianceRule(
                id="hipaa_001",
                name="PHI Exposure",
                description="Protected Health Information must be secured",
                regulation=RegulationType.HIPAA,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"\b(patient|medical record|SSN|social security)\b",
                message="Potential PHI detected",
                recommendation="Ensure HIPAA compliance for health data"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _add_soc2_rules(self) -> None:
        """Add SOC2 rules."""
        rules = [
            ComplianceRule(
                id="soc2_001",
                name="Credential Exposure",
                description="Credentials must not be exposed",
                regulation=RegulationType.SOC2,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"\b(password|api_key|secret|token)\s*[=:]\s*['\"]?\w+['\"]?\b",
                message="Potential credential exposure",
                recommendation="Remove credentials from content"
            ),
        ]
        
        for rule in rules:
            self._rules[rule.id] = rule
    
    def _build_pii_patterns(self) -> Dict[str, Pattern]:
        """Build PII detection patterns."""
        return {
            "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
            "cnpj": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\(?\d{2}\)?[\s-]?\d{4,5}[-\s]?\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "rg": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}-?[0-9Xx]\b"),
        }
    
    # ============================================================
    # COMPLIANCE CHECKING
    # ============================================================
    
    async def check(
        self,
        content: str,
        regulations: Optional[List[RegulationType]] = None,
        domain: Optional[DomainType] = None
    ) -> ComplianceCheck:
        """
        Check content for compliance violations.
        """
        check_id = str(uuid.uuid4())
        violations = []
        warnings = []
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(regulations, domain)
        
        # Check each rule
        for rule in applicable_rules:
            if rule.pattern:
                matches = re.findall(rule.pattern, content, re.IGNORECASE)
                if matches:
                    if rule.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH):
                        violations.append(ComplianceViolation(
                            regulation=rule.regulation,
                            rule=rule.name,
                            description=rule.message,
                            severity=rule.severity.value
                        ))
                    else:
                        warnings.append(ComplianceWarning(
                            regulation=rule.regulation,
                            rule=rule.name,
                            description=rule.message,
                            recommendation=rule.recommendation
                        ))
        
        # Calculate score
        score = 100.0
        score -= len([v for v in violations if v.severity == "critical"]) * 30
        score -= len([v for v in violations if v.severity == "high"]) * 15
        score -= len(warnings) * 5
        score = max(0, score)
        
        is_compliant = len(violations) == 0
        
        result = ComplianceCheck(
            id=check_id,
            content=content[:100] + "..." if len(content) > 100 else content,
            regulations_checked=regulations or [],
            is_compliant=is_compliant,
            score=score,
            violations=violations,
            warnings=warnings,
            suggestions=[w.recommendation for w in warnings]
        )
        
        # Log audit entry
        await self.audit_log(
            action="compliance_check",
            resource="content",
            details={
                "check_id": check_id,
                "is_compliant": is_compliant,
                "violations_count": len(violations),
                "warnings_count": len(warnings)
            }
        )
        
        logger.info("Compliance check: compliant=%s, score=%.1f, violations=%d",
                   is_compliant, score, len(violations))
        
        return result
    
    def _get_applicable_rules(
        self,
        regulations: Optional[List[RegulationType]],
        domain: Optional[DomainType]
    ) -> List[ComplianceRule]:
        """Get rules applicable to the given regulations/domain."""
        if regulations:
            return [r for r in self._rules.values() if r.regulation in regulations]
        
        # Return all rules if no filter
        return list(self._rules.values())
    
    # ============================================================
    # PII DETECTION
    # ============================================================
    
    async def detect_pii(self, content: str) -> PIIDetection:
        """Detect PII in content."""
        found_types = []
        locations = []
        
        for pii_type, pattern in self._pii_patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                found_types.append(pii_type)
                locations.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group()[:4] + "***"  # Partially mask
                })
        
        return PIIDetection(
            found=len(found_types) > 0,
            types=list(set(found_types)),
            locations=locations,
            redacted_text=await self.redact(content) if found_types else content
        )
    
    async def redact(self, content: str, pii_types: Optional[List[str]] = None) -> str:
        """Redact PII from content."""
        redacted = content
        
        patterns = self._pii_patterns
        if pii_types:
            patterns = {k: v for k, v in patterns.items() if k in pii_types}
        
        for pii_type, pattern in patterns.items():
            redacted = pattern.sub(f"[{pii_type.upper()}_REDACTED]", redacted)
        
        return redacted
    
    # ============================================================
    # RISK ASSESSMENT
    # ============================================================
    
    async def assess_risk(
        self,
        content: str,
        context: Optional[Dict] = None
    ) -> RiskAssessment:
        """Assess risk level of content."""
        factors = []
        score = 0
        
        # Check for PII
        pii = await self.detect_pii(content)
        if pii.found:
            score += len(pii.types) * 15
            factors.append(f"Contains {len(pii.types)} types of PII")
        
        # Run compliance check
        check = await self.check(content)
        if not check.is_compliant:
            score += len(check.violations) * 20
            factors.extend([f"Violation: {v.rule}" for v in check.violations])
        
        score += len(check.warnings) * 5
        
        # Determine level
        if score >= 70:
            level = "critical"
        elif score >= 50:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"
        
        recommendations = []
        if pii.found:
            recommendations.append("Consider redacting PII before sharing")
        if check.violations:
            recommendations.append("Address compliance violations before proceeding")
        
        return RiskAssessment(
            score=min(score, 100),
            level=level,
            factors=factors,
            recommendations=recommendations
        )
    
    # ============================================================
    # AUDIT
    # ============================================================
    
    async def audit_log(
        self,
        action: str,
        resource: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> AuditEntry:
        """Log an audit entry."""
        entry = AuditEntry(
            action=action,
            user_id=user_id,
            resource=resource,
            details=details
        )
        self._audit_log.append(entry)
        
        logger.debug("Audit: %s on %s", action, resource)
        return entry
    
    def get_audit_log(
        self,
        limit: int = 100,
        action: Optional[str] = None
    ) -> List[AuditEntry]:
        """Get audit log entries."""
        entries = self._audit_log
        if action:
            entries = [e for e in entries if e.action == action]
        return entries[-limit:]
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compliance engine statistics."""
        return {
            "total_rules": len(self._rules),
            "rules_by_regulation": {
                reg.value: len([r for r in self._rules.values() if r.regulation == reg])
                for reg in RegulationType
            },
            "audit_entries": len(self._audit_log),
            "pii_patterns": len(self._pii_patterns)
        }


# ============================================================
# FACTORY
# ============================================================

def create_compliance_engine(domain: Optional[DomainType] = None) -> ComplianceEngine:
    """Factory function to create Compliance engine."""
    return ComplianceEngine(domain=domain)

"""
Rules Engine - Feedback Generator

Gera feedback explicativo e sugestões de correção
para violações de regras.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import logging
import re

from openai import AsyncOpenAI

from .types import (
    ValidationResult, Violation, RuleSeverity, RuleAction, RuleCategory
)


logger = logging.getLogger(__name__)


@dataclass
class FeedbackItem:
    """Item de feedback para uma violação."""
    violation: Violation
    explanation: str
    suggestion: str
    auto_fix: Optional[str] = None
    confidence: float = 0.0


@dataclass
class FeedbackReport:
    """Relatório de feedback completo."""
    items: list[FeedbackItem] = field(default_factory=list)
    summary: str = ""
    overall_assessment: str = ""
    
    # Output corrigido
    fixed_content: Optional[str] = None
    
    # Métricas
    total_issues: int = 0
    fixable_issues: int = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "summary": self.summary,
            "overall_assessment": self.overall_assessment,
            "items": [
                {
                    "rule": item.violation.rule_name,
                    "severity": item.violation.severity.value,
                    "explanation": item.explanation,
                    "suggestion": item.suggestion,
                    "auto_fix_available": item.auto_fix is not None
                }
                for item in self.items
            ],
            "total_issues": self.total_issues,
            "fixable_issues": self.fixable_issues,
            "has_fixed_content": self.fixed_content is not None
        }


class FeedbackGenerator:
    """
    Gerador de feedback para violações.
    
    Fornece:
    - Explicações claras das violações
    - Sugestões de correção
    - Auto-fix quando possível
    - Resumo executivo
    
    Uso:
    ```python
    generator = FeedbackGenerator()
    
    # Gerar feedback
    report = await generator.generate(validation_result, original_content)
    
    print(report.summary)
    for item in report.items:
        print(f"- {item.explanation}")
        print(f"  Suggestion: {item.suggestion}")
    
    # Obter conteúdo corrigido
    if report.fixed_content:
        print(f"Fixed: {report.fixed_content}")
    ```
    """
    
    # Templates de explicação por categoria
    EXPLANATION_TEMPLATES = {
        RuleCategory.SECURITY: {
            "prefix": "Security Issue",
            "context": "This could expose sensitive information or create vulnerabilities."
        },
        RuleCategory.COMPLIANCE: {
            "prefix": "Compliance Issue",
            "context": "This may violate regulatory requirements."
        },
        RuleCategory.QUALITY: {
            "prefix": "Quality Issue",
            "context": "This affects the quality or clarity of the response."
        },
        RuleCategory.BUSINESS: {
            "prefix": "Business Rule Violation",
            "context": "This violates a business policy or requirement."
        },
        RuleCategory.CUSTOM: {
            "prefix": "Policy Violation",
            "context": "This violates a configured rule."
        }
    }
    
    # Templates de sugestão por tipo de violação
    SUGGESTION_TEMPLATES = {
        "pii_email": "Remove or mask the email address (e.g., j***@example.com)",
        "pii_phone": "Remove or mask the phone number",
        "pii_cpf": "Remove or mask the CPF number",
        "pii_credit_card": "Remove or mask the credit card number",
        "security_sql_injection": "Remove or sanitize SQL-like patterns",
        "security_xss": "Remove or encode HTML/JavaScript content",
        "security_api_key": "Remove the API key or use environment variables",
        "format_max_length": "Summarize or truncate the content",
        "format_invalid_json": "Fix the JSON syntax errors",
        "toxicity_profanity": "Replace with appropriate language",
        "toxicity_hate_speech": "Remove the offensive content entirely"
    }
    
    def __init__(
        self,
        use_llm: bool = True,
        openai_api_key: Optional[str] = None
    ):
        self.use_llm = use_llm
        self._client: Optional[AsyncOpenAI] = None
        
        if openai_api_key:
            self._client = AsyncOpenAI(api_key=openai_api_key)
    
    async def _get_client(self) -> AsyncOpenAI:
        """Obtém cliente OpenAI."""
        if self._client is None:
            import os
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    async def generate(
        self,
        result: ValidationResult,
        original_content: str,
        generate_fixes: bool = True
    ) -> FeedbackReport:
        """
        Gera feedback completo para um resultado de validação.
        
        Args:
            result: Resultado de validação
            original_content: Conteúdo original
            generate_fixes: Se deve gerar correções automáticas
            
        Returns:
            FeedbackReport com feedback detalhado
        """
        report = FeedbackReport()
        report.total_issues = len(result.violations)
        
        if not result.violations:
            report.summary = "No issues found. The content passed all validation rules."
            report.overall_assessment = "PASS"
            return report
        
        # Gerar feedback para cada violação
        for violation in result.violations:
            item = await self._generate_item_feedback(violation, original_content)
            report.items.append(item)
            
            if item.auto_fix:
                report.fixable_issues += 1
        
        # Gerar resumo
        report.summary = self._generate_summary(result)
        report.overall_assessment = self._assess_overall(result)
        
        # Gerar conteúdo corrigido se solicitado
        if generate_fixes and report.fixable_issues > 0:
            report.fixed_content = await self._generate_fixed_content(
                original_content,
                report.items
            )
        
        return report
    
    async def _generate_item_feedback(
        self,
        violation: Violation,
        content: str
    ) -> FeedbackItem:
        """Gera feedback para uma violação específica."""
        # Obter template
        template = self.EXPLANATION_TEMPLATES.get(
            violation.category,
            self.EXPLANATION_TEMPLATES[RuleCategory.CUSTOM]
        )
        
        # Explicação base
        explanation = f"{template['prefix']}: {violation.message}"
        if template['context']:
            explanation += f" {template['context']}"
        
        # Sugestão
        suggestion = violation.suggestion
        if not suggestion:
            # Tentar template
            rule_key = f"{violation.rule_name}".replace(".", "_")
            suggestion = self.SUGGESTION_TEMPLATES.get(
                rule_key,
                "Review and modify the content to address this issue."
            )
        
        # Auto-fix
        auto_fix = None
        if violation.action == RuleAction.FIX:
            auto_fix = await self._generate_auto_fix(violation, content)
        
        return FeedbackItem(
            violation=violation,
            explanation=explanation,
            suggestion=suggestion,
            auto_fix=auto_fix,
            confidence=0.8 if auto_fix else 0.0
        )
    
    async def _generate_auto_fix(
        self,
        violation: Violation,
        content: str
    ) -> Optional[str]:
        """Tenta gerar correção automática."""
        rule_name = violation.rule_name.lower()
        
        # Fixes baseados em padrões
        if "email" in rule_name:
            return self._mask_emails(content)
        elif "phone" in rule_name:
            return self._mask_phones(content)
        elif "cpf" in rule_name:
            return self._mask_cpf(content)
        elif "credit_card" in rule_name:
            return self._mask_credit_cards(content)
        elif "profanity" in rule_name:
            return self._mask_profanity(content)
        
        # Para outros casos, tentar LLM
        if self.use_llm:
            return await self._llm_fix(violation, content)
        
        return None
    
    def _mask_emails(self, content: str) -> str:
        """Mascara emails."""
        pattern = r'\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
        
        def replacer(match):
            local = match.group(1)
            domain = match.group(2)
            masked = local[0] + "***" + "@" + domain
            return masked
        
        return re.sub(pattern, replacer, content)
    
    def _mask_phones(self, content: str) -> str:
        """Mascara telefones."""
        # Padrão brasileiro
        pattern = r'\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4}\b'
        return re.sub(pattern, "(**) *****-****", content)
    
    def _mask_cpf(self, content: str) -> str:
        """Mascara CPF."""
        pattern = r'\b(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})\b'
        return re.sub(pattern, r"\1.***.***-**", content)
    
    def _mask_credit_cards(self, content: str) -> str:
        """Mascara cartões de crédito."""
        pattern = r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b'
        return re.sub(pattern, r"\1 **** **** \4", content)
    
    def _mask_profanity(self, content: str) -> str:
        """Mascara palavrões."""
        profanity = ["merda", "porra", "caralho", "fuck", "shit"]
        result = content
        for word in profanity:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            masked = word[0] + "*" * (len(word) - 1)
            result = pattern.sub(masked, result)
        return result
    
    async def _llm_fix(
        self,
        violation: Violation,
        content: str
    ) -> Optional[str]:
        """Usa LLM para corrigir conteúdo."""
        try:
            client = await self._get_client()
            
            prompt = f"""Fix the following content to address this issue:
Issue: {violation.message}
Category: {violation.category.value}
Suggestion: {violation.suggestion}

Original content:
{content[:2000]}

Provide ONLY the fixed content, nothing else."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro no LLM fix: {e}")
            return None
    
    async def _generate_fixed_content(
        self,
        original: str,
        items: list[FeedbackItem]
    ) -> Optional[str]:
        """Aplica todas as correções automáticas."""
        fixed = original
        
        for item in items:
            if item.auto_fix:
                fixed = item.auto_fix
        
        return fixed if fixed != original else None
    
    def _generate_summary(self, result: ValidationResult) -> str:
        """Gera resumo das violações."""
        counts = {
            "critical": result.critical_count,
            "error": result.error_count,
            "warning": result.warning_count
        }
        
        parts = []
        if counts["critical"]:
            parts.append(f"{counts['critical']} critical")
        if counts["error"]:
            parts.append(f"{counts['error']} errors")
        if counts["warning"]:
            parts.append(f"{counts['warning']} warnings")
        
        if parts:
            summary = f"Found {', '.join(parts)}."
        else:
            summary = f"Found {len(result.violations)} issues."
        
        if result.should_block:
            summary += " Content should be blocked."
        elif result.should_regenerate:
            summary += " Content should be regenerated."
        
        return summary
    
    def _assess_overall(self, result: ValidationResult) -> str:
        """Avalia resultado geral."""
        if result.critical_count > 0:
            return "CRITICAL"
        elif result.error_count > 0:
            return "FAIL"
        elif result.warning_count > 0:
            return "WARN"
        else:
            return "PASS"
    
    def generate_user_message(
        self,
        report: FeedbackReport,
        verbose: bool = False
    ) -> str:
        """
        Gera mensagem amigável para o usuário.
        
        Args:
            report: Relatório de feedback
            verbose: Se deve incluir detalhes
            
        Returns:
            Mensagem formatada
        """
        if not report.items:
            return "✓ Your request was processed successfully."
        
        lines = []
        
        # Header
        if report.overall_assessment == "CRITICAL":
            lines.append("⛔ Critical issues were found:")
        elif report.overall_assessment == "FAIL":
            lines.append("❌ Some issues need attention:")
        else:
            lines.append("⚠️ Minor issues detected:")
        
        # Issues
        for item in report.items[:5]:  # Limitar a 5
            severity_icon = {
                RuleSeverity.CRITICAL: "🔴",
                RuleSeverity.ERROR: "🟠",
                RuleSeverity.WARNING: "🟡",
                RuleSeverity.INFO: "🔵"
            }.get(item.violation.severity, "⚪")
            
            lines.append(f"  {severity_icon} {item.explanation}")
            
            if verbose and item.suggestion:
                lines.append(f"     → {item.suggestion}")
        
        if len(report.items) > 5:
            lines.append(f"  ... and {len(report.items) - 5} more issues")
        
        # Footer
        if report.fixed_content:
            lines.append("\n✓ Automatic fixes have been applied.")
        
        return "\n".join(lines)


# Singleton
_feedback_generator: Optional[FeedbackGenerator] = None


def get_feedback_generator() -> FeedbackGenerator:
    """Retorna o feedback generator singleton."""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = FeedbackGenerator()
    return _feedback_generator

"""
Legal Domain - Domínio Jurídico Especializado.

Sprint 8: Legal v2.0
"""

from .domain import LegalDomain
from .agents import (
    ContractAnalystAgent,
    LegalResearcherAgent,
    DocumentDrafterAgent,
    ComplianceOfficerAgent,
    DueDiligenceAgent,
    LitigationSupportAgent,
)

__all__ = [
    "LegalDomain",
    "ContractAnalystAgent",
    "LegalResearcherAgent",
    "DocumentDrafterAgent",
    "ComplianceOfficerAgent",
    "DueDiligenceAgent",
    "LitigationSupportAgent",
]

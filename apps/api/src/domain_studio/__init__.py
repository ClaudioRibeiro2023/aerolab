"""
AGNO Domain Studio v3.5 ULTIMATE

Plataforma de Vertical AI com domínios especializados.

Features:
- 15 Domínios Especializados
- 75+ Agentes por Domínio
- Agentic RAG + GraphRAG
- Fine-tuning LORA/RLHF
- MCP Protocol Integration
- Voice-First Interface
- WebGPU 3D UI
- Zero-Trust Security
- XAI (Explainable AI)
- Gamification System
"""

from .core.types import (
    DomainType,
    DomainCapability,
    ComplianceLevel,
    DomainConfiguration,
    DomainAgent,
    DomainWorkflow,
    DomainKnowledge,
)
from .core.registry import DomainRegistry, get_domain_registry
from .core.domain_base import BaseDomain

__version__ = "3.5.0"
__all__ = [
    # Types
    "DomainType",
    "DomainCapability",
    "ComplianceLevel",
    "DomainConfiguration",
    "DomainAgent",
    "DomainWorkflow",
    "DomainKnowledge",
    # Registry
    "DomainRegistry",
    "get_domain_registry",
    # Base
    "BaseDomain",
]

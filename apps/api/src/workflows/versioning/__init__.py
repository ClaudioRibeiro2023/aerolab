"""
Sistema de Versionamento para Workflows.

Componentes:
- VersionManager: Gerencia versões de workflows
- DiffEngine: Compara versões
- MigrationEngine: Migração entre versões
"""

from .versions import (
    WorkflowVersion,
    VersionManager,
    VersionStatus,
    create_version_manager,
    get_version_manager
)
from .diff import DiffEngine, VersionDiff, DiffType

__all__ = [
    "WorkflowVersion",
    "VersionManager",
    "VersionStatus",
    "create_version_manager",
    "get_version_manager",
    "DiffEngine",
    "VersionDiff",
    "DiffType",
]

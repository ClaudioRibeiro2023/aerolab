"""
Gerenciamento de Versões de Workflows.

Features:
- Semantic versioning
- Version history
- Rollback
- Branch/merge
- Activation control
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import copy


class VersionStatus(Enum):
    """Status de uma versão."""
    DRAFT = "draft"           # Em desenvolvimento
    ACTIVE = "active"         # Versão ativa (em produção)
    DEPRECATED = "deprecated"  # Descontinuada
    ARCHIVED = "archived"     # Arquivada


@dataclass
class WorkflowVersion:
    """Representa uma versão de workflow."""
    version: str  # Semantic version: major.minor.patch
    workflow_id: str
    definition: Dict[str, Any]
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    message: str = ""
    parent_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Métricas da versão
    executions_count: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    
    @property
    def major(self) -> int:
        return int(self.version.split(".")[0])
    
    @property
    def minor(self) -> int:
        parts = self.version.split(".")
        return int(parts[1]) if len(parts) > 1 else 0
    
    @property
    def patch(self) -> int:
        parts = self.version.split(".")
        return int(parts[2]) if len(parts) > 2 else 0
    
    def increment_major(self) -> str:
        return f"{self.major + 1}.0.0"
    
    def increment_minor(self) -> str:
        return f"{self.major}.{self.minor + 1}.0"
    
    def increment_patch(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch + 1}"
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "workflow_id": self.workflow_id,
            "definition": self.definition,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "message": self.message,
            "parent_version": self.parent_version,
            "metadata": self.metadata,
            "executions_count": self.executions_count,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowVersion":
        return cls(
            version=data["version"],
            workflow_id=data["workflow_id"],
            definition=data["definition"],
            status=VersionStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            created_by=data.get("created_by", "system"),
            message=data.get("message", ""),
            parent_version=data.get("parent_version"),
            metadata=data.get("metadata", {}),
            executions_count=data.get("executions_count", 0),
            success_rate=data.get("success_rate", 0.0),
            avg_duration_ms=data.get("avg_duration_ms", 0.0)
        )


class VersionManager:
    """
    Gerenciador de versões de workflows.
    
    Exemplo:
        manager = VersionManager()
        
        # Criar versão inicial
        v1 = manager.create_version(
            workflow_id="my-workflow",
            definition={"steps": [...]},
            message="Initial version"
        )
        
        # Ativar
        manager.activate(workflow_id="my-workflow", version="1.0.0")
        
        # Criar nova versão
        v2 = manager.create_version(
            workflow_id="my-workflow",
            definition={"steps": [...]},
            message="Added new step",
            increment="minor"
        )
        
        # Rollback se necessário
        manager.rollback(workflow_id="my-workflow", target_version="1.0.0")
    """
    
    def __init__(self):
        self._versions: Dict[str, Dict[str, WorkflowVersion]] = {}  # workflow_id -> {version -> WorkflowVersion}
        self._active_versions: Dict[str, str] = {}  # workflow_id -> active version
        self._lock = threading.RLock()
    
    def create_version(
        self,
        workflow_id: str,
        definition: Dict[str, Any],
        message: str = "",
        created_by: str = "system",
        increment: str = "patch",  # major, minor, patch
        version_override: Optional[str] = None
    ) -> WorkflowVersion:
        """
        Cria nova versão de um workflow.
        
        Args:
            workflow_id: ID do workflow
            definition: Definição do workflow
            message: Mensagem de commit
            created_by: Autor
            increment: Tipo de incremento (major, minor, patch)
            version_override: Versão específica (ignora increment)
        """
        with self._lock:
            # Determinar versão
            if version_override:
                new_version = version_override
            else:
                versions = self._versions.get(workflow_id, {})
                if not versions:
                    new_version = "1.0.0"
                else:
                    # Pegar última versão
                    sorted_versions = sorted(
                        versions.values(),
                        key=lambda v: (v.major, v.minor, v.patch),
                        reverse=True
                    )
                    latest = sorted_versions[0]
                    
                    if increment == "major":
                        new_version = latest.increment_major()
                    elif increment == "minor":
                        new_version = latest.increment_minor()
                    else:
                        new_version = latest.increment_patch()
            
            # Verificar se versão já existe
            if workflow_id in self._versions and new_version in self._versions[workflow_id]:
                raise ValueError(f"Version {new_version} already exists for {workflow_id}")
            
            # Criar versão
            parent = self._active_versions.get(workflow_id)
            
            version = WorkflowVersion(
                version=new_version,
                workflow_id=workflow_id,
                definition=copy.deepcopy(definition),
                message=message,
                created_by=created_by,
                parent_version=parent
            )
            
            # Armazenar
            if workflow_id not in self._versions:
                self._versions[workflow_id] = {}
            
            self._versions[workflow_id][new_version] = version
            
            return version
    
    def get_version(self, workflow_id: str, version: str) -> Optional[WorkflowVersion]:
        """Obtém versão específica."""
        with self._lock:
            versions = self._versions.get(workflow_id, {})
            return versions.get(version)
    
    def get_active_version(self, workflow_id: str) -> Optional[WorkflowVersion]:
        """Obtém versão ativa."""
        with self._lock:
            active_ver = self._active_versions.get(workflow_id)
            if active_ver:
                return self.get_version(workflow_id, active_ver)
            return None
    
    def list_versions(
        self,
        workflow_id: str,
        status: Optional[VersionStatus] = None
    ) -> List[WorkflowVersion]:
        """Lista versões de um workflow."""
        with self._lock:
            versions = list(self._versions.get(workflow_id, {}).values())
            
            if status:
                versions = [v for v in versions if v.status == status]
            
            return sorted(
                versions,
                key=lambda v: (v.major, v.minor, v.patch),
                reverse=True
            )
    
    def activate(self, workflow_id: str, version: str) -> bool:
        """Ativa uma versão."""
        with self._lock:
            ver = self.get_version(workflow_id, version)
            if not ver:
                return False
            
            # Desativar versão anterior
            current_active = self._active_versions.get(workflow_id)
            if current_active and current_active in self._versions.get(workflow_id, {}):
                self._versions[workflow_id][current_active].status = VersionStatus.DEPRECATED
            
            # Ativar nova
            ver.status = VersionStatus.ACTIVE
            self._active_versions[workflow_id] = version
            
            return True
    
    def deprecate(self, workflow_id: str, version: str) -> bool:
        """Depreca uma versão."""
        with self._lock:
            ver = self.get_version(workflow_id, version)
            if not ver:
                return False
            
            ver.status = VersionStatus.DEPRECATED
            
            if self._active_versions.get(workflow_id) == version:
                del self._active_versions[workflow_id]
            
            return True
    
    def archive(self, workflow_id: str, version: str) -> bool:
        """Arquiva uma versão."""
        with self._lock:
            ver = self.get_version(workflow_id, version)
            if not ver:
                return False
            
            ver.status = VersionStatus.ARCHIVED
            return True
    
    def rollback(self, workflow_id: str, target_version: str) -> Optional[WorkflowVersion]:
        """
        Faz rollback para versão anterior.
        
        Cria nova versão baseada na versão alvo e a ativa.
        """
        with self._lock:
            target = self.get_version(workflow_id, target_version)
            if not target:
                return None
            
            # Criar nova versão com definição da versão alvo
            new_version = self.create_version(
                workflow_id=workflow_id,
                definition=target.definition,
                message=f"Rollback to {target_version}",
                increment="patch"
            )
            
            # Ativar
            self.activate(workflow_id, new_version.version)
            
            return new_version
    
    def compare(
        self,
        workflow_id: str,
        version_a: str,
        version_b: str
    ) -> Optional[Dict]:
        """Compara duas versões."""
        with self._lock:
            a = self.get_version(workflow_id, version_a)
            b = self.get_version(workflow_id, version_b)
            
            if not a or not b:
                return None
            
            from .diff import DiffEngine
            engine = DiffEngine()
            return engine.diff(a.definition, b.definition).to_dict()
    
    def record_execution(
        self,
        workflow_id: str,
        version: str,
        success: bool,
        duration_ms: float
    ) -> None:
        """Registra execução para métricas da versão."""
        with self._lock:
            ver = self.get_version(workflow_id, version)
            if ver:
                ver.executions_count += 1
                
                # Atualizar success rate
                total = ver.executions_count
                current_success = ver.success_rate * (total - 1)
                ver.success_rate = (current_success + (1 if success else 0)) / total
                
                # Atualizar avg duration
                current_duration = ver.avg_duration_ms * (total - 1)
                ver.avg_duration_ms = (current_duration + duration_ms) / total
    
    def get_history(self, workflow_id: str, limit: int = 20) -> List[Dict]:
        """Retorna histórico de versões."""
        versions = self.list_versions(workflow_id)
        
        return [
            {
                "version": v.version,
                "status": v.status.value,
                "message": v.message,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by,
                "executions": v.executions_count,
                "success_rate": v.success_rate
            }
            for v in versions[:limit]
        ]


# Singleton
_version_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """Obtém version manager global."""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


def create_version_manager() -> VersionManager:
    """Cria novo version manager."""
    return VersionManager()

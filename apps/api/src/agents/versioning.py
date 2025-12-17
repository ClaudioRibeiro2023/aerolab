"""
Sistema de Versionamento de Agentes.

Permite versionar configurações de agentes e fazer rollback.
"""

import os
import json
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum


class VersionStatus(Enum):
    """Status de uma versão."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class AgentVersion:
    """Versão de um agente."""
    version: str
    agent_name: str
    config: Dict[str, Any]
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    changelog: Optional[str] = None
    parent_version: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "agent_name": self.agent_name,
            "config": self.config,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "changelog": self.changelog,
            "parent_version": self.parent_version,
            "metrics": self.metrics
        }
    
    @property
    def config_hash(self) -> str:
        """Hash da configuração para comparação."""
        config_str = json.dumps(self.config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]


@dataclass 
class VersionComparison:
    """Comparação entre duas versões."""
    version_a: str
    version_b: str
    added: Dict[str, Any]
    removed: Dict[str, Any]
    changed: Dict[str, Dict[str, Any]]


class AgentVersionManager:
    """
    Gerenciador de versões de agentes.
    
    Features:
    - Versionamento semântico
    - Histórico de mudanças
    - Rollback para versões anteriores
    - Comparação entre versões
    - A/B testing entre versões
    - Métricas por versão
    
    Exemplo:
        manager = AgentVersionManager()
        
        # Criar nova versão
        v1 = manager.create_version(
            agent_name="Researcher",
            config={"temperature": 0.7, "model": "gpt-4"},
            changelog="Versão inicial"
        )
        
        # Ativar versão
        manager.activate(v1.version)
        
        # Rollback
        manager.rollback("Researcher", "1.0.0")
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv("VERSIONS_STORAGE_PATH", "./data/versions"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._versions: Dict[str, List[AgentVersion]] = {}  # agent_name -> versions
        self._active: Dict[str, str] = {}  # agent_name -> active_version
        
        self._load_versions()
    
    def _load_versions(self):
        """Carrega versões salvas."""
        versions_file = self.storage_path / "versions.json"
        if versions_file.exists():
            data = json.loads(versions_file.read_text())
            
            for agent_name, versions in data.get("versions", {}).items():
                self._versions[agent_name] = [
                    AgentVersion(
                        version=v["version"],
                        agent_name=v["agent_name"],
                        config=v["config"],
                        status=VersionStatus(v["status"]),
                        created_at=datetime.fromisoformat(v["created_at"]),
                        created_by=v.get("created_by"),
                        changelog=v.get("changelog"),
                        parent_version=v.get("parent_version"),
                        metrics=v.get("metrics", {})
                    )
                    for v in versions
                ]
            
            self._active = data.get("active", {})
    
    def _save_versions(self):
        """Salva versões."""
        data = {
            "versions": {
                agent_name: [v.to_dict() for v in versions]
                for agent_name, versions in self._versions.items()
            },
            "active": self._active
        }
        (self.storage_path / "versions.json").write_text(json.dumps(data, indent=2))
    
    def _get_next_version(self, agent_name: str, bump: str = "patch") -> str:
        """Calcula próxima versão."""
        versions = self._versions.get(agent_name, [])
        
        if not versions:
            return "1.0.0"
        
        # Pegar última versão
        last = versions[-1].version
        major, minor, patch = map(int, last.split("."))
        
        if bump == "major":
            return f"{major + 1}.0.0"
        elif bump == "minor":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"
    
    def create_version(
        self,
        agent_name: str,
        config: Dict[str, Any],
        changelog: Optional[str] = None,
        created_by: Optional[str] = None,
        bump: str = "patch"
    ) -> AgentVersion:
        """
        Cria nova versão de um agente.
        
        Args:
            agent_name: Nome do agente
            config: Configuração do agente
            changelog: Descrição das mudanças
            created_by: Usuário que criou
            bump: Tipo de incremento (major, minor, patch)
        """
        version_str = self._get_next_version(agent_name, bump)
        parent = self._active.get(agent_name)
        
        version = AgentVersion(
            version=version_str,
            agent_name=agent_name,
            config=config,
            changelog=changelog,
            created_by=created_by,
            parent_version=parent
        )
        
        if agent_name not in self._versions:
            self._versions[agent_name] = []
        
        self._versions[agent_name].append(version)
        self._save_versions()
        
        return version
    
    def activate(self, agent_name: str, version: str) -> bool:
        """Ativa uma versão específica."""
        versions = self._versions.get(agent_name, [])
        target = next((v for v in versions if v.version == version), None)
        
        if not target:
            return False
        
        # Deprecar versão anterior
        if agent_name in self._active:
            old_version = self._active[agent_name]
            for v in versions:
                if v.version == old_version:
                    v.status = VersionStatus.DEPRECATED
        
        # Ativar nova
        target.status = VersionStatus.ACTIVE
        self._active[agent_name] = version
        self._save_versions()
        
        return True
    
    def rollback(self, agent_name: str, target_version: str) -> bool:
        """Rollback para versão anterior."""
        return self.activate(agent_name, target_version)
    
    def get_active_version(self, agent_name: str) -> Optional[AgentVersion]:
        """Obtém versão ativa de um agente."""
        version_str = self._active.get(agent_name)
        if not version_str:
            return None
        
        versions = self._versions.get(agent_name, [])
        return next((v for v in versions if v.version == version_str), None)
    
    def get_active_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Obtém configuração da versão ativa."""
        version = self.get_active_version(agent_name)
        return version.config if version else None
    
    def list_versions(
        self,
        agent_name: str,
        status: Optional[VersionStatus] = None
    ) -> List[AgentVersion]:
        """Lista versões de um agente."""
        versions = self._versions.get(agent_name, [])
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def get_version(self, agent_name: str, version: str) -> Optional[AgentVersion]:
        """Obtém versão específica."""
        versions = self._versions.get(agent_name, [])
        return next((v for v in versions if v.version == version), None)
    
    def compare_versions(
        self,
        agent_name: str,
        version_a: str,
        version_b: str
    ) -> Optional[VersionComparison]:
        """Compara duas versões."""
        v_a = self.get_version(agent_name, version_a)
        v_b = self.get_version(agent_name, version_b)
        
        if not v_a or not v_b:
            return None
        
        config_a = v_a.config
        config_b = v_b.config
        
        added = {k: v for k, v in config_b.items() if k not in config_a}
        removed = {k: v for k, v in config_a.items() if k not in config_b}
        changed = {
            k: {"old": config_a[k], "new": config_b[k]}
            for k in config_a
            if k in config_b and config_a[k] != config_b[k]
        }
        
        return VersionComparison(
            version_a=version_a,
            version_b=version_b,
            added=added,
            removed=removed,
            changed=changed
        )
    
    def update_metrics(
        self,
        agent_name: str,
        version: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Atualiza métricas de uma versão."""
        v = self.get_version(agent_name, version)
        if not v:
            return False
        
        v.metrics.update(metrics)
        self._save_versions()
        return True
    
    def archive(self, agent_name: str, version: str) -> bool:
        """Arquiva uma versão."""
        v = self.get_version(agent_name, version)
        if not v:
            return False
        
        v.status = VersionStatus.ARCHIVED
        self._save_versions()
        return True
    
    def delete_archived(self, agent_name: str, keep_last: int = 5) -> int:
        """Remove versões arquivadas antigas."""
        versions = self._versions.get(agent_name, [])
        archived = [v for v in versions if v.status == VersionStatus.ARCHIVED]
        
        if len(archived) <= keep_last:
            return 0
        
        to_delete = archived[:-keep_last]
        for v in to_delete:
            versions.remove(v)
        
        self._save_versions()
        return len(to_delete)


# Singleton
_version_manager: Optional[AgentVersionManager] = None


def get_version_manager() -> AgentVersionManager:
    """Obtém instância singleton do VersionManager."""
    global _version_manager
    if _version_manager is None:
        _version_manager = AgentVersionManager()
    return _version_manager

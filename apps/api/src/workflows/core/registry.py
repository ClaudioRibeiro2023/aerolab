"""
Workflow Registry - Registro e gerenciamento de definições de workflows.

Funcionalidades:
- CRUD de workflows
- Validação de definições
- Versionamento básico
- Persistência
"""

import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Definição de um step de workflow."""
    id: str
    type: str  # agent, condition, parallel, loop, action, etc.
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    next_step: Optional[str] = None  # ID do próximo step
    on_error: Optional[str] = None  # Step a executar em caso de erro
    retry_policy: Optional[Dict] = None
    timeout_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "config": self.config,
            "next_step": self.next_step,
            "on_error": self.on_error,
            "retry_policy": self.retry_policy,
            "timeout_seconds": self.timeout_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowStep":
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            config=data.get("config", {}),
            next_step=data.get("next_step"),
            on_error=data.get("on_error"),
            retry_policy=data.get("retry_policy"),
            timeout_seconds=data.get("timeout_seconds")
        )


@dataclass
class WorkflowDefinition:
    """Definição completa de um workflow."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    start_step: Optional[str] = None
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Obtém step por ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_start_step(self) -> Optional[WorkflowStep]:
        """Obtém step inicial."""
        if self.start_step:
            return self.get_step(self.start_step)
        if self.steps:
            return self.steps[0]
        return None
    
    def get_next_step(self, current_step_id: str) -> Optional[WorkflowStep]:
        """Obtém próximo step após o atual."""
        current = self.get_step(current_step_id)
        if current and current.next_step:
            return self.get_step(current.next_step)
        
        # Se não tem next_step definido, segue a ordem
        for i, step in enumerate(self.steps):
            if step.id == current_step_id:
                if i + 1 < len(self.steps):
                    return self.steps[i + 1]
        return None
    
    def validate(self) -> List[str]:
        """Valida a definição do workflow."""
        errors = []
        
        if not self.id:
            errors.append("Workflow ID is required")
        if not self.name:
            errors.append("Workflow name is required")
        if not self.steps:
            errors.append("Workflow must have at least one step")
        
        # Verificar IDs únicos
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique")
        
        # Verificar referências válidas
        for step in self.steps:
            if step.next_step and step.next_step not in step_ids:
                errors.append(f"Step {step.id} references unknown next_step: {step.next_step}")
            if step.on_error and step.on_error not in step_ids:
                errors.append(f"Step {step.id} references unknown on_error: {step.on_error}")
        
        # Verificar start_step
        if self.start_step and self.start_step not in step_ids:
            errors.append(f"Invalid start_step: {self.start_step}")
        
        return errors
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [s.to_dict() for s in self.steps],
            "start_step": self.start_step,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "enabled": self.enabled,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            start_step=data.get("start_step"),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            created_by=data.get("created_by", "system"),
            enabled=data.get("enabled", True),
            tags=data.get("tags", [])
        )


class WorkflowRegistry:
    """
    Registro central de workflows.
    
    Features:
    - CRUD de definições
    - Validação
    - Persistência em arquivo/SQLite
    - Thread-safe
    
    Exemplo:
        registry = WorkflowRegistry()
        
        # Registrar workflow
        definition = WorkflowDefinition(
            id="data-pipeline",
            name="Data Pipeline",
            steps=[
                WorkflowStep(id="extract", type="action", name="Extract"),
                WorkflowStep(id="transform", type="agent", name="Transform"),
                WorkflowStep(id="load", type="action", name="Load"),
            ]
        )
        registry.register(definition)
        
        # Obter
        wf = registry.get("data-pipeline")
        
        # Listar
        workflows = registry.list()
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._versions: Dict[str, List[WorkflowDefinition]] = {}
        self._lock = threading.RLock()
        self._storage_path = Path(storage_path) if storage_path else None
        
        # Carregar do storage se existir
        if self._storage_path and self._storage_path.exists():
            self._load_from_storage()
    
    def register(
        self,
        definition: WorkflowDefinition,
        validate: bool = True
    ) -> WorkflowDefinition:
        """
        Registra um workflow.
        
        Args:
            definition: Definição do workflow
            validate: Se deve validar antes de registrar
            
        Returns:
            Definição registrada
            
        Raises:
            ValueError: Se validação falhar
        """
        with self._lock:
            if validate:
                errors = definition.validate()
                if errors:
                    raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
            
            # Atualizar timestamp
            definition.updated_at = datetime.now()
            
            # Guardar versão anterior
            if definition.id in self._workflows:
                old = self._workflows[definition.id]
                if definition.id not in self._versions:
                    self._versions[definition.id] = []
                self._versions[definition.id].append(old)
                
                # Incrementar versão
                parts = definition.version.split(".")
                parts[-1] = str(int(parts[-1]) + 1)
                definition.version = ".".join(parts)
            
            self._workflows[definition.id] = definition
            
            # Persistir
            if self._storage_path:
                self._save_to_storage()
            
            logger.info(f"Registered workflow: {definition.id} v{definition.version}")
            return definition
    
    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Obtém workflow por ID."""
        with self._lock:
            return self._workflows.get(workflow_id)
    
    def get_version(
        self,
        workflow_id: str,
        version: str
    ) -> Optional[WorkflowDefinition]:
        """Obtém versão específica de um workflow."""
        with self._lock:
            # Verificar versão atual
            current = self._workflows.get(workflow_id)
            if current and current.version == version:
                return current
            
            # Buscar em versões anteriores
            versions = self._versions.get(workflow_id, [])
            for v in versions:
                if v.version == version:
                    return v
            
            return None
    
    def list(
        self,
        enabled_only: bool = True,
        tags: Optional[List[str]] = None
    ) -> List[WorkflowDefinition]:
        """Lista workflows com filtros."""
        with self._lock:
            results = list(self._workflows.values())
            
            if enabled_only:
                results = [w for w in results if w.enabled]
            
            if tags:
                results = [w for w in results if any(t in w.tags for t in tags)]
            
            return results
    
    def delete(self, workflow_id: str) -> bool:
        """Remove workflow do registro."""
        with self._lock:
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
                if workflow_id in self._versions:
                    del self._versions[workflow_id]
                
                if self._storage_path:
                    self._save_to_storage()
                
                logger.info(f"Deleted workflow: {workflow_id}")
                return True
            return False
    
    def enable(self, workflow_id: str) -> bool:
        """Habilita workflow."""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id].enabled = True
                if self._storage_path:
                    self._save_to_storage()
                return True
            return False
    
    def disable(self, workflow_id: str) -> bool:
        """Desabilita workflow."""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id].enabled = False
                if self._storage_path:
                    self._save_to_storage()
                return True
            return False
    
    def get_versions(self, workflow_id: str) -> List[str]:
        """Lista todas as versões de um workflow."""
        with self._lock:
            versions = []
            
            current = self._workflows.get(workflow_id)
            if current:
                versions.append(current.version)
            
            for v in self._versions.get(workflow_id, []):
                versions.append(v.version)
            
            return sorted(versions, reverse=True)
    
    def _load_from_storage(self) -> None:
        """Carrega workflows do storage."""
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for wf_data in data.get("workflows", []):
                definition = WorkflowDefinition.from_dict(wf_data)
                self._workflows[definition.id] = definition
            
            logger.info(f"Loaded {len(self._workflows)} workflows from storage")
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
    
    def _save_to_storage(self) -> None:
        """Salva workflows no storage."""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "workflows": [w.to_dict() for w in self._workflows.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self._workflows)} workflows to storage")
        except Exception as e:
            logger.error(f"Failed to save workflows: {e}")
    
    def export(self, workflow_id: str) -> Optional[Dict]:
        """Exporta workflow como dict."""
        wf = self.get(workflow_id)
        return wf.to_dict() if wf else None
    
    def import_workflow(self, data: Dict, overwrite: bool = False) -> WorkflowDefinition:
        """Importa workflow de dict."""
        definition = WorkflowDefinition.from_dict(data)
        
        if not overwrite and definition.id in self._workflows:
            raise ValueError(f"Workflow {definition.id} already exists")
        
        return self.register(definition)


# Singleton global
_registry: Optional[WorkflowRegistry] = None


def get_registry(storage_path: Optional[str] = None) -> WorkflowRegistry:
    """Obtém registry global."""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry(storage_path)
    return _registry


def create_registry(storage_path: Optional[str] = None) -> WorkflowRegistry:
    """Cria novo registry."""
    return WorkflowRegistry(storage_path)

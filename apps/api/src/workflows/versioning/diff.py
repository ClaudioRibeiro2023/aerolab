"""
Engine de Diff para comparação de versões de Workflows.

Features:
- Diff estrutural de definições
- Detecção de mudanças em steps
- Visualização de diferenças
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum


class DiffType(Enum):
    """Tipos de diferença."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffItem:
    """Um item de diferença."""
    path: str  # Caminho no JSON (e.g., "steps[0].config")
    diff_type: DiffType
    old_value: Any = None
    new_value: Any = None
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "type": self.diff_type.value,
            "old": self.old_value,
            "new": self.new_value
        }


@dataclass
class VersionDiff:
    """Resultado de um diff entre versões."""
    items: List[DiffItem] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def add(self, item: DiffItem) -> None:
        self.items.append(item)
        self.summary[item.diff_type.value] = self.summary.get(item.diff_type.value, 0) + 1
    
    @property
    def has_changes(self) -> bool:
        return any(
            item.diff_type != DiffType.UNCHANGED
            for item in self.items
        )
    
    @property
    def added_count(self) -> int:
        return self.summary.get("added", 0)
    
    @property
    def removed_count(self) -> int:
        return self.summary.get("removed", 0)
    
    @property
    def modified_count(self) -> int:
        return self.summary.get("modified", 0)
    
    def to_dict(self) -> Dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary,
            "has_changes": self.has_changes
        }
    
    def to_markdown(self) -> str:
        """Gera markdown do diff."""
        lines = ["## Diff Summary\n"]
        lines.append(f"- Added: {self.added_count}")
        lines.append(f"- Removed: {self.removed_count}")
        lines.append(f"- Modified: {self.modified_count}")
        lines.append("\n## Changes\n")
        
        for item in self.items:
            if item.diff_type == DiffType.ADDED:
                lines.append(f"+ `{item.path}`: {item.new_value}")
            elif item.diff_type == DiffType.REMOVED:
                lines.append(f"- `{item.path}`: ~~{item.old_value}~~")
            elif item.diff_type == DiffType.MODIFIED:
                lines.append(f"~ `{item.path}`: {item.old_value} → {item.new_value}")
        
        return "\n".join(lines)


class DiffEngine:
    """
    Engine para comparar versões de workflows.
    
    Exemplo:
        engine = DiffEngine()
        
        old_def = {"steps": [{"id": "step1", "type": "agent"}]}
        new_def = {"steps": [{"id": "step1", "type": "agent"}, {"id": "step2", "type": "condition"}]}
        
        diff = engine.diff(old_def, new_def)
        print(diff.to_markdown())
    """
    
    def diff(
        self,
        old: Dict[str, Any],
        new: Dict[str, Any],
        path: str = ""
    ) -> VersionDiff:
        """
        Compara duas definições.
        
        Args:
            old: Definição antiga
            new: Definição nova
            path: Caminho atual (para recursão)
        """
        result = VersionDiff()
        
        self._compare(old, new, path, result)
        
        return result
    
    def _compare(
        self,
        old: Any,
        new: Any,
        path: str,
        result: VersionDiff
    ) -> None:
        """Compara valores recursivamente."""
        # Tipos diferentes
        if type(old) != type(new):
            result.add(DiffItem(
                path=path or "root",
                diff_type=DiffType.MODIFIED,
                old_value=self._summarize(old),
                new_value=self._summarize(new)
            ))
            return
        
        # Dicionários
        if isinstance(old, dict) and isinstance(new, dict):
            self._compare_dicts(old, new, path, result)
            return
        
        # Listas
        if isinstance(old, list) and isinstance(new, list):
            self._compare_lists(old, new, path, result)
            return
        
        # Valores primitivos
        if old != new:
            result.add(DiffItem(
                path=path or "root",
                diff_type=DiffType.MODIFIED,
                old_value=old,
                new_value=new
            ))
    
    def _compare_dicts(
        self,
        old: Dict,
        new: Dict,
        path: str,
        result: VersionDiff
    ) -> None:
        """Compara dicionários."""
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            
            if key not in old:
                result.add(DiffItem(
                    path=new_path,
                    diff_type=DiffType.ADDED,
                    new_value=self._summarize(new[key])
                ))
            elif key not in new:
                result.add(DiffItem(
                    path=new_path,
                    diff_type=DiffType.REMOVED,
                    old_value=self._summarize(old[key])
                ))
            else:
                self._compare(old[key], new[key], new_path, result)
    
    def _compare_lists(
        self,
        old: List,
        new: List,
        path: str,
        result: VersionDiff
    ) -> None:
        """Compara listas."""
        # Tentar match por ID se elementos são dicts com ID
        if old and new and isinstance(old[0], dict) and isinstance(new[0], dict):
            if "id" in old[0] and "id" in new[0]:
                self._compare_lists_by_id(old, new, path, result)
                return
        
        # Comparação por índice
        max_len = max(len(old), len(new))
        
        for i in range(max_len):
            item_path = f"{path}[{i}]"
            
            if i >= len(old):
                result.add(DiffItem(
                    path=item_path,
                    diff_type=DiffType.ADDED,
                    new_value=self._summarize(new[i])
                ))
            elif i >= len(new):
                result.add(DiffItem(
                    path=item_path,
                    diff_type=DiffType.REMOVED,
                    old_value=self._summarize(old[i])
                ))
            else:
                self._compare(old[i], new[i], item_path, result)
    
    def _compare_lists_by_id(
        self,
        old: List[Dict],
        new: List[Dict],
        path: str,
        result: VersionDiff
    ) -> None:
        """Compara listas de dicts usando ID como chave."""
        old_by_id = {item["id"]: item for item in old}
        new_by_id = {item["id"]: item for item in new}
        
        all_ids = set(old_by_id.keys()) | set(new_by_id.keys())
        
        for item_id in all_ids:
            item_path = f"{path}[id={item_id}]"
            
            if item_id not in old_by_id:
                result.add(DiffItem(
                    path=item_path,
                    diff_type=DiffType.ADDED,
                    new_value=self._summarize(new_by_id[item_id])
                ))
            elif item_id not in new_by_id:
                result.add(DiffItem(
                    path=item_path,
                    diff_type=DiffType.REMOVED,
                    old_value=self._summarize(old_by_id[item_id])
                ))
            else:
                self._compare(old_by_id[item_id], new_by_id[item_id], item_path, result)
    
    def _summarize(self, value: Any, max_length: int = 100) -> Any:
        """Cria resumo de um valor para exibição."""
        if isinstance(value, dict):
            if "id" in value and "type" in value:
                return f"<{value['type']}:{value['id']}>"
            return f"<dict:{len(value)} keys>"
        elif isinstance(value, list):
            return f"<list:{len(value)} items>"
        elif isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        return value

"""
Dashboard Export/Import - Exportação e importação de dashboards.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, BinaryIO
import json
import base64
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExportMetadata:
    """Metadados de exportação."""
    version: str = "1.0.0"
    exported_at: datetime = field(default_factory=datetime.now)
    exported_by: str = ""
    source_dashboard_id: str = ""
    checksum: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "exportedAt": self.exported_at.isoformat(),
            "exportedBy": self.exported_by,
            "sourceDashboardId": self.source_dashboard_id,
            "checksum": self.checksum,
        }


@dataclass
class ImportResult:
    """Resultado de importação."""
    success: bool = False
    dashboard_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    widgets_imported: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "dashboardId": self.dashboard_id,
            "errors": self.errors,
            "warnings": self.warnings,
            "widgetsImported": self.widgets_imported,
        }


class DashboardExporter:
    """
    Exportador de dashboards.
    
    Suporta formatos:
    - JSON
    - JSON comprimido (base64)
    """
    
    EXPORT_VERSION = "1.0.0"
    
    def export_to_json(
        self,
        dashboard: Dict[str, Any],
        include_data: bool = False,
        pretty: bool = True,
    ) -> str:
        """
        Exporta dashboard para JSON.
        
        Args:
            dashboard: Configuração do dashboard
            include_data: Incluir dados dos widgets
            pretty: Formatação legível
        """
        export_data = self._prepare_export(dashboard, include_data)
        
        if pretty:
            return json.dumps(export_data, indent=2, default=str)
        return json.dumps(export_data, default=str)
    
    def export_to_file(
        self,
        dashboard: Dict[str, Any],
        file_path: str,
        include_data: bool = False,
    ):
        """Exporta dashboard para arquivo."""
        json_str = self.export_to_json(dashboard, include_data, pretty=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        logger.info(f"Dashboard exported to {file_path}")
    
    def export_to_base64(
        self,
        dashboard: Dict[str, Any],
        include_data: bool = False,
    ) -> str:
        """Exporta dashboard para base64 (comprimido)."""
        json_str = self.export_to_json(dashboard, include_data, pretty=False)
        
        # Comprimir e codificar
        import zlib
        compressed = zlib.compress(json_str.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        return encoded
    
    def _prepare_export(
        self,
        dashboard: Dict[str, Any],
        include_data: bool,
    ) -> Dict[str, Any]:
        """Prepara dados para exportação."""
        # Copiar dashboard
        export = {
            "dashboard": self._sanitize_dashboard(dashboard),
        }
        
        # Adicionar metadados
        checksum = self._calculate_checksum(export["dashboard"])
        
        export["metadata"] = ExportMetadata(
            version=self.EXPORT_VERSION,
            source_dashboard_id=dashboard.get("id", ""),
            checksum=checksum,
        ).to_dict()
        
        return export
    
    def _sanitize_dashboard(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Remove dados sensíveis e IDs específicos."""
        sanitized = dashboard.copy()
        
        # Remover campos específicos da instância
        fields_to_remove = [
            "id",
            "createdAt",
            "updatedAt",
            "createdBy",
            "version",
        ]
        
        for field_name in fields_to_remove:
            sanitized.pop(field_name, None)
        
        # Sanitizar widgets
        if "widgets" in sanitized:
            sanitized["widgets"] = [
                self._sanitize_widget(w) for w in sanitized["widgets"]
            ]
        
        return sanitized
    
    def _sanitize_widget(self, widget: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza widget para exportação."""
        sanitized = widget.copy()
        
        # Gerar novo ID placeholder
        sanitized.pop("id", None)
        
        # Remover dados cached
        sanitized.pop("cachedData", None)
        sanitized.pop("lastUpdated", None)
        
        return sanitized
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Calcula checksum dos dados."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class DashboardImporter:
    """
    Importador de dashboards.
    
    Valida e importa dashboards de diferentes formatos.
    """
    
    SUPPORTED_VERSIONS = ["1.0.0"]
    
    def import_from_json(
        self,
        json_str: str,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> ImportResult:
        """Importa dashboard de JSON."""
        result = ImportResult()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result
        
        return self._process_import(data, user_id, folder_id)
    
    def import_from_file(
        self,
        file_path: str,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> ImportResult:
        """Importa dashboard de arquivo."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
        except Exception as e:
            result = ImportResult()
            result.errors.append(f"Error reading file: {e}")
            return result
        
        return self.import_from_json(json_str, user_id, folder_id)
    
    def import_from_base64(
        self,
        encoded: str,
        user_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> ImportResult:
        """Importa dashboard de base64."""
        result = ImportResult()
        
        try:
            import zlib
            decoded = base64.b64decode(encoded)
            decompressed = zlib.decompress(decoded)
            json_str = decompressed.decode('utf-8')
        except Exception as e:
            result.errors.append(f"Error decoding: {e}")
            return result
        
        return self.import_from_json(json_str, user_id, folder_id)
    
    def _process_import(
        self,
        data: Dict[str, Any],
        user_id: Optional[str],
        folder_id: Optional[str],
    ) -> ImportResult:
        """Processa importação."""
        result = ImportResult()
        
        # Validar estrutura
        if "dashboard" not in data:
            result.errors.append("Missing 'dashboard' key in import data")
            return result
        
        # Validar versão
        metadata = data.get("metadata", {})
        version = metadata.get("version", "1.0.0")
        
        if version not in self.SUPPORTED_VERSIONS:
            result.warnings.append(
                f"Version {version} may not be fully compatible"
            )
        
        # Verificar checksum
        if "checksum" in metadata:
            expected_checksum = metadata["checksum"]
            actual_checksum = self._calculate_checksum(data["dashboard"])
            
            if expected_checksum != actual_checksum:
                result.warnings.append(
                    "Checksum mismatch - data may have been modified"
                )
        
        # Processar dashboard
        dashboard = data["dashboard"]
        
        # Validar widgets
        widgets = dashboard.get("widgets", [])
        valid_widgets = []
        
        for i, widget in enumerate(widgets):
            validation = self._validate_widget(widget)
            
            if validation["valid"]:
                # Gerar novo ID
                widget["id"] = f"widget_{datetime.now().timestamp()}_{i}"
                valid_widgets.append(widget)
            else:
                result.warnings.append(
                    f"Widget {i} skipped: {validation['error']}"
                )
        
        dashboard["widgets"] = valid_widgets
        result.widgets_imported = len(valid_widgets)
        
        # Atualizar layout items com novos IDs
        if "layout" in dashboard and "items" in dashboard["layout"]:
            new_items = []
            for item in dashboard["layout"]["items"]:
                old_id = item.get("widgetId")
                # Encontrar novo ID correspondente
                for widget in valid_widgets:
                    if widget.get("_originalId") == old_id:
                        item["widgetId"] = widget["id"]
                        new_items.append(item)
                        break
            dashboard["layout"]["items"] = new_items
        
        # Gerar novo ID para dashboard
        dashboard["id"] = f"dashboard_{datetime.now().timestamp()}"
        dashboard["createdAt"] = datetime.now().isoformat()
        dashboard["updatedAt"] = datetime.now().isoformat()
        dashboard["createdBy"] = user_id or "import"
        dashboard["version"] = 1
        
        if folder_id:
            dashboard["folderId"] = folder_id
        
        result.success = True
        result.dashboard_id = dashboard["id"]
        
        # Store para uso posterior (em implementação real, salvaria no banco)
        result._imported_dashboard = dashboard
        
        return result
    
    def _validate_widget(self, widget: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração de widget."""
        required_fields = ["type", "query"]
        
        for field_name in required_fields:
            if field_name not in widget:
                return {"valid": False, "error": f"Missing field: {field_name}"}
        
        valid_types = [
            "metric_card", "line_chart", "area_chart", "bar_chart",
            "pie_chart", "donut_chart", "table", "gauge", "text",
            "markdown", "scatter_chart", "heatmap",
        ]
        
        if widget["type"] not in valid_types:
            return {"valid": False, "error": f"Invalid type: {widget['type']}"}
        
        return {"valid": True}
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Calcula checksum dos dados."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def preview_import(self, json_str: str) -> Dict[str, Any]:
        """
        Pré-visualiza importação sem efetuar.
        
        Retorna informações sobre o que seria importado.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON"}
        
        if "dashboard" not in data:
            return {"error": "Invalid format"}
        
        dashboard = data["dashboard"]
        
        return {
            "name": dashboard.get("name", "Untitled"),
            "description": dashboard.get("description", ""),
            "widgetCount": len(dashboard.get("widgets", [])),
            "widgetTypes": list(set(
                w.get("type") for w in dashboard.get("widgets", [])
            )),
            "tags": dashboard.get("tags", []),
            "metadata": data.get("metadata", {}),
        }

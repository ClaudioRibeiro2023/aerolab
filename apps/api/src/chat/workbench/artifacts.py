"""
Artifacts - Conteúdo rico gerado pelo assistente.

Tipos suportados:
- Code: Código com syntax highlighting
- Document: Texto formatado (Markdown)
- Spreadsheet: Dados tabulares
- Diagram: Mermaid, PlantUML
- HTML: Páginas web
- React: Componentes React
- Chart: Gráficos interativos
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ArtifactType(str, Enum):
    """Tipos de artifacts."""
    CODE = "code"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    DIAGRAM = "diagram"
    HTML = "html"
    REACT = "react"
    CHART = "chart"
    IMAGE = "image"
    SVG = "svg"


@dataclass
class ArtifactVersion:
    """Versão de um artifact."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "assistant"  # assistant ou user
    message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "message": self.message
        }


@dataclass
class Artifact:
    """
    Artifact gerado pelo assistente.
    
    Pode ser:
    - Código com execução em sandbox
    - Documento Markdown
    - HTML com preview
    - React component
    - Diagrama
    - Gráfico
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificação
    message_id: str = ""
    conversation_id: str = ""
    
    # Tipo e conteúdo
    type: ArtifactType = ArtifactType.CODE
    title: str = "Untitled"
    content: str = ""
    
    # Para código
    language: Optional[str] = None
    filename: Optional[str] = None
    
    # Preview
    preview_html: Optional[str] = None
    preview_url: Optional[str] = None
    
    # Versionamento
    versions: List[ArtifactVersion] = field(default_factory=list)
    current_version: int = 0
    
    # Status
    is_executing: bool = False
    execution_result: Optional[str] = None
    execution_error: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        # Criar versão inicial
        if not self.versions and self.content:
            self.versions.append(ArtifactVersion(content=self.content))
    
    @property
    def has_preview(self) -> bool:
        return self.type in (
            ArtifactType.HTML, 
            ArtifactType.REACT, 
            ArtifactType.CHART,
            ArtifactType.DIAGRAM,
            ArtifactType.SVG
        )
    
    @property
    def is_editable(self) -> bool:
        return self.type in (
            ArtifactType.CODE,
            ArtifactType.DOCUMENT,
            ArtifactType.HTML,
            ArtifactType.REACT
        )
    
    @property
    def can_execute(self) -> bool:
        return self.type == ArtifactType.CODE and self.language in (
            "python", "javascript", "typescript", "html"
        )
    
    def update_content(self, content: str, message: str = "") -> None:
        """Atualiza conteúdo criando nova versão."""
        self.versions.append(ArtifactVersion(
            content=content,
            message=message
        ))
        self.content = content
        self.current_version = len(self.versions) - 1
        self.updated_at = datetime.now()
    
    def revert_to_version(self, version_index: int) -> bool:
        """Reverte para uma versão anterior."""
        if 0 <= version_index < len(self.versions):
            self.content = self.versions[version_index].content
            self.current_version = version_index
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_version(self, version_index: int) -> Optional[ArtifactVersion]:
        """Obtém uma versão específica."""
        if 0 <= version_index < len(self.versions):
            return self.versions[version_index]
        return None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "language": self.language,
            "filename": self.filename,
            "preview_html": self.preview_html,
            "preview_url": self.preview_url,
            "versions": [v.to_dict() for v in self.versions],
            "current_version": self.current_version,
            "is_executing": self.is_executing,
            "execution_result": self.execution_result,
            "execution_error": self.execution_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Artifact":
        artifact = cls(
            id=data.get("id", str(uuid.uuid4())),
            message_id=data.get("message_id", ""),
            conversation_id=data.get("conversation_id", ""),
            type=ArtifactType(data.get("type", "code")),
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            language=data.get("language"),
            filename=data.get("filename"),
            preview_html=data.get("preview_html"),
            preview_url=data.get("preview_url"),
            current_version=data.get("current_version", 0),
            execution_result=data.get("execution_result"),
            execution_error=data.get("execution_error"),
            metadata=data.get("metadata", {})
        )
        
        # Parse versions
        if "versions" in data:
            artifact.versions = []
            for v in data["versions"]:
                artifact.versions.append(ArtifactVersion(
                    id=v.get("id"),
                    content=v.get("content", ""),
                    created_by=v.get("created_by", "assistant"),
                    message=v.get("message", "")
                ))
        
        return artifact
    
    @classmethod
    def code(cls, content: str, language: str, title: str = "Code", **kwargs) -> "Artifact":
        """Cria artifact de código."""
        return cls(
            type=ArtifactType.CODE,
            title=title,
            content=content,
            language=language,
            **kwargs
        )
    
    @classmethod
    def document(cls, content: str, title: str = "Document", **kwargs) -> "Artifact":
        """Cria artifact de documento."""
        return cls(
            type=ArtifactType.DOCUMENT,
            title=title,
            content=content,
            **kwargs
        )
    
    @classmethod
    def html(cls, content: str, title: str = "Preview", **kwargs) -> "Artifact":
        """Cria artifact HTML."""
        return cls(
            type=ArtifactType.HTML,
            title=title,
            content=content,
            preview_html=content,
            **kwargs
        )
    
    @classmethod
    def react(cls, content: str, title: str = "Component", **kwargs) -> "Artifact":
        """Cria artifact React."""
        return cls(
            type=ArtifactType.REACT,
            title=title,
            content=content,
            language="tsx",
            **kwargs
        )
    
    @classmethod
    def diagram(cls, content: str, diagram_type: str = "mermaid", title: str = "Diagram", **kwargs) -> "Artifact":
        """Cria artifact de diagrama."""
        return cls(
            type=ArtifactType.DIAGRAM,
            title=title,
            content=content,
            metadata={"diagram_type": diagram_type},
            **kwargs
        )


class ArtifactManager:
    """
    Gerenciador de artifacts.
    
    Responsável por:
    - CRUD de artifacts
    - Detecção automática de tipo
    - Geração de previews
    - Execução de código
    """
    
    def __init__(self):
        self._artifacts: Dict[str, Artifact] = {}
        self._by_message: Dict[str, List[str]] = {}  # message_id -> artifact_ids
        self._by_conversation: Dict[str, List[str]] = {}  # conversation_id -> artifact_ids
    
    async def create(
        self,
        content: str,
        artifact_type: ArtifactType,
        message_id: str,
        conversation_id: str,
        title: str = "Untitled",
        language: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Artifact:
        """Cria um novo artifact."""
        artifact = Artifact(
            type=artifact_type,
            title=title,
            content=content,
            message_id=message_id,
            conversation_id=conversation_id,
            language=language,
            metadata=metadata or {}
        )
        
        self._artifacts[artifact.id] = artifact
        
        # Indexar
        if message_id not in self._by_message:
            self._by_message[message_id] = []
        self._by_message[message_id].append(artifact.id)
        
        if conversation_id not in self._by_conversation:
            self._by_conversation[conversation_id] = []
        self._by_conversation[conversation_id].append(artifact.id)
        
        # Gerar preview se aplicável
        if artifact.has_preview:
            await self._generate_preview(artifact)
        
        return artifact
    
    async def get(self, artifact_id: str) -> Optional[Artifact]:
        """Obtém um artifact por ID."""
        return self._artifacts.get(artifact_id)
    
    async def get_by_message(self, message_id: str) -> List[Artifact]:
        """Obtém artifacts de uma mensagem."""
        artifact_ids = self._by_message.get(message_id, [])
        return [self._artifacts[aid] for aid in artifact_ids if aid in self._artifacts]
    
    async def get_by_conversation(self, conversation_id: str) -> List[Artifact]:
        """Obtém artifacts de uma conversa."""
        artifact_ids = self._by_conversation.get(conversation_id, [])
        return [self._artifacts[aid] for aid in artifact_ids if aid in self._artifacts]
    
    async def update(
        self,
        artifact_id: str,
        content: str,
        message: str = ""
    ) -> Optional[Artifact]:
        """Atualiza conteúdo de um artifact."""
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            artifact.update_content(content, message)
            
            if artifact.has_preview:
                await self._generate_preview(artifact)
            
            return artifact
        return None
    
    async def delete(self, artifact_id: str) -> bool:
        """Deleta um artifact."""
        artifact = self._artifacts.pop(artifact_id, None)
        if artifact:
            # Remover dos índices
            if artifact.message_id in self._by_message:
                self._by_message[artifact.message_id] = [
                    aid for aid in self._by_message[artifact.message_id] 
                    if aid != artifact_id
                ]
            if artifact.conversation_id in self._by_conversation:
                self._by_conversation[artifact.conversation_id] = [
                    aid for aid in self._by_conversation[artifact.conversation_id]
                    if aid != artifact_id
                ]
            return True
        return False
    
    async def _generate_preview(self, artifact: Artifact) -> None:
        """Gera preview HTML para um artifact."""
        if artifact.type == ArtifactType.HTML:
            artifact.preview_html = artifact.content
        
        elif artifact.type == ArtifactType.SVG:
            artifact.preview_html = artifact.content
        
        elif artifact.type == ArtifactType.DIAGRAM:
            # Mermaid diagram
            diagram_type = artifact.metadata.get("diagram_type", "mermaid")
            if diagram_type == "mermaid":
                artifact.preview_html = f'''
                <div class="mermaid">
                {artifact.content}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>mermaid.initialize({{startOnLoad:true}});</script>
                '''
        
        elif artifact.type == ArtifactType.REACT:
            # React component preview (simplificado)
            artifact.preview_html = f'''
            <div id="root"></div>
            <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
            <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
            <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
            <script type="text/babel">
            {artifact.content}
            </script>
            '''
    
    async def execute_code(self, artifact_id: str) -> Dict[str, Any]:
        """
        Executa código de um artifact em sandbox.
        
        Em produção, isso usaria Pyodide (Python) ou QuickJS (JavaScript).
        """
        artifact = self._artifacts.get(artifact_id)
        if not artifact or not artifact.can_execute:
            return {"error": "Cannot execute this artifact"}
        
        artifact.is_executing = True
        
        try:
            if artifact.language == "python":
                result = await self._execute_python(artifact.content)
            elif artifact.language in ("javascript", "typescript"):
                result = await self._execute_javascript(artifact.content)
            else:
                result = {"error": f"Unsupported language: {artifact.language}"}
            
            artifact.execution_result = result.get("output", "")
            artifact.execution_error = result.get("error")
            
            return result
        
        finally:
            artifact.is_executing = False
    
    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Executa código Python (placeholder)."""
        # Em produção: usar Pyodide ou sandbox server
        return {
            "output": "[Python execution not implemented in this environment]",
            "error": None
        }
    
    async def _execute_javascript(self, code: str) -> Dict[str, Any]:
        """Executa código JavaScript (placeholder)."""
        # Em produção: usar QuickJS ou sandbox server
        return {
            "output": "[JavaScript execution not implemented in this environment]",
            "error": None
        }
    
    def detect_type(self, content: str, filename: Optional[str] = None) -> ArtifactType:
        """Detecta tipo de artifact pelo conteúdo ou filename."""
        if filename:
            ext = filename.split(".")[-1].lower()
            
            if ext in ("py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "go", "rs"):
                return ArtifactType.CODE
            elif ext in ("md", "txt", "rst"):
                return ArtifactType.DOCUMENT
            elif ext in ("html", "htm"):
                return ArtifactType.HTML
            elif ext == "svg":
                return ArtifactType.SVG
            elif ext in ("csv", "tsv"):
                return ArtifactType.SPREADSHEET
        
        # Detectar por conteúdo
        content_lower = content.lower().strip()
        
        if content_lower.startswith("<!doctype html") or content_lower.startswith("<html"):
            return ArtifactType.HTML
        
        if content_lower.startswith("<svg"):
            return ArtifactType.SVG
        
        if "```mermaid" in content_lower or content_lower.startswith("graph ") or content_lower.startswith("sequencediagram"):
            return ArtifactType.DIAGRAM
        
        if "import react" in content_lower or "from 'react'" in content_lower:
            return ArtifactType.REACT
        
        # Default: código
        return ArtifactType.CODE


# Singleton
_artifact_manager: Optional[ArtifactManager] = None


def get_artifact_manager() -> ArtifactManager:
    """Obtém o gerenciador de artifacts singleton."""
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager

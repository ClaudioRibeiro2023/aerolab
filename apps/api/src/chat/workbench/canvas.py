"""
Canvas - Espaço de trabalho colaborativo.

Similar ao ChatGPT Canvas, permite:
- Edição colaborativa
- Múltiplos elementos
- Real-time sync
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ElementType(str, Enum):
    """Tipos de elementos no canvas."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    SHAPE = "shape"
    STICKY = "sticky"
    FRAME = "frame"
    CONNECTOR = "connector"


@dataclass
class Position:
    """Posição no canvas."""
    x: float = 0
    y: float = 0
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}


@dataclass
class Size:
    """Tamanho de um elemento."""
    width: float = 200
    height: float = 100
    
    def to_dict(self) -> Dict:
        return {"width": self.width, "height": self.height}


@dataclass
class CanvasElement:
    """
    Elemento individual no canvas.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ElementType = ElementType.TEXT
    
    # Posição e tamanho
    position: Position = field(default_factory=Position)
    size: Size = field(default_factory=Size)
    rotation: float = 0
    
    # Conteúdo
    content: str = ""
    
    # Para código
    language: Optional[str] = None
    
    # Para imagens
    image_url: Optional[str] = None
    
    # Estilo
    style: Dict[str, Any] = field(default_factory=lambda: {
        "backgroundColor": "#ffffff",
        "borderColor": "#e5e7eb",
        "borderWidth": 1,
        "borderRadius": 8,
        "fontSize": 14,
        "fontFamily": "Inter",
        "color": "#1f2937"
    })
    
    # Estado
    locked: bool = False
    visible: bool = True
    selected: bool = False
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "rotation": self.rotation,
            "content": self.content,
            "language": self.language,
            "image_url": self.image_url,
            "style": self.style,
            "locked": self.locked,
            "visible": self.visible,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def text(cls, content: str, x: float = 0, y: float = 0, **kwargs) -> "CanvasElement":
        """Cria elemento de texto."""
        return cls(
            type=ElementType.TEXT,
            content=content,
            position=Position(x, y),
            **kwargs
        )
    
    @classmethod
    def code(cls, content: str, language: str, x: float = 0, y: float = 0, **kwargs) -> "CanvasElement":
        """Cria elemento de código."""
        element = cls(
            type=ElementType.CODE,
            content=content,
            language=language,
            position=Position(x, y),
            size=Size(400, 300),
            **kwargs
        )
        element.style["fontFamily"] = "monospace"
        element.style["backgroundColor"] = "#1e1e1e"
        element.style["color"] = "#d4d4d4"
        return element
    
    @classmethod
    def sticky(cls, content: str, color: str = "#fef3c7", x: float = 0, y: float = 0, **kwargs) -> "CanvasElement":
        """Cria sticky note."""
        element = cls(
            type=ElementType.STICKY,
            content=content,
            position=Position(x, y),
            size=Size(200, 200),
            **kwargs
        )
        element.style["backgroundColor"] = color
        return element


@dataclass
class Canvas:
    """
    Canvas colaborativo.
    
    Espaço de trabalho que contém múltiplos elementos
    e suporta edição em tempo real.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    
    # Elementos
    elements: List[CanvasElement] = field(default_factory=list)
    
    # Viewport
    viewport: Dict[str, float] = field(default_factory=lambda: {
        "x": 0,
        "y": 0,
        "zoom": 1.0
    })
    
    # Background
    background_color: str = "#ffffff"
    grid_enabled: bool = True
    grid_size: int = 20
    
    # Estado
    is_collaborative: bool = False
    collaborators: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_element(self, element: CanvasElement) -> None:
        """Adiciona um elemento."""
        self.elements.append(element)
        self.updated_at = datetime.now()
    
    def remove_element(self, element_id: str) -> bool:
        """Remove um elemento."""
        initial_len = len(self.elements)
        self.elements = [e for e in self.elements if e.id != element_id]
        
        if len(self.elements) < initial_len:
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_element(self, element_id: str) -> Optional[CanvasElement]:
        """Obtém um elemento por ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def update_element(
        self,
        element_id: str,
        content: Optional[str] = None,
        position: Optional[Position] = None,
        size: Optional[Size] = None,
        style: Optional[Dict] = None
    ) -> Optional[CanvasElement]:
        """Atualiza um elemento."""
        element = self.get_element(element_id)
        if not element:
            return None
        
        if content is not None:
            element.content = content
        
        if position is not None:
            element.position = position
        
        if size is not None:
            element.size = size
        
        if style is not None:
            element.style.update(style)
        
        element.updated_at = datetime.now()
        self.updated_at = datetime.now()
        
        return element
    
    def move_element(self, element_id: str, x: float, y: float) -> Optional[CanvasElement]:
        """Move um elemento."""
        return self.update_element(element_id, position=Position(x, y))
    
    def resize_element(self, element_id: str, width: float, height: float) -> Optional[CanvasElement]:
        """Redimensiona um elemento."""
        return self.update_element(element_id, size=Size(width, height))
    
    def duplicate_element(self, element_id: str, offset: float = 20) -> Optional[CanvasElement]:
        """Duplica um elemento."""
        original = self.get_element(element_id)
        if not original:
            return None
        
        # Criar cópia
        new_element = CanvasElement(
            type=original.type,
            content=original.content,
            position=Position(
                original.position.x + offset,
                original.position.y + offset
            ),
            size=Size(original.size.width, original.size.height),
            rotation=original.rotation,
            language=original.language,
            style=original.style.copy()
        )
        
        self.add_element(new_element)
        return new_element
    
    def clear(self) -> None:
        """Limpa todos os elementos."""
        self.elements.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "elements": [e.to_dict() for e in self.elements],
            "viewport": self.viewport,
            "background_color": self.background_color,
            "grid_enabled": self.grid_enabled,
            "grid_size": self.grid_size,
            "is_collaborative": self.is_collaborative,
            "collaborators": self.collaborators,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def to_export_format(self, format: str = "json") -> str:
        """Exporta canvas para formato específico."""
        if format == "json":
            import json
            return json.dumps(self.to_dict(), indent=2)
        
        elif format == "markdown":
            lines = ["# Canvas Export\n"]
            for element in self.elements:
                if element.type == ElementType.TEXT:
                    lines.append(element.content)
                    lines.append("")
                elif element.type == ElementType.CODE:
                    lines.append(f"```{element.language or ''}")
                    lines.append(element.content)
                    lines.append("```")
                    lines.append("")
            return "\n".join(lines)
        
        return ""


class CanvasManager:
    """Gerenciador de canvas."""
    
    def __init__(self):
        self._canvases: Dict[str, Canvas] = {}
    
    async def create(self, conversation_id: str) -> Canvas:
        """Cria um novo canvas."""
        canvas = Canvas(conversation_id=conversation_id)
        self._canvases[canvas.id] = canvas
        return canvas
    
    async def get(self, canvas_id: str) -> Optional[Canvas]:
        """Obtém um canvas."""
        return self._canvases.get(canvas_id)
    
    async def get_by_conversation(self, conversation_id: str) -> Optional[Canvas]:
        """Obtém canvas de uma conversa."""
        for canvas in self._canvases.values():
            if canvas.conversation_id == conversation_id:
                return canvas
        return None
    
    async def get_or_create(self, conversation_id: str) -> Canvas:
        """Obtém ou cria canvas para uma conversa."""
        canvas = await self.get_by_conversation(conversation_id)
        if canvas:
            return canvas
        return await self.create(conversation_id)
    
    async def delete(self, canvas_id: str) -> bool:
        """Deleta um canvas."""
        if canvas_id in self._canvases:
            del self._canvases[canvas_id]
            return True
        return False


# Singleton
_canvas_manager: Optional[CanvasManager] = None


def get_canvas_manager() -> CanvasManager:
    """Obtém o gerenciador de canvas singleton."""
    global _canvas_manager
    if _canvas_manager is None:
        _canvas_manager = CanvasManager()
    return _canvas_manager

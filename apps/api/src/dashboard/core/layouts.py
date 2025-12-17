"""
Layouts - Sistema de layout para dashboards.

Suporta grid responsivo, tabs, panels e layouts flexíveis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class LayoutType(str, Enum):
    """Tipos de layout."""
    GRID = "grid"           # Grid responsivo
    FLEX = "flex"           # Flexbox
    TABS = "tabs"           # Abas
    SPLIT = "split"         # Split panels
    MASONRY = "masonry"     # Masonry layout
    FREE = "free"           # Posição livre


@dataclass
class GridPosition:
    """Posição em grid layout."""
    x: int = 0              # Coluna (0-11 para 12 colunas)
    y: int = 0              # Linha
    width: int = 2          # Largura em colunas
    height: int = 1         # Altura em rows
    
    # Responsivo
    min_width: int = 1
    min_height: int = 1
    max_width: int = 12
    max_height: int = 10
    
    # Breakpoints
    sm: Optional[Dict[str, int]] = None  # < 640px
    md: Optional[Dict[str, int]] = None  # < 768px
    lg: Optional[Dict[str, int]] = None  # < 1024px
    xl: Optional[Dict[str, int]] = None  # < 1280px
    
    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.width,
            "h": self.height,
            "minW": self.min_width,
            "minH": self.min_height,
            "maxW": self.max_width,
            "maxH": self.max_height,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
        }
    
    @classmethod
    def auto(cls, index: int, columns: int = 12, widget_width: int = 3) -> "GridPosition":
        """Calcula posição automática baseado no índice."""
        items_per_row = columns // widget_width
        row = index // items_per_row
        col = (index % items_per_row) * widget_width
        
        return cls(x=col, y=row, width=widget_width, height=1)


@dataclass
class LayoutItem:
    """Item em um layout."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    widget_id: str = ""
    position: GridPosition = field(default_factory=GridPosition)
    
    # Visibility
    visible: bool = True
    locked: bool = False  # Impede resize/move
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "widgetId": self.widget_id,
            "position": self.position.to_dict(),
            "visible": self.visible,
            "locked": self.locked,
        }


@dataclass
class TabConfig:
    """Configuração de aba."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = "Tab"
    icon: Optional[str] = None
    items: List[LayoutItem] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "icon": self.icon,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class SplitConfig:
    """Configuração de split panels."""
    direction: str = "horizontal"  # horizontal, vertical
    sizes: List[int] = field(default_factory=lambda: [50, 50])  # %
    min_sizes: List[int] = field(default_factory=lambda: [10, 10])
    resizable: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "direction": self.direction,
            "sizes": self.sizes,
            "minSizes": self.min_sizes,
            "resizable": self.resizable,
        }


@dataclass
class LayoutConfig:
    """Configuração de layout."""
    # Grid settings
    columns: int = 12
    row_height: int = 80       # pixels
    margin: List[int] = field(default_factory=lambda: [16, 16])  # [x, y]
    container_padding: List[int] = field(default_factory=lambda: [16, 16])
    
    # Behavior
    compact_type: str = "vertical"  # vertical, horizontal, none
    prevent_collision: bool = True
    is_draggable: bool = True
    is_resizable: bool = True
    
    # Tabs (se type=TABS)
    tabs: List[TabConfig] = field(default_factory=list)
    
    # Split (se type=SPLIT)
    split: Optional[SplitConfig] = None
    
    def to_dict(self) -> Dict:
        return {
            "columns": self.columns,
            "rowHeight": self.row_height,
            "margin": self.margin,
            "containerPadding": self.container_padding,
            "compactType": self.compact_type,
            "preventCollision": self.prevent_collision,
            "isDraggable": self.is_draggable,
            "isResizable": self.is_resizable,
            "tabs": [t.to_dict() for t in self.tabs] if self.tabs else [],
            "split": self.split.to_dict() if self.split else None,
        }


@dataclass
class Layout:
    """
    Layout de dashboard.
    
    Define como os widgets são organizados visualmente.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Layout"
    type: LayoutType = LayoutType.GRID
    
    # Items
    items: List[LayoutItem] = field(default_factory=list)
    
    # Config
    config: LayoutConfig = field(default_factory=LayoutConfig)
    
    # Responsiveness
    breakpoints: Dict[str, int] = field(default_factory=lambda: {
        "lg": 1200,
        "md": 996,
        "sm": 768,
        "xs": 480,
        "xxs": 0
    })
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_widget(
        self,
        widget_id: str,
        position: Optional[GridPosition] = None
    ) -> LayoutItem:
        """Adiciona widget ao layout."""
        if position is None:
            position = GridPosition.auto(len(self.items))
        
        item = LayoutItem(
            widget_id=widget_id,
            position=position
        )
        self.items.append(item)
        self.updated_at = datetime.now()
        return item
    
    def remove_widget(self, widget_id: str) -> bool:
        """Remove widget do layout."""
        initial_len = len(self.items)
        self.items = [i for i in self.items if i.widget_id != widget_id]
        
        if len(self.items) < initial_len:
            self.updated_at = datetime.now()
            return True
        return False
    
    def move_widget(
        self,
        widget_id: str,
        x: int,
        y: int
    ) -> Optional[LayoutItem]:
        """Move widget para nova posição."""
        for item in self.items:
            if item.widget_id == widget_id:
                item.position.x = x
                item.position.y = y
                self.updated_at = datetime.now()
                return item
        return None
    
    def resize_widget(
        self,
        widget_id: str,
        width: int,
        height: int
    ) -> Optional[LayoutItem]:
        """Redimensiona widget."""
        for item in self.items:
            if item.widget_id == widget_id:
                item.position.width = min(width, item.position.max_width)
                item.position.height = min(height, item.position.max_height)
                self.updated_at = datetime.now()
                return item
        return None
    
    def get_item(self, widget_id: str) -> Optional[LayoutItem]:
        """Obtém item por widget_id."""
        for item in self.items:
            if item.widget_id == widget_id:
                return item
        return None
    
    def auto_arrange(self) -> None:
        """Reorganiza items automaticamente."""
        for i, item in enumerate(self.items):
            item.position = GridPosition.auto(i)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "items": [item.to_dict() for item in self.items],
            "config": self.config.to_dict(),
            "breakpoints": self.breakpoints,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
    
    @classmethod
    def grid(cls, columns: int = 12, **kwargs) -> "Layout":
        """Cria layout em grid."""
        return cls(
            type=LayoutType.GRID,
            config=LayoutConfig(columns=columns),
            **kwargs
        )
    
    @classmethod
    def tabs(cls, tab_labels: List[str], **kwargs) -> "Layout":
        """Cria layout em abas."""
        return cls(
            type=LayoutType.TABS,
            config=LayoutConfig(
                tabs=[TabConfig(label=label) for label in tab_labels]
            ),
            **kwargs
        )
    
    @classmethod
    def split_horizontal(cls, sizes: List[int] = None, **kwargs) -> "Layout":
        """Cria layout split horizontal."""
        return cls(
            type=LayoutType.SPLIT,
            config=LayoutConfig(
                split=SplitConfig(
                    direction="horizontal",
                    sizes=sizes or [50, 50]
                )
            ),
            **kwargs
        )

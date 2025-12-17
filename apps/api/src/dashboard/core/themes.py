"""
Themes - Sistema de temas para dashboards.

Suporta temas customizados e white-label.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class ThemeMode(str, Enum):
    """Modo do tema."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ColorPalette:
    """Paleta de cores."""
    # Primary
    primary: str = "#3b82f6"
    primary_hover: str = "#2563eb"
    primary_light: str = "#eff6ff"
    
    # Secondary
    secondary: str = "#8b5cf6"
    secondary_hover: str = "#7c3aed"
    
    # Status
    success: str = "#22c55e"
    warning: str = "#eab308"
    error: str = "#ef4444"
    info: str = "#0ea5e9"
    
    # Neutral
    background: str = "#ffffff"
    surface: str = "#f8fafc"
    border: str = "#e2e8f0"
    
    # Text
    text_primary: str = "#0f172a"
    text_secondary: str = "#475569"
    text_muted: str = "#94a3b8"
    
    # Chart colors
    chart_colors: List[str] = field(default_factory=lambda: [
        "#3b82f6",  # blue
        "#8b5cf6",  # purple
        "#22c55e",  # green
        "#f59e0b",  # orange
        "#ef4444",  # red
        "#06b6d4",  # cyan
        "#ec4899",  # pink
        "#84cc16",  # lime
    ])
    
    def to_dict(self) -> Dict:
        return {
            "primary": self.primary,
            "primaryHover": self.primary_hover,
            "primaryLight": self.primary_light,
            "secondary": self.secondary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
            "background": self.background,
            "surface": self.surface,
            "border": self.border,
            "textPrimary": self.text_primary,
            "textSecondary": self.text_secondary,
            "textMuted": self.text_muted,
            "chartColors": self.chart_colors,
        }


@dataclass
class DarkColorPalette(ColorPalette):
    """Paleta de cores dark mode."""
    background: str = "#0f172a"
    surface: str = "#1e293b"
    border: str = "#334155"
    text_primary: str = "#f1f5f9"
    text_secondary: str = "#cbd5e1"
    text_muted: str = "#64748b"
    primary_light: str = "#1e3a5f"


@dataclass
class Typography:
    """Configuração de tipografia."""
    font_family: str = "Inter, system-ui, sans-serif"
    font_family_mono: str = "JetBrains Mono, monospace"
    
    # Sizes
    font_size_xs: str = "0.75rem"
    font_size_sm: str = "0.875rem"
    font_size_base: str = "1rem"
    font_size_lg: str = "1.125rem"
    font_size_xl: str = "1.25rem"
    font_size_2xl: str = "1.5rem"
    font_size_3xl: str = "1.875rem"
    
    # Weights
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_semibold: int = 600
    font_weight_bold: int = 700
    
    # Line heights
    line_height_tight: float = 1.25
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75
    
    def to_dict(self) -> Dict:
        return {
            "fontFamily": self.font_family,
            "fontFamilyMono": self.font_family_mono,
            "fontSizeXs": self.font_size_xs,
            "fontSizeSm": self.font_size_sm,
            "fontSizeBase": self.font_size_base,
            "fontSizeLg": self.font_size_lg,
            "fontSizeXl": self.font_size_xl,
        }


@dataclass
class Spacing:
    """Configuração de espaçamento."""
    unit: int = 4  # base unit in px
    
    xs: str = "0.25rem"
    sm: str = "0.5rem"
    md: str = "1rem"
    lg: str = "1.5rem"
    xl: str = "2rem"
    xxl: str = "3rem"
    
    def to_dict(self) -> Dict:
        return {
            "unit": self.unit,
            "xs": self.xs,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
        }


@dataclass
class BorderRadius:
    """Configuração de border radius."""
    none: str = "0"
    sm: str = "0.125rem"
    md: str = "0.375rem"
    lg: str = "0.5rem"
    xl: str = "0.75rem"
    xxl: str = "1rem"
    full: str = "9999px"
    
    def to_dict(self) -> Dict:
        return {
            "none": self.none,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "full": self.full,
        }


@dataclass
class Shadows:
    """Configuração de sombras."""
    none: str = "none"
    sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1)"
    lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1)"
    xl: str = "0 20px 25px -5px rgb(0 0 0 / 0.1)"
    
    def to_dict(self) -> Dict:
        return {
            "none": self.none,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
        }


@dataclass
class ThemeConfig:
    """Configuração completa de tema."""
    colors: ColorPalette = field(default_factory=ColorPalette)
    colors_dark: ColorPalette = field(default_factory=DarkColorPalette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    border_radius: BorderRadius = field(default_factory=BorderRadius)
    shadows: Shadows = field(default_factory=Shadows)
    
    def to_dict(self) -> Dict:
        return {
            "colors": self.colors.to_dict(),
            "colorsDark": self.colors_dark.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "borderRadius": self.border_radius.to_dict(),
            "shadows": self.shadows.to_dict(),
        }


@dataclass
class Theme:
    """
    Tema de dashboard.
    
    Permite customização completa da aparência.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default"
    description: str = ""
    
    # Mode
    mode: ThemeMode = ThemeMode.SYSTEM
    
    # Config
    config: ThemeConfig = field(default_factory=ThemeConfig)
    
    # White-label
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    app_name: str = "Agno Dashboard"
    
    # Custom CSS
    custom_css: str = ""
    
    # Metadata
    is_default: bool = False
    is_system: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def get_colors(self, dark: bool = False) -> ColorPalette:
        """Obtém paleta de cores."""
        return self.config.colors_dark if dark else self.config.colors
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mode": self.mode.value,
            "config": self.config.to_dict(),
            "logoUrl": self.logo_url,
            "logoDarkUrl": self.logo_dark_url,
            "faviconUrl": self.favicon_url,
            "appName": self.app_name,
            "customCss": self.custom_css,
            "isDefault": self.is_default,
            "isSystem": self.is_system,
        }
    
    def to_css_variables(self, dark: bool = False) -> str:
        """Gera CSS variables do tema."""
        colors = self.get_colors(dark)
        
        css = ":root {\n"
        css += f"  --color-primary: {colors.primary};\n"
        css += f"  --color-primary-hover: {colors.primary_hover};\n"
        css += f"  --color-secondary: {colors.secondary};\n"
        css += f"  --color-success: {colors.success};\n"
        css += f"  --color-warning: {colors.warning};\n"
        css += f"  --color-error: {colors.error};\n"
        css += f"  --color-info: {colors.info};\n"
        css += f"  --color-background: {colors.background};\n"
        css += f"  --color-surface: {colors.surface};\n"
        css += f"  --color-border: {colors.border};\n"
        css += f"  --color-text-primary: {colors.text_primary};\n"
        css += f"  --color-text-secondary: {colors.text_secondary};\n"
        css += f"  --font-family: {self.config.typography.font_family};\n"
        css += "}\n"
        
        if self.custom_css:
            css += f"\n{self.custom_css}\n"
        
        return css
    
    @classmethod
    def default(cls) -> "Theme":
        """Cria tema padrão."""
        return cls(
            name="Default",
            is_default=True,
            is_system=True
        )
    
    @classmethod
    def dark(cls) -> "Theme":
        """Cria tema dark."""
        return cls(
            name="Dark",
            mode=ThemeMode.DARK,
            is_system=True
        )


# Temas predefinidos
PRESET_THEMES = {
    "default": Theme.default(),
    "dark": Theme.dark(),
    "blue": Theme(
        name="Blue",
        config=ThemeConfig(
            colors=ColorPalette(
                primary="#0ea5e9",
                primary_hover="#0284c7",
                primary_light="#e0f2fe"
            )
        )
    ),
    "purple": Theme(
        name="Purple",
        config=ThemeConfig(
            colors=ColorPalette(
                primary="#8b5cf6",
                primary_hover="#7c3aed",
                primary_light="#ede9fe"
            )
        )
    ),
    "green": Theme(
        name="Green",
        config=ThemeConfig(
            colors=ColorPalette(
                primary="#22c55e",
                primary_hover="#16a34a",
                primary_light="#dcfce7"
            )
        )
    ),
}


def get_theme(name: str) -> Optional[Theme]:
    """Obtém tema predefinido."""
    return PRESET_THEMES.get(name)

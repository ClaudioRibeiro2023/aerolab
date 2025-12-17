"""
Ferramentas de Geolocalização.

Inclui:
- MapboxTool: Geocoding, rotas, isócronas
- SpatialTool: Análise espacial com GeoPandas/Shapely
- GeoVisualizationTool: Visualização com Folium
"""

from typing import TYPE_CHECKING

# Lazy imports para evitar dependências opcionais
if TYPE_CHECKING:
    from .mapbox import MapboxTool
    from .spatial import SpatialTool

__all__ = [
    "MapboxTool",
    "SpatialTool",
]

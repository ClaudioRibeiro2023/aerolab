"""
Ferramenta de análise espacial.

Requer:
- pip install geopandas shapely (opcional)
"""

from __future__ import annotations

import importlib.util
from typing import Any, Dict, List, Tuple

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="geo")
class SpatialTool(BaseTool):
    """
    Ferramenta para análise espacial.

    Funcionalidades:
    - Buffer: Área ao redor de geometria
    - Intersection: Interseção entre geometrias
    - Within: Verificar se ponto está dentro de polígono
    - Nearest: Encontrar ponto mais próximo
    - Distance: Calcular distância entre pontos
    """

    name = "spatial"
    description = "Análise espacial com GeoPandas/Shapely"
    version = "1.0.0"

    def _setup(self) -> None:
        """Verifica dependências."""
        self._has_shapely = importlib.util.find_spec("shapely") is not None
        self._has_geopandas = importlib.util.find_spec("geopandas") is not None

        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma ação espacial.

        Args:
            action: Ação (buffer, intersection, within, nearest, distance)
            **kwargs: Parâmetros da ação

        Returns:
            ToolResult com os dados
        """
        actions = {
            "buffer": self._buffer,
            "intersection": self._intersection,
            "within": self._within,
            "nearest": self._nearest,
            "distance": self._distance,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _buffer(
        self,
        point: Tuple[float, float],
        distance_km: float,
    ) -> ToolResult:
        """
        Cria buffer ao redor de um ponto.

        Args:
            point: (lat, lon)
            distance_km: Raio em km

        Returns:
            ToolResult com polígono do buffer
        """
        if not self._has_shapely:
            return ToolResult.fail("Shapely não instalado. Use: pip install shapely")

        try:
            from shapely.geometry import Point
            from shapely.ops import transform
            import pyproj

            # Criar ponto
            pt = Point(point[1], point[0])  # lon, lat

            # Projetar para metros (UTM aproximado)
            project = pyproj.Transformer.from_crs(
                "EPSG:4326", "EPSG:3857", always_xy=True
            ).transform
            pt_proj = transform(project, pt)

            # Buffer em metros
            buffer_proj = pt_proj.buffer(distance_km * 1000)

            # Reprojetar para lat/lon
            project_back = pyproj.Transformer.from_crs(
                "EPSG:3857", "EPSG:4326", always_xy=True
            ).transform
            buffer_geo = transform(project_back, buffer_proj)

            return ToolResult.ok({
                "center": point,
                "distance_km": distance_km,
                "geometry": buffer_geo.__geo_interface__,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no buffer: {str(e)}")

    def _within(
        self,
        point: Tuple[float, float],
        polygon: Dict[str, Any],
    ) -> ToolResult:
        """
        Verifica se ponto está dentro de polígono.

        Args:
            point: (lat, lon)
            polygon: GeoJSON do polígono

        Returns:
            ToolResult com resultado booleano
        """
        if not self._has_shapely:
            return ToolResult.fail("Shapely não instalado")

        try:
            from shapely.geometry import Point, shape

            pt = Point(point[1], point[0])
            poly = shape(polygon)

            is_within = pt.within(poly)

            return ToolResult.ok({
                "point": point,
                "within": is_within,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no within: {str(e)}")

    def _distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float],
    ) -> ToolResult:
        """
        Calcula distância entre dois pontos (Haversine).

        Args:
            point1: (lat, lon)
            point2: (lat, lon)

        Returns:
            ToolResult com distância em km
        """
        import math

        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371  # Raio da Terra em km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return ToolResult.ok({
            "point1": point1,
            "point2": point2,
            "distance_km": round(distance, 3),
        })

    def _intersection(
        self,
        geom1: Dict[str, Any],
        geom2: Dict[str, Any],
    ) -> ToolResult:
        """
        Calcula interseção entre duas geometrias.

        Args:
            geom1: GeoJSON da primeira geometria
            geom2: GeoJSON da segunda geometria

        Returns:
            ToolResult com geometria da interseção
        """
        if not self._has_shapely:
            return ToolResult.fail("Shapely não instalado")

        try:
            from shapely.geometry import shape

            g1 = shape(geom1)
            g2 = shape(geom2)

            intersection = g1.intersection(g2)

            if intersection.is_empty:
                return ToolResult.ok({
                    "intersects": False,
                    "geometry": None,
                })

            return ToolResult.ok({
                "intersects": True,
                "geometry": intersection.__geo_interface__,
            })
        except Exception as e:
            return ToolResult.fail(f"Erro na interseção: {str(e)}")

    def _nearest(
        self,
        point: Tuple[float, float],
        candidates: List[Tuple[float, float]],
    ) -> ToolResult:
        """
        Encontra o ponto mais próximo de uma lista.

        Args:
            point: (lat, lon) de referência
            candidates: Lista de (lat, lon) candidatos

        Returns:
            ToolResult com ponto mais próximo e distância
        """
        if not candidates:
            return ToolResult.fail("Lista de candidatos vazia")

        min_dist = float("inf")
        nearest = None
        nearest_idx = -1

        for i, candidate in enumerate(candidates):
            result = self._distance(point, candidate)
            if result.success:
                dist = result.data["distance_km"]
                if dist < min_dist:
                    min_dist = dist
                    nearest = candidate
                    nearest_idx = i

        if nearest is None:
            return ToolResult.fail("Não foi possível calcular distâncias")

        return ToolResult.ok({
            "reference": point,
            "nearest": nearest,
            "index": nearest_idx,
            "distance_km": round(min_dist, 3),
        })

"""
Ferramenta de integração com Mapbox API.

Requer:
- MAPBOX_API_KEY no .env
- pip install mapbox (opcional, usa requests se não disponível)
"""

from __future__ import annotations

import os
from typing import Tuple

from src.tools.base import BaseTool, ToolResult, ToolError, register_tool


@register_tool(domain="geo")
class MapboxTool(BaseTool):
    """
    Ferramenta para operações de geolocalização via Mapbox.

    Funcionalidades:
    - Geocoding (endereço -> coordenadas)
    - Reverse geocoding (coordenadas -> endereço)
    - Directions (rotas entre pontos)
    - Isochrone (área alcançável em X minutos)
    """

    name = "mapbox"
    description = "Operações de geolocalização via Mapbox API"
    version = "1.0.0"
    requires_auth = True

    BASE_URL = "https://api.mapbox.com"

    def _setup(self) -> None:
        """Configura a ferramenta."""
        self.api_key = self.config.get("api_key") or os.getenv("MAPBOX_API_KEY")
        if not self.api_key:
            raise ToolError(
                "MAPBOX_API_KEY não configurada",
                tool_name=self.name,
            )
        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """
        Executa uma ação do Mapbox.

        Args:
            action: Ação a executar (geocode, reverse, directions, isochrone)
            **kwargs: Parâmetros da ação

        Returns:
            ToolResult com os dados
        """
        actions = {
            "geocode": self._geocode,
            "reverse": self._reverse_geocode,
            "directions": self._directions,
            "isochrone": self._isochrone,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _geocode(self, address: str) -> ToolResult:
        """
        Converte endereço em coordenadas.

        Args:
            address: Endereço a geocodificar

        Returns:
            ToolResult com lat, lon e detalhes
        """
        try:
            import requests

            url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{address}.json"
            params = {"access_token": self.api_key, "limit": 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("features"):
                return ToolResult.fail("Endereço não encontrado")

            feature = data["features"][0]
            coords = feature["geometry"]["coordinates"]

            return ToolResult.ok({
                "address": address,
                "lat": coords[1],
                "lon": coords[0],
                "place_name": feature.get("place_name"),
                "place_type": feature.get("place_type", []),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no geocoding: {str(e)}")

    def _reverse_geocode(self, lat: float, lon: float) -> ToolResult:
        """
        Converte coordenadas em endereço.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            ToolResult com endereço e detalhes
        """
        try:
            import requests

            url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{lon},{lat}.json"
            params = {"access_token": self.api_key, "limit": 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("features"):
                return ToolResult.fail("Local não encontrado")

            feature = data["features"][0]

            return ToolResult.ok({
                "lat": lat,
                "lon": lon,
                "place_name": feature.get("place_name"),
                "place_type": feature.get("place_type", []),
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no reverse geocoding: {str(e)}")

    def _directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        profile: str = "driving",
    ) -> ToolResult:
        """
        Calcula rota entre dois pontos.

        Args:
            origin: (lat, lon) de origem
            destination: (lat, lon) de destino
            profile: Perfil de rota (driving, walking, cycling)

        Returns:
            ToolResult com rota, distância e duração
        """
        try:
            import requests

            coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            url = f"{self.BASE_URL}/directions/v5/mapbox/{profile}/{coords}"
            params = {
                "access_token": self.api_key,
                "geometries": "geojson",
                "overview": "full",
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not data.get("routes"):
                return ToolResult.fail("Rota não encontrada")

            route = data["routes"][0]

            return ToolResult.ok({
                "origin": origin,
                "destination": destination,
                "profile": profile,
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": round(route["duration"] / 60, 1),
                "geometry": route["geometry"],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no cálculo de rota: {str(e)}")

    def _isochrone(
        self,
        center: Tuple[float, float],
        minutes: int = 15,
        profile: str = "driving",
    ) -> ToolResult:
        """
        Calcula área alcançável a partir de um ponto.

        Args:
            center: (lat, lon) do centro
            minutes: Tempo em minutos
            profile: Perfil (driving, walking, cycling)

        Returns:
            ToolResult com polígono da área
        """
        try:
            import requests

            coords = f"{center[1]},{center[0]}"
            url = f"{self.BASE_URL}/isochrone/v1/mapbox/{profile}/{coords}"
            params = {
                "access_token": self.api_key,
                "contours_minutes": minutes,
                "polygons": "true",
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not data.get("features"):
                return ToolResult.fail("Isócrona não calculada")

            feature = data["features"][0]

            return ToolResult.ok({
                "center": center,
                "minutes": minutes,
                "profile": profile,
                "geometry": feature["geometry"],
            })
        except Exception as e:
            return ToolResult.fail(f"Erro no cálculo de isócrona: {str(e)}")

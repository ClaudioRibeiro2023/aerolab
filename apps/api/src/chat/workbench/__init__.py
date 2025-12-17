"""
Workbench - Sistema de Artifacts e Canvas.

Similar ao Claude Artifacts e ChatGPT Canvas.
Permite criar e editar conteúdo rico em tempo real.
"""

from .artifacts import Artifact, ArtifactType, ArtifactManager
from .canvas import Canvas, CanvasElement

__all__ = [
    "Artifact",
    "ArtifactType", 
    "ArtifactManager",
    "Canvas",
    "CanvasElement",
]

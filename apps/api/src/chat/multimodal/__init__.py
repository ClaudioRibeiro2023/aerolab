"""
Multimodal - Suporte a múltiplos tipos de mídia.

Suporta:
- Imagens (upload, visualização, geração)
- Áudio (voz, transcrição)
- Vídeo
- Arquivos
"""

from .images import ImageProcessor, ImageAnalyzer
from .audio import AudioProcessor, VoiceMode
from .files import FileHandler

__all__ = [
    "ImageProcessor",
    "ImageAnalyzer",
    "AudioProcessor",
    "VoiceMode",
    "FileHandler",
]

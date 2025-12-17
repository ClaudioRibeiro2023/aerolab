"""
Image Processing - Processamento e análise de imagens.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import base64
import uuid
import logging

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Formatos de imagem suportados."""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
    SVG = "svg"


@dataclass
class ProcessedImage:
    """Imagem processada."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str = ""
    format: ImageFormat = ImageFormat.PNG
    width: int = 0
    height: int = 0
    size_bytes: int = 0
    
    # URLs
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Base64 (para inline)
    base64_data: Optional[str] = None
    
    # Análise
    description: Optional[str] = None
    detected_objects: List[str] = field(default_factory=list)
    ocr_text: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "original_name": self.original_name,
            "format": self.format.value,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "description": self.description,
            "detected_objects": self.detected_objects,
            "ocr_text": self.ocr_text
        }
    
    def to_openai_format(self) -> Dict:
        """Formato para API OpenAI (vision)."""
        if self.url:
            return {
                "type": "image_url",
                "image_url": {"url": self.url}
            }
        elif self.base64_data:
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{self.format.value};base64,{self.base64_data}"
                }
            }
        return {}


class ImageProcessor:
    """
    Processador de imagens.
    
    Funcionalidades:
    - Upload e validação
    - Redimensionamento
    - Conversão de formato
    - Geração de thumbnails
    """
    
    MAX_SIZE_MB = 20
    MAX_DIMENSION = 4096
    THUMBNAIL_SIZE = 200
    
    async def process(
        self,
        image_data: bytes,
        filename: str,
        generate_thumbnail: bool = True
    ) -> ProcessedImage:
        """Processa uma imagem."""
        # Detectar formato
        format = self._detect_format(image_data, filename)
        
        # Validar tamanho
        size_bytes = len(image_data)
        if size_bytes > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Image too large: {size_bytes / 1024 / 1024:.1f}MB")
        
        # Criar resultado
        result = ProcessedImage(
            original_name=filename,
            format=format,
            size_bytes=size_bytes,
            base64_data=base64.b64encode(image_data).decode()
        )
        
        # Em produção: obter dimensões, gerar thumbnail, fazer upload
        # Por agora, placeholder
        result.width = 800
        result.height = 600
        
        return result
    
    def _detect_format(self, data: bytes, filename: str) -> ImageFormat:
        """Detecta formato da imagem."""
        # Por magic bytes
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return ImageFormat.PNG
        if data[:2] == b'\xff\xd8':
            return ImageFormat.JPEG
        if data[:6] in (b'GIF87a', b'GIF89a'):
            return ImageFormat.GIF
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return ImageFormat.WEBP
        
        # Por extensão
        ext = filename.split('.')[-1].lower()
        format_map = {
            'jpg': ImageFormat.JPEG,
            'jpeg': ImageFormat.JPEG,
            'png': ImageFormat.PNG,
            'gif': ImageFormat.GIF,
            'webp': ImageFormat.WEBP,
            'svg': ImageFormat.SVG
        }
        return format_map.get(ext, ImageFormat.PNG)


class ImageAnalyzer:
    """
    Analisador de imagens com vision models.
    """
    
    async def analyze(
        self,
        image: ProcessedImage,
        prompt: str = "Describe this image in detail."
    ) -> str:
        """Analisa uma imagem usando vision model."""
        # Em produção: chamar GPT-4V, Claude, etc.
        return f"[Image analysis placeholder for: {image.original_name}]"
    
    async def extract_text(self, image: ProcessedImage) -> str:
        """Extrai texto de uma imagem (OCR)."""
        # Em produção: usar OCR
        return ""
    
    async def detect_objects(self, image: ProcessedImage) -> List[str]:
        """Detecta objetos em uma imagem."""
        # Em produção: usar object detection
        return []


class ImageGenerator:
    """
    Gerador de imagens com AI.
    """
    
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "natural"
    ) -> ProcessedImage:
        """Gera uma imagem a partir de prompt."""
        # Em produção: usar DALL-E, Stability AI, etc.
        return ProcessedImage(
            original_name=f"generated_{uuid.uuid4().hex[:8]}.png",
            format=ImageFormat.PNG,
            description=prompt
        )


# Singletons
_image_processor: Optional[ImageProcessor] = None
_image_analyzer: Optional[ImageAnalyzer] = None


def get_image_processor() -> ImageProcessor:
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor


def get_image_analyzer() -> ImageAnalyzer:
    global _image_analyzer
    if _image_analyzer is None:
        _image_analyzer = ImageAnalyzer()
    return _image_analyzer

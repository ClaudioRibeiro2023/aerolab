"""
File Handler - Processamento de arquivos diversos.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
import mimetypes
import logging

logger = logging.getLogger(__name__)


class FileCategory(str, Enum):
    """Categorias de arquivos."""
    DOCUMENT = "document"  # PDF, DOC, TXT
    SPREADSHEET = "spreadsheet"  # XLS, CSV
    PRESENTATION = "presentation"  # PPT
    CODE = "code"  # Source files
    DATA = "data"  # JSON, XML, YAML
    ARCHIVE = "archive"  # ZIP, TAR
    OTHER = "other"


@dataclass
class ProcessedFile:
    """Arquivo processado."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    mime_type: str = ""
    category: FileCategory = FileCategory.OTHER
    size_bytes: int = 0
    
    # URLs
    url: Optional[str] = None
    
    # Conteúdo extraído
    extracted_text: Optional[str] = None
    preview_html: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "mime_type": self.mime_type,
            "category": self.category.value,
            "size_bytes": self.size_bytes,
            "url": self.url,
            "has_text": self.extracted_text is not None,
            "has_preview": self.preview_html is not None,
            "metadata": self.metadata
        }


class FileHandler:
    """
    Handler de arquivos.
    
    Processa diversos tipos de arquivos para uso no chat.
    """
    
    MAX_SIZE_MB = 100
    
    # Extensões por categoria
    CATEGORY_MAP = {
        FileCategory.DOCUMENT: ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        FileCategory.SPREADSHEET: ['.xls', '.xlsx', '.csv', '.tsv', '.ods'],
        FileCategory.PRESENTATION: ['.ppt', '.pptx', '.odp'],
        FileCategory.CODE: ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'],
        FileCategory.DATA: ['.json', '.xml', '.yaml', '.yml', '.toml'],
        FileCategory.ARCHIVE: ['.zip', '.tar', '.gz', '.rar', '.7z']
    }
    
    async def process(
        self,
        file_data: bytes,
        filename: str,
        extract_text: bool = True
    ) -> ProcessedFile:
        """Processa um arquivo."""
        # Detectar tipo
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        category = self._detect_category(filename)
        
        # Validar tamanho
        size_bytes = len(file_data)
        if size_bytes > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large: {size_bytes / 1024 / 1024:.1f}MB")
        
        result = ProcessedFile(
            name=filename,
            mime_type=mime_type,
            category=category,
            size_bytes=size_bytes
        )
        
        # Extrair texto se aplicável
        if extract_text:
            result.extracted_text = await self._extract_text(file_data, filename, category)
        
        return result
    
    def _detect_category(self, filename: str) -> FileCategory:
        """Detecta categoria do arquivo."""
        ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        for category, extensions in self.CATEGORY_MAP.items():
            if ext in extensions:
                return category
        
        return FileCategory.OTHER
    
    async def _extract_text(
        self,
        data: bytes,
        filename: str,
        category: FileCategory
    ) -> Optional[str]:
        """Extrai texto do arquivo."""
        if category == FileCategory.CODE:
            # Código: decodificar diretamente
            try:
                return data.decode('utf-8')
            except:
                return data.decode('latin-1', errors='ignore')
        
        elif category == FileCategory.DATA:
            # Dados estruturados
            try:
                return data.decode('utf-8')
            except:
                return None
        
        elif category == FileCategory.DOCUMENT:
            # Documentos: em produção usar PyPDF2, python-docx, etc.
            if filename.endswith('.txt'):
                try:
                    return data.decode('utf-8')
                except:
                    return data.decode('latin-1', errors='ignore')
            # PDF, DOCX: placeholder
            return "[Document text extraction not implemented]"
        
        elif category == FileCategory.SPREADSHEET:
            # Planilhas: em produção usar pandas, openpyxl
            if filename.endswith('.csv'):
                try:
                    return data.decode('utf-8')
                except:
                    return data.decode('latin-1', errors='ignore')
            return "[Spreadsheet text extraction not implemented]"
        
        return None
    
    async def get_preview(self, file: ProcessedFile) -> Optional[str]:
        """Gera preview HTML do arquivo."""
        if file.category == FileCategory.CODE and file.extracted_text:
            # Preview de código com syntax highlighting
            return f"<pre><code>{file.extracted_text[:5000]}</code></pre>"
        
        return None


# Singleton
_file_handler: Optional[FileHandler] = None


def get_file_handler() -> FileHandler:
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler

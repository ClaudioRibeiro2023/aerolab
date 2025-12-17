"""
Sistema de logging configurável
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import get_settings


def setup_logger(
    name: str = "agno_app",
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configura e retorna um logger
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Arquivo para salvar logs (opcional)
    
    Returns:
        Logger configurado
    """
    settings = get_settings()
    level = level or settings.LOG_LEVEL
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "agno_app") -> logging.Logger:
    """
    Retorna um logger existente ou cria um novo
    
    Args:
        name: Nome do logger
    
    Returns:
        Logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

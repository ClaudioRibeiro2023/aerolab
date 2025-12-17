"""
Módulo de persistência - PostgreSQL, Redis e Backup.
"""

from .postgres import PostgresStore, get_postgres_store
from .redis_cache import RedisCache, get_redis_cache
from .backup import BackupManager, BackupMetadata, get_backup_manager

__all__ = [
    # PostgreSQL
    "PostgresStore",
    "get_postgres_store",
    # Redis
    "RedisCache",
    "get_redis_cache",
    # Backup
    "BackupManager",
    "BackupMetadata",
    "get_backup_manager",
]

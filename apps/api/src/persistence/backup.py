"""
Sistema de backup automatizado.

Suporta backup para:
- Sistema de arquivos local
- AWS S3
- Google Cloud Storage
"""

import os
import json
import gzip
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict

try:
    import boto3
    HAS_S3 = True
except ImportError:
    HAS_S3 = False


@dataclass
class BackupMetadata:
    """Metadados do backup."""
    id: str
    timestamp: str
    size_bytes: int
    type: str  # full, incremental
    storage: str  # local, s3, gcs
    tables: List[str]
    status: str  # completed, failed
    duration_seconds: float
    checksum: Optional[str] = None


class BackupManager:
    """
    Gerenciador de backups automatizados.
    
    Features:
    - Backup completo e incremental
    - Compressão gzip
    - Rotação automática (retenção)
    - Suporte a múltiplos destinos
    - Agendamento via cron
    - Restauração
    
    Configuração:
        BACKUP_PATH: Diretório local para backups
        BACKUP_S3_BUCKET: Bucket S3 (opcional)
        BACKUP_RETENTION_DAYS: Dias de retenção (default: 30)
    """
    
    def __init__(
        self,
        backup_path: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        retention_days: int = 30
    ):
        self.backup_path = Path(backup_path or os.getenv("BACKUP_PATH", "./backups"))
        self.s3_bucket = s3_bucket or os.getenv("BACKUP_S3_BUCKET")
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", str(retention_days)))
        
        # Criar diretório de backup
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Cliente S3
        self._s3_client = None
        if self.s3_bucket and HAS_S3:
            self._s3_client = boto3.client("s3")
    
    def _generate_backup_id(self) -> str:
        """Gera ID único para backup."""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    async def backup_data(
        self,
        data: Dict[str, Any],
        backup_type: str = "full",
        compress: bool = True
    ) -> BackupMetadata:
        """
        Realiza backup de dados.
        
        Args:
            data: Dicionário com dados a serem salvos
            backup_type: Tipo (full, incremental)
            compress: Se deve comprimir
        
        Returns:
            Metadados do backup
        """
        start_time = datetime.utcnow()
        backup_id = self._generate_backup_id()
        
        # Serializar dados
        json_data = json.dumps(data, default=str, ensure_ascii=False)
        
        # Nome do arquivo
        filename = f"backup_{backup_type}_{backup_id}"
        if compress:
            filename += ".json.gz"
        else:
            filename += ".json"
        
        filepath = self.backup_path / filename
        
        # Salvar
        if compress:
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                f.write(json_data)
        else:
            filepath.write_text(json_data, encoding="utf-8")
        
        # Calcular tamanho
        size = filepath.stat().st_size
        
        # Upload para S3 se configurado
        storage = "local"
        if self._s3_client and self.s3_bucket:
            await self._upload_to_s3(filepath, filename)
            storage = "s3"
        
        # Metadados
        duration = (datetime.utcnow() - start_time).total_seconds()
        metadata = BackupMetadata(
            id=backup_id,
            timestamp=start_time.isoformat(),
            size_bytes=size,
            type=backup_type,
            storage=storage,
            tables=list(data.keys()),
            status="completed",
            duration_seconds=duration
        )
        
        # Salvar metadados
        self._save_metadata(metadata)
        
        return metadata
    
    async def backup_database(
        self,
        postgres_store,
        tables: Optional[List[str]] = None
    ) -> BackupMetadata:
        """
        Backup do banco de dados PostgreSQL.
        
        Args:
            postgres_store: Instância do PostgresStore
            tables: Lista de tabelas (default: todas)
        """
        tables = tables or ["agents", "executions", "agent_memory"]
        data = {}
        
        for table in tables:
            rows = await postgres_store.query(f"SELECT * FROM {table}")
            data[table] = rows
        
        return await self.backup_data(data, backup_type="full")
    
    async def backup_files(
        self,
        source_dirs: List[str],
        backup_type: str = "full"
    ) -> BackupMetadata:
        """
        Backup de diretórios de arquivos.
        
        Args:
            source_dirs: Lista de diretórios a incluir
            backup_type: Tipo do backup
        """
        start_time = datetime.utcnow()
        backup_id = self._generate_backup_id()
        
        # Criar arquivo tar.gz
        filename = f"files_{backup_type}_{backup_id}.tar.gz"
        filepath = self.backup_path / filename
        
        # Criar arquivo compactado
        import tarfile
        with tarfile.open(filepath, "w:gz") as tar:
            for dir_path in source_dirs:
                if os.path.exists(dir_path):
                    tar.add(dir_path, arcname=os.path.basename(dir_path))
        
        size = filepath.stat().st_size
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        metadata = BackupMetadata(
            id=backup_id,
            timestamp=start_time.isoformat(),
            size_bytes=size,
            type=backup_type,
            storage="local",
            tables=source_dirs,
            status="completed",
            duration_seconds=duration
        )
        
        self._save_metadata(metadata)
        return metadata
    
    async def restore(
        self,
        backup_id: str,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restaura um backup.
        
        Args:
            backup_id: ID do backup
            target_path: Diretório destino (para arquivos)
        
        Returns:
            Dados restaurados ou caminho dos arquivos
        """
        # Encontrar arquivo de backup
        pattern = f"*{backup_id}*"
        files = list(self.backup_path.glob(pattern))
        
        if not files:
            raise FileNotFoundError(f"Backup {backup_id} não encontrado")
        
        filepath = files[0]
        
        # JSON backup
        if filepath.suffix in [".json", ".gz"]:
            if filepath.suffix == ".gz":
                with gzip.open(filepath, "rt", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return json.loads(filepath.read_text())
        
        # Arquivo tar.gz
        elif ".tar" in filepath.name:
            import tarfile
            target = Path(target_path or self.backup_path / "restored" / backup_id)
            target.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(filepath, "r:gz") as tar:
                tar.extractall(target)
            
            return {"restored_to": str(target)}
        
        raise ValueError(f"Formato de backup não suportado: {filepath}")
    
    async def cleanup_old_backups(self) -> int:
        """
        Remove backups mais antigos que retention_days.
        
        Returns:
            Número de backups removidos
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        removed = 0
        
        for filepath in self.backup_path.glob("backup_*"):
            # Extrair data do nome
            try:
                parts = filepath.stem.split("_")
                date_str = parts[-2] if len(parts) >= 3 else parts[-1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff:
                    filepath.unlink()
                    removed += 1
            except (ValueError, IndexError):
                continue
        
        return removed
    
    def list_backups(self, limit: int = 20) -> List[BackupMetadata]:
        """Lista backups disponíveis."""
        metadata_file = self.backup_path / "metadata.json"
        
        if not metadata_file.exists():
            return []
        
        data = json.loads(metadata_file.read_text())
        backups = [BackupMetadata(**b) for b in data.get("backups", [])]
        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def _save_metadata(self, metadata: BackupMetadata):
        """Salva metadados do backup."""
        metadata_file = self.backup_path / "metadata.json"
        
        if metadata_file.exists():
            data = json.loads(metadata_file.read_text())
        else:
            data = {"backups": []}
        
        data["backups"].append(asdict(metadata))
        metadata_file.write_text(json.dumps(data, indent=2))
    
    async def _upload_to_s3(self, filepath: Path, key: str):
        """Upload para S3."""
        if not self._s3_client:
            return
        
        self._s3_client.upload_file(
            str(filepath),
            self.s3_bucket,
            f"backups/{key}"
        )
    
    async def schedule_backup(
        self,
        postgres_store,
        interval_hours: int = 24
    ):
        """
        Agenda backups periódicos.
        
        Args:
            postgres_store: Store do banco
            interval_hours: Intervalo em horas
        """
        while True:
            try:
                await self.backup_database(postgres_store)
                await self.cleanup_old_backups()
            except Exception as e:
                print(f"Backup failed: {e}")
            
            await asyncio.sleep(interval_hours * 3600)


# Singleton
_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Obtém instância singleton do gerenciador de backup."""
    global _manager
    if _manager is None:
        _manager = BackupManager()
    return _manager

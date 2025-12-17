"""Fetcher para download de URLs e arquivos."""

import httpx
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import logging
import tempfile

from ..models import SourceRef

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_SIZE = 50 * 1024 * 1024  # 50MB


class FetcherError(Exception):
    """Erro genérico do fetcher."""
    pass


class RawDocumentRef:
    """Referência a documento baixado."""

    def __init__(
        self,
        url: str,
        local_path: Path | None,
        content_hash: str,
        content_type: str | None,
        size_bytes: int,
        fetched_at: datetime,
    ):
        self.url = url
        self.local_path = local_path
        self.content_hash = content_hash
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.fetched_at = fetched_at

    def to_source_ref(self) -> SourceRef:
        return SourceRef(
            source="fetcher",
            url=self.url,
            fetched_at=self.fetched_at,
            content_hash=self.content_hash,
        )


class Fetcher:
    """Fetcher assíncrono para URLs e arquivos."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_size: int = DEFAULT_MAX_SIZE,
        cache_dir: Path | None = None,
    ):
        self.timeout = timeout
        self.max_size = max_size
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "licitacoes_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "AeroLab-Licitacoes/0.1",
                "Accept": "*/*",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise FetcherError("Fetcher not initialized. Use 'async with Fetcher()' context.")
        return self._client

    async def fetch_url(self, url: str) -> str:
        """
        Busca conteúdo de uma URL (HTML/texto).

        Args:
            url: URL para buscar

        Returns:
            Conteúdo como string

        Raises:
            FetcherError: Se falhar
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            content_length = int(response.headers.get("content-length", 0))
            if content_length > self.max_size:
                raise FetcherError(f"Content too large: {content_length} bytes (max: {self.max_size})")

            return response.text

        except httpx.TimeoutException as e:
            raise FetcherError(f"Timeout fetching {url}") from e
        except httpx.HTTPStatusError as e:
            raise FetcherError(f"HTTP error {e.response.status_code} for {url}") from e
        except httpx.RequestError as e:
            raise FetcherError(f"Request error for {url}: {e}") from e

    async def download_file(
        self,
        url: str,
        filename: str | None = None,
    ) -> RawDocumentRef:
        """
        Baixa arquivo e salva no cache.

        Args:
            url: URL do arquivo
            filename: Nome do arquivo (opcional, extraído da URL se não fornecido)

        Returns:
            RawDocumentRef com informações do arquivo

        Raises:
            FetcherError: Se falhar
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            content_length = int(response.headers.get("content-length", len(response.content)))
            if content_length > self.max_size:
                raise FetcherError(f"File too large: {content_length} bytes (max: {self.max_size})")

            content = response.content
            content_hash = hashlib.sha256(content).hexdigest()
            content_type = response.headers.get("content-type")

            if not filename:
                filename = url.split("/")[-1].split("?")[0] or f"file_{content_hash[:8]}"

            local_path = self.cache_dir / f"{content_hash[:16]}_{filename}"

            with open(local_path, "wb") as f:
                f.write(content)

            return RawDocumentRef(
                url=url,
                local_path=local_path,
                content_hash=content_hash,
                content_type=content_type,
                size_bytes=len(content),
                fetched_at=datetime.now(timezone.utc),
            )

        except httpx.TimeoutException as e:
            raise FetcherError(f"Timeout downloading {url}") from e
        except httpx.HTTPStatusError as e:
            raise FetcherError(f"HTTP error {e.response.status_code} downloading {url}") from e
        except httpx.RequestError as e:
            raise FetcherError(f"Request error downloading {url}: {e}") from e
        except IOError as e:
            raise FetcherError(f"IO error saving file from {url}: {e}") from e

    def get_cached_path(self, content_hash: str) -> Path | None:
        """Busca arquivo no cache pelo hash."""
        for path in self.cache_dir.glob(f"{content_hash[:16]}_*"):
            if path.is_file():
                return path
        return None

    def clear_cache(self) -> int:
        """Limpa cache e retorna número de arquivos removidos."""
        count = 0
        for path in self.cache_dir.iterdir():
            if path.is_file():
                path.unlink()
                count += 1
        return count


async def create_fetcher(cache_dir: Path | None = None) -> Fetcher:
    """Factory function para criar Fetcher."""
    return Fetcher(cache_dir=cache_dir)

"""Agente Watcher — Coleta, normalização, dedup e diff de licitações."""

from datetime import datetime, timezone
from typing import Any
from dataclasses import dataclass
import logging

from ..models import (
    LicitacaoItem,
    ChangeEvent,
    FlowConfig,
    SourceRef,
)
from ..tools import PNCPClient
from ..services import dedup_strong, detect_changes_batch

logger = logging.getLogger(__name__)


@dataclass
class WatcherResult:
    """Resultado da execução do Watcher."""

    items: list[LicitacaoItem]
    changes: list[ChangeEvent]
    new_items: list[LicitacaoItem]
    errors: list[str]
    fetched_at: datetime

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def total_new(self) -> int:
        return len(self.new_items)

    @property
    def total_changes(self) -> int:
        return len(self.changes)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class WatcherAgent:
    """
    Agente responsável por coletar e monitorar licitações.

    Responsabilidades:
    - Buscar licitações em fontes configuradas (PNCP)
    - Normalizar dados para schema canônico
    - Deduplicar itens
    - Detectar mudanças em relação a execuções anteriores

    Restrições:
    - NÃO interpreta conteúdo jurídico
    - NÃO faz triagem ou priorização
    - NÃO baixa anexos automaticamente (só lista)
    """

    def __init__(self, config: FlowConfig | None = None):
        self.config = config or FlowConfig()

    async def search(
        self,
        existing_items: list[LicitacaoItem] | None = None,
    ) -> WatcherResult:
        """
        Executa busca de licitações e retorna resultado normalizado.

        Args:
            existing_items: Itens já conhecidos (para detectar mudanças)

        Returns:
            WatcherResult com itens, mudanças e erros
        """
        errors: list[str] = []
        all_items: list[LicitacaoItem] = []
        fetched_at = datetime.now(timezone.utc)

        try:
            async with PNCPClient() as client:
                items = await client.search(
                    keywords=self.config.keywords,
                    ufs=self.config.ufs if self.config.ufs else None,
                    modalidades=self.config.modalidades if self.config.modalidades else None,
                )
                all_items.extend(items)
                logger.info(f"PNCP returned {len(items)} items")

        except Exception as e:
            error_msg = f"PNCP search failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        items_deduped = dedup_strong(all_items)
        logger.info(f"After dedup: {len(items_deduped)} items")

        changes: list[ChangeEvent] = []
        new_items: list[LicitacaoItem] = []

        if existing_items:
            existing_ids = {item.external_id for item in existing_items}
            new_items = [item for item in items_deduped if item.external_id not in existing_ids]
            changes = detect_changes_batch(existing_items, items_deduped)
            logger.info(f"Detected {len(new_items)} new items, {len(changes)} changes")
        else:
            new_items = items_deduped

        return WatcherResult(
            items=items_deduped,
            changes=changes,
            new_items=new_items,
            errors=errors,
            fetched_at=fetched_at,
        )

    async def get_detail(self, external_id: str) -> LicitacaoItem | None:
        """
        Obtém detalhes de uma licitação específica.

        Args:
            external_id: ID externo da licitação

        Returns:
            LicitacaoItem ou None se não encontrado
        """
        try:
            async with PNCPClient() as client:
                item = await client.get_detail(external_id)
                if item:
                    logger.info(f"Got detail for {external_id}")
                else:
                    logger.warning(f"Item not found: {external_id}")
                return item

        except Exception as e:
            logger.error(f"Failed to get detail for {external_id}: {e}")
            return None

    async def list_attachments(self, external_id: str) -> list[dict[str, Any]]:
        """
        Lista anexos de uma licitação.

        Args:
            external_id: ID externo da licitação

        Returns:
            Lista de referências de anexos
        """
        try:
            async with PNCPClient() as client:
                attachments = await client.list_attachments(external_id)
                logger.info(f"Found {len(attachments)} attachments for {external_id}")
                return [
                    {
                        "filename": a.filename,
                        "url": a.url,
                        "size_bytes": a.size_bytes,
                        "content_type": a.content_type,
                    }
                    for a in attachments
                ]

        except Exception as e:
            logger.error(f"Failed to list attachments for {external_id}: {e}")
            return []


async def create_watcher_agent(config: FlowConfig | None = None) -> WatcherAgent:
    """Factory function para criar WatcherAgent."""
    return WatcherAgent(config=config)

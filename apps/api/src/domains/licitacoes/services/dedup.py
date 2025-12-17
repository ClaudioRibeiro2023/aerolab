"""Serviço de deduplicação de licitações."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import logging

from ..models import LicitacaoItem

logger = logging.getLogger(__name__)


@dataclass
class DuplicateSuggestion:
    """Sugestão de item duplicado (dedup fraco)."""

    original_id: str
    duplicate_id: str
    similarity_score: float
    reason: str


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparação."""
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _compute_item_hash(item: LicitacaoItem) -> str:
    """Computa hash normalizado de um item para dedup forte."""
    key = f"{item.source}:{item.external_id}"
    return hashlib.sha256(key.encode()).hexdigest()


def _compute_fuzzy_hash(item: LicitacaoItem) -> str:
    """Computa hash fuzzy para dedup fraco."""
    normalized = _normalize_text(item.objeto)
    key = f"{item.orgao}:{item.uf}:{normalized[:100]}"
    return hashlib.md5(key.encode()).hexdigest()


def dedup_strong(items: list[LicitacaoItem]) -> list[LicitacaoItem]:
    """
    Deduplicação forte: remove duplicatas exatas por source + external_id.

    Args:
        items: Lista de LicitacaoItem

    Returns:
        Lista sem duplicatas exatas
    """
    seen: dict[str, LicitacaoItem] = {}
    result: list[LicitacaoItem] = []

    for item in items:
        item_hash = _compute_item_hash(item)

        if item_hash not in seen:
            seen[item_hash] = item
            result.append(item)
        else:
            existing = seen[item_hash]
            if item.updated_at > existing.updated_at:
                idx = result.index(existing)
                result[idx] = item
                seen[item_hash] = item
                logger.debug(f"Replaced older duplicate: {item.external_id}")

    removed = len(items) - len(result)
    if removed > 0:
        logger.info(f"Dedup strong: removed {removed} duplicates from {len(items)} items")

    return result


def dedup_fuzzy(items: list[LicitacaoItem]) -> list[DuplicateSuggestion]:
    """
    Deduplicação fraca: identifica possíveis duplicatas por similaridade.

    NUNCA descarta automaticamente. Apenas sugere para revisão humana.

    Args:
        items: Lista de LicitacaoItem

    Returns:
        Lista de DuplicateSuggestion para revisão
    """
    suggestions: list[DuplicateSuggestion] = []
    fuzzy_hashes: dict[str, list[LicitacaoItem]] = {}

    for item in items:
        fuzzy_hash = _compute_fuzzy_hash(item)

        if fuzzy_hash in fuzzy_hashes:
            for existing in fuzzy_hashes[fuzzy_hash]:
                if existing.external_id != item.external_id:
                    suggestions.append(
                        DuplicateSuggestion(
                            original_id=existing.external_id,
                            duplicate_id=item.external_id,
                            similarity_score=0.9,
                            reason="Mesmo órgão, UF e objeto similar",
                        )
                    )
            fuzzy_hashes[fuzzy_hash].append(item)
        else:
            fuzzy_hashes[fuzzy_hash] = [item]

    if suggestions:
        logger.info(f"Dedup fuzzy: found {len(suggestions)} potential duplicates")

    return suggestions


def merge_items(
    existing: list[LicitacaoItem],
    new_items: list[LicitacaoItem],
) -> tuple[list[LicitacaoItem], list[LicitacaoItem], list[LicitacaoItem]]:
    """
    Mescla novos itens com existentes.

    Args:
        existing: Itens já conhecidos
        new_items: Novos itens coletados

    Returns:
        Tupla: (todos_itens, apenas_novos, atualizados)
    """
    existing_map = {_compute_item_hash(item): item for item in existing}
    all_items: list[LicitacaoItem] = list(existing)
    only_new: list[LicitacaoItem] = []
    updated: list[LicitacaoItem] = []

    for item in new_items:
        item_hash = _compute_item_hash(item)

        if item_hash not in existing_map:
            all_items.append(item)
            only_new.append(item)
        else:
            existing_item = existing_map[item_hash]
            if item.updated_at > existing_item.updated_at:
                idx = all_items.index(existing_item)
                all_items[idx] = item
                updated.append(item)

    logger.info(f"Merge: {len(only_new)} new, {len(updated)} updated, {len(all_items)} total")

    return all_items, only_new, updated

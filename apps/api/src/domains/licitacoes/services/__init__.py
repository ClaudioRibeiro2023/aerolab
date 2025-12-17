# Licitacoes Services
from .dedup import dedup_strong, dedup_fuzzy, merge_items, DuplicateSuggestion
from .diff import detect_changes, detect_changes_batch

__all__ = [
    "dedup_strong",
    "dedup_fuzzy",
    "merge_items",
    "DuplicateSuggestion",
    "detect_changes",
    "detect_changes_batch",
]

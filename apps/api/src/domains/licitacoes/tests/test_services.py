"""Testes dos services do Núcleo Licitações."""

import pytest
from datetime import datetime, timezone

from ..models import (
    LicitacaoItem,
    SourceRef,
    AttachmentRef,
    Situacao,
    TipoMudanca,
)
from ..services import (
    dedup_strong,
    dedup_fuzzy,
    merge_items,
    detect_changes,
    detect_changes_batch,
)


def make_item(
    external_id: str,
    objeto: str = "Aquisição de drones",
    orgao: str = "Prefeitura",
    uf: str = "SP",
    **kwargs,
) -> LicitacaoItem:
    """Helper para criar LicitacaoItem de teste."""
    return LicitacaoItem(
        external_id=external_id,
        source="pncp",
        objeto=objeto,
        orgao=orgao,
        uf=uf,
        sources=[SourceRef(source="pncp", url=f"https://pncp.gov.br/{external_id}")],
        **kwargs,
    )


class TestDedupStrong:
    """Testes para dedup_strong."""

    def test_no_duplicates(self):
        items = [
            make_item("001"),
            make_item("002"),
            make_item("003"),
        ]
        result = dedup_strong(items)
        assert len(result) == 3

    def test_removes_exact_duplicates(self):
        items = [
            make_item("001"),
            make_item("001"),  # Duplicata
            make_item("002"),
        ]
        result = dedup_strong(items)
        assert len(result) == 2
        assert {item.external_id for item in result} == {"001", "002"}

    def test_keeps_newer_version(self):
        old_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        new_time = datetime(2025, 1, 2, tzinfo=timezone.utc)

        items = [
            make_item("001", objeto="Versão antiga", updated_at=old_time),
            make_item("001", objeto="Versão nova", updated_at=new_time),
        ]
        result = dedup_strong(items)
        assert len(result) == 1
        assert result[0].objeto == "Versão nova"

    def test_empty_list(self):
        result = dedup_strong([])
        assert result == []


class TestDedupFuzzy:
    """Testes para dedup_fuzzy."""

    def test_no_suggestions_for_different_items(self):
        items = [
            make_item("001", objeto="Compra de computadores", orgao="Prefeitura A", uf="SP"),
            make_item("002", objeto="Serviços de limpeza", orgao="Prefeitura B", uf="RJ"),
        ]
        suggestions = dedup_fuzzy(items)
        assert len(suggestions) == 0

    def test_suggests_similar_items(self):
        items = [
            make_item("001", objeto="Aquisição de drones para combate", orgao="Prefeitura", uf="SP"),
            make_item("002", objeto="Aquisição de drones para combate", orgao="Prefeitura", uf="SP"),
        ]
        suggestions = dedup_fuzzy(items)
        assert len(suggestions) == 1
        assert suggestions[0].original_id == "001"
        assert suggestions[0].duplicate_id == "002"


class TestMergeItems:
    """Testes para merge_items."""

    def test_merge_new_items(self):
        existing = [make_item("001")]
        new_items = [make_item("002"), make_item("003")]

        all_items, only_new, updated = merge_items(existing, new_items)

        assert len(all_items) == 3
        assert len(only_new) == 2
        assert len(updated) == 0

    def test_merge_updated_item(self):
        old_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        new_time = datetime(2025, 1, 2, tzinfo=timezone.utc)

        existing = [make_item("001", objeto="Versão antiga", updated_at=old_time)]
        new_items = [make_item("001", objeto="Versão nova", updated_at=new_time)]

        all_items, only_new, updated = merge_items(existing, new_items)

        assert len(all_items) == 1
        assert len(only_new) == 0
        assert len(updated) == 1
        assert all_items[0].objeto == "Versão nova"


class TestDetectChanges:
    """Testes para detect_changes."""

    def test_no_changes(self):
        item = make_item("001")
        changes = detect_changes(item, item)
        assert len(changes) == 0

    def test_detect_deadline_change(self):
        old_item = make_item("001", data_abertura=datetime(2025, 1, 15, tzinfo=timezone.utc))
        new_item = make_item("001", data_abertura=datetime(2025, 1, 20, tzinfo=timezone.utc))

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 1
        assert changes[0].tipo == TipoMudanca.PRAZO_ALTERADO
        assert changes[0].campo == "data_abertura"

    def test_detect_status_change(self):
        old_item = make_item("001", situacao=Situacao.ABERTA)
        new_item = make_item("001", situacao=Situacao.ENCERRADA)

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 1
        assert changes[0].tipo == TipoMudanca.STATUS_ALTERADO
        assert changes[0].valor_anterior == "aberta"
        assert changes[0].valor_novo == "encerrada"

    def test_detect_value_change(self):
        old_item = make_item("001", valor_estimado=100000.0)
        new_item = make_item("001", valor_estimado=150000.0)

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 1
        assert changes[0].tipo == TipoMudanca.VALOR_ALTERADO

    def test_detect_attachment_added(self):
        old_item = make_item("001", anexos=[])
        new_item = make_item(
            "001",
            anexos=[AttachmentRef(filename="edital.pdf", url="https://example.com/edital.pdf")],
        )

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 1
        assert changes[0].tipo == TipoMudanca.ANEXO_ADICIONADO
        assert changes[0].valor_novo == "edital.pdf"

    def test_detect_attachment_removed(self):
        old_item = make_item(
            "001",
            anexos=[AttachmentRef(filename="edital.pdf", url="https://example.com/edital.pdf")],
        )
        new_item = make_item("001", anexos=[])

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 1
        assert changes[0].tipo == TipoMudanca.ANEXO_REMOVIDO
        assert changes[0].valor_anterior == "edital.pdf"

    def test_detect_multiple_changes(self):
        old_item = make_item(
            "001",
            situacao=Situacao.ABERTA,
            valor_estimado=100000.0,
        )
        new_item = make_item(
            "001",
            situacao=Situacao.SUSPENSA,
            valor_estimado=120000.0,
        )

        changes = detect_changes(old_item, new_item)

        assert len(changes) == 2
        tipos = {c.tipo for c in changes}
        assert TipoMudanca.STATUS_ALTERADO in tipos
        assert TipoMudanca.VALOR_ALTERADO in tipos


class TestDetectChangesBatch:
    """Testes para detect_changes_batch."""

    def test_batch_detection(self):
        old_items = [
            make_item("001", situacao=Situacao.ABERTA),
            make_item("002", valor_estimado=50000.0),
        ]
        new_items = [
            make_item("001", situacao=Situacao.ENCERRADA),
            make_item("002", valor_estimado=60000.0),
            make_item("003"),  # Novo item, não gera change
        ]

        changes = detect_changes_batch(old_items, new_items)

        assert len(changes) == 2

    def test_batch_no_changes(self):
        items = [make_item("001"), make_item("002")]
        changes = detect_changes_batch(items, items)
        assert len(changes) == 0

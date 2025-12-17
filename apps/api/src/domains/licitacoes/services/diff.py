"""Serviço de detecção de mudanças em licitações."""

from datetime import datetime, timezone
import logging

from ..models import LicitacaoItem, ChangeEvent, TipoMudanca, SourceRef

logger = logging.getLogger(__name__)


def detect_changes(
    old_item: LicitacaoItem,
    new_item: LicitacaoItem,
) -> list[ChangeEvent]:
    """
    Detecta mudanças entre duas versões de uma licitação.

    Args:
        old_item: Versão anterior
        new_item: Versão atual

    Returns:
        Lista de ChangeEvent detectados
    """
    changes: list[ChangeEvent] = []
    now = datetime.now(timezone.utc)

    source = new_item.sources[0] if new_item.sources else SourceRef(
        source=new_item.source,
        url=new_item.url_edital or "",
    )

    if old_item.data_abertura != new_item.data_abertura:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.PRAZO_ALTERADO,
            campo="data_abertura",
            valor_anterior=str(old_item.data_abertura) if old_item.data_abertura else None,
            valor_novo=str(new_item.data_abertura) if new_item.data_abertura else None,
            detectado_em=now,
            fonte=source,
            descricao="Data de abertura alterada",
        ))

    if old_item.data_encerramento != new_item.data_encerramento:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.PRAZO_ALTERADO,
            campo="data_encerramento",
            valor_anterior=str(old_item.data_encerramento) if old_item.data_encerramento else None,
            valor_novo=str(new_item.data_encerramento) if new_item.data_encerramento else None,
            detectado_em=now,
            fonte=source,
            descricao="Data de encerramento alterada",
        ))

    if old_item.situacao != new_item.situacao:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.STATUS_ALTERADO,
            campo="situacao",
            valor_anterior=old_item.situacao.value,
            valor_novo=new_item.situacao.value,
            detectado_em=now,
            fonte=source,
            descricao=f"Status alterado de {old_item.situacao.value} para {new_item.situacao.value}",
        ))

    if old_item.valor_estimado != new_item.valor_estimado:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.VALOR_ALTERADO,
            campo="valor_estimado",
            valor_anterior=str(old_item.valor_estimado) if old_item.valor_estimado else None,
            valor_novo=str(new_item.valor_estimado) if new_item.valor_estimado else None,
            detectado_em=now,
            fonte=source,
            descricao="Valor estimado alterado",
        ))

    old_anexos = {a.filename for a in old_item.anexos}
    new_anexos = {a.filename for a in new_item.anexos}

    added_anexos = new_anexos - old_anexos
    removed_anexos = old_anexos - new_anexos

    for filename in added_anexos:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.ANEXO_ADICIONADO,
            campo="anexos",
            valor_anterior=None,
            valor_novo=filename,
            detectado_em=now,
            fonte=source,
            descricao=f"Anexo adicionado: {filename}",
        ))

    for filename in removed_anexos:
        changes.append(ChangeEvent(
            licitacao_id=new_item.external_id,
            tipo=TipoMudanca.ANEXO_REMOVIDO,
            campo="anexos",
            valor_anterior=filename,
            valor_novo=None,
            detectado_em=now,
            fonte=source,
            descricao=f"Anexo removido: {filename}",
        ))

    if changes:
        logger.info(f"Detected {len(changes)} changes for {new_item.external_id}")

    return changes


def detect_changes_batch(
    old_items: list[LicitacaoItem],
    new_items: list[LicitacaoItem],
) -> list[ChangeEvent]:
    """
    Detecta mudanças em lote comparando listas de itens.

    Args:
        old_items: Lista de versões anteriores
        new_items: Lista de versões atuais

    Returns:
        Lista de todos os ChangeEvent detectados
    """
    old_map = {item.external_id: item for item in old_items}
    all_changes: list[ChangeEvent] = []

    for new_item in new_items:
        if new_item.external_id in old_map:
            old_item = old_map[new_item.external_id]
            changes = detect_changes(old_item, new_item)
            all_changes.extend(changes)

    return all_changes

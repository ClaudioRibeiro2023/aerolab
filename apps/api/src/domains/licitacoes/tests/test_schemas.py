"""Testes dos schemas do Núcleo Licitações."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ..models import (
    SourceRef,
    AttachmentRef,
    LicitacaoItem,
    ChangeEvent,
    TriageScore,
    AnalysisPack,
    FlowConfig,
    FlowResult,
    Modalidade,
    Situacao,
    Prioridade,
    NivelRisco,
    TipoMudanca,
    StatusFluxo,
)


class TestSourceRef:
    """Testes para SourceRef."""

    def test_create_valid(self):
        source = SourceRef(
            source="pncp",
            url="https://pncp.gov.br/api/v1/123",
        )
        assert source.source == "pncp"
        assert source.url == "https://pncp.gov.br/api/v1/123"
        assert source.fetched_at is not None

    def test_with_hash(self):
        source = SourceRef(
            source="pncp",
            url="https://pncp.gov.br/api/v1/123",
            content_hash="abc123",
        )
        assert source.content_hash == "abc123"


class TestLicitacaoItem:
    """Testes para LicitacaoItem."""

    def test_create_minimal_valid(self):
        item = LicitacaoItem(
            external_id="PNCP-123",
            source="pncp",
            objeto="Aquisição de drones para combate à dengue",
            orgao="Prefeitura Municipal",
            uf="sp",
            sources=[
                SourceRef(source="pncp", url="https://pncp.gov.br/123"),
            ],
        )
        assert item.external_id == "PNCP-123"
        assert item.uf == "SP"  # Deve ser uppercase
        assert item.modalidade == Modalidade.OUTRO
        assert item.situacao == Situacao.DESCONHECIDA
        assert len(item.sources) == 1

    def test_uf_uppercase(self):
        item = LicitacaoItem(
            external_id="123",
            source="pncp",
            objeto="Teste",
            orgao="Orgao",
            uf="rj",
            sources=[SourceRef(source="pncp", url="https://example.com")],
        )
        assert item.uf == "RJ"

    def test_full_item(self):
        item = LicitacaoItem(
            external_id="PNCP-456",
            source="pncp",
            objeto="Contratação de serviços de geotecnologia",
            orgao="Secretaria de Saúde",
            uf="MG",
            municipio="Belo Horizonte",
            modalidade=Modalidade.PREGAO_ELETRONICO,
            situacao=Situacao.ABERTA,
            valor_estimado=150000.00,
            data_publicacao=datetime(2025, 1, 1),
            data_abertura=datetime(2025, 1, 15),
            url_edital="https://pncp.gov.br/edital/456",
            anexos=[
                AttachmentRef(
                    filename="edital.pdf",
                    url="https://pncp.gov.br/edital/456/anexo1",
                    size_bytes=1024000,
                ),
            ],
            sources=[
                SourceRef(source="pncp", url="https://pncp.gov.br/api/v1/456"),
            ],
        )
        assert item.modalidade == Modalidade.PREGAO_ELETRONICO
        assert item.valor_estimado == 150000.00
        assert len(item.anexos) == 1

    def test_sources_required(self):
        """sources[] é obrigatório e deve ter pelo menos 1 item."""
        with pytest.raises(ValidationError) as exc_info:
            LicitacaoItem(
                external_id="123",
                source="pncp",
                objeto="Teste",
                orgao="Orgao",
                uf="SP",
                sources=[],  # Lista vazia deve falhar
            )
        assert "too_short" in str(exc_info.value)


class TestChangeEvent:
    """Testes para ChangeEvent."""

    def test_create_prazo_alterado(self):
        event = ChangeEvent(
            licitacao_id="PNCP-123",
            tipo=TipoMudanca.PRAZO_ALTERADO,
            campo="data_abertura",
            valor_anterior="2025-01-15",
            valor_novo="2025-01-20",
        )
        assert event.tipo == TipoMudanca.PRAZO_ALTERADO
        assert event.campo == "data_abertura"


class TestTriageScore:
    """Testes para TriageScore."""

    def test_create_valid(self):
        score = TriageScore(
            licitacao_id="PNCP-123",
            score=0.85,
            prioridade=Prioridade.P0,
            aderencia_portfolio=0.9,
            regiao_estrategica=0.8,
            motivos=["Alta aderência ao portfólio", "Região prioritária"],
        )
        assert score.score == 0.85
        assert score.prioridade == Prioridade.P0
        assert len(score.motivos) == 2

    def test_score_bounds(self):
        """Score deve estar entre 0 e 1."""
        with pytest.raises(ValidationError):
            TriageScore(
                licitacao_id="123",
                score=1.5,  # Inválido
                prioridade=Prioridade.P0,
            )


class TestAnalysisPack:
    """Testes para AnalysisPack."""

    def test_create_valid(self):
        pack = AnalysisPack(
            licitacao_id="PNCP-123",
            resumo_executivo="Licitação com alta aderência ao portfólio da Aero.",
            pontos_atencao=["Prazo curto"],
            recomendacao="participar",
        )
        assert pack.licitacao_id == "PNCP-123"
        assert pack.aviso_revisao is not None  # Default obrigatório
        assert pack.confianca == 0.5  # Default


class TestFlowConfig:
    """Testes para FlowConfig."""

    def test_defaults(self):
        cfg = FlowConfig()
        assert cfg.janela_dias == 7
        assert cfg.limite_itens == 100
        assert "dengue" in cfg.keywords
        assert Modalidade.PREGAO_ELETRONICO in cfg.modalidades

    def test_custom_config(self):
        cfg = FlowConfig(
            janela_dias=14,
            ufs=["SP", "RJ", "MG"],
            keywords=["drone", "geoprocessamento"],
        )
        assert cfg.janela_dias == 14
        assert len(cfg.ufs) == 3


class TestFlowResult:
    """Testes para FlowResult."""

    def test_init_result(self):
        result = FlowResult.init_result("run-001")
        assert result.status == StatusFluxo.INIT
        assert result.run_id == "run-001"
        assert result.started_at is not None
        assert result.errors == []

    def test_mark_success(self):
        result = FlowResult.init_result("run-002")
        result.items_processed = 50
        result.items_p0 = 3
        result.mark_success()

        assert result.status == StatusFluxo.SUCCESS
        assert result.finished_at is not None
        assert result.duration_seconds is not None

    def test_mark_error(self):
        result = FlowResult.init_result("run-003")
        result.mark_error("PNCP API timeout")

        assert result.status == StatusFluxo.ERROR
        assert "PNCP API timeout" in result.errors

    def test_always_valid_default(self):
        """FlowResult deve ter estado válido por padrão."""
        result = FlowResult()
        assert result.status == StatusFluxo.INIT
        assert result.payload_json == "{}"
        assert result.errors == []


class TestEnums:
    """Testes para Enums."""

    def test_modalidade_values(self):
        assert Modalidade.PREGAO_ELETRONICO.value == "pregao_eletronico"
        assert Modalidade.CONCORRENCIA.value == "concorrencia"

    def test_prioridade_values(self):
        assert Prioridade.P0.value == "P0"
        assert Prioridade.P3.value == "P3"

    def test_nivel_risco_values(self):
        assert NivelRisco.CRITICO.value == "critico"
        assert NivelRisco.BAIXO.value == "baixo"

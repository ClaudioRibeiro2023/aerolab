"""Golden tests para o Núcleo Licitações.

Golden tests validam que os agentes produzem resultados consistentes
com expectativas pré-definidas. Quando mudar prompt/model/tool,
rodar estes testes para detectar regressões.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone

from ..models import LicitacaoItem, SourceRef, Prioridade
from ..agents import TriageAgent, AnalystAgent
from ..tools.pncp_client import PNCPClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_DIR = Path(__file__).parent / "golden"


def load_fixture(name: str) -> dict:
    """Carrega fixture JSON."""
    path = FIXTURES_DIR / "pncp" / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def load_golden(category: str, name: str) -> dict:
    """Carrega expectativa golden."""
    path = GOLDEN_DIR / category / f"{name}.expected.json"
    with open(path) as f:
        return json.load(f)


def fixture_to_item(fixture: dict) -> LicitacaoItem:
    """Converte fixture PNCP para LicitacaoItem."""
    client = PNCPClient()
    return client._normalize_item(fixture)


class TestGoldenTriage:
    """Golden tests para o agente Triage."""

    @pytest.fixture
    def triage_agent(self):
        return TriageAgent()

    def test_sample_001_high_priority(self, triage_agent):
        """Sample 001: Drones para dengue em SP - deve ser P0."""
        fixture = load_fixture("sample_001")
        golden = load_golden("triage", "sample_001")

        item = fixture_to_item(fixture)
        result = triage_agent.score_items([item])
        score = result.scores[0]

        assert score.prioridade.value == golden["expected_priority"], \
            f"Prioridade esperada {golden['expected_priority']}, obtida {score.prioridade.value}"

        assert score.score >= golden["expected_score_min"], \
            f"Score mínimo esperado {golden['expected_score_min']}, obtido {score.score}"

        assert score.score <= golden["expected_score_max"], \
            f"Score máximo esperado {golden['expected_score_max']}, obtido {score.score}"

        assert score.aderencia_portfolio >= golden["expected_aderencia_min"], \
            f"Aderência mínima esperada {golden['expected_aderencia_min']}, obtida {score.aderencia_portfolio}"

        motivos_text = " ".join(score.motivos).lower()
        for keyword in golden["expected_motivos_contains"]:
            assert keyword.lower() in motivos_text, \
                f"Motivo esperado contendo '{keyword}' não encontrado em {score.motivos}"

    def test_sample_002_low_priority(self, triage_agent):
        """Sample 002: Material de escritório - deve ser P3."""
        fixture = load_fixture("sample_002")
        golden = load_golden("triage", "sample_002")

        item = fixture_to_item(fixture)
        result = triage_agent.score_items([item])
        score = result.scores[0]

        assert score.prioridade.value == golden["expected_priority"], \
            f"Prioridade esperada {golden['expected_priority']}, obtida {score.prioridade.value}"

        assert score.score >= golden["expected_score_min"], \
            f"Score mínimo esperado {golden['expected_score_min']}, obtido {score.score}"

        assert score.score <= golden["expected_score_max"], \
            f"Score máximo esperado {golden['expected_score_max']}, obtido {score.score}"

    def test_sample_003_high_priority(self, triage_agent):
        """Sample 003: VANT para dengue em MG - deve ser P0."""
        fixture = load_fixture("sample_003")
        golden = load_golden("triage", "sample_003")

        item = fixture_to_item(fixture)
        result = triage_agent.score_items([item])
        score = result.scores[0]

        assert score.prioridade.value == golden["expected_priority"], \
            f"Prioridade esperada {golden['expected_priority']}, obtida {score.prioridade.value}"

        assert score.score >= golden["expected_score_min"], \
            f"Score mínimo esperado {golden['expected_score_min']}, obtido {score.score}"

    def test_batch_triage_consistency(self, triage_agent):
        """Testa triagem em lote - resultados devem ser consistentes."""
        items = [
            fixture_to_item(load_fixture("sample_001")),
            fixture_to_item(load_fixture("sample_002")),
            fixture_to_item(load_fixture("sample_003")),
        ]

        result = triage_agent.score_items(items)

        assert result.total == 3
        assert result.p0_count >= 2, "Esperado pelo menos 2 P0 (samples 001 e 003)"
        assert result.p0_count + result.p1_count + len(result.p2_items) + len(result.p3_items) == 3

        priorities = [s.prioridade for s in result.scores]
        assert Prioridade.P0 in priorities
        # Sample 002 é P2 (não P3) porque RJ é região estratégica
        assert Prioridade.P2 in priorities or Prioridade.P3 in priorities


class TestGoldenAnalyst:
    """Golden tests para o agente Analyst."""

    @pytest.fixture
    def analyst_agent(self):
        return AnalystAgent()

    def test_sample_001_analysis(self, analyst_agent):
        """Sample 001: Análise deve identificar oportunidades de drone/dengue."""
        fixture = load_fixture("sample_001")
        item = fixture_to_item(fixture)

        result = analyst_agent.analyze(item)

        assert result.analysis is not None
        assert result.analysis.licitacao_id == item.external_id
        assert len(result.analysis.resumo_executivo) > 0
        assert result.analysis.aviso_revisao is not None

        oportunidades_text = " ".join(result.analysis.oportunidades).lower()
        assert "drone" in oportunidades_text or "saúde" in oportunidades_text or "dengue" in oportunidades_text, \
            f"Esperado oportunidade relacionada a drone/dengue em {result.analysis.oportunidades}"

    def test_sample_002_analysis_no_opportunity(self, analyst_agent):
        """Sample 002: Material de escritório - poucas oportunidades."""
        fixture = load_fixture("sample_002")
        item = fixture_to_item(fixture)

        result = analyst_agent.analyze(item)

        assert result.analysis is not None
        assert len(result.analysis.oportunidades) <= 1, \
            "Material de escritório não deve ter muitas oportunidades"

    def test_analysis_always_has_disclaimer(self, analyst_agent):
        """Toda análise deve ter aviso de revisão humana."""
        for sample in ["sample_001", "sample_002", "sample_003"]:
            fixture = load_fixture(sample)
            item = fixture_to_item(fixture)
            result = analyst_agent.analyze(item)

            assert result.analysis.aviso_revisao is not None
            assert "revisão" in result.analysis.aviso_revisao.lower() or \
                   "humana" in result.analysis.aviso_revisao.lower()


class TestGoldenNormalization:
    """Golden tests para normalização de dados PNCP."""

    def test_normalize_all_samples(self):
        """Todos os samples devem normalizar corretamente."""
        client = PNCPClient()

        for sample in ["sample_001", "sample_002", "sample_003"]:
            fixture = load_fixture(sample)
            item = client._normalize_item(fixture)

            assert item.external_id is not None
            assert item.source == "pncp"
            assert len(item.sources) >= 1
            assert item.objeto is not None
            assert item.orgao is not None
            assert len(item.uf) == 2

    def test_normalize_preserves_values(self):
        """Normalização deve preservar valores importantes."""
        fixture = load_fixture("sample_001")
        client = PNCPClient()
        item = client._normalize_item(fixture)

        assert item.valor_estimado == 750000.00
        assert item.uf == "SP"
        assert "drone" in item.objeto.lower() or "monitoramento" in item.objeto.lower()

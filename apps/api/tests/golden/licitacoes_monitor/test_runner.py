"""Testes do workflow licitacoes_monitor."""

import json
import pytest
from pathlib import Path


class TestLicitacoesMonitorRunner:
    """Testes para o runner do workflow."""

    @pytest.fixture
    def golden_cases(self):
        """Carrega casos golden."""
        cases_dir = Path(__file__).parent
        cases = []
        for f in sorted(cases_dir.glob("case_*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                cases.append(json.load(fp))
        return cases

    @pytest.mark.asyncio
    async def test_basic_run(self):
        """Teste básico de execução do runner."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone dengue",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        assert len(result.itens_encontrados) > 0
        assert result.triagem.total > 0

    @pytest.mark.asyncio
    async def test_with_uf_filter(self):
        """Teste com filtro por UF."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="equipamentos",
            uf="SP",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        for item in result.itens_encontrados:
            assert item.uf == "SP"

    @pytest.mark.asyncio
    async def test_triagem_scores(self):
        """Teste de triagem com scores."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone dengue",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        assert len(result.triagem.scores) > 0

        for score in result.triagem.scores:
            assert score.prioridade in ["P0", "P1", "P2", "P3"]
            assert 0 <= score.score <= 1

    @pytest.mark.asyncio
    async def test_audit_log(self):
        """Teste de audit log."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        assert len(result.runs) > 0

        steps = [r["step"] for r in result.runs]
        assert "input" in steps
        assert "coleta" in steps
        assert "triagem" in steps

    @pytest.mark.asyncio
    async def test_alertas_p0_p1(self):
        """Teste de geração de alertas P0/P1."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone dengue",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"

        if result.triagem.p0_count > 0 or result.triagem.p1_count > 0:
            assert len(result.alertas) > 0
            for alerta in result.alertas:
                assert alerta.prioridade in ["P0", "P1"]

    @pytest.mark.asyncio
    async def test_metadata(self):
        """Teste de metadata da execução."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        assert result.metadata is not None
        assert result.metadata.run_id
        assert result.metadata.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_export_json(self):
        """Teste de export JSON."""
        from src.workflows.licitacoes.licitacoes_monitor.runner import (
            LicitacoesMonitorRunner,
        )
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        runner = LicitacoesMonitorRunner()
        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone",
            modo_execucao="one_shot",
        )

        result = await runner.run(input_data)

        assert result.status == "success"
        assert result.export_json
        assert result.payload_json

        parsed = json.loads(result.payload_json)
        assert "total_itens" in parsed


class TestLicitacoesMonitorModels:
    """Testes para os models do workflow."""

    def test_input_validation(self):
        """Teste de validação de input."""
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )

        input_data = LicitacoesMonitorInput(
            fonte="pncp",
            termo_busca="drone",
            modo_execucao="one_shot",
        )

        assert input_data.fonte == "pncp"
        assert input_data.termo_busca == "drone"

    def test_input_invalid_fonte(self):
        """Teste de fonte inválida."""
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LicitacoesMonitorInput(
                fonte="invalid",
                termo_busca="drone",
                modo_execucao="one_shot",
            )

    def test_input_termo_busca_min_length(self):
        """Teste de termo de busca muito curto."""
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorInput,
        )
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LicitacoesMonitorInput(
                fonte="pncp",
                termo_busca="ab",
                modo_execucao="one_shot",
            )

    def test_result_defaults(self):
        """Teste de defaults do result."""
        from src.workflows.licitacoes.licitacoes_monitor.models import (
            LicitacoesMonitorResult,
        )

        result = LicitacoesMonitorResult()

        assert result.status == "init"
        assert result.payload_json == "{}"
        assert result.errors == []
        assert result.itens_encontrados == []

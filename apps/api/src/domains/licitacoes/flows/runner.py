"""Runner de orquestração para fluxos de licitações."""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any
import uuid
import json
import logging

from ..models import (
    LicitacaoItem,
    TriageScore,
    AnalysisPack,
    FlowConfig,
    FlowResult,
    StatusFluxo,
    Prioridade,
)
from ..agents import (
    WatcherAgent,
    TriageAgent,
    AnalystAgent,
    ComplianceAgent,
)

logger = logging.getLogger(__name__)


@dataclass
class DailyDigest:
    """Digest diário de licitações."""

    date: str
    total_items: int
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int
    new_items_count: int
    changes_count: int
    items: list[LicitacaoItem] = field(default_factory=list)
    scores: list[TriageScore] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MonitorFlowState:
    """Estado do fluxo daily_monitor."""

    run_id: str
    config: FlowConfig
    items: list[LicitacaoItem] = field(default_factory=list)
    changes: list[Any] = field(default_factory=list)
    scores: list[TriageScore] = field(default_factory=list)
    digest: DailyDigest | None = None
    result: FlowResult | None = None


@dataclass
class AnalyzeFlowState:
    """Estado do fluxo on_demand_analyze."""

    run_id: str
    licitacao_id: str | None = None
    url: str | None = None
    text: str | None = None
    licitacao: LicitacaoItem | None = None
    document_text: str | None = None
    analysis: AnalysisPack | None = None
    result: FlowResult | None = None


class DailyMonitorRunner:
    """
    Runner para o fluxo daily_monitor.

    Executa: Watcher → Triage → Digest → Persist
    """

    def __init__(self, config: FlowConfig | None = None):
        self.config = config or FlowConfig()
        self.watcher = WatcherAgent(config=self.config)
        self.triage = TriageAgent(config=self.config)

    async def run(
        self,
        existing_items: list[LicitacaoItem] | None = None,
    ) -> tuple[MonitorFlowState, FlowResult]:
        """
        Executa o fluxo completo de monitoramento diário.

        Args:
            existing_items: Itens já conhecidos (para detectar mudanças)

        Returns:
            Tupla (state, result)
        """
        run_id = f"monitor-{uuid.uuid4().hex[:8]}"
        result = FlowResult.init_result(run_id)
        state = MonitorFlowState(run_id=run_id, config=self.config)

        try:
            logger.info(f"[{run_id}] Starting daily_monitor flow")

            logger.info(f"[{run_id}] Step 1: Watcher.search()")
            watcher_result = await self.watcher.search(existing_items=existing_items)
            state.items = watcher_result.items
            state.changes = watcher_result.changes

            if watcher_result.has_errors:
                for err in watcher_result.errors:
                    result.add_warning(err)

            logger.info(f"[{run_id}] Step 2: Triage.score_items() - {len(state.items)} items")
            triage_result = self.triage.score_items(state.items)
            state.scores = triage_result.scores

            logger.info(f"[{run_id}] Step 3: Generate digest")
            state.digest = self._generate_digest(state, watcher_result.new_items)

            result.items_processed = len(state.items)
            result.items_p0 = triage_result.p0_count
            result.items_p1 = triage_result.p1_count
            result.payload_json = json.dumps({
                "digest_date": state.digest.date,
                "total_items": state.digest.total_items,
                "p0_count": state.digest.p0_count,
                "p1_count": state.digest.p1_count,
            })

            result.mark_success()
            logger.info(f"[{run_id}] Flow completed successfully")

        except Exception as e:
            logger.error(f"[{run_id}] Flow failed: {e}")
            result.mark_error(str(e))

        state.result = result
        return state, result

    def _generate_digest(
        self,
        state: MonitorFlowState,
        new_items: list[LicitacaoItem],
    ) -> DailyDigest:
        """Gera o digest diário."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        p0 = [s for s in state.scores if s.prioridade == Prioridade.P0]
        p1 = [s for s in state.scores if s.prioridade == Prioridade.P1]
        p2 = [s for s in state.scores if s.prioridade == Prioridade.P2]
        p3 = [s for s in state.scores if s.prioridade == Prioridade.P3]

        return DailyDigest(
            date=today,
            total_items=len(state.items),
            p0_count=len(p0),
            p1_count=len(p1),
            p2_count=len(p2),
            p3_count=len(p3),
            new_items_count=len(new_items),
            changes_count=len(state.changes),
            items=state.items,
            scores=state.scores,
        )


class OnDemandAnalyzeRunner:
    """
    Runner para o fluxo on_demand_analyze.

    Executa: Compliance(in) → Watcher(detail) → Analyst → Compliance(out)
    """

    def __init__(self):
        self.watcher = WatcherAgent()
        self.analyst = AnalystAgent()
        self.compliance = ComplianceAgent()

    async def run(
        self,
        licitacao_id: str | None = None,
        url: str | None = None,
        text: str | None = None,
    ) -> tuple[AnalyzeFlowState, FlowResult]:
        """
        Executa análise sob demanda de uma licitação.

        Args:
            licitacao_id: ID externo da licitação
            url: URL do edital
            text: Texto do edital

        Returns:
            Tupla (state, result)
        """
        run_id = f"analyze-{uuid.uuid4().hex[:8]}"
        result = FlowResult.init_result(run_id)
        state = AnalyzeFlowState(
            run_id=run_id,
            licitacao_id=licitacao_id,
            url=url,
            text=text,
        )

        try:
            logger.info(f"[{run_id}] Starting on_demand_analyze flow")

            logger.info(f"[{run_id}] Step 1: Compliance.check_input()")
            input_text = text or url or licitacao_id or ""
            compliance_result = self.compliance.check_input(input_text)

            if not compliance_result.passed:
                logger.warning(f"[{run_id}] Compliance check failed: {compliance_result.issues}")
                result.mark_error(f"Compliance check failed: {compliance_result.issues}")
                state.result = result
                return state, result

            if compliance_result.has_warnings:
                for warn in compliance_result.warnings:
                    result.add_warning(warn)

            if licitacao_id:
                logger.info(f"[{run_id}] Step 2: Watcher.get_detail({licitacao_id})")
                state.licitacao = await self.watcher.get_detail(licitacao_id)

                if not state.licitacao:
                    result.mark_error(f"Licitação não encontrada: {licitacao_id}")
                    state.result = result
                    return state, result

            if not state.licitacao and not text:
                result.mark_error("Forneça licitacao_id ou text para análise")
                state.result = result
                return state, result

            logger.info(f"[{run_id}] Step 3: Analyst.analyze()")
            if state.licitacao:
                analyst_result = self.analyst.analyze(
                    item=state.licitacao,
                    document_text=text,
                )
                state.analysis = analyst_result.analysis

            logger.info(f"[{run_id}] Step 4: Compliance.check_output()")
            if state.analysis:
                output_check = self.compliance.check_output(state.analysis.model_dump())
                if output_check.has_warnings:
                    for warn in output_check.warnings:
                        result.add_warning(warn)

            result.items_processed = 1
            result.payload_json = json.dumps({
                "licitacao_id": licitacao_id,
                "has_analysis": state.analysis is not None,
                "recomendacao": state.analysis.recomendacao if state.analysis else None,
            })

            result.mark_success()
            logger.info(f"[{run_id}] Flow completed successfully")

        except Exception as e:
            logger.error(f"[{run_id}] Flow failed: {e}")
            result.mark_error(str(e))

        state.result = result
        return state, result


async def run_daily_monitor(
    config: FlowConfig | None = None,
    existing_items: list[LicitacaoItem] | None = None,
) -> tuple[MonitorFlowState, FlowResult]:
    """Função de conveniência para executar daily_monitor."""
    runner = DailyMonitorRunner(config=config)
    return await runner.run(existing_items=existing_items)


async def run_on_demand_analyze(
    licitacao_id: str | None = None,
    url: str | None = None,
    text: str | None = None,
) -> tuple[AnalyzeFlowState, FlowResult]:
    """Função de conveniência para executar on_demand_analyze."""
    runner = OnDemandAnalyzeRunner()
    return await runner.run(licitacao_id=licitacao_id, url=url, text=text)

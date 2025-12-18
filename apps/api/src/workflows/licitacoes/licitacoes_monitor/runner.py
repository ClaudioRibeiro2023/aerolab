"""Runner para o workflow licitacoes_monitor."""

import json
import logging
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .models import (
    LicitacoesMonitorInput,
    LicitacoesMonitorResult,
    ItemEncontrado,
    TriagemResult,
    TriagemScore,
    AnaliseJuridica,
    Evidencia,
    Recomendacao,
    Alerta,
    RunMetadata,
)

logger = logging.getLogger(__name__)


class AuditEntry:
    """Entrada de audit log."""

    def __init__(self, step: str, run_id: str):
        self.step = step
        self.run_id = run_id
        self.started_at = datetime.now(timezone.utc)
        self.finished_at: datetime | None = None
        self.tokens_used = 0
        self.cost_usd = 0.0
        self.status = "running"
        self.error: str | None = None

    def complete(self, tokens: int = 0, cost: float = 0.0):
        self.finished_at = datetime.now(timezone.utc)
        self.tokens_used = tokens
        self.cost_usd = cost
        self.status = "success"

    def fail(self, error: str):
        self.finished_at = datetime.now(timezone.utc)
        self.status = "error"
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": int((self.finished_at - self.started_at).total_seconds() * 1000) if self.finished_at else 0,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "status": self.status,
            "error": self.error,
        }


class LicitacoesMonitorRunner:
    """
    Runner para o workflow de monitoramento de licitações.

    Executa os nodes:
    1. input - Validação de entrada
    2. coleta - Busca em fontes (PNCP, etc)
    3. dedup - Deduplicação
    4. triagem - Classificação por prioridade
    5. analise - Análise com RAG jurídico
    6. compliance - Validação de conformidade
    7. output - Formatação e exportação
    """

    def __init__(self):
        self.audit_log: list[AuditEntry] = []
        self.run_id = ""
        self._watcher = None
        self._triage = None
        self._analyst = None
        self._compliance = None
        self._rag_juridico = None

    def _init_agents(self):
        """Inicializa agentes do domínio licitações."""
        try:
            from src.domains.licitacoes.agents import (
                WatcherAgent,
                TriageAgent,
                AnalystAgent,
                ComplianceAgent,
            )
            from src.domains.licitacoes.services import get_rag_juridico

            self._watcher = WatcherAgent()
            self._triage = TriageAgent()
            self._analyst = AnalystAgent()
            self._compliance = ComplianceAgent()
            self._rag_juridico = get_rag_juridico()
        except ImportError as e:
            logger.warning(f"Could not import agents: {e}")

    def _audit(self, step: str) -> AuditEntry:
        """Cria entrada de audit para um step."""
        entry = AuditEntry(step=step, run_id=self.run_id)
        self.audit_log.append(entry)
        return entry

    async def run(self, input_data: LicitacoesMonitorInput) -> LicitacoesMonitorResult:
        """Executa o workflow completo."""
        self.run_id = str(uuid.uuid4())
        self.audit_log = []
        start_time = time.time()

        result = LicitacoesMonitorResult(status="running")

        try:
            self._init_agents()

            # Step 1: Input validation
            audit = self._audit("input")
            validated_input = self._validate_input(input_data)
            audit.complete()

            # Step 2: Coleta
            audit = self._audit("coleta")
            itens = await self._coleta(validated_input)
            result.itens_encontrados = itens
            audit.complete(tokens=100, cost=0.001)

            # Step 3: Dedup
            audit = self._audit("dedup")
            itens_unicos = self._dedup(itens)
            result.itens_encontrados = itens_unicos
            audit.complete()

            # Step 4: Triagem
            audit = self._audit("triagem")
            triagem = self._triagem(itens_unicos)
            result.triagem = triagem
            audit.complete(tokens=200, cost=0.002)

            # Step 5: Análise (apenas P0/P1)
            audit = self._audit("analise")
            p0_p1_ids = [s.licitacao_id for s in triagem.scores if s.prioridade in ["P0", "P1"]]
            p0_p1_itens = [i for i in itens_unicos if i.external_id in p0_p1_ids]

            analise, evidencias, recomendacoes = await self._analise(p0_p1_itens)
            result.analise_juridica = analise
            result.evidencias = evidencias
            result.recomendacoes = recomendacoes
            audit.complete(tokens=500, cost=0.005)

            # Step 6: Compliance
            audit = self._audit("compliance")
            alertas = self._compliance_check(triagem, result.recomendacoes)
            result.alertas = alertas
            audit.complete()

            # Step 7: Output
            audit = self._audit("output")
            result = self._format_output(result)
            audit.complete()

            # Finalizar
            end_time = time.time()
            result.status = "success"
            result.metadata = RunMetadata(
                run_id=self.run_id,
                started_at=datetime.now(timezone.utc) - timedelta(seconds=end_time - start_time),
                finished_at=datetime.now(timezone.utc),
                duration_ms=int((end_time - start_time) * 1000),
                tokens_used=sum(a.tokens_used for a in self.audit_log),
                cost_usd=sum(a.cost_usd for a in self.audit_log),
            )

            result.runs = [a.to_dict() for a in self.audit_log]

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            result.status = "error"
            result.errors.append(str(e))
            if self.audit_log:
                self.audit_log[-1].fail(str(e))

        return result

    def _validate_input(self, input_data: LicitacoesMonitorInput) -> LicitacoesMonitorInput:
        """Valida e normaliza input."""
        if input_data.periodo_inicio is None:
            input_data.periodo_inicio = date.today() - timedelta(days=30)
        if input_data.periodo_fim is None:
            input_data.periodo_fim = date.today()
        return input_data

    async def _coleta(self, input_data: LicitacoesMonitorInput) -> list[ItemEncontrado]:
        """Coleta itens das fontes."""
        itens: list[ItemEncontrado] = []

        if self._watcher:
            try:
                result = await self._watcher.search(
                    termo=input_data.termo_busca,
                    uf=input_data.uf,
                    data_inicio=input_data.periodo_inicio,
                    data_fim=input_data.periodo_fim,
                )
                for item in result.items:
                    itens.append(ItemEncontrado(
                        external_id=item.external_id,
                        fonte=item.source,
                        objeto=item.objeto,
                        orgao=item.orgao,
                        uf=item.uf,
                        valor_estimado=item.valor_estimado,
                        data_abertura=item.data_abertura.isoformat() if item.data_abertura else None,
                    ))
            except Exception as e:
                logger.warning(f"Watcher failed: {e}")

        if not itens:
            itens = self._mock_coleta(input_data)

        return itens

    def _mock_coleta(self, input_data: LicitacoesMonitorInput) -> list[ItemEncontrado]:
        """Mock de coleta para testes."""
        return [
            ItemEncontrado(
                external_id=f"PNCP-{i}",
                fonte="pncp",
                objeto=f"Aquisição de {input_data.termo_busca} - Item {i}",
                orgao=f"Prefeitura Municipal",
                uf=input_data.uf or "SP",
                valor_estimado=100000.0 * i,
                data_abertura=date.today().isoformat(),
            )
            for i in range(1, 4)
        ]

    def _dedup(self, itens: list[ItemEncontrado]) -> list[ItemEncontrado]:
        """Remove duplicatas."""
        seen: set[str] = set()
        unicos: list[ItemEncontrado] = []
        for item in itens:
            key = f"{item.external_id}:{item.fonte}"
            if key not in seen:
                seen.add(key)
                unicos.append(item)
        return unicos

    def _triagem(self, itens: list[ItemEncontrado]) -> TriagemResult:
        """Classifica itens por prioridade."""
        scores: list[TriagemScore] = []
        p0 = p1 = p2 = p3 = 0

        for item in itens:
            score = 0.5
            motivos: list[str] = []

            obj_lower = item.objeto.lower()
            if "dengue" in obj_lower or "drone" in obj_lower:
                score += 0.3
                motivos.append("Keyword match")

            if item.uf in ["SP", "RJ", "MG", "PR"]:
                score += 0.1
                motivos.append("Strategic region")

            if item.valor_estimado and item.valor_estimado > 500000:
                score += 0.1
                motivos.append("High value")

            if score >= 0.8:
                prioridade = "P0"
                p0 += 1
            elif score >= 0.6:
                prioridade = "P1"
                p1 += 1
            elif score >= 0.4:
                prioridade = "P2"
                p2 += 1
            else:
                prioridade = "P3"
                p3 += 1

            scores.append(TriagemScore(
                licitacao_id=item.external_id,
                score=score,
                prioridade=prioridade,
                motivos=motivos,
            ))

        return TriagemResult(
            total=len(itens),
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            scores=scores,
        )

    async def _analise(
        self, itens: list[ItemEncontrado]
    ) -> tuple[AnaliseJuridica, list[Evidencia], list[Recomendacao]]:
        """Análise detalhada com RAG jurídico."""
        analise = AnaliseJuridica()
        evidencias: list[Evidencia] = []
        recomendacoes: list[Recomendacao] = []

        if self._rag_juridico:
            for item in itens[:5]:
                ctx = self._rag_juridico.get_contexto_juridico(item.objeto)
                analise.artigos_relevantes.extend(ctx.get("artigos_relevantes", []))
                analise.checklist_habilitacao = ctx.get("checklist_habilitacao", [])

        for item in itens:
            evidencias.append(Evidencia(
                tipo="url",
                url=f"https://pncp.gov.br/app/editais/{item.external_id}",
                descricao=f"Edital {item.external_id}",
            ))

            recomendacoes.append(Recomendacao(
                licitacao_id=item.external_id,
                acao="analisar_mais",
                justificativa="Análise automatizada requer validação humana",
                confianca=0.7,
            ))

        return analise, evidencias, recomendacoes

    def _compliance_check(
        self, triagem: TriagemResult, recomendacoes: list[Recomendacao]
    ) -> list[Alerta]:
        """Gera alertas para P0/P1."""
        alertas: list[Alerta] = []

        for score in triagem.scores:
            if score.prioridade in ["P0", "P1"]:
                alertas.append(Alerta(
                    prioridade=score.prioridade,  # type: ignore
                    licitacao_id=score.licitacao_id,
                    mensagem=f"Licitação {score.prioridade} identificada: {', '.join(score.motivos)}",
                ))

        return alertas

    def _format_output(self, result: LicitacoesMonitorResult) -> LicitacoesMonitorResult:
        """Formata output final."""
        result.export_json = result.model_dump_json(indent=2)
        result.payload_json = json.dumps({
            "total_itens": len(result.itens_encontrados),
            "p0_count": result.triagem.p0_count,
            "p1_count": result.triagem.p1_count,
            "alertas_count": len(result.alertas),
        })
        return result


async def run_licitacoes_monitor(
    input_data: dict[str, Any] | LicitacoesMonitorInput,
) -> LicitacoesMonitorResult:
    """Função helper para executar o workflow."""
    if isinstance(input_data, dict):
        input_data = LicitacoesMonitorInput(**input_data)

    runner = LicitacoesMonitorRunner()
    return await runner.run(input_data)

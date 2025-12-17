"""Agente Triage — Triagem e priorização de licitações."""

from datetime import datetime, timezone
from dataclasses import dataclass
import logging
import re

from ..models import (
    LicitacaoItem,
    TriageScore,
    RiscoIdentificado,
    SourceRef,
    Prioridade,
    NivelRisco,
    FlowConfig,
)

logger = logging.getLogger(__name__)

KEYWORDS_PORTFOLIO = [
    "drone", "drones", "vant", "rpas",
    "geotecnologia", "geoprocessamento", "sig", "gis",
    "mapeamento", "aerofotogrametria", "fotogrametria",
    "sensoriamento", "monitoramento",
    "dengue", "arbovirose", "aedes", "zika", "chikungunya",
    "saúde pública", "vigilância epidemiológica",
    "combate a vetores", "controle de vetores",
]

UFS_ESTRATEGICAS = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE", "GO", "DF"]

KEYWORDS_RISCO = {
    "prazo_curto": ["urgente", "emergencial", "calamidade"],
    "exigencia_restritiva": ["exclusivo", "marca específica", "único fornecedor"],
    "valor_alto": [],
    "complexidade": ["técnica e preço", "melhor técnica"],
}


@dataclass
class TriageResult:
    """Resultado da triagem de licitações."""

    scores: list[TriageScore]
    p0_items: list[TriageScore]
    p1_items: list[TriageScore]
    p2_items: list[TriageScore]
    p3_items: list[TriageScore]
    triaged_at: datetime

    @property
    def total(self) -> int:
        return len(self.scores)

    @property
    def p0_count(self) -> int:
        return len(self.p0_items)

    @property
    def p1_count(self) -> int:
        return len(self.p1_items)


class TriageAgent:
    """
    Agente responsável por triagem e priorização de licitações.

    Responsabilidades:
    - Calcular score de aderência ao portfólio
    - Identificar riscos preliminares
    - Classificar prioridade (P0/P1/P2/P3)
    - Justificar classificação com motivos

    Restrições:
    - NÃO inventa informações
    - NÃO faz análise jurídica profunda
    - SEMPRE explica os motivos da classificação
    """

    def __init__(self, config: FlowConfig | None = None):
        self.config = config or FlowConfig()

    def score_items(self, items: list[LicitacaoItem]) -> TriageResult:
        """
        Executa triagem de lista de licitações.

        Args:
            items: Lista de LicitacaoItem para triar

        Returns:
            TriageResult com scores e classificações
        """
        scores: list[TriageScore] = []
        triaged_at = datetime.now(timezone.utc)

        for item in items:
            score = self._score_item(item)
            scores.append(score)

        p0 = [s for s in scores if s.prioridade == Prioridade.P0]
        p1 = [s for s in scores if s.prioridade == Prioridade.P1]
        p2 = [s for s in scores if s.prioridade == Prioridade.P2]
        p3 = [s for s in scores if s.prioridade == Prioridade.P3]

        logger.info(f"Triaged {len(scores)} items: P0={len(p0)}, P1={len(p1)}, P2={len(p2)}, P3={len(p3)}")

        return TriageResult(
            scores=scores,
            p0_items=p0,
            p1_items=p1,
            p2_items=p2,
            p3_items=p3,
            triaged_at=triaged_at,
        )

    def _score_item(self, item: LicitacaoItem) -> TriageScore:
        """Calcula score para um item individual."""
        motivos: list[str] = []
        riscos: list[RiscoIdentificado] = []

        aderencia = self._calc_aderencia_portfolio(item)
        if aderencia > 0.5:
            motivos.append(f"Alta aderência ao portfólio ({aderencia:.0%})")

        regiao = self._calc_regiao_estrategica(item)
        if regiao > 0.5:
            motivos.append(f"Região estratégica: {item.uf}")

        valor_norm = self._calc_valor_normalizado(item)
        if valor_norm > 0.5:
            motivos.append(f"Valor estimado relevante: R$ {item.valor_estimado:,.2f}" if item.valor_estimado else "Valor não informado")

        prazo_norm = self._calc_prazo_normalizado(item)
        if prazo_norm < 0.3:
            motivos.append("Prazo curto - atenção")
            riscos.append(RiscoIdentificado(
                tipo="prazo_curto",
                nivel=NivelRisco.MEDIO,
                descricao="Prazo reduzido para preparação de proposta",
            ))

        barreiras_norm = self._calc_barreiras(item, riscos)

        score = (
            aderencia * 0.35 +
            regiao * 0.20 +
            valor_norm * 0.15 +
            prazo_norm * 0.20 +
            barreiras_norm * 0.10
        )

        prioridade = self._classify_priority(score)

        if not motivos:
            motivos.append("Baixa aderência aos critérios de priorização")

        return TriageScore(
            licitacao_id=item.external_id,
            score=round(score, 3),
            prioridade=prioridade,
            aderencia_portfolio=round(aderencia, 3),
            regiao_estrategica=round(regiao, 3),
            valor_normalizado=round(valor_norm, 3),
            prazo_normalizado=round(prazo_norm, 3),
            barreiras_normalizado=round(barreiras_norm, 3),
            riscos_preliminares=riscos,
            motivos=motivos,
            triado_em=datetime.now(timezone.utc),
            sources=item.sources,
        )

    def _calc_aderencia_portfolio(self, item: LicitacaoItem) -> float:
        """Calcula aderência ao portfólio baseado em keywords."""
        texto = f"{item.objeto} {item.orgao}".lower()
        matches = sum(1 for kw in KEYWORDS_PORTFOLIO if kw.lower() in texto)
        return min(matches / 3, 1.0)

    def _calc_regiao_estrategica(self, item: LicitacaoItem) -> float:
        """Calcula score de região estratégica."""
        if item.uf in UFS_ESTRATEGICAS:
            return 1.0
        return 0.3

    def _calc_valor_normalizado(self, item: LicitacaoItem) -> float:
        """Normaliza valor estimado (0-1)."""
        if not item.valor_estimado:
            return 0.5

        if item.valor_estimado >= 1_000_000:
            return 1.0
        elif item.valor_estimado >= 500_000:
            return 0.8
        elif item.valor_estimado >= 100_000:
            return 0.6
        elif item.valor_estimado >= 50_000:
            return 0.4
        else:
            return 0.2

    def _calc_prazo_normalizado(self, item: LicitacaoItem) -> float:
        """Normaliza prazo (1 = muito tempo, 0 = urgente)."""
        if not item.data_abertura:
            return 0.5

        now = datetime.now(timezone.utc)
        if item.data_abertura.tzinfo is None:
            data_abertura = item.data_abertura.replace(tzinfo=timezone.utc)
        else:
            data_abertura = item.data_abertura

        dias = (data_abertura - now).days

        if dias < 0:
            return 0.0
        elif dias <= 3:
            return 0.2
        elif dias <= 7:
            return 0.5
        elif dias <= 15:
            return 0.7
        else:
            return 1.0

    def _calc_barreiras(self, item: LicitacaoItem, riscos: list[RiscoIdentificado]) -> float:
        """Calcula score de barreiras/riscos (1 = sem barreiras, 0 = muitas)."""
        texto = item.objeto.lower()
        barrier_count = 0

        for tipo, keywords in KEYWORDS_RISCO.items():
            for kw in keywords:
                if kw.lower() in texto:
                    barrier_count += 1
                    riscos.append(RiscoIdentificado(
                        tipo=tipo,
                        nivel=NivelRisco.MEDIO,
                        descricao=f"Detectada palavra-chave de risco: {kw}",
                        evidencia=kw,
                    ))

        if barrier_count == 0:
            return 1.0
        elif barrier_count == 1:
            return 0.7
        elif barrier_count == 2:
            return 0.4
        else:
            return 0.2

    def _classify_priority(self, score: float) -> Prioridade:
        """Classifica prioridade baseado no score."""
        if score >= 0.75:
            return Prioridade.P0
        elif score >= 0.50:
            return Prioridade.P1
        elif score >= 0.25:
            return Prioridade.P2
        else:
            return Prioridade.P3


async def create_triage_agent(config: FlowConfig | None = None) -> TriageAgent:
    """Factory function para criar TriageAgent."""
    return TriageAgent(config=config)

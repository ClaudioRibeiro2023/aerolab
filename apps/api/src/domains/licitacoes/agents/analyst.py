"""Agente Analyst — Análise detalhada de editais."""

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
import logging

from ..models import (
    LicitacaoItem,
    AnalysisPack,
    RiscoIdentificado,
    ChecklistItem,
    SourceRef,
    NivelRisco,
)

logger = logging.getLogger(__name__)

CHECKLIST_TECNICO = [
    "Objeto claramente definido",
    "Especificações técnicas disponíveis",
    "Quantitativos informados",
    "Prazo de execução definido",
    "Local de execução especificado",
    "Critérios de aceitação definidos",
]

CHECKLIST_JURIDICO = [
    "Habilitação jurídica exigida",
    "Qualificação técnica exigida",
    "Qualificação econômico-financeira exigida",
    "Regularidade fiscal exigida",
    "Declarações obrigatórias listadas",
    "Garantias exigidas",
]

AVISO_REVISAO = (
    "Esta análise é assistência automatizada e não constitui parecer jurídico. "
    "Revisão humana obrigatória antes de qualquer decisão."
)


@dataclass
class AnalystResult:
    """Resultado da análise de um edital."""

    analysis: AnalysisPack
    confidence: float
    analyzed_at: datetime
    errors: list[str]


class AnalystAgent:
    """
    Agente responsável por análise detalhada de editais.

    Responsabilidades:
    - Extrair informações-chave do edital
    - Identificar riscos e oportunidades
    - Preencher checklists técnico e jurídico
    - Gerar resumo executivo para decisão

    Restrições:
    - NÃO emite parecer jurídico
    - NÃO inventa informações não presentes no edital
    - SEMPRE cita evidências (trechos do documento)
    - SEMPRE inclui aviso de revisão humana
    """

    def __init__(self):
        pass

    def analyze(
        self,
        item: LicitacaoItem,
        document_text: str | None = None,
    ) -> AnalystResult:
        """
        Analisa uma licitação e gera pacote de análise.

        Args:
            item: LicitacaoItem com dados básicos
            document_text: Texto extraído do edital (opcional)

        Returns:
            AnalystResult com análise completa
        """
        errors: list[str] = []
        analyzed_at = datetime.now(timezone.utc)

        resumo = self._generate_resumo(item, document_text)
        pontos_atencao = self._identify_pontos_atencao(item, document_text)
        riscos = self._identify_riscos(item, document_text)
        oportunidades = self._identify_oportunidades(item, document_text)
        checklist_tec = self._fill_checklist_tecnico(item, document_text)
        checklist_jur = self._fill_checklist_juridico(item, document_text)
        recomendacao = self._generate_recomendacao(item, riscos, pontos_atencao)
        evidences = self._extract_evidences(document_text)
        confidence = self._calc_confidence(document_text, checklist_tec, checklist_jur)

        analysis = AnalysisPack(
            licitacao_id=item.external_id,
            resumo_executivo=resumo,
            pontos_atencao=pontos_atencao,
            riscos=riscos,
            oportunidades=oportunidades,
            checklist_tecnico=checklist_tec,
            checklist_juridico=checklist_jur,
            recomendacao=recomendacao,
            confianca=confidence,
            aviso_revisao=AVISO_REVISAO,
            analisado_em=analyzed_at,
            sources=item.sources,
            evidences=evidences,
        )

        return AnalystResult(
            analysis=analysis,
            confidence=confidence,
            analyzed_at=analyzed_at,
            errors=errors,
        )

    def _generate_resumo(self, item: LicitacaoItem, text: str | None) -> str:
        """Gera resumo executivo."""
        partes = [
            f"**Objeto:** {item.objeto}",
            f"**Órgão:** {item.orgao} ({item.uf})",
            f"**Modalidade:** {item.modalidade.value}",
        ]

        if item.valor_estimado:
            partes.append(f"**Valor estimado:** R$ {item.valor_estimado:,.2f}")

        if item.data_abertura:
            partes.append(f"**Abertura:** {item.data_abertura.strftime('%d/%m/%Y %H:%M')}")

        if text:
            partes.append("\n*Documento do edital disponível para análise detalhada.*")
        else:
            partes.append("\n*Documento do edital não disponível. Análise baseada apenas em metadados.*")

        return "\n".join(partes)

    def _identify_pontos_atencao(self, item: LicitacaoItem, text: str | None) -> list[str]:
        """Identifica pontos de atenção."""
        pontos: list[str] = []

        if item.data_abertura:
            now = datetime.now(timezone.utc)
            if item.data_abertura.tzinfo is None:
                data = item.data_abertura.replace(tzinfo=timezone.utc)
            else:
                data = item.data_abertura

            dias = (data - now).days
            if dias <= 3:
                pontos.append(f"⚠️ Prazo curto: apenas {dias} dias para abertura")
            elif dias <= 7:
                pontos.append(f"📅 Prazo moderado: {dias} dias para abertura")

        if not text:
            pontos.append("📄 Edital não analisado - apenas metadados disponíveis")

        if not item.valor_estimado:
            pontos.append("💰 Valor estimado não informado")

        return pontos

    def _identify_riscos(self, item: LicitacaoItem, text: str | None) -> list[RiscoIdentificado]:
        """Identifica riscos potenciais."""
        riscos: list[RiscoIdentificado] = []

        keywords_risco = {
            "exclusivo": ("exigencia_restritiva", NivelRisco.ALTO, "Possível restrição de competitividade"),
            "marca": ("marca_especifica", NivelRisco.MEDIO, "Possível exigência de marca específica"),
            "único fornecedor": ("fornecedor_unico", NivelRisco.ALTO, "Indica possível direcionamento"),
            "calamidade": ("urgencia", NivelRisco.MEDIO, "Licitação em regime de urgência"),
            "emergencial": ("urgencia", NivelRisco.MEDIO, "Contratação emergencial"),
        }

        search_text = f"{item.objeto} {text or ''}".lower()

        for keyword, (tipo, nivel, desc) in keywords_risco.items():
            if keyword in search_text:
                riscos.append(RiscoIdentificado(
                    tipo=tipo,
                    nivel=nivel,
                    descricao=desc,
                    evidencia=f"Palavra-chave detectada: '{keyword}'",
                ))

        return riscos

    def _identify_oportunidades(self, item: LicitacaoItem, text: str | None) -> list[str]:
        """Identifica oportunidades."""
        oportunidades: list[str] = []

        keywords_oport = [
            ("drone", "Alinhado com expertise em drones/VANTs"),
            ("geotecnologia", "Alinhado com expertise em geotecnologia"),
            ("mapeamento", "Oportunidade em mapeamento/cartografia"),
            ("dengue", "Projeto de saúde pública - área estratégica"),
            ("monitoramento", "Serviço recorrente - potencial contrato contínuo"),
        ]

        search_text = f"{item.objeto}".lower()

        for keyword, desc in keywords_oport:
            if keyword in search_text:
                oportunidades.append(f"✅ {desc}")

        if item.valor_estimado and item.valor_estimado >= 500_000:
            oportunidades.append("💰 Valor expressivo - alto potencial de receita")

        return oportunidades

    def _fill_checklist_tecnico(self, item: LicitacaoItem, text: str | None) -> list[ChecklistItem]:
        """Preenche checklist técnico."""
        checklist: list[ChecklistItem] = []

        for item_check in CHECKLIST_TECNICO:
            if text:
                status = "pendente"
                obs = "Verificar no documento do edital"
            else:
                status = "pendente"
                obs = "Edital não disponível para verificação"

            checklist.append(ChecklistItem(
                item=item_check,
                status=status,
                observacao=obs,
            ))

        return checklist

    def _fill_checklist_juridico(self, item: LicitacaoItem, text: str | None) -> list[ChecklistItem]:
        """Preenche checklist jurídico."""
        checklist: list[ChecklistItem] = []

        for item_check in CHECKLIST_JURIDICO:
            if text:
                status = "pendente"
                obs = "Verificar no documento do edital"
            else:
                status = "pendente"
                obs = "Edital não disponível para verificação"

            checklist.append(ChecklistItem(
                item=item_check,
                status=status,
                observacao=obs,
            ))

        return checklist

    def _generate_recomendacao(
        self,
        item: LicitacaoItem,
        riscos: list[RiscoIdentificado],
        pontos: list[str],
    ) -> str:
        """Gera recomendação baseada na análise."""
        riscos_altos = [r for r in riscos if r.nivel in (NivelRisco.ALTO, NivelRisco.CRITICO)]

        if riscos_altos:
            return "analisar mais"
        elif len(riscos) > 2:
            return "analisar mais"
        elif len(pontos) > 3:
            return "analisar mais"
        else:
            return "participar"

    def _extract_evidences(self, text: str | None) -> list[str]:
        """Extrai trechos relevantes como evidências."""
        if not text:
            return ["Documento do edital não disponível para extração de evidências"]

        return [f"Documento com {len(text)} caracteres disponível para análise"]

    def _calc_confidence(
        self,
        text: str | None,
        checklist_tec: list[ChecklistItem],
        checklist_jur: list[ChecklistItem],
    ) -> float:
        """Calcula nível de confiança da análise."""
        if not text:
            return 0.3

        items_ok = sum(1 for c in checklist_tec + checklist_jur if c.status == "ok")
        total = len(checklist_tec) + len(checklist_jur)

        if total == 0:
            return 0.5

        return 0.5 + (items_ok / total) * 0.5


async def create_analyst_agent() -> AnalystAgent:
    """Factory function para criar AnalystAgent."""
    return AnalystAgent()

"""Schemas canônicos do Núcleo Licitações (Pydantic v2)."""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .enums import (
    Modalidade,
    Situacao,
    Prioridade,
    NivelRisco,
    TipoMudanca,
    StatusFluxo,
)


class SourceRef(BaseModel):
    """Referência rastreável de origem de dados."""

    source: str = Field(..., description="Identificador da fonte (ex: pncp, comprasnet)")
    url: str = Field(..., description="URL de origem do dado")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = Field(default=None, description="Hash do conteúdo (SHA256)")


class AttachmentRef(BaseModel):
    """Referência a anexo de edital."""

    filename: str
    url: str
    size_bytes: int | None = None
    content_type: str | None = None
    content_hash: str | None = None


class LicitacaoItem(BaseModel):
    """Item de licitação normalizado (schema canônico)."""

    id: str | None = Field(default=None, description="ID interno (gerado após persistência)")
    external_id: str = Field(..., description="ID no portal de origem")
    source: str = Field(..., description="Portal de origem (pncp, comprasnet, etc)")

    objeto: str = Field(..., description="Descrição do objeto da licitação")
    orgao: str = Field(..., description="Nome do órgão licitante")
    uf: str = Field(..., max_length=2, description="UF do órgão")
    municipio: str | None = Field(default=None, description="Município do órgão")

    modalidade: Modalidade = Field(default=Modalidade.OUTRO)
    situacao: Situacao = Field(default=Situacao.DESCONHECIDA)

    valor_estimado: float | None = Field(default=None, ge=0)
    data_publicacao: datetime | None = None
    data_abertura: datetime | None = None
    data_encerramento: datetime | None = None

    url_edital: str | None = None
    anexos: list[AttachmentRef] = Field(default_factory=list)

    sources: list[SourceRef] = Field(
        default_factory=list,
        min_length=1,
        description="Pelo menos uma fonte é obrigatória",
    )

    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Dados brutos originais (para debug/auditoria)",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("uf")
    @classmethod
    def uf_upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("sources", mode="before")
    @classmethod
    def ensure_sources_list(cls, v):
        if v is None:
            return []
        return v


class ChangeEvent(BaseModel):
    """Evento de mudança detectada em uma licitação."""

    licitacao_id: str = Field(..., description="ID da licitação afetada")
    tipo: TipoMudanca
    campo: str | None = Field(default=None, description="Campo que mudou (ex: data_abertura)")
    valor_anterior: str | None = None
    valor_novo: str | None = None
    detectado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fonte: SourceRef | None = None
    descricao: str | None = None


class RiscoIdentificado(BaseModel):
    """Risco identificado durante triagem ou análise."""

    tipo: str = Field(..., description="Tipo do risco (ex: prazo_curto, exigencia_restritiva)")
    nivel: NivelRisco
    descricao: str
    evidencia: str | None = Field(default=None, description="Trecho do edital que evidencia o risco")
    mitigacao: str | None = Field(default=None, description="Sugestão de mitigação")


class TriageScore(BaseModel):
    """Resultado da triagem de uma licitação."""

    licitacao_id: str
    score: float = Field(..., ge=0, le=1, description="Score calculado (0-1)")
    prioridade: Prioridade

    aderencia_portfolio: float = Field(default=0, ge=0, le=1)
    regiao_estrategica: float = Field(default=0, ge=0, le=1)
    valor_normalizado: float = Field(default=0, ge=0, le=1)
    prazo_normalizado: float = Field(default=0, ge=0, le=1)
    barreiras_normalizado: float = Field(default=0, ge=0, le=1)

    riscos_preliminares: list[RiscoIdentificado] = Field(default_factory=list)
    motivos: list[str] = Field(default_factory=list, description="Justificativas da classificação")

    triado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources: list[SourceRef] = Field(default_factory=list)


class ChecklistItem(BaseModel):
    """Item de checklist para análise."""

    item: str
    status: str = Field(default="pendente", description="pendente, ok, alerta, falha")
    observacao: str | None = None
    evidencia: str | None = None


class AnalysisPack(BaseModel):
    """Pacote de análise completa de uma licitação."""

    licitacao_id: str
    resumo_executivo: str = Field(..., description="Resumo para tomada de decisão")

    pontos_atencao: list[str] = Field(default_factory=list)
    riscos: list[RiscoIdentificado] = Field(default_factory=list)
    oportunidades: list[str] = Field(default_factory=list)

    checklist_tecnico: list[ChecklistItem] = Field(default_factory=list)
    checklist_juridico: list[ChecklistItem] = Field(default_factory=list)

    recomendacao: str | None = Field(
        default=None,
        description="Recomendação final (participar, não participar, analisar mais)",
    )

    confianca: float = Field(default=0.5, ge=0, le=1, description="Nível de confiança da análise")
    aviso_revisao: str = Field(
        default="Esta análise é assistência automatizada. Revisão humana obrigatória.",
        description="Aviso legal obrigatório",
    )

    analisado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources: list[SourceRef] = Field(default_factory=list)
    evidences: list[str] = Field(default_factory=list, description="Trechos do edital citados")


class FlowConfig(BaseModel):
    """Configuração de execução de um fluxo."""

    janela_dias: int = Field(default=7, ge=1, le=90, description="Janela de busca em dias")
    limite_itens: int = Field(default=100, ge=1, le=500)
    prazo_min_dias: int = Field(default=3, ge=0, description="Prazo mínimo para considerar")
    limite_risco: NivelRisco = Field(default=NivelRisco.ALTO)

    ufs: list[str] = Field(default_factory=list, description="UFs para filtrar (vazio = todas)")
    municipios: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(
        default_factory=lambda: ["dengue", "arbovirose", "drone", "geotecnologia"],
    )
    modalidades: list[Modalidade] = Field(
        default_factory=lambda: [Modalidade.PREGAO_ELETRONICO, Modalidade.CONCORRENCIA],
    )


class FlowResult(BaseModel):
    """Resultado wrapper de execução de fluxo (always-valid state)."""

    status: StatusFluxo = Field(default=StatusFluxo.INIT)
    run_id: str | None = Field(default=None, description="ID único da execução")

    payload_json: str = Field(
        default="{}",
        description="Payload serializado (referência ao artefato ou dados inline)",
    )

    items_processed: int = Field(default=0)
    items_p0: int = Field(default=0)
    items_p1: int = Field(default=0)

    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None

    @classmethod
    def init_result(cls, run_id: str) -> "FlowResult":
        """Cria um resultado inicializado (padrão para Start node)."""
        return cls(
            status=StatusFluxo.INIT,
            run_id=run_id,
            started_at=datetime.now(timezone.utc),
        )

    def mark_success(self) -> "FlowResult":
        """Marca o resultado como sucesso."""
        self.status = StatusFluxo.SUCCESS
        self.finished_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        return self

    def mark_error(self, error: str) -> "FlowResult":
        """Marca o resultado como erro."""
        self.status = StatusFluxo.ERROR
        self.errors.append(error)
        self.finished_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        return self

    def add_warning(self, warning: str) -> "FlowResult":
        """Adiciona um warning (não muda status)."""
        self.warnings.append(warning)
        return self

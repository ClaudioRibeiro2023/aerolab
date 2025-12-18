"""Models para o workflow licitacoes_monitor."""

from datetime import date, datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


class LicitacoesMonitorInput(BaseModel):
    """Schema de entrada do workflow."""

    fonte: Literal["pncp", "diarios_oficiais", "portais"] = Field(
        default="pncp",
        description="Fonte de dados para coleta",
    )
    termo_busca: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Termo principal de busca",
    )
    uf: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}$",
        description="Estado (sigla UF)",
    )
    municipio: str | None = Field(
        default=None,
        max_length=100,
        description="Município específico",
    )
    periodo_inicio: date | None = Field(
        default=None,
        description="Data início do período",
    )
    periodo_fim: date | None = Field(
        default=None,
        description="Data fim do período",
    )
    palavras_chave: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Palavras-chave adicionais",
    )
    modo_execucao: Literal["one_shot", "monitor"] = Field(
        default="one_shot",
        description="Modo de execução",
    )


class ItemEncontrado(BaseModel):
    """Item de licitação encontrado."""

    external_id: str
    fonte: str
    objeto: str
    orgao: str
    uf: str
    valor_estimado: float | None = None
    data_abertura: str | None = None


class TriagemScore(BaseModel):
    """Score de triagem."""

    licitacao_id: str
    score: float
    prioridade: str
    motivos: list[str] = Field(default_factory=list)


class TriagemResult(BaseModel):
    """Resultado da triagem."""

    total: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    scores: list[TriagemScore] = Field(default_factory=list)


class AnaliseJuridica(BaseModel):
    """Análise jurídica."""

    artigos_relevantes: list[dict[str, Any]] = Field(default_factory=list)
    checklist_habilitacao: list[dict[str, Any]] = Field(default_factory=list)
    riscos: list[dict[str, Any]] = Field(default_factory=list)
    conformidade: bool = True


class Evidencia(BaseModel):
    """Evidência coletada."""

    tipo: str
    url: str
    descricao: str


class Recomendacao(BaseModel):
    """Recomendação de ação."""

    licitacao_id: str
    acao: Literal["participar", "analisar_mais", "descartar"]
    justificativa: str
    confianca: float


class Alerta(BaseModel):
    """Alerta P0/P1."""

    prioridade: Literal["P0", "P1"]
    licitacao_id: str
    mensagem: str
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RunMetadata(BaseModel):
    """Metadados da execução."""

    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0


class LicitacoesMonitorResult(BaseModel):
    """Schema de resultado do workflow."""

    status: Literal["init", "running", "success", "error", "partial"] = "init"
    payload_json: str = "{}"
    errors: list[str] = Field(default_factory=list)
    runs: list[dict[str, Any]] = Field(default_factory=list)
    itens_encontrados: list[ItemEncontrado] = Field(default_factory=list)
    triagem: TriagemResult = Field(default_factory=TriagemResult)
    analise_juridica: AnaliseJuridica = Field(default_factory=AnaliseJuridica)
    evidencias: list[Evidencia] = Field(default_factory=list)
    recomendacoes: list[Recomendacao] = Field(default_factory=list)
    alertas: list[Alerta] = Field(default_factory=list)
    export_json: str = ""
    metadata: RunMetadata | None = None

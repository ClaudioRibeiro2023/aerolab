"""Enums canônicos do Núcleo Licitações."""

from enum import Enum


class Modalidade(str, Enum):
    """Modalidades de licitação conforme Lei 14.133/2021."""

    PREGAO_ELETRONICO = "pregao_eletronico"
    PREGAO_PRESENCIAL = "pregao_presencial"
    CONCORRENCIA = "concorrencia"
    CONCURSO = "concurso"
    LEILAO = "leilao"
    DIALOGO_COMPETITIVO = "dialogo_competitivo"
    DISPENSA = "dispensa"
    INEXIGIBILIDADE = "inexigibilidade"
    CHAMAMENTO_PUBLICO = "chamamento_publico"
    OUTRO = "outro"


class Situacao(str, Enum):
    """Status da licitação no portal de origem."""

    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    SUSPENSA = "suspensa"
    ENCERRADA = "encerrada"
    REVOGADA = "revogada"
    ANULADA = "anulada"
    DESERTA = "deserta"
    FRACASSADA = "fracassada"
    HOMOLOGADA = "homologada"
    ADJUDICADA = "adjudicada"
    DESCONHECIDA = "desconhecida"


class Prioridade(str, Enum):
    """Classificação de prioridade após triagem."""

    P0 = "P0"  # Crítico - ação imediata
    P1 = "P1"  # Alta - analisar hoje
    P2 = "P2"  # Média - analisar esta semana
    P3 = "P3"  # Baixa - arquivar/monitorar


class NivelRisco(str, Enum):
    """Classificação de risco identificado."""

    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


class TipoMudanca(str, Enum):
    """Tipo de mudança detectada em uma licitação."""

    PRAZO_ALTERADO = "prazo_alterado"
    ANEXO_ADICIONADO = "anexo_adicionado"
    ANEXO_REMOVIDO = "anexo_removido"
    STATUS_ALTERADO = "status_alterado"
    VALOR_ALTERADO = "valor_alterado"
    ESCLARECIMENTO = "esclarecimento"
    IMPUGNACAO = "impugnacao"
    OUTRO = "outro"


class StatusFluxo(str, Enum):
    """Status de execução de um fluxo."""

    INIT = "init"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"  # Concluiu com erros não-críticos
    ERROR = "error"
    TIMEOUT = "timeout"

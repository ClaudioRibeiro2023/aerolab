"""Serviço RAG Jurídico para o Núcleo Licitações.

Permite consultas à base de conhecimento jurídico:
- Lei 14.133/2021 (Nova Lei de Licitações)
- Checklists de conformidade
- Padrões internos
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import logging
import re

logger = logging.getLogger(__name__)

COLLECTION_LEI_14133 = "licitacoes_lei_14133"
COLLECTION_CHECKLISTS = "licitacoes_checklists"

LEI_14133_CAPITULOS = {
    "cap1": {
        "titulo": "Disposições Preliminares",
        "artigos": "1-4",
        "resumo": "Define objeto, princípios e definições da lei de licitações.",
    },
    "cap2": {
        "titulo": "Das Modalidades de Licitação",
        "artigos": "28-32",
        "resumo": "Pregão, concorrência, concurso, leilão e diálogo competitivo.",
    },
    "cap3": {
        "titulo": "Dos Agentes Públicos",
        "artigos": "7-10",
        "resumo": "Responsabilidades e vedações dos agentes de contratação.",
    },
    "cap4": {
        "titulo": "Do Procedimento",
        "artigos": "17-27",
        "resumo": "Fases da licitação: preparatória, divulgação, proposta, julgamento.",
    },
    "cap5": {
        "titulo": "Da Habilitação",
        "artigos": "62-70",
        "resumo": "Requisitos de habilitação jurídica, técnica, fiscal e econômica.",
    },
    "cap6": {
        "titulo": "Dos Contratos",
        "artigos": "89-114",
        "resumo": "Formalização, execução, alteração e extinção de contratos.",
    },
    "cap7": {
        "titulo": "Das Sanções",
        "artigos": "155-163",
        "resumo": "Infrações e sanções administrativas.",
    },
}

CHECKLIST_HABILITACAO = [
    {
        "item": "Habilitação Jurídica",
        "requisitos": [
            "Ato constitutivo, estatuto ou contrato social",
            "Registro comercial (empresário individual)",
            "Decreto de autorização (empresa estrangeira)",
        ],
        "base_legal": "Art. 66 da Lei 14.133/2021",
    },
    {
        "item": "Regularidade Fiscal e Trabalhista",
        "requisitos": [
            "CNPJ",
            "Inscrição estadual e/ou municipal",
            "Certidão negativa de débitos federais",
            "Certidão negativa de débitos estaduais",
            "Certidão negativa de débitos municipais",
            "Certidão de regularidade FGTS",
            "Certidão negativa de débitos trabalhistas (CNDT)",
        ],
        "base_legal": "Art. 68 da Lei 14.133/2021",
    },
    {
        "item": "Qualificação Técnica",
        "requisitos": [
            "Registro ou inscrição em entidade profissional",
            "Atestados de capacidade técnica",
            "Indicação de equipe técnica",
            "Declaração de instalações e aparelhamento",
        ],
        "base_legal": "Art. 67 da Lei 14.133/2021",
    },
    {
        "item": "Qualificação Econômico-Financeira",
        "requisitos": [
            "Balanço patrimonial e demonstrações contábeis",
            "Certidão negativa de falência e recuperação judicial",
            "Índices contábeis (liquidez, solvência, endividamento)",
        ],
        "base_legal": "Art. 69 da Lei 14.133/2021",
    },
]


@dataclass
class RagResult:
    """Resultado de uma consulta RAG."""

    query: str
    results: list[dict[str, Any]]
    sources: list[str]
    confidence: float
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LegalReference:
    """Referência legal encontrada."""

    artigo: str
    texto: str
    capitulo: str
    relevancia: float


class RagJuridicoService:
    """
    Serviço de RAG para consultas jurídicas em licitações.

    Funcionalidades:
    - Busca semântica na Lei 14.133/2021
    - Consulta a checklists de conformidade
    - Identificação de artigos relevantes
    """

    def __init__(self, rag_service: Any = None):
        self.rag_service = rag_service
        self._initialized = False

    async def initialize(self) -> bool:
        """Inicializa o serviço RAG (carrega coleções)."""
        if self._initialized:
            return True

        try:
            if self.rag_service:
                self.rag_service.get_collection(COLLECTION_LEI_14133)
                self.rag_service.get_collection(COLLECTION_CHECKLISTS)

            self._initialized = True
            logger.info("RAG Jurídico initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG Jurídico: {e}")
            return False

    def query_lei_14133(self, query: str, top_k: int = 5) -> RagResult:
        """
        Consulta a base de conhecimento da Lei 14.133/2021.

        Args:
            query: Pergunta ou termo de busca
            top_k: Número máximo de resultados

        Returns:
            RagResult com trechos relevantes
        """
        results: list[dict[str, Any]] = []
        sources: list[str] = []

        query_lower = query.lower()
        for cap_id, cap_info in LEI_14133_CAPITULOS.items():
            titulo_lower = cap_info["titulo"].lower()
            resumo_lower = cap_info["resumo"].lower()

            relevance = 0.0
            if any(word in titulo_lower for word in query_lower.split()):
                relevance += 0.5
            if any(word in resumo_lower for word in query_lower.split()):
                relevance += 0.3

            if relevance > 0:
                results.append({
                    "capitulo": cap_info["titulo"],
                    "artigos": cap_info["artigos"],
                    "resumo": cap_info["resumo"],
                    "relevancia": relevance,
                })
                sources.append(f"Lei 14.133/2021, Arts. {cap_info['artigos']}")

        results.sort(key=lambda x: x.get("relevancia", 0), reverse=True)
        results = results[:top_k]

        if self.rag_service:
            try:
                rag_results = self.rag_service.query(
                    collection=COLLECTION_LEI_14133,
                    query_text=query,
                    top_k=top_k,
                )
                for r in rag_results:
                    results.append({
                        "texto": r.get("text", ""),
                        "metadata": r.get("metadata", {}),
                        "relevancia": 0.8,
                    })
                    if r.get("metadata", {}).get("source"):
                        sources.append(r["metadata"]["source"])
            except Exception as e:
                logger.warning(f"RAG query failed, using fallback: {e}")

        confidence = min(len(results) / top_k, 1.0) if results else 0.0

        return RagResult(
            query=query,
            results=results,
            sources=list(set(sources)),
            confidence=confidence,
        )

    def get_checklist_habilitacao(self) -> list[dict[str, Any]]:
        """Retorna checklist de habilitação."""
        return CHECKLIST_HABILITACAO

    def query_checklist(self, query: str) -> list[dict[str, Any]]:
        """
        Busca em checklists por termo.

        Args:
            query: Termo de busca

        Returns:
            Lista de itens de checklist relevantes
        """
        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        for item in CHECKLIST_HABILITACAO:
            item_text = f"{item['item']} {' '.join(item['requisitos'])}".lower()
            if any(word in item_text for word in query_lower.split()):
                results.append(item)

        return results

    def identify_artigos_relevantes(self, texto: str) -> list[LegalReference]:
        """
        Identifica artigos da Lei 14.133/2021 relevantes para um texto.

        Args:
            texto: Texto do edital ou documento

        Returns:
            Lista de referências legais relevantes
        """
        references: list[LegalReference] = []
        texto_lower = texto.lower()

        keywords_map = {
            "pregão": ("cap2", "Art. 28-29", 0.9),
            "concorrência": ("cap2", "Art. 28-29", 0.9),
            "habilitação": ("cap5", "Art. 62-70", 0.85),
            "técnica": ("cap5", "Art. 67", 0.8),
            "fiscal": ("cap5", "Art. 68", 0.8),
            "contrato": ("cap6", "Art. 89-114", 0.75),
            "sanção": ("cap7", "Art. 155-163", 0.7),
            "penalidade": ("cap7", "Art. 155-163", 0.7),
            "procedimento": ("cap4", "Art. 17-27", 0.7),
            "edital": ("cap4", "Art. 25", 0.8),
            "proposta": ("cap4", "Art. 17-27", 0.75),
            "julgamento": ("cap4", "Art. 17-27", 0.75),
        }

        for keyword, (cap_id, artigo, relevancia) in keywords_map.items():
            if keyword in texto_lower:
                cap_info = LEI_14133_CAPITULOS.get(cap_id, {})
                references.append(LegalReference(
                    artigo=artigo,
                    texto=cap_info.get("resumo", ""),
                    capitulo=cap_info.get("titulo", ""),
                    relevancia=relevancia,
                ))

        seen = set()
        unique_refs = []
        for ref in references:
            key = ref.artigo
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)

        unique_refs.sort(key=lambda x: x.relevancia, reverse=True)
        return unique_refs[:5]

    def get_contexto_juridico(self, licitacao_objeto: str) -> dict[str, Any]:
        """
        Gera contexto jurídico para análise de uma licitação.

        Args:
            licitacao_objeto: Objeto da licitação

        Returns:
            Contexto com artigos e checklists relevantes
        """
        artigos = self.identify_artigos_relevantes(licitacao_objeto)
        checklist = self.get_checklist_habilitacao()
        query_result = self.query_lei_14133(licitacao_objeto, top_k=3)

        return {
            "artigos_relevantes": [
                {
                    "artigo": ref.artigo,
                    "capitulo": ref.capitulo,
                    "resumo": ref.texto,
                    "relevancia": ref.relevancia,
                }
                for ref in artigos
            ],
            "checklist_habilitacao": checklist,
            "consulta_rag": {
                "query": query_result.query,
                "results": query_result.results[:3],
                "sources": query_result.sources,
                "confidence": query_result.confidence,
            },
            "aviso": "Consulta automatizada. Não substitui análise jurídica profissional.",
        }


_rag_juridico: RagJuridicoService | None = None


def get_rag_juridico() -> RagJuridicoService:
    """Obtém instância singleton do serviço RAG Jurídico."""
    global _rag_juridico
    if _rag_juridico is None:
        try:
            from src.rag import get_rag_service
            rag = get_rag_service()
            _rag_juridico = RagJuridicoService(rag_service=rag)
        except Exception as e:
            logger.warning(f"RAG service not available, using fallback: {e}")
            _rag_juridico = RagJuridicoService(rag_service=None)
    return _rag_juridico

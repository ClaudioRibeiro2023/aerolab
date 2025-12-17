"""Testes do RAG Jurídico para o Núcleo Licitações."""

import pytest
from ..services.rag_juridico import (
    RagJuridicoService,
    get_rag_juridico,
    CHECKLIST_HABILITACAO,
    LEI_14133_CAPITULOS,
)


class TestRagJuridicoService:
    """Testes para RagJuridicoService."""

    @pytest.fixture
    def service(self):
        return RagJuridicoService(rag_service=None)

    def test_query_lei_14133_modalidades(self, service):
        """Busca por modalidades deve retornar capítulo 2."""
        result = service.query_lei_14133("modalidades de licitação pregão")

        assert result.query == "modalidades de licitação pregão"
        assert len(result.results) > 0
        assert result.confidence > 0

        capitulos = [r.get("capitulo", "") for r in result.results]
        assert any("Modalidades" in c for c in capitulos)

    def test_query_lei_14133_habilitacao(self, service):
        """Busca por habilitação deve retornar capítulo 5."""
        result = service.query_lei_14133("habilitação técnica fiscal")

        assert len(result.results) > 0
        capitulos = [r.get("capitulo", "") for r in result.results]
        assert any("Habilitação" in c for c in capitulos)

    def test_query_lei_14133_contratos(self, service):
        """Busca por contratos deve retornar capítulo 6."""
        result = service.query_lei_14133("contrato execução")

        assert len(result.results) > 0
        capitulos = [r.get("capitulo", "") for r in result.results]
        assert any("Contrato" in c for c in capitulos)

    def test_query_lei_14133_empty(self, service):
        """Busca sem matches deve retornar lista vazia."""
        result = service.query_lei_14133("xyz123abc")

        assert result.confidence == 0.0

    def test_get_checklist_habilitacao(self, service):
        """Checklist de habilitação deve ter 4 itens principais."""
        checklist = service.get_checklist_habilitacao()

        assert len(checklist) == 4
        assert any(c["item"] == "Habilitação Jurídica" for c in checklist)
        assert any(c["item"] == "Qualificação Técnica" for c in checklist)
        assert any(c["item"] == "Regularidade Fiscal e Trabalhista" for c in checklist)
        assert any(c["item"] == "Qualificação Econômico-Financeira" for c in checklist)

    def test_query_checklist_tecnica(self, service):
        """Busca por técnica deve retornar item de qualificação técnica."""
        results = service.query_checklist("técnica atestado")

        assert len(results) > 0
        assert any("Técnica" in r["item"] for r in results)

    def test_query_checklist_fiscal(self, service):
        """Busca por fiscal deve retornar item de regularidade fiscal."""
        results = service.query_checklist("fiscal CNPJ certidão")

        assert len(results) > 0
        assert any("Fiscal" in r["item"] for r in results)

    def test_identify_artigos_pregao(self, service):
        """Texto sobre pregão deve identificar artigos de modalidades."""
        texto = "Pregão eletrônico para aquisição de equipamentos"
        refs = service.identify_artigos_relevantes(texto)

        assert len(refs) > 0
        assert any("28" in r.artigo for r in refs)

    def test_identify_artigos_habilitacao(self, service):
        """Texto sobre habilitação deve identificar artigos 62-70."""
        texto = "Habilitação técnica e fiscal do licitante"
        refs = service.identify_artigos_relevantes(texto)

        assert len(refs) > 0
        artigos = " ".join(r.artigo for r in refs)
        assert "67" in artigos or "68" in artigos or "62-70" in artigos

    def test_identify_artigos_contrato(self, service):
        """Texto sobre contrato deve identificar artigos 89-114."""
        texto = "Formalização e execução do contrato"
        refs = service.identify_artigos_relevantes(texto)

        assert len(refs) > 0
        assert any("89" in r.artigo or "114" in r.artigo for r in refs)

    def test_identify_artigos_unique(self, service):
        """Artigos identificados devem ser únicos."""
        texto = "Pregão eletrônico pregão presencial modalidade pregão"
        refs = service.identify_artigos_relevantes(texto)

        artigos = [r.artigo for r in refs]
        assert len(artigos) == len(set(artigos)), "Artigos duplicados encontrados"

    def test_get_contexto_juridico(self, service):
        """Contexto jurídico deve conter todos os elementos."""
        contexto = service.get_contexto_juridico(
            "Contratação de serviços de drone para mapeamento"
        )

        assert "artigos_relevantes" in contexto
        assert "checklist_habilitacao" in contexto
        assert "consulta_rag" in contexto
        assert "aviso" in contexto

        assert len(contexto["checklist_habilitacao"]) == 4
        assert "análise jurídica" in contexto["aviso"].lower()

    def test_get_contexto_juridico_drone(self, service):
        """Contexto para drones deve ter artigos relevantes."""
        contexto = service.get_contexto_juridico(
            "Pregão eletrônico para aquisição de drones com habilitação técnica"
        )

        assert len(contexto["artigos_relevantes"]) > 0
        tipos = [a["capitulo"] for a in contexto["artigos_relevantes"]]
        assert any("Modalidades" in t or "Habilitação" in t for t in tipos)


class TestChecklistHabilitacao:
    """Testes para a constante CHECKLIST_HABILITACAO."""

    def test_all_items_have_requisitos(self):
        """Todos os itens devem ter requisitos."""
        for item in CHECKLIST_HABILITACAO:
            assert "requisitos" in item
            assert len(item["requisitos"]) > 0

    def test_all_items_have_base_legal(self):
        """Todos os itens devem ter base legal."""
        for item in CHECKLIST_HABILITACAO:
            assert "base_legal" in item
            assert "14.133" in item["base_legal"]

    def test_fiscal_has_cndt(self):
        """Regularidade fiscal deve incluir CNDT."""
        fiscal = next(
            (c for c in CHECKLIST_HABILITACAO if "Fiscal" in c["item"]), None
        )
        assert fiscal is not None
        requisitos_text = " ".join(fiscal["requisitos"])
        assert "CNDT" in requisitos_text or "trabalhist" in requisitos_text.lower()


class TestLei14133Capitulos:
    """Testes para a constante LEI_14133_CAPITULOS."""

    def test_has_all_main_chapters(self):
        """Deve ter os capítulos principais."""
        assert len(LEI_14133_CAPITULOS) >= 7

    def test_all_chapters_have_titulo(self):
        """Todos os capítulos devem ter título."""
        for cap_id, cap_info in LEI_14133_CAPITULOS.items():
            assert "titulo" in cap_info
            assert len(cap_info["titulo"]) > 0

    def test_all_chapters_have_artigos(self):
        """Todos os capítulos devem ter artigos."""
        for cap_id, cap_info in LEI_14133_CAPITULOS.items():
            assert "artigos" in cap_info
            assert "-" in cap_info["artigos"] or cap_info["artigos"].isdigit()

    def test_all_chapters_have_resumo(self):
        """Todos os capítulos devem ter resumo."""
        for cap_id, cap_info in LEI_14133_CAPITULOS.items():
            assert "resumo" in cap_info
            assert len(cap_info["resumo"]) > 10


class TestGetRagJuridico:
    """Testes para a função get_rag_juridico."""

    def test_returns_service_instance(self):
        """Deve retornar uma instância de RagJuridicoService."""
        service = get_rag_juridico()
        assert isinstance(service, RagJuridicoService)

    def test_returns_same_instance(self):
        """Deve retornar a mesma instância (singleton)."""
        service1 = get_rag_juridico()
        service2 = get_rag_juridico()
        assert service1 is service2

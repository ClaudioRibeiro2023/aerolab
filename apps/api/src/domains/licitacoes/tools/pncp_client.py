"""Cliente para API do Portal Nacional de Contratações Públicas (PNCP)."""

import httpx
from datetime import datetime, timezone, timedelta
from typing import Any
import logging

from ..models import (
    LicitacaoItem,
    AttachmentRef,
    SourceRef,
    Modalidade,
    Situacao,
)

logger = logging.getLogger(__name__)

PNCP_BASE_URL = "https://pncp.gov.br/api/consulta/v1"
DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRIES = 2


class PNCPClientError(Exception):
    """Erro genérico do cliente PNCP."""
    pass


class PNCPClient:
    """Cliente para consulta à API do PNCP."""

    def __init__(
        self,
        base_url: str = PNCP_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise PNCPClientError("Client not initialized. Use 'async with PNCPClient()' context.")
        return self._client

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Faz requisição com retry."""
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                response = await self.client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"PNCP timeout (attempt {attempt + 1}/{self.retries + 1}): {e}")
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500:
                    logger.warning(f"PNCP server error (attempt {attempt + 1}): {e}")
                else:
                    raise PNCPClientError(f"PNCP API error: {e.response.status_code}") from e
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"PNCP request error (attempt {attempt + 1}): {e}")

        raise PNCPClientError(f"PNCP request failed after {self.retries + 1} attempts") from last_error

    async def search(
        self,
        keywords: list[str] | None = None,
        ufs: list[str] | None = None,
        modalidades: list[Modalidade] | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
        pagina: int = 1,
        tam_pagina: int = 50,
    ) -> list[LicitacaoItem]:
        """
        Busca licitações no PNCP.

        Args:
            keywords: Palavras-chave para busca no objeto
            ufs: UFs para filtrar
            modalidades: Modalidades de licitação
            data_inicio: Data inicial de publicação
            data_fim: Data final de publicação
            pagina: Número da página
            tam_pagina: Tamanho da página (max 500)

        Returns:
            Lista de LicitacaoItem normalizados
        """
        params: dict[str, Any] = {
            "pagina": pagina,
            "tamanhoPagina": min(tam_pagina, 500),
        }

        if keywords:
            params["q"] = " ".join(keywords)

        if ufs:
            params["uf"] = ",".join(ufs)

        if data_inicio:
            params["dataInicial"] = data_inicio.strftime("%Y-%m-%d")

        if data_fim:
            params["dataFinal"] = data_fim.strftime("%Y-%m-%d")

        if modalidades:
            modalidade_map = {
                Modalidade.PREGAO_ELETRONICO: "6",
                Modalidade.CONCORRENCIA: "1",
                Modalidade.DISPENSA: "8",
                Modalidade.INEXIGIBILIDADE: "9",
            }
            codes = [modalidade_map.get(m) for m in modalidades if m in modalidade_map]
            if codes:
                params["modalidade"] = ",".join(filter(None, codes))

        try:
            data = await self._request("GET", "/contratacoes/publicacao", params=params)
        except PNCPClientError:
            logger.error("Failed to search PNCP")
            return []

        items = []
        for raw in data.get("data", []):
            try:
                item = self._normalize_item(raw)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to normalize PNCP item: {e}")

        return items

    async def get_detail(self, external_id: str) -> LicitacaoItem | None:
        """
        Obtém detalhes de uma licitação pelo ID externo.

        Args:
            external_id: ID no formato "cnpj-ano-sequencial"

        Returns:
            LicitacaoItem ou None se não encontrado
        """
        try:
            parts = external_id.split("-")
            if len(parts) < 3:
                raise ValueError(f"Invalid external_id format: {external_id}")

            cnpj = parts[0]
            ano = parts[1]
            sequencial = parts[2]

            data = await self._request(
                "GET",
                f"/orgaos/{cnpj}/compras/{ano}/{sequencial}",
            )
            return self._normalize_item(data)

        except PNCPClientError as e:
            logger.error(f"Failed to get PNCP detail for {external_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing PNCP detail for {external_id}: {e}")
            return None

    async def list_attachments(self, external_id: str) -> list[AttachmentRef]:
        """
        Lista anexos de uma licitação.

        Args:
            external_id: ID no formato "cnpj-ano-sequencial"

        Returns:
            Lista de AttachmentRef
        """
        try:
            parts = external_id.split("-")
            if len(parts) < 3:
                return []

            cnpj = parts[0]
            ano = parts[1]
            sequencial = parts[2]

            data = await self._request(
                "GET",
                f"/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos",
            )

            attachments = []
            for raw in data.get("data", data if isinstance(data, list) else []):
                try:
                    attachment = AttachmentRef(
                        filename=raw.get("nomeArquivo", "unknown"),
                        url=raw.get("url", ""),
                        size_bytes=raw.get("tamanho"),
                        content_type=raw.get("tipoArquivo"),
                    )
                    attachments.append(attachment)
                except Exception as e:
                    logger.warning(f"Failed to parse attachment: {e}")

            return attachments

        except PNCPClientError as e:
            logger.warning(f"Failed to list attachments for {external_id}: {e}")
            return []

    def _normalize_item(self, raw: dict[str, Any]) -> LicitacaoItem:
        """Normaliza dados brutos do PNCP para LicitacaoItem."""
        orgao_data = raw.get("orgaoEntidade", {})
        cnpj = orgao_data.get("cnpj", raw.get("cnpjOrgao", ""))
        ano = raw.get("anoCompra", "")
        seq = raw.get("sequencialCompra", "")

        external_id = f"{cnpj}-{ano}-{seq}" if cnpj and ano and seq else raw.get("id", str(hash(str(raw))))

        modalidade = self._map_modalidade(raw.get("modalidadeId"))
        situacao = self._map_situacao(raw.get("situacaoCompraId"))

        data_publicacao = self._parse_date(raw.get("dataPublicacaoPncp"))
        data_abertura = self._parse_date(raw.get("dataAberturaProposta"))
        data_encerramento = self._parse_date(raw.get("dataEncerramentoProposta"))

        url_edital = raw.get("linkSistemaOrigem") or f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"

        source_url = f"{self.base_url}/orgaos/{cnpj}/compras/{ano}/{seq}" if cnpj else self.base_url

        return LicitacaoItem(
            external_id=external_id,
            source="pncp",
            objeto=raw.get("objetoCompra", raw.get("descricao", "Sem descrição")),
            orgao=orgao_data.get("razaoSocial", raw.get("nomeOrgao", "Órgão não identificado")),
            uf=orgao_data.get("uf", raw.get("uf", "XX")),
            municipio=orgao_data.get("municipio", {}).get("nome"),
            modalidade=modalidade,
            situacao=situacao,
            valor_estimado=raw.get("valorTotalEstimado"),
            data_publicacao=data_publicacao,
            data_abertura=data_abertura,
            data_encerramento=data_encerramento,
            url_edital=url_edital,
            sources=[
                SourceRef(
                    source="pncp",
                    url=source_url,
                    fetched_at=datetime.now(timezone.utc),
                ),
            ],
            raw_data=raw,
        )

    def _map_modalidade(self, modalidade_id: int | str | None) -> Modalidade:
        """Mapeia ID de modalidade do PNCP para enum."""
        mapping = {
            1: Modalidade.CONCORRENCIA,
            2: Modalidade.CONCURSO,
            3: Modalidade.LEILAO,
            4: Modalidade.PREGAO_PRESENCIAL,
            5: Modalidade.PREGAO_PRESENCIAL,
            6: Modalidade.PREGAO_ELETRONICO,
            7: Modalidade.DIALOGO_COMPETITIVO,
            8: Modalidade.DISPENSA,
            9: Modalidade.INEXIGIBILIDADE,
        }
        try:
            return mapping.get(int(modalidade_id or 0), Modalidade.OUTRO)
        except (ValueError, TypeError):
            return Modalidade.OUTRO

    def _map_situacao(self, situacao_id: int | str | None) -> Situacao:
        """Mapeia ID de situação do PNCP para enum."""
        mapping = {
            1: Situacao.ABERTA,
            2: Situacao.EM_ANDAMENTO,
            3: Situacao.SUSPENSA,
            4: Situacao.ENCERRADA,
            5: Situacao.REVOGADA,
            6: Situacao.ANULADA,
            7: Situacao.DESERTA,
            8: Situacao.FRACASSADA,
            9: Situacao.HOMOLOGADA,
            10: Situacao.ADJUDICADA,
        }
        try:
            return mapping.get(int(situacao_id or 0), Situacao.DESCONHECIDA)
        except (ValueError, TypeError):
            return Situacao.DESCONHECIDA

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse de data do PNCP."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19] if "T" in date_str else date_str, fmt)
            except ValueError:
                continue

        return None


async def create_pncp_client() -> PNCPClient:
    """Factory function para criar cliente PNCP."""
    return PNCPClient()

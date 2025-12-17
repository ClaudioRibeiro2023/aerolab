"""
Classe base para ferramentas customizadas.

Todas as ferramentas de domínio devem herdar de BaseTool.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
import logging


logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Exceção para erros de ferramentas."""

    def __init__(self, message: str, tool_name: str = "", details: Optional[Dict] = None):
        self.message = message
        self.tool_name = tool_name
        self.details = details or {}
        super().__init__(message)


@dataclass
class ToolResult:
    """Resultado padronizado de uma ferramenta."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def ok(cls, data: Any, **metadata) -> "ToolResult":
        """Cria resultado de sucesso."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "ToolResult":
        """Cria resultado de falha."""
        return cls(success=False, error=error, metadata=metadata)


class BaseTool(ABC):
    """
    Classe base abstrata para todas as ferramentas.

    Ferramentas são componentes reutilizáveis que agentes podem usar
    para executar ações específicas (consultar APIs, processar dados, etc).

    Exemplo de implementação:
        class MyTool(BaseTool):
            name = "my_tool"
            description = "Faz algo útil"

            def _execute(self, param1: str, param2: int = 10) -> ToolResult:
                # Implementação
                return ToolResult.ok({"result": "..."})
    """

    # Metadados da ferramenta (sobrescrever nas subclasses)
    name: str = "base_tool"
    description: str = "Ferramenta base"
    version: str = "1.0.0"

    # Configurações
    requires_auth: bool = False
    rate_limited: bool = False
    timeout_seconds: int = 30

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa a ferramenta.

        Args:
            config: Configurações opcionais da ferramenta.
        """
        self.config = config or {}
        self._initialized = False
        self._setup()

    def _setup(self) -> None:
        """
        Setup inicial da ferramenta.
        Sobrescrever para inicialização customizada.
        """
        self._initialized = True

    @abstractmethod
    def _execute(self, **kwargs) -> ToolResult:
        """
        Executa a ferramenta.

        Args:
            **kwargs: Parâmetros específicos da ferramenta.

        Returns:
            ToolResult com o resultado da execução.
        """
        pass

    def run(self, **kwargs) -> ToolResult:
        """
        Executa a ferramenta com tratamento de erros.

        Args:
            **kwargs: Parâmetros para a ferramenta.

        Returns:
            ToolResult com o resultado.
        """
        try:
            logger.debug(f"Executando {self.name} com params: {kwargs}")
            result = self._execute(**kwargs)
            logger.debug(f"{self.name} retornou: success={result.success}")
            return result
        except ToolError as e:
            logger.error(f"ToolError em {self.name}: {e.message}")
            return ToolResult.fail(e.message, tool=self.name, details=e.details)
        except Exception as e:
            logger.exception(f"Erro inesperado em {self.name}")
            return ToolResult.fail(str(e), tool=self.name)

    def validate_params(self, **kwargs) -> Optional[str]:
        """
        Valida parâmetros antes da execução.

        Args:
            **kwargs: Parâmetros a validar.

        Returns:
            Mensagem de erro se inválido, None se válido.
        """
        return None

    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna o schema da ferramenta para documentação.

        Returns:
            Dicionário com metadados da ferramenta.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "requires_auth": self.requires_auth,
            "rate_limited": self.rate_limited,
            "timeout_seconds": self.timeout_seconds,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class ToolRegistry:
    """
    Registry de ferramentas disponíveis.

    Permite registrar e recuperar ferramentas por nome ou domínio.
    """

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._domains: Dict[str, List[str]] = {}

    def register(self, tool_class: Type[BaseTool], domain: str = "general") -> None:
        """
        Registra uma ferramenta.

        Args:
            tool_class: Classe da ferramenta.
            domain: Domínio da ferramenta (geo, finance, etc).
        """
        name = tool_class.name
        self._tools[name] = tool_class

        if domain not in self._domains:
            self._domains[domain] = []
        self._domains[domain].append(name)

        logger.info(f"Ferramenta registrada: {name} (domain={domain})")

    def get(self, name: str, config: Optional[Dict] = None) -> Optional[BaseTool]:
        """
        Obtém uma instância de ferramenta.

        Args:
            name: Nome da ferramenta.
            config: Configurações opcionais.

        Returns:
            Instância da ferramenta ou None.
        """
        tool_class = self._tools.get(name)
        if tool_class:
            return tool_class(config=config)
        return None

    def list_tools(self, domain: Optional[str] = None) -> List[str]:
        """
        Lista ferramentas disponíveis.

        Args:
            domain: Filtrar por domínio.

        Returns:
            Lista de nomes de ferramentas.
        """
        if domain:
            return self._domains.get(domain, [])
        return list(self._tools.keys())

    def list_domains(self) -> List[str]:
        """Lista domínios disponíveis."""
        return list(self._domains.keys())


# Registry global
_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Retorna o registry global de ferramentas."""
    return _registry


def register_tool(domain: str = "general"):
    """
    Decorator para registrar uma ferramenta.

    Exemplo:
        @register_tool(domain="geo")
        class MapboxTool(BaseTool):
            ...
    """

    def decorator(cls: Type[BaseTool]) -> Type[BaseTool]:
        _registry.register(cls, domain=domain)
        return cls

    return decorator

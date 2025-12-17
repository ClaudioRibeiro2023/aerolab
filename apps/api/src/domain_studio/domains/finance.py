"""Finance Domain - Stub implementation."""
from ..core.types import DomainType, DomainConfiguration
from ..core.domain_base import BaseDomain

class FinanceDomain(BaseDomain):
    @property
    def domain_type(self) -> DomainType:
        return DomainType.FINANCE
    
    def _get_default_config(self) -> DomainConfiguration:
        return DomainConfiguration(type=DomainType.FINANCE, name="Financeiro")
    
    def _register_agents(self) -> None:
        pass
    
    def _register_workflows(self) -> None:
        pass

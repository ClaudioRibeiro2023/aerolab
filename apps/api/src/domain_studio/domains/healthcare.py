"""Healthcare Domain - Stub implementation."""
from ..core.types import DomainType, DomainConfiguration
from ..core.domain_base import BaseDomain

class HealthcareDomain(BaseDomain):
    @property
    def domain_type(self) -> DomainType:
        return DomainType.HEALTHCARE
    
    def _get_default_config(self) -> DomainConfiguration:
        return DomainConfiguration(type=DomainType.HEALTHCARE, name="Saude")
    
    def _register_agents(self) -> None:
        pass
    
    def _register_workflows(self) -> None:
        pass

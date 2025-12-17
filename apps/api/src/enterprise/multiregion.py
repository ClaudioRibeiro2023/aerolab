"""
Multi-Region Manager - Deploy e Data Residency Multi-Região.

Gerencia deploy em múltiplas regiões com latência otimizada e compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import uuid
import random

from .types import (
    Region, RegionConfig, DataResidencyPolicy, TenantRegion
)


class RegionManager:
    """
    Gerenciador de regiões.
    
    Features:
    - Configuração de regiões
    - Health checks
    - Capacidade e alocação
    - Failover automático
    """
    
    def __init__(self):
        self._regions: Dict[Region, RegionConfig] = {}
        self._initialize_default_regions()
    
    def _initialize_default_regions(self) -> None:
        """Inicializa regiões padrão."""
        default_regions = [
            RegionConfig(
                region=Region.US_EAST_1,
                enabled=True,
                is_primary=True,
                api_endpoint="https://api-us-east-1.agno.ai",
                ws_endpoint="wss://ws-us-east-1.agno.ai",
                cdn_endpoint="https://cdn-us-east-1.agno.ai",
                cloud_provider="aws",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                max_tenants=5000,
                latency_map={
                    "us-west-2": 70,
                    "eu-west-1": 80,
                    "ap-northeast-1": 150,
                    "sa-east-1": 130,
                }
            ),
            RegionConfig(
                region=Region.EU_WEST_1,
                enabled=True,
                is_primary=False,
                api_endpoint="https://api-eu-west-1.agno.ai",
                ws_endpoint="wss://ws-eu-west-1.agno.ai",
                cdn_endpoint="https://cdn-eu-west-1.agno.ai",
                cloud_provider="aws",
                availability_zones=["eu-west-1a", "eu-west-1b", "eu-west-1c"],
                max_tenants=3000,
                latency_map={
                    "us-east-1": 80,
                    "eu-central-1": 15,
                    "ap-northeast-1": 200,
                }
            ),
            RegionConfig(
                region=Region.SA_EAST_1,
                enabled=True,
                is_primary=False,
                api_endpoint="https://api-sa-east-1.agno.ai",
                ws_endpoint="wss://ws-sa-east-1.agno.ai",
                cdn_endpoint="https://cdn-sa-east-1.agno.ai",
                cloud_provider="aws",
                availability_zones=["sa-east-1a", "sa-east-1b", "sa-east-1c"],
                max_tenants=2000,
                latency_map={
                    "us-east-1": 130,
                    "eu-west-1": 180,
                }
            ),
            RegionConfig(
                region=Region.AP_NORTHEAST_1,
                enabled=True,
                is_primary=False,
                api_endpoint="https://api-ap-northeast-1.agno.ai",
                ws_endpoint="wss://ws-ap-northeast-1.agno.ai",
                cdn_endpoint="https://cdn-ap-northeast-1.agno.ai",
                cloud_provider="aws",
                availability_zones=["ap-northeast-1a", "ap-northeast-1b", "ap-northeast-1c"],
                max_tenants=3000,
                latency_map={
                    "us-east-1": 150,
                    "ap-southeast-1": 50,
                    "ap-southeast-2": 80,
                }
            ),
        ]
        
        for config in default_regions:
            self._regions[config.region] = config
    
    # =========================================================================
    # Region Management
    # =========================================================================
    
    def get_region(self, region: Region) -> Optional[RegionConfig]:
        """Obtém configuração de uma região."""
        return self._regions.get(region)
    
    def list_regions(self, enabled_only: bool = True) -> List[RegionConfig]:
        """Lista regiões disponíveis."""
        regions = list(self._regions.values())
        if enabled_only:
            regions = [r for r in regions if r.enabled]
        return sorted(regions, key=lambda r: r.region.value)
    
    def add_region(self, config: RegionConfig) -> RegionConfig:
        """Adiciona ou atualiza uma região."""
        self._regions[config.region] = config
        return config
    
    def disable_region(self, region: Region) -> bool:
        """Desabilita uma região."""
        config = self._regions.get(region)
        if config:
            config.enabled = False
            return True
        return False
    
    # =========================================================================
    # Health & Capacity
    # =========================================================================
    
    def check_health(self, region: Region) -> Dict[str, Any]:
        """Verifica saúde de uma região."""
        config = self._regions.get(region)
        if not config:
            return {"healthy": False, "error": "Region not found"}
        
        # Simular health check
        config.last_health_check = datetime.now()
        
        return {
            "healthy": config.health_status == "healthy",
            "status": config.health_status,
            "capacity_percent": (config.current_tenants / config.max_tenants) * 100,
            "availability_zones": len(config.availability_zones),
            "last_check": config.last_health_check.isoformat(),
        }
    
    def get_capacity(self, region: Region) -> Dict[str, Any]:
        """Obtém informações de capacidade."""
        config = self._regions.get(region)
        if not config:
            return {"error": "Region not found"}
        
        return {
            "region": region.value,
            "max_tenants": config.max_tenants,
            "current_tenants": config.current_tenants,
            "available": config.max_tenants - config.current_tenants,
            "has_capacity": config.has_capacity(),
            "utilization_percent": (config.current_tenants / config.max_tenants) * 100,
        }
    
    def allocate_tenant(self, region: Region) -> bool:
        """Aloca um tenant para uma região."""
        config = self._regions.get(region)
        if config and config.has_capacity():
            config.current_tenants += 1
            return True
        return False
    
    def deallocate_tenant(self, region: Region) -> bool:
        """Remove alocação de tenant de uma região."""
        config = self._regions.get(region)
        if config and config.current_tenants > 0:
            config.current_tenants -= 1
            return True
        return False
    
    # =========================================================================
    # Selection & Routing
    # =========================================================================
    
    def get_best_region(
        self,
        client_region: Optional[str] = None,
        required_compliance: Optional[List[str]] = None
    ) -> Optional[RegionConfig]:
        """
        Obtém melhor região baseado em critérios.
        
        Args:
            client_region: Região do cliente para calcular latência
            required_compliance: Frameworks de compliance necessários
            
        Returns:
            Melhor região disponível
        """
        available = [
            r for r in self._regions.values()
            if r.enabled and r.has_capacity() and r.health_status == "healthy"
        ]
        
        if not available:
            return None
        
        if client_region:
            # Ordenar por latência estimada
            def get_latency(region: RegionConfig) -> int:
                return region.latency_map.get(client_region, 999)
            
            available.sort(key=get_latency)
        else:
            # Ordenar por capacidade disponível
            available.sort(
                key=lambda r: r.max_tenants - r.current_tenants,
                reverse=True
            )
        
        return available[0]
    
    def get_failover_region(self, current_region: Region) -> Optional[RegionConfig]:
        """Obtém região de failover."""
        current = self._regions.get(current_region)
        if not current:
            return None
        
        # Buscar região mais próxima com capacidade
        candidates = [
            r for r in self._regions.values()
            if r.region != current_region
            and r.enabled
            and r.has_capacity()
            and r.health_status == "healthy"
        ]
        
        if not candidates:
            return None
        
        # Ordenar por latência
        candidates.sort(
            key=lambda r: current.latency_map.get(r.region.value, 999)
        )
        
        return candidates[0]


class DataResidencyManager:
    """
    Gerenciador de residência de dados.
    
    Features:
    - Políticas de residência
    - Configuração por tenant
    - Compliance tracking
    - Replicação de dados
    """
    
    def __init__(self, region_manager: Optional[RegionManager] = None):
        self._region_manager = region_manager or RegionManager()
        self._policies: Dict[str, DataResidencyPolicy] = {}
        self._tenant_configs: Dict[str, TenantRegion] = {}
        self._initialize_default_policies()
    
    def _initialize_default_policies(self) -> None:
        """Inicializa políticas padrão."""
        # GDPR - Europa
        gdpr_policy = DataResidencyPolicy(
            name="GDPR Compliant",
            description="Data residency policy for GDPR compliance",
            allowed_regions=[Region.EU_WEST_1, Region.EU_CENTRAL_1, Region.EU_WEST_2],
            primary_region=Region.EU_WEST_1,
            enable_replication=True,
            replication_regions=[Region.EU_CENTRAL_1],
            compliance_frameworks=["GDPR"],
            encryption_required=True,
        )
        self._policies[gdpr_policy.id] = gdpr_policy
        
        # LGPD - Brasil
        lgpd_policy = DataResidencyPolicy(
            name="LGPD Compliant",
            description="Data residency policy for LGPD compliance",
            allowed_regions=[Region.SA_EAST_1],
            primary_region=Region.SA_EAST_1,
            enable_replication=False,
            compliance_frameworks=["LGPD"],
            encryption_required=True,
        )
        self._policies[lgpd_policy.id] = lgpd_policy
        
        # Global - Sem restrições
        global_policy = DataResidencyPolicy(
            name="Global",
            description="No regional restrictions",
            allowed_regions=list(Region),
            primary_region=Region.US_EAST_1,
            enable_replication=True,
            replication_regions=[Region.EU_WEST_1, Region.AP_NORTHEAST_1],
            compliance_frameworks=[],
        )
        self._policies[global_policy.id] = global_policy
    
    # =========================================================================
    # Policy Management
    # =========================================================================
    
    def create_policy(self, policy: DataResidencyPolicy) -> DataResidencyPolicy:
        """Cria nova política de residência."""
        policy.created_at = datetime.now()
        self._policies[policy.id] = policy
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[DataResidencyPolicy]:
        """Obtém política por ID."""
        return self._policies.get(policy_id)
    
    def list_policies(self) -> List[DataResidencyPolicy]:
        """Lista todas as políticas."""
        return list(self._policies.values())
    
    def get_policy_by_compliance(self, framework: str) -> Optional[DataResidencyPolicy]:
        """Obtém política por framework de compliance."""
        for policy in self._policies.values():
            if framework in policy.compliance_frameworks:
                return policy
        return None
    
    # =========================================================================
    # Tenant Configuration
    # =========================================================================
    
    def configure_tenant(
        self,
        tenant_id: str,
        primary_region: Region,
        policy_id: Optional[str] = None,
        secondary_regions: Optional[List[Region]] = None
    ) -> TenantRegion:
        """
        Configura região para um tenant.
        
        Args:
            tenant_id: ID do tenant
            primary_region: Região primária
            policy_id: ID da política de residência
            secondary_regions: Regiões secundárias
            
        Returns:
            Configuração do tenant
        """
        # Validar região
        region_config = self._region_manager.get_region(primary_region)
        if not region_config or not region_config.enabled:
            raise ValueError(f"Region {primary_region.value} is not available")
        
        # Validar política se fornecida
        if policy_id:
            policy = self._policies.get(policy_id)
            if policy and primary_region not in policy.allowed_regions:
                raise ValueError(
                    f"Region {primary_region.value} not allowed by policy {policy.name}"
                )
        
        # Criar configuração
        tenant_config = TenantRegion(
            tenant_id=tenant_id,
            primary_region=primary_region,
            residency_policy_id=policy_id,
            secondary_regions=secondary_regions or [],
            failover_priority=secondary_regions or [],
        )
        
        # Alocar tenant na região
        self._region_manager.allocate_tenant(primary_region)
        
        self._tenant_configs[tenant_id] = tenant_config
        return tenant_config
    
    def get_tenant_config(self, tenant_id: str) -> Optional[TenantRegion]:
        """Obtém configuração de região de um tenant."""
        return self._tenant_configs.get(tenant_id)
    
    def update_tenant_region(
        self,
        tenant_id: str,
        new_primary: Region
    ) -> Optional[TenantRegion]:
        """Atualiza região primária de um tenant."""
        config = self._tenant_configs.get(tenant_id)
        if not config:
            return None
        
        # Desalocar da região antiga
        self._region_manager.deallocate_tenant(config.primary_region)
        
        # Alocar na nova região
        if not self._region_manager.allocate_tenant(new_primary):
            # Restaurar alocação antiga se falhar
            self._region_manager.allocate_tenant(config.primary_region)
            return None
        
        config.primary_region = new_primary
        config.updated_at = datetime.now()
        
        return config
    
    # =========================================================================
    # Data Operations
    # =========================================================================
    
    def get_data_location(
        self,
        tenant_id: str,
        data_type: str = "user_data"
    ) -> Dict[str, Any]:
        """
        Obtém localização dos dados de um tenant.
        
        Args:
            tenant_id: ID do tenant
            data_type: Tipo de dado
            
        Returns:
            Dict com informações de localização
        """
        config = self._tenant_configs.get(tenant_id)
        if not config:
            return {"error": "Tenant not configured"}
        
        primary = self._region_manager.get_region(config.primary_region)
        
        result = {
            "tenant_id": tenant_id,
            "data_type": data_type,
            "primary_region": config.primary_region.value,
            "primary_endpoint": primary.api_endpoint if primary else None,
            "secondary_regions": [r.value for r in config.secondary_regions],
        }
        
        # Verificar política de residência
        if config.residency_policy_id:
            policy = self._policies.get(config.residency_policy_id)
            if policy:
                result["policy"] = policy.name
                result["compliance"] = policy.compliance_frameworks
                result["replication_enabled"] = policy.enable_replication
        
        return result
    
    def validate_data_location(
        self,
        tenant_id: str,
        target_region: Region
    ) -> Dict[str, Any]:
        """
        Valida se dados podem ser armazenados em uma região.
        
        Returns:
            Dict com resultado da validação
        """
        config = self._tenant_configs.get(tenant_id)
        if not config:
            return {"allowed": True, "reason": "No policy configured"}
        
        if not config.residency_policy_id:
            return {"allowed": True, "reason": "No residency policy"}
        
        policy = self._policies.get(config.residency_policy_id)
        if not policy:
            return {"allowed": True, "reason": "Policy not found"}
        
        if target_region in policy.allowed_regions:
            return {"allowed": True, "reason": "Region allowed by policy"}
        
        return {
            "allowed": False,
            "reason": f"Region {target_region.value} not allowed by policy {policy.name}",
            "allowed_regions": [r.value for r in policy.allowed_regions],
        }


class LatencyRouter:
    """
    Roteador baseado em latência.
    
    Features:
    - Roteamento por latência
    - Roteamento geográfico
    - Load balancing
    - Failover automático
    """
    
    def __init__(
        self,
        region_manager: Optional[RegionManager] = None,
        residency_manager: Optional[DataResidencyManager] = None
    ):
        self._region_manager = region_manager or RegionManager()
        self._residency_manager = residency_manager or DataResidencyManager(self._region_manager)
        
        # Cache de latência por IP/região
        self._latency_cache: Dict[str, Dict[str, int]] = {}
    
    def route_request(
        self,
        tenant_id: str,
        client_ip: Optional[str] = None,
        client_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Roteia request para melhor região.
        
        Args:
            tenant_id: ID do tenant
            client_ip: IP do cliente
            client_region: Região detectada do cliente
            
        Returns:
            Dict com região e endpoint selecionados
        """
        # Verificar configuração do tenant
        tenant_config = self._residency_manager.get_tenant_config(tenant_id)
        
        if tenant_config:
            # Tenant tem configuração específica
            primary = self._region_manager.get_region(tenant_config.primary_region)
            
            if primary and primary.health_status == "healthy":
                return {
                    "region": tenant_config.primary_region.value,
                    "endpoint": primary.api_endpoint,
                    "ws_endpoint": primary.ws_endpoint,
                    "routing_type": "tenant_config",
                }
            
            # Failover
            for failover_region in tenant_config.failover_priority:
                failover = self._region_manager.get_region(failover_region)
                if failover and failover.health_status == "healthy":
                    return {
                        "region": failover_region.value,
                        "endpoint": failover.api_endpoint,
                        "ws_endpoint": failover.ws_endpoint,
                        "routing_type": "failover",
                    }
        
        # Sem configuração específica - rotear por latência
        best = self._region_manager.get_best_region(client_region)
        
        if best:
            return {
                "region": best.region.value,
                "endpoint": best.api_endpoint,
                "ws_endpoint": best.ws_endpoint,
                "routing_type": "latency",
            }
        
        return {"error": "No available region"}
    
    def measure_latency(
        self,
        client_id: str,
        region: Region
    ) -> int:
        """
        Mede latência para uma região.
        
        Em produção, faria ping real.
        """
        # Simular medição de latência
        config = self._region_manager.get_region(region)
        if not config:
            return 999
        
        # Simular variação de latência
        base_latency = 50  # ms base
        variation = random.randint(-10, 20)
        
        latency = base_latency + variation
        
        # Cachear resultado
        if client_id not in self._latency_cache:
            self._latency_cache[client_id] = {}
        self._latency_cache[client_id][region.value] = latency
        
        return latency
    
    def get_all_endpoints(self, tenant_id: str) -> Dict[str, Any]:
        """Obtém todos os endpoints disponíveis para um tenant."""
        tenant_config = self._residency_manager.get_tenant_config(tenant_id)
        
        endpoints = []
        regions_to_check = []
        
        if tenant_config:
            regions_to_check = [tenant_config.primary_region] + tenant_config.secondary_regions
        else:
            regions_to_check = [r.region for r in self._region_manager.list_regions()]
        
        for region in regions_to_check:
            config = self._region_manager.get_region(region)
            if config and config.enabled:
                endpoints.append({
                    "region": region.value,
                    "api": config.api_endpoint,
                    "ws": config.ws_endpoint,
                    "cdn": config.cdn_endpoint,
                    "healthy": config.health_status == "healthy",
                })
        
        return {
            "tenant_id": tenant_id,
            "endpoints": endpoints,
            "count": len(endpoints),
        }


# Singleton instance
_region_manager: Optional[RegionManager] = None


def get_region_manager() -> RegionManager:
    """Obtém instância singleton do RegionManager."""
    global _region_manager
    if _region_manager is None:
        _region_manager = RegionManager()
    return _region_manager

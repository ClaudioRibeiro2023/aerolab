"""
Enterprise Features Module - Agno Platform v2.0

Features empresariais avançadas:
- SSO/SAML: Autenticação enterprise com SAML 2.0 e OIDC
- Multi-Region: Deploy multi-região com data residency
- White-Label: Customização completa de marca e domínio
"""

from .types import (
    # SSO Types
    SSOProvider,
    SSOProtocol,
    SSOConfig,
    SAMLConfig,
    OIDCConfig,
    SSOSession,
    SSOUser,
    # Multi-Region Types
    Region,
    RegionConfig,
    DataResidencyPolicy,
    TenantRegion,
    # White-Label Types
    BrandingConfig,
    DomainConfig,
    EmailTemplate,
    WhiteLabelConfig,
)

from .sso import (
    SSOManager,
    SAMLHandler,
    OIDCHandler,
    get_sso_manager,
)

from .multiregion import (
    RegionManager,
    DataResidencyManager,
    LatencyRouter,
    get_region_manager,
)

from .whitelabel import (
    WhiteLabelManager,
    BrandingEngine,
    DomainManager,
    EmailTemplateEngine,
    get_whitelabel_manager,
)

__all__ = [
    # SSO Types
    "SSOProvider",
    "SSOProtocol", 
    "SSOConfig",
    "SAMLConfig",
    "OIDCConfig",
    "SSOSession",
    "SSOUser",
    # SSO Services
    "SSOManager",
    "SAMLHandler",
    "OIDCHandler",
    "get_sso_manager",
    # Multi-Region Types
    "Region",
    "RegionConfig",
    "DataResidencyPolicy",
    "TenantRegion",
    # Multi-Region Services
    "RegionManager",
    "DataResidencyManager",
    "LatencyRouter",
    "get_region_manager",
    # White-Label Types
    "BrandingConfig",
    "DomainConfig",
    "EmailTemplate",
    "WhiteLabelConfig",
    # White-Label Services
    "WhiteLabelManager",
    "BrandingEngine",
    "DomainManager",
    "EmailTemplateEngine",
    "get_whitelabel_manager",
]

__version__ = "2.0.0"

"""
Enterprise Types - Tipos e estruturas de dados para features enterprise.

Define dataclasses e enums para SSO, Multi-Region e White-Label.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


# =============================================================================
# SSO/SAML Types
# =============================================================================

class SSOProvider(Enum):
    """Provedores de SSO suportados."""
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    AUTH0 = "auth0"
    ONELOGIN = "onelogin"
    PING_IDENTITY = "ping_identity"
    CUSTOM = "custom"


class SSOProtocol(Enum):
    """Protocolos de SSO suportados."""
    SAML_2_0 = "saml_2.0"
    OIDC = "oidc"
    OAUTH2 = "oauth2"


@dataclass
class SAMLConfig:
    """Configuração SAML 2.0."""
    
    # Identity Provider
    idp_entity_id: str
    idp_sso_url: str
    idp_slo_url: Optional[str] = None
    idp_certificate: Optional[str] = None
    idp_metadata_url: Optional[str] = None
    
    # Service Provider
    sp_entity_id: str = ""
    sp_acs_url: str = ""  # Assertion Consumer Service
    sp_slo_url: str = ""  # Single Logout
    sp_certificate: Optional[str] = None
    sp_private_key: Optional[str] = None
    
    # Assertion settings
    want_assertions_signed: bool = True
    want_response_signed: bool = True
    sign_requests: bool = True
    
    # Attribute mapping
    attribute_mapping: Dict[str, str] = field(default_factory=lambda: {
        "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
        "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
        "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups",
    })
    
    def get_sp_metadata(self) -> Dict[str, Any]:
        """Gera metadados do Service Provider."""
        return {
            "entityId": self.sp_entity_id,
            "assertionConsumerService": {
                "url": self.sp_acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            },
            "singleLogoutService": {
                "url": self.sp_slo_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            },
            "wantAssertionsSigned": self.want_assertions_signed,
            "authnRequestsSigned": self.sign_requests,
        }


@dataclass
class OIDCConfig:
    """Configuração OIDC (OpenID Connect)."""
    
    # Provider settings
    issuer: str
    client_id: str
    client_secret: str
    
    # Endpoints (podem ser auto-descobertos via .well-known)
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    end_session_endpoint: Optional[str] = None
    
    # Scopes
    scopes: List[str] = field(default_factory=lambda: [
        "openid", "profile", "email"
    ])
    
    # Response settings
    response_type: str = "code"
    response_mode: str = "query"
    
    # Claims mapping
    claims_mapping: Dict[str, str] = field(default_factory=lambda: {
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
        "picture": "picture",
        "groups": "groups",
    })
    
    # Token settings
    token_expiry_buffer: int = 300  # Segundos antes da expiração para refresh
    
    def get_discovery_url(self) -> str:
        """Retorna URL de discovery OIDC."""
        issuer = self.issuer.rstrip("/")
        return f"{issuer}/.well-known/openid-configuration"


@dataclass
class SSOConfig:
    """Configuração completa de SSO para um tenant."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    enabled: bool = True
    
    # Provider
    provider: SSOProvider = SSOProvider.CUSTOM
    protocol: SSOProtocol = SSOProtocol.SAML_2_0
    
    # Config específica
    saml_config: Optional[SAMLConfig] = None
    oidc_config: Optional[OIDCConfig] = None
    
    # Domain settings
    allowed_domains: List[str] = field(default_factory=list)
    auto_provision_users: bool = True
    default_role: str = "member"
    
    # Session settings
    session_duration_hours: int = 24
    force_reauth_after_hours: int = 168  # 7 dias
    
    # Audit
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class SSOUser:
    """Usuário autenticado via SSO."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    external_id: str = ""  # ID no IdP
    tenant_id: str = ""
    
    # Dados do usuário
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    display_name: str = ""
    picture_url: Optional[str] = None
    
    # Grupos/Roles do IdP
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    
    # Atributos extras do IdP
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Metadados
    provider: SSOProvider = SSOProvider.CUSTOM
    last_login: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        """Nome completo do usuário."""
        if self.display_name:
            return self.display_name
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class SSOSession:
    """Sessão SSO ativa."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    tenant_id: str = ""
    
    # Tokens
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    
    # SAML específico
    saml_session_index: Optional[str] = None
    saml_name_id: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Status
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Verifica se a sessão expirou."""
        return datetime.now() > self.expires_at
    
    def refresh(self, hours: int = 24) -> None:
        """Renova a sessão."""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.last_activity = datetime.now()


# =============================================================================
# Multi-Region Types
# =============================================================================

class Region(Enum):
    """Regiões disponíveis."""
    # Americas
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    SA_EAST_1 = "sa-east-1"  # São Paulo
    
    # Europe
    EU_WEST_1 = "eu-west-1"  # Ireland
    EU_CENTRAL_1 = "eu-central-1"  # Frankfurt
    EU_WEST_2 = "eu-west-2"  # London
    
    # Asia Pacific
    AP_SOUTHEAST_1 = "ap-southeast-1"  # Singapore
    AP_NORTHEAST_1 = "ap-northeast-1"  # Tokyo
    AP_SOUTH_1 = "ap-south-1"  # Mumbai
    
    # Australia
    AP_SOUTHEAST_2 = "ap-southeast-2"  # Sydney


@dataclass
class RegionConfig:
    """Configuração de uma região."""
    
    region: Region
    enabled: bool = True
    is_primary: bool = False
    
    # Endpoints
    api_endpoint: str = ""
    ws_endpoint: str = ""
    cdn_endpoint: str = ""
    
    # Cloud provider
    cloud_provider: str = "aws"  # aws, gcp, azure
    availability_zones: List[str] = field(default_factory=list)
    
    # Capacidade
    max_tenants: int = 1000
    current_tenants: int = 0
    max_requests_per_second: int = 10000
    
    # Latência média (ms) para outras regiões
    latency_map: Dict[str, int] = field(default_factory=dict)
    
    # Status
    health_status: str = "healthy"  # healthy, degraded, unhealthy
    last_health_check: datetime = field(default_factory=datetime.now)
    
    def has_capacity(self) -> bool:
        """Verifica se a região tem capacidade."""
        return self.current_tenants < self.max_tenants


@dataclass
class DataResidencyPolicy:
    """Política de residência de dados."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Regiões permitidas para dados
    allowed_regions: List[Region] = field(default_factory=list)
    primary_region: Optional[Region] = None
    
    # Tipos de dados cobertos
    data_types: List[str] = field(default_factory=lambda: [
        "user_data", "conversation_history", "documents", "embeddings"
    ])
    
    # Replicação
    enable_replication: bool = False
    replication_regions: List[Region] = field(default_factory=list)
    replication_mode: str = "async"  # sync, async
    
    # Compliance
    compliance_frameworks: List[str] = field(default_factory=list)  # GDPR, LGPD, CCPA
    data_retention_days: int = 365
    encryption_required: bool = True
    
    # Audit
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TenantRegion:
    """Configuração de região para um tenant."""
    
    tenant_id: str
    primary_region: Region
    
    # Política de residência
    residency_policy_id: Optional[str] = None
    
    # Regiões secundárias
    secondary_regions: List[Region] = field(default_factory=list)
    
    # Failover
    enable_failover: bool = True
    failover_priority: List[Region] = field(default_factory=list)
    
    # Roteamento
    routing_policy: str = "latency"  # latency, geo, round_robin
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# White-Label Types
# =============================================================================

@dataclass
class BrandingConfig:
    """Configuração de branding/marca."""
    
    # Cores
    primary_color: str = "#6366f1"  # Indigo
    secondary_color: str = "#8b5cf6"  # Violet
    accent_color: str = "#06b6d4"  # Cyan
    
    # Background
    background_color: str = "#ffffff"
    surface_color: str = "#f8fafc"
    text_color: str = "#1e293b"
    
    # Dark mode
    dark_primary_color: str = "#818cf8"
    dark_background_color: str = "#0f172a"
    dark_surface_color: str = "#1e293b"
    dark_text_color: str = "#f1f5f9"
    
    # Logo
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
    # Tipografia
    font_family: str = "Inter, system-ui, sans-serif"
    heading_font_family: str = "Inter, system-ui, sans-serif"
    
    # Bordas e sombras
    border_radius: str = "8px"
    shadow_style: str = "subtle"  # none, subtle, medium, strong
    
    def to_css_variables(self) -> Dict[str, str]:
        """Gera variáveis CSS para o tema."""
        return {
            "--color-primary": self.primary_color,
            "--color-secondary": self.secondary_color,
            "--color-accent": self.accent_color,
            "--color-background": self.background_color,
            "--color-surface": self.surface_color,
            "--color-text": self.text_color,
            "--font-family": self.font_family,
            "--font-heading": self.heading_font_family,
            "--border-radius": self.border_radius,
        }


@dataclass
class DomainConfig:
    """Configuração de domínio customizado."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    
    # Domínio
    custom_domain: str = ""  # Ex: app.empresa.com
    subdomain: str = ""  # Ex: empresa (para empresa.agno.ai)
    
    # SSL
    ssl_enabled: bool = True
    ssl_certificate: Optional[str] = None
    ssl_private_key: Optional[str] = None
    ssl_auto_renew: bool = True
    
    # DNS
    dns_verified: bool = False
    dns_verification_token: str = field(default_factory=lambda: str(uuid.uuid4()))
    cname_target: str = ""  # Ex: tenant-123.edge.agno.ai
    
    # Status
    status: str = "pending"  # pending, verifying, active, error
    error_message: Optional[str] = None
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None


@dataclass
class EmailTemplate:
    """Template de email customizado."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    
    # Identificação
    template_type: str = ""  # welcome, reset_password, invoice, notification
    name: str = ""
    description: str = ""
    
    # Conteúdo
    subject: str = ""
    html_content: str = ""
    text_content: str = ""
    
    # Variáveis disponíveis
    available_variables: List[str] = field(default_factory=lambda: [
        "{{user_name}}", "{{user_email}}", "{{company_name}}",
        "{{action_url}}", "{{support_email}}"
    ])
    
    # Configurações
    from_name: str = ""
    from_email: str = ""
    reply_to: Optional[str] = None
    
    # Status
    is_active: bool = True
    is_default: bool = False
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WhiteLabelConfig:
    """Configuração completa de white-label para um tenant."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    enabled: bool = True
    
    # Branding
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    
    # Domínio
    domain: Optional[DomainConfig] = None
    
    # Email templates
    email_templates: List[EmailTemplate] = field(default_factory=list)
    
    # Textos customizados
    app_name: str = "Agno"
    app_tagline: str = "AI Agent Platform"
    support_email: str = "support@agno.ai"
    support_url: str = "https://docs.agno.ai"
    privacy_url: str = ""
    terms_url: str = ""
    
    # Embed SDK
    embed_enabled: bool = False
    embed_domains: List[str] = field(default_factory=list)
    embed_config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_email_template(self, template_type: str) -> Optional[EmailTemplate]:
        """Obtém template de email por tipo."""
        for template in self.email_templates:
            if template.template_type == template_type and template.is_active:
                return template
        return None

"""
Tests for Enterprise Features Module.

Covers SSO/SAML, Multi-Region, and White-Label functionality.
"""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# SSO TYPES TESTS
# =============================================================================

class TestSSOTypes:
    """Test SSO types and enums."""
    
    def test_sso_provider_enum(self):
        from enterprise.types import SSOProvider
        assert SSOProvider.OKTA.value == "okta"
        assert SSOProvider.AZURE_AD.value == "azure_ad"
        assert SSOProvider.GOOGLE.value == "google"
    
    def test_sso_protocol_enum(self):
        from enterprise.types import SSOProtocol
        assert SSOProtocol.SAML_2_0.value == "saml_2.0"
        assert SSOProtocol.OIDC.value == "oidc"
    
    def test_saml_config_creation(self):
        from enterprise.types import SAMLConfig
        config = SAMLConfig(
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        assert config.idp_entity_id == "https://idp.example.com"
        assert config.want_assertions_signed is True
    
    def test_saml_config_sp_metadata(self):
        from enterprise.types import SAMLConfig
        config = SAMLConfig(
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        metadata = config.get_sp_metadata()
        assert metadata["entityId"] == "https://app.agno.ai/saml/sp"
        assert "assertionConsumerService" in metadata
    
    def test_oidc_config_creation(self):
        from enterprise.types import OIDCConfig
        config = OIDCConfig(
            issuer="https://auth.example.com",
            client_id="client-123",
            client_secret="secret-456",
        )
        assert config.issuer == "https://auth.example.com"
        assert "openid" in config.scopes
    
    def test_oidc_config_discovery_url(self):
        from enterprise.types import OIDCConfig
        config = OIDCConfig(
            issuer="https://auth.example.com/",
            client_id="client-123",
            client_secret="secret",
        )
        assert config.get_discovery_url() == "https://auth.example.com/.well-known/openid-configuration"
    
    def test_sso_config_creation(self):
        from enterprise.types import SSOConfig, SSOProvider, SSOProtocol
        config = SSOConfig(
            tenant_id="tenant-1",
            provider=SSOProvider.OKTA,
            protocol=SSOProtocol.SAML_2_0,
        )
        assert config.tenant_id == "tenant-1"
        assert config.enabled is True
    
    def test_sso_user_creation(self):
        from enterprise.types import SSOUser
        user = SSOUser(
            external_id="ext-123",
            tenant_id="tenant-1",
            email="user@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"
    
    def test_sso_session_creation(self):
        from enterprise.types import SSOSession
        session = SSOSession(
            user_id="user-1",
            tenant_id="tenant-1",
        )
        assert session.is_active is True
        assert not session.is_expired()
    
    def test_sso_session_expiry(self):
        from enterprise.types import SSOSession
        session = SSOSession(
            user_id="user-1",
            tenant_id="tenant-1",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert session.is_expired() is True


# =============================================================================
# REGION TYPES TESTS
# =============================================================================

class TestRegionTypes:
    """Test Multi-Region types."""
    
    def test_region_enum(self):
        from enterprise.types import Region
        assert Region.US_EAST_1.value == "us-east-1"
        assert Region.SA_EAST_1.value == "sa-east-1"
        assert Region.EU_WEST_1.value == "eu-west-1"
    
    def test_region_config_creation(self):
        from enterprise.types import RegionConfig, Region
        config = RegionConfig(
            region=Region.US_EAST_1,
            enabled=True,
            is_primary=True,
            max_tenants=1000,
        )
        assert config.has_capacity() is True
    
    def test_region_config_capacity(self):
        from enterprise.types import RegionConfig, Region
        config = RegionConfig(
            region=Region.US_EAST_1,
            max_tenants=100,
            current_tenants=100,
        )
        assert config.has_capacity() is False
    
    def test_data_residency_policy(self):
        from enterprise.types import DataResidencyPolicy, Region
        policy = DataResidencyPolicy(
            name="GDPR",
            allowed_regions=[Region.EU_WEST_1, Region.EU_CENTRAL_1],
            compliance_frameworks=["GDPR"],
        )
        assert Region.EU_WEST_1 in policy.allowed_regions
        assert "GDPR" in policy.compliance_frameworks
    
    def test_tenant_region(self):
        from enterprise.types import TenantRegion, Region
        config = TenantRegion(
            tenant_id="tenant-1",
            primary_region=Region.SA_EAST_1,
        )
        assert config.primary_region == Region.SA_EAST_1


# =============================================================================
# WHITE-LABEL TYPES TESTS
# =============================================================================

class TestWhiteLabelTypes:
    """Test White-Label types."""
    
    def test_branding_config(self):
        from enterprise.types import BrandingConfig
        config = BrandingConfig(
            primary_color="#ff0000",
            secondary_color="#00ff00",
        )
        assert config.primary_color == "#ff0000"
    
    def test_branding_css_variables(self):
        from enterprise.types import BrandingConfig
        config = BrandingConfig()
        css_vars = config.to_css_variables()
        assert "--color-primary" in css_vars
        assert "--font-family" in css_vars
    
    def test_domain_config(self):
        from enterprise.types import DomainConfig
        config = DomainConfig(
            tenant_id="tenant-1",
            custom_domain="app.empresa.com",
            subdomain="empresa",
        )
        assert config.custom_domain == "app.empresa.com"
        assert config.ssl_enabled is True
    
    def test_email_template(self):
        from enterprise.types import EmailTemplate
        template = EmailTemplate(
            tenant_id="tenant-1",
            template_type="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )
        assert template.template_type == "welcome"
    
    def test_whitelabel_config(self):
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        config = WhiteLabelConfig(
            tenant_id="tenant-1",
            branding=BrandingConfig(primary_color="#123456"),
            app_name="My App",
        )
        assert config.app_name == "My App"
        assert config.branding.primary_color == "#123456"
    
    def test_whitelabel_get_email_template(self):
        from enterprise.types import WhiteLabelConfig, EmailTemplate
        template = EmailTemplate(
            tenant_id="t1",
            template_type="welcome",
            subject="Hi",
            is_active=True,
        )
        config = WhiteLabelConfig(
            tenant_id="t1",
            email_templates=[template],
        )
        found = config.get_email_template("welcome")
        assert found is not None
        assert found.subject == "Hi"


# =============================================================================
# SSO MANAGER TESTS
# =============================================================================

class TestSSOManager:
    """Test SSO Manager functionality."""
    
    def test_sso_manager_creation(self):
        from enterprise.sso import SSOManager
        manager = SSOManager()
        assert manager is not None
    
    def test_configure_saml_sso(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, SSOProvider, SAMLConfig
        
        manager = SSOManager()
        
        saml_config = SAMLConfig(
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        
        config = SSOConfig(
            tenant_id="tenant-1",
            provider=SSOProvider.OKTA,
            protocol=SSOProtocol.SAML_2_0,
            saml_config=saml_config,
        )
        
        result = manager.configure_sso(config)
        assert result.tenant_id == "tenant-1"
        assert manager.get_config("tenant-1") is not None
    
    def test_configure_oidc_sso(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, SSOProvider, OIDCConfig
        
        manager = SSOManager()
        
        oidc_config = OIDCConfig(
            issuer="https://auth.example.com",
            client_id="client-123",
            client_secret="secret",
        )
        
        config = SSOConfig(
            tenant_id="tenant-2",
            provider=SSOProvider.AUTH0,
            protocol=SSOProtocol.OIDC,
            oidc_config=oidc_config,
        )
        
        result = manager.configure_sso(config)
        assert result.protocol == SSOProtocol.OIDC
    
    def test_initiate_saml_login(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, SSOProvider, SAMLConfig
        
        manager = SSOManager()
        
        saml_config = SAMLConfig(
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        
        config = SSOConfig(
            tenant_id="tenant-saml",
            protocol=SSOProtocol.SAML_2_0,
            saml_config=saml_config,
        )
        manager.configure_sso(config)
        
        result = manager.initiate_login("tenant-saml", "https://app.agno.ai/callback")
        assert "redirect_url" in result
        assert "request_id" in result
    
    def test_initiate_oidc_login(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, OIDCConfig
        
        manager = SSOManager()
        
        oidc_config = OIDCConfig(
            issuer="https://auth.example.com",
            client_id="client-123",
            client_secret="secret",
        )
        
        config = SSOConfig(
            tenant_id="tenant-oidc",
            protocol=SSOProtocol.OIDC,
            oidc_config=oidc_config,
        )
        manager.configure_sso(config)
        
        result = manager.initiate_login("tenant-oidc", "https://app.agno.ai/callback")
        assert "auth_url" in result
        assert "state" in result
    
    def test_disable_sso(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig
        
        manager = SSOManager()
        config = SSOConfig(tenant_id="tenant-disable")
        manager.configure_sso(config)
        
        assert manager.disable_sso("tenant-disable") is True
        assert manager.get_config("tenant-disable").enabled is False
    
    def test_get_sp_metadata(self):
        from enterprise.sso import SSOManager
        from enterprise.types import SSOConfig, SSOProtocol, SAMLConfig
        
        manager = SSOManager()
        
        saml_config = SAMLConfig(
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        
        config = SSOConfig(
            tenant_id="tenant-meta",
            protocol=SSOProtocol.SAML_2_0,
            saml_config=saml_config,
        )
        manager.configure_sso(config)
        
        metadata = manager.get_sp_metadata("tenant-meta")
        assert metadata is not None
        assert "EntityDescriptor" in metadata


# =============================================================================
# REGION MANAGER TESTS
# =============================================================================

class TestRegionManager:
    """Test Region Manager functionality."""
    
    def test_region_manager_creation(self):
        from enterprise.multiregion import RegionManager
        manager = RegionManager()
        assert manager is not None
    
    def test_default_regions(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        regions = manager.list_regions()
        
        assert len(regions) >= 4
        assert any(r.region == Region.US_EAST_1 for r in regions)
    
    def test_get_region(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        region = manager.get_region(Region.US_EAST_1)
        
        assert region is not None
        assert region.api_endpoint != ""
    
    def test_check_health(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        health = manager.check_health(Region.US_EAST_1)
        
        assert health["healthy"] is True
        assert "capacity_percent" in health
    
    def test_get_capacity(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        capacity = manager.get_capacity(Region.US_EAST_1)
        
        assert "max_tenants" in capacity
        assert "available" in capacity
    
    def test_allocate_tenant(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        initial = manager.get_capacity(Region.US_EAST_1)["current_tenants"]
        
        result = manager.allocate_tenant(Region.US_EAST_1)
        assert result is True
        
        after = manager.get_capacity(Region.US_EAST_1)["current_tenants"]
        assert after == initial + 1
    
    def test_get_best_region(self):
        from enterprise.multiregion import RegionManager
        
        manager = RegionManager()
        best = manager.get_best_region(client_region="us-west-2")
        
        assert best is not None
    
    def test_get_failover_region(self):
        from enterprise.multiregion import RegionManager
        from enterprise.types import Region
        
        manager = RegionManager()
        failover = manager.get_failover_region(Region.US_EAST_1)
        
        assert failover is not None
        assert failover.region != Region.US_EAST_1


# =============================================================================
# DATA RESIDENCY MANAGER TESTS
# =============================================================================

class TestDataResidencyManager:
    """Test Data Residency Manager functionality."""
    
    def test_residency_manager_creation(self):
        from enterprise.multiregion import DataResidencyManager
        manager = DataResidencyManager()
        assert manager is not None
    
    def test_default_policies(self):
        from enterprise.multiregion import DataResidencyManager
        
        manager = DataResidencyManager()
        policies = manager.list_policies()
        
        assert len(policies) >= 3
    
    def test_get_policy_by_compliance(self):
        from enterprise.multiregion import DataResidencyManager
        
        manager = DataResidencyManager()
        gdpr_policy = manager.get_policy_by_compliance("GDPR")
        
        assert gdpr_policy is not None
        assert "GDPR" in gdpr_policy.compliance_frameworks
    
    def test_configure_tenant(self):
        from enterprise.multiregion import DataResidencyManager
        from enterprise.types import Region
        
        manager = DataResidencyManager()
        config = manager.configure_tenant(
            tenant_id="tenant-br",
            primary_region=Region.SA_EAST_1,
        )
        
        assert config.primary_region == Region.SA_EAST_1
    
    def test_get_data_location(self):
        from enterprise.multiregion import DataResidencyManager
        from enterprise.types import Region
        
        manager = DataResidencyManager()
        manager.configure_tenant("tenant-loc", Region.EU_WEST_1)
        
        location = manager.get_data_location("tenant-loc")
        assert location["primary_region"] == "eu-west-1"
    
    def test_validate_data_location(self):
        from enterprise.multiregion import DataResidencyManager
        from enterprise.types import Region
        
        manager = DataResidencyManager()
        
        # Get GDPR policy
        gdpr_policy = manager.get_policy_by_compliance("GDPR")
        
        manager.configure_tenant(
            tenant_id="tenant-gdpr",
            primary_region=Region.EU_WEST_1,
            policy_id=gdpr_policy.id,
        )
        
        # EU region should be allowed
        result_eu = manager.validate_data_location("tenant-gdpr", Region.EU_WEST_1)
        assert result_eu["allowed"] is True
        
        # US region should not be allowed
        result_us = manager.validate_data_location("tenant-gdpr", Region.US_EAST_1)
        assert result_us["allowed"] is False


# =============================================================================
# LATENCY ROUTER TESTS
# =============================================================================

class TestLatencyRouter:
    """Test Latency Router functionality."""
    
    def test_router_creation(self):
        from enterprise.multiregion import LatencyRouter
        router = LatencyRouter()
        assert router is not None
    
    def test_route_request(self):
        from enterprise.multiregion import LatencyRouter
        
        router = LatencyRouter()
        result = router.route_request("tenant-new", client_region="us-east-1")
        
        assert "region" in result
        assert "endpoint" in result
    
    def test_route_with_tenant_config(self):
        from enterprise.multiregion import LatencyRouter, DataResidencyManager
        from enterprise.types import Region
        
        residency = DataResidencyManager()
        residency.configure_tenant("tenant-configured", Region.SA_EAST_1)
        
        router = LatencyRouter(residency_manager=residency)
        result = router.route_request("tenant-configured")
        
        assert result["region"] == "sa-east-1"
    
    def test_get_all_endpoints(self):
        from enterprise.multiregion import LatencyRouter
        
        router = LatencyRouter()
        endpoints = router.get_all_endpoints("tenant-x")
        
        assert "endpoints" in endpoints
        assert len(endpoints["endpoints"]) >= 4


# =============================================================================
# WHITE-LABEL MANAGER TESTS
# =============================================================================

class TestWhiteLabelManager:
    """Test White-Label Manager functionality."""
    
    def test_manager_creation(self):
        from enterprise.whitelabel import WhiteLabelManager
        manager = WhiteLabelManager()
        assert manager is not None
    
    def test_configure_whitelabel(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        
        manager = WhiteLabelManager()
        
        config = WhiteLabelConfig(
            tenant_id="tenant-wl",
            branding=BrandingConfig(primary_color="#ff6600"),
            app_name="My Custom App",
        )
        
        result = manager.configure(config)
        assert result.app_name == "My Custom App"
    
    def test_get_theme_css(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        
        manager = WhiteLabelManager()
        
        config = WhiteLabelConfig(
            tenant_id="tenant-css",
            branding=BrandingConfig(primary_color="#ff6600"),
        )
        manager.configure(config)
        
        css = manager.get_theme_css("tenant-css")
        assert css is not None
        assert "--color-primary" in css
        assert "#ff6600" in css
    
    def test_update_branding(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        
        manager = WhiteLabelManager()
        
        config = WhiteLabelConfig(
            tenant_id="tenant-brand",
            branding=BrandingConfig(primary_color="#111111"),
        )
        manager.configure(config)
        
        new_branding = BrandingConfig(primary_color="#222222")
        result = manager.update_branding("tenant-brand", new_branding)
        
        assert result["success"] is True
        assert "#222222" in result["css"]
    
    def test_setup_domain(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig
        
        manager = WhiteLabelManager()
        manager.configure(WhiteLabelConfig(tenant_id="tenant-domain"))
        
        result = manager.setup_domain(
            tenant_id="tenant-domain",
            custom_domain="app.mycompany.com",
            subdomain="mycompany",
        )
        
        assert result["success"] is True
        assert result["domain"].custom_domain == "app.mycompany.com"
    
    def test_add_email_template(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, EmailTemplate
        
        manager = WhiteLabelManager()
        manager.configure(WhiteLabelConfig(tenant_id="tenant-email"))
        
        template = EmailTemplate(
            tenant_id="tenant-email",
            template_type="welcome",
            subject="Welcome to {{company_name}}!",
            html_content="<h1>Welcome</h1>",
            text_content="Welcome",
        )
        
        result = manager.add_email_template(template)
        assert result["success"] is True
    
    def test_preview_email(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig
        
        manager = WhiteLabelManager()
        manager.configure(WhiteLabelConfig(tenant_id="tenant-preview"))
        
        preview = manager.preview_email("tenant-preview", "welcome")
        assert "subject" in preview
        assert "html" in preview
    
    def test_configure_embed(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig
        
        manager = WhiteLabelManager()
        manager.configure(WhiteLabelConfig(tenant_id="tenant-embed"))
        
        result = manager.configure_embed(
            tenant_id="tenant-embed",
            enabled=True,
            allowed_domains=["example.com", "test.com"],
        )
        
        assert result["success"] is True
        assert "embed_script" in result
    
    def test_get_manifest(self):
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import WhiteLabelConfig, BrandingConfig
        
        manager = WhiteLabelManager()
        manager.configure(WhiteLabelConfig(
            tenant_id="tenant-manifest",
            branding=BrandingConfig(primary_color="#123456"),
            app_name="PWA App",
        ))
        
        manifest = manager.get_manifest("tenant-manifest")
        assert manifest is not None
        assert manifest["name"] == "PWA App"
        assert manifest["theme_color"] == "#123456"


# =============================================================================
# BRANDING ENGINE TESTS
# =============================================================================

class TestBrandingEngine:
    """Test Branding Engine functionality."""
    
    def test_validate_color_valid(self):
        from enterprise.whitelabel import BrandingEngine
        engine = BrandingEngine()
        
        assert engine.validate_color("#ff0000") is True
        assert engine.validate_color("#FFF") is True
        assert engine.validate_color("#123456") is True
    
    def test_validate_color_invalid(self):
        from enterprise.whitelabel import BrandingEngine
        engine = BrandingEngine()
        
        assert engine.validate_color("red") is False
        assert engine.validate_color("#gg0000") is False
        assert engine.validate_color("123456") is False
    
    def test_validate_branding(self):
        from enterprise.whitelabel import BrandingEngine
        from enterprise.types import BrandingConfig
        
        engine = BrandingEngine()
        
        valid_config = BrandingConfig(primary_color="#ff0000")
        result = engine.validate_branding(valid_config)
        assert result["valid"] is True
    
    def test_compile_theme(self):
        from enterprise.whitelabel import BrandingEngine
        from enterprise.types import BrandingConfig
        
        engine = BrandingEngine()
        config = BrandingConfig(
            primary_color="#ff6600",
            font_family="Arial, sans-serif",
        )
        
        css = engine.compile_theme("tenant-compile", config)
        assert "--color-primary: #ff6600" in css
        assert "font-family: var(--font-family)" in css


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestEnterpriseIntegration:
    """Integration tests for Enterprise features."""
    
    def test_full_sso_flow(self):
        """Test complete SSO configuration and login flow."""
        from enterprise.sso import SSOManager
        from enterprise.types import (
            SSOConfig, SSOProtocol, SSOProvider, SAMLConfig
        )
        
        manager = SSOManager()
        
        # Configure SSO
        saml_config = SAMLConfig(
            idp_entity_id="https://idp.enterprise.com",
            idp_sso_url="https://idp.enterprise.com/sso",
            sp_entity_id="https://app.agno.ai/saml/sp",
            sp_acs_url="https://app.agno.ai/saml/acs",
        )
        
        config = SSOConfig(
            tenant_id="enterprise-tenant",
            provider=SSOProvider.OKTA,
            protocol=SSOProtocol.SAML_2_0,
            saml_config=saml_config,
            allowed_domains=["enterprise.com"],
            auto_provision_users=True,
        )
        
        manager.configure_sso(config)
        
        # Initiate login
        login_result = manager.initiate_login(
            "enterprise-tenant",
            "https://app.agno.ai/callback"
        )
        assert "redirect_url" in login_result
        
        # Get SP metadata
        metadata = manager.get_sp_metadata("enterprise-tenant")
        assert "EntityDescriptor" in metadata
    
    def test_full_multiregion_flow(self):
        """Test complete multi-region configuration."""
        from enterprise.multiregion import (
            RegionManager, DataResidencyManager, LatencyRouter
        )
        from enterprise.types import Region
        
        region_mgr = RegionManager()
        residency_mgr = DataResidencyManager(region_mgr)
        router = LatencyRouter(region_mgr, residency_mgr)
        
        # Get LGPD policy for Brazil
        lgpd_policy = residency_mgr.get_policy_by_compliance("LGPD")
        
        # Configure tenant for Brazil
        residency_mgr.configure_tenant(
            tenant_id="tenant-brazil",
            primary_region=Region.SA_EAST_1,
            policy_id=lgpd_policy.id,
        )
        
        # Route request
        route = router.route_request("tenant-brazil")
        assert route["region"] == "sa-east-1"
        
        # Validate data location
        validation = residency_mgr.validate_data_location(
            "tenant-brazil",
            Region.US_EAST_1
        )
        assert validation["allowed"] is False
    
    def test_full_whitelabel_flow(self):
        """Test complete white-label configuration."""
        from enterprise.whitelabel import WhiteLabelManager
        from enterprise.types import (
            WhiteLabelConfig, BrandingConfig, EmailTemplate
        )
        
        manager = WhiteLabelManager()
        
        # Configure white-label
        config = WhiteLabelConfig(
            tenant_id="partner-tenant",
            branding=BrandingConfig(
                primary_color="#00aa00",
                secondary_color="#008800",
                logo_url="https://partner.com/logo.png",
            ),
            app_name="Partner Platform",
            app_tagline="Powered by AI",
        )
        manager.configure(config)
        
        # Setup domain
        domain_result = manager.setup_domain(
            "partner-tenant",
            custom_domain="ai.partner.com",
            subdomain="partner",
        )
        assert domain_result["success"] is True
        
        # Add email template
        template = EmailTemplate(
            tenant_id="partner-tenant",
            template_type="welcome",
            subject="Welcome to {{company_name}}!",
            html_content="<h1>Welcome</h1>",
            text_content="Welcome",
        )
        manager.add_email_template(template)
        
        # Get theme CSS
        css = manager.get_theme_css("partner-tenant")
        assert "#00aa00" in css
        
        # Configure embed
        embed_result = manager.configure_embed(
            "partner-tenant",
            enabled=True,
            allowed_domains=["partner.com"],
        )
        assert "partner-tenant" in embed_result["embed_script"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

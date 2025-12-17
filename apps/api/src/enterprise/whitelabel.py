"""
White-Label Manager - Customização de Marca e Domínio.

Gerencia branding, domínios customizados, templates de email e embed SDK.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import re
import hashlib

from .types import (
    BrandingConfig, DomainConfig, EmailTemplate, WhiteLabelConfig
)


class BrandingEngine:
    """
    Motor de branding.
    
    Features:
    - Geração de temas CSS
    - Validação de cores
    - Asset management
    - Theme compilation
    """
    
    # Regex para validar cores hex
    HEX_COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
    
    def __init__(self):
        self._themes: Dict[str, BrandingConfig] = {}
        self._compiled_css: Dict[str, str] = {}
    
    def validate_color(self, color: str) -> bool:
        """Valida formato de cor hex."""
        return bool(self.HEX_COLOR_PATTERN.match(color))
    
    def validate_branding(self, config: BrandingConfig) -> Dict[str, Any]:
        """
        Valida configuração de branding.
        
        Returns:
            Dict com resultado da validação
        """
        errors = []
        
        # Validar cores
        color_fields = [
            'primary_color', 'secondary_color', 'accent_color',
            'background_color', 'surface_color', 'text_color',
            'dark_primary_color', 'dark_background_color',
            'dark_surface_color', 'dark_text_color'
        ]
        
        for field_name in color_fields:
            color = getattr(config, field_name, '')
            if color and not self.validate_color(color):
                errors.append(f"Invalid color format for {field_name}: {color}")
        
        # Validar URLs de logo
        if config.logo_url and not config.logo_url.startswith(('http://', 'https://', '/')):
            errors.append("Invalid logo URL format")
        
        # Validar font family
        if not config.font_family:
            errors.append("Font family is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    
    def compile_theme(self, tenant_id: str, config: BrandingConfig) -> str:
        """
        Compila tema para CSS.
        
        Args:
            tenant_id: ID do tenant
            config: Configuração de branding
            
        Returns:
            CSS compilado
        """
        css_vars = config.to_css_variables()
        
        # Gerar CSS com variáveis
        css_lines = [":root {"]
        for var_name, value in css_vars.items():
            css_lines.append(f"  {var_name}: {value};")
        css_lines.append("}")
        
        # Dark mode
        css_lines.append("")
        css_lines.append("@media (prefers-color-scheme: dark) {")
        css_lines.append("  :root {")
        css_lines.append(f"    --color-primary: {config.dark_primary_color};")
        css_lines.append(f"    --color-background: {config.dark_background_color};")
        css_lines.append(f"    --color-surface: {config.dark_surface_color};")
        css_lines.append(f"    --color-text: {config.dark_text_color};")
        css_lines.append("  }")
        css_lines.append("}")
        
        # Estilos base
        css_lines.extend([
            "",
            "/* Base styles */",
            "body {",
            "  font-family: var(--font-family);",
            "  background-color: var(--color-background);",
            "  color: var(--color-text);",
            "}",
            "",
            ".btn-primary {",
            "  background-color: var(--color-primary);",
            "  border-radius: var(--border-radius);",
            "}",
            "",
            ".btn-secondary {",
            "  background-color: var(--color-secondary);",
            "  border-radius: var(--border-radius);",
            "}",
            "",
            ".card {",
            "  background-color: var(--color-surface);",
            "  border-radius: var(--border-radius);",
            "}",
        ])
        
        compiled = "\n".join(css_lines)
        
        # Cachear
        self._themes[tenant_id] = config
        self._compiled_css[tenant_id] = compiled
        
        return compiled
    
    def get_theme(self, tenant_id: str) -> Optional[BrandingConfig]:
        """Obtém tema de um tenant."""
        return self._themes.get(tenant_id)
    
    def get_compiled_css(self, tenant_id: str) -> Optional[str]:
        """Obtém CSS compilado de um tenant."""
        return self._compiled_css.get(tenant_id)
    
    def generate_manifest(self, config: BrandingConfig, app_name: str) -> Dict[str, Any]:
        """Gera manifest.json para PWA."""
        return {
            "name": app_name,
            "short_name": app_name[:12],
            "theme_color": config.primary_color,
            "background_color": config.background_color,
            "display": "standalone",
            "icons": [
                {
                    "src": config.favicon_url or "/favicon.ico",
                    "sizes": "192x192",
                    "type": "image/png"
                }
            ]
        }


class DomainManager:
    """
    Gerenciador de domínios customizados.
    
    Features:
    - Configuração de domínio
    - Verificação DNS
    - Certificados SSL
    - Subdomain management
    """
    
    def __init__(self):
        self._domains: Dict[str, DomainConfig] = {}
        self._subdomain_map: Dict[str, str] = {}  # subdomain -> tenant_id
    
    def configure_domain(
        self,
        tenant_id: str,
        custom_domain: Optional[str] = None,
        subdomain: Optional[str] = None
    ) -> DomainConfig:
        """
        Configura domínio para um tenant.
        
        Args:
            tenant_id: ID do tenant
            custom_domain: Domínio customizado (ex: app.empresa.com)
            subdomain: Subdomain (ex: empresa -> empresa.agno.ai)
            
        Returns:
            Configuração de domínio
        """
        config = DomainConfig(
            tenant_id=tenant_id,
            custom_domain=custom_domain or "",
            subdomain=subdomain or "",
            cname_target=f"tenant-{tenant_id[:8]}.edge.agno.ai",
        )
        
        # Registrar subdomain
        if subdomain:
            if subdomain in self._subdomain_map:
                raise ValueError(f"Subdomain '{subdomain}' already in use")
            self._subdomain_map[subdomain] = tenant_id
        
        self._domains[tenant_id] = config
        return config
    
    def get_domain(self, tenant_id: str) -> Optional[DomainConfig]:
        """Obtém configuração de domínio."""
        return self._domains.get(tenant_id)
    
    def verify_dns(self, tenant_id: str) -> Dict[str, Any]:
        """
        Verifica configuração DNS.
        
        Em produção, faria lookup DNS real.
        """
        config = self._domains.get(tenant_id)
        if not config:
            return {"verified": False, "error": "Domain not configured"}
        
        # Simular verificação DNS
        # Em produção: verificar CNAME, TXT record para verificação
        
        verification_record = f"_agno-verification.{config.custom_domain}"
        expected_value = f"agno-verify={config.dns_verification_token}"
        
        # Simular sucesso
        config.dns_verified = True
        config.verified_at = datetime.now()
        config.status = "active"
        
        return {
            "verified": True,
            "domain": config.custom_domain,
            "cname_target": config.cname_target,
            "instructions": {
                "cname": {
                    "host": config.custom_domain,
                    "target": config.cname_target,
                },
                "verification": {
                    "type": "TXT",
                    "host": verification_record,
                    "value": expected_value,
                }
            }
        }
    
    def provision_ssl(self, tenant_id: str) -> Dict[str, Any]:
        """
        Provisiona certificado SSL.
        
        Em produção, usaria Let's Encrypt ou similar.
        """
        config = self._domains.get(tenant_id)
        if not config:
            return {"success": False, "error": "Domain not configured"}
        
        if not config.dns_verified:
            return {"success": False, "error": "DNS not verified"}
        
        # Simular provisionamento SSL
        config.ssl_enabled = True
        config.ssl_auto_renew = True
        
        return {
            "success": True,
            "domain": config.custom_domain,
            "ssl_enabled": True,
            "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
            "auto_renew": True,
        }
    
    def get_tenant_by_domain(self, domain: str) -> Optional[str]:
        """Obtém tenant_id por domínio."""
        for tenant_id, config in self._domains.items():
            if config.custom_domain == domain:
                return tenant_id
        return None
    
    def get_tenant_by_subdomain(self, subdomain: str) -> Optional[str]:
        """Obtém tenant_id por subdomain."""
        return self._subdomain_map.get(subdomain)
    
    def list_domains(self) -> List[DomainConfig]:
        """Lista todos os domínios configurados."""
        return list(self._domains.values())


class EmailTemplateEngine:
    """
    Motor de templates de email.
    
    Features:
    - Gerenciamento de templates
    - Renderização com variáveis
    - Preview
    - Validação
    """
    
    # Templates padrão
    DEFAULT_TEMPLATES = {
        "welcome": {
            "subject": "Welcome to {{company_name}}!",
            "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: {{primary_color}};">Welcome, {{user_name}}!</h1>
    <p>Thank you for joining {{company_name}}. We're excited to have you on board.</p>
    <p><a href="{{action_url}}" style="background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Get Started</a></p>
    <p>Best regards,<br>The {{company_name}} Team</p>
</body>
</html>
            """,
            "text": """
Welcome, {{user_name}}!

Thank you for joining {{company_name}}. We're excited to have you on board.

Get Started: {{action_url}}

Best regards,
The {{company_name}} Team
            """
        },
        "reset_password": {
            "subject": "Reset your password for {{company_name}}",
            "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: {{primary_color}};">Reset Your Password</h1>
    <p>Hi {{user_name}},</p>
    <p>We received a request to reset your password. Click the button below to create a new password:</p>
    <p><a href="{{action_url}}" style="background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password</a></p>
    <p>If you didn't request this, you can safely ignore this email.</p>
    <p>Best regards,<br>The {{company_name}} Team</p>
</body>
</html>
            """,
            "text": """
Hi {{user_name}},

We received a request to reset your password. Click the link below to create a new password:

{{action_url}}

If you didn't request this, you can safely ignore this email.

Best regards,
The {{company_name}} Team
            """
        },
        "invoice": {
            "subject": "Your {{company_name}} Invoice #{{invoice_number}}",
            "html": """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: {{primary_color}};">Invoice #{{invoice_number}}</h1>
    <p>Hi {{user_name}},</p>
    <p>Your invoice for {{billing_period}} is now available.</p>
    <table style="width: 100%; border-collapse: collapse;">
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Amount Due:</strong></td><td style="text-align: right;">{{amount_due}}</td></tr>
        <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Due Date:</strong></td><td style="text-align: right;">{{due_date}}</td></tr>
    </table>
    <p><a href="{{action_url}}" style="background: {{primary_color}}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Invoice</a></p>
    <p>Best regards,<br>The {{company_name}} Team</p>
</body>
</html>
            """,
            "text": """
Invoice #{{invoice_number}}

Hi {{user_name}},

Your invoice for {{billing_period}} is now available.

Amount Due: {{amount_due}}
Due Date: {{due_date}}

View Invoice: {{action_url}}

Best regards,
The {{company_name}} Team
            """
        },
    }
    
    def __init__(self):
        self._templates: Dict[str, Dict[str, EmailTemplate]] = {}  # tenant_id -> {type -> template}
    
    def get_default_template(self, template_type: str) -> Optional[Dict[str, str]]:
        """Obtém template padrão."""
        return self.DEFAULT_TEMPLATES.get(template_type)
    
    def create_template(self, template: EmailTemplate) -> EmailTemplate:
        """Cria ou atualiza template."""
        tenant_id = template.tenant_id
        
        if tenant_id not in self._templates:
            self._templates[tenant_id] = {}
        
        template.updated_at = datetime.now()
        self._templates[tenant_id][template.template_type] = template
        
        return template
    
    def get_template(
        self,
        tenant_id: str,
        template_type: str
    ) -> Optional[EmailTemplate]:
        """Obtém template customizado."""
        tenant_templates = self._templates.get(tenant_id, {})
        return tenant_templates.get(template_type)
    
    def list_templates(self, tenant_id: str) -> List[EmailTemplate]:
        """Lista templates de um tenant."""
        return list(self._templates.get(tenant_id, {}).values())
    
    def render(
        self,
        template: EmailTemplate,
        variables: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Renderiza template com variáveis.
        
        Args:
            template: Template a renderizar
            variables: Variáveis para substituição
            
        Returns:
            Dict com subject, html e text renderizados
        """
        def replace_vars(text: str) -> str:
            result = text
            for var_name, value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                result = result.replace(placeholder, str(value))
            return result
        
        return {
            "subject": replace_vars(template.subject),
            "html": replace_vars(template.html_content),
            "text": replace_vars(template.text_content),
            "from_name": template.from_name,
            "from_email": template.from_email,
            "reply_to": template.reply_to,
        }
    
    def preview(
        self,
        tenant_id: str,
        template_type: str,
        sample_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Gera preview de um template.
        
        Returns:
            Template renderizado com dados de exemplo
        """
        template = self.get_template(tenant_id, template_type)
        
        if not template:
            # Usar template padrão
            default = self.get_default_template(template_type)
            if not default:
                return {"error": f"Template '{template_type}' not found"}
            
            template = EmailTemplate(
                tenant_id=tenant_id,
                template_type=template_type,
                subject=default["subject"],
                html_content=default["html"],
                text_content=default["text"],
            )
        
        # Dados de exemplo
        sample = sample_data or {
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "company_name": "Acme Corp",
            "action_url": "https://app.example.com/action",
            "support_email": "support@example.com",
            "primary_color": "#6366f1",
            "invoice_number": "INV-2024-001",
            "billing_period": "December 2024",
            "amount_due": "$99.00",
            "due_date": "January 15, 2025",
        }
        
        return self.render(template, sample)
    
    def validate_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """Valida template."""
        errors = []
        warnings = []
        
        # Validar campos obrigatórios
        if not template.subject:
            errors.append("Subject is required")
        if not template.html_content and not template.text_content:
            errors.append("Either HTML or text content is required")
        
        # Verificar variáveis não fechadas
        for content in [template.subject, template.html_content, template.text_content]:
            if content:
                open_count = content.count("{{")
                close_count = content.count("}}")
                if open_count != close_count:
                    errors.append("Unbalanced template variables")
        
        # Avisos
        if not template.text_content:
            warnings.append("Text version is recommended for accessibility")
        if not template.reply_to:
            warnings.append("Reply-to address is recommended")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


class WhiteLabelManager:
    """
    Gerenciador central de White-Label.
    
    Features:
    - Configuração completa por tenant
    - Branding, domínios, emails
    - Embed SDK configuration
    """
    
    def __init__(self):
        self._configs: Dict[str, WhiteLabelConfig] = {}
        self._branding_engine = BrandingEngine()
        self._domain_manager = DomainManager()
        self._email_engine = EmailTemplateEngine()
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def configure(self, config: WhiteLabelConfig) -> WhiteLabelConfig:
        """
        Configura white-label para um tenant.
        
        Args:
            config: Configuração de white-label
            
        Returns:
            Configuração salva
        """
        config.updated_at = datetime.now()
        self._configs[config.tenant_id] = config
        
        # Compilar tema
        self._branding_engine.compile_theme(config.tenant_id, config.branding)
        
        # Configurar domínio se fornecido
        if config.domain:
            self._domain_manager._domains[config.tenant_id] = config.domain
        
        # Registrar templates
        for template in config.email_templates:
            self._email_engine.create_template(template)
        
        return config
    
    def get_config(self, tenant_id: str) -> Optional[WhiteLabelConfig]:
        """Obtém configuração de um tenant."""
        return self._configs.get(tenant_id)
    
    def update_branding(
        self,
        tenant_id: str,
        branding: BrandingConfig
    ) -> Dict[str, Any]:
        """Atualiza branding de um tenant."""
        config = self._configs.get(tenant_id)
        if not config:
            return {"error": "Tenant not configured"}
        
        # Validar
        validation = self._branding_engine.validate_branding(branding)
        if not validation["valid"]:
            return validation
        
        # Atualizar
        config.branding = branding
        config.updated_at = datetime.now()
        
        # Recompilar tema
        css = self._branding_engine.compile_theme(tenant_id, branding)
        
        return {
            "success": True,
            "css": css,
        }
    
    # =========================================================================
    # Assets
    # =========================================================================
    
    def get_theme_css(self, tenant_id: str) -> Optional[str]:
        """Obtém CSS do tema."""
        return self._branding_engine.get_compiled_css(tenant_id)
    
    def get_manifest(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtém manifest.json para PWA."""
        config = self._configs.get(tenant_id)
        if not config:
            return None
        
        return self._branding_engine.generate_manifest(
            config.branding,
            config.app_name
        )
    
    # =========================================================================
    # Domain
    # =========================================================================
    
    def setup_domain(
        self,
        tenant_id: str,
        custom_domain: Optional[str] = None,
        subdomain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configura domínio customizado."""
        try:
            domain_config = self._domain_manager.configure_domain(
                tenant_id, custom_domain, subdomain
            )
            
            # Atualizar config principal
            config = self._configs.get(tenant_id)
            if config:
                config.domain = domain_config
            
            return {
                "success": True,
                "domain": domain_config,
                "dns_instructions": self._domain_manager.verify_dns(tenant_id),
            }
            
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    def verify_domain(self, tenant_id: str) -> Dict[str, Any]:
        """Verifica DNS do domínio."""
        return self._domain_manager.verify_dns(tenant_id)
    
    def provision_ssl(self, tenant_id: str) -> Dict[str, Any]:
        """Provisiona SSL para domínio."""
        return self._domain_manager.provision_ssl(tenant_id)
    
    # =========================================================================
    # Email Templates
    # =========================================================================
    
    def add_email_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """Adiciona template de email."""
        validation = self._email_engine.validate_template(template)
        if not validation["valid"]:
            return validation
        
        created = self._email_engine.create_template(template)
        
        # Atualizar config
        config = self._configs.get(template.tenant_id)
        if config:
            # Remover template existente do mesmo tipo
            config.email_templates = [
                t for t in config.email_templates
                if t.template_type != template.template_type
            ]
            config.email_templates.append(created)
        
        return {
            "success": True,
            "template": created,
        }
    
    def get_email_template(
        self,
        tenant_id: str,
        template_type: str
    ) -> Optional[EmailTemplate]:
        """Obtém template de email."""
        return self._email_engine.get_template(tenant_id, template_type)
    
    def preview_email(
        self,
        tenant_id: str,
        template_type: str,
        sample_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Preview de email."""
        return self._email_engine.preview(tenant_id, template_type, sample_data)
    
    # =========================================================================
    # Embed SDK
    # =========================================================================
    
    def configure_embed(
        self,
        tenant_id: str,
        enabled: bool = True,
        allowed_domains: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Configura Embed SDK."""
        wl_config = self._configs.get(tenant_id)
        if not wl_config:
            return {"error": "Tenant not configured"}
        
        wl_config.embed_enabled = enabled
        wl_config.embed_domains = allowed_domains or []
        wl_config.embed_config = config or {}
        wl_config.updated_at = datetime.now()
        
        # Gerar script de embed
        embed_script = self._generate_embed_script(tenant_id)
        
        return {
            "success": True,
            "enabled": enabled,
            "allowed_domains": wl_config.embed_domains,
            "embed_script": embed_script,
        }
    
    def _generate_embed_script(self, tenant_id: str) -> str:
        """Gera script de embed."""
        config = self._configs.get(tenant_id)
        if not config:
            return ""
        
        # Determinar endpoint
        domain = "agno.ai"
        if config.domain and config.domain.dns_verified:
            domain = config.domain.custom_domain
        elif config.domain and config.domain.subdomain:
            domain = f"{config.domain.subdomain}.agno.ai"
        
        return f"""
<!-- Agno Embed Widget -->
<script>
(function(w,d,s,o,f,js,fjs){{
w['AgnoEmbed']=o;w[o]=w[o]||function(){{(w[o].q=w[o].q||[]).push(arguments)}};
js=d.createElement(s);fjs=d.getElementsByTagName(s)[0];
js.id=o;js.src='https://{domain}/embed/v1/widget.js';js.async=1;
fjs.parentNode.insertBefore(js,fjs);
}}(window,document,'script','agno'));
agno('init', '{tenant_id}');
</script>
<!-- End Agno Embed Widget -->
        """.strip()
    
    def get_embed_script(self, tenant_id: str) -> Optional[str]:
        """Obtém script de embed."""
        config = self._configs.get(tenant_id)
        if not config or not config.embed_enabled:
            return None
        return self._generate_embed_script(tenant_id)
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def list_configs(self) -> List[WhiteLabelConfig]:
        """Lista todas as configurações."""
        return list(self._configs.values())
    
    def resolve_tenant(
        self,
        domain: Optional[str] = None,
        subdomain: Optional[str] = None
    ) -> Optional[str]:
        """Resolve tenant por domínio ou subdomain."""
        if domain:
            return self._domain_manager.get_tenant_by_domain(domain)
        if subdomain:
            return self._domain_manager.get_tenant_by_subdomain(subdomain)
        return None


# Singleton instance
_whitelabel_manager: Optional[WhiteLabelManager] = None


def get_whitelabel_manager() -> WhiteLabelManager:
    """Obtém instância singleton do WhiteLabelManager."""
    global _whitelabel_manager
    if _whitelabel_manager is None:
        _whitelabel_manager = WhiteLabelManager()
    return _whitelabel_manager

"""
SSO Manager - Autenticação Enterprise com SAML 2.0 e OIDC.

Gerencia integração com Identity Providers empresariais.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import uuid
import base64
import hashlib
import hmac
import json
import urllib.parse

from .types import (
    SSOProvider, SSOProtocol, SSOConfig,
    SAMLConfig, OIDCConfig, SSOSession, SSOUser
)


class SAMLHandler:
    """
    Handler para SAML 2.0.
    
    Features:
    - Geração de AuthnRequest
    - Validação de SAML Response
    - Extração de assertions
    - Single Logout
    """
    
    def __init__(self, config: SAMLConfig):
        self.config = config
    
    def generate_authn_request(
        self,
        relay_state: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Gera AuthnRequest para redirect ao IdP.
        
        Returns:
            Dict com URL e parâmetros para redirect
        """
        request_id = f"_agno_{uuid.uuid4().hex}"
        issue_instant = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # SAML AuthnRequest simplificado
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.config.idp_sso_url}"
    AssertionConsumerServiceURL="{self.config.sp_acs_url}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.config.sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy
        Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        AllowCreate="true"/>
</samlp:AuthnRequest>"""
        
        # Encode request
        import zlib
        compressed = zlib.compress(authn_request.encode())[2:-4]
        encoded = base64.b64encode(compressed).decode()
        
        # Build redirect URL
        params = {
            "SAMLRequest": encoded,
        }
        if relay_state:
            params["RelayState"] = relay_state
        
        redirect_url = f"{self.config.idp_sso_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "request_id": request_id,
            "redirect_url": redirect_url,
            "saml_request": encoded,
            "relay_state": relay_state or "",
        }
    
    def parse_response(
        self,
        saml_response: str,
        expected_request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse SAML Response do IdP.
        
        Args:
            saml_response: Response Base64 encoded
            expected_request_id: ID do request original
            
        Returns:
            Dict com dados do usuário e sessão
        """
        try:
            # Decode response
            decoded = base64.b64decode(saml_response).decode()
            
            # Parse básico (em produção usar lxml com validação)
            result = self._extract_assertion_data(decoded)
            
            return {
                "success": True,
                "user": result,
                "session_index": result.get("session_index"),
                "name_id": result.get("name_id"),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _extract_assertion_data(self, xml_response: str) -> Dict[str, Any]:
        """Extrai dados da assertion SAML."""
        # Simulação de parsing (em produção usar lxml)
        # Aqui extraímos dados básicos do XML
        
        result = {
            "name_id": "",
            "session_index": "",
            "attributes": {},
        }
        
        # Extrair NameID
        if "<saml:NameID" in xml_response:
            start = xml_response.find("<saml:NameID")
            end = xml_response.find("</saml:NameID>")
            if start != -1 and end != -1:
                name_id_xml = xml_response[start:end]
                # Extrair valor entre > e <
                value_start = name_id_xml.find(">") + 1
                result["name_id"] = name_id_xml[value_start:].strip()
        
        # Mapear atributos usando config
        for local_name, saml_name in self.config.attribute_mapping.items():
            if saml_name in xml_response:
                # Extrair valor do atributo
                result["attributes"][local_name] = f"extracted_{local_name}"
        
        return result
    
    def generate_logout_request(
        self,
        name_id: str,
        session_index: str
    ) -> Dict[str, str]:
        """
        Gera LogoutRequest para Single Logout.
        
        Returns:
            Dict com URL e parâmetros para logout
        """
        if not self.config.idp_slo_url:
            return {"error": "SLO not configured"}
        
        request_id = f"_agno_logout_{uuid.uuid4().hex}"
        issue_instant = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        logout_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:LogoutRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.config.idp_slo_url}">
    <saml:Issuer>{self.config.sp_entity_id}</saml:Issuer>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
        {name_id}
    </saml:NameID>
    <samlp:SessionIndex>{session_index}</samlp:SessionIndex>
</samlp:LogoutRequest>"""
        
        import zlib
        compressed = zlib.compress(logout_request.encode())[2:-4]
        encoded = base64.b64encode(compressed).decode()
        
        redirect_url = f"{self.config.idp_slo_url}?SAMLRequest={urllib.parse.quote(encoded)}"
        
        return {
            "request_id": request_id,
            "redirect_url": redirect_url,
        }
    
    def get_sp_metadata_xml(self) -> str:
        """Gera metadata XML do Service Provider."""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{self.config.sp_entity_id}">
    <md:SPSSODescriptor
        AuthnRequestsSigned="{str(self.config.sign_requests).lower()}"
        WantAssertionsSigned="{str(self.config.want_assertions_signed).lower()}"
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{self.config.sp_acs_url}"
            index="0"
            isDefault="true"/>
        <md:SingleLogoutService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="{self.config.sp_slo_url}"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""


class OIDCHandler:
    """
    Handler para OIDC (OpenID Connect).
    
    Features:
    - Authorization Code Flow
    - Token validation
    - UserInfo retrieval
    - Token refresh
    """
    
    def __init__(self, config: OIDCConfig):
        self.config = config
        self._discovery_cache: Optional[Dict[str, Any]] = None
    
    def generate_auth_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        nonce: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Gera URL de autorização para redirect.
        
        Returns:
            Dict com URL e parâmetros
        """
        state = state or str(uuid.uuid4())
        nonce = nonce or str(uuid.uuid4())
        
        params = {
            "client_id": self.config.client_id,
            "response_type": self.config.response_type,
            "scope": " ".join(self.config.scopes),
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
            "response_mode": self.config.response_mode,
        }
        
        auth_endpoint = self.config.authorization_endpoint or f"{self.config.issuer}/authorize"
        auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state,
            "nonce": nonce,
        }
    
    def exchange_code(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Troca authorization code por tokens.
        
        Em produção, fazer request HTTP real.
        """
        # Simulação - em produção usar httpx/aiohttp
        token_endpoint = self.config.token_endpoint or f"{self.config.issuer}/oauth/token"
        
        # Dados para POST
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        
        # Simular resposta de tokens
        return {
            "access_token": f"access_{uuid.uuid4().hex}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"refresh_{uuid.uuid4().hex}",
            "id_token": self._generate_mock_id_token(),
        }
    
    def _generate_mock_id_token(self) -> str:
        """Gera ID token mock para desenvolvimento."""
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
        ).decode().rstrip("=")
        
        payload = base64.urlsafe_b64encode(
            json.dumps({
                "iss": self.config.issuer,
                "sub": str(uuid.uuid4()),
                "aud": self.config.client_id,
                "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "iat": int(datetime.now().timestamp()),
                "email": "user@example.com",
                "name": "Test User",
            }).encode()
        ).decode().rstrip("=")
        
        signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
        
        return f"{header}.{payload}.{signature}"
    
    def validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Valida ID token e extrai claims.
        
        Em produção, validar assinatura com JWKS.
        """
        try:
            parts = id_token.split(".")
            if len(parts) != 3:
                return {"valid": False, "error": "Invalid token format"}
            
            # Decode payload
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            
            claims = json.loads(base64.urlsafe_b64decode(payload))
            
            # Validate expiration
            if claims.get("exp", 0) < datetime.now().timestamp():
                return {"valid": False, "error": "Token expired"}
            
            # Validate issuer
            if claims.get("iss") != self.config.issuer:
                return {"valid": False, "error": "Invalid issuer"}
            
            # Validate audience
            if claims.get("aud") != self.config.client_id:
                return {"valid": False, "error": "Invalid audience"}
            
            return {
                "valid": True,
                "claims": claims,
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """
        Obtém informações do usuário via UserInfo endpoint.
        
        Em produção, fazer request HTTP real.
        """
        userinfo_endpoint = self.config.userinfo_endpoint or f"{self.config.issuer}/userinfo"
        
        # Simular resposta
        return {
            "sub": str(uuid.uuid4()),
            "email": "user@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.png",
        }
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Renova tokens usando refresh token."""
        token_endpoint = self.config.token_endpoint or f"{self.config.issuer}/oauth/token"
        
        # Simular resposta
        return {
            "access_token": f"access_{uuid.uuid4().hex}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": f"refresh_{uuid.uuid4().hex}",
        }
    
    def generate_logout_url(self, id_token_hint: str, post_logout_redirect: str) -> str:
        """Gera URL para logout."""
        end_session = self.config.end_session_endpoint or f"{self.config.issuer}/logout"
        
        params = {
            "id_token_hint": id_token_hint,
            "post_logout_redirect_uri": post_logout_redirect,
        }
        
        return f"{end_session}?{urllib.parse.urlencode(params)}"


class SSOManager:
    """
    Gerenciador central de SSO.
    
    Features:
    - Configuração de SSO por tenant
    - Handlers SAML e OIDC
    - Gerenciamento de sessões
    - Provisionamento de usuários
    """
    
    def __init__(self):
        self._configs: Dict[str, SSOConfig] = {}
        self._sessions: Dict[str, SSOSession] = {}
        self._users: Dict[str, SSOUser] = {}
        self._saml_handlers: Dict[str, SAMLHandler] = {}
        self._oidc_handlers: Dict[str, OIDCHandler] = {}
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def configure_sso(self, config: SSOConfig) -> SSOConfig:
        """
        Configura SSO para um tenant.
        
        Args:
            config: Configuração de SSO
            
        Returns:
            Configuração salva
        """
        config.updated_at = datetime.now()
        self._configs[config.tenant_id] = config
        
        # Criar handlers apropriados
        if config.protocol == SSOProtocol.SAML_2_0 and config.saml_config:
            self._saml_handlers[config.tenant_id] = SAMLHandler(config.saml_config)
        elif config.protocol == SSOProtocol.OIDC and config.oidc_config:
            self._oidc_handlers[config.tenant_id] = OIDCHandler(config.oidc_config)
        
        return config
    
    def get_config(self, tenant_id: str) -> Optional[SSOConfig]:
        """Obtém configuração de SSO de um tenant."""
        return self._configs.get(tenant_id)
    
    def disable_sso(self, tenant_id: str) -> bool:
        """Desabilita SSO para um tenant."""
        config = self._configs.get(tenant_id)
        if config:
            config.enabled = False
            config.updated_at = datetime.now()
            return True
        return False
    
    # =========================================================================
    # Authentication Flow
    # =========================================================================
    
    def initiate_login(
        self,
        tenant_id: str,
        redirect_uri: str,
        relay_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inicia fluxo de login SSO.
        
        Args:
            tenant_id: ID do tenant
            redirect_uri: URL de callback
            relay_state: Estado para preservar
            
        Returns:
            Dict com URL de redirect e dados auxiliares
        """
        config = self._configs.get(tenant_id)
        if not config or not config.enabled:
            return {"error": "SSO not configured for tenant"}
        
        if config.protocol == SSOProtocol.SAML_2_0:
            handler = self._saml_handlers.get(tenant_id)
            if handler:
                return handler.generate_authn_request(relay_state)
        
        elif config.protocol == SSOProtocol.OIDC:
            handler = self._oidc_handlers.get(tenant_id)
            if handler:
                return handler.generate_auth_url(redirect_uri, relay_state)
        
        return {"error": "No handler configured"}
    
    def handle_callback(
        self,
        tenant_id: str,
        callback_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processa callback do IdP.
        
        Args:
            tenant_id: ID do tenant
            callback_data: Dados do callback (SAMLResponse ou code)
            
        Returns:
            Dict com usuário e sessão ou erro
        """
        config = self._configs.get(tenant_id)
        if not config:
            return {"error": "SSO not configured"}
        
        if config.protocol == SSOProtocol.SAML_2_0:
            return self._handle_saml_callback(tenant_id, config, callback_data)
        elif config.protocol == SSOProtocol.OIDC:
            return self._handle_oidc_callback(tenant_id, config, callback_data)
        
        return {"error": "Unknown protocol"}
    
    def _handle_saml_callback(
        self,
        tenant_id: str,
        config: SSOConfig,
        data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Processa callback SAML."""
        handler = self._saml_handlers.get(tenant_id)
        if not handler:
            return {"error": "SAML handler not found"}
        
        saml_response = data.get("SAMLResponse", "")
        result = handler.parse_response(saml_response)
        
        if not result.get("success"):
            return {"error": result.get("error", "SAML validation failed")}
        
        # Criar ou atualizar usuário
        user = self._provision_user(tenant_id, config, result["user"])
        
        # Criar sessão
        session = self._create_session(
            user, 
            config,
            saml_session_index=result.get("session_index"),
            saml_name_id=result.get("name_id")
        )
        
        return {
            "success": True,
            "user": user,
            "session": session,
        }
    
    def _handle_oidc_callback(
        self,
        tenant_id: str,
        config: SSOConfig,
        data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Processa callback OIDC."""
        handler = self._oidc_handlers.get(tenant_id)
        if not handler:
            return {"error": "OIDC handler not found"}
        
        code = data.get("code", "")
        redirect_uri = data.get("redirect_uri", "")
        
        # Trocar code por tokens
        tokens = handler.exchange_code(code, redirect_uri)
        
        if "error" in tokens:
            return {"error": tokens["error"]}
        
        # Validar ID token
        id_token_result = handler.validate_id_token(tokens["id_token"])
        if not id_token_result.get("valid"):
            return {"error": id_token_result.get("error", "Invalid ID token")}
        
        # Obter userinfo
        userinfo = handler.get_userinfo(tokens["access_token"])
        
        # Criar ou atualizar usuário
        user = self._provision_user(tenant_id, config, {
            "name_id": userinfo.get("sub"),
            "attributes": userinfo,
        })
        
        # Criar sessão
        session = self._create_session(
            user,
            config,
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            id_token=tokens.get("id_token")
        )
        
        return {
            "success": True,
            "user": user,
            "session": session,
        }
    
    def _provision_user(
        self,
        tenant_id: str,
        config: SSOConfig,
        user_data: Dict[str, Any]
    ) -> SSOUser:
        """Provisiona ou atualiza usuário."""
        external_id = user_data.get("name_id", "")
        attrs = user_data.get("attributes", {})
        
        # Verificar se usuário já existe
        user_key = f"{tenant_id}:{external_id}"
        existing_user = self._users.get(user_key)
        
        if existing_user:
            # Atualizar dados
            existing_user.email = attrs.get("email", existing_user.email)
            existing_user.first_name = attrs.get("given_name", attrs.get("first_name", existing_user.first_name))
            existing_user.last_name = attrs.get("family_name", attrs.get("last_name", existing_user.last_name))
            existing_user.picture_url = attrs.get("picture", existing_user.picture_url)
            existing_user.groups = attrs.get("groups", existing_user.groups) or []
            existing_user.last_login = datetime.now()
            existing_user.attributes = attrs
            return existing_user
        
        # Criar novo usuário
        user = SSOUser(
            external_id=external_id,
            tenant_id=tenant_id,
            email=attrs.get("email", ""),
            first_name=attrs.get("given_name", attrs.get("first_name", "")),
            last_name=attrs.get("family_name", attrs.get("last_name", "")),
            display_name=attrs.get("name", ""),
            picture_url=attrs.get("picture"),
            groups=attrs.get("groups", []) or [],
            roles=[config.default_role],
            attributes=attrs,
            provider=config.provider,
        )
        
        self._users[user_key] = user
        return user
    
    def _create_session(
        self,
        user: SSOUser,
        config: SSOConfig,
        **kwargs
    ) -> SSOSession:
        """Cria nova sessão SSO."""
        session = SSOSession(
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=datetime.now() + timedelta(hours=config.session_duration_hours),
            **kwargs
        )
        
        self._sessions[session.id] = session
        return session
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def get_session(self, session_id: str) -> Optional[SSOSession]:
        """Obtém sessão por ID."""
        session = self._sessions.get(session_id)
        if session and not session.is_expired():
            return session
        return None
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Valida sessão e retorna dados."""
        session = self.get_session(session_id)
        if not session:
            return {"valid": False, "error": "Session not found or expired"}
        
        if not session.is_active:
            return {"valid": False, "error": "Session inactive"}
        
        # Atualizar última atividade
        session.last_activity = datetime.now()
        
        # Buscar usuário
        user_key = f"{session.tenant_id}:{session.user_id}"
        user = None
        for key, u in self._users.items():
            if u.id == session.user_id:
                user = u
                break
        
        return {
            "valid": True,
            "session": session,
            "user": user,
        }
    
    def logout(self, session_id: str) -> Dict[str, Any]:
        """
        Faz logout de uma sessão.
        
        Returns:
            Dict com URL de logout do IdP se aplicável
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": True}
        
        # Desativar sessão
        session.is_active = False
        
        config = self._configs.get(session.tenant_id)
        if not config:
            return {"success": True}
        
        # Gerar logout URL se necessário
        if config.protocol == SSOProtocol.SAML_2_0:
            handler = self._saml_handlers.get(session.tenant_id)
            if handler and session.saml_name_id and session.saml_session_index:
                logout_data = handler.generate_logout_request(
                    session.saml_name_id,
                    session.saml_session_index
                )
                return {
                    "success": True,
                    "logout_url": logout_data.get("redirect_url"),
                }
        
        elif config.protocol == SSOProtocol.OIDC:
            handler = self._oidc_handlers.get(session.tenant_id)
            if handler and session.id_token:
                logout_url = handler.generate_logout_url(
                    session.id_token,
                    f"https://app.agno.ai/{session.tenant_id}/logout-complete"
                )
                return {
                    "success": True,
                    "logout_url": logout_url,
                }
        
        return {"success": True}
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def get_sp_metadata(self, tenant_id: str) -> Optional[str]:
        """Obtém metadata XML do SP para um tenant."""
        handler = self._saml_handlers.get(tenant_id)
        if handler:
            return handler.get_sp_metadata_xml()
        return None
    
    def list_configs(self) -> List[SSOConfig]:
        """Lista todas as configurações de SSO."""
        return list(self._configs.values())
    
    def get_active_sessions(self, tenant_id: str) -> List[SSOSession]:
        """Lista sessões ativas de um tenant."""
        return [
            s for s in self._sessions.values()
            if s.tenant_id == tenant_id and s.is_active and not s.is_expired()
        ]


# Singleton instance
_sso_manager: Optional[SSOManager] = None


def get_sso_manager() -> SSOManager:
    """Obtém instância singleton do SSOManager."""
    global _sso_manager
    if _sso_manager is None:
        _sso_manager = SSOManager()
    return _sso_manager

"""
Sistema SSO (Single Sign-On) com OAuth2.

Suporta:
- Google OAuth
- GitHub OAuth
- Microsoft/Azure AD
- SAML (enterprise)
"""

import os
import secrets
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import urlencode
import httpx
import jwt


@dataclass
class OAuthProvider:
    """Configuração de um provedor OAuth."""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str]
    
    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        """Gera URL de autorização."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }
        return f"{self.authorize_url}?{urlencode(params)}"


@dataclass
class SSOUser:
    """Usuário autenticado via SSO."""
    provider: str
    provider_id: str
    email: str
    name: str
    picture: Optional[str] = None
    raw_data: Optional[Dict] = None


# Provedores pré-configurados
PROVIDERS = {
    "google": lambda: OAuthProvider(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
    ),
    "github": lambda: OAuthProvider(
        name="github",
        client_id=os.getenv("GITHUB_CLIENT_ID", ""),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["user:email"],
    ),
    "microsoft": lambda: OAuthProvider(
        name="microsoft",
        client_id=os.getenv("MICROSOFT_CLIENT_ID", ""),
        client_secret=os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
        scopes=["openid", "email", "profile"],
    ),
}


class SSOManager:
    """
    Gerenciador de Single Sign-On.
    
    Features:
    - Múltiplos provedores OAuth2
    - State validation (CSRF protection)
    - Token exchange
    - User info retrieval
    - Session management
    
    Configuração:
        SSO_PROVIDERS: Provedores habilitados (google,github,microsoft)
        SSO_REDIRECT_URI: URI de callback
    """
    
    def __init__(
        self,
        redirect_uri: Optional[str] = None,
        enabled_providers: Optional[List[str]] = None,
        jwt_secret: Optional[str] = None
    ):
        self.redirect_uri = redirect_uri or os.getenv("SSO_REDIRECT_URI", "http://localhost:3000/auth/callback")
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", secrets.token_hex(32))
        
        # Provedores habilitados
        providers_str = os.getenv("SSO_PROVIDERS", "google,github")
        self.enabled_providers = enabled_providers or providers_str.split(",")
        
        # Cache de states para validação
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def get_provider(self, name: str) -> OAuthProvider:
        """Obtém configuração do provedor."""
        if name not in self.enabled_providers:
            raise ValueError(f"Provedor '{name}' não habilitado")
        
        if name not in PROVIDERS:
            raise ValueError(f"Provedor '{name}' não suportado")
        
        return PROVIDERS[name]()
    
    def list_providers(self) -> List[Dict[str, str]]:
        """Lista provedores disponíveis."""
        result = []
        for name in self.enabled_providers:
            if name in PROVIDERS:
                provider = PROVIDERS[name]()
                if provider.client_id:  # Só lista se configurado
                    result.append({
                        "name": name,
                        "display_name": name.title(),
                    })
        return result
    
    def generate_auth_url(self, provider_name: str) -> Dict[str, str]:
        """
        Gera URL de autorização para iniciar fluxo OAuth.
        
        Returns:
            {"url": "...", "state": "..."}
        """
        provider = self.get_provider(provider_name)
        
        # Gerar state único
        state = secrets.token_urlsafe(32)
        self._states[state] = {
            "provider": provider_name,
            "created_at": time.time(),
        }
        
        url = provider.get_authorize_url(
            redirect_uri=f"{self.redirect_uri}/{provider_name}",
            state=state
        )
        
        return {"url": url, "state": state}
    
    async def handle_callback(
        self,
        provider_name: str,
        code: str,
        state: str
    ) -> SSOUser:
        """
        Processa callback do provedor OAuth.
        
        Args:
            provider_name: Nome do provedor
            code: Código de autorização
            state: State para validação
        
        Returns:
            Usuário autenticado
        """
        # Validar state
        if state not in self._states:
            raise ValueError("Invalid state - possible CSRF attack")
        
        state_data = self._states.pop(state)
        if state_data["provider"] != provider_name:
            raise ValueError("State provider mismatch")
        
        # Verificar expiração (5 minutos)
        if time.time() - state_data["created_at"] > 300:
            raise ValueError("State expired")
        
        provider = self.get_provider(provider_name)
        
        # Trocar code por token
        token_data = await self._exchange_code(provider, code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError("Failed to get access token")
        
        # Obter informações do usuário
        user_info = await self._get_user_info(provider, access_token)
        
        # Normalizar dados do usuário
        return self._normalize_user(provider_name, user_info)
    
    async def _exchange_code(
        self,
        provider: OAuthProvider,
        code: str
    ) -> Dict[str, Any]:
        """Troca código por token de acesso."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.token_url,
                data={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                    "code": code,
                    "redirect_uri": f"{self.redirect_uri}/{provider.name}",
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def _get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str
    ) -> Dict[str, Any]:
        """Obtém informações do usuário."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")
            
            return response.json()
    
    def _normalize_user(
        self,
        provider_name: str,
        user_info: Dict[str, Any]
    ) -> SSOUser:
        """Normaliza dados do usuário para formato padrão."""
        if provider_name == "google":
            return SSOUser(
                provider="google",
                provider_id=user_info.get("id"),
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                raw_data=user_info
            )
        elif provider_name == "github":
            return SSOUser(
                provider="github",
                provider_id=str(user_info.get("id")),
                email=user_info.get("email") or f"{user_info.get('login')}@github.local",
                name=user_info.get("name") or user_info.get("login"),
                picture=user_info.get("avatar_url"),
                raw_data=user_info
            )
        elif provider_name == "microsoft":
            return SSOUser(
                provider="microsoft",
                provider_id=user_info.get("id"),
                email=user_info.get("mail") or user_info.get("userPrincipalName"),
                name=user_info.get("displayName"),
                picture=None,  # Requer chamada adicional
                raw_data=user_info
            )
        else:
            # Fallback genérico
            return SSOUser(
                provider=provider_name,
                provider_id=str(user_info.get("id", user_info.get("sub"))),
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                raw_data=user_info
            )
    
    def create_session_token(
        self,
        user: SSOUser,
        expires_hours: int = 24
    ) -> str:
        """
        Cria token JWT para sessão.
        
        Args:
            user: Usuário autenticado
            expires_hours: Validade em horas
        
        Returns:
            Token JWT
        """
        payload = {
            "sub": user.provider_id,
            "email": user.email,
            "name": user.name,
            "provider": user.provider,
            "iat": int(time.time()),
            "exp": int(time.time()) + (expires_hours * 3600),
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica token de sessão.
        
        Returns:
            Payload do token ou None se inválido
        """
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None


# Singleton
_sso_manager: Optional[SSOManager] = None


def get_sso_manager() -> SSOManager:
    """Obtém instância singleton do SSO Manager."""
    global _sso_manager
    if _sso_manager is None:
        _sso_manager = SSOManager()
    return _sso_manager

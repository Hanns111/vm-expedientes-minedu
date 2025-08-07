"""
Autenticación OAuth2 empresarial con Google y Microsoft
Implementación segura con PKCE, state validation y refresh tokens
"""
import os
import secrets
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, parse_qs
import httpx
import jwt
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from pydantic import BaseModel, validator
import logging

logger = logging.getLogger(__name__)

class OAuth2Config:
    """Configuración OAuth2 para diferentes providers"""
    
    def __init__(self):
        # Google OAuth2
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/oauth2/google/callback")
        
        # Microsoft OAuth2 (Azure AD)
        self.microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.microsoft_tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")  # 'common' for multi-tenant
        self.microsoft_redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/oauth2/microsoft/callback")
        
        # Security settings
        self.state_secret = os.getenv("OAUTH2_STATE_SECRET", "oauth2-state-secret-change-in-production")
        
        # Endpoints
        self.google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        self.microsoft_auth_url = f"https://login.microsoftonline.com/{self.microsoft_tenant_id}/oauth2/v2.0/authorize"
        self.microsoft_token_url = f"https://login.microsoftonline.com/{self.microsoft_tenant_id}/oauth2/v2.0/token"
        self.microsoft_userinfo_url = "https://graph.microsoft.com/v1.0/me"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validar configuración OAuth2"""
        if not self.google_client_id or not self.google_client_secret:
            logger.warning("Google OAuth2 not configured")
        
        if not self.microsoft_client_id or not self.microsoft_client_secret:
            logger.warning("Microsoft OAuth2 not configured")
        
        if not self.google_client_id and not self.microsoft_client_id:
            raise ValueError("At least one OAuth2 provider must be configured")

class OAuth2State(BaseModel):
    """Estado OAuth2 para validación de seguridad"""
    provider: str
    redirect_url: Optional[str] = None
    timestamp: float
    code_verifier: Optional[str] = None  # Para PKCE
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['google', 'microsoft']:
            raise ValueError('Provider must be google or microsoft')
        return v

class OAuth2UserInfo(BaseModel):
    """Información del usuario desde OAuth2"""
    provider: str
    provider_id: str
    email: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    verified_email: bool = False

class OAuth2Manager:
    """Manager principal para autenticación OAuth2"""
    
    def __init__(self, config: Optional[OAuth2Config] = None):
        self.config = config or OAuth2Config()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generar par PKCE (code_verifier, code_challenge)"""
        # Generate code_verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')
        
        # Generate code_challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def create_state_token(self, state_data: OAuth2State) -> str:
        """Crear token de estado firmado"""
        payload = {
            "provider": state_data.provider,
            "redirect_url": state_data.redirect_url,
            "timestamp": state_data.timestamp,
            "code_verifier": state_data.code_verifier,
            "exp": datetime.utcnow() + timedelta(minutes=10)  # 10 min expiry
        }
        
        return jwt.encode(payload, self.config.state_secret, algorithm="HS256")
    
    def verify_state_token(self, state_token: str) -> OAuth2State:
        """Verificar token de estado"""
        try:
            payload = jwt.decode(state_token, self.config.state_secret, algorithms=["HS256"])
            return OAuth2State(**payload)
        except jwt.PyJWTError as e:
            logger.error(f"Invalid state token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state token"
            )
    
    async def get_google_auth_url(self, redirect_url: Optional[str] = None) -> Tuple[str, str]:
        """Obtener URL de autorización de Google"""
        if not self.config.google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth2 not configured"
            )
        
        # Generate PKCE pair
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Create state
        state_data = OAuth2State(
            provider="google",
            redirect_url=redirect_url,
            timestamp=datetime.utcnow().timestamp(),
            code_verifier=code_verifier
        )
        state_token = self.create_state_token(state_data)
        
        # Build authorization URL
        params = {
            "client_id": self.config.google_client_id,
            "redirect_uri": self.config.google_redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state_token,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",  # For refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        auth_url = f"{self.config.google_auth_url}?{urlencode(params)}"
        return auth_url, state_token
    
    async def get_microsoft_auth_url(self, redirect_url: Optional[str] = None) -> Tuple[str, str]:
        """Obtener URL de autorización de Microsoft"""
        if not self.config.microsoft_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Microsoft OAuth2 not configured"
            )
        
        # Generate PKCE pair
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Create state
        state_data = OAuth2State(
            provider="microsoft",
            redirect_url=redirect_url,
            timestamp=datetime.utcnow().timestamp(),
            code_verifier=code_verifier
        )
        state_token = self.create_state_token(state_data)
        
        # Build authorization URL
        params = {
            "client_id": self.config.microsoft_client_id,
            "redirect_uri": self.config.microsoft_redirect_uri,
            "scope": "openid email profile User.Read",
            "response_type": "code",
            "state": state_token,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query"
        }
        
        auth_url = f"{self.config.microsoft_auth_url}?{urlencode(params)}"
        return auth_url, state_token
    
    async def exchange_google_code(self, code: str, state_token: str) -> OAuth2UserInfo:
        """Intercambiar código de Google por información del usuario"""
        # Verify state
        state_data = self.verify_state_token(state_token)
        if state_data.provider != "google":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State token provider mismatch"
            )
        
        # Exchange code for tokens
        token_data = {
            "client_id": self.config.google_client_id,
            "client_secret": self.config.google_client_secret,
            "redirect_uri": self.config.google_redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": state_data.code_verifier
        }
        
        try:
            # Get access token
            token_response = await self.http_client.post(
                self.config.google_token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = await self.http_client.get(
                self.config.google_userinfo_url,
                headers=headers
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Parse user info
            return OAuth2UserInfo(
                provider="google",
                provider_id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                given_name=user_data.get("given_name"),
                family_name=user_data.get("family_name"),
                picture=user_data.get("picture"),
                verified_email=user_data.get("verified_email", False)
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Google OAuth2 error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Google"
            )
    
    async def exchange_microsoft_code(self, code: str, state_token: str) -> OAuth2UserInfo:
        """Intercambiar código de Microsoft por información del usuario"""
        # Verify state
        state_data = self.verify_state_token(state_token)
        if state_data.provider != "microsoft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State token provider mismatch"
            )
        
        # Exchange code for tokens
        token_data = {
            "client_id": self.config.microsoft_client_id,
            "client_secret": self.config.microsoft_client_secret,
            "redirect_uri": self.config.microsoft_redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": state_data.code_verifier
        }
        
        try:
            # Get access token
            token_response = await self.http_client.post(
                self.config.microsoft_token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = await self.http_client.get(
                self.config.microsoft_userinfo_url,
                headers=headers
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Parse user info
            return OAuth2UserInfo(
                provider="microsoft",
                provider_id=user_data["id"],
                email=user_data["mail"] or user_data.get("userPrincipalName", ""),
                name=user_data["displayName"],
                given_name=user_data.get("givenName"),
                family_name=user_data.get("surname"),
                picture=None,  # Microsoft Graph requires separate call for photo
                verified_email=True  # Microsoft emails are verified
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Microsoft OAuth2 error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Microsoft"
            )
    
    async def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Obtener providers OAuth2 disponibles"""
        providers = {}
        
        if self.config.google_client_id:
            providers["google"] = {
                "name": "Google",
                "icon": "https://developers.google.com/identity/images/g-logo.png",
                "color": "#4285f4",
                "enabled": True
            }
        
        if self.config.microsoft_client_id:
            providers["microsoft"] = {
                "name": "Microsoft",
                "icon": "https://docs.microsoft.com/en-us/azure/active-directory/develop/media/howto-add-branding-in-azure-ad-apps/ms-symbollockup_mssymbol_19.png",
                "color": "#00a1f1",
                "enabled": True
            }
        
        return providers
    
    async def close(self):
        """Cerrar cliente HTTP"""
        await self.http_client.aclose()

# Instancia global
oauth2_manager = OAuth2Manager()

# Funciones de utilidad
async def get_oauth2_auth_url(provider: str, redirect_url: Optional[str] = None) -> Tuple[str, str]:
    """Obtener URL de autorización OAuth2"""
    if provider == "google":
        return await oauth2_manager.get_google_auth_url(redirect_url)
    elif provider == "microsoft":
        return await oauth2_manager.get_microsoft_auth_url(redirect_url)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth2 provider: {provider}"
        )

async def handle_oauth2_callback(provider: str, code: str, state: str) -> OAuth2UserInfo:
    """Manejar callback OAuth2"""
    if provider == "google":
        return await oauth2_manager.exchange_google_code(code, state)
    elif provider == "microsoft":
        return await oauth2_manager.exchange_microsoft_code(code, state)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth2 provider: {provider}"
        )

def validate_oauth2_config() -> Dict[str, bool]:
    """Validar configuración OAuth2"""
    config = OAuth2Config()
    return {
        "google_configured": bool(config.google_client_id and config.google_client_secret),
        "microsoft_configured": bool(config.microsoft_client_id and config.microsoft_client_secret),
        "any_provider_configured": bool(
            (config.google_client_id and config.google_client_secret) or
            (config.microsoft_client_id and config.microsoft_client_secret)
        )
    }
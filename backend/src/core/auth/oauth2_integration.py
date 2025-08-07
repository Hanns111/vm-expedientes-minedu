"""
Integración OAuth2 con el sistema de autenticación existente
Combina OAuth2 con JWT tokens y gestión de usuarios en PostgreSQL
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import UUID
import logging

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .oauth2_providers import OAuth2UserInfo, oauth2_manager
from .jwt_auth import JWTAuth, TokenResponse
from ..database.repositories import UnitOfWork, UserRepository
from ..database.models import User

logger = logging.getLogger(__name__)

class OAuth2AuthService:
    """Servicio de autenticación OAuth2 integrado"""
    
    def __init__(self):
        self.jwt_auth = JWTAuth()
    
    async def authenticate_or_create_user(
        self,
        oauth_info: OAuth2UserInfo,
        session: AsyncSession,
        request: Request
    ) -> Tuple[User, TokenResponse]:
        """Autenticar o crear usuario desde OAuth2"""
        
        async with UnitOfWork(session) as uow:
            try:
                # Buscar usuario existente por OAuth ID
                user = await uow.users.get_by_oauth_id(oauth_info.provider, oauth_info.provider_id)
                
                if user:
                    # Usuario existente - actualizar información
                    user = await self._update_existing_user(user, oauth_info, uow)
                    logger.info(f"OAuth2 login for existing user: {user.email}")
                else:
                    # Verificar si existe usuario con el mismo email
                    existing_user = await uow.users.get_by_email(oauth_info.email)
                    if existing_user:
                        # Vincular cuenta OAuth2 existente
                        user = await self._link_oauth_to_existing_user(existing_user, oauth_info, uow)
                        logger.info(f"Linked OAuth2 to existing user: {user.email}")
                    else:
                        # Crear nuevo usuario
                        user = await self._create_new_oauth_user(oauth_info, uow)
                        logger.info(f"Created new OAuth2 user: {user.email}")
                
                # Actualizar última actividad
                await uow.users.update_last_activity(user.id)
                user.last_login = datetime.now(timezone.utc)
                
                # Crear token JWT
                token_response = await self._create_jwt_token(user, request, uow)
                
                # Log de auditoría
                await uow.audit.log_action(
                    user_id=user.id,
                    action="oauth2_login",
                    resource="user",
                    resource_id=str(user.id),
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", ""),
                    endpoint=str(request.url),
                    method=request.method,
                    status_code=200,
                    response_time=0.0,
                    details={
                        "provider": oauth_info.provider,
                        "oauth_id": oauth_info.provider_id,
                        "verified_email": oauth_info.verified_email
                    }
                )
                
                await uow.commit()
                return user, token_response
                
            except Exception as e:
                await uow.rollback()
                logger.error(f"OAuth2 authentication failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication failed"
                )
    
    async def _update_existing_user(
        self,
        user: User,
        oauth_info: OAuth2UserInfo,
        uow: UnitOfWork
    ) -> User:
        """Actualizar usuario existente con información OAuth2"""
        updates = {}
        
        # Actualizar nombre si es diferente
        if user.full_name != oauth_info.name:
            updates["full_name"] = oauth_info.name
        
        # Actualizar foto de perfil si está disponible
        if oauth_info.picture and user.profile_picture != oauth_info.picture:
            updates["profile_picture"] = oauth_info.picture
        
        # Marcar como verificado si el email está verificado en OAuth2
        if oauth_info.verified_email and not user.is_verified:
            updates["is_verified"] = True
        
        # Actualizar última actividad
        updates["last_login"] = datetime.now(timezone.utc)
        
        if updates:
            user = await uow.users.update(user.id, **updates)
        
        return user
    
    async def _link_oauth_to_existing_user(
        self,
        user: User,
        oauth_info: OAuth2UserInfo,
        uow: UnitOfWork
    ) -> User:
        """Vincular OAuth2 a usuario existente"""
        updates = {}
        
        # Agregar ID de OAuth2
        if oauth_info.provider == "google":
            if user.google_id and user.google_id != oauth_info.provider_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este email ya está vinculado a otra cuenta de Google"
                )
            updates["google_id"] = oauth_info.provider_id
        elif oauth_info.provider == "microsoft":
            if user.microsoft_id and user.microsoft_id != oauth_info.provider_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este email ya está vinculado a otra cuenta de Microsoft"
                )
            updates["microsoft_id"] = oauth_info.provider_id
        
        # Actualizar provider si no estaba configurado
        if not user.provider or user.provider == "local":
            updates["provider"] = oauth_info.provider
        
        # Marcar como verificado
        if oauth_info.verified_email:
            updates["is_verified"] = True
        
        # Actualizar foto de perfil si no tiene una
        if not user.profile_picture and oauth_info.picture:
            updates["profile_picture"] = oauth_info.picture
        
        return await uow.users.update(user.id, **updates)
    
    async def _create_new_oauth_user(
        self,
        oauth_info: OAuth2UserInfo,
        uow: UnitOfWork
    ) -> User:
        """Crear nuevo usuario desde OAuth2"""
        return await uow.users.create_oauth_user(
            email=oauth_info.email,
            full_name=oauth_info.name,
            provider=oauth_info.provider,
            oauth_id=oauth_info.provider_id,
            profile_picture=oauth_info.picture
        )
    
    async def _create_jwt_token(
        self,
        user: User,
        request: Request,
        uow: UnitOfWork
    ) -> TokenResponse:
        """Crear token JWT y sesión"""
        # Crear token JWT
        access_token = self.jwt_auth.create_access_token(
            username=user.username,
            roles=list(user.roles.keys()) if user.roles else ["user"]
        )
        
        # Decodificar token para obtener JTI
        token_payload = self.jwt_auth.verify_token(access_token)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create valid token"
            )
        
        # Crear sesión en base de datos
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        await uow.sessions.create(
            user_id=user.id,
            jti=f"oauth2_{user.id}_{datetime.now().timestamp()}",  # Simple JTI for OAuth2
            token_type="access",
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            expires_at=expires_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours
            user=user
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente"""
        # Check for forwarded headers (load balancer, proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return str(request.client.host) if request.client else "unknown"
    
    async def unlink_oauth_provider(
        self,
        user_id: UUID,
        provider: str,
        session: AsyncSession
    ) -> bool:
        """Desvincular provider OAuth2 de usuario"""
        async with UnitOfWork(session) as uow:
            try:
                user = await uow.users.get_by_id(user_id)
                if not user:
                    return False
                
                # Verificar que el usuario tenga otro método de autenticación
                has_password = bool(user.hashed_password)
                has_other_oauth = False
                
                if provider == "google":
                    has_other_oauth = bool(user.microsoft_id)
                elif provider == "microsoft":
                    has_other_oauth = bool(user.google_id)
                
                if not has_password and not has_other_oauth:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot unlink last authentication method. Set a password first."
                    )
                
                # Remover OAuth2 ID
                updates = {}
                if provider == "google":
                    updates["google_id"] = None
                elif provider == "microsoft":
                    updates["microsoft_id"] = None
                
                # Si era el provider principal, cambiar a local o al otro
                if user.provider == provider:
                    if has_password:
                        updates["provider"] = "local"
                    elif provider == "google" and user.microsoft_id:
                        updates["provider"] = "microsoft"
                    elif provider == "microsoft" and user.google_id:
                        updates["provider"] = "google"
                
                await uow.users.update(user_id, **updates)
                await uow.commit()
                
                logger.info(f"Unlinked {provider} from user {user.email}")
                return True
                
            except Exception as e:
                await uow.rollback()
                logger.error(f"Failed to unlink OAuth2 provider: {e}")
                raise
    
    async def get_user_oauth_status(
        self,
        user_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Obtener estado OAuth2 del usuario"""
        async with UnitOfWork(session) as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "primary_provider": user.provider,
                "has_password": bool(user.hashed_password),
                "linked_providers": {
                    "google": {
                        "linked": bool(user.google_id),
                        "id": user.google_id if user.google_id else None
                    },
                    "microsoft": {
                        "linked": bool(user.microsoft_id),
                        "id": user.microsoft_id if user.microsoft_id else None
                    }
                },
                "available_providers": await oauth2_manager.get_available_providers()
            }

# Servicios globales
oauth2_service = OAuth2AuthService()

# Funciones de utilidad para FastAPI
async def initiate_oauth2_login(provider: str, redirect_url: Optional[str] = None) -> Dict[str, str]:
    """Iniciar proceso de login OAuth2"""
    try:
        auth_url, state_token = await oauth2_manager.get_oauth2_auth_url(provider, redirect_url)
        return {
            "auth_url": auth_url,
            "state": state_token,
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Failed to initiate OAuth2 login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth2 login"
        )

async def complete_oauth2_login(
    provider: str,
    code: str,
    state: str,
    request: Request,
    session: AsyncSession
) -> TokenResponse:
    """Completar proceso de login OAuth2"""
    try:
        # Intercambiar código por información del usuario
        oauth_info = await oauth2_manager.handle_oauth2_callback(provider, code, state)
        
        # Autenticar o crear usuario
        user, token_response = await oauth2_service.authenticate_or_create_user(
            oauth_info, session, request
        )
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 login completion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth2 authentication failed"
        )
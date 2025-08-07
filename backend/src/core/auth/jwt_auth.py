"""
Autenticación JWT profesional para FastAPI
Implementación segura con roles y permisos
"""
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuración JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "minedu-rag-secret-key-2025-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class User(BaseModel):
    """Modelo de usuario"""
    username: str
    email: str
    full_name: str
    roles: List[str] = ["user"]
    is_active: bool = True
    created_at: datetime = datetime.now()

class UserInDB(User):
    """Usuario en base de datos con password hash"""
    hashed_password: str

class TokenData(BaseModel):
    """Datos del token JWT"""
    username: Optional[str] = None
    roles: List[str] = []
    exp: Optional[datetime] = None

class LoginRequest(BaseModel):
    """Request de login"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Response de token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

# Base de datos en memoria para desarrollo (en producción usar BD real)
USERS_DB = {
    "admin": UserInDB(
        username="admin",
        email="admin@minedu.gob.pe",
        full_name="Administrador MINEDU",
        roles=["admin", "user"],
        is_active=True,
        hashed_password=pwd_context.hash("admin123")  # Cambiar en producción
    ),
    "consultor": UserInDB(
        username="consultor",
        email="consultor@minedu.gob.pe", 
        full_name="Consultor RAG",
        roles=["user"],
        is_active=True,
        hashed_password=pwd_context.hash("consultor123")
    ),
    "demo": UserInDB(
        username="demo",
        email="demo@minedu.gob.pe",
        full_name="Usuario Demo",
        roles=["demo"],
        is_active=True,
        hashed_password=pwd_context.hash("demo123")
    )
}

class JWTAuth:
    """Clase principal para autenticación JWT"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash de password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
        """Autenticar usuario"""
        user = USERS_DB.get(username)
        if not user:
            return None
        if not JWTAuth.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_access_token(username: str, roles: List[str]) -> str:
        """Crear token JWT"""
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "sub": username,
            "roles": roles,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verificar y decodificar token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            roles = payload.get("roles", [])
            exp = datetime.fromtimestamp(payload.get("exp"))
            
            if username is None:
                return None
                
            return TokenData(username=username, roles=roles, exp=exp)
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def get_user(username: str) -> Optional[User]:
        """Obtener usuario por username"""
        user_db = USERS_DB.get(username)
        if user_db:
            return User(**user_db.dict(exclude={"hashed_password"}))
        return None

# Dependencias de FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Dependencia para obtener usuario actual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        token_data = JWTAuth.verify_token(token)
        
        if token_data is None or token_data.username is None:
            raise credentials_exception
            
        # Verificar expiración
        if token_data.exp and token_data.exp < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = JWTAuth.get_user(token_data.username)
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception as e:
        raise credentials_exception

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependencia para verificar rol admin"""
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol admin."
        )
    return current_user

async def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependencia para verificar usuario activo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user

class RoleChecker:
    """Clase para verificar roles específicos"""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not any(role in current_user.roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(self.required_roles)}"
            )
        return current_user

# Instancias de verificadores de roles
require_admin = RoleChecker(["admin"])
require_user = RoleChecker(["user", "admin"])
require_demo = RoleChecker(["demo", "user", "admin"])

def create_api_key(username: str, purpose: str = "api_access") -> str:
    """Crear API key para acceso programático"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{username}:{purpose}:{timestamp}"
    
    # Hash simple para API key
    api_key = hashlib.sha256(f"{data}:{JWT_SECRET_KEY}".encode()).hexdigest()[:32]
    return f"mk_{api_key}"

def verify_api_key(api_key: str) -> Optional[str]:
    """Verificar API key (implementación básica)"""
    # En producción, almacenar en BD con metadatos
    if api_key.startswith("mk_") and len(api_key) == 35:
        # Para desarrollo, permitir ciertas API keys
        dev_keys = {
            "mk_dev_admin_2025": "admin",
            "mk_dev_user_2025": "consultor",
            "mk_demo_2025": "demo"
        }
        return dev_keys.get(api_key)
    return None

async def get_user_from_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Autenticación alternativa con API key"""
    api_key = credentials.credentials
    username = verify_api_key(api_key)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = JWTAuth.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return user

# Rate limiting básico (en producción usar Redis)
from collections import defaultdict
import time

class RateLimiter:
    """Rate limiter básico por usuario"""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(list)
    
    def is_allowed(self, username: str) -> bool:
        """Verificar si el usuario puede hacer request"""
        now = time.time()
        user_requests = self.requests[username]
        
        # Limpiar requests antiguos
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.window_seconds]
        
        # Verificar límite
        if len(user_requests) >= self.max_requests:
            return False
        
        # Agregar request actual
        user_requests.append(now)
        return True

rate_limiter = RateLimiter()

async def check_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    """Dependencia para verificar rate limiting"""
    if not rate_limiter.is_allowed(current_user.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Intenta más tarde."
        )
    return current_user
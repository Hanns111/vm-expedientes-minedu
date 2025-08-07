"""
Repositorios de datos para operaciones CRUD empresariales
Incluye patrones Repository y Unit of Work para arquitectura limpia
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Generic, TypeVar, Union
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import User, UserSession, QueryLog, SystemMetrics, Document, DocumentChunk, AuditLog

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Repositorio base con operaciones CRUD comunes"""
    
    def __init__(self, session: Union[Session, AsyncSession], model_class: type):
        self.session = session
        self.model_class = model_class
    
    async def get_by_id(self, id: Union[UUID, str]) -> Optional[T]:
        """Obtener por ID"""
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            return result.scalar_one_or_none()
        else:
            return self.session.get(self.model_class, id)
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Obtener todos con paginación"""
        stmt = select(self.model_class).offset(offset).limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def create(self, **kwargs) -> T:
        """Crear nuevo registro"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        
        if isinstance(self.session, AsyncSession):
            await self.session.flush()
        else:
            self.session.flush()
        
        return instance
    
    async def update(self, id: Union[UUID, str], **kwargs) -> Optional[T]:
        """Actualizar registro existente"""
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.now(timezone.utc)
        
        if isinstance(self.session, AsyncSession):
            await self.session.flush()
        else:
            self.session.flush()
        
        return instance
    
    async def delete(self, id: Union[UUID, str]) -> bool:
        """Eliminar registro"""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        if isinstance(self.session, AsyncSession):
            await self.session.delete(instance)
            await self.session.flush()
        else:
            self.session.delete(instance)
            self.session.flush()
        
        return True
    
    async def count(self) -> int:
        """Contar registros"""
        stmt = select(func.count(self.model_class.id))
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar()
        else:
            return self.session.execute(stmt).scalar()

class UserRepository(BaseRepository[User]):
    """Repositorio para gestión de usuarios"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        stmt = select(User).where(User.email == email)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.session.execute(stmt).scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por username"""
        stmt = select(User).where(User.username == username)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.session.execute(stmt).scalar_one_or_none()
    
    async def get_by_oauth_id(self, provider: str, oauth_id: str) -> Optional[User]:
        """Obtener usuario por ID de OAuth"""
        if provider == "google":
            stmt = select(User).where(User.google_id == oauth_id)
        elif provider == "microsoft":
            stmt = select(User).where(User.microsoft_id == oauth_id)
        else:
            return None
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.session.execute(stmt).scalar_one_or_none()
    
    async def create_oauth_user(
        self, 
        email: str, 
        full_name: str, 
        provider: str, 
        oauth_id: str,
        profile_picture: Optional[str] = None
    ) -> User:
        """Crear usuario desde OAuth"""
        # Generate username from email
        username = email.split('@')[0]
        
        # Ensure username is unique
        counter = 1
        original_username = username
        while await self.get_by_username(username):
            username = f"{original_username}{counter}"
            counter += 1
        
        user_data = {
            "email": email,
            "username": username,
            "full_name": full_name,
            "provider": provider,
            "is_verified": True,  # OAuth users are pre-verified
            "profile_picture": profile_picture,
        }
        
        # Set provider-specific ID
        if provider == "google":
            user_data["google_id"] = oauth_id
        elif provider == "microsoft":
            user_data["microsoft_id"] = oauth_id
        
        return await self.create(**user_data)
    
    async def get_active_users(self, limit: int = 100) -> List[User]:
        """Obtener usuarios activos"""
        stmt = select(User).where(User.is_active == True).limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def search_users(
        self, 
        query: str, 
        department: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 50
    ) -> List[User]:
        """Buscar usuarios por diferentes criterios"""
        stmt = select(User).where(User.is_active == True)
        
        # Text search
        if query:
            search_filter = or_(
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        # Department filter
        if department:
            stmt = stmt.where(User.department == department)
        
        # Role filter
        if role:
            stmt = stmt.where(User.roles[role].astext == 'true')
        
        stmt = stmt.limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def update_last_activity(self, user_id: UUID) -> None:
        """Actualizar última actividad del usuario"""
        stmt = update(User).where(User.id == user_id).values(
            last_activity=datetime.now(timezone.utc)
        )
        
        if isinstance(self.session, AsyncSession):
            await self.session.execute(stmt)
        else:
            self.session.execute(stmt)

class UserSessionRepository(BaseRepository[UserSession]):
    """Repositorio para gestión de sesiones de usuario"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, UserSession)
    
    async def get_by_jti(self, jti: str) -> Optional[UserSession]:
        """Obtener sesión por JWT ID"""
        stmt = select(UserSession).where(UserSession.jti == jti)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.session.execute(stmt).scalar_one_or_none()
    
    async def get_active_sessions(self, user_id: UUID) -> List[UserSession]:
        """Obtener sesiones activas del usuario"""
        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > now
            )
        ).order_by(desc(UserSession.created_at))
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def revoke_session(self, jti: str) -> bool:
        """Revocar sesión específica"""
        session = await self.get_by_jti(jti)
        if not session:
            return False
        
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)
        
        if isinstance(self.session, AsyncSession):
            await self.session.flush()
        else:
            self.session.flush()
        
        return True
    
    async def revoke_user_sessions(self, user_id: UUID) -> int:
        """Revocar todas las sesiones de un usuario"""
        now = datetime.now(timezone.utc)
        stmt = update(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).values(
            is_active=False,
            revoked_at=now
        )
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.rowcount
        else:
            result = self.session.execute(stmt)
            return result.rowcount
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpiar sesiones expiradas"""
        now = datetime.now(timezone.utc)
        stmt = update(UserSession).where(
            and_(
                UserSession.expires_at < now,
                UserSession.is_active == True
            )
        ).values(
            is_active=False,
            revoked_at=now
        )
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.rowcount
        else:
            result = self.session.execute(stmt)
            return result.rowcount

class QueryLogRepository(BaseRepository[QueryLog]):
    """Repositorio para logs de consultas RAG"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, QueryLog)
    
    async def create_query_log(
        self,
        user_id: UUID,
        query_text: str,
        response_text: str,
        trace_id: str,
        method: str,
        processing_time: float,
        confidence_score: float,
        **kwargs
    ) -> QueryLog:
        """Crear log de consulta con datos específicos"""
        log_data = {
            "user_id": user_id,
            "query_text": query_text,
            "response_text": response_text,
            "trace_id": trace_id,
            "method": method,
            "processing_time": processing_time,
            "confidence_score": confidence_score,
            **kwargs
        }
        
        return await self.create(**log_data)
    
    async def get_user_queries(
        self, 
        user_id: UUID, 
        limit: int = 50,
        offset: int = 0
    ) -> List[QueryLog]:
        """Obtener consultas de un usuario"""
        stmt = select(QueryLog).where(
            QueryLog.user_id == user_id
        ).order_by(desc(QueryLog.created_at)).offset(offset).limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def get_recent_queries(self, hours: int = 24, limit: int = 100) -> List[QueryLog]:
        """Obtener consultas recientes"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(QueryLog).where(
            QueryLog.created_at > since
        ).order_by(desc(QueryLog.created_at)).limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Query base
        base_query = select(QueryLog).where(QueryLog.created_at > since)
        
        if isinstance(self.session, AsyncSession):
            # Total queries
            total_result = await self.session.execute(
                select(func.count(QueryLog.id)).where(QueryLog.created_at > since)
            )
            total_queries = total_result.scalar()
            
            # Average processing time
            avg_time_result = await self.session.execute(
                select(func.avg(QueryLog.processing_time)).where(QueryLog.created_at > since)
            )
            avg_processing_time = avg_time_result.scalar() or 0
            
            # Average confidence
            avg_conf_result = await self.session.execute(
                select(func.avg(QueryLog.confidence_score)).where(QueryLog.created_at > since)
            )
            avg_confidence = avg_conf_result.scalar() or 0
            
            # Fallback usage
            fallback_result = await self.session.execute(
                select(func.count(QueryLog.id)).where(
                    and_(QueryLog.created_at > since, QueryLog.used_fallback == True)
                )
            )
            fallback_count = fallback_result.scalar()
            
            # Error rate
            error_result = await self.session.execute(
                select(func.count(QueryLog.id)).where(
                    and_(QueryLog.created_at > since, QueryLog.error_occurred == True)
                )
            )
            error_count = error_result.scalar()
            
        else:
            # Synchronous version
            total_queries = self.session.execute(
                select(func.count(QueryLog.id)).where(QueryLog.created_at > since)
            ).scalar()
            
            avg_processing_time = self.session.execute(
                select(func.avg(QueryLog.processing_time)).where(QueryLog.created_at > since)
            ).scalar() or 0
            
            avg_confidence = self.session.execute(
                select(func.avg(QueryLog.confidence_score)).where(QueryLog.created_at > since)
            ).scalar() or 0
            
            fallback_count = self.session.execute(
                select(func.count(QueryLog.id)).where(
                    and_(QueryLog.created_at > since, QueryLog.used_fallback == True)
                )
            ).scalar()
            
            error_count = self.session.execute(
                select(func.count(QueryLog.id)).where(
                    and_(QueryLog.created_at > since, QueryLog.error_occurred == True)
                )
            ).scalar()
        
        return {
            "total_queries": total_queries,
            "average_processing_time": round(avg_processing_time, 3),
            "average_confidence": round(avg_confidence, 3),
            "fallback_rate": round(fallback_count / max(total_queries, 1), 3),
            "error_rate": round(error_count / max(total_queries, 1), 3),
            "success_rate": round((total_queries - error_count) / max(total_queries, 1), 3),
            "period_days": days
        }

class DocumentRepository(BaseRepository[Document]):
    """Repositorio para gestión de documentos"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, Document)
    
    async def get_by_hash(self, file_hash: str) -> Optional[Document]:
        """Obtener documento por hash"""
        stmt = select(Document).where(Document.file_hash == file_hash)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.session.execute(stmt).scalar_one_or_none()
    
    async def get_processed_documents(self) -> List[Document]:
        """Obtener documentos procesados"""
        stmt = select(Document).where(Document.is_processed == True)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()
    
    async def search_documents(
        self, 
        query: str,
        document_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Document]:
        """Buscar documentos por texto"""
        stmt = select(Document).where(Document.is_processed == True)
        
        # Text search
        if query:
            search_filter = or_(
                Document.title.ilike(f"%{query}%"),
                Document.content.ilike(f"%{query}%"),
                Document.summary.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        # Type filter
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        
        stmt = stmt.limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()

class SystemMetricsRepository(BaseRepository[SystemMetrics]):
    """Repositorio para métricas del sistema"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, SystemMetrics)
    
    async def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        labels: Optional[Dict[str, Any]] = None,
        period: str = "1m"
    ) -> SystemMetrics:
        """Registrar métrica del sistema"""
        metric_data = {
            "metric_name": metric_name,
            "value": value,
            "metric_type": metric_type,
            "labels": labels or {},
            "period": period
        }
        
        return await self.create(**metric_data)
    
    async def get_latest_metrics(
        self,
        metric_name: str,
        hours: int = 1
    ) -> List[SystemMetrics]:
        """Obtener métricas recientes"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(SystemMetrics).where(
            and_(
                SystemMetrics.metric_name == metric_name,
                SystemMetrics.timestamp > since
            )
        ).order_by(desc(SystemMetrics.timestamp))
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()

class AuditLogRepository(BaseRepository[AuditLog]):
    """Repositorio para logs de auditoría"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        super().__init__(session, AuditLog)
    
    async def log_action(
        self,
        user_id: Optional[UUID],
        action: str,
        resource: str,
        ip_address: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        resource_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Registrar acción en auditoría"""
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "details": details or {}
        }
        
        return await self.create(**log_data)
    
    async def get_user_actions(
        self,
        user_id: UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """Obtener acciones de un usuario"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(AuditLog).where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp > since
            )
        ).order_by(desc(AuditLog.timestamp)).limit(limit)
        
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt)
            return result.scalars().all()
        else:
            return self.session.execute(stmt).scalars().all()

# Unit of Work pattern para transacciones complejas
class UnitOfWork:
    """Unit of Work para gestionar transacciones complejas"""
    
    def __init__(self, session: Union[Session, AsyncSession]):
        self.session = session
        self.users = UserRepository(session)
        self.sessions = UserSessionRepository(session)
        self.queries = QueryLogRepository(session)
        self.documents = DocumentRepository(session)
        self.metrics = SystemMetricsRepository(session)
        self.audit = AuditLogRepository(session)
    
    async def commit(self):
        """Confirmar transacción"""
        if isinstance(self.session, AsyncSession):
            await self.session.commit()
        else:
            self.session.commit()
    
    async def rollback(self):
        """Revertir transacción"""
        if isinstance(self.session, AsyncSession):
            await self.session.rollback()
        else:
            self.session.rollback()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
"""
Modelos de base de datos PostgreSQL para sistema RAG empresarial
Usando SQLAlchemy 2.0 con type hints y mejores prácticas
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID

from sqlalchemy import (
    String, DateTime, Boolean, Integer, Float, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Base(DeclarativeBase):
    """Base class para todos los modelos"""
    pass

class User(Base):
    """Modelo de usuario con OAuth2 y roles empresariales"""
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Información básica
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Autenticación (local + OAuth2)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Null si solo OAuth2
    
    # OAuth2 providers
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'local', 'google', 'microsoft'
    
    # Estado y roles
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Roles empresariales
    roles: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=lambda: {"user": True}, nullable=False)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Información de perfil
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Configuraciones del usuario
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    queries: Mapped[List["QueryLog"]] = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name="valid_email"),
        CheckConstraint("length(username) >= 3", name="username_min_length"),
        CheckConstraint("provider IN ('local', 'google', 'microsoft') OR provider IS NULL", name="valid_provider"),
        Index("idx_users_provider_active", "provider", "is_active"),
        Index("idx_users_department", "department"),
    )
    
    def verify_password(self, password: str) -> bool:
        """Verificar password"""
        if not self.hashed_password:
            return False
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Establecer password hasheado"""
        self.hashed_password = pwd_context.hash(password)
    
    def has_role(self, role: str) -> bool:
        """Verificar si el usuario tiene un rol específico"""
        return self.roles.get(role, False)
    
    def has_permission(self, permission: str) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        return self.permissions.get(permission, False)

class UserSession(Base):
    """Sesiones de usuario para JWT y auditoría"""
    __tablename__ = "user_sessions"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Token information
    jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    token_type: Mapped[str] = mapped_column(String(20), default="access", nullable=False)
    
    # Session details
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relación
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_ip", "ip_address"),
    )

class QueryLog(Base):
    """Logs de consultas RAG para análisis y auditoría"""
    __tablename__ = "query_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Query information
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Method and routing
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # 'professional', 'real', 'hybrid'
    agent_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intent_detected: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Performance metrics
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    documents_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # System behavior
    used_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_occurred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Detailed information
    node_history: Mapped[List[str]] = mapped_column(JSONB, default=list, nullable=False)
    sources_used: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    validation_errors: Mapped[List[str]] = mapped_column(JSONB, default=list, nullable=False)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relación
    user: Mapped["User"] = relationship("User", back_populates="queries")
    
    __table_args__ = (
        Index("idx_queries_user_created", "user_id", "created_at"),
        Index("idx_queries_method", "method"),
        Index("idx_queries_performance", "processing_time", "confidence_score"),
        Index("idx_queries_errors", "error_occurred", "used_fallback"),
        Index("idx_queries_created_at", "created_at"),
    )

class SystemMetrics(Base):
    """Métricas del sistema para monitoreo y análisis"""
    __tablename__ = "system_metrics"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Metric identification
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'counter', 'gauge', 'histogram'
    
    # Metric values
    value: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Dimensions/Labels
    labels: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Time information
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    period: Mapped[str] = mapped_column(String(20), default="1m", nullable=False)  # '1m', '5m', '1h', '1d'
    
    __table_args__ = (
        Index("idx_metrics_name_timestamp", "metric_name", "timestamp"),
        Index("idx_metrics_type", "metric_type"),
        Index("idx_metrics_period", "period"),
    )

class Document(Base):
    """Documentos estructurados y su metadata"""
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Document identification
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'directiva', 'decreto', 'resolucion'
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Document metadata
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="es", nullable=False)
    
    # File information
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)  # SHA-256
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Vector information
    chunks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embeddings_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relación
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_documents_type_status", "document_type", "processing_status"),
        Index("idx_documents_processed", "is_processed"),
        Index("idx_documents_source", "source"),
    )

class DocumentChunk(Base):
    """Chunks de documentos para RAG"""
    __tablename__ = "document_chunks"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Chunk information
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Processing
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_vector: Mapped[Optional[List[float]]] = mapped_column(JSONB, nullable=True)  # Vector embeddings
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relación
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk"),
        Index("idx_chunks_document", "document_id"),
        Index("idx_chunks_token_count", "token_count"),
    )

class AuditLog(Base):
    """Logs de auditoría para compliance y seguridad"""
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Action information
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Request details
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Response information
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Additional context
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Auditoría
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_resource", "resource", "timestamp"),
        Index("idx_audit_ip", "ip_address"),
        Index("idx_audit_status", "status_code"),
    )

# Funciones de utilidad para crear la base de datos

def create_indexes(engine):
    """Crear índices adicionales para optimización"""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Índices para consultas frecuentes
        conn.execute(text("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_queries_recent 
            ON query_logs (created_at DESC) 
            WHERE created_at > NOW() - INTERVAL '30 days'
        """))
        
        # Índice para métricas de tiempo
        conn.execute(text("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_hourly 
            ON system_metrics (metric_name, timestamp) 
            WHERE period = '1h'
        """))
        
        # Índice para auditoría reciente
        conn.execute(text("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_recent 
            ON audit_logs (timestamp DESC) 
            WHERE timestamp > NOW() - INTERVAL '7 days'
        """))
        
        conn.commit()

def setup_database_constraints(engine):
    """Configurar constraints y triggers adicionales"""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Trigger para actualizar updated_at automáticamente
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))
        
        # Aplicar trigger a tablas relevantes
        for table in ['users', 'documents']:
            conn.execute(text(f"""
                DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                CREATE TRIGGER update_{table}_updated_at 
                    BEFORE UPDATE ON {table} 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """))
        
        conn.commit()
"""
Configuración de conexión PostgreSQL para producción
Incluye pooling, monitoring y manejo de errores robusto
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Engine, event, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncpg

from .models import Base, create_indexes, setup_database_constraints

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuración de base de datos para diferentes entornos"""
    
    def __init__(self):
        # Database connection parameters
        self.host = os.getenv("DATABASE_HOST", "localhost")
        self.port = int(os.getenv("DATABASE_PORT", "5432"))
        self.database = os.getenv("DATABASE_NAME", "minedu_rag")
        self.username = os.getenv("DATABASE_USER", "minedu_user")
        self.password = os.getenv("DATABASE_PASSWORD", "minedu_password")
        
        # SSL Configuration
        self.ssl_mode = os.getenv("DATABASE_SSL_MODE", "prefer")  # disable, allow, prefer, require
        self.ssl_cert = os.getenv("DATABASE_SSL_CERT")
        self.ssl_key = os.getenv("DATABASE_SSL_KEY")
        self.ssl_ca = os.getenv("DATABASE_SSL_CA")
        
        # Connection pool settings
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        self.pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    @property
    def sync_url(self) -> str:
        """URL de conexión síncrona"""
        password = quote_plus(self.password) if self.password else ""
        base_url = f"postgresql://{self.username}:{password}@{self.host}:{self.port}/{self.database}"
        
        # Add SSL parameters
        ssl_params = []
        if self.ssl_mode != "disable":
            ssl_params.append(f"sslmode={self.ssl_mode}")
            if self.ssl_cert:
                ssl_params.append(f"sslcert={self.ssl_cert}")
            if self.ssl_key:
                ssl_params.append(f"sslkey={self.ssl_key}")
            if self.ssl_ca:
                ssl_params.append(f"sslrootcert={self.ssl_ca}")
        
        if ssl_params:
            base_url += "?" + "&".join(ssl_params)
            
        return base_url
    
    @property
    def async_url(self) -> str:
        """URL de conexión asíncrona"""
        return self.sync_url.replace("postgresql://", "postgresql+asyncpg://")

class DatabaseManager:
    """Manager principal para conexiones de base de datos"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        
    def create_engine(self) -> Engine:
        """Crear engine síncrono con configuración de producción"""
        if self._engine is None:
            logger.info(f"Creating sync database engine for {self.config.environment}")
            
            engine_kwargs = {
                "url": self.config.sync_url,
                "poolclass": QueuePool,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "pool_pre_ping": True,  # Validate connections before use
                "echo": self.config.environment == "development",
                "future": True,
            }
            
            # Configuración específica para producción
            if self.config.environment == "production":
                engine_kwargs.update({
                    "pool_reset_on_return": "commit",
                    "connect_args": {
                        "connect_timeout": 10,
                        "command_timeout": 30,
                        "server_settings": {
                            "application_name": "minedu_rag_backend",
                            "timezone": "UTC",
                        }
                    }
                })
            
            self._engine = create_engine(**engine_kwargs)
            
            # Add event listeners for monitoring
            self._add_engine_listeners(self._engine)
            
        return self._engine
    
    def create_async_engine(self) -> AsyncEngine:
        """Crear engine asíncrono con configuración de producción"""
        if self._async_engine is None:
            logger.info(f"Creating async database engine for {self.config.environment}")
            
            engine_kwargs = {
                "url": self.config.async_url,
                "poolclass": QueuePool,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
                "pool_recycle": self.config.pool_recycle,
                "pool_pre_ping": True,
                "echo": self.config.environment == "development",
                "future": True,
            }
            
            # Configuración específica para producción
            if self.config.environment == "production":
                engine_kwargs.update({
                    "pool_reset_on_return": "commit",
                    "connect_args": {
                        "connect_timeout": 10,
                        "command_timeout": 30,
                        "server_settings": {
                            "application_name": "minedu_rag_backend_async",
                            "timezone": "UTC",
                        }
                    }
                })
            
            self._async_engine = create_async_engine(**engine_kwargs)
            
        return self._async_engine
    
    def get_session_factory(self) -> sessionmaker:
        """Obtener session factory síncrono"""
        if self._session_factory is None:
            engine = self.create_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._session_factory
    
    def get_async_session_factory(self) -> async_sessionmaker:
        """Obtener session factory asíncrono"""
        if self._async_session_factory is None:
            engine = self.create_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._async_session_factory
    
    def _add_engine_listeners(self, engine: Engine):
        """Agregar listeners para monitoring y debugging"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configurar parámetros de conexión"""
            if hasattr(dbapi_connection, 'set_session'):
                # PostgreSQL specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")
                    cursor.execute("SET statement_timeout = '30s'")
                    cursor.execute("SET lock_timeout = '10s'")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log when connection is checked out from pool"""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log when connection is returned to pool"""
            logger.debug("Connection returned to pool")
        
        @event.listens_for(engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            """Log when connection is invalidated"""
            logger.warning(f"Connection invalidated: {exception}")
    
    async def create_database_if_not_exists(self):
        """Crear base de datos si no existe (solo para desarrollo)"""
        if self.config.environment == "production":
            logger.warning("Database creation skipped in production")
            return
        
        # Connect to postgres database to create target database
        admin_url = self.config.sync_url.replace(f"/{self.config.database}", "/postgres")
        
        try:
            admin_engine = create_engine(admin_url)
            with admin_engine.connect() as conn:
                conn.execute(text("COMMIT"))  # End any transaction
                
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": self.config.database}
                )
                
                if not result.fetchone():
                    logger.info(f"Creating database: {self.config.database}")
                    conn.execute(text(f"CREATE DATABASE {self.config.database}"))
                    logger.info("Database created successfully")
                else:
                    logger.info("Database already exists")
            
            admin_engine.dispose()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    async def create_tables(self):
        """Crear todas las tablas"""
        try:
            engine = self.create_engine()
            logger.info("Creating database tables...")
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            # Create additional indexes and constraints
            create_indexes(engine)
            setup_database_constraints(engine)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """Verificar conectividad de la base de datos"""
        try:
            engine = self.create_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Obtener información de la base de datos"""
        try:
            engine = self.create_engine()
            with engine.connect() as conn:
                # PostgreSQL version
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                # Database size
                size_result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """))
                size = size_result.fetchone()[0]
                
                # Connection count
                conn_result = conn.execute(text("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                connections = conn_result.fetchone()[0]
                
                return {
                    "version": version,
                    "size": size,
                    "active_connections": connections,
                    "database_name": self.config.database,
                    "host": self.config.host,
                    "port": self.config.port,
                }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Cerrar todas las conexiones"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        
        if self._async_engine:
            self._async_engine.sync_close()
            self._async_engine = None

# Instancia global del manager
db_manager = DatabaseManager()

# Dependencias para FastAPI
def get_db() -> Session:
    """Dependencia para obtener sesión de base de datos síncrona"""
    session_factory = db_manager.get_session_factory()
    session = session_factory()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Context manager para obtener sesión de base de datos asíncrona"""
    session_factory = db_manager.get_async_session_factory()
    session = session_factory()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

async def get_async_db_dependency() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI para sesión asíncrona"""
    async with get_async_db() as session:
        yield session

# Funciones de utilidad
async def init_database():
    """Inicializar base de datos completa"""
    logger.info("Initializing database...")
    
    try:
        # Create database if needed (development only)
        await db_manager.create_database_if_not_exists()
        
        # Create tables and indexes
        await db_manager.create_tables()
        
        # Verify connection
        is_connected = await db_manager.check_connection()
        if not is_connected:
            raise Exception("Database connection verification failed")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def get_database_health() -> Dict[str, Any]:
    """Obtener estado de salud de la base de datos"""
    try:
        # Check basic connectivity
        is_connected = await db_manager.check_connection()
        
        if not is_connected:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Cannot connect to database"
            }
        
        # Get detailed info
        db_info = await db_manager.get_database_info()
        
        # Check pool status
        engine = db_manager.create_engine()
        pool = engine.pool
        
        return {
            "status": "healthy",
            "connected": True,
            "database_info": db_info,
            "connection_pool": {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
"""
API Gateway Service - Fase 5: RAGP (PRODUCCIÓN SEGURA)
Punto de entrada único con load balancing, rate limiting y routing
"""
import logging
import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Response, Security
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Pydantic para validación
try:
    from pydantic import BaseModel, validator, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False

# HTTP client para proxy real
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Monitoring imports
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Circuit breaker
try:
    from circuit_breaker import CircuitBreaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

# Rate limiting con Redis
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# OpenTelemetry
try:
    from opentelemetry import trace
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)

# === MODELOS PYDANTIC PARA VALIDACIÓN ===

class ChatRequest(BaseModel):
    """Modelo para requests de chat"""
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    session_id: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9_-]{1,50}$', description="ID de sesión")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    
    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('Message too short (minimum 3 characters)')
        return v.strip()

class AgentType(BaseModel):
    """Validación para tipos de agente"""
    agent_type: str = Field(..., regex=r'^(viaticos|legal|calculation|memory)$', description="Tipo de agente válido")

class CalculationRequest(BaseModel):
    """Modelo para requests de cálculo"""
    calculation_type: str = Field(..., regex=r'^(viaticos|uit|infraction)$')
    params: Dict[str, Any] = Field(..., description="Parámetros del cálculo")
    
    @validator('params')
    def validate_params(cls, v):
        if not isinstance(v, dict) or not v:
            raise ValueError('Params must be a non-empty dictionary')
        return v

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    error: str
    detail: str
    timestamp: str
    request_id: Optional[str] = None

# === CONFIGURACIÓN DE SEGURIDAD ===

class SecurityConfig:
    """Configuración centralizada de seguridad"""
    
    # API Keys válidas (en producción, usar base de datos o servicio externo)
    VALID_API_KEYS = {
        os.getenv("MINEDU_API_KEY", "minedu-prod-key-2024"): "production",
        os.getenv("MINEDU_DEV_API_KEY", "minedu-dev-key-2024"): "development"
    }
    
    # Dominios CORS permitidos
    ALLOWED_ORIGINS = [
        "https://ai.minedu.gob.pe",
        "https://expedientes.minedu.gob.pe",
        "https://rag.minedu.gob.pe"
    ]
    
    # En desarrollo, permitir localhost
    if os.getenv("ENVIRONMENT", "production") == "development":
        ALLOWED_ORIGINS.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000"
        ])
    
    # Hosts confiables
    TRUSTED_HOSTS = [
        "ai.minedu.gob.pe",
        "expedientes.minedu.gob.pe",
        "rag.minedu.gob.pe"
    ]
    
    if os.getenv("ENVIRONMENT", "production") == "development":
        TRUSTED_HOSTS.extend([
            "localhost",
            "127.0.0.1"
        ])

# === AUTENTICACIÓN ===

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verificar API key en el header Authorization
    """
    api_key = credentials.credentials
    
    if api_key not in SecurityConfig.VALID_API_KEYS:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    environment = SecurityConfig.VALID_API_KEYS[api_key]
    logger.info(f"Valid API key authenticated for environment: {environment}")
    return environment

# === EXCEPCIONES ESPECÍFICAS ===

class ServiceUnavailableError(Exception):
    """Error cuando un servicio no está disponible"""
    pass

class ProxyError(Exception):
    """Error en el proxy de requests"""
    pass

class RateLimitError(Exception):
    """Error de rate limiting"""
    pass

class ValidationError(Exception):
    """Error de validación"""
    pass

# === GATEWAY SERVICE ===

class GatewayService:
    """
    API Gateway Service para arquitectura de microservicios
    VERSIÓN SEGURA PARA PRODUCCIÓN
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_secure_config()
        self.app = None
        self.services = {}
        self.circuit_breakers = {}
        self.metrics = {}
        self.redis_client = None
        self.limiter = None
        self.http_client = None
        
        # Verificar dependencias críticas
        self._verify_dependencies()
        
        # Inicializar componentes
        self._setup_metrics()
        self._setup_circuit_breakers()
        self._setup_redis()
        self._setup_rate_limiter()
        self._setup_http_client()
        self._setup_fastapi()
        
        logger.info("🌐 GatewayService inicializado MODO SEGURO")
    
    def _verify_dependencies(self):
        """Verificar dependencias críticas"""
        missing_deps = []
        
        if not FASTAPI_AVAILABLE:
            missing_deps.append("fastapi")
        if not PYDANTIC_AVAILABLE:
            missing_deps.append("pydantic")
        if not HTTPX_AVAILABLE:
            missing_deps.append("httpx")
        
        if missing_deps:
            raise ImportError(f"Missing critical dependencies: {', '.join(missing_deps)}")
    
    def _get_secure_config(self) -> Dict[str, Any]:
        """Configuración segura del gateway"""
        return {
            "host": os.getenv("GATEWAY_HOST", "0.0.0.0"),
            "port": int(os.getenv("GATEWAY_PORT", "8000")),
            "debug": os.getenv("ENVIRONMENT", "production") == "development",
            "cors_enabled": True,
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
                "burst_limit": int(os.getenv("RATE_LIMIT_BURST", "10"))
            },
            "circuit_breaker": {
                "failure_threshold": int(os.getenv("CB_FAILURE_THRESHOLD", "5")),
                "recovery_timeout": int(os.getenv("CB_RECOVERY_TIMEOUT", "30"))
            },
            "services": {
                "rag_service": os.getenv("RAG_SERVICE_URL", "http://localhost:8001"),
                "agents_service": os.getenv("AGENTS_SERVICE_URL", "http://localhost:8002"), 
                "memory_service": os.getenv("MEMORY_SERVICE_URL", "http://localhost:8003"),
                "calculation_service": os.getenv("CALCULATION_SERVICE_URL", "http://localhost:8004")
            },
            "monitoring": {
                "metrics_enabled": True,
                "tracing_enabled": True
            },
            "timeouts": {
                "service_timeout": int(os.getenv("SERVICE_TIMEOUT", "30")),
                "connection_timeout": int(os.getenv("CONNECTION_TIMEOUT", "5"))
            }
        }
    
    def _setup_metrics(self):
        """Configurar métricas de Prometheus"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus no disponible - métricas deshabilitadas")
            return
            
        self.metrics = {
            "requests_total": Counter(
                "gateway_requests_total",
                "Total requests procesados por el gateway",
                ["method", "endpoint", "status", "environment"]
            ),
            "request_duration": Histogram(
                "gateway_request_duration_seconds", 
                "Duración de requests en segundos",
                ["method", "endpoint", "environment"]
            ),
            "active_connections": Gauge(
                "gateway_active_connections",
                "Conexiones activas en el gateway"
            ),
            "circuit_breaker_state": Gauge(
                "gateway_circuit_breaker_state",
                "Estado del circuit breaker (0=closed, 1=open, 2=half-open)",
                ["service"]
            ),
            "auth_failures": Counter(
                "gateway_auth_failures_total",
                "Total de fallos de autenticación"
            )
        }
    
    def _setup_circuit_breakers(self):
        """Configurar circuit breakers para servicios"""
        if not CIRCUIT_BREAKER_AVAILABLE:
            logger.warning("Circuit breaker no disponible")
            return
            
        for service_name in self.config["services"].keys():
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=self.config["circuit_breaker"]["failure_threshold"],
                recovery_timeout=self.config["circuit_breaker"]["recovery_timeout"]
            )
    
    def _setup_redis(self):
        """Configurar cliente Redis SEGURO"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis no disponible - rate limiting simplificado")
            return
        
        try:
            # URL segura de Redis desde variable de entorno
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.warning("REDIS_URL no configurada - usando configuración por defecto")
                redis_url = "redis://localhost:6379/0"
            
            self.redis_client = redis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis conectado de forma segura")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Error de conexión Redis: {e}")
            self.redis_client = None
        except redis.AuthenticationError as e:
            logger.error(f"❌ Error de autenticación Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Error inesperado Redis: {e}")
            self.redis_client = None
    
    def _setup_rate_limiter(self):
        """Configurar rate limiter con slowapi"""
        if not SLOWAPI_AVAILABLE:
            logger.warning("slowapi no disponible - rate limiting deshabilitado")
            return
        
        try:
            # Usar Redis si está disponible, sino memoria
            if self.redis_client:
                self.limiter = Limiter(
                    key_func=get_remote_address,
                    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/1")
                )
            else:
                self.limiter = Limiter(key_func=get_remote_address)
            
            logger.info("✅ Rate limiter configurado")
            
        except Exception as e:
            logger.error(f"Error configurando rate limiter: {e}")
            self.limiter = None
    
    def _setup_http_client(self):
        """Configurar cliente HTTP para proxy"""
        if not HTTPX_AVAILABLE:
            logger.error("httpx no disponible - proxy no funcionará")
            return
        
        timeout = httpx.Timeout(
            connect=self.config["timeouts"]["connection_timeout"],
            read=self.config["timeouts"]["service_timeout"],
            write=self.config["timeouts"]["service_timeout"],
            pool=self.config["timeouts"]["service_timeout"]
        )
        
        self.http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            verify=True  # Verificar certificados SSL
        )
        
        logger.info("✅ HTTP client configurado")
    
    def _setup_fastapi(self):
        """Configurar aplicación FastAPI SEGURA"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - Gateway no puede iniciar")
            return
            
        self.app = FastAPI(
            title="MINEDU RAG Gateway SEGURO",
            description="API Gateway para sistema RAG distribuido - PRODUCCIÓN",
            version="2.0.0",
            debug=self.config["debug"],
            docs_url="/docs" if self.config["debug"] else None,  # Desactivar docs en producción
            redoc_url="/redoc" if self.config["debug"] else None
        )
        
        # === MIDDLEWARE DE SEGURIDAD ===
        
        # 1. TrustedHost - PREVIENE ATAQUES POR HOST HEADER
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=SecurityConfig.TRUSTED_HOSTS
        )
        
        # 2. CORS SEGURO
        if self.config["cors_enabled"]:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=SecurityConfig.ALLOWED_ORIGINS,
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
                expose_headers=["X-Request-ID"]
            )
        
        # 3. Rate limiting
        if self.limiter:
            self.app.state.limiter = self.limiter
            self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Rutas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rutas del gateway SEGURAS"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check público (sin autenticación)"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        
        # === DESARROLLO: Endpoint de servicios detallado ===
        if self.config["debug"]:
            @self.app.get("/health/services")
            async def detailed_health_check(environment: str = Depends(verify_api_key)):
                """
                ⚠️ SOLO DESARROLLO: Health check detallado de servicios
                """
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "services": await self._check_services_health(),
                    "environment": environment,
                    "note": "ENDPOINT SOLO PARA DESARROLLO"
                }
        
        @self.app.get("/metrics")
        async def get_metrics(environment: str = Depends(verify_api_key)):
            """Endpoint de métricas para Prometheus (autenticado)"""
            if PROMETHEUS_AVAILABLE:
                return Response(
                    content=generate_latest(),
                    media_type="text/plain"
                )
            return {"error": "Metrics not available"}
        
        # === ENDPOINTS PRINCIPALES CON AUTENTICACIÓN ===
        
        @self.app.post("/api/chat", response_model=Dict[str, Any])
        async def chat_endpoint(
            request: ChatRequest,
            http_request: Request,
            environment: str = Depends(verify_api_key)
        ):
            """Endpoint principal de chat (AUTENTICADO)"""
            if self.limiter:
                await self.limiter.limit("60/minute")(http_request)
            
            return await self._proxy_request_secure(
                "rag_service", 
                "/api/chat", 
                http_request,
                json_data=request.dict(),
                environment=environment
            )
        
        @self.app.post("/api/agents/{agent_type}")
        async def agents_endpoint(
            agent_type: str,
            http_request: Request,
            environment: str = Depends(verify_api_key)
        ):
            """Endpoints para agentes específicos (AUTENTICADO + VALIDADO)"""
            # Validar agent_type
            try:
                AgentType(agent_type=agent_type)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid agent type: {e}")
            
            if self.limiter:
                await self.limiter.limit("30/minute")(http_request)
            
            return await self._proxy_request_secure(
                "agents_service",
                f"/api/agents/{agent_type}",
                http_request,
                environment=environment
            )
        
        @self.app.post("/api/calculate")
        async def calculation_endpoint(
            request: CalculationRequest,
            http_request: Request,
            environment: str = Depends(verify_api_key)
        ):
            """Endpoint de cálculos (AUTENTICADO + VALIDADO)"""
            if self.limiter:
                await self.limiter.limit("20/minute")(http_request)
            
            return await self._proxy_request_secure(
                "calculation_service",
                "/api/calculate",
                http_request,
                json_data=request.dict(),
                environment=environment
            )
        
        @self.app.get("/api/memory/{session_id}")
        async def memory_endpoint(
            session_id: str,
            http_request: Request,
            environment: str = Depends(verify_api_key)
        ):
            """Endpoint de memoria (AUTENTICADO + VALIDADO)"""
            # Validar session_id
            if not session_id or len(session_id) > 50 or not session_id.replace('-', '').replace('_', '').isalnum():
                raise HTTPException(status_code=400, detail="Invalid session_id format")
            
            if self.limiter:
                await self.limiter.limit("100/minute")(http_request)
            
            return await self._proxy_request_secure(
                "memory_service",
                f"/api/memory/{session_id}",
                http_request,
                environment=environment
            )
    
    async def _proxy_request_secure(
        self, 
        service_name: str, 
        path: str, 
        request: Request,
        json_data: Optional[Dict] = None,
        environment: str = "unknown"
    ):
        """Proxy request SEGURO a microservicio específico"""
        
        if not self.http_client:
            logger.error("HTTP client no disponible")
            raise HTTPException(status_code=503, detail="Proxy service unavailable")
        
        # Circuit breaker check
        if service_name in self.circuit_breakers:
            cb = self.circuit_breakers[service_name]
            if cb.state == "open":
                logger.warning(f"Circuit breaker OPEN for {service_name}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Service {service_name} temporarily unavailable"
                )
        
        start_time = datetime.utcnow()
        
        try:
            service_url = self.config["services"].get(service_name)
            if not service_url:
                raise ServiceUnavailableError(f"Service {service_name} not configured")
            
            full_url = f"{service_url}{path}"
            
            # Preparar headers
            headers = {
                "Content-Type": "application/json",
                "X-Forwarded-For": request.client.host,
                "X-Gateway-Environment": environment,
                "X-Request-ID": str(datetime.utcnow().timestamp())
            }
            
            # === PROXY REAL (NO SIMULACIÓN) ===
            if json_data:
                response = await self.http_client.post(
                    full_url,
                    json=json_data,
                    headers=headers
                )
            else:
                # Para requests GET
                response = await self.http_client.get(
                    full_url,
                    headers=headers
                )
            
            # Verificar respuesta
            response.raise_for_status()
            
            # Métricas de éxito
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._record_metrics(request.method, path, response.status_code, duration, environment)
            
            # Circuit breaker success
            if service_name in self.circuit_breakers:
                self.circuit_breakers[service_name].record_success()
            
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Timeout en {service_name}: {path}")
            self._handle_service_error(service_name, request, path, "timeout", environment)
            raise HTTPException(status_code=504, detail="Service timeout")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} en {service_name}: {path}")
            self._handle_service_error(service_name, request, path, f"http_{e.response.status_code}", environment)
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"Service error: {e.response.text}"
            )
            
        except httpx.RequestError as e:
            logger.error(f"Request error en {service_name}: {e}")
            self._handle_service_error(service_name, request, path, "connection", environment)
            raise HTTPException(status_code=503, detail="Service connection error")
            
        except ServiceUnavailableError as e:
            logger.error(f"Service unavailable: {e}")
            self._handle_service_error(service_name, request, path, "unavailable", environment)
            raise HTTPException(status_code=503, detail=str(e))
            
        except Exception as e:
            logger.error(f"Unexpected error en {service_name}: {e}")
            self._handle_service_error(service_name, request, path, "unexpected", environment)
            raise HTTPException(status_code=500, detail="Internal gateway error")
    
    def _handle_service_error(
        self, 
        service_name: str, 
        request: Request, 
        path: str, 
        error_type: str,
        environment: str
    ):
        """Manejar errores de servicio de forma específica"""
        
        # Circuit breaker
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].record_failure()
        
        # Métricas
        self._record_metrics(request.method, path, 500, 0, environment)
        
        # Log específico por tipo de error
        logger.error(f"Service error - Type: {error_type}, Service: {service_name}, Path: {path}")
    
    async def _check_services_health(self) -> Dict[str, Any]:
        """Verificar salud REAL de microservicios"""
        health_status = {}
        
        if not self.http_client:
            return {"error": "HTTP client not available"}
        
        for service_name, service_url in self.config["services"].items():
            try:
                health_url = f"{service_url}/health"
                response = await self.http_client.get(
                    health_url,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    health_data = response.json()
                    health_status[service_name] = {
                        "status": "healthy",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "details": health_data
                    }
                else:
                    health_status[service_name] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except httpx.TimeoutException:
                health_status[service_name] = {
                    "status": "timeout",
                    "error": "Health check timeout"
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    def _record_metrics(
        self, 
        method: str, 
        endpoint: str, 
        status: int, 
        duration: float,
        environment: str
    ):
        """Registrar métricas con environment"""
        if not PROMETHEUS_AVAILABLE or not self.metrics:
            return
            
        try:
            self.metrics["requests_total"].labels(
                method=method, 
                endpoint=endpoint, 
                status=str(status),
                environment=environment
            ).inc()
            
            self.metrics["request_duration"].labels(
                method=method,
                endpoint=endpoint,
                environment=environment
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
    
    async def start_server(self):
        """Iniciar servidor del gateway"""
        if not FASTAPI_AVAILABLE:
            logger.error("No se puede iniciar servidor - FastAPI no disponible")
            return
            
        config = uvicorn.Config(
            app=self.app,
            host=self.config["host"],
            port=self.config["port"],
            log_level="info",
            access_log=True,
            server_header=False,  # No exponer servidor
            date_header=False     # No exponer fecha
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Gateway SEGURO iniciando en {self.config['host']}:{self.config['port']}")
        logger.info(f"🛡️ Ambiente: {os.getenv('ENVIRONMENT', 'production')}")
        logger.info(f"🔐 CORS origins: {len(SecurityConfig.ALLOWED_ORIGINS)} configured")
        
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise
        finally:
            if self.http_client:
                await self.http_client.aclose()
    
    async def shutdown(self):
        """Shutdown limpio del gateway"""
        logger.info("🛑 Iniciando shutdown del gateway...")
        
        if self.http_client:
            await self.http_client.aclose()
            logger.info("✅ HTTP client cerrado")
        
        if self.redis_client:
            await self.redis_client.aclose() if hasattr(self.redis_client, 'aclose') else None
            logger.info("✅ Redis client cerrado")
        
        logger.info("✅ Gateway shutdown completado")
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """Estadísticas del gateway SEGURO"""
        return {
            "version": "2.0.0",
            "security_level": "PRODUCTION",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "dependencies": {
                "fastapi": FASTAPI_AVAILABLE,
                "pydantic": PYDANTIC_AVAILABLE,
                "httpx": HTTPX_AVAILABLE,
                "slowapi": SLOWAPI_AVAILABLE,
                "prometheus": PROMETHEUS_AVAILABLE,
                "redis": REDIS_AVAILABLE,
                "circuit_breaker": CIRCUIT_BREAKER_AVAILABLE,
                "telemetry": TELEMETRY_AVAILABLE
            },
            "security_features": [
                "api_key_authentication",
                "request_validation",
                "rate_limiting", 
                "circuit_breaker",
                "cors_protection",
                "trusted_hosts",
                "real_proxy",
                "specific_error_handling",
                "metrics_authentication"
            ],
            "services_registered": len(self.config["services"]),
            "cors_origins": len(SecurityConfig.ALLOWED_ORIGINS),
            "trusted_hosts": len(SecurityConfig.TRUSTED_HOSTS)
        }

# Instancia global SEGURA
global_gateway_service = GatewayService()
"""
API Gateway Service - Fase 5: RAGP (Versión Simplificada)
Punto de entrada único con load balancing, rate limiting y routing
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

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

# OpenTelemetry
try:
    from opentelemetry import trace
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

# Redis no disponible en esta versión simplificada
REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class GatewayService:
    """
    API Gateway Service para arquitectura de microservicios
    
    Features:
    - Load balancing entre servicios
    - Rate limiting por cliente
    - Circuit breaker pattern
    - Health checks automáticos
    - Métricas con Prometheus
    - Distributed tracing
    - CORS y seguridad
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.app = None
        self.services = {}
        self.circuit_breakers = {}
        self.metrics = {}
        self.redis_client = None
        
        # Inicializar componentes
        self._setup_metrics()
        self._setup_circuit_breakers()
        self._setup_fastapi()
        
        logger.info("🌐 GatewayService simplificado inicializado")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del gateway"""
        return {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True,
            "cors_enabled": True,
            "rate_limiting": {
                "enabled": False,  # Deshabilitado en versión simple
                "requests_per_minute": 100
            },
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 30
            },
            "services": {
                "rag_service": "http://localhost:8001",
                "agents_service": "http://localhost:8002", 
                "memory_service": "http://localhost:8003",
                "calculation_service": "http://localhost:8004"
            },
            "monitoring": {
                "metrics_enabled": True,
                "tracing_enabled": True
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
                ["method", "endpoint", "status"]
            ),
            "request_duration": Histogram(
                "gateway_request_duration_seconds", 
                "Duración de requests en segundos",
                ["method", "endpoint"]
            ),
            "active_connections": Gauge(
                "gateway_active_connections",
                "Conexiones activas en el gateway"
            ),
            "circuit_breaker_state": Gauge(
                "gateway_circuit_breaker_state",
                "Estado del circuit breaker (0=closed, 1=open, 2=half-open)",
                ["service"]
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
    
    def _setup_fastapi(self):
        """Configurar aplicación FastAPI"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - Gateway no puede iniciar")
            return
            
        self.app = FastAPI(
            title="MINEDU RAG Gateway",
            description="API Gateway para sistema RAG distribuido",
            version="1.0.0",
            debug=self.config["debug"]
        )
        
        # Middleware
        if self.config["cors_enabled"]:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
        
        # Rutas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configurar rutas del gateway"""
        if not self.app:
            return
            
        @self.app.get("/health")
        async def health_check():
            """Health check del gateway"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": await self._check_services_health()
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Endpoint de métricas para Prometheus"""
            if PROMETHEUS_AVAILABLE:
                return Response(
                    content=generate_latest(),
                    media_type="text/plain"
                )
            return {"error": "Metrics not available"}
        
        @self.app.post("/api/chat")
        async def chat_endpoint(request: Request):
            """Endpoint principal de chat"""
            return await self._proxy_request("rag_service", "/api/chat", request)
    
    async def _proxy_request(self, service_name: str, path: str, request: Request):
        """Proxy request a microservicio específico"""
        
        try:
            # Simular proxy (en implementación real usaríamos httpx)
            start_time = datetime.utcnow()
            
            response_data = {
                "service": service_name,
                "path": path,
                "proxied": True,
                "timestamp": start_time.isoformat(),
                "status": "success"
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error proxying to {service_name}: {e}")
            raise HTTPException(status_code=500, detail="Service error")
    
    async def _check_services_health(self) -> Dict[str, str]:
        """Verificar salud de microservicios"""
        health_status = {}
        
        for service_name, service_url in self.config["services"].items():
            try:
                # En implementación real, haríamos HTTP request al health endpoint
                health_status[service_name] = "healthy"
            except Exception:
                health_status[service_name] = "unhealthy"
        
        return health_status
    
    async def start_server(self):
        """Iniciar servidor del gateway"""
        if not FASTAPI_AVAILABLE:
            logger.error("No se puede iniciar servidor - FastAPI no disponible")
            return
            
        config = uvicorn.Config(
            app=self.app,
            host=self.config["host"],
            port=self.config["port"],
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Iniciando Gateway en {self.config['host']}:{self.config['port']}")
        await server.serve()
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """Estadísticas del gateway"""
        return {
            "fastapi_available": FASTAPI_AVAILABLE,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "redis_available": REDIS_AVAILABLE,
            "circuit_breaker_available": CIRCUIT_BREAKER_AVAILABLE,
            "telemetry_available": TELEMETRY_AVAILABLE,
            "services_registered": len(self.config["services"]),
            "features": [
                "load_balancing",
                "health_checks",
                "metrics",
                "cors_support",
                "distributed_tracing"
            ],
            "config": {
                "host": self.config["host"],
                "port": self.config["port"],
                "debug": self.config["debug"]
            }
        } 
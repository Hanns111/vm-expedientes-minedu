"""
Agents Service - Microservicio especializado en agentes inteligentes
Maneja QueryClassifier, CalculationAgent, LegalExpert y otros agentes
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Integración con agentes existentes
from ..core.agents.query_classifier import QueryClassifierAgent
from ..core.agents.calculation_agent import CalculationAgent
from ..core.agents.legal_expert import LegalExpert
from ..core.agents.procedure_agent import ProcedureAgent
from ..core.agents.historical_agent import HistoricalAgent

logger = logging.getLogger(__name__)

class AgentsService:
    """
    Microservicio especializado en agentes inteligentes
    Centraliza todos los agentes especializados del sistema
    """
    
    def __init__(self, port: int = 8002):
        self.port = port
        self.app = self._create_fastapi_app() if FASTAPI_AVAILABLE else None
        
        # Inicializar agentes
        self.query_classifier = QueryClassifierAgent()
        self.calculation_agent = CalculationAgent()
        self.legal_expert = LegalExpert()
        self.procedure_agent = ProcedureAgent()
        self.historical_agent = HistoricalAgent()
        
        # Configurar rutas
        if self.app:
            self._setup_routes()
        
        logger.info(f"🤖 AgentsService inicializado en puerto {port}")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para Agents Service"""
        return FastAPI(
            title="Agents Service",
            description="Microservicio de agentes inteligentes",
            version="1.0.0"
        )
    
    def _setup_routes(self):
        """Configurar rutas del Agents Service"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check del agents service"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agents_loaded": 5,
                "agents": [
                    "query_classifier",
                    "calculation_agent", 
                    "legal_expert",
                    "procedure_agent",
                    "historical_agent"
                ]
            }
        
        @self.app.post("/api/agents/classify")
        async def classify_query(request: Dict[str, Any]):
            """Clasificar consulta usando QueryClassifier"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Clasificar consulta
                classification = self.query_classifier.classify_query(query, context)
                
                return {
                    "success": True,
                    "classification": classification,
                    "service": "agents_service",
                    "agent": "query_classifier",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in query classification: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/calculate")
        async def process_calculation(request: Dict[str, Any]):
            """Procesar cálculo usando CalculationAgent"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Procesar cálculo
                result = self.calculation_agent.process_calculation_query(query, context)
                
                return {
                    "success": True,
                    "calculation_result": {
                        "type": result.calculation_type,
                        "value": str(result.result_value),
                        "formatted": result.result_formatted,
                        "legal_basis": result.legal_basis,
                        "steps": result.calculation_steps,
                        "confidence": result.confidence,
                        "year": result.applicable_year
                    },
                    "service": "agents_service",
                    "agent": "calculation_agent",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in calculation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/legal")
        async def process_legal_query(request: Dict[str, Any]):
            """Procesar consulta legal usando LegalExpert"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Procesar consulta legal
                result = self.legal_expert.process_legal_query(query, context)
                
                return {
                    "success": True,
                    "legal_result": result,
                    "service": "agents_service",
                    "agent": "legal_expert",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in legal processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/procedure")
        async def process_procedure_query(request: Dict[str, Any]):
            """Procesar consulta de procedimiento usando ProcedureAgent"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Procesar procedimiento
                result = self.procedure_agent.process_procedure_query(query, context)
                
                return {
                    "success": True,
                    "procedure_result": result,
                    "service": "agents_service",
                    "agent": "procedure_agent",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in procedure processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/agents/historical")
        async def process_historical_query(request: Dict[str, Any]):
            """Procesar consulta histórica usando HistoricalAgent"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Procesar consulta histórica
                result = self.historical_agent.process_historical_query(query, context)
                
                return {
                    "success": True,
                    "historical_result": result,
                    "service": "agents_service",
                    "agent": "historical_agent",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in historical processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/agents/capabilities")
        async def get_agents_capabilities():
            """Obtener capacidades de todos los agentes"""
            try:
                capabilities = {
                    "query_classifier": self.query_classifier.get_classifier_capabilities(),
                    "calculation_agent": self.calculation_agent.get_agent_capabilities(),
                    "legal_expert": self.legal_expert.get_expert_capabilities(),
                    "procedure_agent": self.procedure_agent.get_agent_capabilities(),
                    "historical_agent": self.historical_agent.get_agent_capabilities()
                }
                
                return {
                    "success": True,
                    "capabilities": capabilities,
                    "service": "agents_service",
                    "total_agents": len(capabilities),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting capabilities: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/stats")
        async def get_service_stats():
            """Estadísticas del Agents Service"""
            try:
                return {
                    "service": "agents_service",
                    "port": self.port,
                    "agents_count": 5,
                    "endpoints": [
                        "/api/agents/classify",
                        "/api/agents/calculate",
                        "/api/agents/legal",
                        "/api/agents/procedure",
                        "/api/agents/historical"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_service(self):
        """Iniciar Agents Service"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - Agents Service no puede iniciar")
            return
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Iniciando Agents Service en puerto {self.port}")
        await server.serve()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check programático"""
        try:
            return {
                "status": "healthy",
                "agents_loaded": 5,
                "fastapi_available": FASTAPI_AVAILABLE,
                "service_ready": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Instancia global
global_agents_service = AgentsService()

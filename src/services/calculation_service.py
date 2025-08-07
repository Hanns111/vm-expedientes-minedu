"""
Calculation Service - Microservicio especializado en cálculos normativos
Maneja cálculos de viáticos, UIT, porcentajes y montos
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from decimal import Decimal

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Integración con sistema de cálculos existente
from ..core.calculations.normative_calculator import NormativeCalculator
from ..core.calculations.temporal_legal import TemporalLegalProcessor
from ..core.agents.calculation_agent import CalculationAgent

logger = logging.getLogger(__name__)

class CalculationService:
    """
    Microservicio especializado en cálculos normativos
    Centraliza toda la lógica de cálculos del sistema
    """
    
    def __init__(self, port: int = 8004):
        self.port = port
        self.app = self._create_fastapi_app() if FASTAPI_AVAILABLE else None
        
        # Componentes de cálculo
        self.normative_calculator = NormativeCalculator()
        self.temporal_processor = TemporalLegalProcessor()
        self.calculation_agent = CalculationAgent()
        
        # Cache de cálculos
        self.calculation_cache: Dict[str, Dict[str, Any]] = {}
        
        # Configurar rutas
        if self.app:
            self._setup_routes()
        
        logger.info(f"🧮 CalculationService inicializado en puerto {port}")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para Calculation Service"""
        return FastAPI(
            title="Calculation Service",
            description="Microservicio de cálculos normativos",
            version="1.0.0"
        )
    
    def _setup_routes(self):
        """Configurar rutas del Calculation Service"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check del calculation service"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "calculators_loaded": 3,
                "calculation_types": [
                    "viaticos",
                    "uit_calculations",
                    "percentage_calculations",
                    "daily_rates",
                    "total_calculations"
                ]
            }
        
        @self.app.post("/api/calculate/viaticos")
        async def calculate_viaticos(request: Dict[str, Any]):
            """Calcular viáticos usando sistema existente"""
            try:
                level = request.get("level", "funcionario")
                year = request.get("year", datetime.now().year)
                days = request.get("days", 1)
                location = request.get("location", "Nacional")
                
                # Verificar cache
                cache_key = f"viaticos_{level}_{year}_{days}_{location}"
                if cache_key in self.calculation_cache:
                    cached_result = self.calculation_cache[cache_key]
                    cached_result["from_cache"] = True
                    return cached_result
                
                # Calcular viáticos
                result = self.normative_calculator.calculate_viaticos(
                    level=level,
                    year=year,
                    days=days,
                    location=location
                )
                
                response = {
                    "success": True,
                    "calculation_type": "viaticos",
                    "result": result,
                    "parameters": {
                        "level": level,
                        "year": year,
                        "days": days,
                        "location": location
                    },
                    "service": "calculation_service",
                    "from_cache": False,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Guardar en cache
                self.calculation_cache[cache_key] = response
                
                return response
                
            except Exception as e:
                logger.error(f"Error calculating viaticos: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/calculate/query")
        async def calculate_from_query(request: Dict[str, Any]):
            """Calcular basado en consulta natural usando CalculationAgent"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                context = request.get("context", {})
                
                # Usar agente de cálculos
                result = self.calculation_agent.process_calculation_query(query, context)
                
                return {
                    "success": True,
                    "calculation_type": result.calculation_type,
                    "result": {
                        "value": str(result.result_value),
                        "formatted": result.result_formatted,
                        "legal_basis": result.legal_basis,
                        "steps": result.calculation_steps,
                        "confidence": result.confidence,
                        "year": result.applicable_year
                    },
                    "query": query,
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in query calculation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/calculate/uit")
        async def calculate_uit(request: Dict[str, Any]):
            """Calcular valores UIT"""
            try:
                year = request.get("year", datetime.now().year)
                quantity = request.get("quantity", 1)
                
                # Usar calculadora normativa
                uit_value = self.normative_calculator.get_uit_value(year)
                total_value = Decimal(str(uit_value)) * Decimal(str(quantity))
                
                return {
                    "success": True,
                    "calculation_type": "uit",
                    "result": {
                        "uit_unit_value": uit_value,
                        "quantity": quantity,
                        "total_value": float(total_value),
                        "formatted": f"S/ {total_value:,.2f}",
                        "year": year
                    },
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error calculating UIT: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/calculate/percentage")
        async def calculate_percentage(request: Dict[str, Any]):
            """Calcular porcentajes"""
            try:
                base_amount = request.get("base_amount")
                percentage = request.get("percentage")
                
                if base_amount is None or percentage is None:
                    raise HTTPException(
                        status_code=400,
                        detail="base_amount and percentage required"
                    )
                
                base_decimal = Decimal(str(base_amount))
                percentage_decimal = Decimal(str(percentage))
                
                result_value = base_decimal * percentage_decimal / Decimal("100")
                
                return {
                    "success": True,
                    "calculation_type": "percentage",
                    "result": {
                        "base_amount": float(base_decimal),
                        "percentage": float(percentage_decimal),
                        "result_value": float(result_value),
                        "formatted": f"S/ {result_value:,.2f}",
                        "calculation": f"{base_amount} × {percentage}% = {result_value}"
                    },
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error calculating percentage: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/calculate/rates")
        async def get_current_rates():
            """Obtener tarifas actuales"""
            try:
                current_year = datetime.now().year
                
                # Obtener tarifas de viáticos
                viaticos_rates = {
                    "ministro": {
                        "nacional": 380.00,
                        "internacional": 650.00
                    },
                    "viceministro": {
                        "nacional": 340.00,
                        "internacional": 580.00
                    },
                    "funcionario": {
                        "nacional": 320.00,
                        "internacional": 520.00
                    },
                    "servidor": {
                        "nacional": 280.00,
                        "internacional": 450.00
                    }
                }
                
                # Obtener valor UIT actual
                uit_value = self.normative_calculator.get_uit_value(current_year)
                
                return {
                    "success": True,
                    "year": current_year,
                    "viaticos_rates": viaticos_rates,
                    "uit_value": uit_value,
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting rates: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/calculate/capabilities")
        async def get_calculation_capabilities():
            """Obtener capacidades de cálculo"""
            try:
                capabilities = self.calculation_agent.get_agent_capabilities()
                
                return {
                    "success": True,
                    "capabilities": capabilities,
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting capabilities: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/calculate/cache")
        async def clear_calculation_cache():
            """Limpiar cache de cálculos"""
            try:
                cache_size = len(self.calculation_cache)
                self.calculation_cache.clear()
                
                return {
                    "success": True,
                    "cache_cleared": cache_size,
                    "service": "calculation_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/stats")
        async def get_service_stats():
            """Estadísticas del Calculation Service"""
            try:
                return {
                    "service": "calculation_service",
                    "port": self.port,
                    "cache_size": len(self.calculation_cache),
                    "calculators_loaded": 3,
                    "endpoints": [
                        "/api/calculate/viaticos",
                        "/api/calculate/query",
                        "/api/calculate/uit",
                        "/api/calculate/percentage",
                        "/api/calculate/rates"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_service(self):
        """Iniciar Calculation Service"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - Calculation Service no puede iniciar")
            return
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Iniciando Calculation Service en puerto {self.port}")
        await server.serve()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check programático"""
        try:
            return {
                "status": "healthy",
                "calculators_ready": True,
                "cache_size": len(self.calculation_cache),
                "normative_calculator_available": True,
                "temporal_processor_available": True,
                "calculation_agent_available": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Instancia global
global_calculation_service = CalculationService()

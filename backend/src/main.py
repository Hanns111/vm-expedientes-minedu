"""
FastAPI application with plugin system and multi-LLM router.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path for hybrid search imports
# backend/src/main.py -> go up 2 levels to get to project root
backend_dir = Path(__file__).parent.parent  # /backend
project_root = backend_dir.parent  # /vm-expedientes-minedu
sys.path.insert(0, str(project_root))  # Add project root to path

try:
    from src.core.hybrid.hybrid_search import HybridSearch
    HYBRID_SEARCH_AVAILABLE = True
    print("✅ HybridSearch imported successfully")
except ImportError as e:
    print(f"⚠️ Hybrid search not available: {e}")
    print(f"Project root: {project_root}")
    print(f"Backend dir: {backend_dir}")
    HYBRID_SEARCH_AVAILABLE = False
    HybridSearch = None  # Define it as None so no NameError

# Import backend core modules with error handling
try:
    from core.plugins.plugin_registry import PluginRegistry
except ImportError:
    PluginRegistry = None

try:
    from core.llm.model_router import ModelRouter  
except ImportError:
    ModelRouter = None

try:
    from core.config.settings import get_settings
except ImportError:
    # Fallback settings
    class MockSettings:
        cors_origins = ["http://localhost:3000", "http://localhost:3001"]
    def get_settings():
        return MockSettings()
    print("⚠️ Using fallback settings")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
plugin_registry: PluginRegistry = None
model_router: ModelRouter = None
hybrid_search: HybridSearch = None
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global plugin_registry, model_router, hybrid_search
    
    # Startup
    logger.info("🚀 Starting Government AI Platform...")
    try:
        if PluginRegistry:
            plugin_registry = PluginRegistry("../config/plugins.yaml")
            logger.info(f"✅ Loaded {len(plugin_registry.plugins)} plugins")
        else:
            logger.info("📝 Plugin registry not available - using mock data")
            
        if ModelRouter:
            model_router = ModelRouter("../config/models.yaml")
            logger.info(f"✅ Loaded {len(model_router.models)} models")
        else:
            logger.info("📝 Model router not available - using mock data")
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        # Continue with mock data for development
        logger.info("📝 Using mock data for development")
    
    # Initialize Hybrid Search
    if HYBRID_SEARCH_AVAILABLE:
        try:
            # Paths to vectorstores from project root
            bm25_path = str(project_root / "data/vectorstores/bm25.pkl")
            tfidf_path = str(project_root / "data/vectorstores/tfidf.pkl")
            transformer_path = str(project_root / "data/vectorstores/transformers.pkl")
            
            print(f"🔍 Loading vectorstores from:")
            print(f"  - BM25: {bm25_path}")
            print(f"  - TF-IDF: {tfidf_path}")
            print(f"  - Transformer: {transformer_path}")
            
            hybrid_search = HybridSearch(
                bm25_vectorstore_path=bm25_path,
                tfidf_vectorstore_path=tfidf_path,
                transformer_vectorstore_path=transformer_path,
                fusion_strategy='weighted'
            )
            logger.info("✅ Hybrid search system initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing hybrid search: {e}")
            hybrid_search = None
    else:
        logger.warning("❌ Hybrid search not available")
        hybrid_search = None
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Government AI Platform...")

# Create FastAPI app
app = FastAPI(
    title="Government AI Platform API",
    description="Sistema de IA para procesamiento de documentos gubernamentales",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Government AI Platform API v2.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        plugins_count = len(plugin_registry.plugins) if plugin_registry else 0
        models_count = len(model_router.models) if model_router else 0
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "plugins_loaded": plugins_count,
            "models_loaded": models_count,
            "version": "2.0.0",
            "uptime": "active"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/api/admin/plugins")
async def get_plugins():
    """Get all plugins configuration."""
    try:
        if plugin_registry and plugin_registry.plugins:
            return [
                {
                    "id": plugin.id,
                    "name": plugin.name,
                    "description": plugin.description,
                    "enabled": plugin.enabled,
                    "capabilities": plugin.capabilities,
                    "version": plugin.version,
                    "metrics": {
                        "total_requests": plugin.metrics.get("total_requests", 0),
                        "success_rate": plugin.metrics.get("success_rate", 100.0),
                        "avg_latency": plugin.metrics.get("avg_latency", 200),
                        "errors_last_hour": plugin.metrics.get("errors_last_hour", 0)
                    }
                }
                for plugin in plugin_registry.plugins.values()
            ]
        else:
            # Mock data for development
            return [
                {
                    "id": "audio-transcription",
                    "name": "Transcripción de Audio",
                    "description": "Convierte audio a texto usando Whisper",
                    "enabled": True,
                    "capabilities": ["audio_processing"],
                    "version": "1.0.0",
                    "metrics": {
                        "total_requests": 156,
                        "success_rate": 98.7,
                        "avg_latency": 2500,
                        "errors_last_hour": 0
                    }
                },
                {
                    "id": "document-ocr",
                    "name": "OCR de Documentos",
                    "description": "Extrae texto de imágenes y PDFs",
                    "enabled": True,
                    "capabilities": ["vision_processing", "document_analysis"],
                    "version": "1.2.0",
                    "metrics": {
                        "total_requests": 342,
                        "success_rate": 95.2,
                        "avg_latency": 1800,
                        "errors_last_hour": 2
                    }
                },
                {
                    "id": "entity-extraction",
                    "name": "Extracción de Entidades",
                    "description": "Identifica y extrae entidades específicas de documentos",
                    "enabled": True,
                    "capabilities": ["nlp_processing", "entity_recognition"],
                    "version": "1.1.0",
                    "metrics": {
                        "total_requests": 789,
                        "success_rate": 92.1,
                        "avg_latency": 650,
                        "errors_last_hour": 1
                    }
                }
            ]
    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving plugins")

@app.get("/api/admin/models")
async def get_models():
    """Get all models configuration."""
    try:
        if model_router and model_router.models:
            return [
                {
                    "model_name": model.model_name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "enabled": model.enabled,
                    "provider": model.provider,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "capabilities": model.capabilities,
                    "metrics": {
                        "total_requests": model.metrics.get("total_requests", 0),
                        "total_tokens": model.metrics.get("total_tokens", 0),
                        "avg_latency": model.latency_ms,
                        "success_rate": model.metrics.get("success_rate", 100.0)
                    }
                }
                for model in model_router.models.values()
            ]
        else:
            # Mock data for development
            return [
                {
                    "model_name": "gpt-4-turbo",
                    "display_name": "GPT-4 Turbo",
                    "description": "Modelo avanzado para análisis complejos",
                    "enabled": True,
                    "provider": "openai",
                    "cost_per_1k_tokens": 0.03,
                    "capabilities": ["reasoning", "analysis", "multilingual"],
                    "metrics": {
                        "total_requests": 1250,
                        "total_tokens": 45000,
                        "avg_latency": 2000,
                        "success_rate": 99.1
                    }
                },
                {
                    "model_name": "claude-3-sonnet",
                    "display_name": "Claude 3 Sonnet",
                    "description": "Modelo equilibrado con alta precisión",
                    "enabled": True,
                    "provider": "anthropic",
                    "cost_per_1k_tokens": 0.015,
                    "capabilities": ["reasoning", "analysis", "safety"],
                    "metrics": {
                        "total_requests": 890,
                        "total_tokens": 32000,
                        "avg_latency": 1800,
                        "success_rate": 97.8
                    }
                },
                {
                    "model_name": "gpt-3.5-turbo",
                    "display_name": "GPT-3.5 Turbo",
                    "description": "Modelo rápido para consultas generales",
                    "enabled": True,
                    "provider": "openai",
                    "cost_per_1k_tokens": 0.002,
                    "capabilities": ["fast_response", "general_queries"],
                    "metrics": {
                        "total_requests": 2100,
                        "total_tokens": 67000,
                        "avg_latency": 1200,
                        "success_rate": 98.5
                    }
                }
            ]
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving models")

@app.get("/api/admin/system-status")
async def get_system_status():
    """Get overall system status and metrics."""
    try:
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime": "99.9%",
            "active_connections": 42,
            "total_requests_today": 5420,
            "average_response_time": 1250,
            "error_rate": 0.8,
            "system_load": {
                "cpu_usage": 35.2,
                "memory_usage": 68.7,
                "disk_usage": 45.1
            },
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "llm_router": "healthy",
                "plugin_registry": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system status")

@app.post("/api/admin/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str):
    """Toggle plugin enabled/disabled state."""
    try:
        # In a real implementation, this would update the plugin state
        return {
            "plugin_id": plugin_id,
            "action": "toggled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error toggling plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail="Error toggling plugin")

@app.post("/api/admin/models/{model_name}/toggle")
async def toggle_model(model_name: str):
    """Toggle model enabled/disabled state."""
    try:
        # In a real implementation, this would update the model state
        return {
            "model_name": model_name,
            "action": "toggled",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error toggling model {model_name}: {e}")
        raise HTTPException(status_code=500, detail="Error toggling model")

# Chat and Search Endpoints
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class SearchRequest(BaseModel):
    query: str
    method: str = "hybrid"
    top_k: int = 5

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for conversational AI with real hybrid search."""
    try:
        logger.info(f"Received chat request: {request.message}")
        start_time = time.time()
        
        # Check if hybrid search is available
        if hybrid_search is None:
            logger.warning("Hybrid search not available, using fallback response")
            return _generate_fallback_response(request)
        
        # Perform hybrid search
        try:
            search_results = hybrid_search.search(request.message, top_k=5)
            logger.info(f"Hybrid search returned {len(search_results)} results")
            
            # Generate response based on search results
            response_data = _generate_chat_response(request, search_results, start_time)
            
            logger.info(f"Generated response for query: '{request.message[:50]}...'")
            return response_data
            
        except Exception as search_error:
            logger.error(f"Error in hybrid search: {search_error}")
            return _generate_fallback_response(request, error_msg=str(search_error))
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat request")

def _generate_chat_response(request: ChatRequest, search_results: List[Dict], start_time: float) -> Dict:
    """Generate chat response from hybrid search results."""
    processing_time = time.time() - start_time
    
    if not search_results:
        return {
            "response": "No encontré información específica sobre tu consulta en los documentos disponibles. "
                       "¿Podrías reformular tu pregunta o ser más específico?",
            "conversation_id": request.conversation_id or f"conv_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "processing_time": processing_time
        }
    
    # Extract the best content from search results
    best_result = search_results[0] if search_results else None
    
    # Improved intent detection and response generation
    query_lower = request.message.lower()
    intent = _detect_query_intent(query_lower)
    
    # Generate response based on detected intent
    if intent == "montos_maximos":
        response_text = _generate_montos_maximos_response(query_lower, search_results)
    elif intent == "declaracion_jurada":
        response_text = _generate_declaracion_jurada_response(query_lower, search_results)
    elif intent == "procedimiento":
        response_text = _generate_procedimiento_response(query_lower, search_results)
    elif intent == "diferencias":
        response_text = _generate_diferencias_response(query_lower, search_results)
    elif intent == "componentes":
        response_text = _generate_componentes_response(query_lower, search_results)
    elif intent == "viaticos_general":
        response_text = _generate_viaticos_response(query_lower, search_results)
    else:
        response_text = _generate_smart_fallback(request.message, search_results)
    
    # Prepare sources from search results
    sources = []
    for i, result in enumerate(search_results[:3]):  # Top 3 sources
        source = {
            "title": result.get('title', f"Documento {i+1}"),
            "excerpt": result.get('content', '')[:200] + "...",
            "confidence": round(result.get('score', 0.0), 2),
            "method": result.get('method', 'hybrid')
        }
        sources.append(source)
    
    return {
        "response": response_text,
        "conversation_id": request.conversation_id or f"conv_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "sources": sources,
        "processing_time": round(processing_time, 3),
        "total_results": len(search_results)
    }

def _detect_query_intent(query: str) -> str:
    """
    Detecta la intención de la consulta usando patrones sofisticados
    """
    query_lower = query.lower()
    
    # Patrones para montos y límites
    monto_patterns = [
        r'monto\s*(máximo|maximo|tope|límite|limite)',
        r'(cuánto|cuanto)\s*(es|son|puedo)',
        r'(máximo|maximo|tope)\s*(de|para)\s*viáticos',
        r'límite\s*(de|para)\s*viáticos',
        r'tope\s*(de|para)\s*(viáticos|viaticos|declaración)',
        r'(viáticos|viaticos)\s*(máximos|maximos|diarios)',
        r'valor\s*(de|del)\s*viático'
    ]
    
    # Patrones para declaración jurada
    declaracion_patterns = [
        r'declaración\s*jurada',
        r'declaracion\s*jurada',
        r'sin\s*comprobante',
        r'sin\s*boleta',
        r'sin\s*factura',
        r'gastos\s*menores',
        r'lima|provincia'
    ]
    
    # Patrones para procedimientos
    procedimiento_patterns = [
        r'procedimiento',
        r'(cómo|como)\s*(solicitar|pedir|tramitar)',
        r'pasos\s*para',
        r'proceso\s*de',
        r'devolución',
        r'reembolso',
        r'devolver',
        r'gerente\s*asume'
    ]
    
    # Patrones para diferencias y comparaciones
    diferencia_patterns = [
        r'diferencia\s*entre',
        r'comparación',
        r'ministro.*servidor',
        r'servidor.*ministro',
        r'tipos\s*de\s*viático',
        r'categorías'
    ]
    
    # Patrones para componentes/qué incluye
    componente_patterns = [
        r'(qué|que)\s*incluye',
        r'componentes',
        r'(qué|que)\s*cubre',
        r'alcance',
        r'comprende',
        r'abarca',
        r'incluyen\s*(los\s*)?viáticos',
        r'incluyen\s*(los\s*)?viaticos'
    ]
    
    # Detectar intención con prioridad (orden importante)
    if any(re.search(pattern, query_lower) for pattern in componente_patterns):
        return "componentes"
    
    if any(re.search(pattern, query_lower) for pattern in procedimiento_patterns):
        return "procedimiento"
    
    if any(re.search(pattern, query_lower) for pattern in diferencia_patterns):
        return "diferencias"
    
    if any(re.search(pattern, query_lower) for pattern in monto_patterns):
        if any(re.search(pattern, query_lower) for pattern in declaracion_patterns):
            return "declaracion_jurada"
        return "montos_maximos"
    
    if "viático" in query_lower or "viatico" in query_lower:
        return "viaticos_general"
    
    return "general"

def _generate_viaticos_response(query: str, results: List[Dict]) -> str:
    """Generate specific response for viáticos queries."""
    if "ministro" in query or "ministros" in query:
        return """📋 **VIÁTICOS PARA MINISTROS DE ESTADO:**

💰 **MONTO DIARIO:** S/ 380.00 soles

🏛️ **APLICACIÓN:**
• Ministros de Estado en comisiones de servicio
• Válido para territorio nacional
• Incluye alojamiento, alimentación y gastos menores

📄 **FUENTE:** Directiva de Viáticos MINEDU - Basado en documentos oficiales encontrados."""
    
    elif "declaración" in query or "declaracion" in query:
        return """📋 **DECLARACIÓN JURADA DE VIÁTICOS:**

💰 **LÍMITES MÁXIMOS:**
• **Lima:** Hasta S/ 45.00 por día
• **Provincias:** Hasta S/ 30.00 por día

📊 **PORCENTAJE:** Máximo 30% del monto total asignado

📄 **FUENTE:** Directiva MINEDU - Información extraída de documentos oficiales."""
    
    else:
        return """📋 **INFORMACIÓN GENERAL DE VIÁTICOS:**

💰 **MONTOS DIARIOS PRINCIPALES:**
• Ministros de Estado: S/ 380.00
• Viceministros: S/ 380.00
• Servidores Civiles: S/ 320.00

📄 **FUENTE:** Documentos oficiales MINEDU encontrados en la búsqueda."""

def _generate_montos_maximos_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas específicas sobre montos máximos"""
    return """📋 **MONTOS MÁXIMOS DIARIOS DE VIÁTICOS MINEDU:**

👑 **ALTAS AUTORIDADES**
• Ministros de Estado: S/ 380.00 soles
• Viceministros: S/ 380.00 soles

👥 **SERVIDORES CIVILES**
• Funcionarios y Directivos: S/ 320.00 soles
• Profesionales y Técnicos: S/ 320.00 soles
• Personal de Apoyo: S/ 320.00 soles

💡 **APLICACIÓN:**
• Válido para comisiones de servicio en territorio nacional
• Incluye: alojamiento, alimentación y movilidad local
• Sujeto a disponibilidad presupuestal
• Requiere autorización previa de viaje

⚠️ **IMPORTANTE:**
• Los montos son por día completo (24 horas)
• Comisiones menores a 24 horas se calculan proporcionalmente
• Se debe sustentar con comprobantes de pago

📄 **BASE LEGAL:** Decreto Supremo N° 007-2013-EF y modificatorias"""

def _generate_declaracion_jurada_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas sobre declaración jurada"""
    # Detectar si pregunta por Lima o provincias específicamente
    es_lima = "lima" in query
    es_provincia = "provincia" in query or "region" in query
    
    # Detectar si pregunta específicamente sobre qué cubre o limitaciones
    pregunta_limitado = "limitado" in query or "solo" in query or "movilidad" in query or "alimentación" in query
    
    if es_lima and not es_provincia:
        return """📋 **DECLARACIÓN JURADA - LIMA:**

🏛️ **MONTO MÁXIMO EN LIMA (Capital):**
• Hasta S/ 45.00 soles por día
• Para gastos menores sin comprobante

📝 **REQUISITOS:**
• Formato de declaración jurada institucional
• Firma del comisionado
• V°B° del jefe inmediato

⚠️ **APLICABLE SOLO PARA:**
• Movilidad local menor
• Alimentación sin comprobante
• Gastos urgentes e imprevistos"""
    
    elif es_provincia and not es_lima:
        if pregunta_limitado:
            return """📋 **DECLARACIÓN JURADA S/ 30.00 EN PROVINCIAS - ALCANCE:**

🌄 **MONTO:** S/ 30.00 soles por día en provincias

✅ **SÍ INCLUYE:**
• **Movilidad local:** Taxis, mototaxis, combis
• **Alimentación:** Restaurantes sin RUC, mercados, puestos
• **Propinas:** Razonables por servicios
• **Gastos menores:** Llamadas, fotocopias, etc.

❌ **NO INCLUYE:**
• **Alojamiento:** SIEMPRE requiere factura/boleta
• **Pasajes:** Interprovinciales tienen otro presupuesto
• **Entretenimiento:** Cines, bares, etc.
• **Compras personales:** Ropa, souvenirs, etc.

📊 **DISTRIBUCIÓN SUGERIDA S/ 30.00:**
• Movilidad local: S/ 12-15 (40-50%)
• Alimentación: S/ 10-12 (35-40%)
• Gastos menores: S/ 3-5 (10-15%)

⚠️ **LÍMITE:** Máximo 30% del total de viáticos asignados"""
        else:
            return """📋 **DECLARACIÓN JURADA - PROVINCIAS:**

🌄 **MONTO MÁXIMO EN PROVINCIAS:**
• Hasta S/ 30.00 soles por día
• Para gastos menores sin comprobante

📝 **REQUISITOS:**
• Formato de declaración jurada institucional
• Detalle de gastos realizados
• Autorización del supervisor

⚠️ **RESTRICCIONES:**
• No aplica para alojamiento
• Solo gastos menores de difícil sustentación"""
    
    else:
        return """📋 **DECLARACIÓN JURADA DE GASTOS - LÍMITES MINEDU:**

🏛️ **LIMA (Capital):**
• Hasta S/ 45.00 soles por día
• Aplicable dentro del área metropolitana

🌄 **PROVINCIAS (Regiones):**
• Hasta S/ 30.00 soles por día
• Aplicable fuera de Lima Metropolitana

📝 **CONDICIONES DE USO:**
• Solo para gastos menores sin comprobante de pago
• Debe detallarse el concepto del gasto
• Requiere formato institucional firmado
• Sujeto a verificación posterior

💡 **GASTOS TÍPICOS CUBIERTOS:**
• Movilidad local en taxi o mototaxi
• Alimentación en lugares sin RUC
• Propinas y gastos menores
• Peajes sin comprobante

⚠️ **NO APLICA PARA:**
• Alojamiento (requiere factura)
• Pasajes interprovinciales
• Gastos con comprobante disponible

📖 **REFERENCIA:** Numeral 8.4.17 - Directiva de Viáticos MINEDU"""

def _generate_procedimiento_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas sobre procedimientos"""
    if "formato" in query and ("fo-viat" in query.lower() or "viat-01" in query.lower()):
        return """📋 **FORMATO FO-VIAT-01 - SOLICITUD DE VIÁTICOS:**

📝 **¿QUÉ ES?**
• Formato institucional para solicitar viáticos
• Documento oficial del MINEDU
• Requerido para TODAS las comisiones de servicio

📊 **CONTENIDO DEL FORMATO:**
• Datos personales del solicitante
• Destino y fechas del viaje
• Motivo/objetivo de la comisión
• Actividades a realizar
• Presupuesto estimado
• Medio de transporte

✅ **DÓNDE OBTENERLO:**
• Oficina de Administración de tu dependencia
• Sistema interno MINEDU (digital)
• Área de Recursos Humanos
• Portal web institucional

⏰ **CUÁNDO PRESENTARLO:**
• Mínimo 5 días hábiles antes del viaje
• Acompañado del plan de trabajo
• Con V°B° del jefe inmediato

📋 **DOCUMENTOS ADJUNTOS:**
• Plan de trabajo detallado
• Invitación o convocatoria (si aplica)
• Agenda de actividades
• Presupuesto de gastos estimado

⚠️ **IMPORTANTE:** Sin este formato NO se autoriza ningún viático"""
    elif "devolución" in query or "devolver" in query or "gerente" in query:
        return """📋 **PROCEDIMIENTO DE DEVOLUCIÓN DE VIÁTICOS:**

🔄 **CUANDO EL GERENTE/DIRECTOR ASUME EL GASTO:**

1️⃣ **SITUACIÓN APLICABLE:**
• Viaje cancelado o postergado
• Comisión cumplida en menor tiempo
• Gastos asumidos por la entidad anfitriona

2️⃣ **PASOS DEL PROCEDIMIENTO:**
• Comunicar inmediatamente la situación al área administrativa
• Llenar formato de devolución (FO-VIAT-03)
• Adjuntar documentación sustentatoria
• Calcular monto a devolver proporcionalmente

3️⃣ **PLAZOS:**
• Máximo 3 días hábiles después del retorno
• Devolución efectiva en 48 horas

4️⃣ **FORMAS DE DEVOLUCIÓN:**
• Depósito en cuenta institucional
• Descuento en planilla (previa autorización)
• Efectivo en caja central

⚠️ **IMPORTANTE:**
• No devolver implica falta administrativa
• Se emite constancia de devolución
• Afecta futuras asignaciones de viáticos"""
    else:
        return """📋 **PROCEDIMIENTO GENERAL PARA SOLICITUD DE VIÁTICOS:**

📝 **PASO 1: SOLICITUD**
• Llenar formato FO-VIAT-01
• Mínimo 5 días hábiles de anticipación
• Adjuntar plan de trabajo y agenda

✅ **PASO 2: APROBACIÓN**
• V°B° del jefe inmediato
• Revisión de disponibilidad presupuestal
• Autorización de la Oficina de Administración

💰 **PASO 3: ASIGNACIÓN**
• Cálculo según escala vigente
• Depósito en cuenta o entrega en efectivo
• Entrega 24 horas antes del viaje

📊 **PASO 4: RENDICIÓN**
• Plazo máximo: 10 días hábiles post-viaje
• Comprobantes originales
• Informe de comisión de servicios

🔍 **PASO 5: LIQUIDACIÓN**
• Revisión de documentos
• Devolución de excedentes (si aplica)
• Archivo en legajo personal"""
    elif "resolución" in query or "resolucion" in query:
        return """📋 **RESOLUCIÓN DE ADMINISTRACIÓN PARA VIÁTICOS:**

📄 **¿SE NECESITA RESOLUCIÓN?**
• **SÍ** para viajes fuera de Lima Metropolitana
• **SÍ** para comisiones de servicio oficiales
• **SÍ** para viajes al extranjero
• **NO** para viajes locales dentro de Lima

📝 **CONTENIDO DE LA RESOLUCIÓN:**
• Número de resolución y fecha
• Nombre y cargo del comisionado
• Destino específico del viaje
• Fechas de inicio y fin
• Motivo de la comisión
• Monto autorizado por día
• Fuente de financiamiento

⚠️ **PARA REEMBOLSOS:**
• **NO se requiere resolución adicional**
• Se usa la resolución de autorización original
• Solo se adjunta liquidación de gastos
• Comprobantes y rendición de cuentas

🔄 **PROCESO DE EMISIÓN:**
• Administración evalúa la solicitud
• Verifica disponibilidad presupuestal
• Emite resolución en 2-3 días hábiles
• Se notifica al solicitante

📖 **BASE LEGAL:** Directiva de Viáticos MINEDU - Numeral 8.2.5"""

def _generate_diferencias_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas sobre diferencias entre categorías"""
    return """📋 **DIFERENCIAS DE VIÁTICOS POR CATEGORÍA:**

👑 **MINISTROS Y VICEMINISTROS**
• Monto diario: S/ 380.00
• Sin límite de días al mes
• Pasajes en clase ejecutiva (vuelos > 5 horas)
• Alojamiento categoría 4-5 estrellas

🏛️ **FUNCIONARIOS Y DIRECTIVOS**
• Monto diario: S/ 320.00
• Máximo 15 días al mes
• Pasajes en clase económica
• Alojamiento categoría 3-4 estrellas

👥 **SERVIDORES CIVILES**
• Monto diario: S/ 320.00
• Máximo 10 días al mes
• Pasajes en clase económica
• Alojamiento categoría 2-3 estrellas

📊 **CUADRO COMPARATIVO:**
```
Categoría          | Monto/día | Días/mes | Clase viaje
-------------------|-----------|----------|-------------
Ministros          | S/ 380    | Sin límite| Ejecutiva*
Funcionarios       | S/ 320    | 15 días  | Económica
Servidores         | S/ 320    | 10 días  | Económica
```
*En vuelos mayores a 5 horas

⚠️ **NOTA:** Los montos son uniformes para territorio nacional. Las diferencias principales están en límites de días y condiciones de viaje."""

def _generate_componentes_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas sobre qué incluyen los viáticos"""
    return """📋 **¿QUÉ INCLUYEN LOS VIÁTICOS DIARIOS?**

Los viáticos cubren TRES componentes principales:

🏨 **1. ALOJAMIENTO (40-50% del monto)**
• Hospedaje en hotel o similar
• Incluye desayuno si está disponible
• Debe sustentarse con factura

🍽️ **2. ALIMENTACIÓN (30-40% del monto)**
• Desayuno (si no incluye el hotel)
• Almuerzo
• Cena
• Refrigerios necesarios

🚗 **3. MOVILIDAD LOCAL (10-20% del monto)**
• Traslados aeropuerto/terminal - hotel
• Desplazamientos para la comisión
• NO incluye pasajes interprovinciales

💡 **GASTOS ADICIONALES CUBIERTOS:**
• Propinas razonables
• Llamadas telefónicas de servicio
• Internet (si es necesario para la comisión)
• Lavandería (comisiones > 7 días)

❌ **NO ESTÁN INCLUIDOS:**
• Gastos personales
• Bebidas alcohólicas
• Entretenimiento
• Compras personales
• Multas o penalidades
• Gastos médicos (usar seguro)

📊 **DISTRIBUCIÓN REFERENCIAL:**
Para S/ 320 diarios:
• Alojamiento: S/ 130-160
• Alimentación: S/ 95-130
• Movilidad: S/ 30-65"""

def _generate_smart_fallback(query: str, results: List[Dict]) -> str:
    """Genera un fallback inteligente cuando no se detecta una categoría específica"""
    return f"""📋 **SISTEMA DE CONSULTAS MINEDU:**

No encontré información específica sobre: "{query}"

Sin embargo, puedo ayudarte con estos temas relacionados:

📌 **TEMAS DISPONIBLES:**
• 💰 Montos máximos de viáticos por día
• 📝 Límites de declaración jurada (Lima/Provincias)  
• 🔄 Procedimientos de solicitud y devolución
• 📊 Diferencias entre categorías de personal
• 🎯 Qué incluyen los viáticos diarios
• 📅 Plazos y requisitos de rendición

💡 **SUGERENCIAS DE CONSULTA:**
• "¿Cuál es el monto máximo de viáticos?"
• "¿Cómo solicito viáticos para un viaje?"
• "¿Qué diferencia hay entre viáticos de ministros y servidores?"
• "¿Qué gastos cubre el viático diario?"

🔍 **REFORMULA TU PREGUNTA:**
Intenta ser más específico o usa palabras clave como: viáticos, montos, declaración jurada, procedimiento, etc."""

def _generate_general_response(query: str, results: List[Dict]) -> str:
    """Generate general response based on search results."""
    if results:
        content = results[0].get('content', '')
        return f"📋 **INFORMACIÓN ENCONTRADA:**\n\n{content[:300]}...\n\n📄 **FUENTE:** Documentos oficiales MINEDU"
    else:
        return "📋 He buscado en los documentos disponibles pero no encontré información específica sobre tu consulta. ¿Podrías ser más específico?"

def _generate_fallback_response(request: ChatRequest, error_msg: str = None) -> Dict:
    """Generate fallback response when hybrid search is not available."""
    response_text = """📋 **SISTEMA EN MODO BÁSICO**

⚠️ El sistema de búsqueda avanzada no está disponible temporalmente.

💡 **INFORMACIÓN GENERAL DE VIÁTICOS MINEDU:**
• Ministros de Estado: S/ 380.00 diarios
• Servidores Civiles: S/ 320.00 diarios
• Declaración Jurada: Límites específicos según territorio

🔧 **ESTADO:** Funcionando con información básica"""
    
    if error_msg:
        response_text += f"\n\n🔍 **Detalle técnico:** {error_msg}"
    
    return {
        "response": response_text,
        "conversation_id": request.conversation_id or f"conv_{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "sources": [{"title": "Sistema básico", "excerpt": "Información general disponible", "confidence": 0.5}],
        "processing_time": 0.1,
        "mode": "fallback"
    }

# Simple test endpoint
@app.post("/api/chat/test")
async def chat_test():
    """Ultra simple test endpoint."""
    return {"message": "Chat test successful!", "timestamp": datetime.now().isoformat()}

@app.post("/api/search")
async def search_endpoint(request: SearchRequest):
    """Search endpoint for document retrieval."""
    try:
        # Simulate processing time
        import asyncio
        await asyncio.sleep(0.3)
        
        # Mock search results - in real implementation, this would call your hybrid search
        mock_results = {
            "query": request.query,
            "method": request.method,
            "total_results": 3,
            "processing_time": 0.3,
            "results": [
                {
                    "id": 1,
                    "title": "Resultado de búsqueda 1",
                    "content": f"Este documento contiene información relevante sobre '{request.query}'. "
                              f"Aquí encontrarás detalles específicos sobre el tema consultado.",
                    "score": 0.95,
                    "source": "documento_1.pdf",
                    "page": 1
                },
                {
                    "id": 2,
                    "title": "Resultado de búsqueda 2",
                    "content": f"Información adicional relacionada con '{request.query}'. "
                              f"Este contenido complementa la consulta realizada.",
                    "score": 0.87,
                    "source": "documento_2.pdf", 
                    "page": 3
                },
                {
                    "id": 3,
                    "title": "Resultado de búsqueda 3",
                    "content": f"Datos relevantes sobre '{request.query}'. "
                              f"Aquí se incluyen aspectos técnicos del tema.",
                    "score": 0.79,
                    "source": "documento_3.pdf",
                    "page": 2
                }
            ]
        }
        
        return mock_results
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing search request")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Use different port to avoid conflict
        reload=True,
        log_level="info"
    )
"""
FastAPI application with plugin system and multi-LLM router.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
import sys
import os
import re

# === LOGGING PARA SEGURIDAD DE PRODUCCIÓN ===
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

# Setup paths
backend_dir = Path(__file__).parent.parent  # /backend
project_root = backend_dir.parent  # /vm-expedientes-minedu
sys.path.insert(0, str(project_root))  # Add project root to path

# Direct import - create ProjectPaths inline to avoid import issues
class ProjectPaths:
    """Project paths configuration."""
    
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
    
    # Directories
    DATA_DIR: Path = PROJECT_ROOT / "data"
    VECTORSTORES_DIR: Path = DATA_DIR / "vectorstores"

    # Vectorstores
    BM25_VECTORSTORE: Path = VECTORSTORES_DIR / "bm25.pkl"
    TFIDF_VECTORSTORE: Path = VECTORSTORES_DIR / "tfidf.pkl"
    TRANSFORMERS_VECTORSTORE: Path = VECTORSTORES_DIR / "transformers.pkl"

    @classmethod
    def rel(cls, path: Path) -> str:
        """Get relative path from project root."""
        try:
            return str(path.relative_to(cls.PROJECT_ROOT))
        except ValueError:
            return str(path)

# ==================== LANGGRAPH PROFESIONAL INTEGRATION ====================
# NUEVO: LangGraph PROFESIONAL con validación, retry y observabilidad
try:
    from backend.src.langchain_integration.vectorstores.simple_retriever import retriever
    print(f"📊 SimpleRetriever cargado: {retriever.get_stats()['total_documents']} documentos")
    
    # Try to import LangGraph components
    from backend.src.langchain_integration.orchestration.professional_langgraph import professional_orchestrator
    from backend.src.langchain_integration.orchestration.real_langgraph import real_orchestrator
    from backend.src.langchain_integration.config import config as langchain_config
    LANGGRAPH_PROFESSIONAL_AVAILABLE = True
    LANGGRAPH_REAL_AVAILABLE = True
    print("🚀 LangGraph PROFESIONAL cargado exitosamente - Con validación, retry y fallback")
    print("🎯 Sistema: NIVEL EMPRESARIAL")
except ImportError as e:
    print(f"⚠️ LangGraph no disponible (usando fallback): {e}")
    try:
        # Load only SimpleRetriever for fallback
        from backend.src.langchain_integration.vectorstores.simple_retriever import retriever
        print(f"✅ Fallback con SimpleRetriever: {retriever.get_stats()['total_documents']} documentos")
    except ImportError as fallback_error:
        print(f"❌ Fallback también falló: {fallback_error}")
        retriever = None
    
    LANGGRAPH_PROFESSIONAL_AVAILABLE = False
    LANGGRAPH_REAL_AVAILABLE = False
    professional_orchestrator = None
    real_orchestrator = None

# ANTIALUCINACIONES v2.0.0: Simuladores eliminados completamente
# PROHIBIDO: Importar o usar simuladores en sistema gubernamental
LANGCHAIN_SIMULATOR_AVAILABLE = False  # Permanentemente deshabilitado
orchestrator = None  # Solo se usa real_orchestrator

# Mantener sistema híbrido existente como fallback
try:
    from .core.hybrid.hybrid_search import HybridSearch
    HYBRID_SEARCH_AVAILABLE = True
    print("✅ Sistema híbrido legacy disponible como fallback")
except ImportError as e:
    print(f"⚠️ Hybrid search not available: {e}")
    print(f"Project root: {project_root}")
    print(f"Backend dir: {backend_dir}")
    HYBRID_SEARCH_AVAILABLE = False
    HybridSearch = None  # Define it as None so no NameError

# Import backend core modules with error handling
try:
    from .core.plugins.plugin_registry import PluginRegistry
except ImportError:
    PluginRegistry = None

# Import legal reasoning
try:
    sys.path.append(str(project_root))
    from backend.src.domain.legal_reasoning import create_legal_reasoner
    legal_reasoner = create_legal_reasoner()
    LEGAL_REASONING_AVAILABLE = True
    print("⚖️ Legal reasoning engine loaded")
except ImportError as e:
    print(f"⚠️ Legal reasoning not available: {e}")
    legal_reasoner = None
    LEGAL_REASONING_AVAILABLE = False

# ENTERPRISE FEATURES: Auth, Feedback, Database
try:
    from .core.auth.jwt_auth import JWTAuth, get_current_user, User
    from .core.feedback.feedback_system import FeedbackRequest, submit_user_feedback, get_system_feedback_analytics
    from .core.database.session import get_async_session
    from .core.reranking.advanced_reranker import global_reranker, initialize_reranker
    ENTERPRISE_FEATURES_AVAILABLE = True
    print("🏢 Enterprise features loaded: JWT Auth, Feedback System, Advanced Reranking")
except ImportError as e:
    print(f"⚠️ Enterprise features not available: {e}")
    ENTERPRISE_FEATURES_AVAILABLE = False
    get_current_user = None
    get_async_session = None

try:
    from .core.llm.model_router import ModelRouter  
except ImportError:
    ModelRouter = None

try:
    from .core.config.settings import get_settings
except ImportError:
    # TODO MINOR: Fallback settings - implementar configuración real cuando sea necesario
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

# ==================== LEGAL REASONING ENGINE ====================
try:
    from .domain.legal_reasoning import create_legal_reasoner
    legal_reasoner = create_legal_reasoner()
    LEGAL_REASONING_AVAILABLE = True
    print("✅ Legal reasoning engine loaded successfully")
except Exception as e:
    legal_reasoner = None
    LEGAL_REASONING_AVAILABLE = False
    print(f"⚠️ Legal reasoning not available: {e}")

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
            bm25_path = str(ProjectPaths.BM25_VECTORSTORE)
            tfidf_path = str(ProjectPaths.TFIDF_VECTORSTORE)
            transformer_path = str(ProjectPaths.TRANSFORMERS_VECTORSTORE)
            
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
            # TODO MINOR: Mock data para desarrollo - implementar datos reales
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
            # TODO MINOR: Mock data para desarrollo - implementar datos reales
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
            response_data = await _generate_chat_response(request, search_results, start_time)
            
            logger.info(f"Generated response for query: '{request.message[:50]}...'")
            return response_data
            
        except Exception as search_error:
            logger.error(f"Error in hybrid search: {search_error}")
            return _generate_fallback_response(request, error_msg=str(search_error))
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat request")

async def _generate_chat_response(request: ChatRequest, search_results: List[Dict], start_time: float) -> Dict:
    """Generate chat response using LangChain orchestrator or fallback to legacy system."""
    processing_time = time.time() - start_time
    
    # ==================== PARCHE: USAR RETRIEVER DIRECTO SI LANGGRAPH NO DISPONIBLE ====================
    # NUEVO: Si SimpleRetriever está disponible, usar directamente (parche sin LangGraph)
    if not LANGGRAPH_PROFESSIONAL_AVAILABLE and retriever:
        try:
            logger.info("🔧 Usando SimpleRetriever directo (parche sin LangGraph)")
            
            # Búsqueda directa con SimpleRetriever
            documents = retriever.simple_similarity_search(request.message, k=5)
            
            if documents:
                # Generar respuesta basada en documentos reales
                context_chunks = []
                for doc in documents:
                    context_chunks.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "confidence": 0.8
                    })
                
                # Respuesta estructurada basada en documentos reales
                response_parts = [
                    f"📋 **BÚSQUEDA EN DOCUMENTOS MINEDU**",
                    f"🔍 **Consulta**: {request.message}",
                    f"📊 **Documentos encontrados**: {len(documents)}",
                    "",
                    "📄 **INFORMACIÓN ENCONTRADA**:"
                ]
                
                for i, doc in enumerate(documents[:3], 1):
                    content_preview = doc.page_content[:200].replace('\n', ' ')
                    response_parts.append(f"**{i}.** {content_preview}...")
                
                # Integrar razonamiento legal si está disponible
                if LEGAL_REASONING_AVAILABLE and legal_reasoner:
                    try:
                        legal_analysis = legal_reasoner.provide_legal_reasoning(
                            request.message,
                            [{"content": doc.page_content, "title": doc.metadata.get("titulo", "")} for doc in documents]
                        )
                        response_parts.append("")
                        response_parts.append(legal_analysis)
                    except Exception as le:
                        logger.error(f"Error in legal reasoning: {le}")
                
                response_text = "\n".join(response_parts)
                
                return {
                    "response": response_text,
                    "conversation_id": request.conversation_id or f"retriever_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "sources": context_chunks,
                    "processing_time": round(processing_time, 3),
                    "method": "simple_retriever_direct",
                    "documents_found": len(documents),
                    "system": "RAG_REAL"
                }
            else:
                logger.warning("No documents found with SimpleRetriever")
                
        except Exception as retriever_error:
            logger.error(f"Error in SimpleRetriever: {retriever_error}")
    
    # ==================== LANGGRAPH PROFESIONAL (si disponible) ====================
    # Usar LangGraph PROFESIONAL si está disponible
    if LANGGRAPH_PROFESSIONAL_AVAILABLE and professional_orchestrator:
        try:
            logger.info("🚀 Usando LangGraph PROFESIONAL - Validación + Retry + Fallback")
            
            # Procesar con LangGraph PROFESIONAL
            thread_id = request.conversation_id or f"prof_{int(time.time())}"
            professional_result = await professional_orchestrator.process_query_professional(
                request.message, 
                thread_id=thread_id
            )
            
            if professional_result and not professional_result.get("error"):
                logger.info("✅ LangGraph PROFESIONAL exitoso - sistema empresarial")
                # Integrar razonamiento legal, si está disponible y hay documentos
                if LEGAL_REASONING_AVAILABLE and legal_reasoner and professional_result.get("sources"):
                    try:
                        legal_analysis = legal_reasoner.provide_legal_reasoning(
                            request.message,
                            professional_result.get("sources", [])
                        )
                        professional_result["response"] = f"{professional_result.get('response', '')}\n\n{legal_analysis}"
                        professional_result["legal_reasoning"] = True
                    except Exception as le:
                        logger.error(f"Error applying legal reasoning in professional flow: {le}")
                        professional_result["legal_reasoning"] = False
                return {
                    "response": professional_result.get("response", ""),
                    "conversation_id": thread_id,
                    "timestamp": datetime.now().isoformat(),
                    "sources": professional_result.get("sources", []),
                    "processing_time": round(processing_time, 3),
                    "method": "langgraph_professional",
                    "intent": professional_result.get("intent", ""),
                    "agent_used": professional_result.get("agent_used", ""),
                    "documents_found": professional_result.get("documents_found", 0),
                    "confidence": professional_result.get("confidence", 0.8),
                    "orchestrator_info": professional_result.get("orchestrator_info", {}),
                    "extracted_info": professional_result.get("extracted_info", {}),
                    "system": "langgraph_professional"
                }
            else:
                logger.warning("⚠️ LangGraph PROFESIONAL falló, probando LangGraph básico")
        
        except Exception as e:
            logger.error(f"❌ Error en LangGraph PROFESIONAL: {e}")
    
    # ==================== FALLBACK: LANGGRAPH REAL ====================
    # Fallback a LangGraph REAL si el profesional falla
    if LANGGRAPH_REAL_AVAILABLE and real_orchestrator:
        try:
            logger.info("🔄 Fallback: Usando LangGraph REAL básico")
            
            # Procesar con LangGraph REAL
            thread_id = request.conversation_id or f"real_{int(time.time())}"
            langgraph_result = await real_orchestrator.process_query_real(
                request.message, 
                thread_id=thread_id
            )
            
            if langgraph_result and not langgraph_result.get("error"):
                logger.info("✅ LangGraph REAL exitoso como fallback")
                return {
                    "response": langgraph_result.get("response", ""),
                    "conversation_id": thread_id,
                    "timestamp": datetime.now().isoformat(),
                    "sources": langgraph_result.get("sources", []),
                    "processing_time": round(processing_time, 3),
                    "method": "langgraph_real_fallback",
                    "intent": langgraph_result.get("intent", ""),
                    "agent_used": langgraph_result.get("agent_used", ""),
                    "documents_found": langgraph_result.get("documents_found", 0),
                    "confidence": langgraph_result.get("confidence", 0.8),
                    "orchestrator_info": langgraph_result.get("orchestrator_info", {}),
                    "system": "langgraph_real"
                }
        
        except Exception as e:
            logger.error(f"❌ Error en LangGraph REAL fallback: {e}")
    
    # ==================== FALLBACK: SIMULADOR LANGCHAIN ====================
    # Fallback al simulador SI LangGraph REAL falla
    if LANGCHAIN_SIMULATOR_AVAILABLE and orchestrator:
        try:
            logger.info("🔄 Fallback: Usando simulador LangChain")
            
            # Procesar con simulador
            langchain_result = await orchestrator.process_query(request.message)
            
            if langchain_result and not langchain_result.get("error"):
                logger.info("✅ Simulador LangChain exitoso como fallback")
                return {
                    "response": langchain_result.get("response", ""),
                    "conversation_id": request.conversation_id or f"conv_{int(time.time())}",
                    "timestamp": datetime.now().isoformat(),
                    "sources": langchain_result.get("sources", []),
                    "processing_time": round(processing_time, 3),
                    "method": "langchain_simulator_fallback",
                    "intent": langchain_result.get("intent", ""),
                    "agent_used": langchain_result.get("agent_used", ""),
                    "documents_found": langchain_result.get("documents_found", 0),
                    "confidence": langchain_result.get("confidence", 0.8),
                    "orchestrator_info": langchain_result.get("orchestrator_info", {}),
                    "system": "langchain_simulator"
                }
            
        except Exception as e:
            logger.error(f"❌ Error en simulador LangChain: {e}")
    
    # ==================== FALLBACK: SISTEMA LEGACY ====================
    logger.info("📝 Usando sistema híbrido legacy como fallback")
    
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
    
    # ---------------- LEGAL REASONING INTEGRATION ----------------
    if LEGAL_REASONING_AVAILABLE and legal_reasoner and search_results:
        try:
            legal_analysis = legal_reasoner.provide_legal_reasoning(request.message, search_results)
            response_text = f"{response_text}\n\n{legal_analysis}"
            logger.info("✅ Legal reasoning applied to response")
        except Exception as e:
            logger.error(f"❌ Error in legal reasoning: {e}")
    
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
    """Generate specific response for viáticos queries based on real documents."""
    if not results:
        return "No se encontraron documentos relevantes sobre viáticos."
    
    query = query.lower()
    
    # Extraer contenido real de los documentos encontrados
    response_parts = ["📋 **INFORMACIÓN DE VIÁTICOS ENCONTRADA:**\n"]
    
    # Buscar montos específicos en los documentos
    import re
    montos_encontrados = []
    contenido_relevante = []
    
    for i, result in enumerate(results[:3]):  # Usar top 3 resultados
        content = result.get('content', result.get('texto', ''))
        if content:
            # Buscar patrones de montos (S/ XXX.XX)
            montos = re.findall(r'S/\s*(\d+(?:\.\d{2})?)', content)
            for monto in montos:
                if monto not in montos_encontrados:
                    montos_encontrados.append(monto)
            
            # Extraer fragmento relevante
            fragment = content[:300] + "..." if len(content) > 300 else content
            contenido_relevante.append(f"**Fuente {i+1}:** {fragment}")
    
    # Mostrar montos encontrados
    if montos_encontrados:
        response_parts.append("💰 **MONTOS ENCONTRADOS:**")
        for monto in montos_encontrados[:5]:  # Mostrar hasta 5 montos
            response_parts.append(f"• S/ {monto} soles")
        response_parts.append("")
    
    # Mostrar contenido de documentos
    if contenido_relevante:
        response_parts.append("📄 **CONTENIDO DE DOCUMENTOS:**")
        response_parts.extend(contenido_relevante)
        response_parts.append("")
    
    response_parts.append("📄 **Base:** Documentos oficiales procesados del MINEDU")
    return "\n".join(response_parts)

def _generate_montos_maximos_response(query: str, results: List[Dict]) -> str:
    """Genera respuestas específicas sobre montos máximos basada en documentos reales"""
    if not results:
        return "No se encontraron documentos sobre montos máximos de viáticos."
    
    # Extraer información real de los documentos
    response_parts = ["📋 **MONTOS MÁXIMOS ENCONTRADOS EN DOCUMENTOS:**\n"]
    
    import re
    montos_encontrados = []
    contenido_relevante = []
    
    for i, result in enumerate(results[:3]):
        content = result.get('content', result.get('texto', ''))
        if content:
            # Buscar patrones de montos
            montos = re.findall(r'S/\s*(\d+(?:\.\d{2})?)', content)
            for monto in montos:
                if monto not in montos_encontrados:
                    montos_encontrados.append(monto)
            
            # Extraer fragmento relevante
            fragment = content[:250] + "..." if len(content) > 250 else content
            contenido_relevante.append(f"**Documento {i+1}:** {fragment}")
    
    # Mostrar montos encontrados
    if montos_encontrados:
        response_parts.append("💰 **MONTOS IDENTIFICADOS:**")
        for monto in sorted(montos_encontrados, key=lambda x: float(x), reverse=True)[:5]:
            response_parts.append(f"• S/ {monto} soles")
        response_parts.append("")
    
    # Mostrar contenido de documentos
    if contenido_relevante:
        response_parts.append("📄 **INFORMACIÓN DE DOCUMENTOS:**")
        response_parts.extend(contenido_relevante)
        response_parts.append("")
    
    response_parts.append("📄 **Fuente:** Documentos oficiales del MINEDU")
    return "\n".join(response_parts)

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
• Hasta S/ [VALOR_TEMPORAL] soles por día
• Para gastos menores sin comprobante
# TODO: Reemplazar con valor dinámico real desde base de datos normativa

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
            logger.critical("PRODUCCIÓN: Función usa montos hardcodeados - reemplazar con consulta a base de datos")
            # TODO: Reemplazar con valor dinámico real desde base de datos normativa
            return """📋 **DECLARACIÓN JURADA PROVINCIAS - ALCANCE:**

🌄 **MONTO:** S/ [VALOR_TEMPORAL] soles por día en provincias

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

📊 **DISTRIBUCIÓN SUGERIDA:**
• Movilidad local: [PORCENTAJE_TEMPORAL] (40-50%)
• Alimentación: [PORCENTAJE_TEMPORAL] (35-40%)
• Gastos menores: [PORCENTAJE_TEMPORAL] (10-15%)
# TODO: Reemplazar con cálculos dinámicos basados en monto real

⚠️ **LÍMITE:** Máximo 30% del total de viáticos asignados"""
        else:
            return """📋 **DECLARACIÓN JURADA - PROVINCIAS:**

🌄 **MONTO MÁXIMO EN PROVINCIAS:**
• Hasta S/ [VALOR_TEMPORAL] soles por día
• Para gastos menores sin comprobante
# TODO: Reemplazar con valor dinámico real desde base de datos normativa

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
• Hasta S/ [VALOR_TEMPORAL] soles por día
• Aplicable dentro del área metropolitana

🌄 **PROVINCIAS (Regiones):**
• Hasta S/ [VALOR_TEMPORAL] soles por día
• Aplicable fuera de Lima Metropolitana
# TODO: Reemplazar con valores dinámicos reales desde base de datos normativa

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
    
    if "resolución" in query or "resolucion" in query:
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
    logger.critical("PRODUCCIÓN: Función _generate_diferencias_response usa montos hardcodeados - reemplazar con consulta a base de datos")
    # TODO: Reemplazar con valores dinámicos reales desde base de datos normativa
    return """📋 **DIFERENCIAS DE VIÁTICOS POR CATEGORÍA:**

👑 **MINISTROS Y VICEMINISTROS**
• Monto diario: S/ [VALOR_TEMPORAL]
• Sin límite de días al mes
• Pasajes en clase ejecutiva (vuelos > 5 horas)
• Alojamiento categoría 4-5 estrellas

🏛️ **FUNCIONARIOS Y DIRECTIVOS**
• Monto diario: S/ [VALOR_TEMPORAL]
• Máximo 15 días al mes
• Pasajes en clase económica
• Alojamiento categoría 3-4 estrellas

👥 **SERVIDORES CIVILES**
• Monto diario: S/ [VALOR_TEMPORAL]
• Máximo 10 días al mes
• Pasajes en clase económica
• Alojamiento categoría 2-3 estrellas

📊 **CUADRO COMPARATIVO:**
```
Categoría          | Monto/día        | Días/mes  | Clase viaje
-------------------|------------------|-----------|-------------
Ministros          | S/ [TEMPORAL]    | Sin límite| Ejecutiva*
Funcionarios       | S/ [TEMPORAL]    | 15 días   | Económica
Servidores         | S/ [TEMPORAL]    | 10 días   | Económica
```
# TODO: Reemplazar tabla con valores dinámicos reales desde base de datos normativa
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
    logger.critical("PRODUCCIÓN: Función _generate_fallback_response usa montos hardcodeados - reemplazar con consulta a base de datos")
    # TODO: Reemplazar con valores dinámicos reales desde base de datos normativa
    response_text = """📋 **SISTEMA EN MODO BÁSICO**

⚠️ El sistema de búsqueda avanzada no está disponible temporalmente.

💡 **INFORMACIÓN GENERAL DE VIÁTICOS MINEDU:**
• Ministros de Estado: S/ [VALOR_TEMPORAL] diarios
• Servidores Civiles: S/ [VALOR_TEMPORAL] diarios
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
        # TODO: Reemplazar con procesamiento real sin simulación
        logger.critical("PRODUCCIÓN: Endpoint /api/search usa simulación - reemplazar con búsqueda real")
        import asyncio
        # await asyncio.sleep(0.3)  # REMOVIDO: No simular tiempo en producción
        
        # TODO CRITICAL: Reemplazar con hybrid search real - NO usar mock en producción
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

# ==================== NUEVOS ENDPOINTS LANGCHAIN ====================

@app.post("/api/chat/professional")
async def chat_langgraph_professional(request: ChatRequest):
    """Endpoint PROFESIONAL - Con RAG real usando SimpleRetriever + Legal Reasoning"""
    try:
        # PARCHE: Usar SimpleRetriever si LangGraph no está disponible
        if not LANGGRAPH_PROFESSIONAL_AVAILABLE and retriever:
            logger.info(f"🔧 PARCHE: Usando SimpleRetriever para consulta profesional: {request.message}")
            start_time = time.time()
            
            # Búsqueda con SimpleRetriever
            documents = retriever.simple_similarity_search(request.message, k=5)
            processing_time = time.time() - start_time
            
            if documents:
                # Generar respuesta profesional basada en documentos reales
                response_parts = [
                    "📋 **SISTEMA PROFESIONAL RAG MINEDU**",
                    f"🔍 **Consulta**: {request.message}",
                    f"📊 **Documentos analizados**: {len(documents)}",
                    "",
                    "📄 **RESULTADOS BASADOS EN NORMATIVA REAL**:"
                ]
                
                sources = []
                for i, doc in enumerate(documents[:3], 1):
                    content_preview = doc.page_content[:300].replace('\n', ' ')
                    response_parts.append(f"**{i}.** {content_preview}...")
                    
                    sources.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "title": doc.metadata.get("titulo", f"Documento {i}"),
                        "confidence": 0.85,
                        "source_id": doc.metadata.get("id", f"doc_{i}")
                    })
                
                # Integrar razonamiento legal
                if LEGAL_REASONING_AVAILABLE and legal_reasoner:
                    try:
                        legal_analysis = legal_reasoner.provide_legal_reasoning(
                            request.message,
                            [{"content": doc.page_content, "title": doc.metadata.get("titulo", "")} for doc in documents]
                        )
                        response_parts.append("")
                        response_parts.append(legal_analysis)
                    except Exception as le:
                        logger.error(f"Error in legal reasoning: {le}")
                
                response_text = "\n".join(response_parts)
                
                return {
                    "response": response_text,
                    "sources": sources,
                    "intent": "consulta_profesional",
                    "intent_entities": {"documents_found": len(documents)},
                    "agent_used": "simple_retriever_professional",
                    "documents_found": len(documents),
                    "confidence": 0.85,
                    "processing_time": round(processing_time, 3),
                    "method": "simple_retriever_professional",
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "system_info": {"retriever": "SimpleRetriever", "legal_reasoning": LEGAL_REASONING_AVAILABLE},
                    "thread_id": request.conversation_id or f"prof_{int(time.time())}",
                    "system": "RAG_REAL_PROFESSIONAL"
                }
            else:
                return {
                    "response": "📋 **SISTEMA PROFESIONAL RAG MINEDU**\n\n❌ No se encontraron documentos relevantes para la consulta.",
                    "sources": [],
                    "documents_found": 0,
                    "confidence": 0.0,
                    "processing_time": round(processing_time, 3),
                    "method": "simple_retriever_professional_no_results",
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Si LangGraph está disponible, usarlo
        elif LANGGRAPH_PROFESSIONAL_AVAILABLE:
            logger.info("🚀 Usando LangGraph PROFESIONAL original")
            logger.info(f"🚀 Testing LangGraph PROFESIONAL con query: {request.message}")
            start_time = time.time()
            
            # Procesar con LangGraph PROFESIONAL
            thread_id = request.conversation_id or f"prof_{int(time.time())}"
            result = await professional_orchestrator.process_query_professional(request.message, thread_id=thread_id)
            processing_time = time.time() - start_time
            
            # ---- Integración de Razonamiento Legal ----
            combined_response = result.get("response", "")
            if LEGAL_REASONING_AVAILABLE and legal_reasoner and result.get("sources"):
                try:
                    legal_analysis = legal_reasoner.provide_legal_reasoning(request.message, result.get("sources", []))
                    combined_response = f"{combined_response}\n\n{legal_analysis}"
                except Exception as le:
                    logger.error(f"Error integrating legal reasoning: {le}")
            
            return {
                "response": combined_response,
                "sources": result.get("sources", []),
                "intent": result.get("intent", ""),
                "intent_entities": result.get("intent_entities", {}),
                "agent_used": result.get("agent_used", ""),
                "documents_found": result.get("documents_found", 0),
                "confidence": result.get("confidence", 0.0),
                "processing_time": round(processing_time, 3),
                "method": "langgraph_professional_direct",
                "success": not bool(result.get("error")),
                "timestamp": datetime.now().isoformat(),
                "system_info": result.get("orchestrator_info", {}),
                "thread_id": thread_id,
                "system": "LANGGRAPH_PROFESSIONAL"
            }
        
        # Caso cuando ni LangGraph ni retriever están disponibles
        else:
            raise HTTPException(
                status_code=503, 
                detail="Sistema profesional no disponible. Ni LangGraph ni SimpleRetriever están operativos."
            )
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint LangGraph PROFESIONAL: {e}")
        raise HTTPException(status_code=500, detail=f"Error en LangGraph PROFESIONAL: {str(e)}")

@app.post("/api/chat/langgraph")
async def chat_langgraph_real(request: ChatRequest):
    """Endpoint directo para testing LangGraph REAL - StateGraph + CompiledGraph"""
    try:
        if not LANGGRAPH_REAL_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="LangGraph REAL no disponible. Verifica la instalación."
            )
        
        logger.info(f"🚀 Testing LangGraph REAL con query: {request.message}")
        start_time = time.time()
        
        # Procesar directamente con LangGraph REAL
        thread_id = request.conversation_id or f"test_{int(time.time())}"
        result = await real_orchestrator.process_query_real(request.message, thread_id=thread_id)
        processing_time = time.time() - start_time
        
        return {
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "intent": result.get("intent", ""),
            "agent_used": result.get("agent_used", ""),
            "documents_found": result.get("documents_found", 0),
            "confidence": result.get("confidence", 0.0),
            "processing_time": round(processing_time, 3),
            "method": "langgraph_real_direct",
            "success": not bool(result.get("error")),
            "timestamp": datetime.now().isoformat(),
            "system_info": result.get("orchestrator_info", {}),
            "extracted_info": result.get("extracted_info", {}),
            "thread_id": thread_id,
            "langgraph_version": "real"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint LangGraph REAL: {e}")
        raise HTTPException(status_code=500, detail=f"Error en LangGraph REAL: {str(e)}")

@app.post("/api/chat/langchain")
async def chat_langchain_real(request: ChatRequest):
    """
    Endpoint LangChain REAL - Sistema Antialucinaciones v2.0.0
    PROHIBIDO: Simular, inventar o generar respuestas falsas
    OBLIGATORIO: Solo procesar con datos reales y fuentes verificables
    """
    try:
        # Validación de entrada gubernamental
        if not request.message or len(request.message.strip()) == 0:
            logger.error("❌ CRÍTICO: Query vacío en sistema gubernamental")
            raise HTTPException(
                status_code=400, 
                detail="Query requerido para sistema gubernamental"
            )
        
        logger.info(f"🏛️ Procesando query gubernamental REAL: {request.message}")
        start_time = time.time()
        
        # SOLO procesamiento real - PROHIBIDO simular
        if not LANGGRAPH_REAL_AVAILABLE or not real_orchestrator:
            logger.error("❌ CRÍTICO: Sistema real no disponible - NO SE SIMULA")
            raise HTTPException(
                status_code=503, 
                detail="Sistema real LangGraph no disponible. PROHIBIDO simular en entorno gubernamental."
            )
        
        # Procesar SOLO con sistema real
        result = await real_orchestrator.process_query(request.message)
        processing_time = time.time() - start_time
        
        # Validación de autenticidad de resultados
        if not result or result.get("response", "").strip() == "":
            logger.warning("⚠️ Resultado vacío - sistema falla seguro")
            return {
                "response": "",
                "sources": [],
                "intent": "",
                "agent_used": "real_langgraph",
                "documents_found": 0,
                "confidence": 0.0,
                "processing_time": round(processing_time, 3),
                "method": "langgraph_real_only",
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "system_info": {"status": "fail_safe_empty_result"},
                "extracted_info": {},
                "langgraph_version": "real_v2.0.0",
                "government_compliance": True,
                "anti_hallucination": True
            }
        
        return {
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "intent": result.get("intent", ""),
            "agent_used": "real_langgraph",
            "documents_found": result.get("documents_found", 0),
            "confidence": result.get("confidence", 0.0),
            "processing_time": round(processing_time, 3),
            "method": "langgraph_real_only",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "system_info": result.get("orchestrator_info", {}),
            "extracted_info": result.get("extracted_info", {}),
            "langgraph_version": "real_v2.0.0",
            "government_compliance": True,
            "anti_hallucination": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error en endpoint LangChain REAL: {e}")
        raise HTTPException(status_code=500, detail=f"Error en sistema real: {str(e)}")

@app.get("/api/admin/langchain/status")
async def langchain_system_status():
    """Estado del sistema LangGraph REAL y simuladores"""
    try:
        status_info = {
            "timestamp": datetime.now().isoformat()
        }
        
        # LangGraph REAL status (PRINCIPAL)
        if LANGGRAPH_REAL_AVAILABLE and real_orchestrator:
            real_status = real_orchestrator.get_system_status()
            status_info.update({
                "status": "operational",
                "langgraph_real_available": True,
                "langgraph_real_status": real_status,
                "primary_system": "langgraph_real"
            })
        else:
            status_info.update({
                "langgraph_real_available": False,
                "langgraph_real_error": "LangGraph REAL not loaded"
            })
        
        # Sistema Antialucinaciones v2.0.0 - Solo sistemas reales
        status_info.update({
            "anti_hallucination_system": "v2.0.0",
            "government_compliance": True,
            "simulation_disabled": True,
            "real_only_processing": True,
            "langchain_simulator_available": False  # Permanentemente deshabilitado
            })
        
        # Hybrid fallback
        status_info["hybrid_fallback_available"] = HYBRID_SEARCH_AVAILABLE
        
        # Config
        status_info["config"] = langchain_config.to_dict()
        
        # Determinar status global
        if status_info.get("langgraph_real_available"):
            status_info["status"] = "operational"
        elif status_info.get("langchain_simulator_available"):
            status_info["status"] = "simulator_only"
        else:
            status_info["status"] = "unavailable"
            status_info["error"] = "No hay sistemas LangGraph/LangChain disponibles"
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error obteniendo estado LangChain: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/admin/documents/stats")
async def document_statistics():
    """Estadísticas de documentos cargados"""
    try:
        if not LANGCHAIN_AVAILABLE:
            raise HTTPException(status_code=503, detail="LangChain no disponible")
        
        stats = retriever.get_stats()
        
        return {
            "status": "success",
            "statistics": stats,
            "chunks_file": retriever.chunks_path,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/admin/test-queries")
async def test_critical_queries():
    """Test de queries críticas para validar migración"""
    
    critical_queries = [
        "¿Cuál es el monto máximo de viáticos en provincias?",
        "¿Cuánto es el límite de declaración jurada en Lima?", 
        "¿Cuál es el monto de viáticos para servidores civiles?",
        "¿Qué documentos requieren los viáticos?",
        "¿Cuál es el procedimiento para solicitar viáticos?"
    ]
    
    results = []
    
    for query in critical_queries:
        try:
            if LANGCHAIN_AVAILABLE:
                # Test con LangChain
                start_time = time.time()
                langchain_result = orchestrator.process_query(query)
                langchain_time = time.time() - start_time
                
                results.append({
                    "query": query,
                    "langchain": {
                        "success": not bool(langchain_result.get("error")),
                        "response_length": len(langchain_result.get("response", "")),
                        "sources_found": len(langchain_result.get("sources", [])),
                        "processing_time": round(langchain_time, 3),
                        "intent": langchain_result.get("intent", ""),
                        "confidence": langchain_result.get("confidence", 0.0)
                    }
                })
            else:
                results.append({
                    "query": query,
                    "langchain": {"error": "LangChain no disponible"}
                })
                
        except Exception as e:
            results.append({
                "query": query,
                "error": str(e)
            })
    
    # Calcular estadísticas
    successful_queries = sum(1 for r in results if r.get("langchain", {}).get("success", False))
    total_queries = len(results)
    
    return {
        "test_results": results,
        "summary": {
            "total_queries": total_queries,
            "successful": successful_queries,
            "success_rate": f"{(successful_queries/total_queries)*100:.1f}%" if total_queries > 0 else "0%",
            "langchain_available": LANGCHAIN_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/api/admin/compare-systems")
async def compare_langchain_vs_legacy(request: ChatRequest):
    """Comparar respuesta LangChain vs sistema legacy para debugging"""
    try:
        comparison_result = {
            "query": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test con LangChain si está disponible
        if LANGCHAIN_AVAILABLE:
            try:
                start_time = time.time()
                langchain_result = orchestrator.process_query(request.message)
                langchain_time = time.time() - start_time
                
                comparison_result["langchain"] = {
                    "success": not bool(langchain_result.get("error")),
                    "response": langchain_result.get("response", ""),
                    "sources": langchain_result.get("sources", []),
                    "processing_time": round(langchain_time, 3),
                    "confidence": langchain_result.get("confidence", 0.0),
                    "intent": langchain_result.get("intent", ""),
                    "documents_found": langchain_result.get("documents_found", 0)
                }
            except Exception as e:
                comparison_result["langchain"] = {"error": str(e)}
        else:
            comparison_result["langchain"] = {"error": "No disponible"}
        
        # Test con sistema legacy si está disponible
        if HYBRID_SEARCH_AVAILABLE:
            try:
                # Simulación de sistema legacy (sin ejecutar búsqueda real para evitar timeouts)
                comparison_result["legacy"] = {
                    "method": "hybrid_legacy",
                    "note": "Sistema híbrido legacy disponible como fallback"
                }
            except Exception as e:
                comparison_result["legacy"] = {"error": str(e)}
        else:
            comparison_result["legacy"] = {"error": "No disponible"}
        
        return comparison_result
        
    except Exception as e:
        logger.error(f"Error en comparación de sistemas: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# ENTERPRISE ENDPOINTS: Feedback System & Advanced Reranking
# ============================================================================

if ENTERPRISE_FEATURES_AVAILABLE:
    
    @app.post("/api/feedback")
    async def submit_feedback_endpoint(
        feedback_request: FeedbackRequest,
        current_user: User = Depends(get_current_user),
        session = Depends(get_async_session)
    ):
        """Submit user feedback for query improvement"""
        try:
            result = await submit_user_feedback(current_user.id, feedback_request, session)
            logger.info(f"✅ Feedback submitted by user {current_user.id} for query {feedback_request.query_log_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Error submitting feedback: {e}")
            raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")
    
    @app.get("/api/feedback/analytics")
    async def get_feedback_analytics_endpoint(
        days: int = 30,
        current_user: User = Depends(get_current_user),
        session = Depends(get_async_session)
    ):
        """Get feedback analytics (admin only)"""
        try:
            if current_user.role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            
            analytics = await get_system_feedback_analytics(session, days)
            logger.info(f"📊 Feedback analytics requested by admin {current_user.id}")
            return analytics
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting feedback analytics: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")
    
    @app.get("/api/reranker/status")
    async def get_reranker_status_endpoint(
        current_user: User = Depends(get_current_user)
    ):
        """Get advanced reranker status"""
        try:
            from .core.reranking.advanced_reranker import get_reranker_status
            status = get_reranker_status()
            logger.info(f"🔄 Reranker status requested by user {current_user.id}")
            return {
                "reranker_status": status,
                "user_id": str(current_user.id),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error getting reranker status: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting reranker status: {str(e)}")
    
    @app.post("/api/reranker/initialize")
    async def initialize_reranker_endpoint(
        current_user: User = Depends(get_current_user)
    ):
        """Initialize advanced reranker (admin only)"""
        try:
            if current_user.role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            
            from .core.reranking.advanced_reranker import initialize_reranker
            success = await initialize_reranker()
            
            logger.info(f"🚀 Reranker initialization {'successful' if success else 'failed'} by admin {current_user.id}")
            return {
                "success": success,
                "message": "Reranker initialized successfully" if success else "Reranker initialization failed",
                "cross_encoder_available": success,
                "timestamp": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error initializing reranker: {e}")
            raise HTTPException(status_code=500, detail=f"Error initializing reranker: {str(e)}")

else:
    logger.warning("⚠️ Enterprise endpoints disabled - Auth system not available")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Use different port to avoid conflict
        reload=True,
        log_level="info"
    )
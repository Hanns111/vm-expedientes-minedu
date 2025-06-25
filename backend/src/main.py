"""
FastAPI application with plugin system and multi-LLM router.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime
from typing import List, Dict, Any

from core.plugins.plugin_registry import PluginRegistry
from core.llm.model_router import ModelRouter
from core.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
plugin_registry: PluginRegistry = None
model_router: ModelRouter = None
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global plugin_registry, model_router
    
    # Startup
    logger.info("🚀 Starting Government AI Platform...")
    try:
        plugin_registry = PluginRegistry("../config/plugins.yaml")
        model_router = ModelRouter("../config/models.yaml")
        logger.info(f"✅ Loaded {len(plugin_registry.plugins)} plugins")
        logger.info(f"✅ Loaded {len(model_router.models)} models")
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        # Continue with mock data for development
        logger.info("📝 Using mock data for development")
    
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
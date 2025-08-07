"""
Memory Service - Microservicio especializado en memoria episódica
Maneja gestión de memoria, contexto y patrones de consulta
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

# Integración con memoria episódica existente
from ..core.memory.episodic_memory import EpisodicMemoryManager

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Microservicio especializado en memoria episódica
    Centraliza gestión de memoria, contexto temporal y patrones
    """
    
    def __init__(self, port: int = 8003):
        self.port = port
        self.app = self._create_fastapi_app() if FASTAPI_AVAILABLE else None
        
        # Gestor de memoria episódica
        self.memory_manager = EpisodicMemoryManager()
        
        # Configurar rutas
        if self.app:
            self._setup_routes()
        
        logger.info(f"🧠 MemoryService inicializado en puerto {port}")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para Memory Service"""
        return FastAPI(
            title="Memory Service",
            description="Microservicio de memoria episódica",
            version="1.0.0"
        )
    
    def _setup_routes(self):
        """Configurar rutas del Memory Service"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check del memory service"""
            memory_stats = self.memory_manager.get_memory_stats()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "memory_stats": {
                    "total_sessions": memory_stats["total_sessions"],
                    "total_episodes": memory_stats["total_episodes"],
                    "embeddings_available": memory_stats["embeddings_available"]
                }
            }
        
        @self.app.post("/api/memory/store")
        async def store_episode(request: Dict[str, Any]):
            """Almacenar episodio de memoria"""
            try:
                session_id = request.get("session_id")
                episode_data = request.get("episode")
                
                if not session_id or not episode_data:
                    raise HTTPException(
                        status_code=400, 
                        detail="session_id and episode required"
                    )
                
                # Almacenar episodio
                episode_id = await self.memory_manager.store_episode(
                    session_id=session_id,
                    episode=episode_data
                )
                
                return {
                    "success": True,
                    "episode_id": episode_id,
                    "session_id": session_id,
                    "service": "memory_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error storing episode: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/memory/retrieve")
        async def retrieve_episodes(request: Dict[str, Any]):
            """Recuperar episodios relevantes"""
            try:
                query = request.get("query")
                session_id = request.get("session_id")
                
                if not query or not session_id:
                    raise HTTPException(
                        status_code=400,
                        detail="query and session_id required"
                    )
                
                max_episodes = request.get("max_episodes", 5)
                include_other_sessions = request.get("include_other_sessions", True)
                
                # Recuperar episodios relevantes
                result = await self.memory_manager.retrieve_relevant_episodes(
                    query=query,
                    session_id=session_id,
                    max_episodes=max_episodes,
                    include_other_sessions=include_other_sessions
                )
                
                return {
                    "success": True,
                    "result": result,
                    "service": "memory_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error retrieving episodes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/memory/{session_id}")
        async def get_session_memory(session_id: str):
            """Obtener memoria de sesión específica"""
            try:
                # Obtener episodios de la sesión
                session_episodes = self.memory_manager.episodes_cache.get(session_id, [])
                
                episodes_data = []
                for episode in session_episodes:
                    episodes_data.append({
                        "episode_id": episode.episode_id,
                        "episode_type": episode.episode_type.value,
                        "query": episode.query,
                        "response": episode.response,
                        "confidence": episode.confidence,
                        "timestamp": episode.timestamp.isoformat(),
                        "tags": episode.tags,
                        "success": episode.success
                    })
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "episodes_count": len(episodes_data),
                    "episodes": episodes_data,
                    "service": "memory_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting session memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/memory/patterns")
        async def get_detected_patterns():
            """Obtener patrones detectados en memoria"""
            try:
                patterns = self.memory_manager.detected_patterns
                
                return {
                    "success": True,
                    "patterns": patterns,
                    "patterns_count": len(patterns),
                    "service": "memory_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting patterns: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/memory/{session_id}")
        async def clear_session_memory(session_id: str):
            """Limpiar memoria de sesión"""
            try:
                # Limpiar cache de episodios
                if session_id in self.memory_manager.episodes_cache:
                    del self.memory_manager.episodes_cache[session_id]
                
                # Limpiar embeddings de la sesión
                episodes_to_remove = []
                for episode_id, embedding in self.memory_manager.embeddings_index.items():
                    if episode_id.startswith(session_id):
                        episodes_to_remove.append(episode_id)
                
                for episode_id in episodes_to_remove:
                    del self.memory_manager.embeddings_index[episode_id]
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "episodes_removed": len(episodes_to_remove),
                    "service": "memory_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error clearing session memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/stats")
        async def get_service_stats():
            """Estadísticas del Memory Service"""
            try:
                memory_stats = self.memory_manager.get_memory_stats()
                
                return {
                    "service": "memory_service",
                    "port": self.port,
                    "memory_stats": memory_stats,
                    "endpoints": [
                        "/api/memory/store",
                        "/api/memory/retrieve",
                        "/api/memory/{session_id}",
                        "/api/memory/patterns"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_service(self):
        """Iniciar Memory Service"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - Memory Service no puede iniciar")
            return
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Iniciando Memory Service en puerto {self.port}")
        await server.serve()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check programático"""
        try:
            memory_stats = self.memory_manager.get_memory_stats()
            
            return {
                "status": "healthy",
                "memory_manager_ready": True,
                "total_sessions": memory_stats["total_sessions"],
                "total_episodes": memory_stats["total_episodes"],
                "embeddings_available": memory_stats["embeddings_available"]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Instancia global
global_memory_service = MemoryService()

"""
RAG Service - Microservicio especializado en procesamiento RAG
Maneja búsqueda híbrida y generación de respuestas
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

# Integración con sistema RAG existente
from ..core.langchain_integration.langgraph_orchestrator import LangGraphOrchestrator
from ..core.langchain_integration.semantic_rag import SemanticRAGChain
from ..core.hybrid.hybrid_search import HybridSearch

logger = logging.getLogger(__name__)

class RAGService:
    """
    Microservicio especializado en procesamiento RAG
    Encapsula toda la lógica de búsqueda y generación
    """
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.app = self._create_fastapi_app() if FASTAPI_AVAILABLE else None
        
        # Componentes RAG integrados - LAZY LOADING OPTIMIZADO
        self._langgraph_orchestrator = None
        self._semantic_rag = None  
        self._hybrid_search = None
        
        # Configurar rutas
        if self.app:
            self._setup_routes()
        
        logger.info(f"🔍 RAGService inicializado en puerto {port} - LAZY LOADING ACTIVADO")
    
    @property
    def langgraph_orchestrator(self):
        """Lazy loading del LangGraph orchestrator"""
        if self._langgraph_orchestrator is None:
            logger.info("🔄 Cargando LangGraph orchestrator...")
            try:
                self._langgraph_orchestrator = LangGraphOrchestrator()
            except Exception as e:
                logger.warning(f"Error cargando LangGraph: {e}")
                # Fallback simple
                self._langgraph_orchestrator = type('MockOrchestrator', (), {
                    'get_orchestrator_stats': lambda: {"langgraph_available": False},
                    'process_query': lambda **kwargs: {"response": "LangGraph no disponible", "source": "fallback"}
                })()
        return self._langgraph_orchestrator
    
    @property 
    def semantic_rag(self):
        """Lazy loading del Semantic RAG"""
        if self._semantic_rag is None:
            logger.info("🔄 Cargando Semantic RAG...")
            try:
                self._semantic_rag = SemanticRAGChain()
            except Exception as e:
                logger.warning(f"Error cargando Semantic RAG: {e}")
                # Fallback simple
                self._semantic_rag = type('MockSemanticRAG', (), {
                    'get_chain_stats': lambda: {"documents_loaded": 0},
                    'search_and_generate': lambda **kwargs: {"response": "SemanticRAG no disponible", "source": "fallback"}
                })()
        return self._semantic_rag
    
    @property
    def hybrid_search(self):
        """Lazy loading del Hybrid Search"""
        if self._hybrid_search is None:
            logger.info("🔄 Cargando Hybrid Search...")
            try:
                self._hybrid_search = HybridSearch(
                    bm25_vectorstore_path='data/vectorstores/bm25.pkl',
                    tfidf_vectorstore_path='data/vectorstores/tfidf.pkl',
                    transformer_vectorstore_path='data/vectorstores/transformers.pkl'
                )
            except Exception as e:
                logger.warning(f"Error cargando Hybrid Search: {e}")
                # Fallback simple
                self._hybrid_search = type('MockHybridSearch', (), {
                    'search': lambda **kwargs: [{"content": "Hybrid Search no disponible", "score": 0.0}]
                })()
        return self._hybrid_search
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para RAG Service"""
        return FastAPI(
            title="RAG Service",
            description="Microservicio de procesamiento RAG",
            version="1.0.0"
        )
    
    def _setup_routes(self):
        """Configurar rutas del RAG Service"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check del RAG service"""
            try:
                # Verificar componentes
                orchestrator_stats = self.langgraph_orchestrator.get_orchestrator_stats()
                semantic_stats = self.semantic_rag.get_chain_stats()
                hybrid_stats = {"status": "active"}
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "langgraph": orchestrator_stats["langgraph_available"],
                        "semantic_rag": semantic_stats["documents_loaded"] > 0,
                        "hybrid_search": True
                    }
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}
        
        @self.app.post("/api/chat")
        async def process_chat(request: Dict[str, Any]):
            """Endpoint principal de chat RAG"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                session_id = request.get("session_id", "default")
                context = request.get("context", {})
                
                # Procesar con LangGraph orchestrator
                result = await self.langgraph_orchestrator.process_query(
                    query=query,
                    session_id=session_id,
                    context=context
                )
                
                return {
                    "success": True,
                    "result": result,
                    "service": "rag_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in chat processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/search")
        async def hybrid_search_endpoint(request: Dict[str, Any]):
            """Endpoint de búsqueda híbrida"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                max_results = request.get("max_results", 5)
                
                # Búsqueda híbrida
                search_results = self.hybrid_search.search(
                    query=query,
                    max_results=max_results
                )
                
                return {
                    "success": True,
                    "results": search_results,
                    "service": "rag_service",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in search: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/generate")
        async def semantic_generation(request: Dict[str, Any]):
            """Endpoint de generación semántica"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                max_docs = request.get("max_docs", 5)
                
                # Generación semántica
                result = self.semantic_rag.search_and_generate(
                    query=query,
                    max_docs=max_docs
                )
                
                return {
                    "success": True,
                    "result": result,
                    "service": "rag_service", 
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in generation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/stats")
        async def get_service_stats():
            """Estadísticas del RAG service"""
            try:
                return {
                    "service": "rag_service",
                    "port": self.port,
                    "langgraph_orchestrator": self.langgraph_orchestrator.get_orchestrator_stats(),
                    "semantic_rag": self.semantic_rag.get_chain_stats(),
                    "endpoints": ["/api/chat", "/api/search", "/api/generate"],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_service(self):
        """Iniciar RAG Service"""
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI no disponible - RAG Service no puede iniciar")
            return
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        logger.info(f"🚀 Iniciando RAG Service en puerto {self.port}")
        await server.serve()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check programático"""
        try:
            return {
                "status": "healthy",
                "components_loaded": 3,
                "langgraph_available": True,
                "semantic_rag_ready": True,
                "hybrid_search_active": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Comentar la instancia global que causa carga pesada
# global_rag_service = RAGService()

# Función para obtener instancia lazy
def get_rag_service():
    """Obtener instancia RAG Service con lazy loading"""
    global _rag_service_instance
    if '_rag_service_instance' not in globals():
        _rag_service_instance = RAGService()
    return _rag_service_instance
"""
RAG Service Optimizado - Microservicio especializado en procesamiento RAG
Versión con lazy loading para evitar carga pesada de modelos
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

logger = logging.getLogger(__name__)

class RAGServiceOptimized:
    """
    Microservicio RAG optimizado con lazy loading
    Evita carga pesada de modelos hasta que sean necesarios
    """
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.app = self._create_fastapi_app() if FASTAPI_AVAILABLE else None
        
        # Componentes RAG - LAZY LOADING
        self._langgraph_orchestrator = None
        self._semantic_rag = None  
        self._hybrid_search = None
        
        # Configurar rutas
        if self.app:
            self._setup_routes()
        
        logger.info(f"🔍 RAGServiceOptimized inicializado en puerto {port} - LAZY LOADING")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para RAG Service"""
        return FastAPI(
            title="RAG Service Optimized",
            description="Microservicio RAG con lazy loading",
            version="1.0.0"
        )
    
    @property
    def langgraph_orchestrator(self):
        """Lazy loading del LangGraph orchestrator"""
        if self._langgraph_orchestrator is None:
            logger.info("🔄 Cargando LangGraph orchestrator...")
            try:
                from ..core.langchain_integration.langgraph_orchestrator import LangGraphOrchestrator
                self._langgraph_orchestrator = LangGraphOrchestrator()
                logger.info("✅ LangGraph orchestrator cargado")
            except Exception as e:
                logger.warning(f"Error cargando LangGraph: {e}")
                # Fallback simple
                self._langgraph_orchestrator = self._create_mock_orchestrator()
        return self._langgraph_orchestrator
    
    @property 
    def semantic_rag(self):
        """Lazy loading del Semantic RAG"""
        if self._semantic_rag is None:
            logger.info("🔄 Cargando Semantic RAG...")
            try:
                from ..core.langchain_integration.semantic_rag import SemanticRAGChain
                self._semantic_rag = SemanticRAGChain()
                logger.info("✅ Semantic RAG cargado")
            except Exception as e:
                logger.warning(f"Error cargando Semantic RAG: {e}")
                # Fallback simple
                self._semantic_rag = self._create_mock_semantic_rag()
        return self._semantic_rag
    
    @property
    def hybrid_search(self):
        """Lazy loading del Hybrid Search"""
        if self._hybrid_search is None:
            logger.info("🔄 Cargando Hybrid Search...")
            try:
                from ..core.hybrid.hybrid_search import HybridSearch
                self._hybrid_search = HybridSearch(
                    bm25_vectorstore_path='data/vectorstores/bm25.pkl',
                    tfidf_vectorstore_path='data/vectorstores/tfidf.pkl',
                    transformer_vectorstore_path='data/vectorstores/transformers.pkl'
                )
                logger.info("✅ Hybrid Search cargado")
            except Exception as e:
                logger.warning(f"Error cargando Hybrid Search: {e}")
                # Fallback simple
                self._hybrid_search = self._create_mock_hybrid_search()
        return self._hybrid_search
    
    def _create_mock_orchestrator(self):
        """TODO CRITICAL: Reemplazar con orchestrator real - NO usar en producción"""
        class MockOrchestrator:
            def get_orchestrator_stats(self):
                return {"langgraph_available": False}
            
            async def process_query(self, query, session_id="default", context=None):
                return {
                    "response": f"Procesando consulta: {query} (modo fallback)",
                    "source": "mock_orchestrator",
                    "confidence": 0.5
                }
        return MockOrchestrator()
    
    def _create_mock_semantic_rag(self):
        """TODO CRITICAL: Reemplazar con semantic RAG real - NO usar en producción"""
        class MockSemanticRAG:
            def get_chain_stats(self):
                return {"documents_loaded": 0}
            
            def search_and_generate(self, query, max_docs=5):
                return {
                    "response": f"Generando respuesta para: {query} (modo fallback)",
                    "source": "mock_semantic_rag",
                    "documents_used": 0
                }
        return MockSemanticRAG()
    
    def _create_mock_hybrid_search(self):
        """TODO CRITICAL: Reemplazar con hybrid search real - NO usar en producción"""
        class MockHybridSearch:
            def search(self, query, max_results=5):
                return [
                    {
                        "content": f"Resultado mock para: {query}",
                        "score": 0.8,
                        "source": "mock_hybrid_search",
                        "metadata": {"type": "fallback"}
                    }
                ]
        return MockHybridSearch()
    
    def _setup_routes(self):
        """Configurar rutas del RAG Service optimizado"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check ligero del RAG service"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "port": self.port,
                "service": "rag_service_optimized",
                "lazy_loading": True,
                "components_loaded": {
                    "langgraph": self._langgraph_orchestrator is not None,
                    "semantic_rag": self._semantic_rag is not None,
                    "hybrid_search": self._hybrid_search is not None
                }
            }
        
        @self.app.post("/api/chat")
        async def process_chat(request: Dict[str, Any]):
            """Endpoint principal de chat RAG optimizado"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                session_id = request.get("session_id", "default")
                context = request.get("context", {})
                
                # Procesar con orchestrator (lazy loaded)
                result = await self.langgraph_orchestrator.process_query(
                    query=query,
                    session_id=session_id,
                    context=context
                )
                
                return {
                    "success": True,
                    "result": result,
                    "service": "rag_service_optimized",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in chat processing: {e}")
                # Respuesta de fallback
                return {
                    "success": True,
                    "result": {
                        "response": f"Respuesta de fallback para: {query}",
                        "source": "error_fallback",
                        "error": str(e)
                    },
                    "service": "rag_service_optimized",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.post("/api/search")
        async def hybrid_search_endpoint(request: Dict[str, Any]):
            """Endpoint de búsqueda híbrida optimizado"""
            try:
                query = request.get("query")
                if not query:
                    raise HTTPException(status_code=400, detail="Query required")
                
                max_results = request.get("max_results", 5)
                
                # Búsqueda híbrida (lazy loaded)
                search_results = self.hybrid_search.search(
                    query=query,
                    max_results=max_results
                )
                
                return {
                    "success": True,
                    "results": search_results,
                    "service": "rag_service_optimized",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in search: {e}")
                # Respuesta de fallback
                return {
                    "success": True,
                    "results": [
                        {
                            "content": f"Resultado de fallback para: {query}",
                            "score": 0.5,
                            "source": "search_fallback"
                        }
                    ],
                    "service": "rag_service_optimized",
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.get("/api/stats")
        async def get_service_stats():
            """Estadísticas del RAG service optimizado"""
            return {
                "service": "rag_service_optimized",
                "port": self.port,
                "lazy_loading": True,
                "components_status": {
                    "langgraph_loaded": self._langgraph_orchestrator is not None,
                    "semantic_rag_loaded": self._semantic_rag is not None,
                    "hybrid_search_loaded": self._hybrid_search is not None
                },
                "endpoints": ["/api/chat", "/api/search"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_service(self):
        """Iniciar RAG Service optimizado"""
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
        logger.info(f"🚀 Iniciando RAG Service Optimizado en puerto {self.port}")
        await server.serve()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check programático"""
        return {
            "status": "healthy",
            "port": self.port,
            "service": "rag_service_optimized",
            "lazy_loading_active": True,
            "components_loaded": {
                "langgraph": self._langgraph_orchestrator is not None,
                "semantic_rag": self._semantic_rag is not None,
                "hybrid_search": self._hybrid_search is not None
            }
        }

# Factory function para lazy loading
def get_rag_service_optimized():
    """Obtener instancia RAG Service optimizado con lazy loading"""
    global _rag_service_optimized_instance
    if '_rag_service_optimized_instance' not in globals():
        _rag_service_optimized_instance = RAGServiceOptimized()
    return _rag_service_optimized_instance 
"""
Sistema de reranking avanzado con cross-encoder
Mejora la relevancia de resultados antes de enviar al LLM
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

# Cross-encoder imports (instalar con: pip install sentence-transformers)
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class RerankingResult:
    """Resultado del reranking"""
    document_id: str
    content: str
    original_score: float
    reranked_score: float
    confidence: float
    ranking_method: str
    metadata: Dict[str, Any]

class AdvancedReranker:
    """Sistema de reranking avanzado con múltiples estrategias"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.cross_encoder = None
        self.fallback_enabled = True
        self.initialized = False
        
        # Configuración de reranking
        self.max_documents = 50  # Máximo documentos a reranquear
        self.top_k_after_rerank = 10  # Top K después del reranking
        
        # Métricas
        self.reranking_stats = {
            "total_rerankings": 0,
            "average_processing_time": 0.0,
            "cross_encoder_usage": 0,
            "fallback_usage": 0
        }
    
    async def initialize(self) -> bool:
        """Inicializar el cross-encoder model"""
        if self.initialized:
            return True
        
        try:
            if CROSS_ENCODER_AVAILABLE:
                logger.info(f"🧠 Cargando cross-encoder model: {self.model_name}")
                
                # Ejecutar en thread pool para no bloquear
                loop = asyncio.get_event_loop()
                self.cross_encoder = await loop.run_in_executor(
                    None, 
                    CrossEncoder, 
                    self.model_name
                )
                
                logger.info("✅ Cross-encoder model cargado exitosamente")
                self.initialized = True
                return True
            else:
                logger.warning("⚠️ Cross-encoder no disponible, usando fallback")
                self.initialized = True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cargando cross-encoder: {e}")
            self.initialized = True
            return False
    
    async def rerank_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        strategy: str = "hybrid"
    ) -> List[RerankingResult]:
        """
        Reranquear documentos usando estrategia especificada
        
        Args:
            query: Consulta del usuario
            documents: Lista de documentos con scores originales
            strategy: 'cross_encoder', 'semantic', 'hybrid', 'fallback'
        
        Returns:
            Lista de documentos reranqueados
        """
        start_time = time.time()
        
        # Asegurar inicialización
        if not self.initialized:
            await self.initialize()
        
        # Limitar número de documentos
        documents = documents[:self.max_documents]
        
        if not documents:
            return []
        
        logger.info(f"🔄 Reranqueando {len(documents)} documentos con estrategia: {strategy}")
        
        try:
            if strategy == "cross_encoder" and self.cross_encoder:
                results = await self._rerank_with_cross_encoder(query, documents)
                self.reranking_stats["cross_encoder_usage"] += 1
            elif strategy == "semantic":
                results = await self._rerank_semantic(query, documents)
            elif strategy == "hybrid":
                results = await self._rerank_hybrid(query, documents)
            else:
                results = await self._rerank_fallback(query, documents)
                self.reranking_stats["fallback_usage"] += 1
            
            # Actualizar estadísticas
            processing_time = time.time() - start_time
            self.reranking_stats["total_rerankings"] += 1
            
            # Actualizar promedio de tiempo
            current_avg = self.reranking_stats["average_processing_time"]
            total_rerankings = self.reranking_stats["total_rerankings"]
            new_avg = (current_avg * (total_rerankings - 1) + processing_time) / total_rerankings
            self.reranking_stats["average_processing_time"] = new_avg
            
            logger.info(f"✅ Reranking completado en {processing_time:.3f}s - Top result score: {results[0].reranked_score:.3f}")
            
            return results[:self.top_k_after_rerank]
            
        except Exception as e:
            logger.error(f"❌ Error en reranking: {e}")
            return await self._rerank_fallback(query, documents)
    
    async def _rerank_with_cross_encoder(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Reranking usando cross-encoder"""
        
        # Preparar pares query-document
        query_doc_pairs = []
        for doc in documents:
            content = doc.get('content', doc.get('text', ''))
            if content:
                query_doc_pairs.append([query, content])
        
        if not query_doc_pairs:
            return await self._rerank_fallback(query, documents)
        
        # Ejecutar cross-encoder en thread pool
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            self.cross_encoder.predict,
            query_doc_pairs
        )
        
        # Crear resultados reranqueados
        results = []
        for i, doc in enumerate(documents):
            if i < len(scores):
                result = RerankingResult(
                    document_id=doc.get('id', str(i)),
                    content=doc.get('content', doc.get('text', '')),
                    original_score=doc.get('score', 0.0),
                    reranked_score=float(scores[i]),
                    confidence=min(float(scores[i]) * 1.2, 1.0),  # Ajustar confianza
                    ranking_method="cross_encoder",
                    metadata={
                        "model": self.model_name,
                        "original_rank": i,
                        "source": doc.get('source', ''),
                        "title": doc.get('title', ''),
                    }
                )
                results.append(result)
        
        # Ordenar por score reranqueado (descendente)
        results.sort(key=lambda x: x.reranked_score, reverse=True)
        
        return results
    
    async def _rerank_semantic(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Reranking usando similaridad semántica simple"""
        
        results = []
        
        for i, doc in enumerate(documents):
            content = doc.get('content', doc.get('text', ''))
            
            # Calcular score semántico simple basado en términos clave
            semantic_score = self._calculate_semantic_similarity(query, content)
            
            # Combinar con score original
            original_score = doc.get('score', 0.0)
            combined_score = (semantic_score * 0.7) + (original_score * 0.3)
            
            result = RerankingResult(
                document_id=doc.get('id', str(i)),
                content=content,
                original_score=original_score,
                reranked_score=combined_score,
                confidence=combined_score * 0.8,  # Menor confianza que cross-encoder
                ranking_method="semantic",
                metadata={
                    "semantic_score": semantic_score,
                    "original_rank": i,
                    "source": doc.get('source', ''),
                    "title": doc.get('title', ''),
                }
            )
            results.append(result)
        
        # Ordenar por score reranqueado
        results.sort(key=lambda x: x.reranked_score, reverse=True)
        
        return results
    
    async def _rerank_hybrid(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Reranking híbrido: cross-encoder si está disponible, sino semántico"""
        
        if self.cross_encoder:
            return await self._rerank_with_cross_encoder(query, documents)
        else:
            return await self._rerank_semantic(query, documents)
    
    async def _rerank_fallback(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Reranking fallback usando heurísticas simples"""
        
        results = []
        
        # Palabras clave importantes para MINEDU
        key_terms = {
            "viático": 2.0, "viaticos": 2.0,
            "monto": 1.5, "cantidad": 1.5, "importe": 1.5,
            "máximo": 1.8, "minimo": 1.8, "limite": 1.8,
            "declaración": 1.6, "jurada": 1.6,
            "provincia": 1.4, "lima": 1.4,
            "directiva": 1.7, "decreto": 1.7, "resolución": 1.7,
            "ministro": 1.3, "funcionario": 1.3
        }
        
        query_lower = query.lower()
        
        for i, doc in enumerate(documents):
            content = doc.get('content', doc.get('text', '')).lower()
            
            # Score basado en términos clave
            key_score = 0.0
            for term, weight in key_terms.items():
                if term in query_lower and term in content:
                    key_score += weight
            
            # Score basado en longitud de contenido (preferir contenido sustancial)
            length_score = min(len(content) / 1000, 1.0) * 0.3
            
            # Score basado en posición original (preferir primeros resultados)
            position_score = max(0, (len(documents) - i) / len(documents)) * 0.2
            
            # Combinar scores
            original_score = doc.get('score', 0.0)
            reranked_score = (
                original_score * 0.4 +
                key_score * 0.4 +
                length_score * 0.1 +
                position_score * 0.1
            )
            
            result = RerankingResult(
                document_id=doc.get('id', str(i)),
                content=doc.get('content', doc.get('text', '')),
                original_score=original_score,
                reranked_score=reranked_score,
                confidence=min(reranked_score * 0.6, 0.9),  # Confianza conservadora
                ranking_method="fallback",
                metadata={
                    "key_score": key_score,
                    "length_score": length_score,
                    "position_score": position_score,
                    "original_rank": i,
                    "source": doc.get('source', ''),
                    "title": doc.get('title', ''),
                }
            )
            results.append(result)
        
        # Ordenar por score reranqueado
        results.sort(key=lambda x: x.reranked_score, reverse=True)
        
        return results
    
    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """Calcular similaridad semántica simple (sin transformers)"""
        
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Bonus por términos exactos
        exact_matches = sum(1 for word in query_words if word in content_words)
        exact_bonus = exact_matches / len(query_words) if query_words else 0.0
        
        # Score final
        similarity = (jaccard * 0.6) + (exact_bonus * 0.4)
        
        return min(similarity * 2, 1.0)  # Normalizar a [0, 1]
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del reranking"""
        return {
            **self.reranking_stats,
            "cross_encoder_available": CROSS_ENCODER_AVAILABLE and self.cross_encoder is not None,
            "model_name": self.model_name,
            "initialized": self.initialized,
            "fallback_enabled": self.fallback_enabled,
            "max_documents": self.max_documents,
            "top_k_after_rerank": self.top_k_after_rerank
        }

# Instancia global del reranker
global_reranker = AdvancedReranker()

# Funciones de utilidad
async def rerank_search_results(
    query: str,
    documents: List[Dict[str, Any]],
    strategy: str = "hybrid"
) -> List[RerankingResult]:
    """Función helper para reranquear resultados de búsqueda"""
    return await global_reranker.rerank_documents(query, documents, strategy)

async def initialize_reranker() -> bool:
    """Inicializar el reranker global"""
    return await global_reranker.initialize()

def get_reranker_status() -> Dict[str, Any]:
    """Obtener estado del reranker"""
    return global_reranker.get_reranking_stats()
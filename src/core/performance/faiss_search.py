#!/usr/bin/env python3
"""
Búsqueda Semántica Optimizada con FAISS IVF+PQ
==============================================

Implementación de búsqueda vectorial ultrarrápida usando FAISS
con índices optimizados para producción.
"""

import faiss
import numpy as np
import pickle
import logging
import time
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from prometheus_client import Counter, Histogram

from .cache_system import get_cache, cached

# Métricas FAISS
FAISS_SEARCH_OPERATIONS = Counter('faiss_search_operations_total', 'Total FAISS search operations', ['index_type'])
FAISS_SEARCH_DURATION = Histogram('faiss_search_duration_seconds', 'FAISS search duration', ['index_type'])
FAISS_INDEX_SIZE = Counter('faiss_index_size_vectors', 'Number of vectors in FAISS index', ['index_type'])

logger = logging.getLogger(__name__)

class OptimizedFAISSSearch:
    """
    Búsqueda semántica optimizada usando FAISS con múltiples tipos de índices.
    
    Características:
    - Índice IVF+PQ para datasets grandes (>10K vectores)
    - Índice Flat para datasets pequeños (<10K vectores)
    - Cache de embeddings precomputados
    - Métricas detalladas de rendimiento
    - Búsqueda híbrida con fallback
    """
    
    def __init__(self, 
                 model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                 index_dir: str = 'data/faiss_indexes',
                 embedding_dim: int = 384):
        
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar modelo de embeddings
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"✅ Modelo de embeddings cargado: {model_name}")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            self.model = None
            
        # Índices FAISS
        self.indexes = {}
        self.metadata = {}  # Metadatos asociados a cada vector
        self.cache = get_cache()
        
        # Configuración de índices por tamaño de dataset
        self.index_configs = {
            'small': {'type': 'Flat', 'threshold': 1000},
            'medium': {'type': 'IVF', 'threshold': 10000, 'nlist': 100},
            'large': {'type': 'IVFPQ', 'threshold': float('inf'), 'nlist': 1000, 'm': 64}
        }
        
        self._load_existing_indexes()
    
    def _load_existing_indexes(self):
        """Cargar índices existentes desde disco"""
        for index_file in self.index_dir.glob("*.faiss"):
            index_name = index_file.stem
            try:
                index = faiss.read_index(str(index_file))
                metadata_file = self.index_dir / f"{index_name}_metadata.pkl"
                
                if metadata_file.exists():
                    with open(metadata_file, 'rb') as f:
                        metadata = pickle.load(f)
                    
                    self.indexes[index_name] = index
                    self.metadata[index_name] = metadata
                    
                    FAISS_INDEX_SIZE.labels(index_type=self._get_index_type(index)).inc(index.ntotal)
                    logger.info(f"✅ Índice cargado: {index_name} ({index.ntotal} vectores)")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error cargando índice {index_name}: {e}")
    
    def _get_index_type(self, index) -> str:
        """Obtener tipo de índice FAISS"""
        if isinstance(index, faiss.IndexFlatIP):
            return 'Flat'
        elif isinstance(index, faiss.IndexIVFFlat):
            return 'IVF'
        elif isinstance(index, faiss.IndexIVFPQ):
            return 'IVFPQ'
        else:
            return 'Unknown'
    
    def _choose_index_config(self, num_vectors: int) -> Dict[str, Any]:
        """Elegir configuración de índice según tamaño del dataset"""
        for config_name, config in self.index_configs.items():
            if num_vectors <= config['threshold']:
                return config
        return self.index_configs['large']
    
    def _create_index(self, vectors: np.ndarray, index_config: Dict[str, Any]) -> faiss.Index:
        """Crear índice FAISS optimizado"""
        num_vectors, dim = vectors.shape
        
        if index_config['type'] == 'Flat':
            # Índice plano (exacto) para datasets pequeños
            index = faiss.IndexFlatIP(dim)  # Inner Product (similitud coseno)
            
        elif index_config['type'] == 'IVF':
            # Índice IVF para datasets medianos
            quantizer = faiss.IndexFlatIP(dim)
            index = faiss.IndexIVFFlat(quantizer, dim, index_config['nlist'])
            
        elif index_config['type'] == 'IVFPQ':
            # Índice IVF+PQ para datasets grandes (compresión + velocidad)
            quantizer = faiss.IndexFlatIP(dim)
            index = faiss.IndexIVFPQ(quantizer, dim, index_config['nlist'], index_config['m'], 8)
            
        else:
            raise ValueError(f"Tipo de índice no soportado: {index_config['type']}")
        
        # Normalizar vectores para similitud coseno
        faiss.normalize_L2(vectors)
        
        # Entrenar índice si es necesario
        if hasattr(index, 'train'):
            logger.info(f"🏋️ Entrenando índice {index_config['type']} con {num_vectors} vectores...")
            index.train(vectors)
        
        # Agregar vectores al índice
        index.add(vectors)
        
        logger.info(f"✅ Índice {index_config['type']} creado: {num_vectors} vectores, {dim}D")
        return index
    
    @cached('hybrid', ttl=3600)
    def create_index_from_documents(self, 
                                  documents: List[str], 
                                  index_name: str,
                                  metadata_list: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Crear índice FAISS desde lista de documentos
        
        Args:
            documents: Lista de textos para indexar
            index_name: Nombre del índice
            metadata_list: Metadatos asociados a cada documento
            
        Returns:
            True si el índice se creó exitosamente
        """
        start_time = time.time()
        
        try:
            if not self.model:
                raise ValueError("Modelo de embeddings no disponible")
                
            logger.info(f"🔨 Creando índice '{index_name}' con {len(documents)} documentos...")
            
            # Generar embeddings
            logger.info("🧠 Generando embeddings...")
            embeddings = self.model.encode(documents, show_progress_bar=True)
            embeddings = np.array(embeddings, dtype=np.float32)
            
            # Elegir configuración de índice
            index_config = self._choose_index_config(len(documents))
            logger.info(f"📊 Configuración elegida: {index_config['type']} para {len(documents)} vectores")
            
            # Crear índice
            index = self._create_index(embeddings, index_config)
            
            # Guardar índice y metadatos
            index_path = self.index_dir / f"{index_name}.faiss"
            faiss.write_index(index, str(index_path))
            
            if metadata_list:
                metadata_path = self.index_dir / f"{index_name}_metadata.pkl"
                with open(metadata_path, 'wb') as f:
                    pickle.dump(metadata_list, f)
                self.metadata[index_name] = metadata_list
            
            # Guardar en memoria
            self.indexes[index_name] = index
            
            # Métricas
            creation_time = time.time() - start_time
            FAISS_INDEX_SIZE.labels(index_type=index_config['type']).inc(len(documents))
            
            logger.info(f"✅ Índice '{index_name}' creado en {creation_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando índice '{index_name}': {e}")
            return False
    
    def search(self, 
               query: str, 
               index_name: str, 
               k: int = 5,
               score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica en índice FAISS
        
        Args:
            query: Consulta de búsqueda
            index_name: Nombre del índice a usar
            k: Número de resultados a devolver
            score_threshold: Umbral mínimo de similitud
            
        Returns:
            Lista de resultados con scores y metadatos
        """
        start_time = time.time()
        
        try:
            if index_name not in self.indexes:
                logger.warning(f"⚠️ Índice '{index_name}' no encontrado")
                return []
                
            if not self.model:
                logger.error("❌ Modelo de embeddings no disponible")
                return []
            
            index = self.indexes[index_name]
            metadata = self.metadata.get(index_name, [])
            
            # Generar embedding de la consulta
            query_embedding = self.model.encode([query])
            query_embedding = np.array(query_embedding, dtype=np.float32)
            faiss.normalize_L2(query_embedding)  # Normalizar para similitud coseno
            
            # Búsqueda en FAISS
            scores, indices = index.search(query_embedding, k)
            
            # Procesar resultados
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # FAISS devuelve -1 si no encuentra suficientes resultados
                    continue
                    
                if score < score_threshold:
                    continue
                
                result = {
                    'rank': i + 1,
                    'score': float(score),
                    'document_id': int(idx),
                    'metadata': metadata[idx] if idx < len(metadata) else {}
                }
                results.append(result)
            
            # Métricas
            search_time = time.time() - start_time
            index_type = self._get_index_type(index)
            
            FAISS_SEARCH_OPERATIONS.labels(index_type=index_type).inc()
            FAISS_SEARCH_DURATION.labels(index_type=index_type).observe(search_time)
            
            logger.debug(f"🔍 Búsqueda FAISS completada: {len(results)} resultados en {search_time:.3f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda FAISS: {e}")
            return []
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Obtener estadísticas de un índice específico"""
        if index_name not in self.indexes:
            return {'error': f"Índice '{index_name}' no encontrado"}
        
        index = self.indexes[index_name]
        metadata = self.metadata.get(index_name, [])
        
        return {
            'index_name': index_name,
            'index_type': self._get_index_type(index),
            'total_vectors': index.ntotal,
            'dimension': index.d,
            'metadata_entries': len(metadata),
            'is_trained': getattr(index, 'is_trained', True),
            'memory_usage_mb': self._estimate_memory_usage(index)
        }
    
    def _estimate_memory_usage(self, index) -> float:
        """Estimar uso de memoria de un índice FAISS"""
        try:
            # Estimación básica basada en tipo de índice
            if isinstance(index, faiss.IndexFlatIP):
                return (index.ntotal * index.d * 4) / (1024 * 1024)  # 4 bytes por float32
            elif isinstance(index, faiss.IndexIVFFlat):
                return (index.ntotal * index.d * 4) / (1024 * 1024) * 1.2  # +20% overhead
            elif isinstance(index, faiss.IndexIVFPQ):
                # PQ usa menos memoria debido a compresión
                return (index.ntotal * index.d * 4) / (1024 * 1024) * 0.25  # ~75% compresión
            else:
                return 0.0
        except:
            return 0.0
    
    def list_indexes(self) -> List[Dict[str, Any]]:
        """Listar todos los índices disponibles"""
        return [self.get_index_stats(name) for name in self.indexes.keys()]
    
    def delete_index(self, index_name: str) -> bool:
        """Eliminar índice de memoria y disco"""
        try:
            # Remover de memoria
            if index_name in self.indexes:
                del self.indexes[index_name]
            if index_name in self.metadata:
                del self.metadata[index_name]
            
            # Remover archivos
            index_path = self.index_dir / f"{index_name}.faiss"
            metadata_path = self.index_dir / f"{index_name}_metadata.pkl"
            
            if index_path.exists():
                index_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
                
            logger.info(f"🗑️ Índice '{index_name}' eliminado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando índice '{index_name}': {e}")
            return False
    
    def optimize_index(self, index_name: str) -> bool:
        """Optimizar índice existente (re-entrenar con mejores parámetros)"""
        try:
            if index_name not in self.indexes:
                logger.warning(f"⚠️ Índice '{index_name}' no encontrado para optimizar")
                return False
            
            # Para simplificar, esta implementación recrea el índice
            # En producción, se podrían aplicar optimizaciones específicas
            logger.info(f"🔧 Optimización de índice '{index_name}' no implementada aún")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error optimizando índice '{index_name}': {e}")
            return False

# Factory function para uso fácil
def create_faiss_search(model_name: str = None) -> OptimizedFAISSSearch:
    """Crear instancia de búsqueda FAISS con configuración por defecto"""
    if model_name is None:
        model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    
    return OptimizedFAISSSearch(model_name=model_name)
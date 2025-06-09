#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline de Búsqueda Híbrido Avanzado.
Orquesta el flujo completo de búsqueda combinando múltiples sistemas:
BM25, E5-Large Dense Retrieval, Hybrid Fusion y Neural Re-ranking.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

# Importar componentes del sistema
from src.ai.retrieval.retriever_dense_e5 import DenseRetrieverE5
from src.ai.retrieval.hybrid_fusion import HybridFusion
from src.ai.reranking.cross_encoder import NeuralReranker
from src.ai.vectorstore.chroma_manager import ChromaManager

# Importar sistema BM25 existente
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ai.search_vectorstore_bm25 import BM25Search

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SearchPipeline')

class SearchPipeline:
    """
    Pipeline de búsqueda híbrido avanzado que integra múltiples sistemas.
    
    Combina lo mejor de cada enfoque:
    - BM25: Rápido y preciso para coincidencias léxicas
    - E5-Large: Comprensión semántica avanzada
    - Hybrid Fusion: Combinación inteligente de resultados
    - Neural Re-ranking: Mejora de relevancia con CrossEncoder
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        load_all: bool = True
    ):
        """
        Inicializa el pipeline de búsqueda híbrido.
        
        Args:
            config: Configuración del pipeline
            load_all: Si cargar todos los componentes al inicializar
        """
        # Configuración por defecto
        self.default_config = {
            "bm25": {
                "enabled": True,
                "vectorstore_path": "data/vectorstores/bm25_index.pkl",
                "top_k": 10
            },
            "dense_retrieval": {
                "enabled": True,
                "model_name": "intfloat/multilingual-e5-large",
                "collection_name": "minedu_documents",
                "persist_directory": "data/vectorstores/chroma",
                "top_k": 10
            },
            "hybrid_fusion": {
                "enabled": True,
                "weights": {"bm25": 0.4, "dense": 0.6},
                "rrf_k": 60,
                "deduplicate": True,
                "top_k": 10
            },
            "reranking": {
                "enabled": True,
                "model_name": "cross-encoder/ms-marco-MiniLM-L-12-v2",
                "top_k": 5,
                "score_threshold": 0.1
            }
        }
        
        # Usar configuración proporcionada o la por defecto
        self.config = config if config else self.default_config
        
        # Componentes del pipeline
        self.bm25_search = None
        self.dense_retriever = None
        self.chroma_manager = None
        self.hybrid_fusion = None
        self.reranker = None
        
        # Cargar componentes si se solicita
        if load_all:
            self.load_components()
        
        logger.info("SearchPipeline inicializado")
    
    def load_components(self):
        """
        Carga todos los componentes del pipeline según la configuración.
        """
        start_time = time.time()
        logger.info("Cargando componentes del pipeline...")
        
        # Cargar BM25
        if self.config["bm25"]["enabled"]:
            try:
                logger.info("Cargando BM25...")
                self.bm25_search = BM25Search()
                self.bm25_search.load_vectorstore(self.config["bm25"]["vectorstore_path"])
                logger.info("BM25 cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar BM25: {str(e)}")
                self.config["bm25"]["enabled"] = False
        
        # Cargar Dense Retriever con ChromaDB
        if self.config["dense_retrieval"]["enabled"]:
            try:
                logger.info("Cargando Dense Retriever E5...")
                
                # Cargar ChromaDB Manager
                self.chroma_manager = ChromaManager(
                    collection_name=self.config["dense_retrieval"]["collection_name"],
                    persist_directory=self.config["dense_retrieval"]["persist_directory"],
                    embedding_model=self.config["dense_retrieval"]["model_name"]
                )
                
                # Verificar si hay documentos en la colección
                collection_info = self.chroma_manager.get_collection_info()
                if collection_info["count"] == 0:
                    logger.warning("La colección ChromaDB está vacía. Dense Retrieval podría no funcionar correctamente.")
                
                logger.info("Dense Retriever E5 cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar Dense Retriever E5: {str(e)}")
                self.config["dense_retrieval"]["enabled"] = False
        
        # Configurar Hybrid Fusion
        if self.config["hybrid_fusion"]["enabled"]:
            try:
                logger.info("Configurando Hybrid Fusion...")
                
                # Verificar que al menos un retriever esté habilitado
                if not self.config["bm25"]["enabled"] and not self.config["dense_retrieval"]["enabled"]:
                    logger.error("No hay retrievers habilitados para Hybrid Fusion")
                    self.config["hybrid_fusion"]["enabled"] = False
                else:
                    # Crear diccionario de retrievers
                    retrievers = {}
                    weights = {}
                    
                    if self.config["bm25"]["enabled"]:
                        retrievers["bm25"] = self.bm25_search
                        weights["bm25"] = self.config["hybrid_fusion"]["weights"].get("bm25", 0.5)
                    
                    if self.config["dense_retrieval"]["enabled"]:
                        # Crear wrapper para ChromaManager
                        class DenseRetrieverWrapper:
                            def __init__(self, chroma_manager):
                                self.chroma_manager = chroma_manager
                            
                            def search(self, query, **kwargs):
                                top_k = kwargs.get("top_k", 5)
                                metadata_filter = kwargs.get("metadata_filter", None)
                                return self.chroma_manager.search(query, top_k, metadata_filter)
                        
                        retrievers["dense"] = DenseRetrieverWrapper(self.chroma_manager)
                        weights["dense"] = self.config["hybrid_fusion"]["weights"].get("dense", 0.5)
                    
                    # Crear Hybrid Fusion
                    self.hybrid_fusion = HybridFusion(
                        retrievers=retrievers,
                        weights=weights,
                        rrf_k=self.config["hybrid_fusion"]["rrf_k"],
                        deduplicate=self.config["hybrid_fusion"]["deduplicate"]
                    )
                    
                    logger.info("Hybrid Fusion configurado correctamente")
            except Exception as e:
                logger.error(f"Error al configurar Hybrid Fusion: {str(e)}")
                self.config["hybrid_fusion"]["enabled"] = False
        
        # Cargar Neural Reranker
        if self.config["reranking"]["enabled"]:
            try:
                logger.info("Cargando Neural Reranker...")
                self.reranker = NeuralReranker(
                    model_name=self.config["reranking"]["model_name"]
                )
                logger.info("Neural Reranker cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar Neural Reranker: {str(e)}")
                self.config["reranking"]["enabled"] = False
        
        load_time = time.time() - start_time
        logger.info(f"Componentes cargados en {load_time:.2f} segundos")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        use_reranking: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de búsqueda.
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de resultados a devolver
            metadata_filter: Filtro de metadatos
            use_reranking: Si usar re-ranking (sobreescribe configuración)
            
        Returns:
            Resultados de búsqueda con métricas
        """
        start_time = time.time()
        logger.info(f"Ejecutando pipeline de búsqueda para: '{query}'")
        
        # Determinar si usar re-ranking
        do_reranking = use_reranking if use_reranking is not None else self.config["reranking"]["enabled"]
        
        # Configurar parámetros para cada componente
        retriever_params = {
            "bm25": {
                "top_k": self.config["bm25"]["top_k"]
            },
            "dense": {
                "top_k": self.config["dense_retrieval"]["top_k"],
                "metadata_filter": metadata_filter
            }
        }
        
        # Resultados y tiempos
        results = None
        component_times = {}
        
        # 1. Retrieval (BM25 + Dense) con Hybrid Fusion
        if self.config["hybrid_fusion"]["enabled"]:
            fusion_start = time.time()
            
            # Ejecutar hybrid fusion
            fusion_results = self.hybrid_fusion.search(
                query,
                top_k=self.config["hybrid_fusion"]["top_k"] if do_reranking else top_k,
                retriever_params=retriever_params
            )
            
            # Guardar resultados y tiempo
            results = fusion_results["results"]
            component_times["hybrid_fusion"] = time.time() - fusion_start
            component_times.update(fusion_results["retriever_times"])
            
            logger.info(f"Hybrid Fusion completado en {component_times['hybrid_fusion']:.4f} segundos")
            logger.info(f"Resultados de fusion: {len(results)}")
        
        # Alternativa: usar solo BM25 si hybrid fusion no está disponible
        elif self.config["bm25"]["enabled"]:
            bm25_start = time.time()
            
            # Ejecutar búsqueda BM25
            bm25_results = self.bm25_search.search(
                query,
                top_k=self.config["bm25"]["top_k"] if do_reranking else top_k
            )
            
            # Normalizar formato
            results = []
            for i, result in enumerate(bm25_results.get("results", [])):
                results.append({
                    "rank": i + 1,
                    "id": result.get("id", f"bm25_{i}"),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "source_retriever": "bm25"
                })
            
            component_times["bm25"] = time.time() - bm25_start
            
            logger.info(f"BM25 completado en {component_times['bm25']:.4f} segundos")
            logger.info(f"Resultados de BM25: {len(results)}")
        
        # Alternativa: usar solo Dense Retrieval si hybrid fusion no está disponible
        elif self.config["dense_retrieval"]["enabled"]:
            dense_start = time.time()
            
            # Ejecutar búsqueda con ChromaDB
            dense_results = self.chroma_manager.search(
                query,
                n_results=self.config["dense_retrieval"]["top_k"] if do_reranking else top_k,
                metadata_filter=metadata_filter
            )
            
            # Normalizar formato
            results = []
            for i, result in enumerate(dense_results.get("results", [])):
                results.append({
                    "rank": i + 1,
                    "id": result.get("id", f"dense_{i}"),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "source_retriever": "dense"
                })
            
            component_times["dense"] = time.time() - dense_start
            
            logger.info(f"Dense Retrieval completado en {component_times['dense']:.4f} segundos")
            logger.info(f"Resultados de Dense Retrieval: {len(results)}")
        
        # Si no hay resultados, devolver respuesta vacía
        if not results:
            logger.warning("No se encontraron resultados en ningún sistema")
            return {
                "query": query,
                "time_taken": time.time() - start_time,
                "component_times": component_times,
                "total_found": 0,
                "results": []
            }
        
        # 2. Re-ranking con Neural Reranker
        if do_reranking and self.config["reranking"]["enabled"] and self.reranker:
            rerank_start = time.time()
            
            # Ejecutar re-ranking
            reranked_results = self.reranker.rerank(
                query,
                results,
                top_k=top_k,
                score_threshold=self.config["reranking"]["score_threshold"]
            )
            
            # Actualizar resultados
            results = reranked_results
            component_times["reranking"] = time.time() - rerank_start
            
            logger.info(f"Re-ranking completado en {component_times['reranking']:.4f} segundos")
            logger.info(f"Resultados después de re-ranking: {len(results)}")
        
        # Preparar respuesta final
        response = {
            "query": query,
            "time_taken": time.time() - start_time,
            "component_times": component_times,
            "total_found": len(results),
            "results": results
        }
        
        logger.info(f"Pipeline de búsqueda completado en {response['time_taken']:.4f} segundos")
        logger.info(f"Total resultados finales: {len(results)}")
        
        return response
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae entidades nombradas de un texto.
        
        Args:
            text: Texto para extraer entidades
            
        Returns:
            Diccionario con entidades por tipo
        """
        try:
            # Importar spaCy solo cuando se necesite
            import spacy
            
            # Cargar modelo de spaCy si no está cargado
            if not hasattr(self, "nlp"):
                logger.info("Cargando modelo spaCy para extracción de entidades...")
                self.nlp = spacy.load("es_core_news_md")
            
            # Procesar texto
            doc = self.nlp(text)
            
            # Extraer entidades
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                
                # Evitar duplicados
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
            
            return entities
        
        except Exception as e:
            logger.error(f"Error al extraer entidades: {str(e)}")
            return {}
    
    def print_results(self, results: Dict[str, Any], show_entities: bool = True, max_text_length: int = 200):
        """
        Imprime resultados de búsqueda de forma legible.
        
        Args:
            results: Resultados de búsqueda
            show_entities: Si mostrar entidades extraídas
            max_text_length: Longitud máxima de texto a mostrar
        """
        print(f"\n{'=' * 80}")
        print(f"RESULTADOS PARA: '{results['query']}'")
        print(f"{'=' * 80}")
        print(f"Tiempo total: {results['time_taken']:.4f} segundos")
        
        # Mostrar tiempos por componente
        if "component_times" in results:
            print("\nTiempos por componente:")
            for component, time_taken in results["component_times"].items():
                print(f"  - {component}: {time_taken:.4f} segundos")
        
        print(f"\nResultados encontrados: {results['total_found']}")
        
        # Mostrar resultados
        for i, result in enumerate(results["results"]):
            print(f"\n{'-' * 80}")
            print(f"RESULTADO {i+1} (Score: {result['score']:.4f})")
            print(f"{'-' * 80}")
            
            # Mostrar fuente del retriever
            if "source_retriever" in result:
                print(f"Fuente: {result['source_retriever']}")
            
            # Mostrar metadata
            if "metadata" in result and result["metadata"]:
                print("Metadata:")
                for key, value in result["metadata"].items():
                    print(f"  - {key}: {value}")
            
            # Mostrar texto truncado
            text = result["text"]
            if len(text) > max_text_length:
                print(f"\nTexto: {text[:max_text_length]}...")
            else:
                print(f"\nTexto: {text}")
            
            # Extraer y mostrar entidades
            if show_entities:
                try:
                    entities = self.extract_entities(text)
                    if entities:
                        print("\nEntidades:")
                        for entity_type, entity_list in entities.items():
                            print(f"  - {entity_type}: {', '.join(entity_list)}")
                except Exception as e:
                    print(f"Error al extraer entidades: {str(e)}")
        
        print(f"\n{'=' * 80}")


if __name__ == "__main__":
    # Ejemplo de uso
    print("Inicializando SearchPipeline...")
    pipeline = SearchPipeline()
    
    # Ejemplo de búsqueda
    query = "¿Cuál es el procedimiento para solicitar viáticos?"
    print(f"\nRealizando búsqueda: '{query}'")
    
    results = pipeline.search(query, top_k=3)
    
    # Mostrar resultados
    pipeline.print_results(results)

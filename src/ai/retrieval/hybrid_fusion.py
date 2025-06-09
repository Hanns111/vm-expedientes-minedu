#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Hybrid Fusion con Reciprocal Rank Fusion (RRF).
Combina resultados de múltiples retrievers (BM25 y E5-Large)
para obtener lo mejor de cada enfoque.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from collections import defaultdict

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HybridFusion')

class HybridFusion:
    """
    Implementa fusión híbrida de resultados usando Reciprocal Rank Fusion (RRF).
    
    RRF combina rankings de diferentes sistemas asignando puntuaciones basadas
    en la posición inversa de cada documento en cada ranking, permitiendo
    aprovechar las fortalezas de sistemas léxicos (BM25) y semánticos (E5).
    """
    
    def __init__(
        self,
        retrievers: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
        rrf_k: int = 60,
        deduplicate: bool = True
    ):
        """
        Inicializa el sistema de fusión híbrida.
        
        Args:
            retrievers: Diccionario de retrievers {'nombre': objeto_retriever}
            weights: Pesos para cada retriever {'nombre': peso}
            rrf_k: Constante k para RRF (default: 60)
            deduplicate: Si se deben eliminar duplicados
        """
        self.retrievers = retrievers
        self.rrf_k = rrf_k
        self.deduplicate = deduplicate
        
        # Configurar pesos (default: pesos iguales)
        if weights:
            self.weights = weights
        else:
            # Pesos iguales para todos los retrievers
            self.weights = {name: 1.0 for name in retrievers.keys()}
        
        # Normalizar pesos para que sumen 1
        weight_sum = sum(self.weights.values())
        self.weights = {k: v / weight_sum for k, v in self.weights.items()}
        
        logger.info(f"HybridFusion inicializado con {len(retrievers)} retrievers")
        logger.info(f"Pesos: {self.weights}")
        logger.info(f"RRF k: {rrf_k}, Deduplicación: {deduplicate}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        retriever_params: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Realiza búsqueda híbrida combinando resultados de todos los retrievers.
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de resultados a devolver
            retriever_params: Parámetros específicos para cada retriever
            
        Returns:
            Resultados combinados con scores y metadatos
        """
        start_time = time.time()
        logger.info(f"Iniciando búsqueda híbrida para: '{query}'")
        
        # Parámetros por defecto si no se especifican
        if not retriever_params:
            retriever_params = {}
        
        # Resultados de cada retriever
        retriever_results = {}
        retriever_times = {}
        
        # Ejecutar cada retriever
        for name, retriever in self.retrievers.items():
            retriever_start = time.time()
            
            # Obtener parámetros específicos para este retriever
            params = retriever_params.get(name, {})
            
            # Ejecutar búsqueda con el retriever correspondiente
            try:
                results = retriever.search(query, **params)
                
                # Normalizar formato de resultados
                normalized_results = self._normalize_results(results, name)
                
                retriever_results[name] = normalized_results
                retriever_times[name] = time.time() - retriever_start
                
                logger.info(f"Retriever {name}: {len(normalized_results)} resultados en {retriever_times[name]:.4f} segundos")
            
            except Exception as e:
                logger.error(f"Error en retriever {name}: {str(e)}")
                retriever_results[name] = []
                retriever_times[name] = time.time() - retriever_start
        
        # Aplicar fusión de resultados
        fused_results = self._apply_rrf_fusion(retriever_results, top_k)
        
        # Preparar respuesta
        response = {
            "query": query,
            "time_taken": time.time() - start_time,
            "retriever_times": retriever_times,
            "total_found": len(fused_results),
            "results": fused_results
        }
        
        logger.info(f"Búsqueda híbrida completada en {response['time_taken']:.4f} segundos")
        logger.info(f"Total resultados fusionados: {len(fused_results)}")
        
        return response
    
    def _normalize_results(self, results: Any, retriever_name: str) -> List[Dict[str, Any]]:
        """
        Normaliza los resultados de diferentes retrievers a un formato común.
        
        Args:
            results: Resultados del retriever (puede ser dict, list, etc.)
            retriever_name: Nombre del retriever
            
        Returns:
            Lista normalizada de resultados
        """
        normalized = []
        
        # Manejar diferentes formatos de resultados
        if isinstance(results, dict) and "results" in results:
            # Formato {results: [...]}
            items = results["results"]
        elif isinstance(results, list):
            # Formato lista directa
            items = results
        else:
            logger.warning(f"Formato de resultados desconocido para {retriever_name}")
            return []
        
        # Normalizar cada resultado
        for i, item in enumerate(items):
            if isinstance(item, dict):
                normalized_item = {
                    "id": item.get("id", f"{retriever_name}_{i}"),
                    "text": item.get("text", ""),
                    "score": item.get("score", 0.0),
                    "rank": item.get("rank", i + 1),
                    "metadata": item.get("metadata", {}),
                    "source_retriever": retriever_name
                }
                normalized.append(normalized_item)
            else:
                logger.warning(f"Elemento de resultados no es un diccionario: {item}")
        
        return normalized
    
    def _apply_rrf_fusion(
        self,
        retriever_results: Dict[str, List[Dict[str, Any]]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Aplica Reciprocal Rank Fusion para combinar resultados.
        
        Args:
            retriever_results: Resultados de cada retriever
            top_k: Número de resultados a devolver
            
        Returns:
            Lista de resultados fusionados
        """
        # Diccionario para acumular scores RRF por documento
        rrf_scores = defaultdict(float)
        
        # Mapeo de documentos para deduplicación y tracking
        doc_map = {}
        
        # Calcular scores RRF
        for retriever_name, results in retriever_results.items():
            weight = self.weights[retriever_name]
            
            for result in results:
                # Crear clave única para el documento
                doc_key = self._get_document_key(result)
                
                # Guardar documento en el mapeo
                if doc_key not in doc_map:
                    doc_map[doc_key] = result
                
                # Calcular score RRF: 1 / (rank + k)
                rank = result["rank"]
                rrf_score = 1.0 / (rank + self.rrf_k)
                
                # Aplicar peso del retriever
                weighted_score = rrf_score * weight
                
                # Acumular score
                rrf_scores[doc_key] += weighted_score
        
        # Ordenar documentos por score RRF
        sorted_docs = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Preparar resultados finales
        fused_results = []
        seen_texts = set() if self.deduplicate else None
        
        for i, (doc_key, rrf_score) in enumerate(sorted_docs):
            if i >= top_k:
                break
                
            # Obtener documento original
            doc = doc_map[doc_key]
            
            # Deduplicación por texto si está activada
            if self.deduplicate:
                # Usar una versión simplificada del texto para deduplicación
                simple_text = self._simplify_for_dedup(doc["text"])
                if simple_text in seen_texts:
                    continue
                seen_texts.add(simple_text)
            
            # Crear resultado fusionado
            fused_doc = {
                "rank": i + 1,
                "id": doc["id"],
                "text": doc["text"],
                "score": rrf_score,
                "original_score": doc["score"],
                "metadata": doc["metadata"],
                "source_retriever": doc["source_retriever"]
            }
            
            fused_results.append(fused_doc)
        
        return fused_results
    
    def _get_document_key(self, doc: Dict[str, Any]) -> str:
        """
        Genera una clave única para un documento.
        
        Args:
            doc: Documento
            
        Returns:
            Clave única
        """
        # Si el documento tiene un ID único, usarlo
        if "id" in doc and doc["id"]:
            return str(doc["id"])
        
        # De lo contrario, usar una combinación de texto y metadata
        text_hash = hash(doc["text"][:100])
        metadata_str = json.dumps(doc["metadata"], sort_keys=True) if "metadata" in doc else ""
        metadata_hash = hash(metadata_str)
        
        return f"{text_hash}_{metadata_hash}"
    
    def _simplify_for_dedup(self, text: str) -> str:
        """
        Simplifica un texto para deduplicación.
        
        Args:
            text: Texto a simplificar
            
        Returns:
            Texto simplificado
        """
        # Tomar los primeros 100 caracteres, convertir a minúsculas y eliminar espacios
        return ''.join(text[:100].lower().split())


if __name__ == "__main__":
    # Ejemplo de uso
    print("Ejemplo de HybridFusion")
    
    # Simulación de retrievers
    class MockRetriever:
        def __init__(self, name, results):
            self.name = name
            self.mock_results = results
        
        def search(self, query, **kwargs):
            print(f"Ejecutando {self.name} con query: {query}")
            return {"results": self.mock_results}
    
    # Resultados simulados de BM25
    bm25_results = [
        {"id": "doc1", "text": "Procedimiento para solicitar viáticos", "score": 0.95, "rank": 1, 
         "metadata": {"source": "Manual de Procedimientos", "page": 15}},
        {"id": "doc2", "text": "Formulario de solicitud de viáticos", "score": 0.85, "rank": 2,
         "metadata": {"source": "Anexos", "page": 3}},
        {"id": "doc3", "text": "Rendición de viáticos y gastos", "score": 0.75, "rank": 3,
         "metadata": {"source": "Manual de Procedimientos", "page": 18}}
    ]
    
    # Resultados simulados de E5
    e5_results = [
        {"id": "doc4", "text": "El proceso para pedir viáticos incluye llenar el formato F-01", "score": 0.92, "rank": 1,
         "metadata": {"source": "Directiva de Viáticos", "page": 5}},
        {"id": "doc1", "text": "Procedimiento para solicitar viáticos", "score": 0.88, "rank": 2,
         "metadata": {"source": "Manual de Procedimientos", "page": 15}},
        {"id": "doc5", "text": "Aprobación de solicitudes de viáticos por jefatura", "score": 0.79, "rank": 3,
         "metadata": {"source": "Directiva de Viáticos", "page": 8}}
    ]
    
    # Crear retrievers simulados
    bm25_retriever = MockRetriever("bm25", bm25_results)
    e5_retriever = MockRetriever("e5", e5_results)
    
    # Crear fusion
    fusion = HybridFusion(
        retrievers={"bm25": bm25_retriever, "e5": e5_retriever},
        weights={"bm25": 0.4, "e5": 0.6},
        rrf_k=60,
        deduplicate=True
    )
    
    # Ejecutar búsqueda híbrida
    query = "¿Cómo solicitar viáticos?"
    results = fusion.search(query, top_k=5)
    
    # Mostrar resultados
    print(f"\nResultados para: '{query}'")
    print(f"Tiempo total: {results['time_taken']:.4f} segundos")
    print(f"Tiempos por retriever: {results['retriever_times']}")
    print(f"Total resultados: {results['total_found']}")
    
    for result in results["results"]:
        print(f"\nRank {result['rank']} (Score RRF: {result['score']:.4f}):")
        print(f"ID: {result['id']}")
        print(f"Fuente: {result['source_retriever']} (Score original: {result['original_score']:.4f})")
        print(f"Metadata: {result['metadata']}")
        print(f"Texto: {result['text']}")

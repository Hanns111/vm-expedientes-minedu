#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fusión Híbrida Centralizada para Sistema RAG MINEDU

Este módulo implementa fusión híbrida de resultados de diferentes retrievers
usando Reciprocal Rank Fusion (RRF) y fusión ponderada.

Autor: Hanns
Fecha: 2025-06-14
"""

import os
import sys
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from collections import defaultdict

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HybridFusion')


class HybridFusion:
    """
    Sistema centralizado de fusión híbrida para combinar resultados de múltiples retrievers.
    
    Soporta:
    - Reciprocal Rank Fusion (RRF)
    - Fusión ponderada
    - Deduplicación de resultados
    - Normalización de formatos
    """
    
    def __init__(
        self,
        retrievers: Optional[Dict[str, Any]] = None,
        method: str = "rrf",
        weights: Optional[Dict[str, float]] = None,
        rrf_k: int = 60,
        deduplicate: bool = True,
        **kwargs
    ):
        """
        Inicializa el sistema de fusión híbrida.
        
        Args:
            retrievers: Diccionario de retrievers {'nombre': objeto_retriever}
            method: Método de fusión ('rrf', 'weighted')
            weights: Pesos para cada retriever
            rrf_k: Constante k para RRF (default: 60)
            deduplicate: Si se deben eliminar duplicados
            **kwargs: Argumentos adicionales
        """
        self.retrievers = retrievers or {}
        self.method = method.lower()
        self.rrf_k = rrf_k
        self.deduplicate = deduplicate
        
        # Configurar pesos por defecto
        if weights:
            self.weights = weights
        else:
            # Pesos iguales para todos los retrievers
            self.weights = {name: 1.0 for name in self.retrievers.keys()}
        
        # Normalizar pesos para que sumen 1
        if self.weights:
            weight_sum = sum(self.weights.values())
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}
        
        # Validar método de fusión
        valid_methods = ["rrf", "weighted"]
        if self.method not in valid_methods:
            logger.warning(f"Método de fusión '{method}' no válido. Usando 'rrf' por defecto.")
            self.method = "rrf"
        
        logger.info(f"HybridFusion inicializado con método: {self.method}")
        logger.info(f"Retrievers: {list(self.retrievers.keys())}")
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
                results = self._execute_retriever(retriever, query, params)
                
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
        if self.method == "rrf":
            fused_results = self._apply_rrf_fusion(retriever_results, top_k)
        else:  # weighted
            fused_results = self._apply_weighted_fusion(retriever_results, top_k)
        
        # Preparar respuesta
        response = {
            "query": query,
            "time_taken": time.time() - start_time,
            "retriever_times": retriever_times,
            "total_found": len(fused_results),
            "results": fused_results,
            "fusion_method": self.method
        }
        
        logger.info(f"Búsqueda híbrida completada en {response['time_taken']:.4f} segundos")
        logger.info(f"Total resultados fusionados: {len(fused_results)}")
        
        return response
    
    def _execute_retriever(self, retriever: Any, query: str, params: Dict[str, Any]) -> Any:
        """
        Ejecuta un retriever con la interfaz apropiada.
        
        Args:
            retriever: Objeto retriever
            query: Consulta de búsqueda
            params: Parámetros adicionales
            
        Returns:
            Resultados del retriever
        """
        # Intentar diferentes interfaces de retriever
        if hasattr(retriever, 'search'):
            return retriever.search(query, **params)
        elif hasattr(retriever, 'retrieve'):
            return retriever.retrieve(query, **params)
        elif hasattr(retriever, 'get_relevant_documents'):
            return retriever.get_relevant_documents(query, **params)
        elif hasattr(retriever, 'generate_response'):
            return retriever.generate_response(query, **params)
        else:
            raise ValueError(f"Retriever no tiene interfaz válida: {type(retriever)}")
    
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
        if isinstance(results, dict):
            if "results" in results:
                # Formato {results: [...]}
                items = results["results"]
            elif "documents" in results:
                # Formato {documents: [...]}
                items = results["documents"]
            else:
                # Asumir que el dict es un solo resultado
                items = [results]
        elif isinstance(results, list):
            # Formato lista directa
            items = results
        else:
            logger.warning(f"Formato de resultados desconocido para {retriever_name}: {type(results)}")
            return []
        
        # Normalizar cada resultado
        for i, item in enumerate(items):
            if isinstance(item, dict):
                normalized_item = {
                    "id": item.get("id", f"{retriever_name}_{i}"),
                    "text": item.get("text", item.get("content", item.get("texto", ""))),
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
        document_info = {}
        
        # Procesar resultados de cada retriever
        for retriever_name, results in retriever_results.items():
            weight = self.weights.get(retriever_name, 1.0)
            
            for rank, doc in enumerate(results):
                doc_key = self._get_document_key(doc)
                rrf_score = weight * (1 / (rank + self.rrf_k))
                
                rrf_scores[doc_key] += rrf_score
                
                # Mantener información del documento
                if doc_key not in document_info:
                    document_info[doc_key] = {
                        "doc": doc,
                        "sources": [retriever_name],
                        "ranks": {retriever_name: rank + 1}
                    }
                else:
                    document_info[doc_key]["sources"].append(retriever_name)
                    document_info[doc_key]["ranks"][retriever_name] = rank + 1
                    # Mantener el documento con más información
                    if len(doc.get("text", "")) > len(document_info[doc_key]["doc"].get("text", "")):
                        document_info[doc_key]["doc"] = doc
        
        # Ordenar por score RRF
        sorted_docs = sorted(
            [(key, score) for key, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Preparar resultados finales
        results = []
        for i, (doc_key, rrf_score) in enumerate(sorted_docs[:top_k]):
            doc_info = document_info[doc_key]
            doc = doc_info["doc"].copy()
            
            doc["score"] = rrf_score
            doc["rank"] = i + 1
            doc["fusion_sources"] = doc_info["sources"]
            doc["fusion_ranks"] = doc_info["ranks"]
            doc["fusion_method"] = "rrf"
            
            results.append(doc)
        
        return results
    
    def _apply_weighted_fusion(
        self,
        retriever_results: Dict[str, List[Dict[str, Any]]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Aplica fusión ponderada de resultados.
        
        Args:
            retriever_results: Resultados de cada retriever
            top_k: Número de resultados a devolver
            
        Returns:
            Lista de resultados fusionados
        """
        # Diccionario para acumular scores ponderados por documento
        weighted_scores = defaultdict(float)
        document_info = {}
        
        # Procesar resultados de cada retriever
        for retriever_name, results in retriever_results.items():
            weight = self.weights.get(retriever_name, 1.0)
            
            for rank, doc in enumerate(results):
                doc_key = self._get_document_key(doc)
                weighted_score = weight * doc.get("score", 0.0)
                
                weighted_scores[doc_key] += weighted_score
                
                # Mantener información del documento
                if doc_key not in document_info:
                    document_info[doc_key] = {
                        "doc": doc,
                        "sources": [retriever_name],
                        "scores": {retriever_name: doc.get("score", 0.0)}
                    }
                else:
                    document_info[doc_key]["sources"].append(retriever_name)
                    document_info[doc_key]["scores"][retriever_name] = doc.get("score", 0.0)
                    # Mantener el documento con más información
                    if len(doc.get("text", "")) > len(document_info[doc_key]["doc"].get("text", "")):
                        document_info[doc_key]["doc"] = doc
        
        # Ordenar por score ponderado
        sorted_docs = sorted(
            [(key, score) for key, score in weighted_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Preparar resultados finales
        results = []
        for i, (doc_key, weighted_score) in enumerate(sorted_docs[:top_k]):
            doc_info = document_info[doc_key]
            doc = doc_info["doc"].copy()
            
            doc["score"] = weighted_score
            doc["rank"] = i + 1
            doc["fusion_sources"] = doc_info["sources"]
            doc["fusion_scores"] = doc_info["scores"]
            doc["fusion_method"] = "weighted"
            
            results.append(doc)
        
        return results
    
    def _get_document_key(self, doc: Dict[str, Any]) -> str:
        """
        Genera una clave única para un documento para deduplicación.
        
        Args:
            doc: Documento a procesar
            
        Returns:
            Clave única del documento
        """
        if self.deduplicate:
            # Usar ID si está disponible
            if "id" in doc:
                return str(doc["id"])
            
            # Usar texto simplificado como clave
            text = doc.get("text", "")
            return self._simplify_for_dedup(text)
        else:
            # Sin deduplicación, usar índice temporal
            return f"doc_{id(doc)}"
    
    def _simplify_for_dedup(self, text: str) -> str:
        """
        Simplifica texto para deduplicación.
        
        Args:
            text: Texto a simplificar
            
        Returns:
            Texto simplificado
        """
        # Convertir a minúsculas y eliminar espacios extra
        simplified = text.lower().strip()
        
        # Eliminar caracteres especiales y normalizar espacios
        import re
        simplified = re.sub(r'[^\w\s]', '', simplified)
        simplified = re.sub(r'\s+', ' ', simplified)
        
        # Limitar longitud para evitar claves muy largas
        return simplified[:100]
    
    def add_retriever(self, name: str, retriever: Any, weight: float = 1.0):
        """
        Agrega un retriever al sistema de fusión.
        
        Args:
            name: Nombre del retriever
            retriever: Objeto retriever
            weight: Peso del retriever
        """
        self.retrievers[name] = retriever
        self.weights[name] = weight
        
        # Renormalizar pesos
        weight_sum = sum(self.weights.values())
        self.weights = {k: v / weight_sum for k, v in self.weights.items()}
        
        logger.info(f"Retriever '{name}' agregado con peso {weight}")
    
    def remove_retriever(self, name: str):
        """
        Remueve un retriever del sistema de fusión.
        
        Args:
            name: Nombre del retriever a remover
        """
        if name in self.retrievers:
            del self.retrievers[name]
            del self.weights[name]
            
            # Renormalizar pesos si quedan retrievers
            if self.weights:
                weight_sum = sum(self.weights.values())
                self.weights = {k: v / weight_sum for k, v in self.weights.items()}
            
            logger.info(f"Retriever '{name}' removido")
        else:
            logger.warning(f"Retriever '{name}' no encontrado")


# Clase de utilidad para testing
class MockRetriever:
    """Retriever mock para testing"""
    
    def __init__(self, name: str, results: List[Dict[str, Any]]):
        self.name = name
        self.results = results
    
    def search(self, query: str, **kwargs):
        return {"results": self.results}


# Ejemplo de uso
if __name__ == "__main__":
    # Crear retrievers mock para testing
    mock_bm25 = MockRetriever("bm25", [
        {"id": "doc1", "text": "Documento 1", "score": 0.9},
        {"id": "doc2", "text": "Documento 2", "score": 0.8}
    ])
    
    mock_dense = MockRetriever("dense", [
        {"id": "doc2", "text": "Documento 2", "score": 0.95},
        {"id": "doc3", "text": "Documento 3", "score": 0.85}
    ])
    
    # Inicializar fusión híbrida
    fusion = HybridFusion(
        retrievers={"bm25": mock_bm25, "dense": mock_dense},
        method="rrf",
        weights={"bm25": 1.0, "dense": 1.0}
    )
    
    # Ejecutar búsqueda
    results = fusion.search("test query", top_k=3)
    
    print("Resultados de fusión híbrida:")
    for i, result in enumerate(results["results"], 1):
        print(f"{i}. Score: {result['score']:.4f} | Fuentes: {result['fusion_sources']}")
        print(f"   Texto: {result['text']}")
        print() 
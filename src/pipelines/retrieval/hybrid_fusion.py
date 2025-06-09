#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Adaptador para la fusión híbrida de retrievers.

Este módulo implementa un adaptador para la fusión híbrida de resultados
de diferentes retrievers (BM25 y Dense) en el pipeline RAG de MINEDU.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

# Importar adaptadores locales
from src.pipelines.retrieval.bm25_retriever import BM25Retriever
from src.pipelines.retrieval.dense_retriever_e5 import DenseRetrieverE5Adapter

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HybridFusion')


class HybridFusion:
    """
    Implementa fusión híbrida de resultados de diferentes retrievers.
    
    Soporta diferentes métodos de fusión como RRF (Reciprocal Rank Fusion)
    y fusión ponderada para combinar resultados de BM25 y retrievers densos.
    """
    
    def __init__(
        self,
        bm25_retriever: Optional[BM25Retriever] = None,
        dense_retriever: Optional[DenseRetrieverE5Adapter] = None,
        method: str = "rrf",
        weights: Dict[str, float] = None,
        rrf_k: int = 60,
        **kwargs
    ):
        """
        Inicializa el componente de fusión híbrida.
        
        Args:
            bm25_retriever: Instancia de BM25Retriever
            dense_retriever: Instancia de DenseRetrieverE5Adapter
            method: Método de fusión ('rrf', 'weighted')
            weights: Pesos para cada retriever en fusión ponderada
            rrf_k: Parámetro k para RRF
            **kwargs: Argumentos adicionales
        """
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.method = method.lower()
        self.rrf_k = rrf_k
        
        # Configurar pesos por defecto si no se proporcionan
        self.weights = weights or {"bm25": 1.0, "dense": 1.0}
        
        # Validar método de fusión
        valid_methods = ["rrf", "weighted"]
        if self.method not in valid_methods:
            logger.warning(f"Método de fusión '{method}' no válido. Usando 'rrf' por defecto.")
            self.method = "rrf"
        
        logger.info(f"HybridFusion inicializado con método: {self.method}")
        logger.info(f"Pesos: {self.weights}, RRF k: {self.rrf_k}")
    
    def retrieve(self, query: str, passages: Optional[List[str]] = None, metadata: Optional[List[Dict[str, Any]]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recupera documentos combinando resultados de múltiples retrievers.
        
        Args:
            query: Consulta de búsqueda
            passages: Lista de pasajes para dense retriever (opcional)
            metadata: Lista de metadatos asociados a los pasajes (opcional)
            top_k: Número de resultados a devolver
            
        Returns:
            Lista combinada de documentos recuperados
        """
        logger.info(f"Ejecutando fusión híbrida para: '{query}' (top_k={top_k})")
        
        # Resultados de cada retriever
        bm25_results = []
        dense_results = []
        
        # Obtener resultados de BM25 si está disponible
        if self.bm25_retriever:
            try:
                bm25_results = self.bm25_retriever.retrieve(query, top_k=top_k*2)  # Recuperar más para fusión
                logger.info(f"BM25 recuperó {len(bm25_results)} documentos")
            except Exception as e:
                logger.error(f"Error en BM25Retriever: {str(e)}")
        
        # Obtener resultados del retriever denso si está disponible y tenemos passages
        if self.dense_retriever and passages:
            try:
                dense_results = self.dense_retriever.retrieve(query, passages, metadata, top_k=top_k*2)  # Recuperar más para fusión
                logger.info(f"Dense retriever recuperó {len(dense_results)} documentos")
            except Exception as e:
                logger.error(f"Error en DenseRetrieverE5: {str(e)}")
        
        # Aplicar método de fusión seleccionado
        if self.method == "rrf":
            results = self._reciprocal_rank_fusion(bm25_results, dense_results, top_k)
        else:  # weighted
            results = self._weighted_fusion(bm25_results, dense_results, top_k)
        
        logger.info(f"Fusión híbrida completada. Resultados combinados: {len(results)}")
        return results
    
    def _reciprocal_rank_fusion(self, bm25_results: List[Dict[str, Any]], dense_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Implementa Reciprocal Rank Fusion (RRF) para combinar resultados.
        
        RRF combina rankings dando más peso a documentos que aparecen en posiciones altas
        en múltiples rankings.
        
        Args:
            bm25_results: Resultados del BM25Retriever
            dense_results: Resultados del DenseRetrieverE5
            top_k: Número de resultados a devolver
            
        Returns:
            Lista combinada de documentos
        """
        # Crear diccionario para acumular puntuaciones RRF
        document_scores = {}
        
        # Procesar resultados de BM25
        for rank, doc in enumerate(bm25_results):
            doc_id = self._get_document_id(doc)
            rrf_score = self.weights.get("bm25", 1.0) * (1 / (rank + self.rrf_k))
            
            if doc_id in document_scores:
                document_scores[doc_id]["rrf_score"] += rrf_score
                # Mantener el documento con más información
                if len(doc.get("content", "")) > len(document_scores[doc_id]["doc"].get("content", "")):
                    document_scores[doc_id]["doc"] = doc
            else:
                document_scores[doc_id] = {
                    "doc": doc,
                    "rrf_score": rrf_score,
                    "sources": ["bm25"]
                }
        
        # Procesar resultados del retriever denso
        for rank, doc in enumerate(dense_results):
            doc_id = self._get_document_id(doc)
            rrf_score = self.weights.get("dense", 1.0) * (1 / (rank + self.rrf_k))
            
            if doc_id in document_scores:
                document_scores[doc_id]["rrf_score"] += rrf_score
                document_scores[doc_id]["sources"].append("dense")
                # Mantener el documento con más información
                if len(doc.get("content", "")) > len(document_scores[doc_id]["doc"].get("content", "")):
                    document_scores[doc_id]["doc"] = doc
            else:
                document_scores[doc_id] = {
                    "doc": doc,
                    "rrf_score": rrf_score,
                    "sources": ["dense"]
                }
        
        # Ordenar por puntuación RRF
        sorted_docs = sorted(document_scores.values(), key=lambda x: x["rrf_score"], reverse=True)
        
        # Preparar resultados finales
        results = []
        for i, item in enumerate(sorted_docs[:top_k]):
            doc = item["doc"].copy()
            doc["score"] = item["rrf_score"]
            doc["rank"] = i + 1
            doc["fusion_sources"] = item["sources"]
            results.append(doc)
        
        return results
    
    def _weighted_fusion(self, bm25_results: List[Dict[str, Any]], dense_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Implementa fusión ponderada de resultados.
        
        Combina resultados usando pesos configurados para cada retriever.
        
        Args:
            bm25_results: Resultados del BM25Retriever
            dense_results: Resultados del DenseRetrieverE5
            top_k: Número de resultados a devolver
            
        Returns:
            Lista combinada de documentos
        """
        # Crear diccionario para acumular puntuaciones ponderadas
        document_scores = {}
        
        # Normalizar puntuaciones BM25
        bm25_max_score = max([doc.get("score", 0) for doc in bm25_results]) if bm25_results else 1.0
        
        # Procesar resultados de BM25
        for doc in bm25_results:
            doc_id = self._get_document_id(doc)
            normalized_score = doc.get("score", 0) / bm25_max_score if bm25_max_score > 0 else 0
            weighted_score = self.weights.get("bm25", 1.0) * normalized_score
            
            if doc_id in document_scores:
                document_scores[doc_id]["weighted_score"] += weighted_score
                # Mantener el documento con más información
                if len(doc.get("content", "")) > len(document_scores[doc_id]["doc"].get("content", "")):
                    document_scores[doc_id]["doc"] = doc
            else:
                document_scores[doc_id] = {
                    "doc": doc,
                    "weighted_score": weighted_score,
                    "sources": ["bm25"]
                }
        
        # Normalizar puntuaciones Dense
        dense_max_score = max([doc.get("score", 0) for doc in dense_results]) if dense_results else 1.0
        
        # Procesar resultados del retriever denso
        for doc in dense_results:
            doc_id = self._get_document_id(doc)
            normalized_score = doc.get("score", 0) / dense_max_score if dense_max_score > 0 else 0
            weighted_score = self.weights.get("dense", 1.0) * normalized_score
            
            if doc_id in document_scores:
                document_scores[doc_id]["weighted_score"] += weighted_score
                document_scores[doc_id]["sources"].append("dense")
                # Mantener el documento con más información
                if len(doc.get("content", "")) > len(document_scores[doc_id]["doc"].get("content", "")):
                    document_scores[doc_id]["doc"] = doc
            else:
                document_scores[doc_id] = {
                    "doc": doc,
                    "weighted_score": weighted_score,
                    "sources": ["dense"]
                }
        
        # Ordenar por puntuación ponderada
        sorted_docs = sorted(document_scores.values(), key=lambda x: x["weighted_score"], reverse=True)
        
        # Preparar resultados finales
        results = []
        for i, item in enumerate(sorted_docs[:top_k]):
            doc = item["doc"].copy()
            doc["score"] = item["weighted_score"]
            doc["rank"] = i + 1
            doc["fusion_sources"] = item["sources"]
            results.append(doc)
        
        return results
    
    def _get_document_id(self, doc: Dict[str, Any]) -> str:
        """
        Genera un ID único para un documento.
        
        Args:
            doc: Documento a identificar
            
        Returns:
            ID único para el documento
        """
        # Intentar usar metadata si está disponible
        metadata = doc.get("metadata", {})
        if metadata:
            source = metadata.get("source", "")
            chunk_id = metadata.get("chunk_id", "")
            if source and chunk_id:
                return f"{source}:{chunk_id}"
        
        # Usar hash del contenido como fallback
        content = doc.get("content", "")
        return f"doc:{hash(content)}"
    
    def get_relevant_documents(self, query: str, passages: Optional[List[str]] = None, metadata: Optional[List[Dict[str, Any]]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Alias para retrieve() para compatibilidad con LangChain.
        
        Args:
            query: Consulta de búsqueda
            passages: Lista de pasajes para dense retriever (opcional)
            metadata: Lista de metadatos asociados a los pasajes (opcional)
            top_k: Número de resultados a devolver
            
        Returns:
            Lista combinada de documentos recuperados
        """
        return self.retrieve(query, passages, metadata, top_k)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear retrievers
    bm25 = BM25Retriever('data/processed/vectorstore_bm25_test.pkl')
    dense = DenseRetrieverE5Adapter(device="cpu")
    
    # Crear fusión híbrida
    fusion = HybridFusion(
        bm25_retriever=bm25,
        dense_retriever=dense,
        method="rrf",
        weights={"bm25": 1.0, "dense": 0.7},
        rrf_k=60
    )
    
    # Ejemplo de consulta
    query = "¿Cuál es el monto máximo para viáticos nacionales?"
    
    # Ejemplo de pasajes para dense retriever
    passages = [
        "Los viáticos nacionales tienen un monto máximo de S/ 320.00 por día según la escala vigente.",
        "El plazo para presentar la rendición de cuentas es de 10 días hábiles contados desde la culminación de la comisión.",
        "Para solicitar viáticos se requiere memorando de autorización, planilla de viáticos y formato de declaración jurada.",
        "Los viáticos para servidores públicos están regulados por el Decreto Supremo N° 007-2013-EF.",
        "Las solicitudes de viáticos son aprobadas por el jefe inmediato del comisionado y el Director de Administración."
    ]
    
    metadata = [
        {"source": "Manual de Procedimientos", "page": 15},
        {"source": "Directiva de Viáticos", "page": 3},
        {"source": "Manual de RRHH", "page": 22},
        {"source": "Directiva de Viáticos", "page": 8},
        {"source": "Manual de Procedimientos", "page": 16}
    ]
    
    # Ejecutar fusión híbrida
    results = fusion.retrieve(query, passages, metadata, top_k=3)
    
    print(f"\nResultados de fusión híbrida ({len(results)}):")
    for i, doc in enumerate(results):
        print(f"\n[{i+1}] Score: {doc['score']:.4f}")
        print(f"Content: {doc['content'][:100]}...")
        print(f"Sources: {doc['fusion_sources']}")
        print(f"Metadata: {doc['metadata']}")

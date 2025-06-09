#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Neural Re-ranking con CrossEncoder.
Implementa re-ranking avanzado usando modelos CrossEncoder para mejorar
la relevancia de los resultados de búsqueda.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

# Dependencias para CrossEncoder
import torch
from sentence_transformers import CrossEncoder
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('NeuralReranker')

class NeuralReranker:
    """
    Re-ranker neural basado en CrossEncoder.
    
    Los CrossEncoders evalúan directamente la relevancia entre una consulta y un documento,
    ofreciendo mayor precisión que los modelos bi-encoder tradicionales.
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = 16,
        max_length: int = 512
    ):
        """
        Inicializa el re-ranker neural con CrossEncoder.
        
        Args:
            model_name: Nombre del modelo CrossEncoder a utilizar
            cache_dir: Directorio para caché de modelos
            device: Dispositivo para inferencia ('cpu', 'cuda', 'cuda:0', etc.)
            batch_size: Tamaño de batch para inferencia
            max_length: Longitud máxima de tokens
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self.max_length = max_length
        
        # Determinar dispositivo
        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Cargar modelo
        self._load_model()
        
        logger.info(f"NeuralReranker inicializado con modelo {model_name}")
        logger.info(f"Usando device: {self.device}, batch_size: {batch_size}, max_length: {max_length}")
    
    def _load_model(self):
        """
        Carga el modelo CrossEncoder.
        """
        start_time = time.time()
        logger.info(f"Cargando modelo CrossEncoder: {self.model_name}")
        
        # Cargar modelo
        self.model = CrossEncoder(
            self.model_name,
            device=self.device,
            max_length=self.max_length
        )
        
        load_time = time.time() - start_time
        logger.info(f"Modelo CrossEncoder cargado en {load_time:.2f} segundos")
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rankea documentos usando el modelo CrossEncoder.
        
        Args:
            query: Consulta de búsqueda
            documents: Lista de documentos a re-rankear
            top_k: Número de documentos a devolver después del re-ranking
            score_threshold: Umbral mínimo de score para incluir documentos
            
        Returns:
            Lista de documentos re-rankeados
        """
        start_time = time.time()
        
        if not documents:
            logger.warning("No se proporcionaron documentos para re-rankear")
            return []
        
        # Preparar pares consulta-documento para CrossEncoder
        query_doc_pairs = [(query, doc["text"]) for doc in documents]
        
        # Calcular scores de relevancia
        logger.info(f"Calculando scores para {len(query_doc_pairs)} pares consulta-documento")
        scores = self.model.predict(
            query_doc_pairs,
            batch_size=self.batch_size,
            show_progress_bar=len(query_doc_pairs) > 10
        )
        
        # Combinar documentos con sus nuevos scores
        reranked_docs = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            # Crear copia del documento original
            reranked_doc = doc.copy()
            
            # Guardar score original si existe
            if "score" in reranked_doc:
                reranked_doc["original_score"] = reranked_doc["score"]
            
            # Actualizar con nuevo score
            reranked_doc["score"] = float(score)
            reranked_doc["reranker_score"] = float(score)
            
            reranked_docs.append(reranked_doc)
        
        # Ordenar por score de mayor a menor
        reranked_docs = sorted(reranked_docs, key=lambda x: x["score"], reverse=True)
        
        # Aplicar filtro de umbral si se especifica
        if score_threshold is not None:
            reranked_docs = [doc for doc in reranked_docs if doc["score"] >= score_threshold]
        
        # Limitar a top_k si se especifica
        if top_k is not None:
            reranked_docs = reranked_docs[:top_k]
        
        # Actualizar ranks
        for i, doc in enumerate(reranked_docs):
            doc["rank"] = i + 1
        
        rerank_time = time.time() - start_time
        logger.info(f"Re-ranking completado en {rerank_time:.4f} segundos")
        logger.info(f"Documentos después de re-ranking: {len(reranked_docs)}")
        
        return reranked_docs
    
    def calibrate_scores(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calibra los scores para que sean más interpretables.
        
        Args:
            documents: Lista de documentos con scores
            
        Returns:
            Lista de documentos con scores calibrados
        """
        if not documents:
            return []
        
        # Extraer scores
        scores = [doc["score"] for doc in documents]
        
        # Aplicar softmax para normalizar entre 0 y 1
        scores_exp = np.exp(scores)
        scores_sum = np.sum(scores_exp)
        softmax_scores = scores_exp / scores_sum if scores_sum > 0 else scores_exp
        
        # Actualizar documentos con scores calibrados
        calibrated_docs = []
        for doc, calibrated_score in zip(documents, softmax_scores):
            doc_copy = doc.copy()
            doc_copy["raw_score"] = doc_copy["score"]
            doc_copy["score"] = float(calibrated_score)
            calibrated_docs.append(doc_copy)
        
        return calibrated_docs


if __name__ == "__main__":
    # Ejemplo de uso
    print("Inicializando NeuralReranker...")
    reranker = NeuralReranker()
    
    # Ejemplo de re-ranking
    query = "¿Cuál es el procedimiento para solicitar viáticos?"
    documents = [
        {
            "id": "doc1",
            "text": "El procedimiento para solicitar viáticos requiere llenar el formulario F-01 y presentarlo a su jefe inmediato.",
            "score": 0.85,
            "rank": 2,
            "metadata": {"source": "Manual de Procedimientos", "page": 15}
        },
        {
            "id": "doc2",
            "text": "Los viáticos son asignaciones que se otorgan al personal para cubrir gastos de alimentación, hospedaje y movilidad.",
            "score": 0.92,
            "rank": 1,
            "metadata": {"source": "Directiva de Viáticos", "page": 3}
        },
        {
            "id": "doc3",
            "text": "Para solicitar vacaciones debe presentar el formulario correspondiente con 15 días de anticipación.",
            "score": 0.75,
            "rank": 3,
            "metadata": {"source": "Manual de RRHH", "page": 22}
        },
        {
            "id": "doc4",
            "text": "El proceso de rendición de viáticos debe realizarse dentro de los 10 días hábiles posteriores al retorno.",
            "score": 0.65,
            "rank": 4,
            "metadata": {"source": "Directiva de Viáticos", "page": 8}
        },
        {
            "id": "doc5",
            "text": "La solicitud de viáticos debe ser aprobada por el jefe de la unidad orgánica y la oficina de administración.",
            "score": 0.60,
            "rank": 5,
            "metadata": {"source": "Manual de Procedimientos", "page": 16}
        }
    ]
    
    print("\nRealizando re-ranking...")
    reranked_docs = reranker.rerank(query, documents, top_k=3)
    
    print(f"\nResultados re-rankeados para: '{query}'")
    for doc in reranked_docs:
        print(f"\nRank {doc['rank']} (Score: {doc['score']:.4f}, Original: {doc['original_score']:.4f}):")
        print(f"ID: {doc['id']}")
        print(f"Metadata: {doc['metadata']}")
        print(f"Texto: {doc['text']}")

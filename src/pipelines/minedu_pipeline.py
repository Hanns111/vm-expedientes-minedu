#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pipeline RAG específico para el dominio MINEDU.
Implementa la recuperación y generación de respuestas para consultas normativas del MINEDU.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from src.core.base_pipeline import BasePipeline
from src.config.rag_config import RAGConfig

# Importar componentes específicos
from src.ai.retrieval.retriever_dense_e5 import DenseRetrieverE5
from src.pipelines.retrieval.bm25_retriever import BM25Retriever
from src.pipelines.retrieval.dense_retriever_e5 import DenseRetrieverE5Adapter
from src.pipelines.retrieval.hybrid_fusion import HybridFusion
from src.ai.reranking.cross_encoder import NeuralReranker

# Configuración de logging
logger = logging.getLogger('MineduRAGPipeline')


class MineduRAGPipeline(BasePipeline):
    """
    Pipeline RAG específico para el dominio MINEDU.
    
    Implementa la recuperación y generación de respuestas para consultas normativas
    relacionadas con el Ministerio de Educación del Perú.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Inicializa el pipeline MINEDU.
        
        Args:
            config: Configuración del pipeline. Si es None, se usa la configuración por defecto.
        """
        config = config or RAGConfig()
        super().__init__(config)
        self.load_components()
        logger.info(f"Pipeline MINEDU inicializado con {len(self.components)} componentes")
    
    def load_components(self) -> None:
        """
        Carga los componentes del pipeline según la configuración.
        
        Implementa la carga de los componentes específicos para el dominio MINEDU:
        - BM25Retriever para recuperación léxica
        - DenseRetriever para recuperación semántica con E5-Large
        - HybridFusion para fusión de resultados
        - CrossEncoderReranker para reranking neural
        """
        start_time = time.time()
        
        try:
            # Cargar BM25 Retriever
            if self.config.bm25.enabled:
                logger.info("Cargando BM25Retriever...")
                self.components["bm25"] = BM25Retriever(
                    vectorstore_path=self.config.bm25.vectorstore_path,
                    top_k=self.config.bm25.top_k
                )
                logger.info("BM25Retriever cargado correctamente")
            
            # Cargar Dense Retriever (E5-Large)
            if self.config.dense_retrieval.enabled:
                logger.info("Cargando DenseRetrieverE5Adapter...")
                self.components["dense"] = DenseRetrieverE5Adapter(
                    model_name=self.config.dense_retrieval.model_name,
                    collection_name=self.config.dense_retrieval.collection_name,
                    persist_directory=self.config.dense_retrieval.persist_directory,
                    device=self.config.dense_retrieval.device
                )
                logger.info("DenseRetrieverE5Adapter cargado correctamente")
            
            # Cargar Hybrid Fusion
            if self.config.hybrid_fusion.enabled:
                logger.info("Cargando HybridFusion...")
                self.components["fusion"] = HybridFusion(
                    weights=self.config.hybrid_fusion.weights,
                    rrf_k=self.config.hybrid_fusion.rrf_k,
                    deduplicate=self.config.hybrid_fusion.deduplicate,
                    similarity_threshold=self.config.hybrid_fusion.similarity_threshold
                )
                logger.info("HybridFusion cargado correctamente")
            
            # Cargar Reranker
            if self.config.reranking.enabled:
                logger.info("Cargando NeuralReranker...")
                self.components["reranker"] = NeuralReranker(
                    model_name=self.config.reranking.model_name,
                    device=self.config.reranking.device
                )
                logger.info("NeuralReranker cargado correctamente")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Todos los componentes cargados en {elapsed_time:.2f} segundos")
            
        except Exception as e:
            logger.error(f"Error al cargar componentes: {str(e)}")
            raise
    
    def query(self, question: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una consulta en el pipeline MINEDU.
        
        Implementa el flujo completo de procesamiento:
        1. Recuperación con BM25
        2. Recuperación densa con E5-Large
        3. Fusión híbrida de resultados
        4. Reranking neural
        5. Extracción de entidades y construcción de respuesta
        
        Args:
            question: Pregunta o consulta del usuario
            **kwargs: Argumentos adicionales
                - top_k: Número de resultados a devolver (opcional)
                - include_metadata: Si se debe incluir metadatos en la respuesta (opcional)
                - rerank: Si se debe aplicar reranking (opcional)
                
        Returns:
            Respuesta estructurada con resultados y metadatos
        """
        start_time = time.time()
        logger.info(f"Procesando consulta: {question}")
        
        # Parámetros opcionales
        top_k = kwargs.get("top_k", self.config.reranking.top_k)
        include_metadata = kwargs.get("include_metadata", True)
        apply_rerank = kwargs.get("rerank", self.config.reranking.enabled)
        
        try:
            results = {}
            
            # 1. Recuperación BM25
            if "bm25" in self.components:
                bm25_start = time.time()
                bm25_results = self.components["bm25"].search(
                    question, top_k=self.config.bm25.top_k
                )
                bm25_time = time.time() - bm25_start
                results["bm25"] = bm25_results
                logger.debug(f"BM25 completado en {bm25_time:.4f} segundos")
            
            # 2. Recuperación densa
            if "dense" in self.components:
                dense_start = time.time()
                dense_results = self.components["dense"].search(
                    question, top_k=self.config.dense_retrieval.top_k
                )
                dense_time = time.time() - dense_start
                results["dense"] = dense_results
                logger.debug(f"Dense retrieval completado en {dense_time:.4f} segundos")
            
            # 3. Fusión híbrida
            if "fusion" in self.components and "bm25" in results and "dense" in results:
                fusion_start = time.time()
                fused_results = self.components["fusion"].fuse(
                    bm25_results=results["bm25"],
                    dense_results=results["dense"],
                    top_k=self.config.hybrid_fusion.top_k
                )
                fusion_time = time.time() - fusion_start
                results["fused"] = fused_results
                logger.debug(f"Hybrid fusion completado en {fusion_time:.4f} segundos")
            else:
                # Si no hay fusión, usar los resultados disponibles
                results["fused"] = results.get("dense", results.get("bm25", []))
            
            # 4. Reranking
            if apply_rerank and "reranker" in self.components and results["fused"]:
                rerank_start = time.time()
                reranked_results = self.components["reranker"].rerank(
                    query=question,
                    documents=results["fused"],
                    top_k=top_k,
                    score_threshold=self.config.reranking.score_threshold
                )
                rerank_time = time.time() - rerank_start
                results["reranked"] = reranked_results
                logger.debug(f"Reranking completado en {rerank_time:.4f} segundos")
                final_results = results["reranked"]
            else:
                # Si no hay reranking, usar los resultados fusionados
                final_results = results["fused"][:top_k] if results["fused"] else []
            
            # Tiempo total
            total_time = time.time() - start_time
            
            # Construir respuesta
            response = {
                "query": question,
                "results": final_results,
                "metadata": {
                    "time_taken": total_time,
                    "num_results": len(final_results),
                    "components_used": list(self.components.keys()),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
            
            # Incluir métricas detalladas si se solicita
            if include_metadata:
                response["metadata"]["metrics"] = {
                    "bm25_time": locals().get("bm25_time", 0),
                    "dense_time": locals().get("dense_time", 0),
                    "fusion_time": locals().get("fusion_time", 0),
                    "rerank_time": locals().get("rerank_time", 0),
                }
            
            logger.info(f"Consulta procesada en {total_time:.4f} segundos con {len(final_results)} resultados")
            return response
            
        except Exception as e:
            logger.error(f"Error al procesar consulta: {str(e)}")
            return {
                "query": question,
                "error": str(e),
                "results": [],
                "metadata": {
                    "time_taken": time.time() - start_time,
                    "error": True,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }
    
    def run_ablation_study(self, dataset_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Ejecuta un estudio de ablación completo para evaluar diferentes configuraciones.
        
        Args:
            dataset_path: Ruta al dataset de evaluación
            output_dir: Directorio donde guardar los resultados. Si es None, se usa el directorio por defecto.
            
        Returns:
            Resultados del estudio de ablación
        """
        output_dir = output_dir or os.path.join(self.config.metrics.export_path, "ablation_studies")
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Iniciando estudio de ablación con dataset {dataset_path}")
        results = {}
        
        # Configuración base
        base_config = self.config.model_copy(deep=True)
        
        # 1. Ablación de componentes (activar/desactivar)
        component_configs = [
            ("solo_bm25", {"bm25": True, "dense_retrieval": False, "reranking": False}),
            ("solo_dense", {"bm25": False, "dense_retrieval": True, "reranking": False}),
            ("bm25_dense_sin_reranking", {"bm25": True, "dense_retrieval": True, "reranking": False}),
            ("completo", {"bm25": True, "dense_retrieval": True, "reranking": True}),
        ]
        
        for name, components in component_configs:
            logger.info(f"Evaluando configuración: {name}")
            config = base_config.model_copy(deep=True)
            
            # Configurar componentes
            config.bm25.enabled = components["bm25"]
            config.dense_retrieval.enabled = components["dense_retrieval"]
            config.reranking.enabled = components["reranking"]
            
            # Crear pipeline con esta configuración
            pipeline = MineduRAGPipeline(config=config)
            
            # Evaluar
            eval_results = pipeline.evaluate(dataset_path)
            results[f"component_{name}"] = eval_results
            
            # Guardar resultados
            with open(os.path.join(output_dir, f"ablation_component_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(eval_results, f, indent=2, ensure_ascii=False)
        
        # 2. Ablación de parámetros de chunking
        chunk_sizes = [512, 1024, 2048]
        chunk_overlaps = [0, 100, 200]
        
        for size in chunk_sizes:
            for overlap in chunk_overlaps:
                name = f"chunk_size_{size}_overlap_{overlap}"
                logger.info(f"Evaluando configuración de chunking: {name}")
                
                config = base_config.model_copy(deep=True)
                config.chunking.chunk_size = size
                config.chunking.chunk_overlap = overlap
                
                # Crear pipeline con esta configuración
                pipeline = MineduRAGPipeline(config=config)
                
                # Evaluar
                eval_results = pipeline.evaluate(dataset_path)
                results[f"chunking_{name}"] = eval_results
                
                # Guardar resultados
                with open(os.path.join(output_dir, f"ablation_chunking_{name}.json"), "w", encoding="utf-8") as f:
                    json.dump(eval_results, f, indent=2, ensure_ascii=False)
        
        # 3. Ablación de pesos de fusión
        weight_configs = [
            ("bm25_dominante", {"bm25": 0.7, "dense": 0.3}),
            ("equilibrado", {"bm25": 0.5, "dense": 0.5}),
            ("dense_dominante", {"bm25": 0.3, "dense": 0.7}),
        ]
        
        for name, weights in weight_configs:
            logger.info(f"Evaluando configuración de pesos: {name}")
            
            config = base_config.model_copy(deep=True)
            config.hybrid_fusion.weights = weights
            
            # Crear pipeline con esta configuración
            pipeline = MineduRAGPipeline(config=config)
            
            # Evaluar
            eval_results = pipeline.evaluate(dataset_path)
            results[f"weights_{name}"] = eval_results
            
            # Guardar resultados
            with open(os.path.join(output_dir, f"ablation_weights_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(eval_results, f, indent=2, ensure_ascii=False)
        
        # Guardar resultados agregados
        with open(os.path.join(output_dir, "ablation_summary.json"), "w", encoding="utf-8") as f:
            summary = {}
            for key, result in results.items():
                if "aggregated" in result:
                    summary[key] = result["aggregated"]
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Estudio de ablación completado. Resultados guardados en {output_dir}")
        return results
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae entidades relevantes del texto.
        
        Args:
            text: Texto del cual extraer entidades
            
        Returns:
            Diccionario con entidades extraídas por categoría
        """
        # Esta es una implementación básica que se puede mejorar con NER específico para el dominio
        entities = {
            "montos": [],
            "fechas": [],
            "normas": [],
            "personas": [],
            "instituciones": [],
        }
        
        # Implementación simple basada en reglas
        # En una versión más avanzada, se usaría un modelo de NER específico para el dominio
        
        # Extraer montos (patrones como S/ 1,234.56 o 1,234.56 soles)
        import re
        monto_patterns = [r'S/\s?[\d,.]+', r'[\d,.]+\s?soles', r'[\d,.]+\s?nuevos soles']
        for pattern in monto_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities["montos"].extend(matches)
        
        # Extraer fechas (patrones como 01/01/2023 o 1 de enero de 2023)
        fecha_patterns = [r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{2,4}']
        for pattern in fecha_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities["fechas"].extend(matches)
        
        # Extraer normas (patrones como Ley N° 12345, Decreto Supremo 012-2023-PCM)
        norma_patterns = [r'(?:ley|decreto|resolución|directiva)\s+(?:n°|nro\.?|número)?\s*\d+[-\w]*', r'r\.\s*m\.\s*n°\s*\d+[-\w]*']
        for pattern in norma_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities["normas"].extend(matches)
        
        return entities


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear pipeline
    pipeline = MineduRAGPipeline()
    
    # Ejecutar consulta de ejemplo
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "¿Cuál es el monto máximo para viáticos nacionales?"
    
    print(f"\nConsulta: {query}")
    results = pipeline.query(query)
    
    print("\nResultados:")
    for i, result in enumerate(results.get("results", [])):
        print(f"\n{i+1}. {result.get('content', '')[:200]}...")
        print(f"   Score: {result.get('score', 0):.4f}")
        print(f"   Fuente: {result.get('metadata', {}).get('source', 'Desconocido')}")
    
    print(f"\nTiempo total: {results.get('metadata', {}).get('time_taken', 0):.4f} segundos")


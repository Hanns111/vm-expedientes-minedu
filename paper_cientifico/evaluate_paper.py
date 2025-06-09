#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de evaluación para el pipeline RAG de MINEDU.

Este script evalúa el rendimiento del pipeline RAG utilizando el dataset de evaluación
y calcula métricas de rendimiento como precisión, recall, F1, etc.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Importar métricas de evaluación
try:
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from ragas.metrics.critique import harmfulness
    RAGAS_AVAILABLE = True
except ImportError:
    print("RAGAS no está instalado. Se usarán métricas básicas.")
    RAGAS_AVAILABLE = False

# Importar pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.pipelines.minedu_pipeline import MineduRAGPipeline
from src.config.rag_config import RAGConfig

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('evaluate_paper')


class RAGEvaluator:
    """
    Evaluador para sistemas RAG.
    
    Implementa la evaluación de pipelines RAG utilizando diferentes métricas
    y datasets de evaluación.
    """
    
    def __init__(self, pipeline, metrics=None):
        """
        Inicializa el evaluador.
        
        Args:
            pipeline: Pipeline RAG a evaluar
            metrics: Lista de métricas a utilizar. Si es None, se usan las métricas por defecto.
        """
        self.pipeline = pipeline
        self.metrics = metrics or ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        logger.info(f"Evaluador inicializado con métricas: {self.metrics}")
    
    def evaluate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """
        Evalúa el pipeline con un dataset completo.
        
        Args:
            dataset_path: Ruta al dataset de evaluación
            
        Returns:
            Resultados de la evaluación
        """
        # Cargar dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        logger.info(f"Evaluando dataset con {len(dataset)} preguntas")
        
        results = []
        start_time = time.time()
        
        # Evaluar cada pregunta
        for i, item in enumerate(dataset):
            logger.info(f"Evaluando pregunta {i+1}/{len(dataset)}: {item['question']}")
            result = self.evaluate_question(item)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # Calcular métricas agregadas
        aggregated = self.aggregate_metrics(results)
        aggregated.update({
            "total_questions": len(dataset),
            "total_time": total_time,
            "avg_time_per_question": total_time / len(dataset) if dataset else 0,
            "timestamp": datetime.now().isoformat(),
        })
        
        logger.info(f"Evaluación completada en {total_time:.2f} segundos")
        
        return {
            "results": results,
            "aggregated": aggregated
        }
    
    def evaluate_question(self, question_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa una sola pregunta.
        
        Args:
            question_item: Item del dataset con la pregunta y respuesta esperada
            
        Returns:
            Resultados de la evaluación para esta pregunta
        """
        question = question_item["question"]
        ground_truth = question_item.get("ground_truth_answer", "")
        
        # Ejecutar consulta en el pipeline
        start_time = time.time()
        response = self.pipeline.query(question)
        query_time = time.time() - start_time
        
        # Extraer respuesta generada
        generated_answer = self.extract_answer(response)
        
        # Calcular métricas
        metrics_result = self.calculate_metrics(question, generated_answer, ground_truth, response)
        
        return {
            "query_id": question_item.get("query_id", ""),
            "question": question,
            "ground_truth": ground_truth,
            "generated_answer": generated_answer,
            "response": response,
            "metrics": metrics_result,
            "query_time": query_time,
            "timestamp": datetime.now().isoformat(),
        }
    
    def extract_answer(self, response: Dict[str, Any]) -> str:
        """
        Extrae la respuesta generada del resultado del pipeline.
        
        Args:
            response: Respuesta del pipeline
            
        Returns:
            Respuesta generada
        """
        # Esta implementación depende de la estructura de la respuesta del pipeline
        # En una versión más avanzada, se podría implementar un extractor más sofisticado
        
        if "results" in response and response["results"]:
            # Tomar el primer resultado como respuesta
            return response["results"][0].get("content", "")
        
        return ""
    
    def calculate_metrics(self, question: str, generated_answer: str, ground_truth: str, response: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula métricas de evaluación para una respuesta.
        
        Args:
            question: Pregunta original
            generated_answer: Respuesta generada por el pipeline
            ground_truth: Respuesta esperada (ground truth)
            response: Respuesta completa del pipeline
            
        Returns:
            Métricas calculadas
        """
        metrics_result = {}
        
        # Usar RAGAS si está disponible
        if RAGAS_AVAILABLE and "faithfulness" in self.metrics:
            try:
                import pandas as pd
                
                # Preparar datos para RAGAS
                data = {
                    "question": [question],
                    "answer": [generated_answer],
                    "ground_truth": [ground_truth],
                }
                
                # Añadir contextos si están disponibles
                if "results" in response:
                    contexts = [result.get("content", "") for result in response.get("results", [])]
                    data["contexts"] = [contexts]
                
                # Crear DataFrame
                df = pd.DataFrame(data)
                
                # Calcular métricas RAGAS
                if "faithfulness" in self.metrics:
                    metrics_result["faithfulness"] = faithfulness.score(df)["faithfulness"][0]
                
                if "answer_relevancy" in self.metrics:
                    metrics_result["answer_relevancy"] = answer_relevancy.score(df)["answer_relevancy"][0]
                
                if "context_precision" in self.metrics and "contexts" in data:
                    metrics_result["context_precision"] = context_precision.score(df)["context_precision"][0]
                
                if "context_recall" in self.metrics and "contexts" in data:
                    metrics_result["context_recall"] = context_recall.score(df)["context_recall"][0]
                
                if "harmfulness" in self.metrics:
                    metrics_result["harmfulness"] = harmfulness.score(df)["harmfulness"][0]
                    
            except Exception as e:
                logger.error(f"Error al calcular métricas RAGAS: {str(e)}")
        
        # Métricas básicas (siempre disponibles)
        # Exactitud exacta
        metrics_result["exact_match"] = 1.0 if generated_answer.lower() == ground_truth.lower() else 0.0
        
        # Solapamiento de tokens
        generated_tokens = set(generated_answer.lower().split())
        ground_truth_tokens = set(ground_truth.lower().split())
        
        if ground_truth_tokens:
            metrics_result["token_overlap"] = len(generated_tokens.intersection(ground_truth_tokens)) / len(ground_truth_tokens)
        else:
            metrics_result["token_overlap"] = 0.0
        
        # Longitud relativa
        if ground_truth:
            metrics_result["length_ratio"] = len(generated_answer) / len(ground_truth)
        else:
            metrics_result["length_ratio"] = 0.0
        
        return metrics_result
    
    def aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Agrega métricas de múltiples resultados.
        
        Args:
            results: Lista de resultados de evaluación
            
        Returns:
            Métricas agregadas
        """
        if not results:
            return {}
        
        # Recopilar todas las métricas disponibles
        all_metrics = set()
        for result in results:
            if "metrics" in result:
                all_metrics.update(result["metrics"].keys())
        
        # Calcular promedio para cada métrica
        aggregated = {}
        for metric in all_metrics:
            values = [result["metrics"].get(metric, 0.0) for result in results if "metrics" in result]
            if values:
                aggregated[f"avg_{metric}"] = sum(values) / len(values)
        
        # Calcular tiempo promedio
        query_times = [result.get("query_time", 0.0) for result in results]
        if query_times:
            aggregated["avg_query_time"] = sum(query_times) / len(query_times)
        
        return aggregated


def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Evaluar pipeline RAG de MINEDU")
    parser.add_argument("--dataset", type=str, default="paper_cientifico/dataset/golden_dataset.json",
                        help="Ruta al dataset de evaluación")
    parser.add_argument("--config", type=str, default=None,
                        help="Ruta a la configuración del pipeline (YAML)")
    parser.add_argument("--output", type=str, default="paper_cientifico/results/evaluation_results.json",
                        help="Ruta para guardar los resultados")
    parser.add_argument("--ablation", action="store_true",
                        help="Ejecutar estudio de ablación")
    
    args = parser.parse_args()
    
    # Cargar configuración si se especifica
    config = None
    if args.config:
        config = RAGConfig.from_yaml(args.config)
    
    # Crear pipeline
    pipeline = MineduRAGPipeline(config=config)
    
    # Crear evaluador
    evaluator = RAGEvaluator(pipeline)
    
    if args.ablation:
        # Ejecutar estudio de ablación
        logger.info("Ejecutando estudio de ablación...")
        results = pipeline.run_ablation_study(args.dataset)
        
        # Guardar resultados
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Resultados del estudio de ablación guardados en {args.output}")
    else:
        # Evaluar dataset
        logger.info(f"Evaluando dataset {args.dataset}...")
        results = evaluator.evaluate_dataset(args.dataset)
        
        # Guardar resultados
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Resultados guardados en {args.output}")
        
        # Mostrar resumen
        print("\nResumen de la evaluación:")
        for metric, value in results["aggregated"].items():
            if isinstance(value, (int, float)):
                print(f"{metric}: {value:.4f}")
            else:
                print(f"{metric}: {value}")


if __name__ == "__main__":
    import sys
    main()

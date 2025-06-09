#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de prueba simplificado para el framework de evaluación RAG de MINEDU.

Este script simula un pipeline RAG básico para probar el flujo de evaluación
sin depender de componentes que aún no están completamente implementados.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import json
import time
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_test')


class SimpleMockPipeline:
    """
    Pipeline RAG simplificado para pruebas.
    
    Esta clase simula el comportamiento básico de un pipeline RAG
    para probar el flujo de evaluación sin dependencias complejas.
    """
    
    def __init__(self, config_path=None):
        """
        Inicializa el pipeline simplificado.
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}
        self.metrics = {"latency": {}, "memory": {}, "tokens": {}}
        logger.info("Pipeline simplificado inicializado")
        
        # Cargar corpus de ejemplo para respuestas
        self.corpus = [
            "Los viáticos nacionales tienen un monto máximo de S/ 320.00 por día según la escala vigente.",
            "El plazo para presentar la rendición de cuentas es de 10 días hábiles contados desde la culminación de la comisión.",
            "Para solicitar viáticos se requiere memorando de autorización, planilla de viáticos y formato de declaración jurada.",
            "Los viáticos para servidores públicos están regulados por el Decreto Supremo N° 007-2013-EF.",
            "Las solicitudes de viáticos son aprobadas por el jefe inmediato del comisionado y el Director de Administración.",
            "Los viáticos internacionales para Europa tienen un monto máximo de US$ 540.00 por día según la escala vigente.",
            "No son reembolsables los gastos de bar, bebidas alcohólicas, lavado de ropa, llamadas no oficiales y propinas.",
            "Para ampliación de viáticos se debe presentar solicitud justificada al jefe con 24 horas de anticipación.",
            "Las sanciones por no presentar rendición incluyen descuento en planilla e impedimento para nuevas comisiones.",
            "Una comisión urgente es aquella imprevista y no programada con anticipación mínima de 24 horas."
        ]
    
    def _load_config(self):
        """
        Carga la configuración desde un archivo YAML.
        
        Returns:
            Configuración cargada
        """
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuración cargada desde {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error al cargar configuración: {str(e)}")
            return {}
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Procesa una consulta y devuelve resultados.
        
        Args:
            question: Pregunta a procesar
            
        Returns:
            Resultados de la consulta
        """
        start_time = time.time()
        logger.info(f"Procesando consulta: {question}")
        
        # Simular latencia de procesamiento
        time.sleep(random.uniform(0.5, 1.5))
        
        # Simular búsqueda en corpus
        results = self._mock_search(question)
        
        # Calcular métricas
        query_time = time.time() - start_time
        
        # Preparar respuesta
        response = {
            "question": question,
            "results": results,
            "metrics": {
                "latency": {
                    "total": query_time,
                    "retrieval": query_time * 0.7,
                    "processing": query_time * 0.3
                },
                "components_used": ["bm25_retriever"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Consulta procesada en {query_time:.2f} segundos")
        return response
    
    def _mock_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Simula una búsqueda en el corpus.
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Resultados de la búsqueda
        """
        # Palabras clave para búsqueda simple
        keywords = query.lower().split()
        
        # Calcular puntuaciones simples basadas en coincidencia de palabras
        scored_results = []
        for i, text in enumerate(self.corpus):
            score = 0
            for keyword in keywords:
                if keyword in text.lower():
                    score += 0.1
            
            if score > 0:
                scored_results.append({
                    "content": text,
                    "score": min(0.95, score),
                    "metadata": {
                        "source": f"documento_{i+1}.txt",
                        "chunk_id": f"chunk_{i+1}"
                    }
                })
        
        # Ordenar por puntuación
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Limitar a los 5 mejores resultados
        return scored_results[:5]
    
    def evaluate(self, dataset_path: str) -> Dict[str, Any]:
        """
        Evalúa el pipeline con un dataset.
        
        Args:
            dataset_path: Ruta al dataset de evaluación
            
        Returns:
            Resultados de la evaluación
        """
        # Cargar dataset
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            logger.info(f"Dataset cargado: {len(dataset)} preguntas")
        except Exception as e:
            logger.error(f"Error al cargar dataset: {str(e)}")
            return {"error": str(e)}
        
        # Evaluar cada pregunta
        results = []
        start_time = time.time()
        
        for i, item in enumerate(dataset):
            logger.info(f"Evaluando pregunta {i+1}/{len(dataset)}: {item['question']}")
            
            # Procesar consulta
            query_result = self.query(item["question"])
            
            # Calcular métricas básicas
            metrics = self._calculate_metrics(query_result, item)
            
            # Guardar resultado
            results.append({
                "query_id": item.get("query_id", f"Q{i+1}"),
                "question": item["question"],
                "ground_truth": item.get("ground_truth_answer", ""),
                "generated_answer": self._extract_answer(query_result),
                "response": query_result,
                "metrics": metrics,
                "query_time": query_result["metrics"]["latency"]["total"]
            })
        
        # Calcular métricas agregadas
        total_time = time.time() - start_time
        aggregated = self._aggregate_metrics(results)
        aggregated.update({
            "total_questions": len(dataset),
            "total_time": total_time,
            "avg_time_per_question": total_time / len(dataset) if dataset else 0
        })
        
        return {
            "results": results,
            "aggregated": aggregated
        }
    
    def _extract_answer(self, response: Dict[str, Any]) -> str:
        """
        Extrae la respuesta generada del resultado.
        
        Args:
            response: Respuesta del pipeline
            
        Returns:
            Respuesta generada
        """
        if "results" in response and response["results"]:
            return response["results"][0]["content"]
        return ""
    
    def _calculate_metrics(self, response: Dict[str, Any], ground_truth_item: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula métricas de evaluación.
        
        Args:
            response: Respuesta del pipeline
            ground_truth_item: Item con la respuesta esperada
            
        Returns:
            Métricas calculadas
        """
        metrics = {}
        
        # Extraer respuesta generada y esperada
        generated_answer = self._extract_answer(response)
        ground_truth = ground_truth_item.get("ground_truth_answer", "")
        
        # Exactitud exacta
        metrics["exact_match"] = 1.0 if generated_answer.lower() == ground_truth.lower() else 0.0
        
        # Solapamiento de tokens
        generated_tokens = set(generated_answer.lower().split())
        ground_truth_tokens = set(ground_truth.lower().split())
        
        if ground_truth_tokens:
            metrics["token_overlap"] = len(generated_tokens.intersection(ground_truth_tokens)) / len(ground_truth_tokens)
        else:
            metrics["token_overlap"] = 0.0
        
        # Longitud relativa
        if ground_truth:
            metrics["length_ratio"] = len(generated_answer) / len(ground_truth)
        else:
            metrics["length_ratio"] = 0.0
        
        return metrics
    
    def _aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Agrega métricas de múltiples resultados.
        
        Args:
            results: Lista de resultados
            
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
    
    def run_ablation_study(self, dataset_path: str) -> Dict[str, Any]:
        """
        Ejecuta un estudio de ablación simplificado.
        
        Args:
            dataset_path: Ruta al dataset de evaluación
            
        Returns:
            Resultados del estudio de ablación
        """
        logger.info(f"Ejecutando estudio de ablación con dataset: {dataset_path}")
        
        # Configuraciones de ablación simuladas
        configs = [
            {"name": "baseline", "latency_factor": 1.0, "score_factor": 1.0},
            {"name": "fast_retrieval", "latency_factor": 0.7, "score_factor": 0.9},
            {"name": "high_precision", "latency_factor": 1.3, "score_factor": 1.1}
        ]
        
        # Ejecutar evaluación para cada configuración
        ablation_results = {}
        
        for config in configs:
            logger.info(f"Evaluando configuración: {config['name']}")
            
            # Ajustar factores para esta configuración
            self._ablation_config = config
            
            # Ejecutar evaluación
            results = self.evaluate(dataset_path)
            
            # Guardar resultados
            ablation_results[config["name"]] = results
        
        # Restaurar configuración original
        self._ablation_config = None
        
        return {
            "ablation_results": ablation_results,
            "timestamp": datetime.now().isoformat()
        }


def main():
    """
    Función principal.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba simplificada del framework de evaluación RAG")
    parser.add_argument("--config", type=str, default=None,
                        help="Ruta al archivo de configuración (opcional)")
    parser.add_argument("--dataset", type=str, default="paper_cientifico/dataset/golden_dataset.json",
                        help="Ruta al dataset de evaluación")
    parser.add_argument("--output", type=str, default="paper_cientifico/results/test_results.json",
                        help="Ruta para guardar los resultados")
    parser.add_argument("--ablation", action="store_true",
                        help="Ejecutar estudio de ablación")
    parser.add_argument("--query", type=str, default=None,
                        help="Ejecutar una consulta específica")
    
    args = parser.parse_args()
    
    # Crear pipeline simplificado
    pipeline = SimpleMockPipeline(args.config)
    
    if args.query:
        # Ejecutar consulta específica
        result = pipeline.query(args.query)
        
        # Mostrar resultado
        print("\n=== RESULTADO DE LA CONSULTA ===")
        if "results" in result and result["results"]:
            for i, res in enumerate(result["results"]):
                print(f"\nResultado {i+1}:")
                print(f"Contenido: {res.get('content', '')}")
                print(f"Puntuación: {res.get('score', 0):.4f}")
                print(f"Fuente: {res.get('metadata', {}).get('source', 'Desconocida')}")
        
        # Guardar resultado
        output_path = "paper_cientifico/results/query_result.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResultado guardado en {output_path}")
        
    elif args.ablation:
        # Ejecutar estudio de ablación
        results = pipeline.run_ablation_study(args.dataset)
        
        # Guardar resultados
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultados del estudio de ablación guardados en {args.output}")
        
    else:
        # Evaluar dataset completo
        results = pipeline.evaluate(args.dataset)
        
        # Guardar resultados
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        print("\n=== RESUMEN DE LA EVALUACIÓN ===")
        print(f"Total de preguntas evaluadas: {results['aggregated']['total_questions']}")
        print(f"Tiempo total: {results['aggregated']['total_time']:.2f} segundos")
        print(f"Tiempo promedio por pregunta: {results['aggregated']['avg_time_per_question']:.2f} segundos")
        
        print("\nMétricas agregadas:")
        for metric, value in results["aggregated"].items():
            if metric.startswith("avg_") and isinstance(value, (int, float)):
                print(f"- {metric}: {value:.4f}")
        
        print(f"\nResultados completos guardados en {args.output}")


if __name__ == "__main__":
    # Crear directorio de resultados si no existe
    os.makedirs("paper_cientifico/results", exist_ok=True)
    main()

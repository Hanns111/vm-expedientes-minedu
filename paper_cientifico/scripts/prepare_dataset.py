#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para preparación y enriquecimiento del dataset de evaluación.

Este script procesa el dataset de evaluación (golden dataset) y lo enriquece
con información adicional para facilitar la evaluación con métricas RAGAS
y otros análisis científicos.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import json
import argparse
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('prepare_dataset')


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Carga el dataset desde un archivo JSON.
    
    Args:
        dataset_path: Ruta al archivo del dataset
        
    Returns:
        Dataset cargado
    """
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_dataset(dataset: List[Dict[str, Any]], output_path: str):
    """
    Guarda el dataset en un archivo JSON.
    
    Args:
        dataset: Dataset a guardar
        output_path: Ruta donde guardar el dataset
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)


def convert_to_ragas_format(dataset: List[Dict[str, Any]], corpus_path: Optional[str] = None) -> pd.DataFrame:
    """
    Convierte el dataset al formato requerido por RAGAS.
    
    Args:
        dataset: Dataset a convertir
        corpus_path: Ruta opcional al corpus de documentos
        
    Returns:
        DataFrame en formato RAGAS
    """
    # Cargar corpus si se proporciona
    corpus_chunks = {}
    if corpus_path and os.path.exists(corpus_path):
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
            for chunk_id, chunk_content in corpus_data.items():
                corpus_chunks[chunk_id] = chunk_content
    
    # Preparar datos para RAGAS
    ragas_data = []
    for item in dataset:
        question = item["question"]
        ground_truth = item.get("ground_truth_answer", "")
        
        # Obtener contextos de soporte si están disponibles
        contexts = []
        if "supporting_chunks" in item and corpus_chunks:
            for chunk_id in item["supporting_chunks"]:
                if chunk_id in corpus_chunks:
                    contexts.append(corpus_chunks[chunk_id])
        
        ragas_data.append({
            "question": question,
            "ground_truth": ground_truth,
            "contexts": contexts if contexts else None,
            "query_id": item.get("query_id", ""),
            "category": item.get("category", "")
        })
    
    return pd.DataFrame(ragas_data)


def enrich_dataset(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enriquece el dataset con información adicional para evaluación.
    
    Args:
        dataset: Dataset a enriquecer
        
    Returns:
        Dataset enriquecido
    """
    enriched_dataset = []
    
    for item in dataset:
        # Copiar item original
        enriched_item = item.copy()
        
        # Añadir información de dificultad si no existe
        if "metadata" not in enriched_item:
            enriched_item["metadata"] = {}
        
        if "difficulty" not in enriched_item["metadata"]:
            # Determinar dificultad basada en longitud de la pregunta y entidades requeridas
            question_length = len(item["question"])
            entities_required = len(enriched_item["metadata"].get("entities_required", []))
            
            if question_length < 50 and entities_required <= 2:
                enriched_item["metadata"]["difficulty"] = "easy"
            elif question_length > 100 or entities_required >= 4:
                enriched_item["metadata"]["difficulty"] = "hard"
            else:
                enriched_item["metadata"]["difficulty"] = "medium"
        
        # Añadir tipo de consulta si no existe
        if "query_type" not in enriched_item["metadata"]:
            # Determinar tipo de consulta basado en palabras clave
            question = item["question"].lower()
            
            if any(word in question for word in ["qué", "cuál", "cuánto", "cuántos", "dónde"]):
                enriched_item["metadata"]["query_type"] = "factual"
            elif any(word in question for word in ["cómo", "procedimiento", "proceso"]):
                enriched_item["metadata"]["query_type"] = "procedural"
            elif any(word in question for word in ["por qué", "razón", "motivo"]):
                enriched_item["metadata"]["query_type"] = "explanation"
            else:
                enriched_item["metadata"]["query_type"] = "other"
        
        enriched_dataset.append(enriched_item)
    
    return enriched_dataset


def analyze_dataset(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analiza el dataset y genera estadísticas.
    
    Args:
        dataset: Dataset a analizar
        
    Returns:
        Estadísticas del dataset
    """
    stats = {
        "total_questions": len(dataset),
        "categories": {},
        "difficulties": {},
        "query_types": {},
        "avg_question_length": 0,
        "avg_answer_length": 0
    }
    
    total_question_length = 0
    total_answer_length = 0
    
    for item in dataset:
        # Contabilizar categorías
        category = item.get("category", "unknown")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        # Contabilizar dificultades
        if "metadata" in item and "difficulty" in item["metadata"]:
            difficulty = item["metadata"]["difficulty"]
            stats["difficulties"][difficulty] = stats["difficulties"].get(difficulty, 0) + 1
        
        # Contabilizar tipos de consulta
        if "metadata" in item and "query_type" in item["metadata"]:
            query_type = item["metadata"]["query_type"]
            stats["query_types"][query_type] = stats["query_types"].get(query_type, 0) + 1
        
        # Calcular longitudes
        total_question_length += len(item["question"])
        total_answer_length += len(item.get("ground_truth_answer", ""))
    
    # Calcular promedios
    if dataset:
        stats["avg_question_length"] = total_question_length / len(dataset)
        stats["avg_answer_length"] = total_answer_length / len(dataset)
    
    return stats


def generate_dataset_report(stats: Dict[str, Any], output_path: str):
    """
    Genera un informe sobre el dataset en formato Markdown.
    
    Args:
        stats: Estadísticas del dataset
        output_path: Ruta donde guardar el informe
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Título y fecha
        f.write(f"# Informe del Dataset de Evaluación\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Estadísticas generales
        f.write("## Estadísticas Generales\n\n")
        f.write(f"- Total de preguntas: {stats['total_questions']}\n")
        f.write(f"- Longitud promedio de preguntas: {stats['avg_question_length']:.2f} caracteres\n")
        f.write(f"- Longitud promedio de respuestas: {stats['avg_answer_length']:.2f} caracteres\n\n")
        
        # Distribución por categoría
        f.write("## Distribución por Categoría\n\n")
        f.write("| Categoría | Cantidad | Porcentaje |\n")
        f.write("|-----------|----------|------------|\n")
        
        for category, count in stats["categories"].items():
            percentage = (count / stats["total_questions"]) * 100
            f.write(f"| {category} | {count} | {percentage:.2f}% |\n")
        
        # Distribución por dificultad
        f.write("\n## Distribución por Dificultad\n\n")
        f.write("| Dificultad | Cantidad | Porcentaje |\n")
        f.write("|------------|----------|------------|\n")
        
        total_with_difficulty = sum(stats["difficulties"].values())
        for difficulty, count in stats["difficulties"].items():
            percentage = (count / total_with_difficulty) * 100 if total_with_difficulty > 0 else 0
            f.write(f"| {difficulty} | {count} | {percentage:.2f}% |\n")
        
        # Distribución por tipo de consulta
        f.write("\n## Distribución por Tipo de Consulta\n\n")
        f.write("| Tipo de Consulta | Cantidad | Porcentaje |\n")
        f.write("|------------------|----------|------------|\n")
        
        total_with_query_type = sum(stats["query_types"].values())
        for query_type, count in stats["query_types"].items():
            percentage = (count / total_with_query_type) * 100 if total_with_query_type > 0 else 0
            f.write(f"| {query_type} | {count} | {percentage:.2f}% |\n")
        
        # Recomendaciones
        f.write("\n## Recomendaciones\n\n")
        
        # Verificar balance de categorías
        categories = list(stats["categories"].values())
        if max(categories) > 2 * min(categories):
            f.write("- **Desbalance de categorías**: Considerar añadir más preguntas a las categorías menos representadas.\n")
        
        # Verificar balance de dificultades
        if "difficulties" in stats and stats["difficulties"]:
            difficulties = list(stats["difficulties"].values())
            if max(difficulties) > 2 * min(difficulties):
                f.write("- **Desbalance de dificultades**: Considerar equilibrar la distribución de dificultades.\n")
        
        # Verificar longitud de preguntas
        if stats["avg_question_length"] < 30:
            f.write("- **Preguntas cortas**: Considerar hacer las preguntas más descriptivas y detalladas.\n")
        elif stats["avg_question_length"] > 150:
            f.write("- **Preguntas muy largas**: Considerar simplificar algunas preguntas para mayor claridad.\n")


def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Preparar dataset de evaluación para pipeline RAG")
    parser.add_argument("--input", type=str, default="paper_cientifico/dataset/golden_dataset.json",
                        help="Ruta al dataset de entrada")
    parser.add_argument("--output", type=str, default="paper_cientifico/dataset/enriched_dataset.json",
                        help="Ruta para guardar el dataset enriquecido")
    parser.add_argument("--corpus", type=str, default=None,
                        help="Ruta al corpus de documentos (opcional)")
    parser.add_argument("--ragas-output", type=str, default="paper_cientifico/dataset/ragas_dataset.csv",
                        help="Ruta para guardar el dataset en formato RAGAS")
    parser.add_argument("--report", type=str, default="paper_cientifico/dataset/dataset_report.md",
                        help="Ruta para guardar el informe del dataset")
    
    args = parser.parse_args()
    
    # Cargar dataset
    logger.info(f"Cargando dataset desde {args.input}...")
    dataset = load_dataset(args.input)
    
    # Enriquecer dataset
    logger.info("Enriqueciendo dataset...")
    enriched_dataset = enrich_dataset(dataset)
    
    # Guardar dataset enriquecido
    logger.info(f"Guardando dataset enriquecido en {args.output}...")
    save_dataset(enriched_dataset, args.output)
    
    # Convertir a formato RAGAS
    logger.info(f"Convirtiendo dataset a formato RAGAS...")
    ragas_df = convert_to_ragas_format(enriched_dataset, args.corpus)
    
    # Guardar dataset en formato RAGAS
    logger.info(f"Guardando dataset en formato RAGAS en {args.ragas_output}...")
    os.makedirs(os.path.dirname(args.ragas_output), exist_ok=True)
    ragas_df.to_csv(args.ragas_output, index=False)
    
    # Analizar dataset y generar informe
    logger.info("Analizando dataset...")
    stats = analyze_dataset(enriched_dataset)
    
    logger.info(f"Generando informe en {args.report}...")
    generate_dataset_report(stats, args.report)
    
    logger.info("Proceso completado con éxito.")


if __name__ == "__main__":
    main()

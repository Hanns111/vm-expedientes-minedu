#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para analizar la composición del dataset dorado.
Identifica categorías, tipos de consultas y distribución de dificultad.
"""

import os
import sys
import json
import logging
from collections import Counter
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("analyze_dataset")

def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Carga el dataset desde un archivo JSON."""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        logger.info(f"Dataset cargado correctamente: {len(dataset)} preguntas")
        return dataset
    except Exception as e:
        logger.error(f"Error al cargar el dataset: {e}")
        sys.exit(1)

def analyze_categories(dataset: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analiza las categorías presentes en el dataset."""
    categories = [item.get("category", "unknown") for item in dataset]
    category_counts = Counter(categories)
    logger.info(f"Categorías encontradas: {dict(category_counts)}")
    return dict(category_counts)

def analyze_query_types(dataset: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analiza los tipos de consulta presentes en el dataset."""
    query_types = [item.get("metadata", {}).get("query_type", "unknown") for item in dataset]
    query_type_counts = Counter(query_types)
    logger.info(f"Tipos de consulta encontrados: {dict(query_type_counts)}")
    return dict(query_type_counts)

def analyze_difficulty(dataset: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analiza los niveles de dificultad presentes en el dataset."""
    difficulties = [item.get("metadata", {}).get("difficulty", "unknown") for item in dataset]
    difficulty_counts = Counter(difficulties)
    logger.info(f"Niveles de dificultad encontrados: {dict(difficulty_counts)}")
    return dict(difficulty_counts)

def analyze_entities(dataset: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analiza las entidades requeridas en el dataset."""
    all_entities = []
    for item in dataset:
        entities = item.get("metadata", {}).get("entities_required", [])
        all_entities.extend(entities)
    
    entity_counts = Counter(all_entities)
    top_entities = dict(entity_counts.most_common(10))
    logger.info(f"Top 10 entidades requeridas: {top_entities}")
    return dict(entity_counts)

def generate_visualizations(
    categories: Dict[str, int], 
    query_types: Dict[str, int], 
    difficulties: Dict[str, int],
    output_dir: str
):
    """Genera visualizaciones de los análisis."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear visualizaciones
    plt.figure(figsize=(10, 6))
    plt.bar(categories.keys(), categories.values())
    plt.title("Distribución de Categorías")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "categories_distribution.png"))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    plt.bar(query_types.keys(), query_types.values())
    plt.title("Distribución de Tipos de Consulta")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "query_types_distribution.png"))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    plt.bar(difficulties.keys(), difficulties.values())
    plt.title("Distribución de Niveles de Dificultad")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "difficulty_distribution.png"))
    plt.close()
    
    logger.info(f"Visualizaciones guardadas en {output_dir}")

def identify_underrepresented_categories(categories: Dict[str, int], query_types: Dict[str, int]) -> Dict[str, List[str]]:
    """Identifica categorías y tipos de consulta subrepresentados."""
    underrepresented = {}
    
    # Categorías con menos de 2 preguntas
    underrepresented["categories"] = [cat for cat, count in categories.items() if count < 2]
    
    # Tipos de consulta con menos de 3 preguntas
    underrepresented["query_types"] = [qtype for qtype, count in query_types.items() if count < 3]
    
    logger.info(f"Categorías subrepresentadas: {underrepresented['categories']}")
    logger.info(f"Tipos de consulta subrepresentados: {underrepresented['query_types']}")
    
    return underrepresented

def generate_report(
    dataset: List[Dict[str, Any]], 
    categories: Dict[str, int], 
    query_types: Dict[str, int], 
    difficulties: Dict[str, int],
    entities: Dict[str, int],
    underrepresented: Dict[str, List[str]],
    output_path: str
):
    """Genera un informe de análisis del dataset."""
    report = {
        "total_questions": len(dataset),
        "categories": categories,
        "query_types": query_types,
        "difficulties": difficulties,
        "top_10_entities": dict(Counter(entities).most_common(10)),
        "underrepresented": underrepresented,
        "recommendations": {
            "new_categories": underrepresented["categories"],
            "focus_query_types": underrepresented["query_types"],
            "suggested_entities": [entity for entity, count in entities.items() if count == 1][:5]
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Informe de análisis guardado en {output_path}")
    
    # Generar también una versión en Markdown para mejor legibilidad
    md_output_path = output_path.replace('.json', '.md')
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write("# Análisis del Dataset Dorado\n\n")
        f.write(f"## Estadísticas Generales\n\n")
        f.write(f"- Total de preguntas: {len(dataset)}\n\n")
        
        f.write("## Distribución de Categorías\n\n")
        for cat, count in categories.items():
            f.write(f"- {cat}: {count} preguntas ({count/len(dataset)*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## Distribución de Tipos de Consulta\n\n")
        for qtype, count in query_types.items():
            f.write(f"- {qtype}: {count} preguntas ({count/len(dataset)*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## Distribución de Niveles de Dificultad\n\n")
        for diff, count in difficulties.items():
            f.write(f"- {diff}: {count} preguntas ({count/len(dataset)*100:.1f}%)\n")
        f.write("\n")
        
        f.write("## Top 10 Entidades Requeridas\n\n")
        for entity, count in Counter(entities).most_common(10):
            f.write(f"- {entity}: {count} menciones\n")
        f.write("\n")
        
        f.write("## Categorías Subrepresentadas\n\n")
        for cat in underrepresented["categories"]:
            f.write(f"- {cat}\n")
        f.write("\n")
        
        f.write("## Tipos de Consulta Subrepresentados\n\n")
        for qtype in underrepresented["query_types"]:
            f.write(f"- {qtype}\n")
        f.write("\n")
        
        f.write("## Recomendaciones para Expansión del Dataset\n\n")
        f.write("### Nuevas Categorías a Priorizar\n\n")
        for cat in underrepresented["categories"]:
            f.write(f"- {cat}\n")
        f.write("\n")
        
        f.write("### Tipos de Consulta a Priorizar\n\n")
        for qtype in underrepresented["query_types"]:
            f.write(f"- {qtype}\n")
        f.write("\n")
        
        f.write("### Entidades Sugeridas para Nuevas Preguntas\n\n")
        for entity in [entity for entity, count in entities.items() if count == 1][:5]:
            f.write(f"- {entity}\n")
    
    logger.info(f"Informe de análisis en formato Markdown guardado en {md_output_path}")

def main():
    # Definir rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "dataset", "golden_dataset.json")
    output_dir = os.path.join(base_dir, "results", "dataset_analysis")
    report_path = os.path.join(output_dir, "dataset_analysis_report.json")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Cargar dataset
    dataset = load_dataset(dataset_path)
    
    # Realizar análisis
    categories = analyze_categories(dataset)
    query_types = analyze_query_types(dataset)
    difficulties = analyze_difficulty(dataset)
    entities = analyze_entities(dataset)
    
    # Identificar categorías subrepresentadas
    underrepresented = identify_underrepresented_categories(categories, query_types)
    
    # Generar visualizaciones
    generate_visualizations(categories, query_types, difficulties, output_dir)
    
    # Generar informe
    generate_report(dataset, categories, query_types, difficulties, entities, underrepresented, report_path)
    
    logger.info("Análisis del dataset completado con éxito")

if __name__ == "__main__":
    main()

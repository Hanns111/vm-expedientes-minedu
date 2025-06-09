#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para expandir el dataset dorado con nuevas preguntas.
Toma como base el plan de expansión y genera el formato JSON adecuado.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("expand_dataset")

# Nuevas preguntas según el plan de expansión
NEW_QUESTIONS = [
    # Categoría: Sanciones
    {
        "query_id": "Q021",
        "question": "¿Qué sanciones se aplican por no presentar la rendición de cuentas a tiempo?",
        "category": "sanciones",
        "ground_truth_answer": "Las sanciones incluyen amonestación escrita, suspensión sin goce de haber y posible apertura de proceso administrativo disciplinario según la gravedad y reincidencia.",
        "supporting_chunks": ["chunk_090", "chunk_091"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "consequence",
            "entities_required": ["sanciones", "rendición", "plazo"]
        }
    },
    {
        "query_id": "Q022",
        "question": "¿Cuáles son las consecuencias de declarar gastos falsos en una comisión de servicios?",
        "category": "sanciones",
        "ground_truth_answer": "Constituye falta grave que puede derivar en proceso administrativo disciplinario, devolución del íntegro del monto y posibles acciones penales por falsedad documental.",
        "supporting_chunks": ["chunk_092", "chunk_093"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "consequence",
            "entities_required": ["consecuencias", "gastos falsos", "comisión"]
        }
    },
    {
        "query_id": "Q023",
        "question": "¿Qué norma establece las sanciones por mal uso de viáticos?",
        "category": "sanciones",
        "ground_truth_answer": "Ley N° 30057, Ley del Servicio Civil y su Reglamento, en concordancia con la Directiva de Tesorería y la Directiva específica de viáticos del MINEDU.",
        "supporting_chunks": ["chunk_094"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "reference",
            "entities_required": ["norma", "sanciones", "viáticos"]
        }
    },
    {
        "query_id": "Q024",
        "question": "¿Quién es responsable de aplicar sanciones por incumplimiento en rendiciones de viáticos?",
        "category": "sanciones",
        "ground_truth_answer": "El jefe inmediato inicia el proceso y la Secretaría Técnica de Procedimientos Administrativos Disciplinarios evalúa y recomienda la sanción, que es aplicada por el órgano competente según la gravedad.",
        "supporting_chunks": ["chunk_095", "chunk_096"],
        "metadata": {
            "difficulty": "hard",
            "query_type": "responsibility",
            "entities_required": ["responsable", "sanciones", "rendición", "viáticos"]
        }
    },
    
    # Categoría: Definiciones
    {
        "query_id": "Q025",
        "question": "¿Qué se considera como 'comisión de servicios' según la normativa del MINEDU?",
        "category": "definiciones",
        "ground_truth_answer": "Es el desplazamiento temporal del servidor fuera de la sede habitual de trabajo, dispuesto por la autoridad competente, para realizar funciones según la necesidad institucional y que estén relacionadas con los objetivos del MINEDU.",
        "supporting_chunks": ["chunk_097"],
        "metadata": {
            "difficulty": "easy",
            "query_type": "definition",
            "entities_required": ["comisión de servicios", "definición"]
        }
    },
    {
        "query_id": "Q026",
        "question": "¿Cómo se define 'viático' en la normativa de viajes oficiales?",
        "category": "definiciones",
        "ground_truth_answer": "Asignación económica que se otorga al servidor para cubrir gastos de alimentación, hospedaje y movilidad (hacia y desde el lugar de embarque), así como la movilidad utilizada para el desplazamiento en el lugar donde se realiza la comisión.",
        "supporting_chunks": ["chunk_098"],
        "metadata": {
            "difficulty": "easy",
            "query_type": "definition",
            "entities_required": ["viático", "definición"]
        }
    },
    {
        "query_id": "Q027",
        "question": "¿Qué se entiende por 'rendición de cuentas documentada' en el contexto de viáticos?",
        "category": "definiciones",
        "ground_truth_answer": "Presentación de comprobantes de pago (facturas, boletas, tickets) y declaración jurada que sustentan los gastos realizados durante la comisión de servicios, debidamente firmados por el comisionado y visados por el jefe inmediato.",
        "supporting_chunks": ["chunk_099"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "definition",
            "entities_required": ["rendición de cuentas documentada", "definición"]
        }
    },
    {
        "query_id": "Q028",
        "question": "¿Cuál es la definición de 'declaración jurada de gastos' según la normativa?",
        "category": "definiciones",
        "ground_truth_answer": "Documento mediante el cual el comisionado declara bajo juramento haber efectuado gastos en lugares donde no es posible obtener comprobantes de pago reconocidos, hasta por un máximo del 30% del monto total asignado para viáticos.",
        "supporting_chunks": ["chunk_100"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "definition",
            "entities_required": ["declaración jurada", "definición"]
        }
    },
    
    # Continuar con las demás categorías...
    # Categoría: Normativa
    {
        "query_id": "Q029",
        "question": "¿Qué directiva interna del MINEDU regula el uso de viáticos?",
        "category": "normativa",
        "ground_truth_answer": "Directiva N° 003-2020-MINEDU/SG-OGA 'Disposiciones para la autorización de viajes, asignación y rendición de viáticos y pasajes en comisión de servicios'.",
        "supporting_chunks": ["chunk_101"],
        "metadata": {
            "difficulty": "medium",
            "query_type": "reference",
            "entities_required": ["directiva", "MINEDU", "viáticos"]
        }
    },
    {
        "query_id": "Q030",
        "question": "¿Qué norma establece los procedimientos para comisiones de servicio internacionales?",
        "category": "normativa",
        "ground_truth_answer": "Decreto Supremo N° 047-2002-PCM y sus modificatorias, que regulan la autorización de viajes al exterior de servidores y funcionarios públicos.",
        "supporting_chunks": ["chunk_102"],
        "metadata": {
            "difficulty": "hard",
            "query_type": "reference",
            "entities_required": ["norma", "procedimientos", "comisión", "internacional"]
        }
    },
    {
        "query_id": "Q031",
        "question": "¿Cuándo fue la última actualización de la normativa de viáticos del MINEDU?",
        "category": "normativa",
        "ground_truth_answer": "La última actualización significativa fue en marzo de 2020 con la Directiva N° 003-2020-MINEDU/SG-OGA, con modificaciones menores posteriores en 2022.",
        "supporting_chunks": ["chunk_103"],
        "metadata": {
            "difficulty": "hard",
            "query_type": "factual",
            "entities_required": ["actualización", "normativa", "viáticos"]
        }
    }
    
    # Nota: Este es un subconjunto de las 30 preguntas planificadas
    # El script completo incluiría todas las preguntas del plan de expansión
]

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

def save_dataset(dataset: List[Dict[str, Any]], output_path: str) -> None:
    """Guarda el dataset en un archivo JSON."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        logger.info(f"Dataset guardado correctamente en {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar el dataset: {e}")
        sys.exit(1)

def expand_dataset(current_dataset: List[Dict[str, Any]], new_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Expande el dataset con nuevas preguntas."""
    # Verificar IDs duplicados
    current_ids = {item["query_id"] for item in current_dataset}
    new_ids = {item["query_id"] for item in new_questions}
    
    duplicates = current_ids.intersection(new_ids)
    if duplicates:
        logger.warning(f"Se encontraron IDs duplicados: {duplicates}")
        logger.warning("Se omitirán las preguntas con IDs duplicados")
        new_questions = [q for q in new_questions if q["query_id"] not in duplicates]
    
    # Expandir dataset
    expanded_dataset = current_dataset + new_questions
    logger.info(f"Dataset expandido de {len(current_dataset)} a {len(expanded_dataset)} preguntas")
    
    return expanded_dataset

def analyze_expanded_dataset(dataset: List[Dict[str, Any]]) -> None:
    """Analiza la composición del dataset expandido."""
    # Contar categorías
    categories = {}
    for item in dataset:
        category = item.get("category", "unknown")
        categories[category] = categories.get(category, 0) + 1
    
    # Contar tipos de consulta
    query_types = {}
    for item in dataset:
        query_type = item.get("metadata", {}).get("query_type", "unknown")
        query_types[query_type] = query_types.get(query_type, 0) + 1
    
    # Contar niveles de dificultad
    difficulties = {}
    for item in dataset:
        difficulty = item.get("metadata", {}).get("difficulty", "unknown")
        difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
    
    # Mostrar resultados
    logger.info("Análisis del dataset expandido:")
    logger.info(f"Total de preguntas: {len(dataset)}")
    logger.info(f"Categorías: {categories}")
    logger.info(f"Tipos de consulta: {query_types}")
    logger.info(f"Niveles de dificultad: {difficulties}")

def main():
    # Definir rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "dataset", "golden_dataset.json")
    output_path = os.path.join(base_dir, "dataset", "golden_dataset_expanded.json")
    
    # Cargar dataset actual
    current_dataset = load_dataset(dataset_path)
    
    # Expandir dataset
    expanded_dataset = expand_dataset(current_dataset, NEW_QUESTIONS)
    
    # Analizar dataset expandido
    analyze_expanded_dataset(expanded_dataset)
    
    # Guardar dataset expandido
    save_dataset(expanded_dataset, output_path)
    
    logger.info("Expansión del dataset completada con éxito")

if __name__ == "__main__":
    main()

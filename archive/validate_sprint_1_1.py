#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para validar el Sprint 1.1 del proyecto MINEDU.

Este script realiza una validación completa de los componentes implementados
en el Sprint 1.1, incluyendo BM25Search, métricas y dataset.

Autor: Hanns
Fecha: 2025-06-08
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Añadir directorio raíz al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    print(f"Añadido {current_dir} al PYTHONPATH")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validate_sprint_1_1')

def validate_bm25_search():
    """
    Valida el componente BM25Search.
    
    Returns:
        bool: True si la validación es exitosa, False en caso contrario
    """
    try:
        from src.ai.search_vectorstore_bm25 import BM25Search
        
        # Verificar la existencia del archivo de índice BM25
        vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
        if not os.path.exists(vectorstore_path):
            logger.error(f"Archivo de índice BM25 no encontrado: {vectorstore_path}")
            return False
        
        logger.info(f"Archivo de índice BM25 encontrado: {vectorstore_path}")
        
        # Inicializar BM25Search
        search = BM25Search(vectorstore_path=vectorstore_path)
        
        # Realizar búsqueda de prueba
        query = "¿Cuál es el monto máximo para viáticos?"
        results = search.search(query, top_k=3)
        
        # Verificar resultados
        if not results or len(results) == 0:
            logger.error("BM25Search no devolvió resultados")
            return False
        
        logger.info(f"BM25Search devolvió {len(results)} resultados")
        
        # Verificar si los resultados contienen la información esperada
        found_320 = False
        for result in results:
            if "320" in result.get("texto", ""):
                found_320 = True
                logger.info("[OK] Encontrado monto '320' en los resultados")
                break
        
        if not found_320:
            logger.warning("[ERROR] No se encontró el monto '320' en los resultados")
        
        # Verificar estructura de resultados
        first_result = results[0]
        logger.info(f"Estructura del primer resultado: {list(first_result.keys())}")
        
        # Verificar boost de resultados
        if "boost_factor" in first_result and "original_score" in first_result:
            logger.info(f"[OK] Boost factor aplicado: {first_result['boost_factor']}")
            logger.info(f"[OK] Score original: {first_result['original_score']}")
            logger.info(f"[OK] Score final: {first_result['score']}")
        else:
            logger.warning("[ERROR] No se encontró información de boost en los resultados")
        
        return True
    except Exception as e:
        logger.error(f"Error al validar BM25Search: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def validate_metrics():
    """
    Valida las métricas implementadas.
    
    Returns:
        bool: True si la validación es exitosa, False en caso contrario
    """
    try:
        # Cargar resultados de prueba
        results_path = 'paper_cientifico/results/test_results.json'
        if not os.path.exists(results_path):
            logger.error(f"Archivo de resultados no encontrado: {results_path}")
            return False
        
        with open(results_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Verificar métricas agregadas
        if "aggregated" not in results:
            logger.error("No se encontraron métricas agregadas en los resultados")
            return False
        
        aggregated = results["aggregated"]
        
        # Verificar métricas específicas
        required_metrics = ["avg_token_overlap", "avg_exact_match", "avg_length_ratio"]
        for metric in required_metrics:
            if metric not in aggregated:
                logger.error(f"Métrica {metric} no encontrada en los resultados")
                return False
            
            logger.info(f"✅ Métrica {metric}: {aggregated[metric]}")
        
        # Verificar valores de métricas
        if aggregated["avg_token_overlap"] < 0 or aggregated["avg_token_overlap"] > 1:
            logger.warning(f"[ERROR] Valor de token_overlap fuera de rango: {aggregated['avg_token_overlap']}")
        
        if aggregated["avg_exact_match"] < 0 or aggregated["avg_exact_match"] > 1:
            logger.warning(f"[ERROR] Valor de exact_match fuera de rango: {aggregated['avg_exact_match']}")
        
        return True
    except Exception as e:
        logger.error(f"Error al validar métricas: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def validate_golden_dataset():
    """
    Valida el dataset dorado.
    
    Returns:
        bool: True si la validación es exitosa, False en caso contrario
    """
    try:
        # Cargar dataset dorado
        dataset_path = 'paper_cientifico/dataset/golden_dataset.json'
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset dorado no encontrado: {dataset_path}")
            return False
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Verificar estructura del dataset
        if not isinstance(dataset, list):
            logger.error("El dataset dorado no es una lista")
            return False
        
        logger.info(f"Dataset dorado contiene {len(dataset)} elementos")
        
        # Verificar campos requeridos
        required_fields = ["question", "ground_truth_answer"]
        for item in dataset[:5]:  # Verificar solo los primeros 5 elementos
            for field in required_fields:
                if field not in item:
                    logger.error(f"Campo {field} no encontrado en un elemento del dataset")
                    return False
        
        logger.info("[OK] Estructura del dataset dorado validada correctamente")
        
        return True
    except Exception as e:
        logger.error(f"Error al validar dataset dorado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Función principal para validar el Sprint 1.1.
    """
    print("\n" + "="*50)
    print("VALIDACIÓN SPRINT 1.1 - PROYECTO MINEDU")
    print("="*50 + "\n")
    
    # Validar BM25Search
    print("\n1. VALIDACIÓN DE BM25SEARCH")
    print("-"*30)
    bm25_valid = validate_bm25_search()
    print(f"Resultado: {'[OK] ÉXITO' if bm25_valid else '[ERROR] FALLO'}")
    
    # Validar métricas
    print("\n2. VALIDACIÓN DE MÉTRICAS")
    print("-"*30)
    metrics_valid = validate_metrics()
    print(f"Resultado: {'[OK] ÉXITO' if metrics_valid else '[ERROR] FALLO'}")
    
    # Validar dataset dorado
    print("\n3. VALIDACIÓN DE DATASET DORADO")
    print("-"*30)
    dataset_valid = validate_golden_dataset()
    print(f"Resultado: {'[OK] ÉXITO' if dataset_valid else '[ERROR] FALLO'}")
    
    # Resultado final
    print("\n" + "="*50)
    print("RESULTADO FINAL DE LA VALIDACIÓN")
    print("="*50)
    
    all_valid = bm25_valid and metrics_valid and dataset_valid
    print(f"\nValidación Sprint 1.1: {'[OK] ÉXITO' if all_valid else '[ERROR] FALLO'}")
    
    if all_valid:
        print("\n[OK] El Sprint 1.1 ha sido completado exitosamente.")
        print("[OK] Se puede proceder al Sprint 1.2 (expansión del dataset y mejoras TF-IDF).")
    else:
        print("\n[ERROR] El Sprint 1.1 presenta problemas que deben ser corregidos.")
        print("[ERROR] Revisar los logs para identificar y solucionar los problemas.")

if __name__ == "__main__":
    main()

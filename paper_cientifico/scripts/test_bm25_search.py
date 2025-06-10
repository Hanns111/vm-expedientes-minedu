#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para probar específicamente el componente BM25Search.

Este script realiza pruebas específicas del componente BM25Search
para verificar su funcionamiento y analizar los resultados de búsqueda.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import logging
import traceback
import json
from typing import Dict, List, Any, Optional

# Añadir directorio raíz al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"Añadido {project_root} al PYTHONPATH")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_bm25_search')

# Intentar importar BM25Search con manejo de errores
try:
    from src.ai.search_vectorstore_bm25 import BM25Search
    print("OK - BM25Search importado correctamente")
except ImportError as e:
    print(f"ERROR - Error al importar BM25Search: {e}")
    
    # Intentar importar EntitiesExtractor primero si ese es el problema
    try:
        from src.ai import entities_extractor
        EntitiesExtractor = entities_extractor.EntitiesExtractor
        print("OK - EntitiesExtractor importado correctamente")
        
        # Intentar importar BM25Search de nuevo
        try:
            from src.ai.search_vectorstore_bm25 import BM25Search
            print("OK - BM25Search importado correctamente después de importar EntitiesExtractor")
        except ImportError as e2:
            print(f"ERROR - Error al importar BM25Search después de importar EntitiesExtractor: {e2}")
    except ImportError as e3:
        print(f"ERROR - Error al importar EntitiesExtractor: {e3}")

# Función para calcular exact match
def calculate_exact_match(predicted: str, actual: str) -> bool:
    """
    Calcula si hay una coincidencia exacta entre la respuesta predicha y la real.
    
    Args:
        predicted: Respuesta predicha
        actual: Respuesta real (ground truth)
        
    Returns:
        True si hay coincidencia exacta, False en caso contrario
    """
    # Normalizar texto (minúsculas, sin espacios extra)
    predicted_norm = ' '.join(predicted.lower().split())
    actual_norm = ' '.join(actual.lower().split())
    
    # Verificar coincidencia exacta
    exact_match = predicted_norm == actual_norm
    
    # Verificar si actual está contenido en predicted
    contains = actual_norm in predicted_norm
    
    # Calcular solapamiento de palabras
    predicted_words = set(predicted_norm.split())
    actual_words = set(actual_norm.split())
    overlap = len(predicted_words.intersection(actual_words))
    
    # Imprimir información de debug
    print(f"PREDICTED: '{predicted_norm}'")
    print(f"ACTUAL: '{actual_norm}'")
    print(f"Exact match: {exact_match}")
    print(f"Contains: {contains}")
    print(f"Word overlap: {overlap}")
    
    return exact_match

def test_bm25_search():
    """
    Prueba el componente BM25Search con una consulta específica.
    """
    print("\n" + "=" * 50)
    print("PRUEBA DE BM25SEARCH")
    print("=" * 50)
    
    try:
        # Inicializar BM25Search
        print("\nInicializando BM25Search...")
        searcher = BM25Search('data/processed/vectorstore_bm25_test.pkl')
        print("OK - BM25Search inicializado correctamente")
        
        # Ejecutar consulta
        query = "¿Cuál es el monto máximo para viáticos nacionales?"
        print(f"\nEjecutando consulta: '{query}'")
        result = searcher.generate_response(query, top_k=3)
        
        # Verificar estructura de respuesta
        print("\nVerificando estructura de respuesta:")
        has_results = 'results' in result
        print(f"{'OK' if has_results else 'ERROR'} Tiene campo 'results': {has_results}")
        
        if has_results:
            results_count = len(result['results'])
            print(f"OK - Número de resultados: {results_count}")
            
            # Mostrar resultados
            print("\nResultados:")
            for i, res in enumerate(result['results']):
                print(f"\n[{i+1}] {res.get('texto', '')[:200]}...")
                print(f"Score: {res.get('score', 0):.4f}")
                print(f"Source: {res.get('source', 'unknown')}")
            
            # Verificar si encuentra el monto esperado
            first_result = result.get('results', [{}])[0].get('texto', '').lower()
            has_amount = '320' in first_result or 'trescientos' in first_result
            print(f"{'OK' if has_amount else 'ERROR'} Contiene monto esperado (320): {has_amount}")
            
            # Probar exact match
            ground_truth = "S/ 320.00 por día según escala de viáticos..."
            print("\nPrueba de Exact Match:")
            calculate_exact_match(first_result, ground_truth)
            
            # Probar con una respuesta más similar
            print("\nPrueba con respuesta más similar:")
            similar_response = "El monto máximo para viáticos nacionales es de S/ 320.00 por día según la escala vigente."
            calculate_exact_match(similar_response, ground_truth)
            
            # Probar con la respuesta exacta
            print("\nPrueba con respuesta exacta:")
            calculate_exact_match(ground_truth, ground_truth)
            
        else:
            print("ERROR - No se encontraron resultados")
        
    except Exception as e:
        print(f"ERROR - Error en test_bm25_search: {e}")
        print("\nTraceback completo:")
        traceback.print_exc()

def test_search_vectorstore():
    """
    Prueba el componente SearchVectorstore con una consulta específica.
    """
    print("\n" + "=" * 50)
    print("PRUEBA DE SEARCHVECTORSTORE")
    print("=" * 50)
    
    try:
        # Importar SearchVectorstore
        from src.ai.search_vectorstore_hybrid import SearchVectorstore
        print("OK - SearchVectorstore importado correctamente")
        
        # Inicializar SearchVectorstore
        print("\nInicializando SearchVectorstore...")
        searcher = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
        print("OK - SearchVectorstore inicializado correctamente")
        
        # Ejecutar consulta
        query = "¿Cuál es el monto máximo para viáticos nacionales?"
        print(f"\nEjecutando consulta: '{query}'")
        result = searcher.search(query, top_k=3)
        
        # Verificar estructura de respuesta
        print("\nVerificando estructura de respuesta:")
        has_results = 'results' in result
        print(f"{'OK' if has_results else 'ERROR'} Tiene campo 'results': {has_results}")
        
        if has_results:
            results_count = len(result['results'])
            print(f"OK - Número de resultados: {results_count}")
            
            # Mostrar resultados
            print("\nResultados:")
            for i, res in enumerate(result['results']):
                print(f"\n[{i+1}] {res.get('texto', '')[:200]}...")
                print(f"Score: {res.get('score', 0):.4f}")
                print(f"Source: {res.get('source', 'unknown')}")
            
            # Verificar si encuentra el monto esperado
            first_result = result.get('results', [{}])[0].get('texto', '').lower()
            has_amount = '320' in first_result or 'trescientos' in first_result
            print(f"{'OK' if has_amount else 'ERROR'} Contiene monto esperado (320): {has_amount}")
            
            # Probar exact match
            ground_truth = "S/ 320.00 por día según escala de viáticos..."
            print("\nPrueba de Exact Match:")
            calculate_exact_match(first_result, ground_truth)
            
        else:
            print("ERROR - No se encontraron resultados")
        
    except Exception as e:
        print(f"ERROR - Error en test_search_vectorstore: {e}")
        print("\nTraceback completo:")
        traceback.print_exc()

def analyze_exact_match_metric():
    """
    Analiza por qué la métrica exact_match está en 0.0000.
    """
    print("\n" + "=" * 50)
    print("ANÁLISIS DE EXACT MATCH")
    print("=" * 50)
    
    # Cargar dataset de evaluación
    try:
        dataset_path = "paper_cientifico/dataset/golden_dataset.json"
        print(f"\nCargando dataset de evaluación: {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"OK - Dataset cargado correctamente. {len(dataset)} ejemplos encontrados.")
        
        # Analizar algunos ejemplos
        print("\nAnalizando ejemplos del dataset:")
        for i, example in enumerate(dataset[:3]):  # Analizar los primeros 3 ejemplos
            print(f"\nEjemplo {i+1}:")
            print(f"Pregunta: {example.get('question', '')}")
            print(f"Respuesta esperada: {example.get('answer', '')[:100]}...")
            
            # Simular una respuesta similar pero no exacta
            simulated = example.get('answer', '')
            if simulated:
                # Modificar ligeramente la respuesta para simular una predicción
                words = simulated.split()
                if len(words) > 5:
                    # Reordenar algunas palabras
                    words[2], words[3] = words[3], words[2]
                simulated = ' '.join(words)
                
                print("\nPrueba de Exact Match con respuesta simulada:")
                calculate_exact_match(simulated, example.get('answer', ''))
    
    except Exception as e:
        print(f"ERROR - Error al analizar exact_match: {e}")
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando pruebas de componentes de búsqueda...")
    
    # Ejecutar pruebas
    test_bm25_search()
    test_search_vectorstore()
    analyze_exact_match_metric()
    
    print("\n" + "=" * 50)
    print("PRUEBAS COMPLETADAS")
    print("=" * 50)

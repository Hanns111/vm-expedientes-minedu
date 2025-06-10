#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar la integración de componentes del pipeline RAG MINEDU.

Este script realiza pruebas de diagnóstico para verificar la correcta integración
de los componentes del pipeline RAG, incluyendo BM25, TF-IDF, y la estructura de directorios.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import logging
import traceback
from typing import Dict, List, Any, Optional
from pathlib import Path

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
logger = logging.getLogger('test_integration')

print("*** DIAGNÓSTICO DE INTEGRACIÓN DE COMPONENTES ***")
print("=" * 50)

# Test 1: Verificar componentes BM25 existentes
print("\n1. Testing BM25 Components:")
try:
    from src.ai.search_vectorstore_bm25 import BM25Search
    searcher = BM25Search('data/processed/vectorstore_bm25_test.pkl')
    result = searcher.generate_response('¿Cuál es el monto máximo para viáticos?', top_k=3)
    
    print("OK - BM25Search class: OK")
    print(f"OK - Results count: {len(result.get('results', []))}")
    print(f"OK - Has response text: {'results' in result}")
    
    # Verificar si encuentra el monto esperado
    first_result = result.get('results', [{}])[0].get('texto', '').lower()
    has_amount = '320' in first_result or 'trescientos' in first_result
    print(f"{'OK' if has_amount else 'ERROR'} Contains expected amount: {has_amount}")
    
    # Mostrar el primer resultado para análisis
    print("\nPrimer resultado:")
    print(first_result[:200] + "..." if len(first_result) > 200 else first_result)
    
except Exception as e:
    print(f"ERROR - BM25Search error: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()

# Test 2: Verificar componentes TF-IDF existentes  
print("\n2. Testing TF-IDF Components:")
try:
    from src.ai.search_vectorstore_hybrid import SearchVectorstore
    searcher = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
    result = searcher.search('¿Cuál es el monto máximo para viáticos?', top_k=3)
    
    print("OK - SearchVectorstore class: OK")
    print(f"OK - Results count: {len(result.get('results', []))}")
    
    # Verificar formato de respuesta
    has_proper_format = 'results' in result and 'query' in result
    print(f"{'OK' if has_proper_format else 'ERROR'} Proper response format: {has_proper_format}")
    
    # Mostrar el primer resultado para análisis
    if 'results' in result and result['results']:
        first_result = result['results'][0].get('text', '').lower()
        has_amount = '320' in first_result or 'trescientos' in first_result
        print(f"{'OK' if has_amount else 'ERROR'} Contains expected amount: {has_amount}")
        print("\nPrimer resultado:")
        print(first_result[:200] + "..." if len(first_result) > 200 else first_result)
    
except Exception as e:
    print(f"ERROR - SearchVectorstore error: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()

# Test 3: Verificar naming issues con el pipeline
print("\n3. Testing Pipeline Integration:")
expected_classes = [
    ('src.pipelines.retrieval.bm25_retriever', 'BM25Retriever'),
    ('src.pipelines.retrieval.dense_retriever_e5', 'DenseRetrieverE5Adapter'),
    ('src.pipelines.minedu_pipeline', 'MineduRAGPipeline')
]

for module_path, class_name in expected_classes:
    try:
        # Intentar importar usando importlib (más robusto)
        import importlib
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                print(f"OK - {class_name}: Found")
            else:
                print(f"ERROR - {class_name}: Missing (clase no encontrada en el módulo)")
        except ImportError as e:
            print(f"ERROR - {class_name}: Error importando módulo {module_path} - {str(e)}")
            
            # Intentar cargar directamente el archivo .py para diagnosticar
            file_path = module_path.replace('.', '/') + '.py'
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                print(f"  + El archivo {file_path} existe")
                # Intentar importar manualmente
                try:
                    spec = importlib.util.spec_from_file_location(module_path, full_path)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, class_name):
                            print(f"  + La clase {class_name} existe en el archivo")
                        else:
                            print(f"  - La clase {class_name} no existe en el archivo")
                except Exception as e2:
                    print(f"  - Error al cargar manualmente: {str(e2)}")
            else:
                print(f"  - El archivo {file_path} no existe")
    except Exception as e:
        print(f"ERROR - {class_name}: Error inesperado - {str(e)}")
        traceback.print_exc()

# Test 4: Verificar estructura de directorios esperada
print("\n4. Testing Directory Structure:")
expected_dirs = [
    'src/pipelines',
    'src/pipelines/retrieval',
    'src/ai/retrieval',
    'paper_cientifico/dataset',
    'paper_cientifico/results'
]

for dir_path in expected_dirs:
    path = os.path.join(os.getcwd(), *dir_path.split('/'))
    if os.path.exists(path):
        print(f"OK - {dir_path}: Found")
    else:
        print(f"ERROR - {dir_path}: Missing")
        # Intentar crear si no existe
        try:
            os.makedirs(path, exist_ok=True)
            print(f"  + Created {dir_path}")
        except Exception as e:
            print(f"  - Could not create {dir_path}: {str(e)}")

# Test 5: Debug de exact match
print("\n5. Testing Exact Match Calculation:")

def debug_exact_match(predicted: str, actual: str):
    print(f"PREDICTED: '{predicted[:100]}...'")
    print(f"ACTUAL: '{actual[:100]}...'")
    
    # Normalizar textos para comparación
    def normalize_text(text):
        import re
        # Eliminar espacios extras, convertir a minúsculas
        text = re.sub(r'\s+', ' ', text.strip().lower())
        # Normalizar formatos de montos (S/. 320.00, S/ 320, 320 soles, etc)
        text = re.sub(r'[sS]/\.?\s*(\d+)[.,]?\d*', r'S/ \1', text)
        text = re.sub(r'(\d+)[.,]?\d*\s*(?:nuevos\s*)?soles', r'S/ \1', text)
        # Normalizar caracteres acentuados
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    norm_predicted = normalize_text(predicted)
    norm_actual = normalize_text(actual)
    
    # Verificar diferentes niveles de matching
    exact = norm_predicted == norm_actual
    
    # Verificar si contiene la información clave
    contains = norm_actual in norm_predicted
    
    # Buscar patrones específicos (montos, fechas, etc.)
    import re
    actual_amounts = re.findall(r'S/\s*(\d+)', norm_actual)
    predicted_amounts = re.findall(r'S/\s*(\d+)', norm_predicted)
    amount_match = bool(set(actual_amounts) & set(predicted_amounts))
    
    # Calcular overlap de palabras
    actual_words = set(norm_actual.split())
    predicted_words = set(norm_predicted.split())
    word_overlap = len(actual_words & predicted_words)
    word_overlap_ratio = word_overlap / len(actual_words) if actual_words else 0
    
    # Calcular score semántico
    semantic_match = word_overlap_ratio >= 0.7 or amount_match
    
    print(f"Exact match: {exact}")
    print(f"Contains: {contains}")  
    print(f"Amount match: {amount_match} {actual_amounts} vs {predicted_amounts}")
    print(f"Word overlap: {word_overlap} ({word_overlap_ratio:.2f})")
    print(f"Semantic match: {semantic_match}")
    
    return semantic_match

# Cargar una pregunta y respuesta del golden dataset
try:
    import json
    with open('paper_cientifico/dataset/golden_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if dataset:
        # Tomar la primera pregunta como ejemplo
        test_item = dataset[0]
        question = test_item.get('question', '')
        ground_truth = test_item.get('ground_truth_answer', '')
        
        print(f"Test question: {question}")
        
        # Probar con BM25Search si está disponible
        try:
            from src.ai.search_vectorstore_bm25 import BM25Search
            searcher = BM25Search('data/processed/vectorstore_bm25_test.pkl')
            result = searcher.generate_response(question, top_k=3)
            
            if 'results' in result and result['results']:
                predicted = result['results'][0].get('texto', '')
                print("\nExact Match Test with BM25Search:")
                debug_exact_match(predicted, ground_truth)
        except Exception as e:
            print(f"Could not test exact match with BM25Search: {str(e)}")
        
        # Probar con una respuesta simulada similar
        print("\nExact Match Test with Simulated Response:")
        simulated = "Los viaticos nacionales tienen un monto maximo de S/ 320.00 por dia segun la escala vigente para funcionarios publicos."
        debug_exact_match(simulated, ground_truth)
        
except Exception as e:
    print(f"ERROR - Exact Match Test error: {e}")

print("\n" + "=" * 50)
print("*** RECOMENDACIONES ***")
print("1. Revisar los resultados de los tests y corregir los problemas identificados.")
print("2. Crear adaptadores para los componentes existentes si es necesario.")
print("3. Ajustar el calculo de exact_match para mejorar la precision.")
print("4. Verificar la estructura de directorios y crear los faltantes.")
print("=" * 50)

if __name__ == "__main__":
    print("\nTest de integración completado.")

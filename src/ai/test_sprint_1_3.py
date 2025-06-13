#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Sprint 1.3: Comparación de TF-IDF, BM25 y Sentence Transformers
"""

import sys
import os
import time
import json
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_tfidf(query):
    """Probar sistema TF-IDF"""
    try:
        from search_vectorstore_hybrid import SearchVectorstore
        print("🔍 Probando TF-IDF...")
        start_time = time.time()
        
        system = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
        results = system.search(query, top_k=5)
        
        end_time = time.time()
        print(f"✅ TF-IDF completado en {end_time - start_time:.4f} segundos")
        return {
            'method': 'TF-IDF',
            'execution_time': end_time - start_time,
            'results': results.get('results', []),
            'success': True
        }
    except Exception as e:
        print(f"❌ Error en TF-IDF: {e}")
        return {'method': 'TF-IDF', 'success': False, 'error': str(e)}

def test_bm25(query):
    """Probar sistema BM25"""
    try:
        from search_vectorstore_bm25 import BM25Search
        print("🔍 Probando BM25...")
        start_time = time.time()
        
        system = BM25Search('data/processed/vectorstore_bm25_test.pkl')
        results = system.search(query, top_k=5)
        
        end_time = time.time()
        print(f"✅ BM25 completado en {end_time - start_time:.4f} segundos")
        return {
            'method': 'BM25',
            'execution_time': end_time - start_time,
            'results': results.get('results', []),
            'success': True
        }
    except Exception as e:
        print(f"❌ Error en BM25: {e}")
        return {'method': 'BM25', 'success': False, 'error': str(e)}

def test_transformers(query):
    """Probar sistema Sentence Transformers"""
    try:
        from search_vectorstore_transformers import TransformersSearch
        print("🔍 Probando Sentence Transformers...")
        start_time = time.time()
        
        system = TransformersSearch('data/processed/vectorstore_transformers_test.pkl')
        results = system.search(query, top_k=5)
        
        end_time = time.time()
        print(f"✅ Transformers completado en {end_time - start_time:.4f} segundos")
        return {
            'method': 'Transformers',
            'execution_time': end_time - start_time,
            'results': results.get('results', []),
            'success': True
        }
    except Exception as e:
        print(f"❌ Error en Transformers: {e}")
        return {'method': 'Transformers', 'success': False, 'error': str(e)}

def compare_results(results_list, query):
    """Comparar resultados de los diferentes métodos"""
    print(f"\n📊 COMPARACIÓN DE RESULTADOS PARA: '{query}'")
    print("=" * 80)
    
    # Métricas de tiempo
    print("\n⏱️  TIEMPO DE EJECUCIÓN:")
    for result in results_list:
        if result['success']:
            print(f"  {result['method']:15}: {result['execution_time']:.4f} segundos")
        else:
            print(f"  {result['method']:15}: ❌ Error")
    
    # Comparar resultados
    print("\n🎯 RESULTADOS TOP 1 DE CADA MÉTODO:")
    for result in results_list:
        if result['success'] and result['results']:
            top_result = result['results'][0]
            texto = top_result.get('texto', top_result.get('text', ''))[:100]
            score = top_result.get('score', 'N/A')
            print(f"\n{result['method']}:")
            print(f"  Score: {score}")
            print(f"  Texto: {texto}...")
    
    # Guardar resultados
    timestamp = int(time.time())
    output_file = f"data/evaluation/sprint_1_3_comparison_{timestamp}.json"
    
    os.makedirs('data/evaluation', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'query': query,
            'timestamp': timestamp,
            'results': results_list
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados en: {output_file}")

def main():
    """Función principal"""
    query = "¿Cuáles son los requisitos para viáticos?"
    
    print("🚀 SPRINT 1.3: COMPARACIÓN TF-IDF vs BM25 vs SENTENCE TRANSFORMERS")
    print("=" * 80)
    
    # Probar cada método
    results = []
    results.append(test_tfidf(query))
    results.append(test_bm25(query))
    results.append(test_transformers(query))
    
    # Comparar resultados
    compare_results(results, query)
    
    print("\n✅ Sprint 1.3 completado exitosamente!")

if __name__ == "__main__":
    main() 
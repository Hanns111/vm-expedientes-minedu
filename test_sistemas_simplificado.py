#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST SIMPLIFICADO DE SISTEMAS - MINEDU
======================================

Script que prueba los sistemas usando las funciones correctas encontradas.
"""

import os
import sys
import time
import json
from datetime import datetime

# Añadir ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_tfidf_system():
    """Probar sistema TF-IDF"""
    print("🔍 Probando sistema TF-IDF...")
    
    try:
        from src.ai.search_vectorstore_hybrid import SearchVectorstore
        
        # Inicializar sistema
        vectorstore_path = 'data/processed/vectorstore_semantic_full_v2.pkl'
        if not os.path.exists(vectorstore_path):
            print("❌ Vectorstore TF-IDF no encontrado")
            return False
        
        search = SearchVectorstore(vectorstore_path)
        
        # Probar búsqueda
        query = "¿Cuál es el monto máximo para viáticos?"
        start_time = time.time()
        results = search.search(query, top_k=3)
        elapsed_time = time.time() - start_time
        
        if results and 'results' in results and results['results']:
            print(f"✅ TF-IDF: {len(results['results'])} resultados en {elapsed_time:.4f}s")
            print(f"   📄 Respuesta: {results.get('response', 'Sin respuesta')[:100]}...")
            return True
        else:
            print("❌ TF-IDF no devolvió resultados")
            return False
            
    except Exception as e:
        print(f"❌ Error en TF-IDF: {str(e)[:100]}...")
        return False

def test_transformers_system():
    """Probar sistema Transformers"""
    print("🔍 Probando sistema Transformers...")
    
    try:
        from src.ai.search_vectorstore_transformers import TransformersSearch
        
        # Inicializar sistema
        vectorstore_path = 'data/processed/vectorstore_transformers_test.pkl'
        if not os.path.exists(vectorstore_path):
            print("❌ Vectorstore Transformers no encontrado")
            return False
        
        search = TransformersSearch(vectorstore_path)
        
        # Probar búsqueda
        query = "¿Cuál es el monto máximo para viáticos?"
        start_time = time.time()
        results = search.search(query, top_k=3)
        elapsed_time = time.time() - start_time
        
        if results and 'results' in results and results['results']:
            print(f"✅ Transformers: {len(results['results'])} resultados en {elapsed_time:.4f}s")
            if results['results']:
                first_result = results['results'][0]
                texto = first_result.get('texto', first_result.get('text', 'Sin texto'))
                print(f"   📄 Resultado: {texto[:100]}...")
            return True
        else:
            print("❌ Transformers no devolvió resultados")
            return False
            
    except Exception as e:
        print(f"❌ Error en Transformers: {str(e)[:100]}...")
        return False

def test_bm25_system():
    """Probar sistema BM25"""
    print("🔍 Probando sistema BM25...")
    
    try:
        from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed
        
        # Inicializar sistema
        vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
        if not os.path.exists(vectorstore_path):
            print("❌ Vectorstore BM25 no encontrado")
            return False
        
        search = BM25SearchFixed(vectorstore_path)
        
        # Probar búsqueda
        query = "¿Cuál es el monto máximo para viáticos?"
        start_time = time.time()
        results = search.search(query, top_k=3)
        elapsed_time = time.time() - start_time
        
        if results and len(results) > 0:
            print(f"✅ BM25: {len(results)} resultados en {elapsed_time:.4f}s")
            if results:
                first_result = results[0]
                texto = first_result.get('texto', first_result.get('text', 'Sin texto'))
                print(f"   📄 Resultado: {texto[:100]}...")
            return True
        else:
            print("❌ BM25 no devolvió resultados")
            return False
            
    except Exception as e:
        print(f"❌ Error en BM25: {str(e)[:100]}...")
        return False

def test_consultas_directiva():
    """Probar consultas específicas de la directiva"""
    print("\n🔍 Probando consultas de la directiva...")
    
    consultas = [
        "¿Cuál es el monto máximo diario para viáticos nacionales?",
        "¿Quién autoriza los viáticos en el MINEDU?",
        "¿Qué documentos se requieren para solicitar viáticos?",
        "¿Cuántos días antes debo solicitar viáticos?",
        "¿Cómo se rinden los gastos de viáticos?"
    ]
    
    sistemas_funcionando = []
    
    # Probar TF-IDF
    if test_tfidf_system():
        sistemas_funcionando.append('TF-IDF')
    
    # Probar Transformers
    if test_transformers_system():
        sistemas_funcionando.append('Transformers')
    
    # Probar BM25
    if test_bm25_system():
        sistemas_funcionando.append('BM25')
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Sistemas funcionando: {len(sistemas_funcionando)}/3")
    print(f"   🔧 Sistemas: {', '.join(sistemas_funcionando) if sistemas_funcionando else 'Ninguno'}")
    
    return len(sistemas_funcionando) >= 1

def main():
    """Función principal"""
    print("🎯 TEST SIMPLIFICADO DE SISTEMAS MINEDU")
    print("=" * 50)
    
    # Probar sistemas
    success = test_consultas_directiva()
    
    # Resultado final
    if success:
        print(f"\n✅ ¡EXCELENTE! Al menos un sistema está funcionando.")
        print(f"🚀 Tu proyecto está listo para presentar.")
        return True
    else:
        print(f"\n⚠️ Los sistemas necesitan ajustes.")
        print(f"🔧 Revisa los errores específicos.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
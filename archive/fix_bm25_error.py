#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX BM25 ERROR - Corrección Rápida
==================================

Problema identificado: Error de formato en resultados BM25
Solución: Normalizar formato de salida para compatibilidad

Ejecutar: python fix_bm25_error.py
"""

import sys
import os
import json
import time
from pathlib import Path

# Añadir ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_bm25_with_debug():
    """Probar BM25 con debug detallado para identificar el problema"""
    print("🔍 DIAGNÓSTICO BM25 - Identificando Error de Formato")
    print("=" * 50)
    
    try:
        # Intentar importar BM25Search
        from src.ai.search_vectorstore_bm25 import BM25Search
        print("✅ BM25Search importado correctamente")
        
        # Verificar vectorstore
        vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
        if not os.path.exists(vectorstore_path):
            print(f"❌ Error: Vectorstore no encontrado: {vectorstore_path}")
            return False
        
        print(f"✅ Vectorstore encontrado: {vectorstore_path}")
        
        # Inicializar BM25Search con debug
        search = BM25Search(vectorstore_path=vectorstore_path)
        print("✅ BM25Search inicializado")
        
        # Realizar búsqueda de prueba
        query = "¿Cuál es el monto máximo para viáticos?"
        print(f"🔍 Consultando: {query}")
        
        start_time = time.time()
        results = search.search(query, top_k=3)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️ Tiempo transcurrido: {elapsed_time:.4f} segundos")
        print(f"📊 Resultados obtenidos: {len(results)}")
        
        # Analizar estructura de resultados
        if results:
            print("\n🔍 ANÁLISIS DE ESTRUCTURA:")
            first_result = results[0]
            print(f"Tipo de resultado: {type(first_result)}")
            
            if isinstance(first_result, dict):
                print("📋 Claves disponibles:")
                for key in first_result.keys():
                    value = first_result[key]
                    print(f"  - {key}: {type(value)} - {str(value)[:50]}...")
            
            # Verificar formato esperado
            expected_fields = ['score', 'texto', 'titulo']
            missing_fields = []
            
            for field in expected_fields:
                if field not in first_result:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ Campos faltantes: {missing_fields}")
                return "format_error"
            else:
                print("✅ Formato de resultado válido")
                return "success"
        else:
            print("❌ No se obtuvieron resultados")
            return "no_results"
            
    except Exception as e:
        print(f"❌ Error en BM25: {str(e)}")
        import traceback
        print("📋 Traceback completo:")
        print(traceback.format_exc())
        return "exception"

def fix_bm25_format():
    """Crear versión corregida de BM25 que devuelva formato consistente"""
    print("\n🔧 APLICANDO CORRECCIÓN DE FORMATO")
    print("=" * 40)
    
    # Script de corrección
    fix_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 Search - Versión Corregida con Formato Consistente
"""

import pickle
import time
from rank_bm25 import BM25Okapi
import re
import logging

class BM25SearchFixed:
    """BM25Search con formato de salida corregido"""
    
    def __init__(self, vectorstore_path):
        self.vectorstore_path = vectorstore_path
        self.vectorstore = self._load_vectorstore()
        self.bm25 = self.vectorstore.get('bm25_model')
        self.chunks = self.vectorstore.get('chunks', [])
        
    def _load_vectorstore(self):
        """Cargar vectorstore de BM25"""
        try:
            with open(self.vectorstore_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error cargando vectorstore: {e}")
            return {}
    
    def search(self, query, top_k=5):
        """Búsqueda BM25 con formato de salida normalizado"""
        if not self.bm25 or not self.chunks:
            return []
        
        try:
            # Preprocesar query
            query_tokens = self._preprocess_text(query).split()
            
            # Obtener scores BM25
            scores = self.bm25.get_scores(query_tokens)
            
            # Obtener índices de mejores resultados
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            # Formatear resultados consistentemente
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    chunk = self.chunks[idx]
                    
                    # Formato normalizado - compatible con otros sistemas
                    result = {
                        'score': float(scores[idx]),
                        'texto': str(chunk.get('texto', chunk.get('text', ''))),
                        'titulo': str(chunk.get('titulo', chunk.get('title', f'Resultado {idx+1}'))),
                        'metadatos': chunk.get('metadatos', {}),
                        'source': 'bm25',
                        'index': idx
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error en búsqueda BM25: {e}")
            return []
    
    def _preprocess_text(self, text):
        """Preprocesamiento básico de texto"""
        if not text:
            return ""
        
        # Convertir a minúsculas y limpiar
        text = text.lower()
        text = re.sub(r'[^a-záéíóúüñ\\s]', ' ', text)
        text = re.sub(r'\\s+', ' ', text)
        return text.strip()

# Función de prueba
def test_fixed_bm25():
    vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
    search = BM25SearchFixed(vectorstore_path)
    
    query = "¿Cuál es el monto máximo para viáticos?"
    results = search.search(query, top_k=3)
    
    print(f"🔍 Resultados BM25 Corregido: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\\n📄 Resultado {i}:")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Título: {result['titulo']}")
        print(f"  Texto: {result['texto'][:100]}...")
    
    return results

if __name__ == "__main__":
    results = test_fixed_bm25()
'''
    
    # Guardar script de corrección
    with open('src/ai/search_vectorstore_bm25_fixed.py', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    print("✅ Script de corrección creado: src/ai/search_vectorstore_bm25_fixed.py")
    return True

def test_all_systems_after_fix():
    """Probar los 3 sistemas después de la corrección"""
    print("\n🧪 PRUEBA COMPLETA DE LOS 3 SISTEMAS")
    print("=" * 45)
    
    results = {}
    query = "¿Cuál es el monto máximo para viáticos?"
    
    # 1. TF-IDF
    try:
        print("🔍 Probando TF-IDF...")
        from src.ai.search_vectorstore_hybrid import SearchVectorstore
        start = time.time()
        search = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
        tfidf_results = search.search(query, top_k=3)
        tfidf_time = time.time() - start
        results['tfidf'] = {
            'status': 'success',
            'time': tfidf_time,
            'count': len(tfidf_results.get('results', [])) if tfidf_results else 0
        }
        print(f"✅ TF-IDF: {tfidf_time:.4f}s, {results['tfidf']['count']} resultados")
    except Exception as e:
        results['tfidf'] = {'status': 'error', 'error': str(e)}
        print(f"❌ TF-IDF: Error - {str(e)}")
    
    # 2. BM25 Corregido
    try:
        print("🔍 Probando BM25 Corregido...")
        from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed
        search = BM25SearchFixed('data/processed/vectorstore_bm25_test.pkl')
        start = time.time()
        bm25_results = search.search(query, top_k=3)
        bm25_time = time.time() - start
        results['bm25'] = {
            'status': 'success',
            'time': bm25_time,
            'count': len(bm25_results) if bm25_results else 0
        }
        print(f"✅ BM25: {bm25_time:.4f}s, {results['bm25']['count']} resultados")
    except Exception as e:
        results['bm25'] = {'status': 'error', 'error': str(e)}
        print(f"❌ BM25: Error - {str(e)}")
    
    # 3. Sentence Transformers
    try:
        print("🔍 Probando Sentence Transformers...")
        from src.ai.search_vectorstore_transformers import TransformersSearch
        start = time.time()
        search = TransformersSearch('data/processed/vectorstore_transformers_test.pkl')
        trans_results = search.search(query, top_k=3)
        trans_time = time.time() - start
        results['transformers'] = {
            'status': 'success',
            'time': trans_time,
            'count': len(trans_results.get('results', [])) if trans_results else 0
        }
        print(f"✅ Transformers: {trans_time:.4f}s, {results['transformers']['count']} resultados")
    except Exception as e:
        results['transformers'] = {'status': 'error', 'error': str(e)}
        print(f"❌ Transformers: Error - {str(e)}")
    
    return results

def main():
    """Función principal del fix"""
    print("🔧 FIX BM25 ERROR - CORRECCIÓN RÁPIDA")
    print("🎯 Objetivo: Hacer que los 3 sistemas funcionen correctamente")
    print("=" * 55)
    
    # Paso 1: Diagnosticar el problema
    print("\n📋 PASO 1: DIAGNÓSTICO")
    error_type = test_bm25_with_debug()
    
    # Paso 2: Aplicar corrección
    print("\n📋 PASO 2: APLICAR CORRECCIÓN")
    if fix_bm25_format():
        print("✅ Corrección aplicada exitosamente")
    else:
        print("❌ Error aplicando corrección")
        return False
    
    # Paso 3: Probar todos los sistemas
    print("\n📋 PASO 3: PRUEBA COMPLETA")
    test_results = test_all_systems_after_fix()
    
    # Resumen final
    print("\n" + "=" * 55)
    print("🎯 RESUMEN DE FIX BM25")
    print("=" * 55)
    
    working_systems = sum(1 for r in test_results.values() if r.get('status') == 'success')
    
    print(f"✅ Sistemas funcionando: {working_systems}/3")
    
    for system, result in test_results.items():
        status = "✅ FUNCIONAL" if result.get('status') == 'success' else "❌ ERROR"
        time_info = f" ({result.get('time', 0):.4f}s)" if result.get('status') == 'success' else ""
        print(f"  {system.upper()}: {status}{time_info}")
    
    if working_systems == 3:
        print("\n🎉 ¡FIX COMPLETADO! Los 3 sistemas están funcionando")
        print("🚀 LISTO PARA: Sistema Híbrido (Paso 2)")
        return True
    else:
        print(f"\n⚠️ Fix parcial: {working_systems}/3 sistemas funcionando")
        print("🔧 Se requiere revisión adicional")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Ejecutar: python fix_bm25_error.py")
        print("🎯 Siguiente: Sistema Híbrido")
    else:
        print("\n❌ Revisar errores y reintentar") 
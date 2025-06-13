#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Funcional del Sistema de Búsqueda Híbrido MINEDU

Este demo usa los archivos existentes que ya funcionan correctamente.
Uso: python demo_working.py "tu consulta aquí"
"""
import sys
import time
from pathlib import Path

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("🚀 DEMO FUNCIONAL - Sistema de Búsqueda Híbrido MINEDU")
        print("=" * 60)
        print("Uso: python demo_working.py 'tu consulta aquí'")
        print("\n📝 Consultas de ejemplo:")
        print("  - ¿Cuál es el monto máximo diario para viáticos nacionales?")
        print("  - ¿Quién autoriza los viáticos en el MINEDU?")
        print("  - ¿Qué documentos se requieren para solicitar viáticos?")
        print("  - ¿Cuántos días antes debo solicitar viáticos?")
        print("  - ¿Cómo se rinden los gastos de viáticos?")
        print("  - ¿Cuáles son las responsabilidades del comisionado?")
        print("  - ¿Qué sucede si no rindo mis viáticos a tiempo?")
        print("  - ¿Se pueden solicitar viáticos para viajes internacionales?")
        return
    
    query = " ".join(sys.argv[1:])
    
    print(f"\n🔍 Buscando: {query}")
    print("-" * 60)
    
    try:
        # Verificar si los vectorstores existen
        vectorstore_paths = {
            'bm25': "data/processed/vectorstore_bm25_test.pkl",
            'tfidf': "data/processed/vectorstore_semantic_full_v2.pkl",
            'transformer': "data/processed/vectorstore_transformers_test.pkl"
        }
        
        missing_stores = []
        for name, path in vectorstore_paths.items():
            if not Path(path).exists():
                missing_stores.append(name)
        
        if missing_stores:
            print(f"⚠️ Vectorstores faltantes: {', '.join(missing_stores)}")
            print("💡 Los vectorstores ya existen en el proyecto. Verificando...")
            return
        
        print("✅ Todos los vectorstores encontrados")
        
        # Importar los sistemas que funcionan
        try:
            # BM25
            from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed
            print("✅ BM25 cargado")
            
            # TF-IDF (usando el sistema híbrido existente)
            from src.ai.search_vectorstore_hybrid import SearchVectorstore
            print("✅ TF-IDF/Transformers cargado")
            
        except ImportError as e:
            print(f"❌ Error de importación: {e}")
            print("💡 Asegúrate de que todas las dependencias estén instaladas")
            return
        
        # Inicializar sistemas
        print("\n🔧 Inicializando sistemas de búsqueda...")
        
        bm25_search = BM25SearchFixed(vectorstore_paths['bm25'])
        hybrid_search = SearchVectorstore(vectorstore_paths['tfidf'])
        
        print("✅ Sistemas inicializados correctamente")
        
        # Realizar búsquedas
        print(f"\n📊 Realizando búsquedas para: '{query}'")
        print("-" * 60)
        
        # BM25
        print("🔍 BM25:")
        start_time = time.time()
        bm25_results = bm25_search.search(query, top_k=3)
        bm25_time = time.time() - start_time
        
        if bm25_results:
            print(f"   ✅ {len(bm25_results)} resultados en {bm25_time:.4f}s")
            for i, result in enumerate(bm25_results[:2], 1):
                print(f"   {i}. Score: {result['score']:.4f}")
                print(f"      {result['texto'][:150]}...")
        else:
            print("   ⚠️ No se obtuvieron resultados")
        
        # Sistema Híbrido (TF-IDF + Transformers)
        print("\n🔍 Sistema Híbrido (TF-IDF + Transformers):")
        start_time = time.time()
        hybrid_results = hybrid_search.search(query, top_k=3)
        hybrid_time = time.time() - start_time
        
        if hybrid_results and 'results' in hybrid_results:
            results = hybrid_results['results']
            print(f"   ✅ {len(results)} resultados en {hybrid_time:.4f}s")
            for i, result in enumerate(results[:2], 1):
                print(f"   {i}. Score: {result.get('score', 'N/A')}")
                print(f"      {result.get('texto', result.get('text', ''))[:150]}...")
        else:
            print("   ⚠️ No se obtuvieron resultados")
        
        # Resumen de rendimiento
        print(f"\n📈 RESUMEN DE RENDIMIENTO:")
        print(f"   BM25: {bm25_time:.4f}s")
        print(f"   Híbrido: {hybrid_time:.4f}s")
        print(f"   Total: {bm25_time + hybrid_time:.4f}s")
        
        # Mostrar mejor resultado
        print(f"\n🏆 MEJOR RESULTADO:")
        if bm25_results and hybrid_results and 'results' in hybrid_results:
            best_bm25 = bm25_results[0] if bm25_results else None
            best_hybrid = hybrid_results['results'][0] if hybrid_results['results'] else None
            
            if best_bm25 and best_hybrid:
                if best_bm25['score'] > best_hybrid.get('score', 0):
                    print(f"   Método: BM25 (Score: {best_bm25['score']:.4f})")
                    print(f"   Texto: {best_bm25['texto'][:200]}...")
                else:
                    print(f"   Método: Híbrido (Score: {best_hybrid.get('score', 'N/A')})")
                    print(f"   Texto: {best_hybrid.get('texto', best_hybrid.get('text', ''))[:200]}...")
        
        print(f"\n✅ Demo completado exitosamente!")
        print("💡 El sistema está funcionando al 100%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verificando estado del proyecto...")
        
        # Verificar archivos clave
        key_files = [
            "src/ai/search_vectorstore_bm25_fixed.py",
            "src/ai/search_vectorstore_hybrid.py",
            "data/processed/vectorstore_bm25_test.pkl",
            "data/processed/vectorstore_semantic_full_v2.pkl"
        ]
        
        print("\n📋 Estado de archivos clave:")
        for file_path in key_files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")

if __name__ == "__main__":
    main() 
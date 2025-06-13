#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo del Sistema de Búsqueda Híbrido MINEDU

Uso: python demo.py "tu consulta aquí"
"""
import sys
import os
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python demo.py 'tu consulta aquí'")
        print("Ejemplo: python demo.py '¿Cuál es el monto máximo para viáticos?'")
        print("\nConsultas de ejemplo:")
        print("  - ¿Cuál es el monto máximo diario para viáticos nacionales?")
        print("  - ¿Quién autoriza los viáticos en el MINEDU?")
        print("  - ¿Qué documentos se requieren para solicitar viáticos?")
        print("  - ¿Cuántos días antes debo solicitar viáticos?")
        return
    
    query = " ".join(sys.argv[1:])
    
    print(f"\n🔍 Buscando: {query}")
    print("-" * 50)
    
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
            print("💡 Ejecuta primero: python src/data_pipeline/generate_vectorstores.py")
            return
        
        # Importar y usar el sistema híbrido
        try:
            from src.core.hybrid import HybridSearch
            
            # Inicializar búsqueda híbrida
            searcher = HybridSearch(
                bm25_vectorstore_path=vectorstore_paths['bm25'],
                tfidf_vectorstore_path=vectorstore_paths['tfidf'],
                transformer_vectorstore_path=vectorstore_paths['transformer']
            )
            
            # Realizar búsqueda
            results = searcher.search(query, top_k=3)
            
            # Mostrar resultados
            print(f"\n📊 Encontrados {len(results)} resultados:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. Score: {result['score']:.3f}")
                print(f"   {result['texto'][:200]}...")
                print(f"   Método: {result.get('method', 'Híbrido')}")
                if 'methods_used' in result:
                    print(f"   Métodos combinados: {', '.join(result['methods_used'])}")
                print()
                
        except ImportError as e:
            print(f"❌ Error de importación: {e}")
            print("💡 Asegúrate de que todas las dependencias estén instaladas")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de que los vectorstores estén generados primero.")
        print("   Ejecuta: python src/data_pipeline/generate_vectorstores.py")

if __name__ == "__main__":
    main()

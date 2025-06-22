#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo del Sistema de Búsqueda Híbrido MINEDU

Uso: python demo.py "tu consulta aquí"
"""
import sys
from src.core.hybrid import HybridSearch

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python demo.py 'tu consulta aquí'")
        print("Ejemplo: python demo.py '¿Cuál es el monto máximo para viáticos?'")
        return
    
    query = " ".join(sys.argv[1:])
    
    print(f"\n🔍 Buscando: {query}")
    print("-" * 50)
    
    try:
        # Inicializar búsqueda híbrida
        searcher = HybridSearch(
            bm25_vectorstore_path="data/vectorstores/bm25.pkl",
            tfidf_vectorstore_path="data/vectorstores/tfidf.pkl",
            transformer_vectorstore_path="data/vectorstores/transformers.pkl"
        )
        
        # Realizar búsqueda
        results = searcher.search(query, top_k=3)
        
        # Mostrar resultados
        print(f"\n📊 Encontrados {len(results)} resultados:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.3f}")
            print(f"   {result['texto'][:200]}...")
            print(f"   Método: {result.get('method', 'Híbrido')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de que los vectorstores estén generados primero.")

if __name__ == "__main__":
    main()

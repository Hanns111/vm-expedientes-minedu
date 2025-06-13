#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspección detallada del vectorstore BM25
"""

import pickle
import json

def inspeccionar_bm25():
    print("=== INSPECCIÓN DETALLADA BM25 ===")
    
    # Cargar vectorstore BM25
    with open('data/processed/vectorstore_bm25_test.pkl', 'rb') as f:
        vs = pickle.load(f)
    
    print(f"Tipo de vectorstore: {type(vs)}")
    print(f"Claves disponibles: {list(vs.keys())}")
    
    # Verificar cada componente
    for key, value in vs.items():
        print(f"\n--- {key} ---")
        if key == 'chunks':
            print(f"Tipo: {type(value)}")
            print(f"Cantidad: {len(value)}")
            if value:
                print(f"Primer chunk: {list(value[0].keys())}")
                print(f"Ejemplo texto: {value[0].get('texto', '')[:100]}...")
        elif key == 'bm25_model':
            print(f"Tipo: {type(value)}")
            if hasattr(value, 'corpus_size'):
                print(f"Corpus size: {value.corpus_size}")
        else:
            print(f"Tipo: {type(value)}")
            print(f"Valor: {value}")
    
    # Probar búsqueda directa
    print("\n=== PRUEBA DE BÚSQUEDA DIRECTA ===")
    
    if 'bm25_model' in vs and 'chunks' in vs:
        bm25 = vs['bm25_model']
        chunks = vs['chunks']
        
        query = "viáticos"
        query_tokens = query.lower().split()
        
        print(f"Query: '{query}'")
        print(f"Tokens: {query_tokens}")
        
        try:
            scores = bm25.get_scores(query_tokens)
            print(f"Scores obtenidos: {len(scores)}")
            print(f"Score máximo: {max(scores)}")
            print(f"Score mínimo: {min(scores)}")
            
            # Top 3 resultados
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
            
            print(f"\nTop 3 resultados:")
            for i, idx in enumerate(top_indices):
                score = scores[idx]
                chunk = chunks[idx]
                print(f"\n{i+1}. Score: {score:.4f}")
                print(f"   Texto: {chunk.get('texto', '')[:100]}...")
                
        except Exception as e:
            print(f"Error en búsqueda: {e}")
    else:
        print("❌ Faltan componentes necesarios")

if __name__ == "__main__":
    inspeccionar_bm25() 
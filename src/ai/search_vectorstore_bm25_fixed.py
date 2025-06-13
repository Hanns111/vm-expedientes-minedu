#!/usr/bin/env python3
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
        text = re.sub(r'[^a-záéíóúüñ\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# Función de prueba
def test_fixed_bm25():
    vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
    search = BM25SearchFixed(vectorstore_path)
    
    query = "¿Cuál es el monto máximo para viáticos?"
    results = search.search(query, top_k=3)
    
    print(f"🔍 Resultados BM25 Corregido: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\n📄 Resultado {i}:")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Título: {result['titulo']}")
        print(f"  Texto: {result['texto'][:100]}...")
    
    return results

if __name__ == "__main__":
    results = test_fixed_bm25()

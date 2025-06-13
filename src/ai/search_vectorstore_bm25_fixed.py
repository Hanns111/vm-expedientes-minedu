#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 Search - Versión Corregida con Formato Consistente
Aplicando las mismas técnicas que funcionaron para TF-IDF y Transformers
"""

import pickle
import time
from rank_bm25 import BM25Okapi
import re
import logging

class BM25SearchFixed:
    """BM25Search con formato de salida corregido - Aplicando técnicas exitosas"""
    
    def __init__(self, vectorstore_path):
        self.vectorstore_path = vectorstore_path
        
        # Configurar logging PRIMERO
        self._setup_logging()
        
        # Luego cargar vectorstore
        self.vectorstore = self._load_vectorstore()
        self.bm25 = self.vectorstore.get('bm25_index')
        self.chunks = self.vectorstore.get('chunks', [])
        
    def _setup_logging(self):
        """Configurar logging como en otros sistemas"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger('BM25SearchFixed')
        
    def _load_vectorstore(self):
        """Cargar vectorstore de BM25"""
        try:
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            self.logger.info(f"Vectorstore BM25 cargado con {len(vectorstore.get('chunks', []))} chunks")
            return vectorstore
        except Exception as e:
            self.logger.error(f"Error cargando vectorstore: {e}")
            return {}
    
    def search(self, query, top_k=5):
        """Búsqueda BM25 con formato de salida normalizado - Aplicando técnicas exitosas"""
        if not self.bm25 or not self.chunks:
            self.logger.warning("BM25 o chunks no disponibles")
            return []
        
        try:
            self.logger.info(f"Realizando búsqueda BM25 para: '{query}'")
            start_time = time.time()
            
            query_tokens = self._preprocess_text(query).split()
            self.logger.info(f"Query preprocesada: {query_tokens}")
            
            scores = self.bm25.get_scores(query_tokens)
            
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    chunk = self.chunks[idx]
                    
                    result = {
                        'score': float(scores[idx]),
                        'texto': str(chunk.get('texto', chunk.get('text', ''))),
                        'titulo': str(chunk.get('titulo', chunk.get('title', f'Resultado {idx+1}'))),
                        'metadatos': chunk.get('metadatos', {}),
                        'source': 'bm25',
                        'index': idx
                    }
                    results.append(result)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Búsqueda completada en {elapsed_time:.4f} segundos, {len(results)} resultados encontrados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda BM25: {e}")
            return []
    
    def _preprocess_text(self, text):
        """Preprocesamiento básico de texto - Misma técnica que otros sistemas"""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'[^a-záéíóúüñ\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# Función de prueba mejorada
def test_fixed_bm25():
    """Prueba completa del BM25 corregido"""
    print("🔧 PROBANDO BM25 CORREGIDO")
    print("=" * 50)
    
    vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
    search = BM25SearchFixed(vectorstore_path)
    
    query = "¿Cuál es el monto máximo para viáticos?"
    results = search.search(query, top_k=3)
    
    print(f"\n🔍 Resultados BM25 Corregido: {len(results)}")
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n📄 Resultado {i}:")
            print(f"  Score: {result['score']:.4f}")
            print(f"  Título: {result['titulo']}")
            print(f"  Texto: {result['texto'][:150]}...")
    else:
        print("❌ No se obtuvieron resultados")
    
    return results

if __name__ == "__main__":
    results = test_fixed_bm25()

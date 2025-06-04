#!/usr/bin/env python3
"""
Script de búsqueda para la DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf
Realiza búsquedas semánticas sobre el documento procesado.
"""

import os
import sys
import pickle
import json
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
VECTORSTORE_FILE = "vectorstore_directiva_limpia.pkl"
CHUNKS_FILE = "chunks_directiva_limpia.json"

class DirectivaLimpiaSearcher:
    def __init__(self):
        self.vectorstore = None
        self.chunks = None
        self.loaded = False
        
    def load_vectorstore(self):
        """Carga el vectorstore desde el archivo pickle"""
        vectorstore_path = PROCESSED_DATA_PATH / VECTORSTORE_FILE
        
        if not vectorstore_path.exists():
            print(f"❌ Error: No se encontró el vectorstore {VECTORSTORE_FILE}")
            print(f"📁 Esperado en: {vectorstore_path}")
            print("💡 Ejecuta primero el script de procesamiento")
            return False
        
        try:
            with open(vectorstore_path, 'rb') as f:
                self.vectorstore = pickle.load(f)
            
            self.chunks = self.vectorstore['chunks']
            self.loaded = True
            
            print(f"✅ Vectorstore cargado exitosamente")
            print(f"📊 Chunks disponibles: {len(self.chunks)}")
            print(f"📊 Dimensión de vectores: {self.vectorstore['tfidf_matrix'].shape[1]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar vectorstore: {str(e)}")
            return False
    
    def search(self, query, top_k=5):
        """Realiza búsqueda semántica en la directiva"""
        if not self.loaded:
            print("❌ Vectorstore no cargado. Ejecuta load_vectorstore() primero.")
            return []
        
        print(f"🔍 Buscando: '{query}'")
        print("-" * 50)
        
        try:
            # Vectorizar la consulta
            query_vector = self.vectorstore['vectorizer'].transform([query])
            
            # Buscar vecinos más cercanos
            distances, indices = self.vectorstore['nn_model'].kneighbors(
                query_vector, n_neighbors=min(top_k, len(self.chunks))
            )
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                chunk = self.chunks[idx]
                similarity = 1 - distance  # Convertir distancia a similitud
                
                result = {
                    'rank': i + 1,
                    'chunk_id': chunk['id'],
                    'similarity': similarity,
                    'pages': chunk.get('pages', []),
                    'text': chunk['text'],
                    'word_count': chunk.get('word_count', 0),
                    'source_file': chunk.get('source_file', '')
                }
                results.append(result)
            
            # Mostrar resultados
            self.display_results(query, results)
            return results
            
        except Exception as e:
            print(f"❌ Error en la búsqueda: {str(e)}")
            return []
    
    def display_results(self, query, results):
        """Muestra los resultados de búsqueda formateados"""
        if not results:
            print("❌ No se encontraron resultados")
            return
        
        print(f"📋 Resultados para: '{query}'")
        print(f"🎯 Se encontraron {len(results)} resultados relevantes\n")
        
        for result in results:
            print(f"🔹 Resultado #{result['rank']}")
            print(f"📄 Páginas: {', '.join(map(str, result['pages']))}")
            print(f"🎯 Similitud: {result['similarity']:.3f}")
            print(f"📝 Palabras: {result['word_count']}")
            print(f"📋 Texto:")
            
            # Mostrar texto con resaltado de la consulta
            text_preview = self.highlight_query_in_text(query, result['text'][:500])
            print(f"   {text_preview}...")
            print("-" * 50)
    
    def highlight_query_in_text(self, query, text):
        """Resalta las palabras de la consulta en el texto"""
        query_words = query.lower().split()
        highlighted_text = text
        
        for word in query_words:
            if len(word) > 2:  # Solo resaltar palabras de 3+ caracteres
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted_text = pattern.sub(f"**{word.upper()}**", highlighted_text)
        
        return highlighted_text
    
    def search_interactive(self):
        """Modo interactivo de búsqueda"""
        if not self.load_vectorstore():
            return
        
        print("🎯 Modo de búsqueda interactiva para la Directiva MINEDU")
        print("💡 Escribe 'salir' para terminar, 'info' para ver información del documento")
        print("=" * 60)
        
        while True:
            try:
                query = input("\n🔍 Ingresa tu consulta: ").strip()
                
                if query.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if query.lower() == 'info':
                    self.show_document_info()
                    continue
                
                if not query:
                    print("⚠️ Por favor ingresa una consulta válida")
                    continue
                
                # Realizar búsqueda
                results = self.search(query)
                
                if results:
                    # Preguntar si quiere ver más detalles
                    response = input(f"\n¿Ver más detalles del resultado #1? (s/n): ").strip().lower()
                    if response in ['s', 'si', 'yes', 'y']:
                        self.show_detailed_result(results[0])
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def show_document_info(self):
        """Muestra información del documento procesado"""
        if not self.loaded:
            return
        
        print("\n📄 INFORMACIÓN DEL DOCUMENTO")
        print("=" * 40)
        print(f"📋 Archivo: {self.vectorstore['metadata']['source_file']}")
        print(f"📊 Total de chunks: {self.vectorstore['metadata']['total_chunks']}")
        print(f"🔍 Dimensión de vectores: {self.vectorstore['metadata']['vector_dimension']}")
        print(f"📅 Procesado el: {self.vectorstore['metadata']['created_at']}")
        print(f"🤖 Modelo: {self.vectorstore['metadata']['model_type']}")
        
        # Estadísticas de los chunks
        total_words = sum(chunk.get('word_count', 0) for chunk in self.chunks)
        avg_words = total_words / len(self.chunks) if self.chunks else 0
        
        print(f"📝 Total de palabras: {total_words:,}")
        print(f"📊 Promedio de palabras por chunk: {avg_words:.0f}")
        
        # Páginas cubiertas
        all_pages = set()
        for chunk in self.chunks:
            all_pages.update(chunk.get('pages', []))
        
        print(f"📄 Páginas cubiertas: {len(all_pages)} ({min(all_pages) if all_pages else 0}-{max(all_pages) if all_pages else 0})")
    
    def show_detailed_result(self, result):
        """Muestra un resultado detallado"""
        print(f"\n📋 DETALLE DEL RESULTADO #{result['rank']}")
        print("=" * 50)
        print(f"🆔 ID del chunk: {result['chunk_id']}")
        print(f"📄 Páginas: {', '.join(map(str, result['pages']))}")
        print(f"🎯 Similitud: {result['similarity']:.4f}")
        print(f"📝 Palabras: {result['word_count']}")
        print(f"📋 Texto completo:")
        print("-" * 30)
        print(result['text'])
        print("-" * 30)

def main():
    """Función principal"""
    searcher = DirectivaLimpiaSearcher()
    
    print("🎯 Buscador de la Directiva MINEDU Limpia")
    print("=" * 50)
    
    # Cargar vectorstore
    if not searcher.load_vectorstore():
        print("💡 Ejecuta primero: python src/ai/process_clean_directive.py")
        return False
    
    # Modo interactivo
    searcher.search_interactive()
    
    return True

if __name__ == "__main__":
    main()
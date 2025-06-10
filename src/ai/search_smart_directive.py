#!/usr/bin/env python3
"""
Buscador inteligente para la DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf
Combina búsqueda exacta, semántica y por similitud
"""

import os
import sys
import pickle
import json
import re
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
VECTORSTORE_FILE = "vectorstore_directiva_limpia.pkl"

class SmartDirectiveSearcher:
    def __init__(self):
        self.vectorstore = None
        self.chunks = None
        self.loaded = False
        
    def load_vectorstore(self):
        """Carga el vectorstore desde el archivo pickle"""
        vectorstore_path = PROCESSED_DATA_PATH / VECTORSTORE_FILE
        
        if not vectorstore_path.exists():
            print(f"❌ Error: No se encontró el vectorstore {VECTORSTORE_FILE}")
            return False
        
        try:
            with open(vectorstore_path, 'rb') as f:
                self.vectorstore = pickle.load(f)
            
            self.chunks = self.vectorstore['chunks']
            self.loaded = True
            
            print(f"✅ Vectorstore cargado exitosamente")
            print(f"📊 Chunks disponibles: {len(self.chunks)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar vectorstore: {str(e)}")
            return False
    
    def exact_search(self, query):
        """Búsqueda exacta de términos en el texto"""
        results = []
        
        # Limpiar la consulta para búsqueda exacta
        query_clean = query.lower().strip()
        
        for i, chunk in enumerate(self.chunks):
            text_lower = chunk['text'].lower()
            
            # Buscar coincidencias exactas
            if query_clean in text_lower:
                # Calcular relevancia basada en frecuencia y posición
                frequency = text_lower.count(query_clean)
                position_bonus = 1.0 if text_lower.find(query_clean) < len(text_lower) / 3 else 0.5
                
                relevance = frequency * position_bonus
                
                # Extraer contexto alrededor de la coincidencia
                match_pos = text_lower.find(query_clean)
                start = max(0, match_pos - 100)
                end = min(len(chunk['text']), match_pos + len(query_clean) + 100)
                context = chunk['text'][start:end]
                
                results.append({
                    'chunk_id': chunk['id'],
                    'chunk_index': i,
                    'relevance': relevance,
                    'match_type': 'exact',
                    'pages': chunk.get('pages', []),
                    'text': chunk['text'],
                    'context': context,
                    'frequency': frequency
                })
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)
    
    def semantic_search(self, query, top_k=5):
        """Búsqueda semántica usando TF-IDF"""
        try:
            # Vectorizar la consulta
            query_vector = self.vectorstore['vectorizer'].transform([query])
            
            # Buscar vecinos más cercanos
            distances, indices = self.vectorstore['nn_model'].kneighbors(
                query_vector, n_neighbors=min(top_k, len(self.chunks))
            )
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                similarity = 1 - distance
                
                # Solo incluir resultados con similitud mínima
                if similarity > 0.01:
                    results.append({
                        'chunk_id': self.chunks[idx]['id'],
                        'chunk_index': idx,
                        'relevance': similarity,
                        'match_type': 'semantic',
                        'pages': self.chunks[idx].get('pages', []),
                        'text': self.chunks[idx]['text'],
                        'context': self.chunks[idx]['text'][:200] + "...",
                        'similarity': similarity
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Error en búsqueda semántica: {str(e)}")
            return []
    
    def smart_search(self, query, top_k=5):
        """Búsqueda inteligente que combina métodos"""
        print(f"🔍 Búsqueda inteligente: '{query}'")
        print("=" * 60)
        
        # 1. Búsqueda exacta (prioritaria)
        exact_results = self.exact_search(query)
        
        # 2. Búsqueda semántica
        semantic_results = self.semantic_search(query, top_k)
        
        # 3. Combinar y deduplicar resultados
        combined_results = {}
        
        # Priorizar resultados exactos
        for result in exact_results:
            chunk_idx = result['chunk_index']
            combined_results[chunk_idx] = result
            combined_results[chunk_idx]['combined_score'] = result['relevance'] + 2.0  # Bonus por exactitud
        
        # Agregar resultados semánticos que no estén ya incluidos
        for result in semantic_results:
            chunk_idx = result['chunk_index']
            if chunk_idx not in combined_results:
                combined_results[chunk_idx] = result
                combined_results[chunk_idx]['combined_score'] = result['relevance']
            else:
                # Si ya existe, mejorar el score combinando ambos métodos
                combined_results[chunk_idx]['combined_score'] += result['relevance']
                combined_results[chunk_idx]['match_type'] = 'exact+semantic'
        
        # Ordenar por score combinado
        final_results = sorted(combined_results.values(), 
                             key=lambda x: x['combined_score'], reverse=True)
        
        return final_results[:top_k]
    
    def display_smart_results(self, query, results):
        """Muestra los resultados de búsqueda inteligente"""
        if not results:
            print("❌ No se encontraron resultados")
            self.suggest_alternatives(query)
            return
        
        print(f"🎯 Se encontraron {len(results)} resultados relevantes para: '{query}'\n")
        
        for i, result in enumerate(results, 1):
            print(f"🔹 Resultado #{i}")
            print(f"📄 Páginas: {', '.join(map(str, result['pages']))}")
            print(f"🎯 Tipo: {result['match_type']}")
            print(f"📊 Relevancia: {result['combined_score']:.3f}")
            
            if result['match_type'] == 'exact':
                print(f"🔍 Coincidencias exactas: {result.get('frequency', 1)}")
                print(f"📋 Contexto: ...{result['context']}...")
            else:
                print(f"📋 Preview: {result['context']}")
            
            print("-" * 50)
    
    def suggest_alternatives(self, query):
        """Sugiere búsquedas alternativas"""
        print("💡 Sugerencias de búsqueda:")
        
        # Sugerencias específicas según el tipo de consulta
        if query.isdigit():
            print(f"   - 'S/ {query}'")
            print(f"   - '{query}.00'")
            print(f"   - 'soles'")
        
        if any(word in query.lower() for word in ['viático', 'viatico']):
            print("   - 'escala de viáticos'")
            print("   - 'viático por día'")
            print("   - 'comisión de servicios'")
        
        if any(word in query.lower() for word in ['responsabilidad', 'responsable']):
            print("   - 'disposiciones generales'")
            print("   - 'jefe de órgano'")
            print("   - 'marco normativo'")
        
        print("   - 'ministro'")
        print("   - 'servidores públicos'")
        print("   - 'planilla de viáticos'")
    
    def search_interactive(self):
        """Modo interactivo de búsqueda inteligente"""
        if not self.load_vectorstore():
            return
        
        print("🎯 BUSCADOR INTELIGENTE - Directiva MINEDU")
        print("💡 Combina búsqueda exacta y semántica para mejores resultados")
        print("💡 Escribe 'salir' para terminar, 'ayuda' para consejos")
        print("=" * 60)
        
        while True:
            try:
                query = input("\n🔍 Ingresa tu consulta: ").strip()
                
                if query.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if query.lower() in ['ayuda', 'help']:
                    self.show_help()
                    continue
                
                if not query:
                    print("⚠️ Por favor ingresa una consulta válida")
                    continue
                
                # Realizar búsqueda inteligente
                results = self.smart_search(query)
                self.display_smart_results(query, results)
                
                if results:
                    response = input(f"\n¿Ver texto completo del resultado #1? (s/n): ").strip().lower()
                    if response in ['s', 'si', 'yes', 'y']:
                        self.show_full_result(results[0])
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def show_help(self):
        """Muestra consejos de búsqueda"""
        print("\n📚 CONSEJOS DE BÚSQUEDA:")
        print("=" * 40)
        print("🔹 Para montos: '320', 'S/ 320', 'trescientos'")
        print("🔹 Para viáticos: 'viático', 'escala', 'por día'")
        print("🔹 Para responsabilidades: 'responsabilidad', 'jefe'")
        print("🔹 Para procedimientos: 'tramitación', 'planilla'")
        print("🔹 Para autorización: 'ministro', 'autorización'")
        print("🔹 El buscador encuentra coincidencias exactas Y semánticas")
    
    def show_full_result(self, result):
        """Muestra un resultado completo"""
        print(f"\n📋 TEXTO COMPLETO - Resultado #{result.get('chunk_index', 0)}")
        print("=" * 60)
        print(f"🆔 ID: {result['chunk_id']}")
        print(f"📄 Páginas: {', '.join(map(str, result['pages']))}")
        print(f"🎯 Tipo: {result['match_type']}")
        print(f"📊 Relevancia: {result['combined_score']:.4f}")
        print("-" * 40)
        print(result['text'])
        print("-" * 40)

def main():
    """Función principal"""
    searcher = SmartDirectiveSearcher()
    searcher.search_interactive()

if __name__ == "__main__":
    main()
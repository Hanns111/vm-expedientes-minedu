#!/usr/bin/env python3
"""
Script para procesar únicamente la DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf
Genera chunks y vectorstore específicamente para el documento limpio.
"""

import os
import sys
import json
import pickle
from pathlib import Path
import fitz  # PyMuPDF - CORREGIDO
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
PDF_FILE = "DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf"

class DirectivaLimpiaProcessor:
    def __init__(self):
        self.pdf_path = RAW_DATA_PATH / PDF_FILE
        self.chunks = []
        self.metadata = {}
        
    def verify_file_exists(self):
        """Verifica que el archivo PDF existe"""
        if not self.pdf_path.exists():
            print(f"❌ Error: No se encontró el archivo {PDF_FILE}")
            print(f"📁 Buscando en: {self.pdf_path}")
            return False
        
        print(f"✅ Archivo encontrado: {PDF_FILE}")
        print(f"📁 Ubicación: {self.pdf_path}")
        return True
    
    def extract_text_from_pdf(self):
        """Extrae texto del PDF página por página"""
        print(f"📖 Extrayendo texto de {PDF_FILE}...")
        
        try:
            doc = fitz.open(self.pdf_path)
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                page_texts.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'char_count': len(text)
                })
                full_text += f"\n--- PÁGINA {page_num + 1} ---\n{text}\n"
            
            doc.close()
            
            print(f"✅ Texto extraído exitosamente")
            print(f"📊 Total de páginas: {len(page_texts)}")
            print(f"📊 Total de caracteres: {len(full_text)}")
            
            return full_text, page_texts
            
        except Exception as e:
            print(f"❌ Error al extraer texto: {str(e)}")
            return None, None
    
    def clean_text(self, text):
        """Limpia y normaliza el texto extraído"""
        if not text:
            return ""
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalizar líneas
        text = text.strip()
        
        return text
    
    def create_chunks(self, full_text, page_texts, chunk_size=1000, overlap=200):
        """Crea chunks del texto con metadatos mejorados"""
        print(f"🔧 Creando chunks (tamaño: {chunk_size}, overlap: {overlap})...")
        
        chunks = []
        words = full_text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunk_text = self.clean_text(chunk_text)
            
            # Determinar páginas que abarca este chunk
            chunk_pages = []
            for page_info in page_texts:
                if any(word in page_info['text'] for word in chunk_words[:10] if len(word) > 3):
                    chunk_pages.append(page_info['page_number'])
            
            chunk_info = {
                'id': f"chunk_{len(chunks)}",
                'text': chunk_text,
                'word_count': len(chunk_words),
                'char_count': len(chunk_text),
                'chunk_index': len(chunks),
                'pages': chunk_pages[:5] if chunk_pages else [1],  # Máximo 5 páginas por chunk
                'source_file': PDF_FILE,
                'created_at': datetime.now().isoformat()
            }
            
            chunks.append(chunk_info)
        
        print(f"✅ Creados {len(chunks)} chunks")
        return chunks
    
    def save_chunks_to_json(self, chunks):
        """Guarda los chunks en formato JSON"""
        output_file = PROCESSED_DATA_PATH / "chunks_directiva_limpia.json"
        
        try:
            PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Chunks guardados en: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar chunks: {str(e)}")
            return False
    
    def create_vectorstore(self, chunks):
        """Crea vectorstore usando TF-IDF"""
        print("🔍 Creando vectorstore con TF-IDF...")
        
        try:
            # Extraer textos para vectorización
            texts = [chunk['text'] for chunk in chunks]
            
            # Crear vectorizador TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words=None,  # No usar stop words para español
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                lowercase=True
            )
            
            # Crear matriz TF-IDF
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Crear modelo de vecinos más cercanos
            nn_model = NearestNeighbors(
                n_neighbors=min(10, len(chunks)),
                metric='cosine',
                algorithm='brute'
            )
            nn_model.fit(tfidf_matrix)
            
            # Crear vectorstore
            vectorstore = {
                'vectorizer': vectorizer,
                'tfidf_matrix': tfidf_matrix,
                'nn_model': nn_model,
                'chunks': chunks,
                'metadata': {
                    'source_file': PDF_FILE,
                    'total_chunks': len(chunks),
                    'vector_dimension': tfidf_matrix.shape[1],
                    'created_at': datetime.now().isoformat(),
                    'model_type': 'TF-IDF + NearestNeighbors'
                }
            }
            
            print(f"✅ Vectorstore creado exitosamente")
            print(f"📊 Dimensión de vectores: {tfidf_matrix.shape[1]}")
            print(f"📊 Total de chunks: {len(chunks)}")
            
            return vectorstore
            
        except Exception as e:
            print(f"❌ Error al crear vectorstore: {str(e)}")
            return None
    
    def save_vectorstore(self, vectorstore):
        """Guarda el vectorstore en archivo pickle"""
        output_file = PROCESSED_DATA_PATH / "vectorstore_directiva_limpia.pkl"
        
        try:
            with open(output_file, 'wb') as f:
                pickle.dump(vectorstore, f)
            
            print(f"✅ Vectorstore guardado en: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar vectorstore: {str(e)}")
            return False
    
    def process_complete_pipeline(self):
        """Ejecuta el pipeline completo de procesamiento"""
        print("🚀 Iniciando procesamiento completo de la directiva limpia...")
        print("=" * 60)
        
        # 1. Verificar archivo
        if not self.verify_file_exists():
            return False
        
        # 2. Extraer texto
        full_text, page_texts = self.extract_text_from_pdf()
        if not full_text:
            return False
        
        # 3. Crear chunks
        chunks = self.create_chunks(full_text, page_texts)
        if not chunks:
            return False
        
        # 4. Guardar chunks
        if not self.save_chunks_to_json(chunks):
            return False
        
        # 5. Crear vectorstore
        vectorstore = self.create_vectorstore(chunks)
        if not vectorstore:
            return False
        
        # 6. Guardar vectorstore
        if not self.save_vectorstore(vectorstore):
            return False
        
        print("=" * 60)
        print("🎉 ¡Procesamiento completado exitosamente!")
        print(f"📄 Documento procesado: {PDF_FILE}")
        print(f"📊 Chunks generados: {len(chunks)}")
        print(f"🔍 Vectorstore listo para búsquedas")
        
        return True

def main():
    """Función principal"""
    processor = DirectivaLimpiaProcessor()
    success = processor.process_complete_pipeline()
    
    if success:
        print("\n✅ El sistema está listo para realizar búsquedas sobre la directiva limpia.")
        print("📝 Próximo paso: usar el script de búsqueda para consultar el documento.")
    else:
        print("\n❌ Hubo errores en el procesamiento. Revisar los mensajes anteriores.")
    
    return success

if __name__ == "__main__":
    main()
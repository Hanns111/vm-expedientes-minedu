#!/usr/bin/env python3
"""
Script simple para procesar el PDF original y generar chunks y vectorstore
"""

import os
import sys
import json
import pickle
from pathlib import Path
import fitz  # PyMuPDF
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import re
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """Extrae texto del PDF"""
    print(f"📖 Extrayendo texto de: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
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

def clean_text(text):
    """Limpia y normaliza el texto"""
    if not text:
        return ""
    
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar caracteres de control
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()

def create_chunks(full_text, page_texts, chunk_size=800, overlap=100):
    """Crea chunks inteligentes del texto"""
    print(f"🔧 Creando chunks (tamaño: {chunk_size}, overlap: {overlap})...")
    
    chunks = []
    words = full_text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        chunk_text = clean_text(chunk_text)
        
        if len(chunk_text.strip()) < 50:  # Saltar chunks muy pequeños
            continue
        
        # Detectar páginas
        chunk_pages = []
        for page_info in page_texts:
            # Buscar palabras clave del chunk en la página
            key_words = [w for w in chunk_words[:10] if len(w) > 4]
            if any(word in page_info['text'] for word in key_words):
                chunk_pages.append(page_info['page_number'])
        
        chunk_info = {
            'id': f"chunk_{len(chunks)}",
            'text': chunk_text,
            'word_count': len(chunk_words),
            'char_count': len(chunk_text),
            'chunk_index': len(chunks),
            'pages': chunk_pages[:3] if chunk_pages else [1],
            'source_file': "directiva_de_viaticos_011_2020_imagen.pdf",
            'created_at': datetime.now().isoformat()
        }
        
        chunks.append(chunk_info)
    
    print(f"✅ Creados {len(chunks)} chunks válidos")
    return chunks

def save_chunks_to_json(chunks, output_path):
    """Guarda chunks en JSON"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Chunks guardados en: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar chunks: {str(e)}")
        return False

def create_vectorstore(chunks, output_path):
    """Crea y guarda vectorstore"""
    print("🔍 Creando vectorstore con TF-IDF...")
    
    try:
        # Extraer textos
        texts = [chunk['text'] for chunk in chunks]
        
        # Crear vectorizador TF-IDF optimizado para español
        vectorizer = TfidfVectorizer(
            max_features=8000,
            stop_words=None,  # Mantener todas las palabras
            ngram_range=(1, 2),  # Unigrams y bigrams
            min_df=1,
            max_df=0.95,
            lowercase=True,
            token_pattern=r'\b[a-záéíóúüñ]{2,}\b'  # Patrón para español
        )
        
        # Crear matriz TF-IDF
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Crear modelo de vecinos más cercanos
        nn_model = NearestNeighbors(
            n_neighbors=min(15, len(chunks)),
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
                'source_file': "directiva_de_viaticos_011_2020_imagen.pdf",
                'total_chunks': len(chunks),
                'vector_dimension': tfidf_matrix.shape[1],
                'created_at': datetime.now().isoformat(),
                'model_type': 'TF-IDF + NearestNeighbors',
                'chunk_size': 800,
                'overlap': 100
            }
        }
        
        # Guardar vectorstore
        with open(output_path, 'wb') as f:
            pickle.dump(vectorstore, f)
        
        print(f"✅ Vectorstore creado y guardado")
        print(f"📊 Dimensión de vectores: {tfidf_matrix.shape[1]}")
        print(f"📊 Total de chunks: {len(chunks)}")
        print(f"💾 Guardado en: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear vectorstore: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 PROCESAMIENTO DE PDF ORIGINAL - DIRECTIVA VIÁTICOS")
    print("=" * 60)
    
    # Rutas - ACTUALIZADO con el nombre preferido por el usuario
    pdf_path = "data/raw/directiva_de_viaticos_011_2020_imagen.pdf"
    chunks_output = "data/processed/chunks_directiva_limpia.json"
    vectorstore_output = "data/processed/vectorstore_directiva_limpia.pkl"
    
    # Verificar que existe el PDF
    if not os.path.exists(pdf_path):
        print(f"❌ Error: No se encontró el archivo PDF en: {pdf_path}")
        return False
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"📄 PDF encontrado: {file_size:.1f} MB")
    
    # 1. Extraer texto
    full_text, page_texts = extract_text_from_pdf(pdf_path)
    if not full_text:
        return False
    
    # 2. Crear chunks
    chunks = create_chunks(full_text, page_texts)
    if not chunks:
        return False
    
    # 3. Guardar chunks
    if not save_chunks_to_json(chunks, chunks_output):
        return False
    
    # 4. Crear y guardar vectorstore
    if not create_vectorstore(chunks, vectorstore_output):
        return False
    
    print("=" * 60)
    print("🎉 ¡PROCESAMIENTO COMPLETADO EXITOSAMENTE!")
    print(f"📊 {len(chunks)} chunks generados")
    print(f"📄 Chunks: {chunks_output}")
    print(f"🔍 Vectorstore: {vectorstore_output}")
    print("🔍 Sistema listo para búsquedas inteligentes")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ El procesamiento falló. Revisa los errores anteriores.")
        sys.exit(1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de generación de vectorstores para el Sistema de Búsqueda Híbrido MINEDU.

Este script genera todos los vectorstores necesarios para el sistema:
- BM25 vectorstore
- TF-IDF vectorstore  
- Transformer vectorstore
"""

import json
import pickle
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class VectorstoreGenerator:
    """
    Generador de vectorstores para diferentes métodos de búsqueda.
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.chunks = []
        
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging."""
        logger = logging.getLogger('VectorstoreGenerator')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_chunks(self, chunks_file: str = "data/processed/chunks.json") -> None:
        """
        Cargar chunks desde archivo JSON.
        
        Args:
            chunks_file (str): Ruta al archivo de chunks
        """
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            self.logger.info(f"Chunks cargados: {len(self.chunks)} fragmentos")
        except FileNotFoundError:
            self.logger.warning(f"Archivo {chunks_file} no encontrado. Usando chunks de ejemplo.")
            self._create_sample_chunks()
        except Exception as e:
            self.logger.error(f"Error cargando chunks: {e}")
            raise
    
    def _create_sample_chunks(self) -> None:
        """Crear chunks de ejemplo si no existen."""
        self.chunks = [
            {
                "id": 1,
                "texto": "El monto máximo diario para viáticos nacionales es de S/ 320.00 según la escala vigente.",
                "titulo": "Escala de Viáticos Nacionales",
                "metadatos": {"page": 1, "type": "normativa", "section": "viáticos"}
            },
            {
                "id": 2,
                "texto": "Los viáticos deben ser solicitados con diez (10) días hábiles de anticipación a la fecha programada para el viaje.",
                "titulo": "Plazo de Solicitud de Viáticos",
                "metadatos": {"page": 2, "type": "normativa", "section": "solicitud"}
            },
            {
                "id": 3,
                "texto": "El comisionado debe presentar una Declaración Jurada de Gastos para sustentar los gastos realizados.",
                "titulo": "Declaración Jurada de Gastos",
                "metadatos": {"page": 3, "type": "normativa", "section": "rendición"}
            }
        ]
        self.logger.info("Chunks de ejemplo creados")
    
    def generate_bm25_vectorstore(self, output_path: str = "data/vectorstores/bm25.pkl") -> None:
        """
        Generar vectorstore para BM25.
        
        Args:
            output_path (str): Ruta de salida para el vectorstore
        """
        self.logger.info("Generando vectorstore BM25...")
        start_time = time.time()
        
        # Preparar textos para BM25
        texts = []
        for chunk in self.chunks:
            text = chunk.get('texto', chunk.get('text', ''))
            # Tokenizar texto
            tokens = text.lower().split()
            texts.append(tokens)
        
        # Crear modelo BM25
        bm25 = BM25Okapi(texts)
        
        # Crear vectorstore
        vectorstore = {
            'bm25_index': bm25,
            'chunks': self.chunks,
            'tokenized_corpus': texts,
            'metadata': {
                'creation_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'method': 'BM25Okapi',
                'chunks_count': len(self.chunks),
                'parameters': {'k1': 1.5, 'b': 0.75},
                'version': '1.0.0',
                'creation_time': time.time() - start_time
            }
        }
        
        # Guardar vectorstore
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(vectorstore, f)
        
        self.logger.info(f"Vectorstore BM25 guardado en {output_path} ({time.time() - start_time:.2f}s)")
    
    def generate_tfidf_vectorstore(self, output_path: str = "data/vectorstores/tfidf.pkl") -> None:
        """
        Generar vectorstore para TF-IDF.
        
        Args:
            output_path (str): Ruta de salida para el vectorstore
        """
        self.logger.info("Generando vectorstore TF-IDF...")
        start_time = time.time()
        
        # Preparar textos para TF-IDF
        texts = []
        for chunk in self.chunks:
            text = chunk.get('texto', chunk.get('text', ''))
            texts.append(text)
        
        # Crear vectorizador TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
        # Ajustar y transformar
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Crear vectorstore
        vectorstore = {
            'chunks': self.chunks,
            'tfidf_vectorizer': vectorizer,
            'tfidf_matrix': tfidf_matrix,
            'metadata': {
                'creation_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'method': 'TF-IDF',
                'chunks_count': len(self.chunks),
                'vocabulary_size': len(vectorizer.vocabulary_),
                'matrix_shape': tfidf_matrix.shape,
                'version': '1.0.0',
                'creation_time': time.time() - start_time
            }
        }
        
        # Guardar vectorstore
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(vectorstore, f)
        
        self.logger.info(f"Vectorstore TF-IDF guardado en {output_path} ({time.time() - start_time:.2f}s)")
    
    def generate_transformer_vectorstore(self, output_path: str = "data/vectorstores/transformers.pkl") -> None:
        """
        Generar vectorstore para Transformers.
        
        Args:
            output_path (str): Ruta de salida para el vectorstore
        """
        self.logger.info("Generando vectorstore Transformers...")
        start_time = time.time()
        
        # Preparar textos
        texts = []
        for chunk in self.chunks:
            text = chunk.get('texto', chunk.get('text', ''))
            texts.append(text)
        
        # Cargar modelo de transformers
        model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        self.logger.info(f"Cargando modelo {model_name}...")
        
        try:
            model = SentenceTransformer(model_name)
            
            # Generar embeddings
            self.logger.info("Generando embeddings...")
            embeddings = model.encode(texts)
            
            # Crear vectorstore
            vectorstore = {
                'chunks': self.chunks,
                'embeddings': embeddings,
                'model_name': model_name,
                'metadata': {
                    'creation_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'method': 'SentenceTransformers',
                    'model': model_name,
                    'chunks_count': len(self.chunks),
                    'embedding_shape': embeddings.shape,
                    'version': '1.0.0',
                    'creation_time': time.time() - start_time
                }
            }
            
            # Guardar vectorstore
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                pickle.dump(vectorstore, f)
            
            self.logger.info(f"Vectorstore Transformers guardado en {output_path} ({time.time() - start_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"Error generando vectorstore Transformers: {e}")
            raise
    
    def generate_all_vectorstores(self, chunks_file: str = "data/processed/chunks.json") -> None:
        """
        Generar todos los vectorstores.
        
        Args:
            chunks_file (str): Ruta al archivo de chunks
        """
        self.logger.info("🚀 GENERANDO TODOS LOS VECTORSTORES")
        self.logger.info("=" * 50)
        
        # Cargar chunks
        self.load_chunks(chunks_file)
        
        # Generar vectorstores
        try:
            self.generate_bm25_vectorstore()
            self.generate_tfidf_vectorstore()
            self.generate_transformer_vectorstore()
            
            self.logger.info("✅ Todos los vectorstores generados exitosamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error generando vectorstores: {e}")
            raise


def main():
    """Función principal."""
    print("🚀 GENERADOR DE VECTORSTORES - MINEDU SEARCH SYSTEM")
    print("=" * 60)
    
    try:
        generator = VectorstoreGenerator()
        generator.generate_all_vectorstores()
        
        print("\n✅ GENERACIÓN COMPLETADA")
        print("=" * 60)
        print("📁 Vectorstores generados:")
        print("   - data/vectorstores/bm25.pkl")
        print("   - data/vectorstores/tfidf.pkl")
        print("   - data/vectorstores/transformers.pkl")
        print("\n💡 Ahora puedes ejecutar: python demo_working.py 'tu consulta'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Verifica que las dependencias estén instaladas:")
        print("   pip install rank-bm25 scikit-learn sentence-transformers")


if __name__ == "__main__":
    main() 
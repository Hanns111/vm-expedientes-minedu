#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de vectorstore BM25 para búsqueda en documentos normativos.
Sistema paralelo al TF-IDF existente para comparación de rendimiento.

Este script:
1. Carga los chunks de texto procesados (chunks_v2.json)
2. Crea un índice BM25 utilizando la biblioteca rank-bm25
3. Guarda el vectorstore resultante como pickle para uso posterior
"""

import os
import json
import pickle
import logging
import time
from typing import Dict, List, Any
from rank_bm25 import BM25Okapi
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bm25_vectorstore_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BM25VectorstoreGenerator")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class BM25VectorstoreGenerator:
    """Generador de vectorstore BM25 para búsqueda en documentos normativos."""
    
    def __init__(self, chunks_path: str, output_path: str, k1: float = 1.5, b: float = 0.75):
        """
        Inicializa el generador de vectorstore BM25.
        
        Args:
            chunks_path: Ruta al archivo JSON con los chunks procesados
            output_path: Ruta donde se guardará el vectorstore BM25
            k1: Parámetro k1 de BM25 (saturación de términos, default: 1.5)
            b: Parámetro b de BM25 (normalización por longitud, default: 0.75)
        """
        self.chunks_path = chunks_path
        self.output_path = output_path
        self.chunks = []
        self.corpus = []
        self.bm25_index = None
        self.k1 = k1
        self.b = b
        self.metadata = {
            "creation_date": datetime.now().isoformat(),
            "method": "BM25Okapi",
            "chunks_count": 0,
            "parameters": {
                "k1": k1,
                "b": b
            },
            "version": "1.0.0"
        }
    
    def load_chunks(self) -> None:
        """Carga los chunks desde el archivo JSON."""
        try:
            logger.info(f"Cargando chunks desde {self.chunks_path}")
            start_time = time.time()
            
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            
            self.metadata["chunks_count"] = len(self.chunks)
            
            # Extraer el texto de cada chunk para el corpus
            self.corpus = [chunk["texto"] for chunk in self.chunks]
            
            logger.info(f"Cargados {len(self.chunks)} chunks en {time.time() - start_time:.2f} segundos")
        except Exception as e:
            logger.error(f"Error al cargar chunks: {str(e)}")
            raise
    
    def create_bm25_index(self) -> None:
        """Crea el índice BM25 a partir del corpus tokenizado."""
        try:
            logger.info(f"Creando índice BM25 con parámetros k1={self.k1}, b={self.b}...")
            start_time = time.time()
            
            # Preprocesar el corpus para tokenización
            import re
            import unicodedata
            
            # Función para preprocesar texto
            def preprocess_text(text):
                # Convertir a minúsculas
                text = text.lower()
                # Eliminar signos de puntuación y caracteres especiales
                text = re.sub(r'[^\w\s]', ' ', text)
                # Normalizar acentos
                text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
                # Tokenizar por espacios
                return text.split()
            
            # Tokenizar corpus
            tokenized_corpus = [preprocess_text(doc) for doc in self.corpus]
            
            # Crear índice BM25 con corpus tokenizado
            self.bm25_index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
            
            # Guardar corpus tokenizado para referencia
            self.tokenized_corpus = tokenized_corpus
            
            logger.info(f"Índice BM25 creado en {time.time() - start_time:.2f} segundos")
            
            # Actualizar metadata
            self.metadata["chunks_count"] = len(self.corpus)
            self.metadata["creation_time"] = time.time() - start_time
            self.metadata["parameters"] = {
                "k1": self.k1,
                "b": self.b
            }
        except Exception as e:
            logger.error(f"Error al crear índice BM25: {e}")
            raise
    
    def save_vectorstore(self) -> None:
        """Guarda el índice BM25 y metadatos como pickle."""
        try:
            logger.info(f"Guardando vectorstore BM25 en {self.output_path}")
            start_time = time.time()
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Estructura del vectorstore
            vectorstore = {
                "bm25_index": self.bm25_index,
                "chunks": self.chunks,
                "tokenized_corpus": getattr(self, 'tokenized_corpus', []),  # Incluir corpus tokenizado
                "metadata": self.metadata
            }
            
            # Guardar como pickle
            with open(self.output_path, 'wb') as f:
                pickle.dump(vectorstore, f)
            
            logger.info(f"Vectorstore guardado en {time.time() - start_time:.2f} segundos")
        except Exception as e:
            logger.error(f"Error al guardar vectorstore: {e}")
            raise
    
    def generate(self) -> None:
        """Ejecuta el proceso completo de generación del vectorstore BM25."""
        try:
            logger.info("Iniciando generación de vectorstore BM25")
            start_time = time.time()
            
            self.load_chunks()
            self.create_bm25_index()
            self.save_vectorstore()
            
            logger.info(f"Vectorstore BM25 generado exitosamente en {time.time() - start_time:.2f} segundos")
            logger.info(f"Total de chunks procesados: {self.metadata['chunks_count']}")
        except Exception as e:
            logger.error(f"Error en la generación del vectorstore BM25: {str(e)}")
            raise

def optimize_parameters(chunks_path: str, output_dir: str, test_queries: List[str]) -> tuple[float, float]:
    """
    Optimiza los parámetros k1 y b de BM25 mediante grid search.
    
    Args:
        chunks_path: Ruta al archivo JSON con los chunks procesados
        output_dir: Directorio donde se guardarán los vectorstores
        test_queries: Lista de consultas de prueba
        
    Returns:
        Tupla con los mejores valores de k1 y b
    """
    logger.info("Iniciando optimización de parámetros BM25...")
    
    # Definir grid de parámetros
    k1_values = [1.2, 1.5, 2.0, 2.5]
    b_values = [0.5, 0.75, 0.9]
    
    best_score = -1
    best_k1 = 1.5
    best_b = 0.75
    
    results = []
    
    # Grid search
    for k1 in k1_values:
        for b in b_values:
            logger.info(f"Evaluando parámetros: k1={k1}, b={b}")
            
            # Crear vectorstore con estos parámetros
            output_path = os.path.join(output_dir, f"vectorstore_bm25_k1_{k1}_b_{b}.pkl")
            generator = BM25VectorstoreGenerator(chunks_path, output_path, k1=k1, b=b)
            generator.load_chunks()
            generator.create_bm25_index()
            generator.save_vectorstore()
            
            # Evaluar calidad con consultas de prueba
            from search_vectorstore_bm25 import BM25Search
            search_system = BM25Search(output_path)
            
            # Métricas de evaluación
            avg_quality_score = 0
            total_filtered = 0
            
            # Ejecutar consultas de prueba
            for query in test_queries:
                results_raw = search_system.search(query, top_k=5)
                
                # Contar resultados filtrados
                original_count = len(results_raw.get('results', []))
                quality_results = [r for r in results_raw.get('results', []) 
                                  if search_system.is_quality_chunk(r.get('texto', ''))]
                filtered_count = original_count - len(quality_results)
                total_filtered += filtered_count
                
                # Calcular score de calidad promedio
                if quality_results:
                    avg_quality_score += len(quality_results) / original_count if original_count > 0 else 0
            
            # Promediar scores
            if test_queries:
                avg_quality_score /= len(test_queries)
            
            # Guardar resultados
            param_result = {
                'k1': k1,
                'b': b,
                'avg_quality_score': avg_quality_score,
                'total_filtered': total_filtered
            }
            results.append(param_result)
            
            # Actualizar mejores parámetros
            if avg_quality_score > best_score:
                best_score = avg_quality_score
                best_k1 = k1
                best_b = b
                logger.info(f"Nuevos mejores parámetros: k1={k1}, b={b}, score={avg_quality_score:.4f}")
    
    # Guardar resultados de la optimización
    with open(os.path.join(output_dir, "bm25_parameter_optimization.json"), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Optimización completada. Mejores parámetros: k1={best_k1}, b={best_b}, score={best_score:.4f}")
    return best_k1, best_b

def main():
    """Función principal"""
    import argparse
    
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Generador de vectorstore BM25')
    parser.add_argument('--input', '-i', type=str, default='data/processed/chunks_v2.json',
                        help='Ruta al archivo JSON con los chunks procesados')
    parser.add_argument('--output', '-o', type=str, default='data/processed/vectorstore_bm25_test.pkl',
                        help='Ruta donde se guardará el vectorstore BM25')
    parser.add_argument('--k1', type=float, default=1.5,
                        help='Parámetro k1 de BM25 (saturación de términos, default: 1.5)')
    parser.add_argument('--b', type=float, default=0.75,
                        help='Parámetro b de BM25 (normalización por longitud, default: 0.75)')
    parser.add_argument('--optimize', action='store_true',
                        help='Optimizar parámetros k1 y b mediante grid search')
    args = parser.parse_args()
    
    # Definir rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    chunks_path = os.path.join(base_dir, args.input)
    output_path = os.path.join(base_dir, args.output)
    
    # Verificar existencia de archivo de entrada
    if not os.path.exists(chunks_path):
        logger.error(f"Archivo de entrada no encontrado: {chunks_path}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if args.optimize:
        # Consultas de prueba para optimización
        test_queries = [
            "¿Cuál es el procedimiento para solicitar viáticos?",
            "¿Cuál es el monto máximo para viáticos nacionales?",
            "Requisitos para autorización de viajes"
        ]
        
        # Optimizar parámetros
        output_dir = os.path.dirname(output_path)
        best_k1, best_b = optimize_parameters(chunks_path, output_dir, test_queries)
        
        # Generar vectorstore con los mejores parámetros
        logger.info(f"Generando vectorstore final con k1={best_k1}, b={best_b}")
        generator = BM25VectorstoreGenerator(chunks_path, output_path, k1=best_k1, b=best_b)
    else:
        # Generar vectorstore con los parámetros especificados
        generator = BM25VectorstoreGenerator(chunks_path, output_path, k1=args.k1, b=args.b)
    
    generator.generate()

if __name__ == "__main__":
    main()

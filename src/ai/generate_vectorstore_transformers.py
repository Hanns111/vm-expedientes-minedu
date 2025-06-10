#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generador de vectorstore basado en Sentence Transformers para el proyecto vm-expedientes-minedu.
Este script crea embeddings semánticos utilizando modelos de Sentence Transformers multilingües
y los almacena en un archivo pickle para su uso posterior en búsquedas semánticas.
"""

import os
import sys
import json
import time
import pickle
import logging
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('TransformersVectorstore')

class TransformersVectorstoreGenerator:
    """
    Generador de vectorstore basado en Sentence Transformers.
    Crea embeddings semánticos para chunks de texto y los almacena en un archivo pickle.
    """
    
    def __init__(
        self, 
        model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        fallback_model: str = 'paraphrase-MiniLM-L6-v2',
        device: str = 'cpu',
        chunk_size: int = 512
    ):
        """
        Inicializa el generador de vectorstore.
        
        Args:
            model_name: Nombre del modelo de Sentence Transformers a utilizar
            fallback_model: Modelo alternativo si el principal falla
            device: Dispositivo para ejecutar el modelo ('cpu' o 'cuda')
            chunk_size: Tamaño máximo de chunk para el modelo
        """
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.device = device
        self.chunk_size = chunk_size
        self.model = None
        
        # Intentar cargar el modelo principal
        try:
            logger.info(f"Cargando modelo {model_name}...")
            start_time = time.time()
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Modelo {model_name} cargado en {time.time() - start_time:.2f} segundos")
        except Exception as e:
            logger.warning(f"Error al cargar el modelo principal: {e}")
            logger.info(f"Intentando cargar modelo alternativo {fallback_model}...")
            try:
                start_time = time.time()
                self.model = SentenceTransformer(fallback_model, device=device)
                logger.info(f"Modelo alternativo {fallback_model} cargado en {time.time() - start_time:.2f} segundos")
                logger.warning("Usando modelo en inglés. Las consultas deberán ser traducidas para mejores resultados.")
            except Exception as e2:
                logger.error(f"Error al cargar modelo alternativo: {e2}")
                raise ValueError(f"No se pudo cargar ningún modelo: {e}, {e2}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos para generar embeddings
            
        Returns:
            Array numpy con los embeddings generados
        """
        if not self.model:
            raise ValueError("No se ha cargado ningún modelo")
        
        logger.info(f"Generando embeddings para {len(texts)} textos...")
        start_time = time.time()
        embeddings = self.model.encode(texts, show_progress_bar=True)
        logger.info(f"Embeddings generados en {time.time() - start_time:.2f} segundos")
        
        return embeddings
    
    def process_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Procesa los chunks y genera embeddings para cada uno.
        
        Args:
            chunks: Lista de chunks con texto y metadatos
            
        Returns:
            Diccionario con vectorstore completo
        """
        # Extraer textos de los chunks
        texts = []
        for chunk in chunks:
            # Usar 'texto' como clave principal, con fallback a 'text'
            if 'texto' in chunk:
                texts.append(chunk['texto'])
            elif 'text' in chunk:
                texts.append(chunk['text'])
            else:
                logger.warning(f"Chunk sin texto: {chunk}")
                texts.append("")
        
        # Generar embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Crear vectorstore
        vectorstore = {
            'chunks': chunks,
            'embeddings': embeddings,
            'model_name': self.model_name if self.model else self.fallback_model,
            'embedding_size': embeddings.shape[1] if embeddings.size > 0 else 0,
            'created_at': time.time(),
            'metadata': {
                'chunk_count': len(chunks),
                'model': self.model_name if self.model else self.fallback_model,
                'device': self.device,
                'chunk_size': self.chunk_size
            }
        }
        
        return vectorstore
    
    def save_vectorstore(self, vectorstore: Dict[str, Any], output_path: str) -> None:
        """
        Guarda el vectorstore en un archivo pickle.
        
        Args:
            vectorstore: Diccionario con vectorstore
            output_path: Ruta del archivo de salida
        """
        logger.info(f"Guardando vectorstore en {output_path}...")
        with open(output_path, 'wb') as f:
            pickle.dump(vectorstore, f)
        logger.info(f"Vectorstore guardado correctamente")
        
        # Mostrar estadísticas
        logger.info(f"Estadísticas del vectorstore:")
        logger.info(f"- Número de chunks: {len(vectorstore['chunks'])}")
        logger.info(f"- Tamaño de embedding: {vectorstore['embedding_size']}")
        logger.info(f"- Modelo utilizado: {vectorstore['model_name']}")
        
    def generate(self, input_path: str, output_path: str) -> None:
        """
        Genera el vectorstore completo desde un archivo de chunks.
        
        Args:
            input_path: Ruta del archivo de chunks
            output_path: Ruta del archivo de salida
        """
        # Cargar chunks
        logger.info(f"Cargando chunks desde {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        logger.info(f"Se cargaron {len(chunks)} chunks")
        
        # Procesar chunks
        vectorstore = self.process_chunks(chunks)
        
        # Guardar vectorstore
        self.save_vectorstore(vectorstore, output_path)

def main():
    """Función principal"""
    # Definir rutas
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_path = base_dir / "data" / "processed" / "chunks_v2.json"
    output_path = base_dir / "data" / "processed" / "vectorstore_transformers_test.pkl"
    
    # Verificar existencia de archivo de entrada
    if not input_path.exists():
        logger.error(f"Archivo de entrada no encontrado: {input_path}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generar vectorstore
    generator = TransformersVectorstoreGenerator()
    generator.generate(str(input_path), str(output_path))

if __name__ == "__main__":
    main()

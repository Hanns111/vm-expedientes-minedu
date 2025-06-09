#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Retriever Denso basado en E5-Large.
Implementa recuperación semántica state-of-the-art usando el modelo E5-Large.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

# Dependencias para E5 embeddings
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DenseRetrieverE5')

class DenseRetrieverE5:
    """
    Retriever denso basado en el modelo E5-Large.
    
    E5 es un modelo de embeddings state-of-the-art para recuperación de información,
    significativamente superior a modelos anteriores como Sentence Transformers.
    """
    
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = 8,
        max_length: int = 512,
        normalize_embeddings: bool = True
    ):
        """
        Inicializa el retriever denso con E5-Large.
        
        Args:
            model_name: Nombre del modelo E5 a utilizar
            cache_dir: Directorio para caché de modelos
            device: Dispositivo para inferencia ('cpu', 'cuda', 'cuda:0', etc.)
            batch_size: Tamaño de batch para inferencia
            max_length: Longitud máxima de tokens
            normalize_embeddings: Si normalizar los embeddings
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self.max_length = max_length
        self.normalize_embeddings = normalize_embeddings
        
        # Determinar dispositivo
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Cargar modelo y tokenizer
        self._load_model()
        
        logger.info(f"DenseRetrieverE5 inicializado con modelo {model_name}")
        logger.info(f"Usando device: {self.device}, batch_size: {batch_size}, max_length: {max_length}")
    
    def _load_model(self):
        """
        Carga el modelo E5 y el tokenizer.
        """
        start_time = time.time()
        logger.info(f"Cargando modelo E5: {self.model_name}")
        
        # Cargar tokenizer y modelo
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        )
        
        self.model = AutoModel.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir
        )
        
        # Mover modelo al dispositivo seleccionado
        self.model.to(self.device)
        
        # Poner modelo en modo evaluación
        self.model.eval()
        
        load_time = time.time() - start_time
        logger.info(f"Modelo E5 cargado en {load_time:.2f} segundos")
    
    def _mean_pooling(self, token_embeddings, attention_mask):
        """
        Realiza mean pooling sobre los token embeddings usando la attention mask.
        
        Args:
            token_embeddings: Embeddings de tokens del modelo
            attention_mask: Máscara de atención
            
        Returns:
            Embeddings promediados
        """
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def encode_queries(self, queries: List[str]) -> np.ndarray:
        """
        Codifica una lista de consultas en embeddings.
        
        Args:
            queries: Lista de consultas a codificar
            
        Returns:
            Array numpy con los embeddings de las consultas
        """
        # Añadir prefijo "query:" según recomendación de E5
        processed_queries = [f"query: {q}" for q in queries]
        
        return self._encode_texts(processed_queries)
    
    def encode_passages(self, passages: List[str]) -> np.ndarray:
        """
        Codifica una lista de pasajes en embeddings.
        
        Args:
            passages: Lista de pasajes a codificar
            
        Returns:
            Array numpy con los embeddings de los pasajes
        """
        # Añadir prefijo "passage:" según recomendación de E5
        processed_passages = [f"passage: {p}" for p in passages]
        
        return self._encode_texts(processed_passages)
    
    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """
        Codifica una lista de textos en embeddings.
        
        Args:
            texts: Lista de textos a codificar
            
        Returns:
            Array numpy con los embeddings
        """
        start_time = time.time()
        all_embeddings = []
        
        # Procesar en batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            # Tokenizar
            encoded_inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt"
            ).to(self.device)
            
            # Generar embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_inputs)
                
                # Aplicar mean pooling
                embeddings = self._mean_pooling(
                    model_output.last_hidden_state,
                    encoded_inputs['attention_mask']
                )
                
                # Normalizar embeddings si es necesario
                if self.normalize_embeddings:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
                # Añadir al resultado
                all_embeddings.append(embeddings.cpu().numpy())
        
        # Concatenar todos los embeddings
        all_embeddings = np.vstack(all_embeddings)
        
        logger.info(f"Generados {len(texts)} embeddings en {time.time() - start_time:.2f} segundos")
        
        return all_embeddings
    
    def search(
        self,
        query: str,
        passages: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica en una lista de pasajes.
        
        Args:
            query: Consulta de búsqueda
            passages: Lista de pasajes donde buscar
            metadata: Lista de metadatos asociados a los pasajes
            top_k: Número de resultados a devolver
            
        Returns:
            Lista de resultados con scores y metadatos
        """
        start_time = time.time()
        
        # Codificar consulta
        query_embedding = self.encode_queries([query])
        
        # Codificar pasajes
        passage_embeddings = self.encode_passages(passages)
        
        # Calcular similitud
        scores = np.dot(query_embedding, passage_embeddings.T)[0]
        
        # Obtener índices de los mejores resultados
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Preparar resultados
        results = []
        for rank, idx in enumerate(top_indices):
            result = {
                "rank": rank + 1,
                "text": passages[idx],
                "score": float(scores[idx]),
            }
            
            # Añadir metadatos si están disponibles
            if metadata and idx < len(metadata):
                result["metadata"] = metadata[idx]
            
            results.append(result)
        
        search_time = time.time() - start_time
        logger.info(f"Búsqueda completada en {search_time:.4f} segundos")
        logger.info(f"Encontrados {len(results)} resultados para: '{query}'")
        
        return results
    
    def save_embeddings(self, embeddings: np.ndarray, file_path: str) -> None:
        """
        Guarda embeddings en un archivo.
        
        Args:
            embeddings: Array numpy con embeddings
            file_path: Ruta del archivo donde guardar
        """
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Guardar embeddings
        np.save(file_path, embeddings)
        logger.info(f"Embeddings guardados en {file_path}")
    
    def load_embeddings(self, file_path: str) -> np.ndarray:
        """
        Carga embeddings desde un archivo.
        
        Args:
            file_path: Ruta del archivo a cargar
            
        Returns:
            Array numpy con los embeddings cargados
        """
        embeddings = np.load(file_path)
        logger.info(f"Embeddings cargados desde {file_path}: {embeddings.shape}")
        return embeddings


if __name__ == "__main__":
    # Ejemplo de uso
    print("Inicializando DenseRetrieverE5...")
    retriever = DenseRetrieverE5()
    
    # Ejemplo de búsqueda
    query = "¿Cuál es el procedimiento para solicitar viáticos?"
    passages = [
        "El procedimiento para solicitar viáticos requiere llenar el formulario F-01 y presentarlo a su jefe inmediato.",
        "Los viáticos son asignaciones que se otorgan al personal para cubrir gastos de alimentación, hospedaje y movilidad.",
        "Para solicitar vacaciones debe presentar el formulario correspondiente con 15 días de anticipación.",
        "El proceso de rendición de viáticos debe realizarse dentro de los 10 días hábiles posteriores al retorno.",
        "La solicitud de viáticos debe ser aprobada por el jefe de la unidad orgánica y la oficina de administración."
    ]
    
    metadata = [
        {"source": "Manual de Procedimientos", "page": 15},
        {"source": "Directiva de Viáticos", "page": 3},
        {"source": "Manual de RRHH", "page": 22},
        {"source": "Directiva de Viáticos", "page": 8},
        {"source": "Manual de Procedimientos", "page": 16}
    ]
    
    print("\nRealizando búsqueda de prueba...")
    results = retriever.search(query, passages, metadata)
    
    print(f"\nResultados para: '{query}'")
    for result in results:
        print(f"\nRank {result['rank']} (Score: {result['score']:.4f}):")
        print(f"Metadata: {result['metadata']}")
        print(f"Texto: {result['text']}")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ChromaDB Manager para sistema de búsqueda híbrido avanzado.
Gestiona la creación, actualización y consulta de vectorstores con ChromaDB.
Utiliza embeddings E5-Large para representación semántica state-of-the-art.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

# Dependencias para ChromaDB y embeddings
import chromadb
from chromadb.utils import embedding_functions
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ChromaManager')

class E5EmbeddingFunction:
    """
    Función de embedding personalizada usando el modelo E5-Large.
    
    E5 es un modelo de embeddings state-of-the-art para recuperación de información,
    significativamente superior a modelos anteriores como Sentence Transformers.
    """
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Inicializa el modelo E5 para generación de embeddings.
        
        Args:
            model_name: Nombre del modelo E5 a utilizar.
        """
        logger.info(f"Cargando modelo E5: {model_name}")
        start_time = time.time()
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        # Mover a GPU si está disponible
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        logger.info(f"Modelo E5 cargado en {time.time() - start_time:.2f} segundos. Usando device: {self.device}")
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos para generar embeddings.
            
        Returns:
            Lista de embeddings como vectores de float.
        """
        # Añadir prefijos según recomendación de E5
        processed_texts = []
        for text in texts:
            if text.startswith("query:") or text.startswith("passage:"):
                processed_texts.append(text)
            else:
                # Para documentos usamos prefijo passage, para consultas usamos query
                if len(text.split()) > 20:  # Heurística simple para distinguir
                    processed_texts.append(f"passage: {text}")
                else:
                    processed_texts.append(f"query: {text}")
        
        # Tokenizar y generar embeddings en batches
        batch_size = 8  # Ajustar según memoria disponible
        embeddings = []
        
        for i in range(0, len(processed_texts), batch_size):
            batch_texts = processed_texts[i:i+batch_size]
            
            # Tokenizar con padding y truncamiento
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Generar embeddings
            with torch.no_grad():
                outputs = self.model(**encoded)
                # Usar mean pooling para obtener un embedding por texto
                attention_mask = encoded['attention_mask']
                embeddings_batch = self._mean_pooling(outputs.last_hidden_state, attention_mask)
                # Normalizar embeddings
                embeddings_batch = torch.nn.functional.normalize(embeddings_batch, p=2, dim=1)
                
            # Convertir a lista y añadir al resultado
            embeddings.extend(embeddings_batch.cpu().numpy().tolist())
        
        return embeddings
    
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


class ChromaManager:
    """
    Gestor de ChromaDB para el sistema de búsqueda híbrido avanzado.
    """
    
    def __init__(
        self,
        collection_name: str = "minedu_documents",
        persist_directory: str = "data/vectorstores/chroma",
        embedding_model: str = "intfloat/multilingual-e5-large",
        metadata_fields: List[str] = ["source", "page", "chunk_id", "year", "entity", "doc_type"]
    ):
        """
        Inicializa el gestor de ChromaDB.
        
        Args:
            collection_name: Nombre de la colección en ChromaDB
            persist_directory: Directorio para persistir la base de datos
            embedding_model: Modelo de embeddings a utilizar
            metadata_fields: Campos de metadatos a incluir
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.metadata_fields = metadata_fields
        
        # Crear directorio si no existe
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Inicializar cliente ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Inicializar función de embedding
        self.embedding_function = E5EmbeddingFunction(model_name=embedding_model)
        
        # Inicializar o cargar colección
        self._initialize_collection()
        
        logger.info(f"ChromaManager inicializado. Colección: {collection_name}")
    
    def _initialize_collection(self):
        """
        Inicializa o carga la colección de ChromaDB.
        """
        try:
            # Intentar obtener colección existente
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Colección existente cargada: {self.collection_name} con {self.collection.count()} documentos")
        except Exception as e:
            # Crear nueva colección si no existe
            logger.info(f"Creando nueva colección: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Documentos MINEDU vectorizados con E5-Large"}
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Añade documentos a la colección de ChromaDB.
        
        Args:
            documents: Lista de documentos con texto y metadatos
        """
        start_time = time.time()
        logger.info(f"Añadiendo {len(documents)} documentos a ChromaDB")
        
        # Preparar datos para ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for i, doc in enumerate(documents):
            # Generar ID único si no existe
            doc_id = doc.get("id", f"doc_{int(time.time())}_{i}")
            ids.append(doc_id)
            
            # Preparar texto con prefijo para E5
            texts.append(f"passage: {doc['text']}")
            
            # Extraer metadatos relevantes
            metadata = {field: doc.get(field, "") for field in self.metadata_fields if field in doc}
            metadatas.append(metadata)
        
        # Añadir documentos en batches para mejor rendimiento
        batch_size = 100
        for i in tqdm(range(0, len(ids), batch_size)):
            end_idx = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        # Persistir cambios
        self.client.persist()
        
        logger.info(f"Documentos añadidos en {time.time() - start_time:.2f} segundos")
        logger.info(f"Total documentos en colección: {self.collection.count()}")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza búsqueda semántica en ChromaDB.
        
        Args:
            query: Consulta de búsqueda
            n_results: Número de resultados a devolver
            metadata_filter: Filtro de metadatos para la búsqueda
            
        Returns:
            Resultados de la búsqueda con scores y metadatos
        """
        start_time = time.time()
        
        # Preparar consulta con prefijo para E5
        query_text = f"query: {query}"
        
        # Realizar búsqueda
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=metadata_filter
        )
        
        # Formatear resultados
        formatted_results = {
            "query": query,
            "time_taken": time.time() - start_time,
            "total_found": len(results["documents"][0]) if results["documents"] else 0,
            "results": []
        }
        
        # Procesar resultados si existen
        if results["documents"] and len(results["documents"][0]) > 0:
            for i, (doc, metadata, score, doc_id) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                results["ids"][0]
            )):
                # Convertir score de distancia a similitud (1 - distancia)
                similarity_score = 1.0 - score
                
                # Limpiar texto (quitar prefijo)
                clean_text = doc.replace("passage: ", "")
                
                formatted_results["results"].append({
                    "rank": i + 1,
                    "id": doc_id,
                    "text": clean_text,
                    "score": similarity_score,
                    "metadata": metadata
                })
        
        logger.info(f"Búsqueda completada en {formatted_results['time_taken']:.4f} segundos")
        logger.info(f"Encontrados {formatted_results['total_found']} resultados para: '{query}'")
        
        return formatted_results
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la colección actual.
        
        Returns:
            Diccionario con información de la colección
        """
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "embedding_model": self.embedding_model,
            "metadata_fields": self.metadata_fields,
            "persist_directory": self.persist_directory
        }
    
    def delete_collection(self) -> None:
        """
        Elimina la colección actual.
        """
        self.client.delete_collection(self.collection_name)
        logger.info(f"Colección {self.collection_name} eliminada")


if __name__ == "__main__":
    # Ejemplo de uso
    print("Inicializando ChromaManager...")
    chroma_manager = ChromaManager()
    
    # Mostrar información de la colección
    collection_info = chroma_manager.get_collection_info()
    print(f"Información de la colección: {json.dumps(collection_info, indent=2)}")
    
    # Ejemplo de búsqueda
    if collection_info["count"] > 0:
        print("\nRealizando búsqueda de prueba...")
        results = chroma_manager.search("¿Cuál es el procedimiento para solicitar viáticos?")
        print(f"Tiempo de búsqueda: {results['time_taken']:.4f} segundos")
        print(f"Resultados encontrados: {results['total_found']}")
        
        for i, result in enumerate(results["results"]):
            print(f"\nResultado {i+1} (Score: {result['score']:.4f}):")
            print(f"ID: {result['id']}")
            print(f"Metadata: {result['metadata']}")
            print(f"Texto: {result['text'][:150]}...")

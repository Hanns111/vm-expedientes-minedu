#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de búsqueda semántica basado en Sentence Transformers para el proyecto vm-expedientes-minedu.
Este script utiliza embeddings semánticos generados por modelos de Sentence Transformers
para realizar búsquedas por similitud semántica en documentos normativos.
"""

import os
import sys
import time
import pickle
import logging
import argparse
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from src.core.config.security_config import SecurityConfig

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('TransformersSearch')

class EntitiesExtractor:
    """Extractor de entidades usando spaCy"""
    
    def __init__(self, model_name: str = 'es_core_news_sm'):
        """
        Inicializa el extractor de entidades.
        
        Args:
            model_name: Nombre del modelo de spaCy a utilizar
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Modelo spaCy '{model_name}' cargado correctamente")
        except Exception as e:
            logger.error(f"Error al cargar el modelo spaCy: {e}")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae entidades de un texto.
        
        Args:
            text: Texto del que extraer entidades
            
        Returns:
            Diccionario con entidades por tipo
        """
        if not self.nlp:
            logger.warning("Modelo spaCy no disponible. No se extraerán entidades.")
            return {}
        
        doc = self.nlp(text)
        entities = {}
        
        # Agrupar entidades por tipo
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            # Evitar duplicados
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
        
        return entities

class TransformersSearch:
    """
    Sistema de búsqueda semántica basado en Sentence Transformers.
    Utiliza embeddings semánticos para encontrar documentos relevantes para una consulta.
    """
    
    def __init__(
        self, 
        vectorstore_path: str,
        model_name: str = None,
        fallback_model: str = 'paraphrase-MiniLM-L6-v2',
        device: str = 'cpu'
    ):
        """
        Inicializa el sistema de búsqueda.
        
        Args:
            vectorstore_path: Ruta al archivo pickle con el vectorstore
            model_name: Nombre del modelo de Sentence Transformers a utilizar
                        (si es None, se usa el mismo que generó el vectorstore)
            fallback_model: Modelo alternativo si el principal falla
            device: Dispositivo para ejecutar el modelo ('cpu' o 'cuda')
        """
        self.vectorstore_path = vectorstore_path
        self.fallback_model = fallback_model
        self.device = device
        self.model = None
        self.vectorstore = None
        self.entities_extractor = EntitiesExtractor()
        
        # Cargar vectorstore
        self._load_vectorstore()
        
        # Determinar modelo a utilizar
        if not model_name:
            model_name = self.vectorstore.get('model_name', fallback_model)
        
        # Cargar modelo
        self._load_model(model_name)
    
    def _load_vectorstore(self) -> None:
        """Carga el vectorstore desde un archivo pickle."""
        try:
            logger.info(f"Cargando vectorstore desde {self.vectorstore_path}")
            start_time = time.time()
            with open(self.vectorstore_path, 'rb') as f:
                self.vectorstore = pickle.load(f)
            logger.info(f"Vectorstore cargado en {time.time() - start_time:.2f} segundos")
            
            # Verificar estructura del vectorstore
            required_keys = ['chunks', 'embeddings', 'model_name']
            for key in required_keys:
                if key not in self.vectorstore:
                    raise ValueError(f"Vectorstore inválido: falta la clave '{key}'")
            
            # Mostrar estadísticas
            logger.info(f"Vectorstore cargado con {len(self.vectorstore['chunks'])} chunks")
            logger.info(f"Modelo utilizado para generar embeddings: {self.vectorstore['model_name']}")
            
        except Exception as e:
            logger.error(f"Error al cargar el vectorstore: {e}")
            raise
    
    def _load_model(self, model_name: str) -> None:
        """
        Carga el modelo de Sentence Transformers.
        
        Args:
            model_name: Nombre del modelo a cargar
        """
        try:
            logger.info(f"Cargando modelo {model_name}...")
            start_time = time.time()
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info(f"Modelo {model_name} cargado en {time.time() - start_time:.2f} segundos")
        except Exception as e:
            logger.warning(f"Error al cargar el modelo principal: {e}")
            logger.info(f"Intentando cargar modelo alternativo {self.fallback_model}...")
            try:
                start_time = time.time()
                self.model = SentenceTransformer(self.fallback_model, device=self.device)
                logger.info(f"Modelo alternativo {self.fallback_model} cargado en {time.time() - start_time:.2f} segundos")
                logger.warning("Usando modelo en inglés. Las consultas deberán ser traducidas para mejores resultados.")
            except Exception as e2:
                logger.error(f"Error al cargar modelo alternativo: {e2}")
                raise ValueError(f"No se pudo cargar ningún modelo: {e}, {e2}")
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Realiza una búsqueda semántica.
        
        Args:
            query: Consulta a buscar
            top_k: Número máximo de resultados a devolver
            
        Returns:
            Diccionario con resultados y metadatos
        """
        logger.info(f"Realizando búsqueda semántica para: '{query}'")
        start_time = time.time()
        
        # Generar embedding de la consulta
        query_embedding = self.model.encode([query])[0]
        
        # Calcular similitud con todos los embeddings
        similarities = cosine_similarity(
            [query_embedding], 
            self.vectorstore['embeddings']
        )[0]
        
        # Obtener índices de los top_k resultados
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Preparar resultados
        results = []
        for idx in top_indices:
            chunk = self.vectorstore['chunks'][idx]
            score = float(similarities[idx])
            
            # Asegurar que el chunk tenga la clave 'texto'
            if 'texto' not in chunk and 'text' in chunk:
                chunk['texto'] = chunk['text']
            
            # Crear resultado con score
            result = {**chunk, 'score': score}
            results.append(result)
        
        # Extraer entidades de los resultados
        entities = self.extract_entities_from_results(results, query)
        
        # Preparar respuesta
        response = {
            'results': results,
            'entities': entities,
            'query': query,
            'execution_time': time.time() - start_time
        }
        
        logger.info(f"Búsqueda completada en {response['execution_time']:.4f} segundos, {len(results)} resultados encontrados")
        return response
    
    def extract_entities_from_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Extrae entidades de los resultados de búsqueda.
        
        Args:
            results: Lista de resultados de búsqueda
            query: Consulta original
            
        Returns:
            Diccionario con entidades extraídas
        """
        # Concatenar textos de los resultados
        all_text = " ".join([r.get("texto", "") for r in results])
        
        # Extraer entidades
        entities = self.entities_extractor.extract_entities(all_text)
        
        return entities

def parse_args():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Búsqueda semántica con Sentence Transformers')
    parser.add_argument('--query', '-q', type=str, help='Consulta a buscar')
    parser.add_argument('--top_k', '-k', type=int, default=5, help='Número de resultados a mostrar')
    parser.add_argument('--vectorstore', '-v', type=str, 
                        default='data/processed/vectorstore_transformers_test.pkl',
                        help='Ruta al archivo pickle con el vectorstore')
    return parser.parse_args()

def main():
    """Función principal"""
    path = SecurityConfig.DATA_DIR / "processed" / "vectorstore_transformers_test.pkl"
    print(f"Usando vectorstore seguro: {path}")
    if not Path(path).exists():
        print("❌ Vectorstore Transformers no encontrado.")
        return
    with open(path, 'rb') as f:
        data = pickle.load(f)
    print(f"Claves en el vectorstore Transformers: {list(data.keys())}")
    
    # Crear sistema de búsqueda
    search_system = TransformersSearch(str(path))
    
    # Si no se proporciona consulta, solicitarla
    query = args.query
    if not query:
        query = input("Ingrese su consulta: ")
    
    # Realizar búsqueda
    results = search_system.search(query, top_k=args.top_k)
    
    # Mostrar resultados
    print(f"\nResultados para '{query}':")
    print(f"Tiempo de ejecución: {results['execution_time']:.4f} segundos")
    
    # Manejar entidades con codificación segura
    try:
        print("Entidades encontradas:")
        for entity_type, entities in results['entities'].items():
            print(f"  - {entity_type}: {', '.join([str(e) for e in entities])}")
    except UnicodeEncodeError:
        print("  [Algunas entidades contienen caracteres que no se pueden mostrar en la consola actual]")
    
    print("\nDocumentos más relevantes:")
    
    for i, result in enumerate(results['results']):
        print(f"\n{i+1}. Score: {result['score']:.4f}")
        print(f"   Chunk ID: {result.get('id', 'N/A')}")
        try:
            texto = result.get('texto', '')[:150]
            print(f"   Texto: {texto}...")
        except UnicodeEncodeError:
            print(f"   Texto: [Contiene caracteres que no se pueden mostrar en la consola actual]")


if __name__ == "__main__":
    main()

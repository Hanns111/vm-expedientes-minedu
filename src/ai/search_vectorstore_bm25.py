#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema de búsqueda BM25 para documentos normativos.
Implementación paralela al sistema TF-IDF existente para comparación de rendimiento.

Este script:
1. Carga el vectorstore BM25 generado previamente
2. Procesa consultas en lenguaje natural
3. Recupera los chunks más relevantes según BM25
4. Extrae entidades y contexto relevante
5. Genera respuestas estructuradas
"""

import os
import json
import pickle
import logging
import time
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from rank_bm25 import BM25Okapi

# Importar el extractor de entidades existente
from entities_extractor import EntitiesExtractor

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bm25_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BM25Search")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class BM25Search:
    """Sistema de búsqueda BM25 para documentos normativos."""
    
    def __init__(self, vectorstore_path: str):
        """
        Inicializa el sistema de búsqueda BM25.
        
        Args:
            vectorstore_path: Ruta al archivo pickle con el vectorstore BM25
        """
        self.vectorstore_path = vectorstore_path
        self.bm25_index = None
        self.chunks = []
        self.metadata = {}
        self.entities_extractor = EntitiesExtractor()
        self.load_vectorstore()
    
    def load_vectorstore(self) -> None:
        """Carga el vectorstore BM25 desde el archivo pickle."""
        try:
            logger.info(f"Cargando vectorstore BM25 desde {self.vectorstore_path}")
            start_time = time.time()
            
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            self.bm25_index = vectorstore["bm25_index"]
            self.chunks = vectorstore["chunks"]
            self.metadata = vectorstore["metadata"]
            
            # Cargar corpus tokenizado si existe
            self.tokenized_corpus = vectorstore.get("tokenized_corpus", [])
            
            logger.info(f"Vectorstore BM25 cargado en {time.time() - start_time:.2f} segundos")
            logger.info(f"Total de chunks disponibles: {len(self.chunks)}")
        except Exception as e:
            logger.error(f"Error al cargar vectorstore: {str(e)}")
            raise
    
    def preprocess_query(self, query: str) -> List[str]:
        """
        Preprocesa la consulta para BM25 (tokenización).
        
        Args:
            query: Consulta en lenguaje natural
            
        Returns:
            Lista de tokens de la consulta
        """
        # Eliminar signos de puntuación y caracteres especiales
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Normalizar acentos (convertir caracteres acentuados a sus equivalentes sin acento)
        import unicodedata
        query = ''.join(c for c in unicodedata.normalize('NFD', query) if unicodedata.category(c) != 'Mn')
        
        # Convertir a minúsculas
        query = query.lower()
        
        # Eliminar palabras vacías comunes en español
        stopwords = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'a', 'ante', 'bajo', 'con', 
                    'de', 'desde', 'en', 'entre', 'hacia', 'hasta', 'para', 'por', 'según', 'sin', 'sobre', 'tras',
                    'es', 'son', 'cual', 'cuales', 'como', 'que', 'donde', 'cuando', 'cuanto']
        
        # Tokenizar y filtrar stopwords
        tokens = [token for token in query.split() if token not in stopwords and len(token) > 1]
        
        logger.info(f"Consulta preprocesada: {tokens}")
        return tokens
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda BM25 con la consulta dada.
        
        Args:
            query: Consulta en lenguaje natural
            top_k: Número de resultados a devolver
            
        Returns:
            Lista de chunks más relevantes con sus scores
        """
        try:
            logger.info(f"Realizando búsqueda BM25 para: '{query}'")
            start_time = time.time()
            
            # Preprocesar la consulta usando el mismo método que se usó para el corpus
            import unicodedata
            
            # Preprocesar texto de la misma manera que se hizo con el corpus
            def preprocess_text(text):
                # Convertir a minúsculas
                text = text.lower()
                # Eliminar signos de puntuación y caracteres especiales
                text = re.sub(r'[^\w\s]', ' ', text)
                # Normalizar acentos
                text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
                # Tokenizar por espacios
                return text.split()
            
            tokenized_query = preprocess_text(query)
            logger.info(f"Consulta preprocesada: {tokenized_query}")
            
            # Realizar búsqueda BM25
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Obtener los índices de los top_k resultados
            top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
            
            # Construir resultados con chunks y scores
            results = []
            for idx in top_indices:
                if bm25_scores[idx] > 0:  # Solo incluir resultados con score positivo
                    chunk = self.chunks[idx].copy()
                    chunk["score"] = float(bm25_scores[idx])  # Convertir a float para serialización JSON
                    results.append(chunk)
                    
            # Filtrar resultados de baja calidad
            original_count = len(results)
            results = self.filter_quality_results(results)
            filtered_count = original_count - len(results)
            if filtered_count > 0:
                logger.info(f"Se filtraron {filtered_count} resultados de baja calidad")
            
            search_time = time.time() - start_time
            logger.info(f"Búsqueda completada en {search_time:.4f} segundos, {len(results)} resultados encontrados")
            
            return results
        except Exception as e:
            logger.error(f"Error en la búsqueda: {str(e)}")
            raise
    
    def count_special_chars(self, text: str) -> int:
        """
        Cuenta caracteres especiales en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Número de caracteres especiales
        """
        if not text:
            return 0
        
        # Considerar como especiales los que no son alfanuméricos ni espacios
        special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
        return special_chars
    
    def is_quality_chunk(self, text: str) -> bool:
        """
        Determina si un chunk tiene calidad suficiente.
        
        Args:
            text: Texto del chunk
            
        Returns:
            True si el chunk tiene calidad suficiente, False en caso contrario
        """
        if not text:
            return False
            
        # Filtro 1: Máximo 20% caracteres especiales
        special_ratio = self.count_special_chars(text) / len(text)
        if special_ratio > 0.2:
            logger.debug(f"Chunk rechazado por alto ratio de caracteres especiales: {special_ratio:.2f}")
            return False
        
        # Filtro 2: Mínimo 70% palabras coherentes (>= 3 chars)
        words = text.split()
        if not words:
            return False
            
        coherent_words = [w for w in words if len(w) >= 3 and w.isalpha()]
        coherent_ratio = len(coherent_words) / len(words) if words else 0
        if coherent_ratio < 0.7:
            logger.debug(f"Chunk rechazado por bajo ratio de palabras coherentes: {coherent_ratio:.2f}")
            return False
        
        # Filtro 3: Sin patrones OCR típicos
        ocr_patterns = ['( %)', 'del del', 'S O LE S', '00/ 1 00']
        if any(pattern in text for pattern in ocr_patterns):
            logger.debug(f"Chunk rechazado por contener patrones OCR típicos")
            return False
             
        return True
    
    def filter_quality_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra los resultados para eliminar chunks de baja calidad.
        
        Args:
            results: Lista de resultados a filtrar
            
        Returns:
            Lista de resultados filtrados
        """
        if not results:
            return []
            
        filtered_results = []
        for result in results:
            text = result.get('texto', '')
            if self.is_quality_chunk(text):
                filtered_results.append(result)
            else:
                logger.info(f"Eliminando chunk de baja calidad: {text[:50]}...")
        
        # Si todos los resultados son de baja calidad, devolver al menos el mejor
        if not filtered_results and results:
            logger.warning("Todos los resultados son de baja calidad. Devolviendo el mejor disponible.")
            return [results[0]]
            
        return filtered_results
        
    def extract_entities_from_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Extrae entidades relevantes de los resultados de búsqueda.
        
        Args:
            results: Lista de chunks relevantes
            query: Consulta original
            
        Returns:
            Diccionario con entidades extraídas y contexto
        """
        try:
            logger.info("Extrayendo entidades de los resultados")
            
            # Concatenar el texto de todos los resultados
            all_text = " ".join([r["texto"] for r in results])
            
            # Extraer entidades usando el extractor existente
            entities = self.entities_extractor.extract_entities(all_text)
            
            # El contexto ya viene incluido en el formato de entities
            # No es necesario llamar a extract_entity_context
            
            # Reorganizar las entidades para el formato de respuesta
            formatted_entities = {}
            context = {}
            
            for entity_type, entity_items in entities.items():
                if entity_type != "entidades" and entity_items:  # Ignorar las entidades de spaCy por ahora
                    formatted_entities[entity_type] = [item["valor"] for item in entity_items]
                    context[entity_type] = {item["valor"]: item["contexto"] for item in entity_items}
            
            return {
                "entities": formatted_entities,
                "context": context
            }
        except Exception as e:
            logger.error(f"Error al extraer entidades: {str(e)}")
            return {"entities": {}, "context": {}}
    
    def generate_response(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Genera una respuesta completa para la consulta.
        
        Args:
            query: Consulta en lenguaje natural
            top_k: Número de resultados a considerar
            
        Returns:
            Respuesta estructurada con resultados, entidades y metadatos
        """
        try:
            start_time = time.time()
            
            # Realizar búsqueda
            results = self.search(query, top_k)
            
            # Extraer entidades si hay resultados
            entities_data = {}
            if results:
                entities_data = self.extract_entities_from_results(results, query)
            
            # Construir respuesta
            response = {
                "query": query,
                "results": results,
                "entities": entities_data.get("entities", {}),
                "context": entities_data.get("context", {}),
                "metadata": {
                    "search_method": "BM25",
                    "top_k": top_k,
                    "total_results": len(results),
                    "search_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return response
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "results": [],
                "entities": {},
                "context": {},
                "metadata": {
                    "search_method": "BM25",
                    "error_occurred": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

def main():
    """Función principal para demostración."""
    try:
        # Ruta al vectorstore BM25
        vectorstore_path = "data/processed/vectorstore_bm25_test.pkl"
        
        # Inicializar sistema de búsqueda
        search_system = BM25Search(vectorstore_path)
        
        # Ejemplo de consulta
        query = "¿Cuál es el monto máximo para viáticos nacionales?"
        
        # Generar respuesta
        response = search_system.generate_response(query)
        
        # Mostrar resultados
        print(f"\nConsulta: {query}")
        print(f"Tiempo de búsqueda: {response['metadata']['search_time']:.4f} segundos")
        print(f"Total de resultados: {response['metadata']['total_results']}")
        
        print("\nResultados principales:")
        for i, result in enumerate(response["results"][:3], 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   {result['texto'][:150]}...")
        
        print("\nEntidades encontradas:")
        for entity_type, entities in response["entities"].items():
            if entities:
                print(f"- {entity_type}: {', '.join(entities)}")
        
        # Guardar resultados para análisis
        output_dir = "data/evaluation/benchmark_results/bm25_results"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = f"{output_dir}/sample_query_result_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        print(f"\nResultados guardados en: {output_file}")
        
    except Exception as e:
        logger.error(f"Error en la función principal: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Adaptador para el BM25Retriever.

Este módulo implementa un adaptador para integrar el BM25Search existente
con el pipeline RAG de MINEDU.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Intentar importar BM25Search
try:
    from src.ai.search_vectorstore_bm25 import BM25Search
except ImportError:
    # Si falla, intentar con una ruta relativa
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    try:
        from src.ai.search_vectorstore_bm25 import BM25Search
    except ImportError as e:
        logging.error(f"No se pudo importar BM25Search: {str(e)}")
        # Crear una clase mock para evitar errores de importación
        class BM25Search:
            def __init__(self, *args, **kwargs):
                pass
            def generate_response(self, *args, **kwargs):
                return {"results": []}

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BM25Retriever')


class BM25Retriever:
    """
    Adaptador para integrar BM25Search existente con el pipeline RAG.
    
    Este adaptador proporciona una interfaz consistente para el pipeline
    utilizando la implementación existente de BM25Search.
    """
    
    def __init__(self, vectorstore_path: str, **kwargs):
        """
        Inicializa el adaptador BM25Retriever.
        
        Args:
            vectorstore_path: Ruta al archivo del vectorstore BM25
            **kwargs: Argumentos adicionales para BM25Search
        """
        self.vectorstore_path = vectorstore_path
        self.search_engine = BM25Search(vectorstore_path)
        self.k = kwargs.get('k', 5)
        logger.info(f"BM25Retriever inicializado con vectorstore: {vectorstore_path}")
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recupera documentos relevantes para una consulta.
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de resultados a devolver (opcional)
            
        Returns:
            Lista de documentos recuperados con sus metadatos
        """
        k = top_k if top_k is not None else self.k
        logger.info(f"Ejecutando búsqueda BM25 para: '{query}' (top_k={k})")
        
        try:
            # Ejecutar búsqueda con BM25Search
            result = self.search_engine.generate_response(query, top_k=k)
            
            # Adaptar formato de resultados si es necesario
            if 'results' in result and result['results']:
                # Convertir al formato esperado por el pipeline
                documents = []
                for i, item in enumerate(result['results']):
                    doc = {
                        'content': item.get('texto', ''),
                        'score': item.get('score', 0.0),
                        'rank': i + 1,
                        'metadata': {
                            'source': item.get('source', 'unknown'),
                            'chunk_id': item.get('id', f"chunk_{i}")
                        }
                    }
                    documents.append(doc)
                
                logger.info(f"Recuperados {len(documents)} documentos con BM25")
                return documents
            else:
                logger.warning(f"No se encontraron resultados para la consulta: '{query}'")
                return []
            
        except Exception as e:
            logger.error(f"Error en BM25Retriever: {str(e)}")
            return []
    
    def get_relevant_documents(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Alias para retrieve() para compatibilidad con LangChain.
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de resultados a devolver (opcional)
            
        Returns:
            Lista de documentos recuperados
        """
        return self.retrieve(query, top_k)


# Ejemplo de uso
if __name__ == "__main__":
    retriever = BM25Retriever('data/processed/vectorstore_bm25_test.pkl')
    results = retriever.retrieve("¿Cuál es el monto máximo para viáticos nacionales?")
    
    print(f"\nResultados ({len(results)}):")
    for i, doc in enumerate(results):
        print(f"\n[{i+1}] Score: {doc['score']:.4f}")
        print(f"Content: {doc['content'][:100]}...")
        print(f"Metadata: {doc['metadata']}")

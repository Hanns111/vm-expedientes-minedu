#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Adaptador para el DenseRetrieverE5.

Este módulo implementa un adaptador para integrar el DenseRetrieverE5 existente
con el pipeline RAG de MINEDU.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Intentar importar DenseRetrieverE5
try:
    from src.ai.retrieval.retriever_dense_e5 import DenseRetrieverE5
except ImportError:
    # Si falla, intentar con una ruta relativa
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    try:
        from src.ai.retrieval.retriever_dense_e5 import DenseRetrieverE5
    except ImportError as e:
        logging.error(f"No se pudo importar DenseRetrieverE5: {str(e)}")
        # Crear una clase mock para evitar errores de importación
        class DenseRetrieverE5:
            def __init__(self, *args, **kwargs):
                pass
            def search(self, *args, **kwargs):
                return []

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DenseRetrieverE5Adapter')


class DenseRetrieverE5Adapter:
    """
    Adaptador para integrar DenseRetrieverE5 con el pipeline RAG.
    
    Este adaptador proporciona una interfaz consistente para el pipeline
    utilizando la implementación existente de DenseRetrieverE5.
    """
    
    def __init__(
        self, 
        model_name: str = "intfloat/multilingual-e5-large",
        device: Optional[str] = None,
        k: int = 5,
        **kwargs
    ):
        """
        Inicializa el adaptador DenseRetrieverE5Adapter.
        
        Args:
            model_name: Nombre del modelo E5 a utilizar
            device: Dispositivo para inferencia ('cpu', 'cuda', etc.)
            k: Número de resultados a devolver por defecto
            **kwargs: Argumentos adicionales para DenseRetrieverE5
        """
        self.model_name = model_name
        self.device = device
        self.k = k
        
        # Inicializar el retriever denso
        self.retriever = DenseRetrieverE5(
            model_name=model_name,
            device=device,
            **kwargs
        )
        
        logger.info(f"DenseRetrieverE5Adapter inicializado con modelo: {model_name}")
    
    def retrieve(self, query: str, passages: List[str], metadata: Optional[List[Dict[str, Any]]] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recupera documentos relevantes para una consulta.
        
        Args:
            query: Consulta de búsqueda
            passages: Lista de pasajes donde buscar
            metadata: Lista de metadatos asociados a los pasajes
            top_k: Número de resultados a devolver (opcional)
            
        Returns:
            Lista de documentos recuperados con sus metadatos
        """
        k = top_k if top_k is not None else self.k
        logger.info(f"Ejecutando búsqueda densa para: '{query}' (top_k={k})")
        
        try:
            # Ejecutar búsqueda con DenseRetrieverE5
            results = self.retriever.search(query, passages, metadata, top_k=k)
            
            # Adaptar formato de resultados
            documents = []
            for i, item in enumerate(results):
                doc = {
                    'content': item.get('text', ''),
                    'score': item.get('score', 0.0),
                    'rank': item.get('rank', i + 1),
                    'metadata': item.get('metadata', {})
                }
                documents.append(doc)
            
            logger.info(f"Recuperados {len(documents)} documentos con DenseRetrieverE5")
            return documents
            
        except Exception as e:
            logger.error(f"Error en DenseRetrieverE5Adapter: {str(e)}")
            return []
    
    def get_relevant_documents(self, query: str, passages: List[str], metadata: Optional[List[Dict[str, Any]]] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Alias para retrieve() para compatibilidad con LangChain.
        
        Args:
            query: Consulta de búsqueda
            passages: Lista de pasajes donde buscar
            metadata: Lista de metadatos asociados a los pasajes
            top_k: Número de resultados a devolver (opcional)
            
        Returns:
            Lista de documentos recuperados
        """
        return self.retrieve(query, passages, metadata, top_k)


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso
    retriever = DenseRetrieverE5Adapter(device="cpu")
    
    # Ejemplo de búsqueda
    query = "¿Cuál es el monto máximo para viáticos nacionales?"
    passages = [
        "Los viáticos nacionales tienen un monto máximo de S/ 320.00 por día según la escala vigente.",
        "El plazo para presentar la rendición de cuentas es de 10 días hábiles contados desde la culminación de la comisión.",
        "Para solicitar viáticos se requiere memorando de autorización, planilla de viáticos y formato de declaración jurada.",
        "Los viáticos para servidores públicos están regulados por el Decreto Supremo N° 007-2013-EF.",
        "Las solicitudes de viáticos son aprobadas por el jefe inmediato del comisionado y el Director de Administración."
    ]
    
    metadata = [
        {"source": "Manual de Procedimientos", "page": 15},
        {"source": "Directiva de Viáticos", "page": 3},
        {"source": "Manual de RRHH", "page": 22},
        {"source": "Directiva de Viáticos", "page": 8},
        {"source": "Manual de Procedimientos", "page": 16}
    ]
    
    results = retriever.retrieve(query, passages, metadata)
    
    print(f"\nResultados ({len(results)}):")
    for i, doc in enumerate(results):
        print(f"\n[{i+1}] Score: {doc['score']:.4f}")
        print(f"Content: {doc['content']}")
        print(f"Metadata: {doc['metadata']}")

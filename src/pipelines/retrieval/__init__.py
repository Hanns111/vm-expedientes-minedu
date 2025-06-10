# retrieval module initialization
# Este archivo permite que Python reconozca el directorio como un paquete

# Importar clases de adaptadores para hacerlas disponibles
try:
    from .bm25_retriever import BM25Retriever
    from .dense_retriever_e5 import DenseRetrieverE5Adapter
    from .hybrid_fusion import HybridFusion
except ImportError as e:
    # Logging de error pero permitir que el módulo se importe parcialmente
    import logging
    logging.warning(f"Error al importar adaptadores de retrieval: {e}")

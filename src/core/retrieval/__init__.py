"""
Módulos centralizados de recuperación de información para el sistema RAG MINEDU.

Este paquete contiene las implementaciones centralizadas de:
- TF-IDF Retriever
- BM25 Retriever  
- Transformer Retriever
- Hybrid Fusion

Autor: Hanns
Fecha: 2025-06-14
"""

from .tfidf_retriever import TFIDFRetriever
from .bm25_retriever import BM25Retriever
from .transformer_retriever import TransformerRetriever
from .hybrid_fusion import HybridFusion

__all__ = [
    'TFIDFRetriever',
    'BM25Retriever', 
    'TransformerRetriever',
    'HybridFusion'
] 
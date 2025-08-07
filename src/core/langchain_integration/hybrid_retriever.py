"""
Hybrid Retriever para LangChain
Integra el sistema híbrido existente con LangChain
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from langchain.schema import Document
    from langchain.retrievers.base import BaseRetriever
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseRetriever = object  # Fallback

logger = logging.getLogger(__name__)

class HybridLangChainRetriever:
    """
    Retriever híbrido que integra el sistema existente con LangChain
    """
    
    def __init__(self, chunks_path: Optional[Path] = None):
        self.chunks_path = chunks_path or Path("data/processed/chunks.json")
        logger.info("🔍 HybridLangChainRetriever inicializado")
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Obtener documentos relevantes para la query"""
        # Implementación básica por ahora
        return []
    
    def aget_relevant_documents(self, query: str) -> List[Document]:
        """Versión async de get_relevant_documents"""
        return self.get_relevant_documents(query) 
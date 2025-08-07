"""
Sistema de carga dinámica de documentos normativos
Permite cargar nuevos PDFs/documentos sin reiniciar el sistema
"""

from .dynamic_loader import DynamicDocumentLoader, DocumentMetadata, ProcessingResult
from .document_processor import DocumentProcessor, ChunkingStrategy
from .vectorstore_updater import VectorstoreUpdater, UpdateStrategy

__all__ = [
    'DynamicDocumentLoader',
    'DocumentMetadata',
    'ProcessingResult',
    'DocumentProcessor', 
    'ChunkingStrategy',
    'VectorstoreUpdater',
    'UpdateStrategy'
]
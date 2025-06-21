"""
OCR Pipeline Extractors Module
==============================

Extractores especializados para diferentes tipos de contenido en documentos PDF.
"""

from .robust_table_extractor import RobustTableExtractor

__all__ = ['RobustTableExtractor']
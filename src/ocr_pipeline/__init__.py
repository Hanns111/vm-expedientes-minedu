"""
OCR Pipeline for Legal Document Processing
==========================================

This module provides a comprehensive OCR pipeline for processing scanned legal documents,
extracting text, detecting layout structures, and preserving hierarchical information.

Components:
- OCR Engine (PaddleOCR optimized for Spanish)
- Layout Detection (LayoutParser + Detectron2)
- Structure Analysis (Legal hierarchy detection)
- Entity Extraction (Legal/financial entities)
"""

# Conditional imports to handle missing dependencies gracefully
try:
    from .core.ocr_engine import OCREngine
except ImportError:
    OCREngine = None

try:
    from .core.layout_detector import LayoutDetector
except ImportError:
    LayoutDetector = None

try:
    from .core.structure_analyzer import StructureAnalyzer
except ImportError:
    StructureAnalyzer = None

try:
    from .processors.legal_ner import LegalNER
except ImportError:
    LegalNER = None

try:
    from .processors.intelligent_chunker import IntelligentChunker
except ImportError:
    IntelligentChunker = None

try:
    from .pipeline import DocumentProcessor
except ImportError:
    DocumentProcessor = None

__version__ = "1.0.0"
__author__ = "Hans - MINEDU OCR Pipeline"

__all__ = [
    "OCREngine",
    "LayoutDetector", 
    "StructureAnalyzer",
    "LegalNER",
    "IntelligentChunker",
    "DocumentProcessor"
]
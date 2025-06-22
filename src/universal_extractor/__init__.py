"""
Universal Legal Document Extractor
==================================

Sistema adaptativo universal para extraer tablas, numerales y montos 
de cualquier norma legal sin configuración manual.

Componentes principales:
- GenericTableExtractor: Detección auto-ajustable de tablas
- GenericMoneyDetector: Identificación dinámica de montos y numerales  
- ConfigOptimizer: Auto-configuración por documento
- AdaptivePipeline: Orquestador principal con fallbacks inteligentes
"""

__version__ = "1.0.0"
__author__ = "Sistema Adaptativo MINEDU"

from .generic_table_extractor import GenericTableExtractor
from .generic_money_detector import GenericMoneyDetector  
from .config_optimizer import ConfigOptimizer
from .adaptive_pipeline import AdaptivePipeline

__all__ = [
    "GenericTableExtractor",
    "GenericMoneyDetector", 
    "ConfigOptimizer",
    "AdaptivePipeline"
]
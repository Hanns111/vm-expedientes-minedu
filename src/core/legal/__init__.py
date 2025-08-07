"""
Módulo de análisis legal avanzado
Concordancia normativa, relaciones entre fuentes, análisis jurídico
"""

from .normative_concordance import NormativeConcordance, RelatedNorm, NormativeRelation
from .legal_analyzer import LegalAnalyzer, LegalConflict
from .report_generator import NormativeReportGenerator, ReportTemplate

__all__ = [
    'NormativeConcordance',
    'RelatedNorm',
    'NormativeRelation', 
    'LegalAnalyzer',
    'LegalConflict',
    'NormativeReportGenerator',
    'ReportTemplate'
]
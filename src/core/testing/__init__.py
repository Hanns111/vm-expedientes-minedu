"""
Módulo de testing de cobertura normativa
Validación automatizada de cobertura semántica del RAG
"""

from .normative_coverage import (
    NormativeCoverageTester, 
    CoverageMetric, 
    CoverageReport,
    pytest_coverage_test,
    global_coverage_tester
)

__all__ = [
    'NormativeCoverageTester',
    'CoverageMetric', 
    'CoverageReport',
    'pytest_coverage_test',
    'global_coverage_tester'
]
"""
Módulo de cálculos normativos para MINEDU
Implementa cálculos sobre tablas normativas con fallback sin pandas
"""

# Usar versión simplificada sin pandas temporalmente
from .normative_calculator_simple import NormativeCalculator, UIT, TipoCambio, UIT_VALUES

# TemporalLegalProcessor comentado temporalmente (requiere pandas)
# from .temporal_legal import TemporalLegalProcessor

# SanctionsCalculator comentado temporalmente
# from .sanctions_calculator import SanctionsCalculator

__all__ = [
    'NormativeCalculator',
    'UIT',
    'TipoCambio',
    'UIT_VALUES',
    # 'TemporalLegalProcessor',
    # 'SanctionsCalculator'
]
"""
Calculadora de sanciones - Fase 4
Calcula sanciones y penalidades normativas
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class SanctionResult:
    """Resultado de cálculo de sanción"""
    sanction_type: str
    amount: Decimal
    basis: str
    applicable_rules: List[str]
    severity: str

class SanctionsCalculator:
    """
    Calculadora de sanciones administrativas
    """
    
    def __init__(self):
        self.sanction_types = {
            "leve": Decimal("0.25"),
            "grave": Decimal("0.50"),
            "muy_grave": Decimal("1.00")
        }
        logger.info("⚖️ SanctionsCalculator inicializado")
    
    def calculate_sanction(self, violation_type: str, context: Dict[str, Any] = None) -> SanctionResult:
        """Calcular sanción por violación"""
        
        # Lógica básica por ahora
        severity = "leve"
        if context and context.get("recurring", False):
            severity = "grave"
        
        multiplier = self.sanction_types.get(severity, Decimal("0.25"))
        base_amount = Decimal("1000.00")  # UIT base simplificado
        
        amount = base_amount * multiplier
        
        return SanctionResult(
            sanction_type=violation_type,
            amount=amount,
            basis=f"UIT base × {multiplier}",
            applicable_rules=["Reglamento General"],
            severity=severity
        )
    
    def get_calculator_stats(self) -> Dict[str, Any]:
        """Estadísticas de la calculadora"""
        return {
            "calculator_type": "sanctions",
            "sanction_types": len(self.sanction_types),
            "status": "active"
        } 
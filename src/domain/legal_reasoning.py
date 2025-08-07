"""
Motor de razonamiento legal para análisis de normativas MINEDU
"""

from datetime import datetime
from typing import Dict, List, Optional
import re

class LegalReasoner:
    """Motor de razonamiento legal para documentos gubernamentales"""

    def __init__(self) -> None:
        self.vigencia_keywords = [
            "vigente",
            "derogado",
            "modificado",
            "suspendido",
            "actualizado",
        ]
        self.conflict_patterns = [
            "contradice",
            "deroga",
            "modifica",
            "reemplaza",
            "anula",
        ]
        # Nivel de jerarquía normativa (mayor número = mayor jerarquía)
        self.authority_levels = {
            "decreto_supremo": 100,
            "resolucion_ministerial": 90,
            "directiva": 80,
            "circular": 70,
        }

    # ------------------------------------------------------------------
    # Evaluación de vigencia
    # ------------------------------------------------------------------
    def analyze_norm_validity(self, text: str, document_metadata: Optional[dict] = None) -> Dict:
        """Analizar si una norma está vigente basado en el contenido textual."""
        validity_analysis: Dict = {
            "is_valid": True,
            "confidence": 0.80,
            "validity_evidence": [],
            "last_modification": None,
            "legal_status": "vigente",
            "analysis_date": datetime.now().isoformat(),
        }

        text_lower = text.lower()

        # Indicadores de derogación
        if any(k in text_lower for k in ["derogado", "sin efecto", "anulado"]):
            validity_analysis.update(
                {
                    "is_valid": False,
                    "legal_status": "derogado",
                    "confidence": 0.90,
                    "validity_evidence": [
                        "Texto contiene indicadores de derogación/ineficacia",
                    ],
                }
            )

        # Indicadores de modificación
        if any(k in text_lower for k in ["modificado", "actualizado", "reformado"]):
            validity_analysis.update(
                {
                    "legal_status": "modificado",
                    "confidence": max(validity_analysis["confidence"], 0.85),
                    "validity_evidence": validity_analysis["validity_evidence"]
                    + ["Documento indica modificaciones"],
                }
            )

        # Búsqueda de fechas
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b"
        dates_found = re.findall(date_pattern, text)
        if dates_found:
            validity_analysis["validity_evidence"].append(
                f"Fechas encontradas: {dates_found}"
            )

        return validity_analysis

    # ------------------------------------------------------------------
    # Detección de conflictos normativos
    # ------------------------------------------------------------------
    def detect_legal_conflicts(self, documents: List[Dict]) -> List[Dict]:
        """Detectar conflictos potenciales entre documentos legales."""
        conflicts: List[Dict] = []
        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i + 1 :], i + 1):
                conflict_info = self._analyze_document_conflict(doc1, doc2)
                if conflict_info:
                    conflicts.append(conflict_info)
        return conflicts

    def _analyze_document_conflict(self, doc1: Dict, doc2: Dict) -> Optional[Dict]:
        """Analizar conflicto entre dos documentos concretos."""
        text1 = doc1.get("content", "").lower()
        text2 = doc2.get("content", "").lower()

        for pattern in self.conflict_patterns:
            if pattern in text1 and pattern in text2:
                return {
                    "conflict_type": "potential_contradiction",
                    "documents": [doc1.get("title", "Doc 1"), doc2.get("title", "Doc 2")],
                    "evidence": f"Ambos documentos contienen el patrón '{pattern}'",
                    "severity": "medium",
                    "requires_review": True,
                }
        return None

    # ------------------------------------------------------------------
    # Proveer razonamiento legal completo
    # ------------------------------------------------------------------
    def provide_legal_reasoning(self, query: str, documents: List[Dict]) -> str:
        """Generar razonamiento legal en texto estructurado."""
        parts: List[str] = []
        parts.append("⚖️ **ANÁLISIS LEGAL AUTOMÁTICO**\n")
        parts.append(f"🔍 **Consulta analizada**: {query}\n")

        # Evaluación de vigencia
        if documents:
            parts.append("📋 **EVALUACIÓN DE VIGENCIA:**")
            for idx, doc in enumerate(documents[:3]):
                validity = self.analyze_norm_validity(doc.get("content", ""))
                icon = "✅" if validity["is_valid"] else "❌"
                parts.append(
                    f"{icon} **Documento {idx+1}**: {validity['legal_status']} "
                    f"(Confianza: {validity['confidence']:.0%})"
                )
        else:
            parts.append("⚠️ No se proporcionaron documentos para análisis de vigencia.")

        # Conflictos
        conflicts = self.detect_legal_conflicts(documents)
        if conflicts:
            parts.append("\n⚠️ **CONFLICTOS DETECTADOS:**")
            for c in conflicts[:2]:
                parts.append(f"• {c['evidence']}")
        else:
            parts.append("\n✅ **SIN CONFLICTOS DETECTADOS** entre documentos analizados")

        parts.append("\n📊 **CONCLUSIÓN LEGAL:**")
        parts.append("• Información extraída de documentos oficiales MINEDU")
        parts.append("• Análisis automático de vigencia normativa")
        parts.append("• Respuesta basada en normativa actual disponible")

        parts.append(
            "\n⚖️ **IMPORTANTE**: Este análisis es automatizado. "
            "Para decisiones legales críticas, consultar asesoría jurídica profesional."
        )

        return "\n".join(parts)


# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------

def create_legal_reasoner() -> LegalReasoner:
    """Crear instancia del motor de razonamiento legal"""
    return LegalReasoner() 
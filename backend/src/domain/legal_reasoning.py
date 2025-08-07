"""
Motor de razonamiento legal para análisis de normativas MINEDU
"""
from datetime import datetime
from typing import Dict, List, Optional
import re

class LegalReasoner:
    """Motor de razonamiento legal para documentos gubernamentales"""
    
    def __init__(self):
        self.vigencia_keywords = ["vigente", "derogado", "modificado", "suspendido", "actualizado"]
        self.conflict_patterns = ["contradice", "deroga", "modifica", "reemplaza", "anula"]
        self.authority_levels = {
            "decreto_supremo": 100,
            "resolucion_ministerial": 90,
            "directiva": 80,
            "circular": 70
        }
    
    def analyze_norm_validity(self, text: str, document_metadata: dict = None) -> Dict:
        """
        Analizar si una norma está vigente basado en el contenido
        """
        validity_analysis = {
            "is_valid": True,
            "confidence": 0.8,
            "validity_evidence": [],
            "last_modification": None,
            "legal_status": "vigente",
            "analysis_date": datetime.now().isoformat()
        }
        
        text_lower = text.lower()
        
        # Detectar indicadores de derogación
        if any(keyword in text_lower for keyword in ["derogado", "sin efecto", "anulado"]):
            validity_analysis.update({
                "is_valid": False,
                "legal_status": "derogado",
                "confidence": 0.9,
                "validity_evidence": ["Texto contiene indicadores de derogación"]
            })
        
        # Detectar modificaciones
        if any(keyword in text_lower for keyword in ["modificado", "actualizado", "reformado"]):
            validity_analysis.update({
                "legal_status": "modificado",
                "confidence": 0.85,
                "validity_evidence": ["Documento indica modificaciones"]
            })
        
        # Buscar fechas de vigencia
        date_patterns = r'\d{1,2}[/-]\d{1,2}[/-]\d{4}'
        dates_found = re.findall(date_patterns, text)
        if dates_found:
            validity_analysis["validity_evidence"].append(f"Fechas encontradas: {dates_found}")
        
        return validity_analysis
    
    def detect_legal_conflicts(self, documents: List[Dict]) -> List[Dict]:
        """
        Detectar conflictos potenciales entre documentos legales
        """
        conflicts = []
        
        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i+1:], i+1):
                conflict = self._analyze_document_conflict(doc1, doc2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _analyze_document_conflict(self, doc1: Dict, doc2: Dict) -> Optional[Dict]:
        """Analizar conflicto entre dos documentos"""
        text1 = doc1.get('content', '').lower()
        text2 = doc2.get('content', '').lower()
        
        # Buscar patrones de conflicto
        for pattern in self.conflict_patterns:
            if pattern in text1 and pattern in text2:
                return {
                    "conflict_type": "potential_contradiction",
                    "documents": [doc1.get('title', 'Doc 1'), doc2.get('title', 'Doc 2')],
                    "evidence": f"Ambos documentos contienen: {pattern}",
                    "severity": "medium",
                    "requires_review": True
                }
        
        return None
    
    def provide_legal_reasoning(self, query: str, documents: List[Dict]) -> str:
        """
        Proporcionar razonamiento legal estructurado para una consulta
        """
        reasoning_parts = []
        
        # Encabezado
        reasoning_parts.append("⚖️ **ANÁLISIS LEGAL AUTOMÁTICO**\n")
        reasoning_parts.append(f"🔍 **Consulta analizada**: {query}\n")
        
        # Análisis de vigencia
        if documents:
            reasoning_parts.append("📋 **EVALUACIÓN DE VIGENCIA:**")
            for i, doc in enumerate(documents[:3]):
                validity = self.analyze_norm_validity(doc.get('content', ''))
                status_icon = "✅" if validity['is_valid'] else "❌"
                reasoning_parts.append(
                    f"{status_icon} **Documento {i+1}**: {validity['legal_status']} "
                    f"(Confianza: {validity['confidence']:.0%})"
                )
        
        # Análisis de conflictos
        conflicts = self.detect_legal_conflicts(documents)
        if conflicts:
            reasoning_parts.append("\n⚠️ **CONFLICTOS DETECTADOS:**")
            for conflict in conflicts[:2]:
                reasoning_parts.append(f"• {conflict['evidence']}")
        else:
            reasoning_parts.append("\n✅ **SIN CONFLICTOS DETECTADOS** entre documentos analizados")
        
        # Conclusión legal
        reasoning_parts.append("\n📊 **CONCLUSIÓN LEGAL:**")
        reasoning_parts.append("• Información extraída de documentos oficiales MINEDU")
        reasoning_parts.append("• Análisis automático de vigencia normativa")
        reasoning_parts.append("• Respuesta basada en normativa actual disponible")
        
        # Disclaimer
        reasoning_parts.append("\n⚖️ **IMPORTANTE**: Este análisis es automatizado. "
                            "Para decisiones legales críticas, consultar con asesoría jurídica especializada.")
        
        return "\n".join(reasoning_parts)

# Factory function
def create_legal_reasoner() -> LegalReasoner:
    """Crear instancia del motor de razonamiento legal"""
    return LegalReasoner()
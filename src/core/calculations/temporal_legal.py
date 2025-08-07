"""
Procesador de temporalidad legal
Detecta año de referencia en consultas y aplica normativa vigente
"""
import re
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class LegalPeriod:
    """Período legal con normativa específica"""
    start_date: date
    end_date: Optional[date]
    regulation: str
    description: str
    changes: List[str]
    
@dataclass
class TemporalQuery:
    """Consulta con contexto temporal"""
    original_query: str
    detected_year: Optional[int]
    detected_date: Optional[date]
    temporal_context: str  # "historical", "current", "future", "comparative"
    confidence: float

class TemporalLegalProcessor:
    """
    Procesador de temporalidad legal para consultas con referencias históricas
    Detecta año/fecha y aplica normativa vigente en ese período
    """
    
    def __init__(self):
        self.current_year = datetime.now().year
        
        # Patrones para detectar referencias temporales
        self.temporal_patterns = [
            # Años específicos
            (r"\b(20\d{2})\b", "year"),
            (r"\b(19\d{2})\b", "year"),
            (r"en\s+(el\s+)?(año\s+)?(20\d{2})", "year"),
            (r"durante\s+(el\s+)?(año\s+)?(20\d{2})", "year"),
            
            # Fechas específicas
            (r"\b(\d{1,2})[\/\-](\d{1,2})[\/\-](20\d{2})\b", "date"),
            (r"\b(\d{1,2})\s+de\s+(\w+)\s+del?\s+(20\d{2})", "date"),
            
            # Referencias relativas
            (r"\b(hace\s+\d+\s+años?)\b", "relative"),
            (r"\b(el\s+año\s+pasado|año\s+anterior)\b", "relative"),
            (r"\b(actualmente|en\s+la\s+actualidad|hoy\s+en\s+día)\b", "current"),
            (r"\b(vigente|actual|en\s+vigor)\b", "current"),
            
            # Comparaciones temporales
            (r"(diferencia|comparar|cambio)\s+.*(entre|desde|de)\s+.*(20\d{2})", "comparative"),
            (r"(20\d{2})\s+(vs|versus|contra|frente\s+a)\s+(20\d{2})", "comparative"),
            (r"evolución\s+.*(desde|de)\s+(20\d{2})", "comparative")
        ]
        
        # Períodos legales importantes MINEDU
        self.legal_periods = self._load_legal_periods()
        
        logger.info("📅 TemporalLegalProcessor inicializado")
    
    def _load_legal_periods(self) -> List[LegalPeriod]:
        """Cargar períodos legales importantes"""
        return [
            LegalPeriod(
                start_date=date(2013, 1, 1),
                end_date=None,  # Vigente
                regulation="DS-007-2013-EF",
                description="Decreto Supremo que establece disposiciones para el otorgamiento de viáticos",
                changes=["Establecimiento de montos actuales", "Unificación de criterios"]
            ),
            LegalPeriod(
                start_date=date(2020, 1, 1),
                end_date=date(2020, 12, 31),
                regulation="COVID-19 Restrictions",
                description="Restricciones por pandemia - reducción de viajes",
                changes=["Limitación de comisiones", "Protocolos sanitarios"]
            ),
            LegalPeriod(
                start_date=date(2002, 1, 1),
                end_date=date(2012, 12, 31),
                regulation="Sistema Anterior",
                description="Normativa anterior al DS-007-2013-EF",
                changes=["Montos diferentes", "Criterios descentralizados"]
            )
        ]
    
    def detect_temporal_context(self, query: str) -> TemporalQuery:
        """Detectar contexto temporal en la consulta"""
        try:
            detected_year = None
            detected_date = None
            temporal_context = "current"  # Por defecto
            confidence = 0.0
            
            query_lower = query.lower()
            
            # Buscar patrones temporales
            for pattern, pattern_type in self.temporal_patterns:
                matches = re.finditer(pattern, query_lower)
                
                for match in matches:
                    if pattern_type == "year":
                        # Extraer año
                        year_match = re.search(r"(20\d{2}|19\d{2})", match.group())
                        if year_match:
                            detected_year = int(year_match.group())
                            confidence = 0.9
                            
                            if detected_year < self.current_year - 1:
                                temporal_context = "historical"
                            elif detected_year > self.current_year:
                                temporal_context = "future"
                            else:
                                temporal_context = "current"
                    
                    elif pattern_type == "date":
                        # Extraer fecha completa
                        try:
                            if "/" in match.group() or "-" in match.group():
                                date_parts = re.findall(r"\d+", match.group())
                                if len(date_parts) >= 3:
                                    day, month, year = date_parts[0], date_parts[1], date_parts[2]
                                    detected_date = date(int(year), int(month), int(day))
                                    detected_year = int(year)
                                    confidence = 0.95
                                    temporal_context = "historical" if detected_year < self.current_year else "current"
                        except ValueError:
                            continue
                    
                    elif pattern_type == "comparative":
                        temporal_context = "comparative"
                        confidence = 0.8
                        # Intentar extraer años para comparación
                        years = re.findall(r"20\d{2}", match.group())
                        if years:
                            detected_year = int(years[0])  # Primer año encontrado
                    
                    elif pattern_type == "current":
                        temporal_context = "current"
                        confidence = 0.7
                        detected_year = self.current_year
                    
                    elif pattern_type == "relative":
                        temporal_context = "historical"
                        confidence = 0.6
                        # Intentar inferir año basado en "hace X años"
                        years_ago_match = re.search(r"hace\s+(\d+)\s+años?", match.group())
                        if years_ago_match:
                            years_ago = int(years_ago_match.group(1))
                            detected_year = self.current_year - years_ago
            
            return TemporalQuery(
                original_query=query,
                detected_year=detected_year,
                detected_date=detected_date,
                temporal_context=temporal_context,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Error detectando contexto temporal: {e}")
            return TemporalQuery(
                original_query=query,
                detected_year=None,
                detected_date=None,
                temporal_context="current",
                confidence=0.0
            )
    
    def get_applicable_regulation(self, target_date: date) -> Optional[LegalPeriod]:
        """Obtener la regulación aplicable para una fecha específica"""
        try:
            for period in self.legal_periods:
                if period.start_date <= target_date:
                    if period.end_date is None or target_date <= period.end_date:
                        return period
            
            # Si no se encuentra período específico, usar el más reciente
            return max(self.legal_periods, key=lambda p: p.start_date)
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo regulación aplicable: {e}")
            return None
    
    def explain_temporal_differences(
        self, 
        query: str,
        year1: int,
        year2: int
    ) -> Dict[str, Any]:
        """Explicar diferencias entre versiones normativas"""
        try:
            date1 = date(year1, 1, 1)
            date2 = date(year2, 1, 1)
            
            regulation1 = self.get_applicable_regulation(date1)
            regulation2 = self.get_applicable_regulation(date2)
            
            differences = {
                "query": query,
                "comparison_years": [year1, year2],
                "regulations": {
                    year1: {
                        "regulation": regulation1.regulation if regulation1 else "No disponible",
                        "description": regulation1.description if regulation1 else "Información no disponible",
                        "period": f"{regulation1.start_date} - {regulation1.end_date or 'Vigente'}" if regulation1 else "N/A"
                    },
                    year2: {
                        "regulation": regulation2.regulation if regulation2 else "No disponible", 
                        "description": regulation2.description if regulation2 else "Información no disponible",
                        "period": f"{regulation2.start_date} - {regulation2.end_date or 'Vigente'}" if regulation2 else "N/A"
                    }
                },
                "changes_detected": [],
                "analysis_date": datetime.now().isoformat()
            }
            
            # Detectar cambios
            if regulation1 and regulation2:
                if regulation1.regulation != regulation2.regulation:
                    differences["changes_detected"].append({
                        "type": "regulation_change",
                        "description": f"Cambio de {regulation1.regulation} a {regulation2.regulation}",
                        "impact": "high"
                    })
                
                # Comparar cambios específicos
                if regulation1.changes != regulation2.changes:
                    differences["changes_detected"].append({
                        "type": "criteria_change",
                        "description": "Cambios en criterios de aplicación",
                        "details": {
                            year1: regulation1.changes,
                            year2: regulation2.changes
                        },
                        "impact": "medium"
                    })
            
            return differences
            
        except Exception as e:
            logger.error(f"❌ Error explicando diferencias temporales: {e}")
            return {"error": str(e)}
    
    def enhance_query_with_temporal_context(
        self, 
        query: str,
        temporal_query: TemporalQuery
    ) -> str:
        """Mejorar consulta con contexto temporal específico"""
        try:
            enhanced_query = query
            
            if temporal_query.detected_year:
                year = temporal_query.detected_year
                
                # Agregar contexto temporal específico
                if temporal_query.temporal_context == "historical":
                    enhanced_query += f" [CONTEXTO TEMPORAL: Año {year} - Normativa histórica aplicable]"
                elif temporal_query.temporal_context == "comparative":
                    enhanced_query += f" [CONTEXTO TEMPORAL: Comparación temporal incluyendo año {year}]"
                elif temporal_query.temporal_context == "current":
                    enhanced_query += f" [CONTEXTO TEMPORAL: Normativa vigente en {year}]"
                
                # Agregar información de regulación aplicable
                if temporal_query.detected_date:
                    applicable_regulation = self.get_applicable_regulation(temporal_query.detected_date)
                else:
                    applicable_regulation = self.get_applicable_regulation(date(year, 1, 1))
                
                if applicable_regulation:
                    enhanced_query += f" [REGULACIÓN APLICABLE: {applicable_regulation.regulation}]"
            
            return enhanced_query
            
        except Exception as e:
            logger.error(f"❌ Error mejorando consulta con contexto temporal: {e}")
            return query
    
    def process_temporal_query(self, query: str) -> Dict[str, Any]:
        """Procesamiento completo de consulta temporal"""
        try:
            # Detectar contexto temporal
            temporal_query = self.detect_temporal_context(query)
            
            # Mejorar consulta
            enhanced_query = self.enhance_query_with_temporal_context(query, temporal_query)
            
            # Obtener regulación aplicable
            applicable_regulation = None
            if temporal_query.detected_year:
                ref_date = temporal_query.detected_date or date(temporal_query.detected_year, 1, 1)
                applicable_regulation = self.get_applicable_regulation(ref_date)
            
            result = {
                "original_query": query,
                "enhanced_query": enhanced_query,
                "temporal_analysis": {
                    "detected_year": temporal_query.detected_year,
                    "detected_date": temporal_query.detected_date.isoformat() if temporal_query.detected_date else None,
                    "temporal_context": temporal_query.temporal_context,
                    "confidence": temporal_query.confidence
                },
                "applicable_regulation": {
                    "regulation": applicable_regulation.regulation if applicable_regulation else None,
                    "description": applicable_regulation.description if applicable_regulation else None,
                    "period": f"{applicable_regulation.start_date} - {applicable_regulation.end_date or 'Vigente'}" if applicable_regulation else None,
                    "changes": applicable_regulation.changes if applicable_regulation else []
                } if applicable_regulation else None,
                "processing_recommendations": self._get_processing_recommendations(temporal_query),
                "processing_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando consulta temporal: {e}")
            return {
                "original_query": query,
                "enhanced_query": query,
                "error": str(e)
            }
    
    def _get_processing_recommendations(self, temporal_query: TemporalQuery) -> List[str]:
        """Obtener recomendaciones de procesamiento"""
        recommendations = []
        
        if temporal_query.temporal_context == "historical":
            recommendations.append("Usar normativa vigente en el año específico")
            recommendations.append("Mencionar cambios posteriores si los hay")
            recommendations.append("Incluir contexto histórico en la respuesta")
        
        elif temporal_query.temporal_context == "comparative":
            recommendations.append("Proporcionar comparación entre períodos")
            recommendations.append("Explicar diferencias normativas")
            recommendations.append("Mostrar evolución temporal")
        
        elif temporal_query.temporal_context == "current":
            recommendations.append("Usar normativa vigente actual")
            recommendations.append("Mencionar fecha de última actualización")
        
        elif temporal_query.temporal_context == "future":
            recommendations.append("Indicar que es proyección")
            recommendations.append("Usar normativa vigente actual como referencia")
            recommendations.append("Advertir sobre posibles cambios")
        
        if temporal_query.confidence < 0.5:
            recommendations.append("Solicitar aclaración del período temporal")
        
        return recommendations
    
    def get_temporal_summary(self) -> Dict[str, Any]:
        """Resumen del procesador temporal"""
        return {
            "status": "operational",
            "current_year": self.current_year,
            "patterns_loaded": len(self.temporal_patterns),
            "legal_periods_loaded": len(self.legal_periods),
            "supported_contexts": ["historical", "current", "future", "comparative"],
            "date_patterns_supported": [
                "Años específicos (2000-2099)",
                "Fechas DD/MM/YYYY",
                "Referencias relativas (hace X años)",
                "Comparaciones temporales",
                "Contexto actual/vigente"
            ]
        }
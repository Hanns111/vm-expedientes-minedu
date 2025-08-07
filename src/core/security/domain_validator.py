"""
Validador de dominio para restringir consultas a temas administrativos del sector educativo
y prevenir alucinaciones del sistema
"""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from src.core.config.security_config import SecurityConfig
from src.core.security.input_validator import SecurityError

class DomainScope(Enum):
    """Alcance de dominio permitido"""
    ADMINISTRATIVE = "administrativo"
    FINANCIAL = "financiero" 
    REGULATORY = "normativo"
    EDUCATIONAL = "educativo"
    OUT_OF_SCOPE = "fuera_de_alcance"

@dataclass
class DomainValidationResult:
    """Resultado de validación de dominio"""
    is_valid: bool
    domain_scope: DomainScope
    confidence: float
    reason: str
    suggestions: List[str]

class DomainValidator:
    """Validador que restringe el sistema a temas administrativos del sector educativo"""
    
    # Palabras clave administrativas permitidas
    ADMINISTRATIVE_KEYWORDS = {
        "viáticos", "viatico", "pasajes", "comisión", "servicios", "directiva",
        "expediente", "tramite", "procedimiento", "resolución", "norma",
        "reglamento", "decreto", "ordenanza", "circular", "memorando",
        "solicitud", "autorización", "aprobación", "presupuesto", "gastos",
        "rendición", "cuentas", "comprobante", "factura", "declaración",
        "jurada", "minedu", "ministerio", "educación", "funcionario",
        "servidor", "comisionado", "unidad", "ejecutora", "administración",
        "tesorería", "contabilidad", "control", "previo", "logística",
        "recursos", "humanos", "planificación", "coordinación", "jefe",
        "director", "secretario", "viceministro", "ministro"
    }
    
    # Palabras clave educativas permitidas  
    EDUCATIONAL_KEYWORDS = {
        "educación", "educativo", "escuela", "colegio", "universidad",
        "instituto", "estudiante", "alumno", "profesor", "docente",
        "maestro", "director", "pedagógico", "curricular", "académico",
        "enseñanza", "aprendizaje", "evaluación", "calificación",
        "matrícula", "inscripción", "certificado", "diploma", "título",
        "grado", "nivel", "básica", "secundaria", "superior", "inicial",
        "primaria", "bachillerato", "educación", "técnica", "especial"
    }
    
    # Palabras clave financieras permitidas
    FINANCIAL_KEYWORDS = {
        "presupuesto", "gasto", "ingreso", "fondo", "recurso", "financiero",
        "económico", "costo", "precio", "tarifa", "monto", "suma", "total",
        "pago", "abono", "depósito", "transferencia", "cheque", "efectivo",
        "banco", "cuenta", "cci", "ruc", "igv", "impuesto", "retención",
        "factura", "boleta", "comprobante", "recibo", "soles", "dólares",
        "moneda", "cambio", "cotización", "liquidación", "reembolso"
    }
    
    # Temas explícitamente fuera del alcance
    OUT_OF_SCOPE_KEYWORDS = {
        "medicina", "salud", "enfermedad", "hospital", "clínica", "médico",
        "deportes", "fútbol", "básquet", "tenis", "olimpiadas", "campeonato",
        "entretenimiento", "música", "película", "actor", "cantante",
        "tecnología", "programación", "software", "hardware", "internet",
        "política", "partido", "elecciones", "candidato", "presidente",
        "economía", "bolsa", "inversión", "acciones", "mercado", "empresa",
        "religión", "iglesia", "dios", "biblia", "oración", "fe",
        "militar", "guerra", "ejército", "soldado", "arma", "conflicto",
        "internacional", "extranjero", "país", "nación", "mundial",
        "personal", "privado", "íntimo", "familiar", "matrimonio", "divorcio"
    }
    
    @classmethod
    def validate_domain_scope(cls, query: str) -> DomainValidationResult:
        """
        Valida si una consulta está dentro del dominio permitido
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Resultado de validación de dominio
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Verificar palabras explícitamente fuera del alcance
        out_of_scope_matches = query_words.intersection(cls.OUT_OF_SCOPE_KEYWORDS)
        if out_of_scope_matches:
            return DomainValidationResult(
                is_valid=False,
                domain_scope=DomainScope.OUT_OF_SCOPE,
                confidence=0.9,
                reason=f"La consulta contiene temas fuera del alcance: {', '.join(out_of_scope_matches)}",
                suggestions=[
                    "Este sistema está restringido a temas administrativos y educativos del MINEDU",
                    "Reformule su consulta sobre viáticos, trámites o procedimientos administrativos",
                    "Consulte temas relacionados con la directiva de viáticos o normativas educativas"
                ]
            )
        
        # Calcular puntuaciones por dominio
        admin_score = len(query_words.intersection(cls.ADMINISTRATIVE_KEYWORDS))
        edu_score = len(query_words.intersection(cls.EDUCATIONAL_KEYWORDS))
        fin_score = len(query_words.intersection(cls.FINANCIAL_KEYWORDS))
        
        total_domain_words = admin_score + edu_score + fin_score
        total_words = len(query_words)
        
        # Si no hay palabras de dominio, es sospechoso
        if total_domain_words == 0:
            return DomainValidationResult(
                is_valid=False,
                domain_scope=DomainScope.OUT_OF_SCOPE,
                confidence=0.8,
                reason="La consulta no contiene términos administrativos o educativos reconocidos",
                suggestions=[
                    "Incluya términos relacionados con viáticos, trámites o procedimientos del MINEDU",
                    "Especifique si consulta sobre directivas, normativas o documentos administrativos",
                    "Use términos como: viáticos, expediente, procedimiento, autorización, etc."
                ]
            )
        
        # Determinar dominio principal
        if admin_score >= edu_score and admin_score >= fin_score:
            domain_scope = DomainScope.ADMINISTRATIVE
        elif edu_score >= fin_score:
            domain_scope = DomainScope.EDUCATIONAL
        else:
            domain_scope = DomainScope.FINANCIAL
        
        # Calcular confianza
        confidence = min(0.9, total_domain_words / max(total_words, 1))
        
        return DomainValidationResult(
            is_valid=True,
            domain_scope=domain_scope,
            confidence=confidence,
            reason=f"Consulta válida en dominio {domain_scope.value}",
            suggestions=[]
        )
    
    @classmethod
    def check_information_availability(cls, query: str, search_results: List[Dict]) -> Tuple[bool, str]:
        """
        Verifica si los resultados de búsqueda contienen información relevante
        para responder la consulta específica
        
        Args:
            query: Consulta original del usuario
            search_results: Resultados de la búsqueda
            
        Returns:
            (tiene_información, mensaje_explicativo)
        """
        if not search_results:
            return False, cls._generate_no_information_message(query, "no_results")
        
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        # Remover palabras vacías
        stop_words = {"el", "la", "de", "en", "y", "a", "es", "por", "para", "con", "su", "que", "se", "del"}
        query_keywords = query_keywords - stop_words
        
        if not query_keywords:
            return False, cls._generate_no_information_message(query, "no_keywords")
        
        # Verificar relevancia de resultados
        relevant_results = 0
        for result in search_results:
            content = result.get('text', result.get('content', '')).lower()
            content_words = set(re.findall(r'\b\w+\b', content))
            
            # Calcular overlap de palabras clave
            overlap = len(query_keywords.intersection(content_words))
            relevance_ratio = overlap / len(query_keywords)
            
            if relevance_ratio >= 0.3:  # Al menos 30% de palabras clave presentes
                relevant_results += 1
        
        # Si menos del 50% de resultados son relevantes, considerar que no hay información
        if relevant_results < len(search_results) * 0.5:
            return False, cls._generate_no_information_message(query, "low_relevance")
        
        return True, "Información encontrada en documentos administrativos"
    
    @classmethod
    def _generate_no_information_message(cls, query: str, reason: str) -> str:
        """Genera mensaje apropiado cuando no hay información disponible"""
        
        base_message = """🚫 **NO TENGO INFORMACIÓN DISPONIBLE**

❌ No dispongo de información específica sobre su consulta en mis documentos administrativos del MINEDU.

🔒 **RESTRICCIÓN DE ALCANCE:**
Este sistema está limitado exclusivamente a:
• 📋 Trámites y procedimientos administrativos del MINEDU
• 💰 Directivas de viáticos y gastos de viaje
• 📄 Normativas y reglamentos educativos
• 🏛️ Documentos oficiales del sector educación

💡 **SUGERENCIAS:**"""
        
        if reason == "no_results":
            specific_msg = """
• Verifique la ortografía de términos técnicos
• Use términos oficiales como aparecen en las directivas
• Consulte sobre procedimientos específicos del MINEDU"""
            
        elif reason == "no_keywords":
            specific_msg = """
• Sea más específico en su consulta
• Incluya términos administrativos relevantes
• Mencione números de directivas o procedimientos"""
            
        elif reason == "low_relevance":
            specific_msg = """
• Reformule su consulta con términos más específicos
• Consulte directamente sobre viáticos, expedientes o trámites
• Especifique el tipo de procedimiento administrativo"""
            
        else:
            specific_msg = """
• Reformule su consulta sobre temas administrativos
• Consulte la directiva de viáticos para referencias específicas
• Use terminología oficial del MINEDU"""
        
        footer = """
📞 **CONTACTO:** Para consultas fuera de este alcance, contacte directamente con:
• Mesa de Partes del MINEDU
• Oficina de Administración correspondiente
• Área especializada según el tema de consulta"""
        
        return base_message + specific_msg + footer
    
    @classmethod
    def validate_response_accuracy(cls, query: str, response: str, confidence_threshold: float = 0.7) -> Tuple[bool, str]:
        """
        Valida que una respuesta generada sea precisa y no contenga alucinaciones
        
        Args:
            query: Consulta original
            response: Respuesta generada
            confidence_threshold: Umbral mínimo de confianza
            
        Returns:
            (es_precisa, mensaje_validación)
        """
        response_lower = response.lower()
        
        # Detectar señales de alucinación
        hallucination_indicators = [
            "creo que", "posiblemente", "podría ser", "me parece", "supongo",
            "es probable", "quizás", "tal vez", "puede que", "imagino",
            "según mi experiencia", "en mi opinión", "generalmente"
        ]
        
        for indicator in hallucination_indicators:
            if indicator in response_lower:
                return False, f"Respuesta contiene indicadores de incertidumbre: '{indicator}'"
        
        # Verificar que la respuesta cite fuentes específicas
        source_indicators = [
            "directiva", "numeral", "artículo", "resolución", "decreto",
            "minedu", "según", "establece", "señala", "indica"
        ]
        
        has_sources = any(indicator in response_lower for indicator in source_indicators)
        if not has_sources and "no tengo información" not in response_lower:
            return False, "Respuesta no cita fuentes específicas de documentos administrativos"
        
        # Verificar longitud apropiada (no demasiado larga para evitar inventar detalles)
        if len(response) > 2000:
            return False, "Respuesta demasiado extensa, posible generación de contenido no verificado"
        
        return True, "Respuesta validada como precisa" 
"""
Agente Clasificador de Consultas
Determina el tipo de consulta y el agente especializado más apropiado
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Tipos de consulta identificados"""
    CALCULATION = "calculation"        # Montos, cálculos, viáticos
    LEGAL = "legal"                   # Interpretación jurídica, conflictos
    PROCEDURE = "procedure"           # Procedimientos administrativos
    HISTORICAL = "historical"         # Consultas temporales, cambios normativos
    GENERAL = "general"               # Consultas generales
    COMPLEX = "complex"               # Requiere múltiples agentes

@dataclass
class ClassificationResult:
    """Resultado de clasificación de consulta"""
    query_type: QueryType
    confidence: float
    target_agent: str
    reasoning: str
    detected_entities: Dict[str, Any]
    complexity_score: float
    requires_multiple_agents: bool

class QueryClassifierAgent:
    """
    Agente especializado en clasificar consultas y determinar routing
    Usa análisis semántico y patrones para clasificación inteligente
    """
    
    def __init__(self):
        self.classification_patterns = self._load_classification_patterns()
        self.entity_extractors = self._setup_entity_extractors()
        
        logger.info("🎯 QueryClassifierAgent inicializado")
    
    def _load_classification_patterns(self) -> Dict[QueryType, Dict[str, Any]]:
        """Cargar patrones de clasificación por tipo de consulta"""
        return {
            QueryType.CALCULATION: {
                "keywords": [
                    "monto", "máximo", "mínimo", "cuánto", "precio", "costo",
                    "viático", "s/", "soles", "dinero", "pago", "tarifa",
                    "cantidad", "suma", "total", "calcular", "valor"
                ],
                "patterns": [
                    r"(?:monto|precio|costo)\s+(?:máximo|mínimo)",
                    r"s/\s*\d+",
                    r"cuánto.*(?:cuesta|vale|es)",
                    r"viático.*(?:monto|cantidad)",
                    r"calcular.*(?:viático|gasto)"
                ],
                "indicators": [
                    "números", "moneda", "cálculo", "matemático"
                ]
            },
            
            QueryType.LEGAL: {
                "keywords": [
                    "legal", "jurídico", "normativa", "ley", "decreto", "directiva",
                    "artículo", "inciso", "numeral", "base legal", "fundamento",
                    "conflicto", "interpretación", "validez", "vigencia"
                ],
                "patterns": [
                    r"(?:artículo|art\.)\s*\d+",
                    r"(?:ley|decreto|directiva)\s+n[°º]?\s*\d+",
                    r"base\s+legal",
                    r"fundamento\s+(?:jurídico|legal)",
                    r"interpretación.*normativa"
                ],
                "indicators": [
                    "citas legales", "referencias normativas", "interpretación"
                ]
            },
            
            QueryType.PROCEDURE: {
                "keywords": [
                    "procedimiento", "proceso", "cómo", "pasos", "requisito",
                    "documento", "solicitar", "presentar", "trámite", "gestión",
                    "autorización", "aprobación", "permiso", "formulario"
                ],
                "patterns": [
                    r"cómo\s+(?:solicitar|presentar|tramitar)",
                    r"(?:qué|cuáles)\s+(?:documentos|requisitos)",
                    r"procedimiento\s+para",
                    r"pasos\s+a\s+seguir",
                    r"proceso\s+de\s+(?:solicitud|trámite)"
                ],
                "indicators": [
                    "instrucciones", "secuencial", "administrativo"
                ]
            },
            
            QueryType.HISTORICAL: {
                "keywords": [
                    "antes", "anterior", "cambio", "modificación", "evolución",
                    "histórico", "temporal", "año", "fecha", "vigente", "derogado",
                    "actualización", "versión", "anterior", "previo"
                ],
                "patterns": [
                    r"(?:año|en)\s+\d{4}",
                    r"antes\s+de",
                    r"cambio.*normativa",
                    r"modificación.*(?:directiva|ley)",
                    r"evolución.*(?:normativa|regulación)"
                ],
                "indicators": [
                    "temporal", "comparativo", "cronológico"
                ]
            },
            
            QueryType.COMPLEX: {
                "keywords": [
                    "además", "también", "asimismo", "por otro lado", "y",
                    "comparar", "diferencia", "relación", "entre", "versus"
                ],
                "patterns": [
                    r"(?:monto|procedimiento).*y.*(?:requisito|documento)",
                    r"comparar.*entre",
                    r"diferencia.*entre",
                    r"tanto.*como",
                    r"además.*también"
                ],
                "indicators": [
                    "múltiples aspectos", "comparativo", "complejo"
                ]
            }
        }
    
    def _setup_entity_extractors(self) -> Dict[str, Any]:
        """Configurar extractores de entidades"""
        return {
            "amounts": {
                "pattern": r"s/\s*(\d+(?:\.\d+)?)",
                "type": "monetary"
            },
            "years": {
                "pattern": r"(?:año\s+)?(\d{4})",
                "type": "temporal"
            },
            "legal_refs": {
                "pattern": r"(?:artículo|art\.)\s*(\d+(?:\.\d+)?)",
                "type": "legal_reference"
            },
            "norms": {
                "pattern": r"(?:ley|decreto|directiva)\s+n[°º]?\s*(\d+[-\d]*)",
                "type": "normative_reference"
            },
            "procedures": {
                "pattern": r"(?:solicitar|presentar|tramitar)\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+)",
                "type": "procedural"
            }
        }
    
    def classify_query(self, query: str) -> ClassificationResult:
        """
        Clasificar consulta y determinar agente apropiado
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Resultado de clasificación con agente recomendado
        """
        try:
            query_lower = query.lower()
            
            # 1. Extraer entidades
            entities = self._extract_entities(query)
            
            # 2. Calcular scores por tipo
            type_scores = self._calculate_type_scores(query_lower)
            
            # 3. Determinar tipo principal
            primary_type = max(type_scores.items(), key=lambda x: x[1])
            query_type, confidence = primary_type
            
            # 4. Determinar complejidad
            complexity_score = self._calculate_complexity(query_lower, entities)
            
            # 5. Verificar si requiere múltiples agentes
            requires_multiple = self._requires_multiple_agents(type_scores, complexity_score)
            
            # 6. Determinar agente objetivo
            target_agent = self._determine_target_agent(query_type, requires_multiple)
            
            # 7. Generar razonamiento
            reasoning = self._generate_reasoning(query_type, confidence, entities, complexity_score)
            
            result = ClassificationResult(
                query_type=query_type,
                confidence=confidence,
                target_agent=target_agent,
                reasoning=reasoning,
                detected_entities=entities,
                complexity_score=complexity_score,
                requires_multiple_agents=requires_multiple
            )
            
            logger.info(f"🎯 Consulta clasificada: {query_type.value} (conf: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error clasificando consulta: {e}")
            return self._create_fallback_classification(query)
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extraer entidades de la consulta"""
        entities = {}
        
        for entity_type, extractor in self.entity_extractors.items():
            pattern = extractor["pattern"]
            matches = re.findall(pattern, query, re.IGNORECASE)
            
            if matches:
                entities[entity_type] = {
                    "values": matches,
                    "type": extractor["type"],
                    "count": len(matches)
                }
        
        return entities
    
    def _calculate_type_scores(self, query_lower: str) -> Dict[QueryType, float]:
        """Calcular scores para cada tipo de consulta"""
        scores = {}
        
        for query_type, patterns_data in self.classification_patterns.items():
            score = 0.0
            
            # Score por keywords
            keywords_found = 0
            for keyword in patterns_data["keywords"]:
                if keyword in query_lower:
                    keywords_found += 1
            
            keyword_score = keywords_found / len(patterns_data["keywords"])
            
            # Score por patrones regex
            patterns_found = 0
            for pattern in patterns_data["patterns"]:
                if re.search(pattern, query_lower):
                    patterns_found += 1
            
            pattern_score = patterns_found / len(patterns_data["patterns"]) if patterns_data["patterns"] else 0
            
            # Score combinado (70% keywords, 30% patterns)
            score = (keyword_score * 0.7) + (pattern_score * 0.3)
            scores[query_type] = score
        
        return scores
    
    def _calculate_complexity(self, query_lower: str, entities: Dict[str, Any]) -> float:
        """Calcular score de complejidad de la consulta"""
        complexity_factors = []
        
        # Factor 1: Longitud de la consulta
        length_factor = min(len(query_lower.split()) / 20, 1.0)
        complexity_factors.append(length_factor)
        
        # Factor 2: Número de entidades detectadas
        entity_count = sum(len(entity_data["values"]) for entity_data in entities.values())
        entity_factor = min(entity_count / 5, 1.0)
        complexity_factors.append(entity_factor)
        
        # Factor 3: Indicadores de complejidad sintáctica
        complexity_indicators = ["y", "además", "también", "comparar", "diferencia", "entre"]
        syntax_complexity = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        syntax_factor = min(syntax_complexity / 3, 1.0)
        complexity_factors.append(syntax_factor)
        
        # Factor 4: Múltiples tipos de consulta detectados
        type_scores = self._calculate_type_scores(query_lower)
        high_scores = [score for score in type_scores.values() if score > 0.3]
        multi_type_factor = min(len(high_scores) / 3, 1.0)
        complexity_factors.append(multi_type_factor)
        
        # Score final de complejidad
        return sum(complexity_factors) / len(complexity_factors)
    
    def _requires_multiple_agents(self, type_scores: Dict[QueryType, float], complexity_score: float) -> bool:
        """Determinar si la consulta requiere múltiples agentes"""
        
        # Criterio 1: Múltiples tipos con score alto
        high_scores = [score for score in type_scores.values() if score > 0.4]
        
        # Criterio 2: Complejidad alta
        high_complexity = complexity_score > 0.7
        
        # Criterio 3: Tipo explícitamente complejo
        complex_type = type_scores.get(QueryType.COMPLEX, 0) > 0.5
        
        return len(high_scores) >= 2 or high_complexity or complex_type
    
    def _determine_target_agent(self, query_type: QueryType, requires_multiple: bool) -> str:
        """Determinar agente objetivo basado en clasificación"""
        
        if requires_multiple:
            return "multi_agent_orchestrator"
        
        agent_mapping = {
            QueryType.CALCULATION: "calculation_agent",
            QueryType.LEGAL: "legal_expert_agent", 
            QueryType.PROCEDURE: "procedure_agent",
            QueryType.HISTORICAL: "historical_agent",
            QueryType.GENERAL: "general_rag_agent",
            QueryType.COMPLEX: "multi_agent_orchestrator"
        }
        
        return agent_mapping.get(query_type, "general_rag_agent")
    
    def _generate_reasoning(self, 
                          query_type: QueryType, 
                          confidence: float, 
                          entities: Dict[str, Any],
                          complexity_score: float) -> str:
        """Generar explicación del razonamiento de clasificación"""
        
        reasoning_parts = [
            f"Tipo identificado: {query_type.value}",
            f"Confianza: {confidence:.2f}",
            f"Complejidad: {complexity_score:.2f}"
        ]
        
        if entities:
            entity_summary = []
            for entity_type, entity_data in entities.items():
                entity_summary.append(f"{entity_type}: {len(entity_data['values'])} encontradas")
            reasoning_parts.append(f"Entidades: {', '.join(entity_summary)}")
        
        # Razonamiento específico por tipo
        type_reasoning = {
            QueryType.CALCULATION: "Consulta sobre montos, cálculos o valores monetarios",
            QueryType.LEGAL: "Consulta jurídica o interpretación normativa",
            QueryType.PROCEDURE: "Consulta sobre procedimientos administrativos",
            QueryType.HISTORICAL: "Consulta temporal o evolución normativa",
            QueryType.GENERAL: "Consulta general que no requiere especialización",
            QueryType.COMPLEX: "Consulta compleja que requiere múltiples perspectivas"
        }
        
        reasoning_parts.append(type_reasoning.get(query_type, "Clasificación general"))
        
        return " | ".join(reasoning_parts)
    
    def _create_fallback_classification(self, query: str) -> ClassificationResult:
        """Crear clasificación de fallback en caso de error"""
        return ClassificationResult(
            query_type=QueryType.GENERAL,
            confidence=0.5,
            target_agent="general_rag_agent",
            reasoning="Clasificación de fallback por error en análisis",
            detected_entities={},
            complexity_score=0.5,
            requires_multiple_agents=False
        )
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del clasificador"""
        return {
            "query_types_supported": len(QueryType),
            "classification_patterns": len(self.classification_patterns),
            "entity_extractors": len(self.entity_extractors),
            "agent_mappings": {
                "calculation_agent": "Cálculos y montos",
                "legal_expert_agent": "Interpretación jurídica",
                "procedure_agent": "Procedimientos administrativos", 
                "historical_agent": "Consultas temporales",
                "general_rag_agent": "Consultas generales",
                "multi_agent_orchestrator": "Consultas complejas"
            }
        }

# Instancia global
global_query_classifier = QueryClassifierAgent()
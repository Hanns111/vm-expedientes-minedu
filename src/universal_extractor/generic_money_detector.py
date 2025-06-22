#!/usr/bin/env python3
"""
Generic Money Detector - Identificación Universal de Montos y Numerales
======================================================================

Detector universal que aprende automáticamente patrones de montos, numerales
y referencias legales de cualquier norma sin configuración manual.
"""

import re
import logging
import time
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MoneyPattern:
    """Patrón de dinero aprendido"""
    pattern: str
    currency: str
    confidence: float
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    contexts: List[str] = field(default_factory=list)
    
@dataclass
class NumeralPattern:
    """Patrón de numeral legal aprendido"""
    pattern: str
    type: str  # 'numeral', 'article', 'section'
    confidence: float
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    contexts: List[str] = field(default_factory=list)

@dataclass
class ExtractedEntity:
    """Entidad extraída (monto o numeral)"""
    value: str
    type: str  # 'amount', 'numeral', 'article'
    currency: Optional[str] = None
    context: str = ""
    confidence: float = 0.0
    position: Tuple[int, int] = (0, 0)  # (start, end) en el texto
    normalized_value: Optional[str] = None

class GenericMoneyDetector:
    """
    Detector universal de montos y numerales que se adapta automáticamente
    a cualquier tipo de norma legal.
    
    Características:
    - Aprendizaje automático de patrones monetarios
    - Detección adaptativa de numerales legales (8.4.17, Art. 23, etc.)
    - Normalización automática de valores
    - Contexto inteligente para mejor precisión
    - Soporte multi-moneda dinámico
    """
    
    def __init__(self, learning_enabled: bool = True):
        self.learning_enabled = learning_enabled
        
        # Patrones base universales
        self.base_money_patterns = self._initialize_base_money_patterns()
        self.base_numeral_patterns = self._initialize_base_numeral_patterns()
        
        # Patrones aprendidos dinámicamente
        self.learned_money_patterns: List[MoneyPattern] = []
        self.learned_numeral_patterns: List[NumeralPattern] = []
        
        # Estadísticas de rendimiento
        self.performance_stats = {
            'total_extractions': 0,
            'money_entities_found': 0,
            'numeral_entities_found': 0,
            'patterns_learned': 0,
            'accuracy_by_type': {},
            'processing_time_avg': 0.0
        }
        
        # Cache para optimización
        self.pattern_cache = {}
        self.normalization_cache = {}
        
        logger.info("GenericMoneyDetector initialized with adaptive learning")
    
    def extract_entities_universal(self, text: str, document_type: str = "legal_norm") -> Dict[str, Any]:
        """
        Extraer montos y numerales de forma universal y adaptativa.
        
        Args:
            text: Texto a analizar
            document_type: Tipo de documento para contexto
            
        Returns:
            Diccionario con entidades extraídas y metadatos
        """
        start_time = time.time()
        
        # 1. Preprocesar texto
        processed_text = self._preprocess_text(text)
        
        # 2. Extraer entidades con todos los métodos
        money_entities = self._extract_money_entities(processed_text, document_type)
        numeral_entities = self._extract_numeral_entities(processed_text, document_type)
        
        # 3. Aprender nuevos patrones si está habilitado
        if self.learning_enabled:
            self._learn_new_patterns(processed_text, money_entities + numeral_entities, document_type)
        
        # 4. Normalizar y validar entidades
        normalized_money = self._normalize_money_entities(money_entities)
        normalized_numerals = self._normalize_numeral_entities(numeral_entities)
        
        # 5. Calcular confianza y ranking
        ranked_entities = self._rank_entities_by_confidence(normalized_money + normalized_numerals)
        
        # 6. Generar resumen y metadatos
        extraction_time = time.time() - start_time
        
        result = {
            'money_entities': normalized_money,
            'numeral_entities': normalized_numerals,
            'all_entities': ranked_entities,
            'summary': {
                'total_money_found': len(normalized_money),
                'total_numerals_found': len(normalized_numerals),
                'unique_currencies': self._get_unique_currencies(normalized_money),
                'numeral_types': self._get_numeral_types(normalized_numerals),
                'highest_confidence': max([e.confidence for e in ranked_entities], default=0.0)
            },
            'metadata': {
                'extraction_time': extraction_time,
                'document_type': document_type,
                'patterns_used': len(self.learned_money_patterns) + len(self.learned_numeral_patterns),
                'learning_enabled': self.learning_enabled,
                'text_length': len(text)
            }
        }
        
        # 7. Actualizar estadísticas
        self._update_performance_stats(result, extraction_time)
        
        return result
    
    def _initialize_base_money_patterns(self) -> List[MoneyPattern]:
        """Inicializar patrones base de dinero universales."""
        
        base_patterns = [
            # Soles peruanos
            MoneyPattern(r'S/\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'PEN', 0.9),
            MoneyPattern(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*soles?', 'PEN', 0.85),
            MoneyPattern(r'nuevos\s+soles\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'PEN', 0.8),
            
            # Dólares americanos
            MoneyPattern(r'USD?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD', 0.9),
            MoneyPattern(r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'USD', 0.85),
            MoneyPattern(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*d[oó]lares?', 'USD', 0.8),
            
            # Euros
            MoneyPattern(r'EUR?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR', 0.9),
            MoneyPattern(r'€\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'EUR', 0.85),
            MoneyPattern(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*euros?', 'EUR', 0.8),
            
            # Patrones genéricos de montos
            MoneyPattern(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)(?=\s*(?:por|diario|mensual|anual))', 'UNKNOWN', 0.7),
            MoneyPattern(r'monto.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'UNKNOWN', 0.6),
            MoneyPattern(r'valor.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'UNKNOWN', 0.6),
        ]
        
        return base_patterns
    
    def _initialize_base_numeral_patterns(self) -> List[NumeralPattern]:
        """Inicializar patrones base de numerales legales universales."""
        
        base_patterns = [
            # Numerales jerárquicos (8.4.17, 10.2.3.1)
            NumeralPattern(r'\b(\d+(?:\.\d+){1,4})\b', 'numeral', 0.8),
            NumeralPattern(r'numeral\s*(\d+(?:\.\d+)*)', 'numeral', 0.9),
            NumeralPattern(r'literal\s*([a-z])\)', 'literal', 0.85),
            
            # Artículos
            NumeralPattern(r'art[íi]culos?\s*(\d+)', 'article', 0.9),
            NumeralPattern(r'art\.?\s*(\d+)', 'article', 0.85),
            
            # Capítulos y secciones
            NumeralPattern(r'cap[íi]tulos?\s*([IVX]+|\d+)', 'chapter', 0.8),
            NumeralPattern(r'secci[óo]n\s*(\d+)', 'section', 0.8),
            
            # Incisos y apartados
            NumeralPattern(r'incisos?\s*([a-z]|\d+)', 'subsection', 0.7),
            NumeralPattern(r'apartados?\s*(\d+)', 'subsection', 0.7),
            
            # Anexos y apéndices
            NumeralPattern(r'anexos?\s*([A-Z]|\d+)', 'annex', 0.75),
            NumeralPattern(r'ap[ée]ndices?\s*([A-Z]|\d+)', 'appendix', 0.75),
        ]
        
        return base_patterns
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesar texto para mejor extracción."""
        
        # Normalizar espacios en blanco
        processed = re.sub(r'\s+', ' ', text)
        
        # Normalizar caracteres especiales comunes
        processed = processed.replace('°', '')  # Grados
        processed = processed.replace('n°', 'N ')  # Número
        processed = processed.replace('N°', 'N ')
        
        # Normalizar guiones y separadores
        processed = processed.replace('–', '-')
        processed = processed.replace('—', '-')
        
        return processed.strip()
    
    def _extract_money_entities(self, text: str, document_type: str) -> List[ExtractedEntity]:
        """Extraer entidades monetarias usando todos los patrones disponibles."""
        
        entities = []
        
        # Combinar patrones base y aprendidos
        all_patterns = self.base_money_patterns + self.learned_money_patterns
        
        for pattern_obj in all_patterns:
            try:
                matches = re.finditer(pattern_obj.pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Extraer contexto alrededor del match
                    start, end = match.span()
                    context_start = max(0, start - 50)
                    context_end = min(len(text), end + 50)
                    context = text[context_start:context_end]
                    
                    # Crear entidad
                    entity = ExtractedEntity(
                        value=match.group(1) if match.groups() else match.group(0),
                        type='amount',
                        currency=pattern_obj.currency,
                        context=context,
                        confidence=pattern_obj.confidence,
                        position=(start, end),
                        normalized_value=None  # Se normalizará después
                    )
                    
                    entities.append(entity)
                    
                    # Actualizar uso del patrón
                    pattern_obj.usage_count += 1
                    pattern_obj.last_used = datetime.now()
                    
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern_obj.pattern} - {e}")
                continue
        
        return entities
    
    def _extract_numeral_entities(self, text: str, document_type: str) -> List[ExtractedEntity]:
        """Extraer entidades de numerales legales."""
        
        entities = []
        
        # Combinar patrones base y aprendidos
        all_patterns = self.base_numeral_patterns + self.learned_numeral_patterns
        
        for pattern_obj in all_patterns:
            try:
                matches = re.finditer(pattern_obj.pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Extraer contexto
                    start, end = match.span()
                    context_start = max(0, start - 50)
                    context_end = min(len(text), end + 50)
                    context = text[context_start:context_end]
                    
                    # Validar que es realmente un numeral legal (no un número cualquiera)
                    if self._is_valid_legal_numeral(match.group(0), context):
                        entity = ExtractedEntity(
                            value=match.group(1) if match.groups() else match.group(0),
                            type='numeral',
                            context=context,
                            confidence=pattern_obj.confidence,
                            position=(start, end),
                            normalized_value=None
                        )
                        
                        entities.append(entity)
                        
                        # Actualizar uso del patrón
                        pattern_obj.usage_count += 1
                        pattern_obj.last_used = datetime.now()
                        
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern_obj.pattern} - {e}")
                continue
        
        return entities
    
    def _is_valid_legal_numeral(self, numeral: str, context: str) -> bool:
        """Validar si un numeral es realmente una referencia legal."""
        
        # Palabras que indican contexto legal
        legal_indicators = [
            'artículo', 'numeral', 'inciso', 'literal', 'capítulo', 
            'sección', 'apartado', 'anexo', 'disposición', 'norma',
            'establecido', 'señalado', 'indicado', 'referido'
        ]
        
        context_lower = context.lower()
        
        # Verificar presencia de indicadores legales
        has_legal_context = any(indicator in context_lower for indicator in legal_indicators)
        
        # Verificar formato típico de numerales legales
        has_legal_format = bool(re.match(r'\d+(?:\.\d+)+', numeral))
        
        # Evitar números que son claramente fechas, teléfonos, etc.
        is_date = bool(re.match(r'\d{1,2}/\d{1,2}/\d{4}', numeral))
        is_phone = len(numeral.replace('.', '').replace('-', '')) > 7
        
        return (has_legal_context or has_legal_format) and not (is_date or is_phone)
    
    def _learn_new_patterns(self, text: str, entities: List[ExtractedEntity], document_type: str):
        """Aprender nuevos patrones basados en el texto y entidades encontradas."""
        
        if not entities:
            return
        
        # Aprender patrones de dinero
        self._learn_money_patterns(text, [e for e in entities if e.type == 'amount'], document_type)
        
        # Aprender patrones de numerales
        self._learn_numeral_patterns(text, [e for e in entities if e.type == 'numeral'], document_type)
    
    def _learn_money_patterns(self, text: str, money_entities: List[ExtractedEntity], document_type: str):
        """Aprender nuevos patrones de dinero del contexto."""
        
        for entity in money_entities:
            context = entity.context
            value = entity.value
            
            # Extraer palabras antes y después del monto
            before_words = re.findall(r'\w+', context[:context.find(value)])[-3:]  # Últimas 3 palabras
            after_words = re.findall(r'\w+', context[context.find(value) + len(value):])[:3]  # Primeras 3 palabras
            
            # Generar patrones potenciales
            potential_patterns = []
            
            if before_words:
                # Patrón: "palabra + valor"
                before_pattern = f"(?:{'|'.join(before_words)})\\s+({re.escape(value)})"
                potential_patterns.append((before_pattern, entity.currency or 'UNKNOWN', 0.6))
            
            if after_words:
                # Patrón: "valor + palabra"  
                after_pattern = f"({re.escape(value)})\\s+(?:{'|'.join(after_words)})"
                potential_patterns.append((after_pattern, entity.currency or 'UNKNOWN', 0.6))
            
            # Evaluar y agregar patrones prometedores
            for pattern, currency, base_confidence in potential_patterns:
                if self._evaluate_pattern_potential(pattern, text):
                    # Verificar que no existe ya
                    if not any(p.pattern == pattern for p in self.learned_money_patterns):
                        new_pattern = MoneyPattern(
                            pattern=pattern,
                            currency=currency,
                            confidence=base_confidence,
                            contexts=[context[:100]]  # Primeros 100 chars del contexto
                        )
                        self.learned_money_patterns.append(new_pattern)
                        self.performance_stats['patterns_learned'] += 1
                        
                        logger.debug(f"Learned new money pattern: {pattern}")
    
    def _learn_numeral_patterns(self, text: str, numeral_entities: List[ExtractedEntity], document_type: str):
        """Aprender nuevos patrones de numerales del contexto."""
        
        for entity in numeral_entities:
            context = entity.context
            value = entity.value
            
            # Buscar patrones de introducción de numerales
            intro_patterns = [
                r'(?:de\s+conformidad\s+con\s+(?:el\s+)?(?:numeral|artículo))\s*(\d+(?:\.\d+)*)',
                r'(?:según\s+(?:lo\s+)?(?:establecido|señalado)\s+en\s+(?:el\s+)?(?:numeral|artículo))\s*(\d+(?:\.\d+)*)',
                r'(?:conforme\s+a\s+(?:lo\s+)?(?:dispuesto|indicado)\s+en)\s*(\d+(?:\.\d+)*)'
            ]
            
            for pattern in intro_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    # Este es un patrón prometedor
                    if not any(p.pattern == pattern for p in self.learned_numeral_patterns):
                        new_pattern = NumeralPattern(
                            pattern=pattern,
                            type='reference_numeral',
                            confidence=0.8,
                            contexts=[context[:100]]
                        )
                        self.learned_numeral_patterns.append(new_pattern)
                        self.performance_stats['patterns_learned'] += 1
                        
                        logger.debug(f"Learned new numeral pattern: {pattern}")
    
    def _evaluate_pattern_potential(self, pattern: str, text: str) -> bool:
        """Evaluar si un patrón tiene potencial para ser útil."""
        
        try:
            # Probar el patrón en el texto
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            # Criterios de evaluación
            match_count = len(matches)
            
            # Debe tener al menos 1 match pero no demasiados (evitar over-matching)
            if match_count < 1 or match_count > 20:
                return False
            
            # Verificar que no sea demasiado genérico
            if len(pattern) < 10:  # Patrones muy cortos tienden a ser genéricos
                return False
            
            return True
            
        except re.error:
            return False
    
    def _normalize_money_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Normalizar valores monetarios."""
        
        normalized = []
        
        for entity in entities:
            normalized_entity = entity
            
            # Normalizar valor numérico
            clean_value = entity.value.replace(',', '').replace(' ', '')
            
            try:
                # Convertir a float y formatear consistentemente
                numeric_value = float(clean_value)
                normalized_entity.normalized_value = f"{numeric_value:.2f}"
                
                # Ajustar confianza basada en contexto
                confidence_adjustment = self._calculate_context_confidence_money(entity)
                normalized_entity.confidence = min(1.0, entity.confidence + confidence_adjustment)
                
            except ValueError:
                # Si no se puede convertir, mantener valor original
                normalized_entity.normalized_value = entity.value
                normalized_entity.confidence *= 0.5  # Reducir confianza
            
            normalized.append(normalized_entity)
        
        # Eliminar duplicados cercanos (mismo valor, posiciones cercanas)
        return self._remove_duplicate_money_entities(normalized)
    
    def _normalize_numeral_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Normalizar numerales legales."""
        
        normalized = []
        
        for entity in entities:
            normalized_entity = entity
            
            # Normalizar formato del numeral
            normalized_entity.normalized_value = self._normalize_numeral_format(entity.value)
            
            # Ajustar confianza basada en contexto
            confidence_adjustment = self._calculate_context_confidence_numeral(entity)
            normalized_entity.confidence = min(1.0, entity.confidence + confidence_adjustment)
            
            normalized.append(normalized_entity)
        
        # Eliminar duplicados
        return self._remove_duplicate_numeral_entities(normalized)
    
    def _normalize_numeral_format(self, numeral: str) -> str:
        """Normalizar formato de numerales legales."""
        
        # Remover espacios extra
        clean = numeral.strip()
        
        # Normalizar puntos (asegurar que no termine en punto)
        if clean.endswith('.'):
            clean = clean[:-1]
        
        return clean
    
    def _calculate_context_confidence_money(self, entity: ExtractedEntity) -> float:
        """Calcular ajuste de confianza basado en contexto para montos."""
        
        context_lower = entity.context.lower()
        
        # Palabras que aumentan confianza
        positive_indicators = [
            'viático', 'monto', 'límite', 'máximo', 'presupuesto', 
            'asignación', 'costo', 'valor', 'importe', 'suma'
        ]
        
        # Palabras que reducen confianza
        negative_indicators = [
            'página', 'línea', 'código', 'número', 'telefono',
            'fecha', 'hora', 'año', 'mes'
        ]
        
        positive_count = sum(1 for word in positive_indicators if word in context_lower)
        negative_count = sum(1 for word in negative_indicators if word in context_lower)
        
        return (positive_count * 0.1) - (negative_count * 0.2)
    
    def _calculate_context_confidence_numeral(self, entity: ExtractedEntity) -> float:
        """Calcular ajuste de confianza basado en contexto para numerales."""
        
        context_lower = entity.context.lower()
        
        # Palabras que aumentan confianza
        positive_indicators = [
            'artículo', 'numeral', 'inciso', 'literal', 'capítulo',
            'disposición', 'establecido', 'señalado', 'conforme'
        ]
        
        # Palabras que reducen confianza  
        negative_indicators = [
            'fecha', 'hora', 'teléfono', 'código postal', 'página'
        ]
        
        positive_count = sum(1 for word in positive_indicators if word in context_lower)
        negative_count = sum(1 for word in negative_indicators if word in context_lower)
        
        return (positive_count * 0.15) - (negative_count * 0.25)
    
    def _remove_duplicate_money_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remover entidades monetarias duplicadas."""
        
        unique_entities = []
        seen_values = set()
        
        # Ordenar por confianza descendente
        sorted_entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
        
        for entity in sorted_entities:
            # Crear clave única basada en valor normalizado y posición aproximada
            key = f"{entity.normalized_value}_{entity.position[0]//50}"  # Agrupar por bloques de 50 chars
            
            if key not in seen_values:
                seen_values.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _remove_duplicate_numeral_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remover entidades de numerales duplicadas."""
        
        unique_entities = []
        seen_values = set()
        
        # Ordenar por confianza descendente
        sorted_entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
        
        for entity in sorted_entities:
            # Crear clave única
            key = f"{entity.normalized_value}_{entity.position[0]//30}"
            
            if key not in seen_values:
                seen_values.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _rank_entities_by_confidence(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Ordenar entidades por confianza descendente."""
        
        return sorted(entities, key=lambda e: e.confidence, reverse=True)
    
    def _get_unique_currencies(self, money_entities: List[ExtractedEntity]) -> List[str]:
        """Obtener lista de monedas únicas encontradas."""
        
        currencies = set()
        for entity in money_entities:
            if entity.currency and entity.currency != 'UNKNOWN':
                currencies.add(entity.currency)
        
        return list(currencies)
    
    def _get_numeral_types(self, numeral_entities: List[ExtractedEntity]) -> List[str]:
        """Obtener tipos de numerales encontrados."""
        
        # Analizar patrones de numerales para determinar tipos
        types = set()
        
        for entity in numeral_entities:
            if '.' in entity.value:
                if entity.value.count('.') == 1:
                    types.add('two_level')  # 8.4
                elif entity.value.count('.') == 2:
                    types.add('three_level')  # 8.4.17
                else:
                    types.add('multi_level')  # 8.4.17.2.1
            else:
                types.add('single_level')  # 8
        
        return list(types)
    
    def _update_performance_stats(self, result: Dict[str, Any], extraction_time: float):
        """Actualizar estadísticas de rendimiento."""
        
        self.performance_stats['total_extractions'] += 1
        self.performance_stats['money_entities_found'] += result['summary']['total_money_found']
        self.performance_stats['numeral_entities_found'] += result['summary']['total_numerals_found']
        
        # Actualizar tiempo promedio de procesamiento
        total_time = self.performance_stats['processing_time_avg'] * (self.performance_stats['total_extractions'] - 1)
        self.performance_stats['processing_time_avg'] = (total_time + extraction_time) / self.performance_stats['total_extractions']
    
    def get_learned_patterns_summary(self) -> Dict[str, Any]:
        """Obtener resumen de patrones aprendidos."""
        
        return {
            'money_patterns': {
                'total': len(self.learned_money_patterns),
                'by_currency': self._group_patterns_by_currency(),
                'most_used': sorted(self.learned_money_patterns, key=lambda p: p.usage_count, reverse=True)[:5]
            },
            'numeral_patterns': {
                'total': len(self.learned_numeral_patterns),
                'by_type': self._group_numeral_patterns_by_type(),
                'most_used': sorted(self.learned_numeral_patterns, key=lambda p: p.usage_count, reverse=True)[:5]
            },
            'performance': self.performance_stats
        }
    
    def _group_patterns_by_currency(self) -> Dict[str, int]:
        """Agrupar patrones de dinero por moneda."""
        
        currency_counts = {}
        for pattern in self.learned_money_patterns:
            currency = pattern.currency
            currency_counts[currency] = currency_counts.get(currency, 0) + 1
        
        return currency_counts
    
    def _group_numeral_patterns_by_type(self) -> Dict[str, int]:
        """Agrupar patrones de numerales por tipo."""
        
        type_counts = {}
        for pattern in self.learned_numeral_patterns:
            pattern_type = pattern.type
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
        
        return type_counts
    
    def save_learned_patterns(self, filepath: str):
        """Guardar patrones aprendidos en archivo."""
        
        data = {
            'money_patterns': [
                {
                    'pattern': p.pattern,
                    'currency': p.currency,
                    'confidence': p.confidence,
                    'usage_count': p.usage_count,
                    'last_used': p.last_used.isoformat(),
                    'contexts': p.contexts
                }
                for p in self.learned_money_patterns
            ],
            'numeral_patterns': [
                {
                    'pattern': p.pattern,
                    'type': p.type,
                    'confidence': p.confidence,
                    'usage_count': p.usage_count,
                    'last_used': p.last_used.isoformat(),
                    'contexts': p.contexts
                }
                for p in self.learned_numeral_patterns
            ],
            'performance_stats': self.performance_stats,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Learned patterns saved to {filepath}")
    
    def load_learned_patterns(self, filepath: str):
        """Cargar patrones aprendidos desde archivo."""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar patrones de dinero
            self.learned_money_patterns = []
            for p_data in data.get('money_patterns', []):
                pattern = MoneyPattern(
                    pattern=p_data['pattern'],
                    currency=p_data['currency'],
                    confidence=p_data['confidence'],
                    usage_count=p_data['usage_count'],
                    last_used=datetime.fromisoformat(p_data['last_used']),
                    contexts=p_data['contexts']
                )
                self.learned_money_patterns.append(pattern)
            
            # Cargar patrones de numerales
            self.learned_numeral_patterns = []
            for p_data in data.get('numeral_patterns', []):
                pattern = NumeralPattern(
                    pattern=p_data['pattern'],
                    type=p_data['type'],
                    confidence=p_data['confidence'],
                    usage_count=p_data['usage_count'],
                    last_used=datetime.fromisoformat(p_data['last_used']),
                    contexts=p_data['contexts']
                )
                self.learned_numeral_patterns.append(pattern)
            
            # Cargar estadísticas
            self.performance_stats.update(data.get('performance_stats', {}))
            
            logger.info(f"Learned patterns loaded from {filepath}")
            logger.info(f"Loaded {len(self.learned_money_patterns)} money patterns and {len(self.learned_numeral_patterns)} numeral patterns")
            
        except Exception as e:
            logger.error(f"Failed to load learned patterns: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Obtener reporte completo de rendimiento."""
        
        total_patterns = len(self.base_money_patterns) + len(self.base_numeral_patterns) + \
                        len(self.learned_money_patterns) + len(self.learned_numeral_patterns)
        
        learning_rate = 0.0
        if self.performance_stats['total_extractions'] > 0:
            learning_rate = self.performance_stats['patterns_learned'] / self.performance_stats['total_extractions']
        
        return {
            'extraction_stats': self.performance_stats,
            'pattern_stats': {
                'total_patterns': total_patterns,
                'base_patterns': len(self.base_money_patterns) + len(self.base_numeral_patterns),
                'learned_patterns': len(self.learned_money_patterns) + len(self.learned_numeral_patterns),
                'learning_rate': learning_rate
            },
            'efficiency_metrics': {
                'avg_processing_time': self.performance_stats['processing_time_avg'],
                'entities_per_extraction': (
                    self.performance_stats['money_entities_found'] + 
                    self.performance_stats['numeral_entities_found']
                ) / max(1, self.performance_stats['total_extractions'])
            }
        }
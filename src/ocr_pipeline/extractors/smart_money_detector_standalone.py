#!/usr/bin/env python3
"""
Detector Inteligente de Montos Monetarios - Versión Standalone
==============================================================

Sistema adaptativo que detecta CUALQUIER patrón monetario sin dependencias problemáticas.
Versión independiente que evita conflictos de numpy/spacy.
"""

import re
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class SmartMoneyDetectorStandalone:
    """Detector inteligente standalone sin dependencias problemáticas"""
    
    def __init__(self, learning_mode: bool = True):
        self.learning_mode = learning_mode
        
        # Patrones base optimizados
        self.base_patterns = [
            # Patrones con símbolos de moneda específicos
            r'S/\.?\s*(\d{1,4}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',  # S/ 1,234.56
            r'(?:USD|US\$|\$)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',  # USD 1,234.56
            r'(?:EUR|€)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',        # EUR 1,234.56
            r'(?:GBP|£)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',        # GBP 1,234.56
            r'(?:PEN|SOL)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',      # PEN 1,234.56
            
            # Patrones contextuales
            r'(?:viáticos?|gastos?|monto|valor|importe|suma|cantidad)\s+(?:de\s+)?(?:S/\.?\s*)?(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            r'(?:hasta|máximo|límite|tope)\s+(?:de\s+)?(?:S/\.?\s*)?(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            r'(?:precio|costo|tarifa|cuota|pago)\s+(?:de\s+)?(?:S/\.?\s*)?(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            
            # Patrones numéricos con contexto
            r'\b(\d{1,3}(?:[,\.]\d{3})+(?:[,\.]\d{2})?)\b(?=\s*(?:soles?|dólares?|euros?))',
            r'\b(\d{3,6}(?:[,\.]\d{2})?)\b(?=\s*(?:por|para|de)\s+(?:participante|evento|día))',
        ]
        
        # Contextos monetarios
        self.monetary_contexts = [
            'viáticos', 'gastos', 'monto', 'valor', 'importe', 'suma', 'cantidad',
            'precio', 'costo', 'tarifa', 'cuota', 'pago', 'remuneración',
            'salario', 'sueldo', 'honorarios', 'dieta', 'subsidio',
            'máximo', 'mínimo', 'límite', 'tope', 'hasta', 'por', 'para'
        ]
        
        # Patrones aprendidos
        self.learned_patterns = set()
        
        # Estadísticas
        self.extraction_stats = defaultdict(int)
        self.confidence_history = []
        
        # Cargar datos previos
        self._load_learned_patterns()
    
    def extract_all_amounts(self, text: str, context_window: int = 100) -> List[Dict[str, Any]]:
        """
        Extrae todos los montos del texto usando patrones optimizados
        
        Args:
            text: Texto a analizar
            context_window: Ventana de contexto
            
        Returns:
            Lista de montos encontrados con metadata
        """
        amounts = []
        all_patterns = list(self.base_patterns) + list(self.learned_patterns)
        
        for pattern_idx, pattern in enumerate(all_patterns):
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extraer monto
                    amount_text = match.group(1) if match.groups() else match.group(0)
                    normalized_amount = self._normalize_amount(amount_text)
                    
                    if self._is_valid_amount(normalized_amount):
                        # Contexto
                        start = max(0, match.start() - context_window)
                        end = min(len(text), match.end() + context_window)
                        context = text[start:end].strip()
                        
                        # Confianza
                        confidence = self._calculate_confidence(context, match.group(0))
                        
                        amount_info = {
                            'raw_text': match.group(0),
                            'amount': normalized_amount,
                            'context': context,
                            'position': match.span(),
                            'pattern_index': pattern_idx,
                            'confidence': confidence,
                            'currency': self._detect_currency(match.group(0), context),
                            'is_learned': pattern in self.learned_patterns
                        }
                        
                        amounts.append(amount_info)
                        self.extraction_stats[f'pattern_{pattern_idx}'] += 1
                        
            except re.error as e:
                logger.warning(f"Error en patrón {pattern}: {e}")
                continue
        
        # Eliminar duplicados
        amounts = self._remove_duplicates(amounts)
        
        # Aprender si está habilitado
        if self.learning_mode:
            self._learn_from_extractions(text, amounts)
        
        # Ordenar por confianza
        amounts.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"💰 Extraídos {len(amounts)} montos únicos")
        return amounts
    
    def _normalize_amount(self, amount_text: str) -> float:
        """Normaliza texto de monto a float"""
        try:
            # Limpiar
            clean_text = re.sub(r'[^\d,\.]', '', amount_text.strip())
            
            if not clean_text:
                return 0.0
            
            # Manejar formatos
            if ',' in clean_text and '.' in clean_text:
                if clean_text.rfind(',') > clean_text.rfind('.'):
                    # Formato europeo: 1.234,56
                    clean_text = clean_text.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,234.56
                    clean_text = clean_text.replace(',', '')
            elif ',' in clean_text:
                # Solo comas
                comma_parts = clean_text.split(',')
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    # Decimal: 123,45
                    clean_text = clean_text.replace(',', '.')
                else:
                    # Miles: 1,234
                    clean_text = clean_text.replace(',', '')
            
            return float(clean_text)
            
        except (ValueError, AttributeError):
            return 0.0
    
    def _is_valid_amount(self, amount: float) -> bool:
        """Valida si un monto es realista"""
        if amount <= 0:
            return False
        
        if amount < 0.01 or amount > 1_000_000_000:
            return False
        
        # Filtrar años
        if 1900 <= amount <= 2100:
            return False
        
        return True
    
    def _calculate_confidence(self, context: str, raw_text: str) -> float:
        """Calcula confianza basada en contexto"""
        confidence = 0.5  # Base
        context_lower = context.lower()
        
        # Bonificaciones por contexto monetario
        for ctx in self.monetary_contexts:
            if ctx in context_lower:
                confidence += 0.1
                if confidence > 1.0:
                    confidence = 1.0
                    break
        
        # Bonificación por símbolo de moneda
        if any(symbol in raw_text for symbol in ['S/', '$', '€', '£', 'USD', 'EUR', 'PEN']):
            confidence += 0.2
        
        # Bonificación por formato numérico
        if re.search(r'\d{1,3}(?:[,\.]\d{3})+', raw_text):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _detect_currency(self, amount_text: str, context: str) -> str:
        """Detecta la moneda del monto"""
        amount_upper = amount_text.upper()
        context_upper = context.upper()
        
        # Detección directa
        if 'USD' in amount_upper or '$' in amount_text:
            return 'USD'
        elif 'EUR' in amount_upper or '€' in amount_text:
            return 'EUR'
        elif 'GBP' in amount_upper or '£' in amount_text:
            return 'GBP'
        elif 'S/' in amount_text or 'PEN' in amount_upper or 'SOL' in amount_upper:
            return 'PEN'
        
        # Detección por contexto
        if any(word in context_upper for word in ['DÓLARES', 'DOLLARS', 'USD']):
            return 'USD'
        elif any(word in context_upper for word in ['EUROS', 'EUR']):
            return 'EUR'
        elif any(word in context_upper for word in ['SOLES', 'NUEVOS SOLES', 'PEN']):
            return 'PEN'
        
        # Por defecto en Perú
        return 'PEN'
    
    def _remove_duplicates(self, amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina montos duplicados"""
        unique_amounts = []
        seen_amounts = set()
        
        for amount in amounts:
            # Crear clave única
            key = (
                round(amount['amount'], 2),
                amount['currency'],
                amount['position'][0] // 50  # Agrupar por posición aproximada
            )
            
            if key not in seen_amounts:
                seen_amounts.add(key)
                unique_amounts.append(amount)
        
        return unique_amounts
    
    def _learn_from_extractions(self, text: str, amounts: List[Dict[str, Any]]):
        """Aprende nuevos patrones de extracciones exitosas"""
        if not amounts:
            return
        
        # Aprender de extracciones con alta confianza
        high_confidence_amounts = [a for a in amounts if a['confidence'] > 0.8]
        
        for amount in high_confidence_amounts:
            context = amount['context']
            raw_text = amount['raw_text']
            
            # Generar patrón contextual
            words_before = self._get_words_before(context, raw_text)
            if words_before:
                pattern = self._create_pattern_from_words(words_before)
                if pattern and pattern not in self.base_patterns:
                    self.learned_patterns.add(pattern)
                    logger.info(f"📚 Nuevo patrón aprendido: {pattern}")
        
        # Guardar patrones aprendidos
        if self.learned_patterns:
            self._save_learned_patterns()
    
    def _get_words_before(self, context: str, raw_text: str) -> List[str]:
        """Obtiene palabras antes del monto"""
        try:
            # Encontrar posición del monto en el contexto
            pos = context.lower().find(raw_text.lower())
            if pos > 0:
                before_text = context[:pos].strip()
                # Obtener últimas 3 palabras
                words = re.findall(r'\w+', before_text)
                return words[-3:] if len(words) >= 3 else words
        except:
            pass
        return []
    
    def _create_pattern_from_words(self, words: List[str]) -> str:
        """Crea patrón regex a partir de palabras contextuales"""
        if not words:
            return ""
        
        try:
            # Crear patrón flexible
            word_pattern = '|'.join(re.escape(word.lower()) for word in words)
            pattern = f'(?:{word_pattern})\\s+(?:de\\s+)?(?:S/\\.?\\s*)?(\\d+(?:[,\\.]\\d{{3}})*(?:[,\\.]\\d{{2}})?)'
            
            # Validar patrón
            re.compile(pattern)
            return pattern
        except re.error:
            return ""
    
    def _load_learned_patterns(self):
        """Carga patrones aprendidos previamente"""
        try:
            patterns_file = Path('data/learned_patterns.json')
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_patterns = set(data.get('patterns', []))
                    logger.info(f"📚 Cargados {len(self.learned_patterns)} patrones aprendidos")
        except Exception as e:
            logger.warning(f"No se pudieron cargar patrones: {e}")
    
    def _save_learned_patterns(self):
        """Guarda patrones aprendidos"""
        try:
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            patterns_file = data_dir / 'learned_patterns.json'
            data = {
                'patterns': list(self.learned_patterns),
                'timestamp': datetime.now().isoformat(),
                'total_patterns': len(self.learned_patterns)
            }
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"No se pudieron guardar patrones: {e}")
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de extracción"""
        return {
            'total_extractions': sum(self.extraction_stats.values()),
            'patterns_used': dict(self.extraction_stats),
            'learned_patterns_count': len(self.learned_patterns),
            'base_patterns_count': len(self.base_patterns),
            'confidence_history': self.confidence_history[-10:]  # Últimas 10
        }
    
    def reset_learning(self):
        """Reinicia el aprendizaje"""
        self.learned_patterns.clear()
        self.extraction_stats.clear()
        self.confidence_history.clear()
        logger.info("🔄 Aprendizaje reiniciado")

def create_smart_detector_standalone(learning_mode: bool = True) -> SmartMoneyDetectorStandalone:
    """Crea una instancia del detector standalone"""
    return SmartMoneyDetectorStandalone(learning_mode=learning_mode) 
#!/usr/bin/env python3
"""
Detector Inteligente de Montos Monetarios
=========================================

Sistema adaptativo que detecta CUALQUIER patrón monetario sin configuración previa.
Aprende automáticamente de los documentos y se optimiza con cada uso.
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartMoneyDetector:
    """Detector inteligente que se adapta automáticamente a cualquier formato monetario"""
    
    def __init__(self, learning_mode: bool = True):
        self.learning_mode = learning_mode
        
        # Patrones base que cubren la mayoría de formatos monetarios mundiales
        self.base_patterns = [
            # Patrones con símbolos de moneda
            r'(?:S/\.?\s*)?(\d{1,4}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',  # S/ 1,234.56
            r'(?:USD|US\$|\$)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',  # USD 1,234.56
            r'(?:EUR|€)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',        # EUR 1,234.56
            r'(?:GBP|£)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',        # GBP 1,234.56
            r'(?:PEN|SOL)\s*(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',      # PEN 1,234.56
            
            # Patrones con palabras
            r'(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)\s*(?:soles?|dólares?|euros?|pesos?)',
            r'(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)\s*(?:nuevos\s+soles?)',
            
            # Patrones numéricos puros (más conservadores)
            r'\b(\d{1,3}(?:[,\.]\d{3})+(?:[,\.]\d{2})?)\b',  # 1,234.56
            r'\b(\d{3,6}(?:[,\.]\d{2})?)\b',                 # 12345.67
            
            # Patrones específicos para documentos legales
            r'(?:monto|valor|importe|suma|cantidad)\s+(?:de\s+)?(?:S/\.?\s*)?(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
            r'(?:hasta|máximo|límite)\s+(?:de\s+)?(?:S/\.?\s*)?(\d+(?:[,\.]\d{3})*(?:[,\.]\d{2})?)',
        ]
        
        # Patrones aprendidos dinámicamente
        self.learned_patterns = set()
        
        # Diccionario de contextos que ayudan a identificar montos
        self.monetary_contexts = {
            'spanish': [
                'viáticos?', 'gastos?', 'monto', 'valor', 'importe', 'suma', 'cantidad',
                'precio', 'costo', 'tarifa', 'cuota', 'pago', 'remuneración',
                'salario', 'sueldo', 'honorarios?', 'dieta', 'subsidio',
                'máximo', 'mínimo', 'límite', 'tope', 'hasta'
            ],
            'english': [
                'amount', 'value', 'price', 'cost', 'fee', 'payment', 'salary',
                'maximum', 'minimum', 'limit', 'up to', 'allowance'
            ]
        }
        
        # Estadísticas para mejora continua
        self.extraction_stats = defaultdict(int)
        self.confidence_history = []
        
        # Cargar patrones aprendidos previamente
        self._load_learned_patterns()
    
    def extract_all_amounts(self, text: str, context_window: int = 100) -> List[Dict[str, Any]]:
        """
        Extrae TODOS los posibles montos del texto, no solo los esperados
        
        Args:
            text: Texto a analizar
            context_window: Ventana de contexto alrededor de cada monto
            
        Returns:
            Lista de diccionarios con montos encontrados y su contexto
        """
        amounts = []
        all_patterns = list(self.base_patterns) + list(self.learned_patterns)
        
        for pattern_idx, pattern in enumerate(all_patterns):
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extraer el monto numérico
                    amount_text = match.group(1) if match.groups() else match.group(0)
                    normalized_amount = self._normalize_amount(amount_text)
                    
                    if self._is_valid_amount(normalized_amount):
                        # Extraer contexto
                        start = max(0, match.start() - context_window)
                        end = min(len(text), match.end() + context_window)
                        context = text[start:end].strip()
                        
                        # Calcular confianza basada en contexto
                        confidence = self._calculate_context_confidence(context)
                        
                        amount_info = {
                            'raw_text': match.group(0),
                            'amount': normalized_amount,
                            'context': context,
                            'position': match.span(),
                            'pattern_used': pattern,
                            'pattern_index': pattern_idx,
                            'confidence': confidence,
                            'currency': self._detect_currency(match.group(0), context),
                            'is_learned_pattern': pattern in self.learned_patterns
                        }
                        
                        amounts.append(amount_info)
                        
                        # Estadísticas
                        self.extraction_stats[f'pattern_{pattern_idx}'] += 1
                        
            except re.error as e:
                logger.warning(f"Error en patrón {pattern}: {e}")
                continue
        
        # Eliminar duplicados cercanos
        amounts = self._remove_duplicate_amounts(amounts)
        
        # Aprender nuevos patrones si está habilitado
        if self.learning_mode:
            self._learn_from_context(text, amounts)
        
        # Ordenar por confianza
        amounts.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"💰 Extraídos {len(amounts)} montos únicos")
        return amounts
    
    def _normalize_amount(self, amount_text: str) -> float:
        """Normaliza un texto de monto a número float"""
        try:
            # Limpiar el texto
            clean_text = re.sub(r'[^\d,\.]', '', amount_text)
            
            if not clean_text:
                return 0.0
            
            # Manejar diferentes formatos
            if ',' in clean_text and '.' in clean_text:
                # Formato: 1,234.56 o 1.234,56
                if clean_text.rfind(',') > clean_text.rfind('.'):
                    # Formato europeo: 1.234,56
                    clean_text = clean_text.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,234.56
                    clean_text = clean_text.replace(',', '')
            elif ',' in clean_text:
                # Solo comas - podría ser separador de miles o decimal
                comma_parts = clean_text.split(',')
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    # Probablemente decimal: 123,45
                    clean_text = clean_text.replace(',', '.')
                else:
                    # Probablemente separador de miles: 1,234
                    clean_text = clean_text.replace(',', '')
            
            return float(clean_text)
            
        except (ValueError, AttributeError):
            return 0.0
    
    def _is_valid_amount(self, amount: float) -> bool:
        """Determina si un monto es válido y realista"""
        # Filtros básicos de validez
        if amount <= 0:
            return False
        
        # Rangos realistas para diferentes contextos
        if amount < 0.01:  # Muy pequeño
            return False
        
        if amount > 1_000_000_000:  # Muy grande (mil millones)
            return False
        
        # Filtrar números que probablemente no son montos
        # (como años, códigos, etc.)
        if 1900 <= amount <= 2100:  # Probablemente años
            return False
        
        if amount in [100, 200, 300, 400, 500, 600, 700, 800, 900]:
            # Números redondos comunes que podrían ser otros valores
            # Solo aceptar si tienen contexto monetario fuerte
            return False
        
        return True
    
    def _calculate_context_confidence(self, context: str) -> float:
        """Calcula la confianza basada en el contexto alrededor del monto"""
        confidence = 0.5  # Base
        context_lower = context.lower()
        
        # Buscar palabras clave monetarias
        for lang, keywords in self.monetary_contexts.items():
            for keyword in keywords:
                if re.search(r'\b' + keyword + r'\b', context_lower):
                    confidence += 0.1
                    if confidence > 1.0:
                        confidence = 1.0
                        break
        
        # Penalizar contextos que sugieren no-montos
        non_monetary_keywords = [
            'página', 'artículo', 'numeral', 'inciso', 'literal',
            'año', 'fecha', 'código', 'número', 'teléfono',
            'dni', 'ruc', 'id', 'serie'
        ]
        
        for keyword in non_monetary_keywords:
            if keyword in context_lower:
                confidence -= 0.2
                if confidence < 0.1:
                    confidence = 0.1
                    break
        
        # Bonus por símbolos monetarios
        if re.search(r'S/|USD|\$|€|£', context):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _detect_currency(self, amount_text: str, context: str) -> str:
        """Detecta la moneda basada en el texto y contexto"""
        full_text = f"{amount_text} {context}".lower()
        
        currency_patterns = {
            'PEN': [r's/', r'soles?', r'nuevos\s+soles?', r'pen'],
            'USD': [r'usd', r'us\$', r'\$', r'dólares?', r'dollars?'],
            'EUR': [r'eur', r'€', r'euros?'],
            'GBP': [r'gbp', r'£', r'pounds?', r'libras?'],
        }
        
        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_text):
                    return currency
        
        return 'UNKNOWN'
    
    def _remove_duplicate_amounts(self, amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina montos duplicados que están muy cerca en el texto"""
        if not amounts:
            return amounts
        
        # Ordenar por posición
        amounts.sort(key=lambda x: x['position'][0])
        
        unique_amounts = []
        
        for current in amounts:
            is_duplicate = False
            
            for existing in unique_amounts:
                # Verificar si es el mismo monto en posiciones cercanas
                if (abs(current['amount'] - existing['amount']) < 0.01 and
                    abs(current['position'][0] - existing['position'][0]) < 50):
                    is_duplicate = True
                    # Mantener el de mayor confianza
                    if current['confidence'] > existing['confidence']:
                        unique_amounts.remove(existing)
                        unique_amounts.append(current)
                    break
            
            if not is_duplicate:
                unique_amounts.append(current)
        
        return unique_amounts
    
    def _learn_from_context(self, text: str, found_amounts: List[Dict[str, Any]]):
        """Aprende nuevos patrones basado en los montos encontrados exitosamente"""
        if not found_amounts:
            return
        
        # Analizar contextos exitosos para crear nuevos patrones
        high_confidence_amounts = [a for a in found_amounts if a['confidence'] > 0.8]
        
        for amount_info in high_confidence_amounts:
            context = amount_info['context']
            
            # Buscar patrones de palabras que preceden a montos
            words_before = re.findall(r'(\w+)\s+(?:S/\.?\s*)?(?:\d+)', context, re.IGNORECASE)
            
            for word in words_before:
                if word.lower() not in [item for sublist in self.monetary_contexts.values() for item in sublist]:
                    # Crear nuevo patrón
                    new_pattern = f"{word}\\s+(?:S/\\.?\\s*)?(\\d+(?:[,\\.]\\d{{3}})*(?:[,\\.]\\d{{2}})?)"
                    
                    if new_pattern not in self.learned_patterns:
                        self.learned_patterns.add(new_pattern)
                        logger.info(f"📚 Nuevo patrón aprendido: {word} + monto")
        
        # Guardar patrones aprendidos
        if self.learned_patterns:
            self._save_learned_patterns()
    
    def _load_learned_patterns(self):
        """Carga patrones aprendidos previamente"""
        patterns_file = Path("data/learned_patterns.json")
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_patterns = set(data.get('patterns', []))
                    logger.info(f"📚 Cargados {len(self.learned_patterns)} patrones aprendidos")
            except Exception as e:
                logger.warning(f"Error cargando patrones: {e}")
    
    def _save_learned_patterns(self):
        """Guarda patrones aprendidos para uso futuro"""
        patterns_file = Path("data/learned_patterns.json")
        patterns_file.parent.mkdir(exist_ok=True)
        
        try:
            data = {
                'patterns': list(self.learned_patterns),
                'last_updated': datetime.now().isoformat(),
                'total_patterns': len(self.learned_patterns)
            }
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Guardados {len(self.learned_patterns)} patrones aprendidos")
            
        except Exception as e:
            logger.warning(f"Error guardando patrones: {e}")
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de extracción para análisis"""
        return {
            'base_patterns_count': len(self.base_patterns),
            'learned_patterns_count': len(self.learned_patterns),
            'total_extractions': sum(self.extraction_stats.values()),
            'pattern_usage': dict(self.extraction_stats),
            'average_confidence': sum(self.confidence_history) / len(self.confidence_history) if self.confidence_history else 0,
            'learning_mode': self.learning_mode
        }
    
    def reset_learning(self):
        """Reinicia el aprendizaje (útil para testing)"""
        self.learned_patterns.clear()
        self.extraction_stats.clear()
        self.confidence_history.clear()
        
        # Eliminar archivo de patrones
        patterns_file = Path("data/learned_patterns.json")
        if patterns_file.exists():
            patterns_file.unlink()
        
        logger.info("🔄 Sistema de aprendizaje reiniciado")


def create_smart_detector(learning_mode: bool = True) -> SmartMoneyDetector:
    """Factory function para crear detector inteligente"""
    return SmartMoneyDetector(learning_mode=learning_mode)
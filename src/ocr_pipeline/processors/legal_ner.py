#!/usr/bin/env python3
"""
Legal Named Entity Recognition (NER) for Peruvian Legal Documents
================================================================

Specialized NER system optimized for extracting legal and financial entities
from Peruvian legal documents with >90% accuracy requirement.
"""

import re
import spacy
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

try:
    # Try to load Spanish spaCy model
    nlp = spacy.load("es_core_news_sm")
except IOError:
    # Fallback - will need to install model
    nlp = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LegalEntity:
    """Represents a legal entity with metadata."""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    context: str = ""
    normalized_value: Optional[str] = None


class LegalNER:
    """
    Advanced NER system for Peruvian legal documents.
    
    Extracts:
    - AMOUNTS: S/ 30.00, treinta soles, 320.00
    - PERCENTAGES: 30%, tres por ciento
    - NUMERALS: 8.4.17, artículo 24, inciso a)
    - ROLES: Ministro, servidor civil, funcionario
    - DATES: 10 días hábiles, 31 de marzo
    - REFERENCES: Decreto Supremo N° 007-2013
    """
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize Legal NER with Peruvian legal optimizations.
        
        Args:
            use_spacy: Whether to use spaCy for enhanced NER
        """
        self.use_spacy = use_spacy and nlp is not None
        
        # Entity extraction patterns (ordered by specificity)
        self.patterns = {
            # FINANCIAL ENTITIES
            'AMOUNT_SOLES': re.compile(
                r'S/\s*(\d{1,3}(?:\,\d{3})*(?:\.\d{2})?)', 
                re.IGNORECASE
            ),
            'AMOUNT_WRITTEN': re.compile(
                r'((?:un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciséis|diecisiete|dieciocho|diecinueve|veinte|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|doscientos|trescientos|cuatrocientos|quinientos|seiscientos|setecientos|ochocientos|novecientos|mil)\s*)+soles?',
                re.IGNORECASE
            ),
            'PERCENTAGE': re.compile(
                r'(\d{1,2}(?:\.\d+)?)\s*(?:%|por\s+ciento)',
                re.IGNORECASE
            ),
            'PERCENTAGE_WRITTEN': re.compile(
                r'((?:un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciséis|diecisiete|dieciocho|diecinueve|veinte|treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa|cien)\s*por\s+ciento)',
                re.IGNORECASE
            ),
            
            # LEGAL HIERARCHY
            'NUMERAL_DEEP': re.compile(
                r'(\d{1,2}\.\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)',
                re.IGNORECASE
            ),
            'ARTICLE': re.compile(
                r'artículo\s+(\d{1,3})(?:\s*[°º])?',
                re.IGNORECASE
            ),
            'INCISO': re.compile(
                r'inciso\s+([a-z])\)',
                re.IGNORECASE
            ),
            'PARAGRAPH': re.compile(
                r'párrafo\s+(\d{1,2})',
                re.IGNORECASE
            ),
            
            # ROLES AND AUTHORITIES
            'MINISTER': re.compile(
                r'(ministro(?:\s+de\s+estado)?|ministra)',
                re.IGNORECASE
            ),
            'CIVIL_SERVANT': re.compile(
                r'(servidor(?:\s+público|\s+civil)|funcionario(?:\s+público)?)',
                re.IGNORECASE
            ),
            'AUTHORITY': re.compile(
                r'(jefe(?:\s+del?\s+órgano)?|director|coordinador|supervisor)',
                re.IGNORECASE
            ),
            
            # LEGAL REFERENCES
            'DECREE': re.compile(
                r'(decreto\s+supremo\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,4})',
                re.IGNORECASE
            ),
            'DIRECTIVE': re.compile(
                r'(directiva\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,10})',
                re.IGNORECASE
            ),
            'RESOLUTION': re.compile(
                r'(resolución\s+(?:ministerial\s+)?n[°º]\s*\d{3}-\d{4}-[A-Z]{2,10})',
                re.IGNORECASE
            ),
            
            # TEMPORAL ENTITIES
            'DAYS_PERIOD': re.compile(
                r'(\d{1,2})\s+días?\s+hábiles?',
                re.IGNORECASE
            ),
            'DATE_DMY': re.compile(
                r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})',
                re.IGNORECASE
            ),
            'DATE_NUMERIC': re.compile(
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
                re.IGNORECASE
            ),
            
            # PROCEDURES AND ACTIONS
            'PROCEDURE': re.compile(
                r'(procedimiento|trámite|gestión|solicitud|requerimiento)',
                re.IGNORECASE
            ),
            'DEADLINE': re.compile(
                r'(plazo|término|fecha\s+límite)',
                re.IGNORECASE
            ),
            'DOCUMENT_TYPE': re.compile(
                r'(declaración\s+jurada|certificado|comprobante|boleta|factura)',
                re.IGNORECASE
            )
        }
        
        # Value normalizers
        self.normalizers = {
            'amount': self._normalize_amount,
            'percentage': self._normalize_percentage,
            'date': self._normalize_date,
            'numeral': self._normalize_numeral
        }
        
        # Spanish number words to digits
        self.number_words = {
            'un': 1, 'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
            'dieciséis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19,
            'veinte': 20, 'treinta': 30, 'cuarenta': 40, 'cincuenta': 50,
            'sesenta': 60, 'setenta': 70, 'ochenta': 80, 'noventa': 90,
            'cien': 100, 'ciento': 100, 'doscientos': 200, 'trescientos': 300,
            'cuatrocientos': 400, 'quinientos': 500, 'seiscientos': 600,
            'setecientos': 700, 'ochocientos': 800, 'novecientos': 900,
            'mil': 1000
        }
        
        logger.info(f"Legal NER initialized with {len(self.patterns)} patterns")
        if self.use_spacy:
            logger.info("Using spaCy for enhanced entity recognition")
    
    def extract_entities(self, text: str, context_window: int = 50) -> List[LegalEntity]:
        """
        Extract all legal entities from text with high accuracy.
        
        Args:
            text: Input text to analyze
            context_window: Characters of context around each entity
            
        Returns:
            List of detected legal entities with metadata
        """
        entities = []
        
        # Pattern-based extraction (rule-based, high precision)
        pattern_entities = self._extract_with_patterns(text, context_window)
        entities.extend(pattern_entities)
        
        # spaCy-based extraction (ML-enhanced)
        if self.use_spacy:
            spacy_entities = self._extract_with_spacy(text, context_window)
            entities.extend(spacy_entities)
        
        # Remove duplicates and sort by position
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda x: x.start)
        
        return entities
    
    def _extract_with_patterns(self, text: str, context_window: int) -> List[LegalEntity]:
        """Extract entities using rule-based patterns."""
        entities = []
        
        for label, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                # Extract context
                start_ctx = max(0, match.start() - context_window)
                end_ctx = min(len(text), match.end() + context_window)
                context = text[start_ctx:end_ctx]
                
                # Normalize value if applicable
                normalized = self._normalize_entity_value(label, match.group(1) if match.groups() else match.group(0))
                
                entity = LegalEntity(
                    text=match.group(0),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,  # High confidence for pattern matches
                    context=context,
                    normalized_value=normalized
                )
                entities.append(entity)
        
        return entities
    
    def _extract_with_spacy(self, text: str, context_window: int) -> List[LegalEntity]:
        """Extract entities using spaCy NLP model."""
        entities = []
        
        try:
            doc = nlp(text)
            
            for ent in doc.ents:
                # Map spaCy labels to our legal labels
                legal_label = self._map_spacy_label(ent.label_, ent.text)
                
                if legal_label:
                    # Extract context
                    start_ctx = max(0, ent.start_char - context_window)
                    end_ctx = min(len(text), ent.end_char + context_window)
                    context = text[start_ctx:end_ctx]
                    
                    entity = LegalEntity(
                        text=ent.text,
                        label=legal_label,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.85,  # Lower confidence for ML predictions
                        context=context,
                        normalized_value=self._normalize_entity_value(legal_label, ent.text)
                    )
                    entities.append(entity)
        
        except Exception as e:
            logger.warning(f"spaCy entity extraction failed: {e}")
        
        return entities
    
    def _map_spacy_label(self, spacy_label: str, text: str) -> Optional[str]:
        """Map spaCy entity labels to our legal entity labels."""
        mapping = {
            'MONEY': 'AMOUNT_SOLES',
            'PERCENT': 'PERCENTAGE',
            'DATE': 'DATE_NUMERIC',
            'PERSON': 'CIVIL_SERVANT',  # Could be refined
            'ORG': 'AUTHORITY',
            'LAW': 'DECREE'  # Custom label if available
        }
        
        # Context-based refinement
        text_lower = text.lower()
        if spacy_label == 'PERSON':
            if 'ministro' in text_lower or 'ministra' in text_lower:
                return 'MINISTER'
            elif 'servidor' in text_lower or 'funcionario' in text_lower:
                return 'CIVIL_SERVANT'
        
        return mapping.get(spacy_label)
    
    def _normalize_entity_value(self, label: str, value: str) -> Optional[str]:
        """Normalize entity values to standard format."""
        try:
            if label.startswith('AMOUNT'):
                return self._normalize_amount(value)
            elif label.startswith('PERCENTAGE'):
                return self._normalize_percentage(value)
            elif label.startswith('DATE'):
                return self._normalize_date(value)
            elif label.startswith('NUMERAL'):
                return self._normalize_numeral(value)
            else:
                return value.strip()
        except Exception as e:
            logger.warning(f"Normalization failed for {label}: {value} - {e}")
            return value
    
    def _normalize_amount(self, amount_text: str) -> str:
        """Normalize amount to standard format (S/ XXX.XX)."""
        # Remove S/ prefix if present
        amount_text = re.sub(r'^S/\s*', '', amount_text)
        
        # Handle written numbers
        if any(word in amount_text.lower() for word in self.number_words.keys()):
            numeric_value = self._convert_written_to_number(amount_text)
            return f"S/ {numeric_value:.2f}"
        
        # Handle numeric amounts
        amount_text = amount_text.replace(',', '')  # Remove thousands separators
        try:
            value = float(amount_text)
            return f"S/ {value:.2f}"
        except ValueError:
            return amount_text
    
    def _normalize_percentage(self, percent_text: str) -> str:
        """Normalize percentage to standard format (XX.X%)."""
        # Extract numeric part
        match = re.search(r'(\d+(?:\.\d+)?)', percent_text)
        if match:
            value = float(match.group(1))
            return f"{value}%"
        
        # Handle written percentages
        if 'por ciento' in percent_text.lower():
            numeric_value = self._convert_written_to_number(percent_text.replace('por ciento', '').strip())
            return f"{numeric_value}%"
        
        return percent_text
    
    def _normalize_date(self, date_text: str) -> str:
        """Normalize date to ISO format (YYYY-MM-DD)."""
        # Handle "DD de MONTH de YYYY" format
        month_names = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        for month_name, month_num in month_names.items():
            if month_name in date_text.lower():
                parts = re.findall(r'\d+', date_text)
                if len(parts) >= 2:
                    day = parts[0].zfill(2)
                    year = parts[1] if len(parts[1]) == 4 else f"20{parts[1]}"
                    return f"{year}-{month_num}-{day}"
        
        # Handle DD/MM/YYYY or DD-MM-YYYY format
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_text)
        if match:
            day, month, year = match.groups()
            if len(year) == 2:
                year = f"20{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_text
    
    def _normalize_numeral(self, numeral_text: str) -> str:
        """Normalize legal numeral to standard format."""
        # Already in good format for most cases
        return numeral_text.strip()
    
    def _convert_written_to_number(self, text: str) -> float:
        """Convert written Spanish numbers to numeric value."""
        words = text.lower().split()
        total = 0
        current = 0
        
        for word in words:
            if word in self.number_words:
                value = self.number_words[word]
                if value == 1000:
                    current *= value
                    total += current
                    current = 0
                elif value == 100:
                    current *= value
                else:
                    current += value
        
        return float(total + current)
    
    def _deduplicate_entities(self, entities: List[LegalEntity]) -> List[LegalEntity]:
        """Remove duplicate entities based on text overlap."""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda x: (x.start, -x.confidence))
        
        deduplicated = []
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = False
            for existing in deduplicated:
                if (entity.start < existing.end and entity.end > existing.start):
                    # Overlapping entities - keep the one with higher confidence
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(entity)
        
        return deduplicated
    
    def get_entity_summary(self, entities: List[LegalEntity]) -> Dict[str, Any]:
        """Get summary statistics of extracted entities."""
        summary = {
            'total_entities': len(entities),
            'by_type': {},
            'confidence_avg': 0.0,
            'amounts_found': [],
            'percentages_found': [],
            'references_found': []
        }
        
        # Count by type
        for entity in entities:
            entity_type = entity.label.split('_')[0]  # Get base type
            summary['by_type'][entity_type] = summary['by_type'].get(entity_type, 0) + 1
        
        # Calculate average confidence
        if entities:
            summary['confidence_avg'] = sum(e.confidence for e in entities) / len(entities)
        
        # Extract specific high-value entities
        for entity in entities:
            if entity.label.startswith('AMOUNT'):
                summary['amounts_found'].append(entity.normalized_value or entity.text)
            elif entity.label.startswith('PERCENTAGE'):
                summary['percentages_found'].append(entity.normalized_value or entity.text)
            elif entity.label in ['DECREE', 'DIRECTIVE', 'RESOLUTION']:
                summary['references_found'].append(entity.text)
        
        return summary
    
    def get_stats(self) -> Dict[str, Any]:
        """Get NER system statistics."""
        return {
            'patterns': len(self.patterns),
            'pattern_types': list(self.patterns.keys()),
            'use_spacy': self.use_spacy,
            'spacy_available': nlp is not None,
            'normalizers': list(self.normalizers.keys()),
            'status': 'initialized'
        }


if __name__ == "__main__":
    # Test the Legal NER system
    ner = LegalNER()
    
    print("Legal NER system initialized successfully")
    print(f"NER stats: {ner.get_stats()}")
    
    # Test with sample legal text
    sample_text = """
    8.4.17. Los comisionados podrán presentar Declaración Jurada por gastos de movilidad 
    que no excedan el treinta por ciento (30%) del monto total de viáticos, equivalente 
    a S/ 30.00 por día, según lo establecido en el Decreto Supremo N° 007-2013-EF.
    El Ministro de Estado tiene asignado S/ 380.00 para viáticos nacionales.
    """
    
    print("\nTesting entity extraction...")
    entities = ner.extract_entities(sample_text)
    
    print(f"Found {len(entities)} entities:")
    for entity in entities:
        print(f"  {entity.label}: '{entity.text}' -> '{entity.normalized_value}' (conf: {entity.confidence:.2f})")
    
    # Show summary
    summary = ner.get_entity_summary(entities)
    print(f"\nSummary: {summary}")
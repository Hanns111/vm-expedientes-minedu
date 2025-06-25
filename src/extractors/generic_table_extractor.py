#!/usr/bin/env python3
"""
Generic Table Extractor - Extracción Pura Sin Lógica de Negocio
===============================================================

Extractor genérico que SOLO extrae tablas y devuelve JSON estructurado.
NO contiene ninguna regla de negocio ni validación normativa.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Reutilizar el extractor universal existente pero solo para extracción
try:
    from ..universal_extractor.generic_table_extractor import GenericTableExtractor as UniversalExtractor
    from ..universal_extractor.generic_money_detector import GenericMoneyDetector as UniversalMoneyDetector
    UNIVERSAL_AVAILABLE = True
except ImportError:
    UNIVERSAL_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ExtractedTableRow:
    """Fila extraída de tabla sin interpretación normativa"""
    numeral: Optional[str] = None
    concepto: Optional[str] = None  
    ubicacion: Optional[str] = None
    tarifa: Optional[float] = None
    unidad: Optional[str] = None
    raw_data: List[str] = None
    confidence: float = 0.0
    source_table: str = ""
    page_number: int = 0

@dataclass 
class ExtractedDocument:
    """Documento completo extraído sin interpretación"""
    file_path: str
    tables: List[Dict[str, Any]]
    structured_rows: List[ExtractedTableRow]
    raw_entities: Dict[str, List[str]]
    metadata: Dict[str, Any]
    extraction_confidence: float

class GenericTableExtractor:
    """
    Extractor genérico que SOLO extrae datos sin aplicar lógica normativa.
    
    Principios:
    - NO valida reglas de negocio
    - NO aplica límites normativos  
    - SOLO estructura datos extraídos
    - Devuelve JSON con campos estándar
    """
    
    def __init__(self):
        self.universal_extractor = None
        self.money_detector = None
        
        if UNIVERSAL_AVAILABLE:
            self.universal_extractor = UniversalExtractor()
            self.money_detector = UniversalMoneyDetector(learning_enabled=False)
        
        # Patrones genéricos para estructurar (sin lógica de negocio)
        self.field_patterns = {
            'numeral': [
                r'\b(\d+(?:\.\d+){1,4})\b',  # 8.4.17, 10.2.3.1
                r'(?:numeral|num\.|n°)\s*(\d+(?:\.\d+)*)',
                r'(?:art|artículo)\\.?\\s*(\\d+)'
            ],
            'concepto': [
                r'(traslado\s+[^,\n]+)',
                r'(movilidad\s+[^,\n]+)', 
                r'(alojamiento\s+[^,\n]+)',
                r'(alimentación\s+[^,\n]+)'
            ],
            'ubicacion': [
                r'\b(lima|región|regiones|provincia|provincias)\b',
                r'\b(capital|interior)\b'
            ],
            'tarifa': [
                r'S/\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*soles?',
                r'USD?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            'unidad': [
                r'por\s+(servicio|día|mes|persona)',
                r'(diario|mensual|anual)',
                r'(máximo|mínimo)'
            ]
        }
        
        logger.info("GenericTableExtractor inicializado - SOLO extracción, sin lógica normativa")
    
    def extract(self, pdf_path: str) -> ExtractedDocument:
        """
        Extraer tablas del PDF y estructurar sin aplicar reglas normativas.
        
        Returns:
            ExtractedDocument con datos estructurados pero sin validación
        """
        logger.info(f"🔍 Extrayendo datos de: {Path(pdf_path).name}")
        
        # 1. Extracción básica usando el sistema universal
        raw_extraction = self._extract_raw_data(pdf_path)
        
        # 2. Estructurar en formato estándar
        structured_rows = self._structure_table_rows(raw_extraction['tables'])
        
        # 3. Extraer entidades monetarias y numerales
        raw_entities = self._extract_raw_entities(pdf_path)
        
        # 4. Calcular confianza global de extracción
        extraction_confidence = self._calculate_extraction_confidence(raw_extraction, structured_rows)
        
        # 5. Crear documento estructurado
        document = ExtractedDocument(
            file_path=pdf_path,
            tables=raw_extraction['tables'],
            structured_rows=structured_rows,
            raw_entities=raw_entities,
            metadata=raw_extraction.get('metadata', {}),
            extraction_confidence=extraction_confidence
        )
        
        logger.info(f"✅ Extraídas {len(structured_rows)} filas estructuradas con confianza {extraction_confidence:.2f}")
        
        return document
    
    def _extract_raw_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extraer datos básicos usando el sistema universal"""
        
        if self.universal_extractor:
            try:
                return self.universal_extractor.extract_tables_universal(pdf_path)
            except Exception as e:
                logger.warning(f"Error con extractor universal: {e}")
        
        # Fallback: extracción básica con PyMuPDF
        return self._fallback_extraction(pdf_path)
    
    def _fallback_extraction(self, pdf_path: str) -> Dict[str, Any]:
        """Extracción de fallback básica"""
        
        try:
            import fitz
            
            tables = []
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Detectar estructuras tabulares básicas
                lines = text.split('\n')
                potential_table_lines = []
                
                for line in lines:
                    # Líneas que podrían ser filas de tabla
                    if (len(line.split()) > 2 and 
                        any(pattern in line.lower() for pattern in ['traslado', 'monto', 'límite', 'viático'])):
                        potential_table_lines.append(line.strip())
                
                if potential_table_lines:
                    tables.append({
                        'id': f'fallback_table_{page_num}',
                        'page': page_num + 1,
                        'method': 'fallback_text_analysis',
                        'raw_lines': potential_table_lines,
                        'confidence': 0.5
                    })
            
            doc.close()
            
            return {
                'tables': tables,
                'metadata': {
                    'extraction_method': 'fallback',
                    'total_tables': len(tables)
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return {'tables': [], 'metadata': {'error': str(e)}}
    
    def _structure_table_rows(self, raw_tables: List[Dict[str, Any]]) -> List[ExtractedTableRow]:
        """Estructurar filas de tablas usando patrones genéricos"""
        
        structured_rows = []
        
        for table in raw_tables:
            table_id = table.get('id', 'unknown')
            page_num = table.get('page', 0)
            
            # Procesar datos de la tabla
            if 'data' in table and table['data']:
                for row_idx, row_data in enumerate(table['data']):
                    row = self._extract_row_fields(row_data, table_id, page_num)
                    if row.numeral or row.concepto or row.tarifa:  # Al menos un campo válido
                        structured_rows.append(row)
            
            # Procesar líneas de texto si no hay datos estructurados
            elif 'raw_lines' in table:
                for line in table['raw_lines']:
                    row = self._extract_row_fields([line], table_id, page_num)
                    if row.numeral or row.concepto or row.tarifa:
                        structured_rows.append(row)
        
        return structured_rows
    
    def _extract_row_fields(self, row_data: List[str], table_id: str, page_num: int) -> ExtractedTableRow:
        """Extraer campos de una fila usando patrones genéricos"""
        
        # Combinar todos los datos de la fila en texto
        if isinstance(row_data, list):
            combined_text = ' '.join(str(cell) for cell in row_data)
        else:
            combined_text = str(row_data)
        
        row = ExtractedTableRow(
            raw_data=row_data if isinstance(row_data, list) else [str(row_data)],
            source_table=table_id,
            page_number=page_num
        )
        
        # Extraer cada campo usando patrones
        row.numeral = self._extract_field(combined_text, 'numeral')
        row.concepto = self._extract_field(combined_text, 'concepto')
        row.ubicacion = self._extract_field(combined_text, 'ubicacion')
        row.unidad = self._extract_field(combined_text, 'unidad')
        
        # Extraer tarifa y convertir a float
        tarifa_text = self._extract_field(combined_text, 'tarifa')
        if tarifa_text:
            row.tarifa = self._parse_currency_amount(tarifa_text)
        
        # Calcular confianza básica
        row.confidence = self._calculate_row_confidence(row, combined_text)
        
        return row
    
    def _extract_field(self, text: str, field_type: str) -> Optional[str]:
        """Extraer un campo específico usando patrones"""
        
        patterns = self.field_patterns.get(field_type, [])
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            except Exception as e:
                logger.debug(f"Error en patrón {pattern}: {e}")
                continue
        
        return None
    
    def _parse_currency_amount(self, amount_text: str) -> Optional[float]:
        """Convertir texto de moneda a float"""
        
        try:
            # Limpiar el texto
            clean_text = amount_text.replace(',', '').replace(' ', '')
            
            # Extraer solo los dígitos y punto decimal
            numeric_match = re.search(r'(\d+(?:\.\d{2})?)', clean_text)
            if numeric_match:
                return float(numeric_match.group(1))
        
        except Exception as e:
            logger.debug(f"Error parseando monto {amount_text}: {e}")
        
        return None
    
    def _calculate_row_confidence(self, row: ExtractedTableRow, original_text: str) -> float:
        """Calcular confianza de extracción de una fila"""
        
        confidence = 0.0
        max_confidence = 5.0  # Máximo posible
        
        # Bonificaciones por campos extraídos
        if row.numeral: confidence += 1.0
        if row.concepto: confidence += 1.5
        if row.tarifa: confidence += 1.5  
        if row.ubicacion: confidence += 0.5
        if row.unidad: confidence += 0.5
        
        # Bonus por palabras clave relevantes
        keywords = ['traslado', 'viático', 'monto', 'límite', 'servicio']
        keyword_count = sum(1 for keyword in keywords if keyword in original_text.lower())
        confidence += keyword_count * 0.2
        
        return min(1.0, confidence / max_confidence)
    
    def _extract_raw_entities(self, pdf_path: str) -> Dict[str, List[str]]:
        """Extraer entidades básicas sin interpretación"""
        
        entities = {
            'amounts': [],
            'numerals': [],
            'locations': [],
            'concepts': []
        }
        
        if self.money_detector:
            try:
                # Extraer texto completo
                import fitz
                doc = fitz.open(pdf_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
                doc.close()
                
                # Usar detector universal
                result = self.money_detector.extract_entities_universal(full_text)
                
                # Estructurar sin interpretación
                entities['amounts'] = [e.value for e in result.get('money_entities', [])]
                entities['numerals'] = [e.value for e in result.get('numeral_entities', [])]
                
            except Exception as e:
                logger.warning(f"Error extrayendo entidades: {e}")
        
        return entities
    
    def _calculate_extraction_confidence(self, raw_extraction: Dict[str, Any], 
                                       structured_rows: List[ExtractedTableRow]) -> float:
        """Calcular confianza global de extracción"""
        
        if not structured_rows:
            return 0.0
        
        # Confianza promedio de filas
        avg_row_confidence = sum(row.confidence for row in structured_rows) / len(structured_rows)
        
        # Factor por número de tablas encontradas
        table_factor = min(1.0, len(raw_extraction.get('tables', [])) / 3.0)
        
        # Factor por metadata de extracción
        metadata_confidence = raw_extraction.get('metadata', {}).get('confidence_score', 0.5)
        
        # Combinar factores
        global_confidence = (avg_row_confidence * 0.5 + 
                           table_factor * 0.2 + 
                           metadata_confidence * 0.3)
        
        return min(1.0, global_confidence)
    
    def export_json(self, document: ExtractedDocument, output_path: str):
        """Exportar documento extraído a JSON"""
        
        output_data = {
            'file_path': document.file_path,
            'extraction_confidence': document.extraction_confidence,
            'metadata': document.metadata,
            'structured_data': {
                'rows': [asdict(row) for row in document.structured_rows],
                'total_rows': len(document.structured_rows)
            },
            'raw_entities': document.raw_entities,
            'raw_tables': document.tables
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Datos extraídos guardados en: {output_path}")
    
    def get_extraction_summary(self, document: ExtractedDocument) -> Dict[str, Any]:
        """Obtener resumen de extracción sin validación normativa"""
        
        return {
            'total_tables': len(document.tables),
            'structured_rows': len(document.structured_rows),
            'confidence': document.extraction_confidence,
            'fields_extracted': {
                'with_numeral': sum(1 for row in document.structured_rows if row.numeral),
                'with_concepto': sum(1 for row in document.structured_rows if row.concepto),
                'with_tarifa': sum(1 for row in document.structured_rows if row.tarifa),
                'with_ubicacion': sum(1 for row in document.structured_rows if row.ubicacion)
            },
            'entities_found': {
                'amounts': len(document.raw_entities.get('amounts', [])),
                'numerals': len(document.raw_entities.get('numerals', [])),
                'locations': len(document.raw_entities.get('locations', []))
            }
        }

# Función de conveniencia para uso directo
def extract_document(pdf_path: str) -> ExtractedDocument:
    """Función de conveniencia para extraer un documento"""
    extractor = GenericTableExtractor()
    return extractor.extract(pdf_path)
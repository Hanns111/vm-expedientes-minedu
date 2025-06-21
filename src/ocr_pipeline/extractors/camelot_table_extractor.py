#!/usr/bin/env python3
"""
Camelot Table Extractor for Legal Documents
==========================================

Advanced table extraction using Camelot for legal documents with precise
numeral detection and context preservation.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    import camelot
    import pandas as pd
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    camelot = None
    pd = None

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

logger = logging.getLogger(__name__)


class CamelotTableExtractor:
    """
    Extractor de tablas usando Camelot con foco en documentos legales.
    Especializado en detectar numerales y mantener contexto jerárquico.
    """
    
    def __init__(self, 
                 flavor: str = 'lattice',
                 confidence_threshold: float = 0.8,
                 preserve_numerals: bool = True):
        """
        Initialize Camelot table extractor.
        
        Args:
            flavor: 'lattice' or 'stream' - detection method
            confidence_threshold: Minimum confidence for extracted tables
            preserve_numerals: Whether to preserve numeral-content relationships
        """
        self.flavor = flavor
        self.confidence_threshold = confidence_threshold
        self.preserve_numerals = preserve_numerals
        
        # Numeral patterns for legal documents
        self.numeral_patterns = {
            'section': re.compile(r'^(\d+)[\.\s]', re.MULTILINE),
            'subsection': re.compile(r'^(\d+\.\d+)[\.\s]', re.MULTILINE),
            'subsubsection': re.compile(r'^(\d+\.\d+\.\d+)[\.\s]', re.MULTILINE),
            'deep_section': re.compile(r'^(\d+\.\d+\.\d+\.\d+)[\.\s]', re.MULTILINE),
            'article': re.compile(r'(?:artículo|art\.?)\s*(\d+)', re.IGNORECASE),
            'item': re.compile(r'(?:inciso|literal)\s*([a-z]|\d+)', re.IGNORECASE)
        }
        
        # Known financial patterns
        self.amount_patterns = {
            'soles': re.compile(r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'percentage': re.compile(r'(\d{1,2}(?:\.\d+)?)%', re.IGNORECASE),
            'days': re.compile(r'(\d+)\s*días?', re.IGNORECASE)
        }
        
        # Context keywords for legal documents
        self.context_keywords = {
            'viaticos': ['viático', 'viáticos', 'gastos de viaje', 'comisión'],
            'roles': ['ministro', 'servidor', 'funcionario', 'secretario'],
            'procedures': ['declaración jurada', 'rendición', 'comprobante'],
            'amounts': ['monto', 'suma', 'importe', 'límite', 'máximo']
        }
        
        if not CAMELOT_AVAILABLE:
            logger.warning("Camelot not available - table extraction will be limited")
    
    def extract_tables_from_pdf(self, pdf_path: str, 
                               pages: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF using Camelot.
        
        Args:
            pdf_path: Path to PDF file
            pages: Page specification (e.g., '1-3,5', 'all')
            
        Returns:
            List of extracted tables with metadata
        """
        if not CAMELOT_AVAILABLE:
            logger.error("Camelot not available for table extraction")
            return self._fallback_table_extraction(pdf_path)
        
        logger.info(f"Extracting tables from {pdf_path} using Camelot {self.flavor}")
        
        try:
            # Extract tables with Camelot
            tables = camelot.read_pdf(
                pdf_path,
                pages=pages or 'all',
                flavor=self.flavor,
                strip_text='\n'
            )
            
            extracted_tables = []
            for i, table in enumerate(tables):
                # Get table metadata
                table_data = self._process_camelot_table(table, i + 1)
                
                # Only include tables above confidence threshold
                if table_data['confidence'] >= self.confidence_threshold:
                    extracted_tables.append(table_data)
                    logger.info(f"Table {i+1}: {table_data['rows']}x{table_data['cols']} "
                              f"(confidence: {table_data['confidence']:.3f})")
                else:
                    logger.debug(f"Table {i+1} below confidence threshold: "
                               f"{table_data['confidence']:.3f}")
            
            logger.info(f"Extracted {len(extracted_tables)} high-confidence tables")
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Camelot table extraction failed: {e}")
            return self._fallback_table_extraction(pdf_path)
    
    def _process_camelot_table(self, table, table_index: int) -> Dict[str, Any]:
        """Process a single Camelot table object."""
        df = table.df
        
        # Basic table information
        table_data = {
            'table_id': table_index,
            'page': table.page,
            'rows': len(df),
            'cols': len(df.columns),
            'confidence': table.accuracy,
            'raw_data': df.values.tolist(),
            'headers': df.iloc[0].tolist() if len(df) > 0 else [],
            'data_rows': df.iloc[1:].values.tolist() if len(df) > 1 else []
        }
        
        # Enhanced metadata for legal documents
        table_data.update(self._analyze_table_content(df))
        
        return table_data
    
    def _analyze_table_content(self, df: 'pd.DataFrame') -> Dict[str, Any]:
        """Analyze table content for legal document patterns."""
        analysis = {
            'contains_numerals': False,
            'contains_amounts': False,
            'contains_roles': False,
            'numeral_patterns': [],
            'extracted_amounts': [],
            'detected_roles': [],
            'table_type': 'unknown',
            'context_score': 0.0
        }
        
        if df.empty:
            return analysis
        
        # Convert entire table to text for pattern analysis
        table_text = ' '.join([
            ' '.join([str(cell) for cell in row])
            for row in df.values
        ]).lower()
        
        # Detect numerals
        numerals_found = []
        for pattern_name, pattern in self.numeral_patterns.items():
            matches = pattern.findall(table_text)
            if matches:
                analysis['contains_numerals'] = True
                numerals_found.extend([(pattern_name, match) for match in matches])
        
        analysis['numeral_patterns'] = numerals_found
        
        # Detect amounts
        amounts_found = []
        for pattern_name, pattern in self.amount_patterns.items():
            matches = pattern.findall(table_text)
            if matches:
                analysis['contains_amounts'] = True
                amounts_found.extend([(pattern_name, match) for match in matches])
        
        analysis['extracted_amounts'] = amounts_found
        
        # Detect roles
        roles_found = []
        for role_category, keywords in self.context_keywords.items():
            for keyword in keywords:
                if keyword in table_text:
                    if role_category == 'roles':
                        analysis['contains_roles'] = True
                        roles_found.append(keyword)
        
        analysis['detected_roles'] = roles_found
        
        # Determine table type based on content
        analysis['table_type'] = self._classify_table_type(analysis)
        
        # Calculate context score
        analysis['context_score'] = self._calculate_context_score(analysis)
        
        return analysis
    
    def _classify_table_type(self, analysis: Dict[str, Any]) -> str:
        """Classify table type based on content analysis."""
        if analysis['contains_amounts'] and analysis['contains_roles']:
            return 'viaticos_scale'  # Escala de viáticos
        elif analysis['contains_numerals'] and analysis['contains_amounts']:
            return 'regulation_amounts'  # Montos regulatorios
        elif analysis['contains_numerals']:
            return 'regulatory_structure'  # Estructura normativa
        elif analysis['contains_amounts']:
            return 'financial_data'  # Datos financieros
        else:
            return 'general_content'
    
    def _calculate_context_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate relevance score for legal document context."""
        score = 0.0
        
        # Base score for having structured content
        if analysis['contains_numerals']:
            score += 0.3
        if analysis['contains_amounts']:
            score += 0.4
        if analysis['contains_roles']:
            score += 0.2
        
        # Bonus for specific patterns
        critical_numerals = ['8.4', '8.4.17', '7.5', '8.5']
        for _, numeral in analysis['numeral_patterns']:
            if numeral in critical_numerals:
                score += 0.1
        
        # Bonus for known amounts
        critical_amounts = ['30.00', '320.00', '380.00']
        for _, amount in analysis['extracted_amounts']:
            if any(crit in amount for crit in critical_amounts):
                score += 0.1
        
        return min(score, 1.0)
    
    def create_hybrid_chunks_from_tables(self, 
                                       tables: List[Dict[str, Any]],
                                       preserve_hierarchy: bool = True) -> List[Dict[str, Any]]:
        """
        Create hybrid chunks from extracted tables that preserve numeral-content relationships.
        
        Args:
            tables: Extracted tables from Camelot
            preserve_hierarchy: Whether to maintain hierarchical relationships
            
        Returns:
            List of chunks with enriched metadata
        """
        chunks = []
        
        for table in tables:
            if table['context_score'] < 0.3:
                continue  # Skip low-relevance tables
            
            # Create table-level chunk
            table_chunk = self._create_table_chunk(table)
            chunks.append(table_chunk)
            
            # Create numeral-specific chunks if requested
            if preserve_hierarchy and table['contains_numerals']:
                numeral_chunks = self._create_numeral_chunks(table)
                chunks.extend(numeral_chunks)
        
        return chunks
    
    def _create_table_chunk(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chunk from table-level information."""
        # Generate table description
        table_text = self._generate_table_text(table)
        
        # Extract key entities
        entities = {
            'amounts': [amount[1] for amount in table['extracted_amounts']],
            'numerals': [num[1] for num in table['numeral_patterns']],
            'roles': table['detected_roles'],
            'table_type': table['table_type']
        }
        
        # Create chunk
        chunk = {
            'id': f"table_{table['table_id']}",
            'texto': table_text,
            'titulo': f"Tabla {table['table_id']} - {table['table_type'].replace('_', ' ').title()}",
            'metadatos': {
                'source': 'camelot_table_extraction',
                'page': table['page'],
                'table_info': {
                    'rows': table['rows'],
                    'cols': table['cols'],
                    'confidence': table['confidence'],
                    'type': table['table_type']
                },
                'entities': entities,
                'context_score': table['context_score'],
                'contains_numerals': table['contains_numerals'],
                'contains_amounts': table['contains_amounts'],
                'hierarchy_level': 0,  # Table level
                'extraction_method': 'camelot_hybrid_chunking'
            }
        }
        
        return chunk
    
    def _create_numeral_chunks(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks for specific numerals found in table."""
        chunks = []
        
        # Group numerals by hierarchy
        numeral_groups = {}
        for pattern_name, numeral in table['numeral_patterns']:
            level = numeral.count('.') + 1
            if level not in numeral_groups:
                numeral_groups[level] = []
            numeral_groups[level].append((pattern_name, numeral))
        
        # Create chunks for each numeral
        for level, numerals in numeral_groups.items():
            for pattern_name, numeral in numerals:
                chunk = self._create_numeral_specific_chunk(
                    table, numeral, pattern_name, level
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_numeral_specific_chunk(self, 
                                     table: Dict[str, Any], 
                                     numeral: str, 
                                     pattern_name: str, 
                                     level: int) -> Dict[str, Any]:
        """Create a chunk specific to a numeral."""
        # Find context around this numeral in the table
        context_text = self._extract_numeral_context(table, numeral)
        
        # Extract related amounts
        related_amounts = self._find_amounts_near_numeral(table, numeral)
        
        chunk = {
            'id': f"numeral_{numeral.replace('.', '_')}",
            'texto': context_text,
            'titulo': f"Numeral {numeral}",
            'metadatos': {
                'source': 'camelot_numeral_extraction',
                'page': table['page'],
                'numeral_info': {
                    'number': numeral,
                    'pattern_type': pattern_name,
                    'hierarchy_level': level,
                    'parent_numeral': self._find_parent_numeral(numeral)
                },
                'entities': {
                    'amounts': related_amounts,
                    'numerals': [numeral],
                    'primary_numeral': numeral
                },
                'table_reference': table['table_id'],
                'context_score': table['context_score'],
                'extraction_method': 'camelot_numeral_specific'
            }
        }
        
        return chunk
    
    def _generate_table_text(self, table: Dict[str, Any]) -> str:
        """Generate readable text from table data."""
        if not table['data_rows']:
            return f"Tabla {table['table_id']} (vacía)"
        
        # Create readable table representation
        text_parts = []
        
        # Add headers if available
        if table['headers']:
            headers = [str(h).strip() for h in table['headers'] if str(h).strip()]
            if headers:
                text_parts.append(f"Columnas: {' | '.join(headers)}")
        
        # Add data rows
        for i, row in enumerate(table['data_rows'][:5]):  # Limit to first 5 rows
            row_data = [str(cell).strip() for cell in row if str(cell).strip()]
            if row_data:
                text_parts.append(f"Fila {i+1}: {' | '.join(row_data)}")
        
        if len(table['data_rows']) > 5:
            text_parts.append(f"... y {len(table['data_rows']) - 5} filas más")
        
        # Add summary
        summary = []
        if table['contains_amounts']:
            amounts = [a[1] for a in table['extracted_amounts']]
            summary.append(f"Montos: {', '.join(amounts[:3])}")
        
        if table['contains_numerals']:
            numerals = [n[1] for n in table['numeral_patterns']]
            summary.append(f"Numerales: {', '.join(numerals[:3])}")
        
        if summary:
            text_parts.append(f"Contenido clave: {' | '.join(summary)}")
        
        return '\n'.join(text_parts)
    
    def _extract_numeral_context(self, table: Dict[str, Any], numeral: str) -> str:
        """Extract context around a specific numeral."""
        # Search for the numeral in table data
        context_parts = []
        
        for i, row in enumerate(table['data_rows']):
            for j, cell in enumerate(row):
                cell_text = str(cell).strip()
                if numeral in cell_text:
                    context_parts.append(f"Numeral {numeral}: {cell_text}")
                    
                    # Add adjacent cells for context
                    if j + 1 < len(row):
                        next_cell = str(row[j + 1]).strip()
                        if next_cell:
                            context_parts.append(f"Contenido: {next_cell}")
        
        if not context_parts:
            context_parts.append(f"Numeral {numeral} identificado en tabla {table['table_id']}")
        
        return '\n'.join(context_parts)
    
    def _find_amounts_near_numeral(self, table: Dict[str, Any], numeral: str) -> List[str]:
        """Find amounts that appear near a specific numeral."""
        amounts = []
        
        # Search in same rows as the numeral
        for row in table['data_rows']:
            row_text = ' '.join([str(cell) for cell in row])
            if numeral in row_text:
                # Extract amounts from this row
                for pattern_name, pattern in self.amount_patterns.items():
                    matches = pattern.findall(row_text)
                    amounts.extend(matches)
        
        return list(set(amounts))  # Remove duplicates
    
    def _find_parent_numeral(self, numeral: str) -> Optional[str]:
        """Find parent numeral in hierarchy."""
        parts = numeral.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return None
    
    def _fallback_table_extraction(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Fallback table extraction when Camelot is not available."""
        logger.warning("Using fallback table extraction - install Camelot for better results")
        
        # Simple pattern-based extraction from filename/path
        return [{
            'table_id': 1,
            'page': 1,
            'rows': 0,
            'cols': 0,
            'confidence': 0.5,
            'raw_data': [],
            'headers': [],
            'data_rows': [],
            'contains_numerals': False,
            'contains_amounts': False,
            'table_type': 'fallback_extraction',
            'context_score': 0.3,
            'extraction_method': 'fallback'
        }]
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics and capabilities."""
        return {
            'camelot_available': CAMELOT_AVAILABLE,
            'cv2_available': CV2_AVAILABLE,
            'flavor': self.flavor,
            'confidence_threshold': self.confidence_threshold,
            'preserve_numerals': self.preserve_numerals,
            'supported_formats': ['PDF'] if CAMELOT_AVAILABLE else [],
            'numeral_patterns': list(self.numeral_patterns.keys()),
            'amount_patterns': list(self.amount_patterns.keys())
        }


def create_table_extractor(flavor: str = 'lattice', 
                          confidence_threshold: float = 0.8) -> CamelotTableExtractor:
    """Factory function to create a table extractor."""
    return CamelotTableExtractor(
        flavor=flavor,
        confidence_threshold=confidence_threshold,
        preserve_numerals=True
    )
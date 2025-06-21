#!/usr/bin/env python3
"""
Hybrid Chunker with Numeral-Content Preservation
================================================

Advanced chunking system that maintains numeral-content relationships,
integrates table data, and creates enriched metadata for legal documents.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

try:
    from ..extractors import CamelotTableExtractor, CAMELOT_EXTRACTOR_AVAILABLE
except ImportError:
    CAMELOT_EXTRACTOR_AVAILABLE = False
    CamelotTableExtractor = None

try:
    from ..validation import EntityValidator, DirectivaEntities, VALIDATION_AVAILABLE
except ImportError:
    VALIDATION_AVAILABLE = False
    EntityValidator = None

logger = logging.getLogger(__name__)


class HybridChunker:
    """
    Advanced chunker that preserves numeral-content relationships and
    integrates multiple data sources (OCR, tables, structured content).
    """
    
    def __init__(self, 
                 chunk_size: int = 500,
                 overlap: int = 50,
                 preserve_numerals: bool = True,
                 integrate_tables: bool = True):
        """
        Initialize hybrid chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
            preserve_numerals: Whether to preserve numeral-content relationships
            integrate_tables: Whether to integrate table extraction
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_numerals = preserve_numerals
        self.integrate_tables = integrate_tables
        
        # Initialize extractors
        self.table_extractor = None
        if CAMELOT_EXTRACTOR_AVAILABLE and integrate_tables:
            self.table_extractor = CamelotTableExtractor(
                confidence_threshold=0.7,
                preserve_numerals=True
            )
        
        self.entity_validator = None
        if VALIDATION_AVAILABLE:
            self.entity_validator = EntityValidator()
        
        # Numeral patterns optimized for legal documents
        self.numeral_patterns = {
            'main_section': re.compile(r'^(\d+)\.?\s+([A-ZÁÉÍÓÚ][^.\n]*)', re.MULTILINE),
            'subsection': re.compile(r'^(\d+\.\d+)\.?\s+([A-ZÁÉÍÓÚ][^.\n]*)', re.MULTILINE),
            'subsubsection': re.compile(r'^(\d+\.\d+\.\d+)\.?\s+([^.\n]*)', re.MULTILINE),
            'deep_section': re.compile(r'^(\d+\.\d+\.\d+\.\d+)\.?\s+([^.\n]*)', re.MULTILINE),
            'paragraph': re.compile(r'^([a-z]\))\s+([^.\n]*)', re.MULTILINE)
        }
        
        # Critical numerals for viáticos directive
        self.critical_numerals = {
            '8.4': 'VIÁTICOS',
            '8.4.17': 'Declaración Jurada',
            '8.5': 'Rendición de Cuentas',
            '7.5': 'Procedimientos Específicos',
            '8.1': 'Disposiciones Generales'
        }
        
        # Amount detection patterns
        self.amount_patterns = {
            'soles': re.compile(r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'percentage': re.compile(r'(\d{1,2}(?:\.\d+)?)%', re.IGNORECASE),
            'days': re.compile(r'(\d+)\s*días?\s+hábiles?', re.IGNORECASE)
        }
        
        # Role detection patterns
        self.role_patterns = {
            'minister': re.compile(r'ministros?\s+de\s+estado', re.IGNORECASE),
            'vice_minister': re.compile(r'viceministros?', re.IGNORECASE),
            'secretary': re.compile(r'secretarios?\s+generales?', re.IGNORECASE),
            'civil_servant': re.compile(r'servidores?\s+(?:públicos?|civiles?)', re.IGNORECASE),
            'trust_official': re.compile(r'funcionarios?\s+de\s+confianza', re.IGNORECASE)
        }
        
        logger.info(f"HybridChunker initialized - Tables: {CAMELOT_EXTRACTOR_AVAILABLE}, "
                   f"Validation: {VALIDATION_AVAILABLE}")
    
    def create_hybrid_chunks(self, 
                           content: Dict[str, Any],
                           pdf_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Create hybrid chunks from multiple content sources.
        
        Args:
            content: Structured content from pipeline (OCR, layout, etc.)
            pdf_path: Optional PDF path for table extraction
            
        Returns:
            List of enriched chunks with preserved relationships
        """
        logger.info("Creating hybrid chunks with numeral preservation")
        
        chunks = []
        
        # Step 1: Extract tables if PDF is available
        table_chunks = []
        if pdf_path and self.table_extractor:
            table_chunks = self._extract_table_chunks(pdf_path)
            logger.info(f"Extracted {len(table_chunks)} table chunks")
        
        # Step 2: Process structured text content
        text_chunks = self._create_text_chunks(content)
        logger.info(f"Created {len(text_chunks)} text chunks")
        
        # Step 3: Create numeral-specific chunks
        numeral_chunks = []
        if self.preserve_numerals:
            numeral_chunks = self._create_numeral_chunks(content, table_chunks)
            logger.info(f"Created {len(numeral_chunks)} numeral-specific chunks")
        
        # Step 4: Combine and enrich all chunks
        all_chunks = table_chunks + text_chunks + numeral_chunks
        enriched_chunks = self._enrich_chunk_metadata(all_chunks)
        
        # Step 5: Validate and filter chunks
        final_chunks = self._validate_and_filter_chunks(enriched_chunks)
        
        logger.info(f"Final hybrid chunks: {len(final_chunks)}")
        return final_chunks
    
    def _extract_table_chunks(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract chunks from PDF tables using Camelot."""
        if not self.table_extractor:
            return []
        
        try:
            # Extract tables
            tables = self.table_extractor.extract_tables_from_pdf(pdf_path)
            
            # Create chunks from tables
            table_chunks = self.table_extractor.create_hybrid_chunks_from_tables(
                tables, preserve_hierarchy=True
            )
            
            return table_chunks
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []
    
    def _create_text_chunks(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks from structured text content."""
        chunks = []
        
        # Process sections if available
        sections = content.get('sections', [])
        for section in sections:
            section_chunks = self._process_section(section)
            chunks.extend(section_chunks)
        
        # Process raw text if no sections
        if not sections and 'text' in content:
            text_chunks = self._chunk_raw_text(content['text'])
            chunks.extend(text_chunks)
        
        return chunks
    
    def _process_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single section into chunks."""
        chunks = []
        
        section_text = section.get('text_content', '')
        section_number = section.get('number', 'unknown')
        section_title = section.get('title', '')
        
        # Create section-level chunk
        section_chunk = {
            'id': f"section_{section_number}",
            'texto': section_text,
            'titulo': f"{section_number} {section_title}".strip(),
            'metadatos': {
                'source': 'hybrid_section_processing',
                'section_info': {
                    'number': section_number,
                    'title': section_title,
                    'level': section.get('level', 1)
                },
                'entities': self._extract_entities_from_text(section_text),
                'chunk_type': 'section',
                'extraction_method': 'hybrid_chunking'
            }
        }
        
        chunks.append(section_chunk)
        
        # Create sub-chunks for long sections
        if len(section_text) > self.chunk_size * 2:
            sub_chunks = self._create_sub_chunks(section_text, section_number)
            chunks.extend(sub_chunks)
        
        return chunks
    
    def _create_numeral_chunks(self, 
                             content: Dict[str, Any],
                             table_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create chunks specifically for numerals with preserved context."""
        chunks = []
        
        # Get all text content
        all_text = self._extract_all_text(content)
        
        # Find all numerals with context
        numerals_found = self._find_numerals_with_context(all_text)
        
        # Create chunks for critical numerals
        for numeral_info in numerals_found:
            if self._is_critical_numeral(numeral_info['numeral']):
                chunk = self._create_critical_numeral_chunk(
                    numeral_info, table_chunks
                )
                chunks.append(chunk)
        
        return chunks
    
    def _find_numerals_with_context(self, text: str) -> List[Dict[str, Any]]:
        """Find numerals in text with their context."""
        numerals_found = []
        
        for pattern_name, pattern in self.numeral_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                numeral = match.group(1)
                title = match.group(2) if len(match.groups()) > 1 else ''
                
                # Extract context around the numeral
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 500)
                context = text[start:end].strip()
                
                numeral_info = {
                    'numeral': numeral,
                    'title': title.strip(),
                    'pattern_type': pattern_name,
                    'context': context,
                    'position': match.start(),
                    'level': numeral.count('.') + 1
                }
                
                numerals_found.append(numeral_info)
        
        return numerals_found
    
    def _is_critical_numeral(self, numeral: str) -> bool:
        """Check if numeral is in critical list."""
        return numeral in self.critical_numerals
    
    def _create_critical_numeral_chunk(self, 
                                     numeral_info: Dict[str, Any],
                                     table_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a chunk for a critical numeral with enhanced metadata."""
        numeral = numeral_info['numeral']
        
        # Find related table information
        related_tables = self._find_related_tables(numeral, table_chunks)
        
        # Extract entities from context
        entities = self._extract_entities_from_text(numeral_info['context'])
        
        # Get known information for this numeral
        known_info = self.critical_numerals.get(numeral, '')
        
        # Enhanced text with context
        enhanced_text = f"Numeral {numeral}: {numeral_info['title']}\n\n"
        enhanced_text += f"{numeral_info['context']}\n"
        
        if related_tables:
            enhanced_text += f"\nTablas relacionadas: {len(related_tables)}"
        
        chunk = {
            'id': f"critical_numeral_{numeral.replace('.', '_')}",
            'texto': enhanced_text,
            'titulo': f"Numeral {numeral} - {known_info or numeral_info['title']}",
            'metadatos': {
                'source': 'hybrid_critical_numeral',
                'numeral_info': {
                    'number': numeral,
                    'title': numeral_info['title'],
                    'known_subject': known_info,
                    'hierarchy_level': numeral_info['level'],
                    'parent_numeral': self._get_parent_numeral(numeral),
                    'pattern_type': numeral_info['pattern_type']
                },
                'entities': entities,
                'related_tables': [t['id'] for t in related_tables],
                'context_length': len(numeral_info['context']),
                'chunk_type': 'critical_numeral',
                'priority': 'high',
                'extraction_method': 'hybrid_numeral_preservation'
            }
        }
        
        return chunk
    
    def _extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using patterns."""
        entities = {
            'amounts': [],
            'roles': [],
            'procedures': [],
            'references': []
        }
        
        # Extract amounts
        for pattern_name, pattern in self.amount_patterns.items():
            matches = pattern.findall(text)
            entities['amounts'].extend(matches)
        
        # Extract roles
        for role_type, pattern in self.role_patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities['roles'].extend([role_type] * len(matches))
        
        # Extract procedures (simplified)
        procedure_keywords = ['declaración jurada', 'rendición', 'comprobante', 'solicitud']
        for keyword in procedure_keywords:
            if keyword.lower() in text.lower():
                entities['procedures'].append(keyword)
        
        return entities
    
    def _find_related_tables(self, 
                           numeral: str, 
                           table_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find table chunks related to a specific numeral."""
        related = []
        
        for table_chunk in table_chunks:
            # Check if numeral appears in table
            table_text = table_chunk.get('texto', '').lower()
            if numeral in table_text:
                related.append(table_chunk)
                continue
            
            # Check table metadata
            entities = table_chunk.get('metadatos', {}).get('entities', {})
            if numeral in entities.get('numerals', []):
                related.append(table_chunk)
        
        return related
    
    def _get_parent_numeral(self, numeral: str) -> Optional[str]:
        """Get parent numeral in hierarchy."""
        parts = numeral.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return None
    
    def _chunk_raw_text(self, text: str) -> List[Dict[str, Any]]:
        """Create chunks from raw text when no structure is available."""
        chunks = []
        
        # Split text into chunks
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= self.chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunk = {
                    'id': f"raw_chunk_{len(chunks) + 1}",
                    'texto': chunk_text,
                    'titulo': f"Contenido {len(chunks) + 1}",
                    'metadatos': {
                        'source': 'hybrid_raw_chunking',
                        'chunk_type': 'raw_text',
                        'entities': self._extract_entities_from_text(chunk_text),
                        'extraction_method': 'hybrid_chunking'
                    }
                }
                chunks.append(chunk)
                
                # Keep overlap
                overlap_words = current_chunk[-self.overlap//10:]
                current_chunk = overlap_words
                current_size = sum(len(w) + 1 for w in overlap_words)
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = {
                'id': f"raw_chunk_{len(chunks) + 1}",
                'texto': chunk_text,
                'titulo': f"Contenido {len(chunks) + 1}",
                'metadatos': {
                    'source': 'hybrid_raw_chunking',
                    'chunk_type': 'raw_text',
                    'entities': self._extract_entities_from_text(chunk_text),
                    'extraction_method': 'hybrid_chunking'
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _create_sub_chunks(self, text: str, section_number: str) -> List[Dict[str, Any]]:
        """Create sub-chunks for long sections."""
        chunks = []
        
        # Split by sentences
        sentences = re.split(r'[.!?]+', text)
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            current_chunk.append(sentence)
            current_size += len(sentence)
            
            if current_size >= self.chunk_size:
                chunk_text = '. '.join(current_chunk) + '.'
                chunk = {
                    'id': f"subsection_{section_number}_{len(chunks) + 1}",
                    'texto': chunk_text,
                    'titulo': f"Sección {section_number} - Parte {len(chunks) + 1}",
                    'metadatos': {
                        'source': 'hybrid_subsection_chunking',
                        'parent_section': section_number,
                        'chunk_type': 'subsection',
                        'entities': self._extract_entities_from_text(chunk_text),
                        'extraction_method': 'hybrid_chunking'
                    }
                }
                chunks.append(chunk)
                
                # Reset with overlap
                current_chunk = current_chunk[-1:] if current_chunk else []
                current_size = len(current_chunk[0]) if current_chunk else 0
        
        return chunks
    
    def _extract_all_text(self, content: Dict[str, Any]) -> str:
        """Extract all text from structured content."""
        text_parts = []
        
        # Extract from sections
        for section in content.get('sections', []):
            text_parts.append(section.get('text_content', ''))
        
        # Extract from raw text
        if 'text' in content:
            text_parts.append(content['text'])
        
        return '\n'.join(text_parts)
    
    def _enrich_chunk_metadata(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich chunk metadata with additional analysis."""
        enriched_chunks = []
        
        for chunk in chunks:
            # Add validation results if available
            if self.entity_validator:
                try:
                    validation = self.entity_validator.validate_entities(
                        chunk.get('texto', ''), confidence_threshold=0.7
                    )
                    chunk['metadatos']['validation_results'] = {
                        'amounts_count': len(validation.amounts),
                        'roles_count': len(validation.roles),
                        'numerals_count': len(validation.numerals),
                        'overall_confidence': validation.overall_confidence
                    }
                except Exception as e:
                    logger.debug(f"Validation failed for chunk {chunk.get('id')}: {e}")
            
            # Add content analysis
            chunk['metadatos']['content_analysis'] = self._analyze_chunk_content(chunk)
            
            # Add relationship information
            chunk['metadatos']['relationships'] = self._find_chunk_relationships(chunk, chunks)
            
            enriched_chunks.append(chunk)
        
        return enriched_chunks
    
    def _analyze_chunk_content(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chunk content for classification and scoring."""
        text = chunk.get('texto', '')
        
        analysis = {
            'length': len(text),
            'word_count': len(text.split()),
            'contains_amounts': bool(self.amount_patterns['soles'].search(text)),
            'contains_roles': any(pattern.search(text) for pattern in self.role_patterns.values()),
            'contains_numerals': bool(re.search(r'\d+\.\d+', text)),
            'relevance_score': 0.0
        }
        
        # Calculate relevance score
        score = 0.0
        if analysis['contains_amounts']:
            score += 0.4
        if analysis['contains_roles']:
            score += 0.3
        if analysis['contains_numerals']:
            score += 0.2
        if 'viático' in text.lower():
            score += 0.1
        
        analysis['relevance_score'] = min(score, 1.0)
        
        return analysis
    
    def _find_chunk_relationships(self, 
                                chunk: Dict[str, Any], 
                                all_chunks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Find relationships between chunks."""
        relationships = {
            'references_to': [],
            'referenced_by': [],
            'related_numerals': [],
            'shared_entities': []
        }
        
        chunk_id = chunk.get('id')
        chunk_entities = chunk.get('metadatos', {}).get('entities', {})
        
        for other_chunk in all_chunks:
            if other_chunk.get('id') == chunk_id:
                continue
            
            # Check for entity overlap
            other_entities = other_chunk.get('metadatos', {}).get('entities', {})
            
            # Check amounts overlap
            chunk_amounts = set(chunk_entities.get('amounts', []))
            other_amounts = set(other_entities.get('amounts', []))
            if chunk_amounts & other_amounts:
                relationships['shared_entities'].append(other_chunk['id'])
        
        return relationships
    
    def _validate_and_filter_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter chunks based on quality criteria."""
        filtered_chunks = []
        
        for chunk in chunks:
            # Quality checks
            if self._is_valid_chunk(chunk):
                filtered_chunks.append(chunk)
            else:
                logger.debug(f"Filtered out low-quality chunk: {chunk.get('id')}")
        
        # Remove duplicates
        unique_chunks = self._remove_duplicate_chunks(filtered_chunks)
        
        # Sort by relevance
        unique_chunks.sort(
            key=lambda x: x.get('metadatos', {}).get('content_analysis', {}).get('relevance_score', 0),
            reverse=True
        )
        
        return unique_chunks
    
    def _is_valid_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Check if chunk meets quality criteria."""
        text = chunk.get('texto', '')
        
        # Minimum length
        if len(text.strip()) < 20:
            return False
        
        # Must contain meaningful content
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', text):
            return False
        
        # Check relevance score
        analysis = chunk.get('metadatos', {}).get('content_analysis', {})
        if analysis.get('relevance_score', 0) < 0.1:
            return False
        
        return True
    
    def _remove_duplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate chunks based on text similarity."""
        unique_chunks = []
        seen_texts = set()
        
        for chunk in chunks:
            text = chunk.get('texto', '').strip()
            
            # Simple deduplication based on text length and first 100 chars
            text_signature = f"{len(text)}_{text[:100]}"
            
            if text_signature not in seen_texts:
                seen_texts.add(text_signature)
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def get_chunking_stats(self) -> Dict[str, Any]:
        """Get chunking statistics and configuration."""
        return {
            'chunk_size': self.chunk_size,
            'overlap': self.overlap,
            'preserve_numerals': self.preserve_numerals,
            'integrate_tables': self.integrate_tables,
            'table_extractor_available': CAMELOT_EXTRACTOR_AVAILABLE,
            'entity_validator_available': VALIDATION_AVAILABLE,
            'critical_numerals': list(self.critical_numerals.keys()),
            'supported_patterns': list(self.numeral_patterns.keys())
        }
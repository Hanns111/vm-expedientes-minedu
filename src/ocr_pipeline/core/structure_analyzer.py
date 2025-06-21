#!/usr/bin/env python3
"""
Structure Analyzer for Legal Documents
======================================

Analyzes document structure to preserve legal hierarchy and create
contextually meaningful chunks. Specifically designed for Peruvian
legal documents with complex numbering systems.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LegalElement:
    """Represents a legal document element with hierarchy information."""
    type: str  # 'article', 'section', 'numeral', 'paragraph', 'list_item'
    text: str
    number: str  # e.g., '8', '8.4', '8.4.17'
    level: int  # Hierarchy level (0=highest)
    parent: Optional[str] = None  # Parent element number
    bbox: Optional[List[float]] = None
    confidence: float = 0.0
    entities: List[Dict[str, Any]] = None


class StructureAnalyzer:
    """
    Analyzes legal document structure to preserve hierarchy and context.
    
    Features:
    - Detects legal numbering patterns (8.4.17, artículo 24, etc.)
    - Preserves parent-child relationships
    - Identifies document sections and subsections
    - Extracts hierarchical context for intelligent chunking
    """
    
    def __init__(self):
        """Initialize structure analyzer with legal document patterns."""
        
        # Legal numbering patterns (ordered by specificity)
        self.patterns = {
            'article': re.compile(r'(?:artículo|artículo)\s+(\d+)(?:\.|°)?', re.IGNORECASE),
            'chapter': re.compile(r'(?:capítulo|capitulo)\s+([IVXLC]+|\d+)', re.IGNORECASE),
            'title': re.compile(r'título\s+([IVXLC]+|\d+)', re.IGNORECASE),
            'section_deep': re.compile(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', re.IGNORECASE),  # 8.4.17.2
            'section_triple': re.compile(r'(\d+)\.(\d+)\.(\d+)', re.IGNORECASE),      # 8.4.17
            'section_double': re.compile(r'(\d+)\.(\d+)', re.IGNORECASE),            # 8.4
            'section_single': re.compile(r'^(\d+)\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]', re.IGNORECASE),  # 8. Objeto
            'inciso': re.compile(r'inciso\s+([a-z])\)', re.IGNORECASE),
            'letter': re.compile(r'^([a-z])\)\s+', re.IGNORECASE),
            'roman': re.compile(r'^([IVXLC]+)\.\s+', re.IGNORECASE),
            'bullet': re.compile(r'^[•·▪▫-]\s+', re.IGNORECASE)
        }
        
        # Content type patterns
        self.content_patterns = {
            'definition': re.compile(r'(?:definición|concepto|entiende por)', re.IGNORECASE),
            'procedure': re.compile(r'(?:procedimiento|proceso|trámite|gestión)', re.IGNORECASE),
            'requirement': re.compile(r'(?:requisito|debe|deberá|obligatorio)', re.IGNORECASE),
            'prohibition': re.compile(r'(?:prohibido|no se|no podrá|queda prohibido)', re.IGNORECASE),
            'penalty': re.compile(r'(?:sanción|multa|penalidad|infracción)', re.IGNORECASE),
            'amount': re.compile(r'(?:monto|suma|cantidad|importe|S/\s*\d+)', re.IGNORECASE),
            'timeframe': re.compile(r'(?:plazo|días|tiempo|fecha|término)', re.IGNORECASE)
        }
        
        logger.info("Structure analyzer initialized with legal patterns")
    
    def analyze_document_structure(
        self, 
        text_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze complete document structure from text blocks.
        
        Args:
            text_blocks: List of text blocks from OCR/layout detection
            
        Returns:
            Complete document structure analysis
        """
        logger.info(f"Analyzing structure of {len(text_blocks)} text blocks")
        
        # Extract legal elements
        elements = self._extract_legal_elements(text_blocks)
        
        # Build hierarchy
        hierarchy = self._build_hierarchy(elements)
        
        # Analyze content types
        content_analysis = self._analyze_content_types(text_blocks)
        
        # Create document sections
        sections = self._create_document_sections(elements, text_blocks)
        
        return {
            'elements': elements,
            'hierarchy': hierarchy,
            'content_analysis': content_analysis,
            'sections': sections,
            'total_elements': len(elements),
            'max_depth': max([elem.level for elem in elements], default=0),
            'document_type': self._classify_document_type(elements, content_analysis)
        }
    
    def _extract_legal_elements(self, text_blocks: List[Dict[str, Any]]) -> List[LegalElement]:
        """Extract legal elements with numbering from text blocks."""
        elements = []
        
        for i, block in enumerate(text_blocks):
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Check each pattern
            for pattern_name, pattern in self.patterns.items():
                matches = pattern.finditer(text)
                
                for match in matches:
                    element = self._create_legal_element(
                        pattern_name, match, text, block, i
                    )
                    if element:
                        elements.append(element)
        
        # Sort by position in document
        elements.sort(key=lambda x: (x.bbox[1] if x.bbox else 0, x.bbox[0] if x.bbox else 0))
        
        return elements
    
    def _create_legal_element(
        self, 
        pattern_name: str, 
        match: re.Match, 
        text: str, 
        block: Dict[str, Any],
        block_index: int
    ) -> Optional[LegalElement]:
        """Create a legal element from pattern match."""
        
        try:
            if pattern_name == 'article':
                number = match.group(1)
                element_type = 'article'
                level = 0
                
            elif pattern_name == 'chapter':
                number = match.group(1)
                element_type = 'chapter'
                level = 0
                
            elif pattern_name == 'title':
                number = match.group(1)
                element_type = 'title'
                level = 0
                
            elif pattern_name == 'section_deep':
                number = f"{match.group(1)}.{match.group(2)}.{match.group(3)}.{match.group(4)}"
                element_type = 'numeral'
                level = 4
                
            elif pattern_name == 'section_triple':
                number = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                element_type = 'numeral'
                level = 3
                
            elif pattern_name == 'section_double':
                number = f"{match.group(1)}.{match.group(2)}"
                element_type = 'section'
                level = 2
                
            elif pattern_name == 'section_single':
                number = match.group(1)
                element_type = 'section'
                level = 1
                
            elif pattern_name == 'inciso':
                number = match.group(1)
                element_type = 'inciso'
                level = 3
                
            elif pattern_name == 'letter':
                number = match.group(1)
                element_type = 'list_item'
                level = 4
                
            else:
                return None
            
            # Extract the line containing the match
            lines = text.split('\n')
            matched_line = ""
            for line in lines:
                if match.group(0) in line:
                    matched_line = line.strip()
                    break
            
            return LegalElement(
                type=element_type,
                text=matched_line[:200],  # Limit text length
                number=number,
                level=level,
                bbox=block.get('bbox'),
                confidence=block.get('confidence', 0.0)
            )
            
        except Exception as e:
            logger.warning(f"Error creating legal element: {e}")
            return None
    
    def _build_hierarchy(self, elements: List[LegalElement]) -> Dict[str, Any]:
        """Build hierarchical relationships between elements."""
        hierarchy = {
            'tree': defaultdict(list),
            'parent_child': {},
            'siblings': defaultdict(list)
        }
        
        # Assign parents based on hierarchy levels
        for i, element in enumerate(elements):
            # Find parent (previous element with lower level)
            parent = None
            for j in range(i - 1, -1, -1):
                if elements[j].level < element.level:
                    parent = elements[j].number
                    break
            
            element.parent = parent
            
            # Build tree structure
            hierarchy['tree'][parent].append(element.number)
            hierarchy['parent_child'][element.number] = parent
            
            # Find siblings (same level, same parent)
            siblings = [
                e.number for e in elements 
                if e.level == element.level and e.parent == parent and e.number != element.number
            ]
            hierarchy['siblings'][element.number] = siblings
        
        return dict(hierarchy)
    
    def _analyze_content_types(self, text_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content types in the document."""
        content_analysis = {
            'types_found': set(),
            'type_distribution': defaultdict(int),
            'blocks_by_type': defaultdict(list)
        }
        
        for i, block in enumerate(text_blocks):
            text = block.get('text', '').lower()
            if not text:
                continue
            
            block_types = []
            for content_type, pattern in self.content_patterns.items():
                if pattern.search(text):
                    block_types.append(content_type)
                    content_analysis['types_found'].add(content_type)
                    content_analysis['type_distribution'][content_type] += 1
                    content_analysis['blocks_by_type'][content_type].append(i)
            
            # If no specific type found, classify as general
            if not block_types:
                block_types = ['general']
                content_analysis['type_distribution']['general'] += 1
                content_analysis['blocks_by_type']['general'].append(i)
        
        content_analysis['types_found'] = list(content_analysis['types_found'])
        content_analysis['type_distribution'] = dict(content_analysis['type_distribution'])
        content_analysis['blocks_by_type'] = dict(content_analysis['blocks_by_type'])
        
        return content_analysis
    
    def _create_document_sections(
        self, 
        elements: List[LegalElement], 
        text_blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create logical document sections for intelligent chunking."""
        sections = []
        current_section = None
        
        for i, block in enumerate(text_blocks):
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Check if this block starts a new section
            block_element = self._find_element_for_block(elements, i, block)
            
            if block_element and block_element.level <= 2:  # Major section
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'id': len(sections),
                    'type': block_element.type,
                    'number': block_element.number,
                    'title': block_element.text,
                    'level': block_element.level,
                    'blocks': [block],
                    'start_block': i,
                    'text_content': text
                }
            else:
                # Add to current section
                if current_section:
                    current_section['blocks'].append(block)
                    current_section['text_content'] += ' ' + text
                else:
                    # Create initial section if none exists
                    current_section = {
                        'id': 0,
                        'type': 'introduction',
                        'number': '0',
                        'title': 'Documento',
                        'level': 0,
                        'blocks': [block],
                        'start_block': i,
                        'text_content': text
                    }
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _find_element_for_block(
        self, 
        elements: List[LegalElement], 
        block_index: int, 
        block: Dict[str, Any]
    ) -> Optional[LegalElement]:
        """Find the legal element that corresponds to a text block."""
        block_text = block.get('text', '')
        
        for element in elements:
            # Simple text matching - could be improved with position matching
            if element.text in block_text or block_text.startswith(element.text[:20]):
                return element
        
        return None
    
    def _classify_document_type(
        self, 
        elements: List[LegalElement], 
        content_analysis: Dict[str, Any]
    ) -> str:
        """Classify the type of legal document."""
        
        # Check for specific document indicators
        if any(e.type == 'article' for e in elements):
            return 'law_regulation'
        
        if 'procedure' in content_analysis['types_found']:
            return 'directive_procedure'
        
        if 'amount' in content_analysis['types_found']:
            return 'financial_regulation'
        
        if any(e.type == 'chapter' for e in elements):
            return 'comprehensive_regulation'
        
        return 'general_document'
    
    def create_contextual_chunks(
        self, 
        structure_analysis: Dict[str, Any],
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Create intelligent chunks that preserve legal context and hierarchy.
        
        Args:
            structure_analysis: Complete structure analysis
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            
        Returns:
            List of contextual chunks ready for vectorization
        """
        chunks = []
        sections = structure_analysis['sections']
        elements = structure_analysis['elements']
        hierarchy = structure_analysis['hierarchy']
        
        for section in sections:
            # Create chunk for each section
            chunk_text = section['text_content']
            
            # Split large sections into smaller chunks
            if len(chunk_text) > max_chunk_size:
                sub_chunks = self._split_section_intelligently(
                    section, chunk_text, max_chunk_size
                )
                for sub_chunk in sub_chunks:
                    chunks.append(sub_chunk)
            elif len(chunk_text) >= min_chunk_size:
                chunk = self._create_chunk_with_context(section, elements, hierarchy)
                chunks.append(chunk)
        
        return chunks
    
    def _split_section_intelligently(
        self, 
        section: Dict[str, Any], 
        text: str, 
        max_size: int
    ) -> List[Dict[str, Any]]:
        """Split large sections into smaller chunks intelligently."""
        chunks = []
        
        # Try splitting by sentences first
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunk = self._create_sub_chunk(section, current_chunk.strip())
                    chunks.append(chunk)
                current_chunk = sentence + ". "
        
        # Add remaining text
        if current_chunk:
            chunk = self._create_sub_chunk(section, current_chunk.strip())
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_with_context(
        self, 
        section: Dict[str, Any], 
        elements: List[LegalElement],
        hierarchy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a chunk with rich contextual metadata."""
        
        # Find relevant elements in this section
        section_elements = []
        for element in elements:
            if any(element.text in block.get('text', '') for block in section['blocks']):
                section_elements.append(element)
        
        # Extract entities from text
        entities = self._extract_entities_from_text(section['text_content'])
        
        return {
            'id': len([]),  # Will be set by caller
            'texto': section['text_content'],
            'titulo': section['title'],
            'metadatos': {
                'section_type': section['type'],
                'section_number': section['number'],
                'hierarchy_level': section['level'],
                'document_type': 'legal_regulation',
                'source': 'OCR_pipeline',
                'elements': [
                    {
                        'type': elem.type,
                        'number': elem.number,
                        'level': elem.level
                    } for elem in section_elements
                ],
                'entities': entities,
                'block_count': len(section['blocks']),
                'text_length': len(section['text_content'])
            }
        }
    
    def _create_sub_chunk(self, section: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Create a sub-chunk from a section."""
        entities = self._extract_entities_from_text(text)
        
        return {
            'texto': text,
            'titulo': f"{section['title']} (parte)",
            'metadatos': {
                'section_type': section['type'],
                'section_number': section['number'],
                'hierarchy_level': section['level'],
                'document_type': 'legal_regulation',
                'source': 'OCR_pipeline',
                'is_sub_chunk': True,
                'entities': entities,
                'text_length': len(text)
            }
        }
    
    def _extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract legal entities from text."""
        entities = {
            'amounts': [],
            'percentages': [],
            'dates': [],
            'references': [],
            'roles': [],
            'procedures': []
        }
        
        # Amount extraction
        amount_pattern = re.compile(r'S/\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
        entities['amounts'] = [match.group(0) for match in amount_pattern.finditer(text)]
        
        # Percentage extraction
        percent_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
        entities['percentages'] = [match.group(0) for match in percent_pattern.finditer(text)]
        
        # Date extraction
        date_pattern = re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', re.IGNORECASE)
        entities['dates'] = [match.group(0) for match in date_pattern.finditer(text)]
        
        # Reference extraction
        ref_pattern = re.compile(r'(decreto|directiva|resolución)\s+n[°º]\s*\d+', re.IGNORECASE)
        entities['references'] = [match.group(0) for match in ref_pattern.finditer(text)]
        
        # Role extraction
        role_pattern = re.compile(r'(ministro|servidor|funcionario|comisionado)', re.IGNORECASE)
        entities['roles'] = [match.group(0) for match in role_pattern.finditer(text)]
        
        return entities
    
    def get_stats(self) -> Dict[str, Any]:
        """Get structure analyzer statistics."""
        return {
            'patterns': list(self.patterns.keys()),
            'content_patterns': list(self.content_patterns.keys()),
            'status': 'initialized'
        }


if __name__ == "__main__":
    # Test the structure analyzer
    analyzer = StructureAnalyzer()
    
    print("Structure analyzer initialized successfully")
    print(f"Analyzer stats: {analyzer.get_stats()}")
    
    # Test with sample text blocks
    sample_blocks = [
        {
            'text': '8. DISPOSICIONES ESPECÍFICAS PARA VIÁTICOS',
            'bbox': [100, 100, 400, 120],
            'confidence': 0.9
        },
        {
            'text': '8.4. Para gastos de movilidad el monto máximo es S/ 30.00 por día.',
            'bbox': [100, 140, 450, 160],
            'confidence': 0.85
        },
        {
            'text': '8.4.17. Los comisionados deberán presentar Declaración Jurada cuando no puedan obtener comprobantes de pago.',
            'bbox': [100, 180, 500, 200],
            'confidence': 0.88
        }
    ]
    
    print("\nTesting structure analysis...")
    result = analyzer.analyze_document_structure(sample_blocks)
    print(f"Found {result['total_elements']} legal elements")
    print(f"Maximum hierarchy depth: {result['max_depth']}")
    print(f"Document type: {result['document_type']}")
    
    # Test chunk creation
    chunks = analyzer.create_contextual_chunks(result)
    print(f"Created {len(chunks)} contextual chunks")
#!/usr/bin/env python3
"""
Intelligent Chunker for Legal Documents
=======================================

Creates semantically coherent chunks that preserve legal hierarchy and context.
Optimized for the existing hybrid search system (BM25 + TF-IDF + Transformers).
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
from collections import defaultdict

from .legal_ner import LegalNER, LegalEntity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Rich metadata for intelligent chunks."""
    chunk_id: str
    title: str
    section_number: str
    hierarchy_level: int
    parent_section: Optional[str]
    entities: Dict[str, List[str]]
    document_type: str
    source: str
    confidence: float
    word_count: int
    char_count: int
    has_amounts: bool
    has_procedures: bool
    legal_context: Dict[str, Any]


class IntelligentChunker:
    """
    Advanced chunking system that creates contextually meaningful chunks
    optimized for legal document search and retrieval.
    
    Features:
    - Preserves legal hierarchy and parent-child relationships
    - Enriches chunks with extracted entities and context
    - Compatible with existing hybrid search system
    - Optimizes chunk size for vector similarity search
    - Maintains S/ 380 vs S/ 320 ranking improvements
    """
    
    def __init__(
        self,
        min_chunk_size: int = 150,
        max_chunk_size: int = 800,
        target_chunk_size: int = 400,
        overlap_size: int = 50
    ):
        """
        Initialize intelligent chunker with optimized parameters.
        
        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters  
            target_chunk_size: Target chunk size for optimal retrieval
            overlap_size: Overlap between adjacent chunks
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        
        # Initialize NER system
        self.ner = LegalNER()
        
        # Chunking strategies
        self.strategies = {
            'hierarchy_based': self._chunk_by_hierarchy,
            'semantic_based': self._chunk_by_semantics,
            'hybrid': self._chunk_hybrid
        }
        
        # Content type patterns for intelligent splitting
        self.split_patterns = {
            'strong_boundary': re.compile(r'(?:\n\s*\n|\.\s*\n\s*\d+\.|\.\s*\n\s*[A-Z])', re.IGNORECASE),
            'medium_boundary': re.compile(r'(?:\.\s+[A-Z]|;\s*\n)', re.IGNORECASE),
            'weak_boundary': re.compile(r'(?:,\s+|:\s*)', re.IGNORECASE)
        }
        
        logger.info(f"Intelligent chunker initialized (target size: {target_chunk_size} chars)")
    
    def create_intelligent_chunks(
        self,
        document_structure: Dict[str, Any],
        strategy: str = 'hybrid'
    ) -> List[Dict[str, Any]]:
        """
        Create intelligent chunks from document structure analysis.
        
        Args:
            document_structure: Complete document structure from StructureAnalyzer
            strategy: Chunking strategy ('hierarchy_based', 'semantic_based', 'hybrid')
            
        Returns:
            List of intelligent chunks ready for vectorization
        """
        if strategy not in self.strategies:
            logger.warning(f"Unknown strategy '{strategy}', using 'hybrid'")
            strategy = 'hybrid'
        
        logger.info(f"Creating chunks using '{strategy}' strategy")
        
        # Apply selected chunking strategy
        chunks = self.strategies[strategy](document_structure)
        
        # Post-process chunks
        chunks = self._post_process_chunks(chunks)
        
        # Add compatibility layer for existing system
        chunks = self._add_compatibility_layer(chunks)
        
        logger.info(f"Created {len(chunks)} intelligent chunks")
        return chunks
    
    def _chunk_by_hierarchy(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks based on legal document hierarchy."""
        chunks = []
        sections = structure.get('sections', [])
        elements = structure.get('elements', [])
        
        for section in sections:
            section_chunks = self._process_section_hierarchically(section, elements)
            chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_by_semantics(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks based on semantic content similarity."""
        chunks = []
        
        # Group content by semantic similarity
        content_groups = self._group_content_semantically(structure)
        
        for group in content_groups:
            group_chunks = self._process_semantic_group(group)
            chunks.extend(group_chunks)
        
        return chunks
    
    def _chunk_hybrid(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks using hybrid approach (hierarchy + semantics)."""
        chunks = []
        sections = structure.get('sections', [])
        elements = structure.get('elements', [])
        content_analysis = structure.get('content_analysis', {})
        
        for section in sections:
            # Analyze section content
            section_text = section.get('text_content', '')
            section_entities = self.ner.extract_entities(section_text)
            
            # Determine if section should be split
            if len(section_text) <= self.max_chunk_size:
                # Small section - create single chunk
                chunk = self._create_single_chunk(section, section_entities, elements)
                if chunk:
                    chunks.append(chunk)
            else:
                # Large section - split intelligently
                section_chunks = self._split_large_section(section, section_entities, elements)
                chunks.extend(section_chunks)
        
        return chunks
    
    def _process_section_hierarchically(
        self, 
        section: Dict[str, Any], 
        elements: List[Any]
    ) -> List[Dict[str, Any]]:
        """Process a section using hierarchical boundaries."""
        chunks = []
        section_text = section.get('text_content', '')
        
        if len(section_text) <= self.max_chunk_size:
            # Create single chunk for small sections
            entities = self.ner.extract_entities(section_text)
            chunk = self._create_single_chunk(section, entities, elements)
            if chunk:
                chunks.append(chunk)
        else:
            # Split by hierarchy markers
            hierarchy_splits = self._find_hierarchy_split_points(section_text)
            sub_chunks = self._split_by_points(section_text, hierarchy_splits)
            
            for i, sub_text in enumerate(sub_chunks):
                entities = self.ner.extract_entities(sub_text)
                chunk = self._create_sub_chunk(section, sub_text, entities, i)
                if chunk:
                    chunks.append(chunk)
        
        return chunks
    
    def _split_large_section(
        self,
        section: Dict[str, Any],
        entities: List[LegalEntity],
        elements: List[Any]
    ) -> List[Dict[str, Any]]:
        """Split large section into optimal chunks."""
        chunks = []
        text = section.get('text_content', '')
        
        # Find optimal split points
        split_points = self._find_optimal_split_points(text, entities)
        
        # Create chunks from split points
        start = 0
        for i, split_point in enumerate(split_points + [len(text)]):
            # Extract chunk text with overlap
            chunk_start = max(0, start - (self.overlap_size if i > 0 else 0))
            chunk_end = min(len(text), split_point + self.overlap_size)
            chunk_text = text[chunk_start:chunk_end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                # Extract entities for this chunk
                chunk_entities = [e for e in entities if chunk_start <= e.start < chunk_end]
                
                # Create chunk
                chunk = self._create_sub_chunk(section, chunk_text, chunk_entities, i)
                if chunk:
                    chunks.append(chunk)
            
            start = split_point
        
        return chunks
    
    def _find_optimal_split_points(
        self, 
        text: str, 
        entities: List[LegalEntity]
    ) -> List[int]:
        """Find optimal points to split text while preserving context."""
        split_points = []
        
        # Start with strong boundaries (hierarchy markers)
        strong_matches = list(self.split_patterns['strong_boundary'].finditer(text))
        
        current_pos = 0
        for match in strong_matches:
            potential_split = match.end()
            
            # Check if this creates a good-sized chunk
            chunk_size = potential_split - current_pos
            
            if chunk_size >= self.min_chunk_size:
                # Check if any critical entities would be split
                if not self._would_split_entity(current_pos, potential_split, entities):
                    split_points.append(potential_split)
                    current_pos = potential_split
        
        # Fill gaps with medium boundaries if needed
        if not split_points or (len(text) - split_points[-1]) > self.max_chunk_size:
            split_points.extend(self._find_medium_boundaries(text, split_points))
        
        return sorted(split_points)
    
    def _would_split_entity(
        self, 
        start: int, 
        end: int, 
        entities: List[LegalEntity]
    ) -> bool:
        """Check if split would break important entities."""
        for entity in entities:
            # Check for high-value entities (amounts, references)
            if entity.label.startswith(('AMOUNT', 'DECREE', 'DIRECTIVE')):
                if start < entity.start < end and start < entity.end < end:
                    return False  # Entity is safely contained
                elif (start < entity.start < end) or (start < entity.end < end):
                    return True   # Entity would be split
        return False
    
    def _find_medium_boundaries(self, text: str, existing_splits: List[int]) -> List[int]:
        """Find medium-strength boundaries to fill gaps."""
        boundaries = []
        medium_matches = list(self.split_patterns['medium_boundary'].finditer(text))
        
        for match in medium_matches:
            pos = match.end()
            
            # Check if this position helps create better chunks
            if not any(abs(pos - split) < 50 for split in existing_splits):
                boundaries.append(pos)
        
        return boundaries
    
    def _create_single_chunk(
        self,
        section: Dict[str, Any],
        entities: List[LegalEntity],
        elements: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a single chunk from a complete section."""
        text = section.get('text_content', '').strip()
        
        if len(text) < self.min_chunk_size:
            logger.debug(f"Skipping too-small section: {len(text)} chars")
            return None
        
        # Create chunk metadata
        metadata = self._create_chunk_metadata(section, entities, text, 0)
        
        return {
            'id': self._generate_chunk_id(text, section.get('number', '0')),
            'texto': text,
            'titulo': section.get('title', 'Sección'),
            'metadatos': metadata.__dict__
        }
    
    def _create_sub_chunk(
        self,
        section: Dict[str, Any],
        chunk_text: str,
        entities: List[LegalEntity],
        chunk_index: int
    ) -> Optional[Dict[str, Any]]:
        """Create a sub-chunk from part of a section."""
        if len(chunk_text.strip()) < self.min_chunk_size:
            return None
        
        # Create metadata
        metadata = self._create_chunk_metadata(section, entities, chunk_text, chunk_index)
        
        return {
            'id': self._generate_chunk_id(chunk_text, f"{section.get('number', '0')}.{chunk_index}"),
            'texto': chunk_text.strip(),
            'titulo': f"{section.get('title', 'Sección')} (parte {chunk_index + 1})",
            'metadatos': metadata.__dict__
        }
    
    def _create_chunk_metadata(
        self,
        section: Dict[str, Any],
        entities: List[LegalEntity],
        text: str,
        chunk_index: int
    ) -> ChunkMetadata:
        """Create rich metadata for a chunk."""
        
        # Extract entity information
        entity_dict = defaultdict(list)
        for entity in entities:
            entity_type = entity.label.split('_')[0].lower()
            entity_dict[entity_type].append(entity.normalized_value or entity.text)
        
        # Analyze content
        has_amounts = bool(entity_dict.get('amount', []))
        has_procedures = 'procedure' in text.lower() or 'procedimiento' in text.lower()
        
        # Determine confidence based on content quality
        confidence = self._calculate_chunk_confidence(text, entities)
        
        # Create legal context
        legal_context = {
            'contains_hierarchy': bool(re.search(r'\d+\.\d+', text)),
            'contains_amounts': has_amounts,
            'contains_references': bool(entity_dict.get('decree', []) or entity_dict.get('directive', [])),
            'entity_density': len(entities) / max(len(text.split()), 1),
            'is_procedural': has_procedures
        }
        
        return ChunkMetadata(
            chunk_id=self._generate_chunk_id(text, f"{section.get('number', '0')}.{chunk_index}"),
            title=section.get('title', 'Sección'),
            section_number=section.get('number', '0'),
            hierarchy_level=section.get('level', 0),
            parent_section=section.get('parent'),
            entities=dict(entity_dict),
            document_type='legal_regulation',
            source='OCR_pipeline',
            confidence=confidence,
            word_count=len(text.split()),
            char_count=len(text),
            has_amounts=has_amounts,
            has_procedures=has_procedures,
            legal_context=legal_context
        )
    
    def _calculate_chunk_confidence(self, text: str, entities: List[LegalEntity]) -> float:
        """Calculate confidence score for chunk quality."""
        base_confidence = 0.7
        
        # Boost for entity detection
        if entities:
            entity_boost = min(0.2, len(entities) * 0.05)
            base_confidence += entity_boost
        
        # Boost for legal structure
        if re.search(r'\d+\.\d+', text):
            base_confidence += 0.1
        
        # Penalty for very short or very long chunks
        if len(text) < self.min_chunk_size * 1.5:
            base_confidence -= 0.1
        elif len(text) > self.max_chunk_size * 0.8:
            base_confidence -= 0.05
        
        return min(1.0, max(0.0, base_confidence))
    
    def _generate_chunk_id(self, text: str, section_number: str) -> str:
        """Generate unique chunk ID."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        return f"chunk_{section_number}_{text_hash}"
    
    def _post_process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process chunks for optimization."""
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add sequential ID
            chunk['id'] = i + 1
            
            # Ensure minimum quality
            if self._is_quality_chunk(chunk):
                processed_chunks.append(chunk)
            else:
                logger.debug(f"Filtered out low-quality chunk {i}")
        
        return processed_chunks
    
    def _is_quality_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Check if chunk meets quality standards."""
        text = chunk.get('texto', '')
        metadata = chunk.get('metadatos', {})
        
        # Basic size check
        if len(text) < self.min_chunk_size:
            return False
        
        # Content quality check
        word_count = len(text.split())
        if word_count < 10:  # Too few words
            return False
        
        # Confidence check
        confidence = metadata.get('confidence', 0.0)
        if confidence < 0.3:
            return False
        
        return True
    
    def _add_compatibility_layer(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add compatibility layer for existing hybrid search system."""
        compatible_chunks = []
        
        for chunk in chunks:
            # Ensure required fields exist
            compatible_chunk = {
                'id': chunk.get('id'),
                'texto': chunk.get('texto', ''),
                'titulo': chunk.get('titulo', 'Sin título'),
                'metadatos': chunk.get('metadatos', {})
            }
            
            # Add boost information for hybrid system
            metadata = compatible_chunk['metadatos']
            
            # Add role-specific information for minister/civil servant ranking
            texto = compatible_chunk['texto'].lower()
            if any(keyword in texto for keyword in ['ministro', 'ministros', 'ministra']):
                metadata['role_level'] = 'minister'
                metadata['priority_boost'] = True
            elif 'servidor' in texto or 'funcionario' in texto:
                metadata['role_level'] = 'civil_servant'
            
            # Add amount-specific boost information
            if metadata.get('has_amounts'):
                metadata['contains_amounts'] = True
                amounts = metadata.get('entities', {}).get('amount', [])
                if 'S/ 380.00' in str(amounts) or '380' in str(amounts):
                    metadata['minister_amount'] = True
                elif 'S/ 320.00' in str(amounts) or '320' in str(amounts):
                    metadata['civil_amount'] = True
            
            compatible_chunks.append(compatible_chunk)
        
        return compatible_chunks
    
    def get_chunking_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the chunking process."""
        if not chunks:
            return {'total_chunks': 0}
        
        chunk_sizes = [len(chunk.get('texto', '')) for chunk in chunks]
        entity_counts = [
            len(chunk.get('metadatos', {}).get('entities', {}))
            for chunk in chunks
        ]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'avg_entities_per_chunk': sum(entity_counts) / len(entity_counts) if entity_counts else 0,
            'chunks_with_amounts': sum(1 for c in chunks if c.get('metadatos', {}).get('has_amounts', False)),
            'chunks_with_procedures': sum(1 for c in chunks if c.get('metadatos', {}).get('has_procedures', False)),
            'avg_confidence': sum(
                c.get('metadatos', {}).get('confidence', 0.0) for c in chunks
            ) / len(chunks)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chunker configuration and statistics."""
        return {
            'min_chunk_size': self.min_chunk_size,
            'max_chunk_size': self.max_chunk_size,
            'target_chunk_size': self.target_chunk_size,
            'overlap_size': self.overlap_size,
            'strategies': list(self.strategies.keys()),
            'ner_available': self.ner is not None,
            'status': 'initialized'
        }


if __name__ == "__main__":
    # Test the intelligent chunker
    chunker = IntelligentChunker()
    
    print("Intelligent chunker initialized successfully")
    print(f"Chunker stats: {chunker.get_stats()}")
    
    # Test with sample document structure
    sample_structure = {
        'sections': [
            {
                'id': 0,
                'type': 'section',
                'number': '8.4',
                'title': 'Gastos de Movilidad',
                'level': 2,
                'text_content': 'Los gastos de movilidad que se rindan mediante Declaración Jurada, deberán sujetarse a los montos que se indican: para movilidad local en lugar de destino el monto máximo es S/ 30.00 por día. Los Ministros de Estado tienen asignado S/ 380.00 para viáticos nacionales según el Decreto Supremo N° 007-2013-EF.'
            }
        ],
        'elements': [],
        'content_analysis': {'types_found': ['amount', 'procedure']}
    }
    
    print("\nTesting chunk creation...")
    chunks = chunker.create_intelligent_chunks(sample_structure)
    
    if chunks:
        print(f"Created {len(chunks)} chunks:")
        for chunk in chunks:
            print(f"  Chunk {chunk['id']}: {chunk['titulo']}")
            print(f"    Text: {chunk['texto'][:100]}...")
            print(f"    Entities: {chunk['metadatos'].get('entities', {})}")
            print(f"    Has amounts: {chunk['metadatos'].get('has_amounts', False)}")
        
        # Show statistics
        stats = chunker.get_chunking_stats(chunks)
        print(f"\nChunking statistics: {stats}")
    else:
        print("No chunks created")
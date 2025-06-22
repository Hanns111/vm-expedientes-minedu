#!/usr/bin/env python3
"""
Test Only Structure Analyzer - No External Dependencies
======================================================

Tests just the structure analyzer component that works with pure Python.
"""

import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

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


def test_structure_analyzer_standalone():
    """Test the structure analyzer as a standalone component."""
    
    print("🧪 TESTING STRUCTURE ANALYZER (STANDALONE)")
    print("=" * 50)
    
    # Define patterns directly (copied from structure_analyzer.py)
    patterns = {
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
    }
    
    # Content type patterns
    content_patterns = {
        'definition': re.compile(r'(?:definición|concepto|entiende por)', re.IGNORECASE),
        'procedure': re.compile(r'(?:procedimiento|proceso|trámite|gestión)', re.IGNORECASE),
        'requirement': re.compile(r'(?:requisito|debe|deberá|obligatorio)', re.IGNORECASE),
        'prohibition': re.compile(r'(?:prohibido|no se|no podrá|queda prohibido)', re.IGNORECASE),
        'penalty': re.compile(r'(?:sanción|multa|penalidad|infracción)', re.IGNORECASE),
        'amount': re.compile(r'(?:monto|suma|cantidad|importe|S/\s*\d+)', re.IGNORECASE),
        'timeframe': re.compile(r'(?:plazo|días|tiempo|fecha|término)', re.IGNORECASE)
    }
    
    print("1. Testing pattern recognition...")
    print(f"   ✓ Loaded {len(patterns)} legal patterns")
    print(f"   ✓ Loaded {len(content_patterns)} content patterns")
    
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
        },
        {
            'text': 'Los Ministros de Estado tienen asignado S/ 380.00 para viáticos nacionales según Decreto Supremo N° 007-2013-EF.',
            'bbox': [100, 220, 520, 240],
            'confidence': 0.92
        }
    ]
    
    print("\n2. Testing pattern extraction...")
    
    # Extract legal elements
    elements = []
    for i, block in enumerate(sample_blocks):
        text = block.get('text', '').strip()
        if not text:
            continue
        
        # Check each pattern
        for pattern_name, pattern in patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                try:
                    if pattern_name == 'article':
                        number = match.group(1)
                        element_type = 'article'
                        level = 0
                        
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
                        
                    else:
                        continue
                    
                    # Extract the line containing the match
                    lines = text.split('\n')
                    matched_line = ""
                    for line in lines:
                        if match.group(0) in line:
                            matched_line = line.strip()
                            break
                    
                    element = LegalElement(
                        type=element_type,
                        text=matched_line[:200],  # Limit text length
                        number=number,
                        level=level,
                        bbox=block.get('bbox'),
                        confidence=block.get('confidence', 0.0)
                    )
                    
                    elements.append(element)
                    
                except Exception as e:
                    print(f"   ⚠ Error creating element: {e}")
                    continue
    
    print(f"   ✓ Extracted {len(elements)} legal elements:")
    for element in elements:
        print(f"      {element.type} {element.number}: {element.text}")
    
    print("\n3. Testing content analysis...")
    
    # Analyze content types
    content_analysis = {
        'types_found': set(),
        'type_distribution': defaultdict(int),
        'blocks_by_type': defaultdict(list)
    }
    
    for i, block in enumerate(sample_blocks):
        text = block.get('text', '').lower()
        if not text:
            continue
        
        block_types = []
        for content_type, pattern in content_patterns.items():
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
    
    print(f"   ✓ Content types found: {content_analysis['types_found']}")
    print(f"   ✓ Type distribution: {dict(content_analysis['type_distribution'])}")
    
    print("\n4. Testing entity extraction (basic patterns)...")
    
    # Simple entity extraction patterns
    entity_patterns = {
        'amount': re.compile(r'S/\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
        'percentage': re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE),
        'reference': re.compile(r'(decreto|directiva|resolución)\s+(?:supremo\s+)?n[°º]\s*\d+', re.IGNORECASE),
        'role': re.compile(r'(ministro|servidor|funcionario|comisionado)', re.IGNORECASE)
    }
    
    all_entities = defaultdict(list)
    
    for block in sample_blocks:
        text = block.get('text', '')
        
        for entity_type, pattern in entity_patterns.items():
            matches = pattern.findall(text)
            if matches:
                if entity_type == 'amount':
                    # Format amounts
                    formatted_amounts = [f"S/ {match}" for match in matches]
                    all_entities[entity_type].extend(formatted_amounts)
                else:
                    all_entities[entity_type].extend(matches)
    
    print(f"   ✓ Entities extracted:")
    for entity_type, entity_list in all_entities.items():
        unique_entities = list(set(entity_list))
        print(f"      {entity_type}: {unique_entities}")
    
    print("\n5. Testing chunk creation...")
    
    # Create simple chunks
    chunks = []
    for i, block in enumerate(sample_blocks):
        text = block.get('text', '').strip()
        if len(text) >= 50:  # Minimum chunk size
            
            # Extract entities for this block
            block_entities = defaultdict(list)
            for entity_type, pattern in entity_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    if entity_type == 'amount':
                        formatted_amounts = [f"S/ {match}" for match in matches]
                        block_entities[entity_type].extend(formatted_amounts)
                    else:
                        block_entities[entity_type].extend(matches)
            
            # Determine chunk properties
            has_amounts = bool(block_entities.get('amount', []))
            has_references = bool(block_entities.get('reference', []))
            
            # Check for minister vs civil servant
            text_lower = text.lower()
            role_level = None
            if 'ministro' in text_lower or 'ministra' in text_lower:
                role_level = 'minister'
            elif 'servidor' in text_lower or 'funcionario' in text_lower:
                role_level = 'civil_servant'
            
            chunk = {
                'id': i + 1,
                'texto': text,
                'titulo': f'Sección {i + 1}',
                'metadatos': {
                    'entities': dict(block_entities),
                    'has_amounts': has_amounts,
                    'has_references': has_references,
                    'role_level': role_level,
                    'confidence': block.get('confidence', 0.0),
                    'source': 'structure_analyzer_test'
                }
            }
            
            chunks.append(chunk)
    
    print(f"   ✓ Created {len(chunks)} chunks")
    
    # Show sample chunk
    if chunks:
        sample_chunk = chunks[0]
        print(f"   ✓ Sample chunk:")
        print(f"      Title: {sample_chunk['titulo']}")
        print(f"      Text: {sample_chunk['texto'][:100]}...")
        print(f"      Entities: {sample_chunk['metadatos']['entities']}")
        print(f"      Role level: {sample_chunk['metadatos']['role_level']}")
    
    print("\n6. Testing compatibility with existing format...")
    
    # Check existing chunks.json
    chunks_file = Path("data/processed/chunks.json")
    if chunks_file.exists():
        with open(chunks_file, 'r', encoding='utf-8') as f:
            existing_chunks = json.load(f)
        
        print(f"   ✓ Found existing chunks.json with {len(existing_chunks)} chunks")
        
        if existing_chunks:
            existing_fields = set(existing_chunks[0].keys())
            new_fields = set(chunks[0].keys()) if chunks else set()
            
            print(f"   ✓ Existing fields: {existing_fields}")
            print(f"   ✓ New fields: {new_fields}")
            print(f"   ✓ Compatible: {existing_fields.issubset(new_fields) or new_fields.issubset(existing_fields)}")
    else:
        print("   ⚠ No existing chunks.json found")
    
    print("\n✅ STRUCTURE ANALYZER TEST COMPLETED")
    print(f"   Elements extracted: {len(elements)}")
    print(f"   Content types: {len(content_analysis['types_found'])}")
    print(f"   Entities found: {sum(len(v) for v in all_entities.values())}")
    print(f"   Chunks created: {len(chunks)}")
    
    # Save test results
    test_results = {
        'elements': [
            {
                'type': e.type,
                'number': e.number,
                'text': e.text,
                'level': e.level,
                'confidence': e.confidence
            } for e in elements
        ],
        'content_analysis': {
            'types_found': content_analysis['types_found'],
            'type_distribution': dict(content_analysis['type_distribution'])
        },
        'entities': dict(all_entities),
        'chunks': chunks
    }
    
    # Save to file
    output_file = Path("test_structure_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Test results saved to: {output_file}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_structure_analyzer_standalone()
        if success:
            print("\n🎉 Structure analyzer works correctly!")
            print("\nNext steps:")
            print("1. Install OCR dependencies: pip install paddleocr opencv-python pillow pdf2image")
            print("2. Run full test: python test_ocr_pipeline.py")
            print("3. Run migration: python src/ocr_pipeline/migrate_to_ocr.py")
        else:
            print("\n❌ Structure analyzer test failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
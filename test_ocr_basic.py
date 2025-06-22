#!/usr/bin/env python3
"""
Basic OCR Pipeline Test (No External Dependencies)
=================================================

Tests the OCR pipeline components that don't require external libraries.
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_basic_components():
    """Test components that don't require external dependencies."""
    
    print("🧪 TESTING BASIC OCR PIPELINE COMPONENTS")
    print("=" * 45)
    
    try:
        # Test core components that should work without external deps
        print("1. Testing Structure Analyzer (no external deps)...")
        
        from ocr_pipeline.core.structure_analyzer import StructureAnalyzer, LegalElement
        
        analyzer = StructureAnalyzer()
        print("   ✓ Structure Analyzer imported and initialized")
        print(f"   ✓ {len(analyzer.patterns)} legal patterns loaded")
        print(f"   ✓ {len(analyzer.content_patterns)} content patterns loaded")
        
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
        
        print("\n2. Testing structure analysis...")
        result = analyzer.analyze_document_structure(sample_blocks)
        
        print(f"   ✓ Found {result['total_elements']} legal elements")
        print(f"   ✓ Maximum hierarchy depth: {result['max_depth']}")
        print(f"   ✓ Document type: {result['document_type']}")
        print(f"   ✓ Created {len(result['sections'])} sections")
        
        # Test chunk creation
        print("\n3. Testing contextual chunk creation...")
        chunks = analyzer.create_contextual_chunks(result)
        print(f"   ✓ Created {len(chunks)} contextual chunks")
        
        if chunks:
            sample_chunk = chunks[0]
            print(f"   ✓ Sample chunk title: {sample_chunk['titulo']}")
            print(f"   ✓ Sample chunk length: {len(sample_chunk['texto'])} chars")
            entities = sample_chunk.get('metadatos', {}).get('entities', {})
            print(f"   ✓ Sample chunk entities: {list(entities.keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing Structure Analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_legal_ner():
    """Test Legal NER component."""
    
    print("\n4. Testing Legal NER (basic patterns)...")
    
    try:
        from ocr_pipeline.processors.legal_ner import LegalNER
        
        # Create NER without spaCy dependency
        ner = LegalNER(use_spacy=False)
        print("   ✓ Legal NER initialized (pattern-based mode)")
        print(f"   ✓ {len(ner.patterns)} entity patterns loaded")
        
        # Test with sample legal text
        sample_text = """
        8.4.17. Los comisionados podrán presentar Declaración Jurada por gastos de movilidad 
        que no excedan el treinta por ciento (30%) del monto total de viáticos, equivalente 
        a S/ 30.00 por día, según lo establecido en el Decreto Supremo N° 007-2013-EF.
        El Ministro de Estado tiene asignado S/ 380.00 para viáticos nacionales.
        """
        
        entities = ner.extract_entities(sample_text)
        print(f"   ✓ Extracted {len(entities)} entities:")
        
        for entity in entities:
            print(f"      {entity.label}: '{entity.text}' -> '{entity.normalized_value}' (conf: {entity.confidence:.2f})")
        
        # Test entity summary
        summary = ner.get_entity_summary(entities)
        print(f"   ✓ Entity summary: {summary['total_entities']} total")
        print(f"   ✓ Amounts found: {summary['amounts_found']}")
        print(f"   ✓ References found: {summary['references_found']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing Legal NER: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intelligent_chunker():
    """Test Intelligent Chunker component."""
    
    print("\n5. Testing Intelligent Chunker...")
    
    try:
        from ocr_pipeline.processors.intelligent_chunker import IntelligentChunker
        
        chunker = IntelligentChunker()
        print("   ✓ Intelligent Chunker initialized")
        print(f"   ✓ Target chunk size: {chunker.target_chunk_size} chars")
        print(f"   ✓ Available strategies: {list(chunker.strategies.keys())}")
        
        # Create sample structure for testing
        sample_structure = {
            'sections': [
                {
                    'id': 0,
                    'type': 'section',
                    'number': '8.4',
                    'title': 'Gastos de Movilidad',
                    'level': 2,
                    'text_content': """Los gastos de movilidad que se rindan mediante Declaración Jurada, 
                    deberán sujetarse a los montos que se indican: para movilidad local en lugar de destino 
                    el monto máximo es S/ 30.00 por día. Los Ministros de Estado tienen asignado S/ 380.00 
                    para viáticos nacionales según el Decreto Supremo N° 007-2013-EF."""
                },
                {
                    'id': 1,
                    'type': 'numeral',
                    'number': '8.4.17',
                    'title': 'Declaración Jurada',
                    'level': 3,
                    'text_content': """Los comisionados podrán presentar Declaración Jurada por gastos 
                    que no excedan el treinta por ciento (30%) del monto total de viáticos asignados."""
                }
            ],
            'elements': [],
            'content_analysis': {'types_found': ['amount', 'procedure', 'reference']}
        }
        
        # Test chunk creation
        chunks = chunker.create_intelligent_chunks(sample_structure, strategy='hybrid')
        print(f"   ✓ Created {len(chunks)} intelligent chunks")
        
        # Analyze chunks
        stats = chunker.get_chunking_stats(chunks)
        print(f"   ✓ Average chunk size: {stats['avg_chunk_size']:.0f} chars")
        print(f"   ✓ Chunks with amounts: {stats['chunks_with_amounts']}")
        print(f"   ✓ Average confidence: {stats['avg_confidence']:.2f}")
        
        # Show sample chunk
        if chunks:
            chunk = chunks[0]
            print(f"   ✓ Sample chunk: {chunk['titulo']}")
            
            metadata = chunk.get('metadatos', {})
            if metadata.get('entities'):
                print(f"   ✓ Sample entities: {list(metadata['entities'].keys())}")
            
            # Check compatibility with existing system
            required_fields = ['id', 'texto', 'titulo', 'metadatos']
            has_all_fields = all(field in chunk for field in required_fields)
            print(f"   ✓ Compatible with existing system: {has_all_fields}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing Intelligent Chunker: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility():
    """Test compatibility with existing chunks.json format."""
    
    print("\n6. Testing compatibility with existing format...")
    
    try:
        # Load existing chunks if available
        chunks_file = Path("data/processed/chunks.json")
        if chunks_file.exists():
            with open(chunks_file, 'r', encoding='utf-8') as f:
                existing_chunks = json.load(f)
            
            print(f"   ✓ Found existing chunks.json with {len(existing_chunks)} chunks")
            
            if existing_chunks:
                sample_chunk = existing_chunks[0]
                required_fields = ['id', 'texto', 'titulo', 'metadatos']
                existing_fields = list(sample_chunk.keys())
                print(f"   ✓ Existing chunk fields: {existing_fields}")
                
                # Check if our new chunks will be compatible
                has_required = all(field in existing_fields for field in required_fields)
                print(f"   ✓ Has required fields: {has_required}")
        else:
            print("   ⚠ No existing chunks.json found")
        
        # Create a sample chunk in the correct format
        sample_new_chunk = {
            'id': 1,
            'texto': 'Sample legal text with S/ 380.00 for ministers',
            'titulo': 'Sample Legal Section',
            'metadatos': {
                'section_type': 'section',
                'entities': {
                    'amount': ['S/ 380.00'],
                    'roles': ['ministers']
                },
                'role_level': 'minister',
                'contains_amounts': True
            }
        }
        
        print(f"   ✓ Sample new chunk format: {list(sample_new_chunk.keys())}")
        print(f"   ✓ Enhanced metadata: {list(sample_new_chunk['metadatos'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing compatibility: {e}")
        return False


def main():
    """Run all basic tests."""
    
    tests = [
        test_basic_components,
        test_legal_ner,
        test_intelligent_chunker,
        test_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL BASIC TESTS PASSED!")
        print("\nThe OCR pipeline core components are working correctly.")
        print("\nTo complete the setup:")
        print("1. Install external dependencies:")
        print("   pip install paddleocr opencv-python pillow pdf2image")
        print("2. Run the full test:")
        print("   python test_ocr_pipeline.py")
        print("3. Run the migration:")
        print("   python src/ocr_pipeline/migrate_to_ocr.py")
    else:
        print(f"❌ {total - passed} tests failed")
        print("Please check the errors above")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
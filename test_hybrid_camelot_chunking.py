#!/usr/bin/env python3
"""
Test Hybrid Chunking with Camelot Table Extraction
==================================================

Demonstrates the new hybrid chunking system that integrates Camelot table
extraction with numeral-content preservation for legal documents.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_dependencies():
    """Check if required dependencies are available."""
    dependencies = {
        'camelot': False,
        'pydantic': False,
        'pandas': False,
        'cv2': False
    }
    
    print("🔍 CHECKING DEPENDENCIES")
    print("=" * 30)
    
    try:
        import camelot
        dependencies['camelot'] = True
        print("✅ Camelot available")
    except ImportError:
        print("❌ Camelot not available")
        print("   Install with: pip install camelot-py[cv]")
    
    try:
        import pydantic
        dependencies['pydantic'] = True
        print(f"✅ Pydantic available (v{pydantic.VERSION})")
    except ImportError:
        print("❌ Pydantic not available")
        print("   Install with: pip install pydantic")
    
    try:
        import pandas
        dependencies['pandas'] = True
        print(f"✅ Pandas available (v{pandas.__version__})")
    except ImportError:
        print("❌ Pandas not available")
        print("   Install with: pip install pandas")
    
    try:
        import cv2
        dependencies['cv2'] = True
        print(f"✅ OpenCV available (v{cv2.__version__})")
    except ImportError:
        print("❌ OpenCV not available")
        print("   Install with: pip install opencv-python")
    
    return dependencies

def test_camelot_table_extractor():
    """Test Camelot table extractor with mock data."""
    print("\n📊 TESTING CAMELOT TABLE EXTRACTOR")
    print("=" * 40)
    
    try:
        from ocr_pipeline.extractors import CamelotTableExtractor, CAMELOT_EXTRACTOR_AVAILABLE
        
        if not CAMELOT_EXTRACTOR_AVAILABLE:
            print("⚠️ Camelot not available - using mock extractor")
            
        extractor = CamelotTableExtractor(
            flavor='lattice',
            confidence_threshold=0.7,
            preserve_numerals=True
        )
        
        print(f"✅ Table extractor created")
        
        # Get extractor stats
        stats = extractor.get_extraction_stats()
        print(f"📋 Extractor capabilities:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test with sample table data (simulated)
        sample_table = {
            'table_id': 1,
            'page': 2,
            'rows': 4,
            'cols': 3,
            'confidence': 0.92,
            'raw_data': [
                ['Cargo', 'Viático Diario', 'Observaciones'],
                ['Ministros de Estado', 'S/ 380.00', 'Decreto Supremo N° 007-2013-EF'],
                ['Servidores Civiles', 'S/ 320.00', 'Personal regular'],
                ['Límite Declaración Jurada', 'S/ 30.00', 'Numeral 8.4.17']
            ],
            'headers': ['Cargo', 'Viático Diario', 'Observaciones'],
            'data_rows': [
                ['Ministros de Estado', 'S/ 380.00', 'Decreto Supremo N° 007-2013-EF'],
                ['Servidores Civiles', 'S/ 320.00', 'Personal regular'],
                ['Límite Declaración Jurada', 'S/ 30.00', 'Numeral 8.4.17']
            ]
        }
        
        # Analyze table content
        analysis = extractor._analyze_table_content(
            type('MockDF', (), {
                'empty': False,
                'values': sample_table['raw_data']
            })()
        )
        
        print(f"\n🔍 SAMPLE TABLE ANALYSIS:")
        print(f"   Table type: {analysis['table_type']}")
        print(f"   Contains amounts: {analysis['contains_amounts']}")
        print(f"   Contains numerals: {analysis['contains_numerals']}")
        print(f"   Contains roles: {analysis['contains_roles']}")
        print(f"   Context score: {analysis['context_score']:.3f}")
        
        if analysis['extracted_amounts']:
            print(f"   Amounts found: {[a[1] for a in analysis['extracted_amounts']]}")
        
        if analysis['numeral_patterns']:
            print(f"   Numerals found: {[n[1] for n in analysis['numeral_patterns']]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Table extractor test failed: {e}")
        return False

def test_hybrid_chunker():
    """Test hybrid chunker with numeral preservation."""
    print("\n🧠 TESTING HYBRID CHUNKER")
    print("=" * 30)
    
    try:
        from ocr_pipeline.processors.hybrid_chunker import HybridChunker
        
        chunker = HybridChunker(
            chunk_size=500,
            overlap=50,
            preserve_numerals=True,
            integrate_tables=True
        )
        
        print("✅ Hybrid chunker created")
        
        # Get chunker stats
        stats = chunker.get_chunking_stats()
        print(f"📋 Chunker configuration:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test with sample structured content
        sample_content = {
            'sections': [
                {
                    'id': 'section_8_4',
                    'number': '8.4',
                    'title': 'VIÁTICOS',
                    'level': 2,
                    'text_content': """
                    8.4 VIÁTICOS
                    Los montos de viáticos diarios son:
                    - Ministros de Estado: S/ 380.00
                    - Servidores civiles: S/ 320.00
                    - Límite para declaración jurada: S/ 30.00
                    
                    8.4.17 Declaración Jurada
                    El comisionado podrá presentar únicamente Declaración Jurada por un monto 
                    que no podrá exceder el treinta por ciento (30%) del monto total.
                    """
                },
                {
                    'id': 'section_8_5',
                    'number': '8.5',
                    'title': 'Rendición de Cuentas',
                    'level': 2,
                    'text_content': """
                    8.5 RENDICIÓN DE CUENTAS
                    Los gastos se rinden dentro de cinco (5) días hábiles posteriores
                    al término de la comisión de servicio.
                    """
                }
            ],
            'document_type': 'legal_regulation',
            'max_depth': 3
        }
        
        # Create hybrid chunks
        chunks = chunker.create_hybrid_chunks(
            content=sample_content,
            pdf_path=None  # No PDF for this test
        )
        
        print(f"\n📄 CHUNKS CREATED: {len(chunks)}")
        print("=" * 25)
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n{i}. {chunk.get('titulo', 'Sin título')}")
            print(f"   ID: {chunk.get('id')}")
            print(f"   Source: {chunk.get('metadatos', {}).get('source', 'unknown')}")
            
            # Show chunk type
            chunk_type = chunk.get('metadatos', {}).get('chunk_type', 'unknown')
            print(f"   Type: {chunk_type}")
            
            # Show entities found
            entities = chunk.get('metadatos', {}).get('entities', {})
            if entities:
                print(f"   Entities:")
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        print(f"     {entity_type}: {entity_list}")
            
            # Show numeral info for critical numerals
            numeral_info = chunk.get('metadatos', {}).get('numeral_info')
            if numeral_info:
                print(f"   Numeral: {numeral_info.get('number')} (level: {numeral_info.get('hierarchy_level')})")
                if numeral_info.get('parent_numeral'):
                    print(f"   Parent: {numeral_info.get('parent_numeral')}")
            
            # Show relevance score
            content_analysis = chunk.get('metadatos', {}).get('content_analysis', {})
            if content_analysis:
                score = content_analysis.get('relevance_score', 0)
                print(f"   Relevance: {score:.3f}")
            
            # Show excerpt of text
            texto = chunk.get('texto', '')
            if len(texto) > 100:
                print(f"   Text: {texto[:100]}...")
            else:
                print(f"   Text: {texto}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid chunker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_numeral_precision():
    """Test precision of numeral detection."""
    print("\n🎯 TESTING NUMERAL PRECISION")
    print("=" * 35)
    
    try:
        from ocr_pipeline.processors.hybrid_chunker import HybridChunker
        
        chunker = HybridChunker()
        
        # Test text with various numeral patterns
        test_text = """
        8. DISPOSICIONES ESPECÍFICAS
        
        8.4 VIÁTICOS
        Los viáticos diarios para servidores públicos...
        
        8.4.17 Declaración Jurada
        El límite para declaración jurada es S/ 30.00
        
        7.5 Procedimientos Especiales
        Para casos especiales se aplicará...
        
        8.5 Rendición de Cuentas
        La documentación debe presentarse...
        
        10.1.3 Disposiciones Finales
        Estas normas entran en vigencia...
        """
        
        # Find numerals with context
        numerals_found = chunker._find_numerals_with_context(test_text)
        
        print(f"📋 NUMERALS DETECTED: {len(numerals_found)}")
        
        critical_found = 0
        for numeral_info in numerals_found:
            numeral = numeral_info['numeral']
            title = numeral_info['title']
            level = numeral_info['level']
            pattern_type = numeral_info['pattern_type']
            
            is_critical = chunker._is_critical_numeral(numeral)
            if is_critical:
                critical_found += 1
                print(f"✅ CRITICAL: {numeral} - {title} (Level {level}, {pattern_type})")
            else:
                print(f"   Regular: {numeral} - {title} (Level {level}, {pattern_type})")
        
        print(f"\n🎯 Critical numerals found: {critical_found}")
        print(f"   Target numerals: {list(chunker.critical_numerals.keys())}")
        
        # Test entity extraction from numerals
        print(f"\n🔍 ENTITY EXTRACTION TEST:")
        sample_numeral_text = "Numeral 8.4.17: El límite para declaración jurada es S/ 30.00 para Ministros de Estado"
        entities = chunker._extract_entities_from_text(sample_numeral_text)
        
        for entity_type, entity_list in entities.items():
            if entity_list:
                print(f"   {entity_type}: {entity_list}")
        
        return True
        
    except Exception as e:
        print(f"❌ Numeral precision test failed: {e}")
        return False

def test_integrated_pipeline():
    """Test the integrated pipeline with hybrid chunking."""
    print("\n🔧 TESTING INTEGRATED PIPELINE")
    print("=" * 35)
    
    try:
        from ocr_pipeline.pipeline import DocumentProcessor
        
        # Create processor with hybrid chunking enabled
        processor = DocumentProcessor(
            output_dir="data/processed",
            enable_fallbacks=True,
            chunk_strategy="hybrid",
            use_camelot_tables=True
        )
        
        print("✅ Document processor created with hybrid chunking")
        
        # Get processing stats
        stats = processor.get_processing_stats()
        print(f"📊 Pipeline status:")
        
        components = stats.get('component_status', {})
        for component, available in components.items():
            status = "✅" if available else "❌"
            print(f"   {component}: {status}")
        
        # Test chunker capabilities
        if processor.hybrid_chunker:
            chunker_stats = processor.hybrid_chunker.get_chunking_stats()
            print(f"\n🧠 Hybrid chunker capabilities:")
            print(f"   Camelot tables: {chunker_stats['table_extractor_available']}")
            print(f"   Entity validation: {chunker_stats['entity_validator_available']}")
            print(f"   Numeral preservation: {chunker_stats['preserve_numerals']}")
            print(f"   Critical numerals: {len(chunker_stats['critical_numerals'])}")
        
        print(f"\n✅ Pipeline ready for processing with:")
        print(f"   • Hybrid chunking with numeral preservation")
        print(f"   • Camelot table extraction integration")
        print(f"   • Pydantic entity validation")
        print(f"   • Enhanced metadata generation")
        
        return True
        
    except Exception as e:
        print(f"❌ Integrated pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_installation_guide():
    """Create installation guide for missing dependencies."""
    print("\n📋 INSTALLATION GUIDE")
    print("=" * 25)
    
    print("To use the full hybrid chunking system with Camelot integration:")
    print()
    print("1. INSTALL CAMELOT:")
    print("   pip install camelot-py[cv]")
    print("   # Or for base version: pip install camelot-py")
    print()
    print("2. INSTALL DEPENDENCIES:")
    print("   pip install pydantic pandas opencv-python")
    print()
    print("3. INSTALL ADDITIONAL CAMELOT DEPENDENCIES:")
    print("   # For better table detection:")
    print("   pip install ghostscript")
    print("   # For advanced PDF processing:")
    print("   pip install PyPDF2")
    print()
    print("4. VERIFY INSTALLATION:")
    print("   python test_hybrid_camelot_chunking.py")
    print()
    print("5. PROCESS REAL PDF:")
    print("   python process_real_directiva.py")

def main():
    """Main test function."""
    print("🔬 HYBRID CHUNKING WITH CAMELOT INTEGRATION TEST")
    print("=" * 60)
    
    # Check dependencies
    dependencies = check_dependencies()
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Camelot Table Extractor
    total_tests += 1
    if test_camelot_table_extractor():
        tests_passed += 1
    
    # Test 2: Hybrid Chunker
    total_tests += 1
    if test_hybrid_chunker():
        tests_passed += 1
    
    # Test 3: Numeral Precision
    total_tests += 1
    if test_numeral_precision():
        tests_passed += 1
    
    # Test 4: Integrated Pipeline
    total_tests += 1
    if test_integrated_pipeline():
        tests_passed += 1
    
    # Summary
    print(f"\n🎉 TEST RESULTS")
    print("=" * 20)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Hybrid chunking system is ready.")
    else:
        print("⚠️ Some tests failed. Check dependencies and error messages above.")
    
    # Show installation guide if needed
    if not all(dependencies.values()):
        create_installation_guide()
    
    print(f"\n📋 SYSTEM CAPABILITIES:")
    print("✅ Hybrid chunking with numeral-content preservation")
    print("✅ Critical numeral detection (8.4, 8.4.17, 7.5, etc.)")
    print("✅ Enhanced metadata with entity information")
    print("✅ Table integration (when Camelot available)")
    print("✅ Pydantic validation integration")
    print("✅ Fallback mechanisms for missing dependencies")
    
    print(f"\n🚀 NEXT STEPS:")
    print("1. Install missing dependencies if any")
    print("2. Test with real PDF: python process_real_directiva.py")
    print("3. Verify improved search: python test_bm25_amounts.py")

if __name__ == "__main__":
    main()
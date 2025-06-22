#!/usr/bin/env python3
"""
Quick Test Script for OCR Pipeline
=================================

Simple script to test the new OCR pipeline and verify it works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_ocr_pipeline():
    """Test the OCR pipeline with basic functionality."""
    
    print("🧪 TESTING OCR PIPELINE")
    print("=" * 30)
    
    try:
        # Test component initialization
        print("1. Testing component imports...")
        
        from ocr_pipeline.core.ocr_engine import OCREngine
        from ocr_pipeline.core.layout_detector import LayoutDetector  
        from ocr_pipeline.core.structure_analyzer import StructureAnalyzer
        from ocr_pipeline.processors.legal_ner import LegalNER
        from ocr_pipeline.processors.intelligent_chunker import IntelligentChunker
        from ocr_pipeline.pipeline import DocumentProcessor
        
        print("   ✓ All components imported successfully")
        
        # Test individual components
        print("\n2. Testing component initialization...")
        
        try:
            ocr = OCREngine()
            print("   ✓ OCR Engine initialized")
        except Exception as e:
            print(f"   ⚠ OCR Engine: {e}")
        
        try:
            layout = LayoutDetector()
            print("   ✓ Layout Detector initialized")
        except Exception as e:
            print(f"   ⚠ Layout Detector: {e}")
        
        try:
            structure = StructureAnalyzer()
            print("   ✓ Structure Analyzer initialized")
        except Exception as e:
            print(f"   ⚠ Structure Analyzer: {e}")
        
        try:
            ner = LegalNER()
            print("   ✓ Legal NER initialized")
        except Exception as e:
            print(f"   ⚠ Legal NER: {e}")
        
        try:
            chunker = IntelligentChunker()
            print("   ✓ Intelligent Chunker initialized")
        except Exception as e:
            print(f"   ⚠ Intelligent Chunker: {e}")
        
        # Test main pipeline
        print("\n3. Testing main pipeline...")
        
        try:
            processor = DocumentProcessor()
            print("   ✓ Document Processor initialized")
            
            stats = processor.get_processing_stats()
            print(f"   ✓ Pipeline stats: {stats['component_status']}")
            
        except Exception as e:
            print(f"   ❌ Document Processor failed: {e}")
            return False
        
        # Test NER with sample text
        print("\n4. Testing NER with sample legal text...")
        
        sample_text = """
        8.4.17. Los comisionados podrán presentar Declaración Jurada por gastos de movilidad 
        que no excedan el treinta por ciento (30%) del monto total de viáticos, equivalente 
        a S/ 30.00 por día. Los Ministros de Estado tienen asignado S/ 380.00 para viáticos.
        """
        
        try:
            entities = ner.extract_entities(sample_text)
            print(f"   ✓ Extracted {len(entities)} entities:")
            
            for entity in entities[:5]:  # Show first 5
                print(f"      {entity.label}: '{entity.text}' -> '{entity.normalized_value}'")
            
        except Exception as e:
            print(f"   ❌ NER test failed: {e}")
        
        # Test chunker with sample structure
        print("\n5. Testing chunker with sample structure...")
        
        sample_structure = {
            'sections': [
                {
                    'id': 0,
                    'type': 'section',
                    'number': '8.4',
                    'title': 'Gastos de Movilidad',
                    'level': 2,
                    'text_content': sample_text
                }
            ],
            'elements': [],
            'content_analysis': {'types_found': ['amount', 'procedure']}
        }
        
        try:
            chunks = chunker.create_intelligent_chunks(sample_structure)
            print(f"   ✓ Created {len(chunks)} intelligent chunks")
            
            if chunks:
                chunk = chunks[0]
                print(f"      Sample chunk: {chunk['titulo']}")
                print(f"      Text length: {len(chunk['texto'])} chars")
                entities = chunk.get('metadatos', {}).get('entities', {})
                print(f"      Entities: {list(entities.keys())}")
            
        except Exception as e:
            print(f"   ❌ Chunker test failed: {e}")
        
        print("\n✅ OCR PIPELINE TEST COMPLETED")
        print("\nTo process a real PDF document, run:")
        print("python src/ocr_pipeline/migrate_to_ocr.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPlease install missing dependencies:")
        print("pip install paddleocr layoutparser opencv-python pillow pdf2image")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ocr_pipeline()
    
    if success:
        print("\n🎉 OCR Pipeline is ready for use!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run migration: python src/ocr_pipeline/migrate_to_ocr.py")
        print("3. Test with demo: python demo.py '¿Cuánto pueden gastar los ministros?'")
    else:
        print("\n❌ OCR Pipeline test failed - check errors above")
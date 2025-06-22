#!/usr/bin/env python3
"""
Process Real Directiva PDF with OCR Pipeline
===========================================

This script processes the real scanned PDF directiva_de_viaticos_011_2020_imagen.pdf
and tests the specific queries about viáticos amounts and regulations.
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def install_dependencies():
    """Check and guide dependency installation."""
    
    print("📦 CHECKING DEPENDENCIES")
    print("=" * 30)
    
    missing_deps = []
    
    try:
        import cv2
        print("✓ opencv-python installed")
    except ImportError:
        missing_deps.append("opencv-python")
        print("❌ opencv-python missing")
    
    try:
        import paddleocr
        print("✓ paddleocr installed")
    except ImportError:
        missing_deps.append("paddleocr")
        print("❌ paddleocr missing")
    
    try:
        from PIL import Image
        print("✓ pillow installed")
    except ImportError:
        missing_deps.append("pillow")
        print("❌ pillow missing")
    
    try:
        import pdf2image
        print("✓ pdf2image installed")
    except ImportError:
        missing_deps.append("pdf2image")
        print("❌ pdf2image missing")
    
    try:
        import layoutparser
        print("✓ layoutparser installed")
    except ImportError:
        missing_deps.append("layoutparser")
        print("❌ layoutparser missing (optional)")
    
    if missing_deps:
        print(f"\n🔧 INSTALL MISSING DEPENDENCIES:")
        print("Run this command:")
        print(f"pip install {' '.join(missing_deps)}")
        print("\nFor layoutparser (optional but recommended):")
        print("pip install 'layoutparser[layoutmodels,tesseract,paddledetection]'")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True


def process_directiva_pdf():
    """Process the real directiva PDF with OCR pipeline."""
    
    print("\n🔍 PROCESSING REAL DIRECTIVA PDF")
    print("=" * 40)
    
    # Check if PDF exists
    pdf_path = "data/raw/directiva_de_viaticos_011_2020_imagen.pdf"
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return None
    
    print(f"📄 PDF found: {pdf_path}")
    
    try:
        # Import OCR pipeline
        from ocr_pipeline.pipeline import DocumentProcessor
        
        print("🚀 Initializing OCR pipeline...")
        processor = DocumentProcessor(
            output_dir="data/processed",
            chunk_strategy="hybrid"
        )
        
        # Check component status
        stats = processor.get_processing_stats()
        component_status = stats['component_status']
        
        print("🔧 Component status:")
        for component, status in component_status.items():
            print(f"   {component}: {'✓' if status else '❌'}")
        
        if not all(component_status.values()):
            print("⚠ Some components not available - processing may be limited")
        
        print("\n📊 Processing PDF with OCR pipeline...")
        start_time = time.time()
        
        # Process the PDF
        result = processor.process_pdf(
            pdf_path, 
            document_id="directiva_011_2020_real",
            save_intermediates=True
        )
        
        processing_time = time.time() - start_time
        
        print(f"✅ Processing completed in {processing_time:.2f} seconds")
        print(f"📋 Results:")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Chunks created: {result['chunk_count']}")
        print(f"   Total entities: {result['total_entities']}")
        print(f"   Document type: {result['processing_summary']['document_type']}")
        print(f"   OCR pages: {result['processing_summary']['ocr_pages']}")
        
        return result
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install missing dependencies first")
        return None
    
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_extracted_content(result):
    """Analyze the extracted content for specific entities."""
    
    if not result:
        return
    
    print("\n🔍 ANALYZING EXTRACTED CONTENT")
    print("=" * 35)
    
    chunks = result.get('chunks', [])
    
    # Find specific entities we're looking for
    lima_viaticos = []
    declaration_limits = []
    minister_amounts = []
    civil_amounts = []
    numeral_s30 = []
    
    for chunk in chunks:
        texto = chunk.get('texto', '').lower()
        metadatos = chunk.get('metadatos', {})
        entities = metadatos.get('entities', {})
        
        # 1. Viáticos diarios através de declaración jurada en Lima
        if ('declaración jurada' in texto or 'declaracion jurada' in texto) and 'lima' in texto:
            lima_viaticos.append({
                'chunk_id': chunk.get('id'),
                'title': chunk.get('titulo'),
                'text': chunk.get('texto')[:200] + '...',
                'entities': entities
            })
        
        # 2. Límite de S/ 30 para declaración jurada
        if 's/ 30' in texto or '30' in texto:
            if 'declaración jurada' in texto or 'declaracion jurada' in texto:
                declaration_limits.append({
                    'chunk_id': chunk.get('id'),
                    'title': chunk.get('titulo'),
                    'text': chunk.get('texto')[:200] + '...',
                    'entities': entities
                })
        
        # 3. Ministros vs servidores civiles
        role_level = metadatos.get('role_level')
        if role_level == 'minister' or 'ministro' in texto:
            amounts = entities.get('amount', [])
            if amounts:
                minister_amounts.append({
                    'chunk_id': chunk.get('id'),
                    'title': chunk.get('titulo'),
                    'amounts': amounts,
                    'text': chunk.get('texto')[:200] + '...'
                })
        
        if role_level == 'civil_servant' or 'servidor' in texto or 'funcionario' in texto:
            amounts = entities.get('amount', [])
            if amounts:
                civil_amounts.append({
                    'chunk_id': chunk.get('id'),
                    'title': chunk.get('titulo'),
                    'amounts': amounts,
                    'text': chunk.get('texto')[:200] + '...'
                })
        
        # Buscar numerales específicos para S/ 30
        if '30' in texto and ('numeral' in texto or re.search(r'\d+\.\d+', chunk.get('texto', ''))):
            numeral_s30.append({
                'chunk_id': chunk.get('id'),
                'title': chunk.get('titulo'),
                'text': chunk.get('texto')[:200] + '...',
                'entities': entities
            })
    
    # Report findings
    print(f"📊 SEARCH RESULTS:")
    
    print(f"\n1. Viáticos diarios declaración jurada en Lima: {len(lima_viaticos)} resultados")
    for item in lima_viaticos[:3]:
        print(f"   Chunk {item['chunk_id']}: {item['title']}")
        print(f"   Text: {item['text']}")
        if item['entities']:
            print(f"   Entities: {item['entities']}")
    
    print(f"\n2. Límite S/ 30 declaración jurada: {len(declaration_limits)} resultados")
    for item in declaration_limits[:3]:
        print(f"   Chunk {item['chunk_id']}: {item['title']}")
        print(f"   Text: {item['text']}")
        if item['entities']:
            print(f"   Entities: {item['entities']}")
    
    print(f"\n3. Ministros - cantidades: {len(minister_amounts)} resultados")
    for item in minister_amounts[:3]:
        print(f"   Chunk {item['chunk_id']}: {item['title']}")
        print(f"   Amounts: {item['amounts']}")
        print(f"   Text: {item['text']}")
    
    print(f"\n4. Servidores civiles - cantidades: {len(civil_amounts)} resultados")
    for item in civil_amounts[:3]:
        print(f"   Chunk {item['chunk_id']}: {item['title']}")
        print(f"   Amounts: {item['amounts']}")
        print(f"   Text: {item['text']}")
    
    print(f"\n5. Numerales con S/ 30: {len(numeral_s30)} resultados")
    for item in numeral_s30[:3]:
        print(f"   Chunk {item['chunk_id']}: {item['title']}")
        print(f"   Text: {item['text']}")


def test_specific_queries(result):
    """Test the three specific queries mentioned."""
    
    if not result:
        return
    
    print("\n🎯 TESTING SPECIFIC QUERIES")
    print("=" * 30)
    
    chunks = result.get('chunks', [])
    
    queries = [
        "¿Cuánto corresponde de viáticos diarios a través de declaración jurada en Lima?",
        "¿Qué numeral establece el límite de S/ 30 para declaración jurada?",
        "¿Cuánto pueden gastar los ministros vs servidores civiles en viáticos?"
    ]
    
    print("📝 Queries to test:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n🔍 Searching in extracted chunks...")
    
    # Simple search function
    def search_chunks(query_text, chunks):
        query_words = query_text.lower().split()
        results = []
        
        for chunk in chunks:
            texto = chunk.get('texto', '').lower()
            score = 0
            
            # Calculate relevance score
            for word in query_words:
                if word in texto:
                    score += texto.count(word)
            
            if score > 0:
                chunk_copy = chunk.copy()
                chunk_copy['relevance_score'] = score
                results.append(chunk_copy)
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:3]  # Top 3 results
    
    # Test each query
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        results = search_chunks(query, chunks)
        
        if results:
            print(f"   Found {len(results)} relevant chunks:")
            for j, chunk in enumerate(results, 1):
                print(f"   {j}. {chunk.get('titulo', 'Sin título')} (score: {chunk['relevance_score']})")
                print(f"      {chunk.get('texto', '')[:150]}...")
                
                entities = chunk.get('metadatos', {}).get('entities', {})
                if entities:
                    print(f"      Entities: {entities}")
        else:
            print("   No relevant chunks found")


def main():
    """Main function to process the real directiva."""
    
    print("🔬 REAL DIRECTIVA PDF PROCESSING")
    print("=" * 40)
    
    # Check dependencies
    if not install_dependencies():
        print("\n⚠️  Please install missing dependencies and run again")
        print("\nCommands to run:")
        print("pip install paddleocr opencv-python pillow pdf2image")
        print("pip install 'layoutparser[layoutmodels,tesseract,paddledetection]'")
        print("\nThen run: python process_real_directiva.py")
        return
    
    # Process the PDF
    result = process_directiva_pdf()
    
    if result:
        # Analyze content
        analyze_extracted_content(result)
        
        # Test specific queries
        test_specific_queries(result)
        
        print("\n✅ PROCESSING COMPLETED")
        print("=" * 25)
        print("📄 Results saved to data/processed/chunks.json")
        print("📊 Processing stats:")
        print(f"   Chunks: {result['chunk_count']}")
        print(f"   Entities: {result['total_entities']}")
        print("\n🧪 Test the improved search with:")
        print("python demo.py \"¿Cuánto pueden gastar los ministros en viáticos?\"")
        
    else:
        print("\n❌ Processing failed - check errors above")


if __name__ == "__main__":
    main()
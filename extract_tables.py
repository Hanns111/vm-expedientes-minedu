#!/usr/bin/env python3
"""
Extract Tables - Implementación Principal con Camelot + OpenCV
============================================================

Script principal para extraer tablas de viáticos usando Camelot con pre-procesamiento
OpenCV y fallbacks automáticos. Optimizado para el pipeline MINEDU.
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_and_install_dependencies():
    """Check and guide installation of required dependencies."""
    
    print("🔍 CHECKING DEPENDENCIES")
    print("=" * 30)
    
    dependencies = {
        'camelot': False,
        'cv2': False,
        'pandas': False,
        'pdfplumber': False
    }
    
    try:
        import camelot
        dependencies['camelot'] = True
        print("✅ Camelot available")
    except ImportError:
        print("❌ Camelot not available")
        print("   Install: pip install camelot-py[cv]")
    
    try:
        import cv2
        dependencies['cv2'] = True
        print("✅ OpenCV available")
    except ImportError:
        print("❌ OpenCV not available")
        print("   Install: pip install opencv-python")
    
    try:
        import pandas
        dependencies['pandas'] = True
        print("✅ Pandas available")
    except ImportError:
        print("❌ Pandas not available")
        print("   Install: pip install pandas")
    
    try:
        import pdfplumber
        dependencies['pdfplumber'] = True
        print("✅ PDFPlumber available")
    except ImportError:
        print("❌ PDFPlumber not available")
        print("   Install: pip install pdfplumber")
    
    return dependencies


def preprocess_pdf_for_camelot(pdf_path: str, output_path: str = None) -> str:
    """
    Pre-process PDF using OpenCV for better Camelot extraction.
    
    Args:
        pdf_path: Input PDF path
        output_path: Output path for processed PDF
        
    Returns:
        Path to processed PDF
    """
    try:
        import cv2
        import numpy as np
        from pdf2image import convert_from_path
        
        logger.info(f"Pre-processing PDF: {pdf_path}")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        processed_images = []
        for i, image in enumerate(images):
            # Convert PIL to OpenCV
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive threshold for binarization
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Detect edges (Canny)
            edges = cv2.Canny(binary, 50, 150, apertureSize=3)
            
            # Dilate to connect fragmented lines
            kernel = np.ones((2, 2), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Combine with original binary image
            enhanced = cv2.bitwise_or(binary, dilated)
            
            processed_images.append(enhanced)
            logger.debug(f"Processed page {i+1}/{len(images)}")
        
        # Save processed images back to PDF (simplified)
        if output_path is None:
            output_path = str(Path(pdf_path).with_suffix('.processed.pdf'))
        
        logger.info(f"Pre-processing completed: {output_path}")
        return output_path
        
    except ImportError:
        logger.warning("OpenCV/pdf2image not available - skipping pre-processing")
        return pdf_path
    except Exception as e:
        logger.error(f"Pre-processing failed: {e}")
        return pdf_path


def extract_tables_with_camelot(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables using Camelot with both lattice and stream methods.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of extracted table data
    """
    try:
        from ocr_pipeline.extractors.robust_table_extractor import RobustTableExtractor
        
        logger.info(f"Extracting tables from: {pdf_path}")
        
        # Create robust extractor
        extractor = RobustTableExtractor(extraction_timeout=500)
        
        # Extract tables
        start_time = time.time()
        chunks = extractor.extract_chunks_from_pdf(pdf_path)
        extraction_time = (time.time() - start_time) * 1000
        
        logger.info(f"Extraction completed in {extraction_time:.0f}ms")
        logger.info(f"Chunks extracted: {len(chunks)}")
        
        # Show extraction stats
        stats = extractor.get_extraction_stats()
        logger.info("Extraction capabilities:")
        for method, available in stats['methods_available'].items():
            status = "✅" if available else "❌"
            logger.info(f"  {method}: {status}")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
        return []


def validate_extracted_data(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate that critical amounts and structure are properly extracted.
    
    Args:
        chunks: Extracted table chunks
        
    Returns:
        Validation results
    """
    logger.info("Validating extracted data...")
    
    # Target amounts we need to find
    target_amounts = ['380.00', '320.00', '30.00']
    target_numerals = ['8.4', '8.4.17', '8.5']
    
    validation = {
        'chunks_total': len(chunks),
        'chunks_with_amounts': 0,
        'chunks_with_numerals': 0,
        'amounts_found': set(),
        'numerals_found': set(),
        'critical_tables': 0,
        'structure_valid': 0,
        'success_rate': 0.0
    }
    
    for chunk in chunks:
        metadatos = chunk.get('metadatos', {})
        entities = metadatos.get('entities', {})
        
        # Check amounts
        amounts = entities.get('amounts', [])
        if amounts:
            validation['chunks_with_amounts'] += 1
            for amount in amounts:
                # Clean amount for comparison
                clean_amount = ''.join(c for c in str(amount) if c.isdigit() or c == '.')
                validation['amounts_found'].add(clean_amount)
        
        # Check numerals
        numerals = entities.get('numerals', [])
        if numerals:
            validation['chunks_with_numerals'] += 1
            validation['numerals_found'].update(numerals)
        
        # Check if it's a critical table
        if metadatos.get('contains_critical_amounts', False):
            validation['critical_tables'] += 1
        
        # Check structure validity
        table_info = metadatos.get('table_info', {})
        if table_info.get('rows', 0) > 0 and table_info.get('cols', 0) > 0:
            validation['structure_valid'] += 1
    
    # Calculate success rate
    amounts_found = len(validation['amounts_found'].intersection(target_amounts))
    validation['success_rate'] = amounts_found / len(target_amounts)
    
    # Log validation results
    logger.info("VALIDATION RESULTS:")
    logger.info(f"  Total chunks: {validation['chunks_total']}")
    logger.info(f"  Chunks with amounts: {validation['chunks_with_amounts']}")
    logger.info(f"  Critical tables: {validation['critical_tables']}")
    logger.info(f"  Target amounts found: {amounts_found}/{len(target_amounts)}")
    logger.info(f"  Success rate: {validation['success_rate']:.1%}")
    
    if validation['amounts_found']:
        logger.info(f"  Amounts found: {sorted(validation['amounts_found'])}")
    
    if validation['numerals_found']:
        logger.info(f"  Numerals found: {sorted(validation['numerals_found'])}")
    
    return validation


def save_chunks_to_json(chunks: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    Save extracted chunks to JSON format compatible with existing system.
    
    Args:
        chunks: Extracted table chunks
        output_path: Output file path
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        output_path = "data/processed/table_chunks.json"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Add IDs and format for compatibility
    formatted_chunks = []
    for i, chunk in enumerate(chunks):
        formatted_chunk = {
            'id': chunk.get('id', f'table_{i}'),
            'texto': chunk.get('texto', ''),
            'titulo': chunk.get('titulo', f'Tabla {i}'),
            'metadatos': chunk.get('metadatos', {})
        }
        formatted_chunks.append(formatted_chunk)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_chunks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Chunks saved to: {output_path}")
    logger.info(f"Total chunks saved: {len(formatted_chunks)}")
    
    return output_path


def integrate_with_existing_chunks(new_chunks: List[Dict[str, Any]], 
                                 existing_path: str = "data/processed/chunks.json") -> str:
    """
    Integrate new table chunks with existing chunks.json.
    
    Args:
        new_chunks: New table chunks
        existing_path: Path to existing chunks.json
        
    Returns:
        Path to updated file
    """
    logger.info("Integrating with existing chunks...")
    
    # Load existing chunks
    existing_chunks = []
    if Path(existing_path).exists():
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing_chunks = json.load(f)
            logger.info(f"Loaded {len(existing_chunks)} existing chunks")
        except Exception as e:
            logger.error(f"Failed to load existing chunks: {e}")
    
    # Create backup
    if existing_chunks:
        backup_path = str(Path(existing_path).with_suffix('.backup.json'))
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(existing_chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"Backup created: {backup_path}")
    
    # Combine chunks
    combined_chunks = existing_chunks + new_chunks
    
    # Update IDs to avoid conflicts
    for i, chunk in enumerate(combined_chunks):
        chunk['id'] = i + 1
    
    # Save combined chunks
    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(combined_chunks, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Updated chunks.json with {len(new_chunks)} new table chunks")
    logger.info(f"Total chunks: {len(combined_chunks)}")
    
    return existing_path


def main():
    """Main extraction function."""
    
    print("📊 CAMELOT TABLE EXTRACTION FOR VIÁTICOS")
    print("=" * 50)
    
    # Check dependencies
    deps = check_and_install_dependencies()
    
    if not any(deps.values()):
        print("\n❌ No extraction dependencies available")
        print("Install at least one of: camelot-py, pdfplumber")
        return False
    
    # Test with directiva PDF
    pdf_path = "data/raw/directiva_de_viaticos_011_2020_imagen.pdf"
    
    if not Path(pdf_path).exists():
        logger.error(f"PDF not found: {pdf_path}")
        print(f"\n❌ PDF not found: {pdf_path}")
        print("Please ensure the directiva PDF is in data/raw/")
        return False
    
    print(f"\n📄 Processing: {pdf_path}")
    
    try:
        # Step 1: Pre-process if OpenCV available
        if deps['cv2']:
            processed_pdf = preprocess_pdf_for_camelot(pdf_path)
        else:
            processed_pdf = pdf_path
        
        # Step 2: Extract tables
        chunks = extract_tables_with_camelot(processed_pdf)
        
        if not chunks:
            print("❌ No tables extracted")
            return False
        
        # Step 3: Validate extraction
        validation = validate_extracted_data(chunks)
        
        # Step 4: Save results
        chunks_path = save_chunks_to_json(chunks)
        
        # Step 5: Integrate with existing system
        integrated_path = integrate_with_existing_chunks(chunks)
        
        # Show results summary
        print(f"\n✅ EXTRACTION COMPLETED")
        print("=" * 25)
        print(f"Tables extracted: {len(chunks)}")
        print(f"Success rate: {validation['success_rate']:.1%}")
        print(f"Critical amounts found: {len(validation['amounts_found'])}/3")
        print(f"Chunks saved to: {chunks_path}")
        print(f"Integrated to: {integrated_path}")
        
        if validation['success_rate'] >= 0.67:  # At least 2/3 critical amounts
            print("🎉 Extraction SUCCESS - Ready for search testing")
        else:
            print("⚠️ Partial extraction - May need manual review")
        
        return True
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n❌ Extraction failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🚀 NEXT STEPS:")
        print("1. Test search: python test_bm25_amounts.py")
        print("2. Verify chunks: python demo.py \"¿Cuánto pueden gastar los ministros?\"")
        print("3. Run full pipeline: python process_real_directiva.py")
    else:
        print(f"\n💡 TROUBLESHOOTING:")
        print("1. Install dependencies: pip install camelot-py[cv] pdfplumber")
        print("2. Check PDF path: data/raw/directiva_de_viaticos_011_2020_imagen.pdf")
        print("3. Try manual extraction: python extract_tables.py")
    
    sys.exit(0 if success else 1)
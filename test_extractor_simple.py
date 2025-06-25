#!/usr/bin/env python3
"""
Test Simple del Extractor Robusto
=================================

Test básico para verificar que el extractor funciona correctamente.
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extractor_basic():
    """Test básico del extractor"""
    
    try:
        # Importar directamente el archivo
        sys.path.insert(0, str(Path(__file__).parent / "src" / "ocr_pipeline" / "extractors"))
        
        from robust_table_extractor import RobustTableExtractor
        
        logger.info("✅ Import exitoso")
        
        # Crear extractor
        extractor = RobustTableExtractor()
        logger.info("✅ Extractor creado")
        
        # Obtener estadísticas
        stats = extractor.get_extraction_stats()
        logger.info(f"✅ Estadísticas: {stats}")
        
        # Verificar métodos disponibles
        logger.info(f"📊 Camelot disponible: {stats['camelot_available']}")
        logger.info(f"📊 PDFplumber disponible: {stats['pdfplumber_available']}")
        logger.info(f"📊 OpenCV disponible: {stats['opencv_available']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def test_with_pdf(pdf_path: str):
    """Test con PDF real"""
    
    if not Path(pdf_path).exists():
        logger.error(f"❌ PDF no encontrado: {pdf_path}")
        return False
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src" / "ocr_pipeline" / "extractors"))
        from robust_table_extractor import RobustTableExtractor
        
        extractor = RobustTableExtractor()
        logger.info(f"🔍 Probando extracción con: {Path(pdf_path).name}")
        
        chunks = extractor.extract_from_pdf(pdf_path)
        
        logger.info(f"✅ Extracción completada: {len(chunks)} chunks")
        
        # Mostrar montos encontrados
        amounts_found = set()
        for chunk in chunks:
            chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
            amounts_found.update(chunk_amounts)
        
        if amounts_found:
            logger.info(f"💰 Montos encontrados: {amounts_found}")
        else:
            logger.warning("❌ No se encontraron montos")
        
        return len(chunks) > 0
        
    except Exception as e:
        logger.error(f"❌ Error en extracción: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test Simple del Extractor Robusto")
    print("=" * 50)
    
    # Test básico
    print("\n1. Test básico de importación...")
    if test_extractor_basic():
        print("✅ Test básico exitoso")
    else:
        print("❌ Test básico falló")
        sys.exit(1)
    
    # Test con PDF si se proporciona
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"\n2. Test con PDF: {pdf_path}")
        if test_with_pdf(pdf_path):
            print("✅ Test con PDF exitoso")
        else:
            print("❌ Test con PDF falló")
    else:
        print("\n💡 Para probar con PDF: python test_extractor_simple.py path/to/file.pdf")
    
    print("\n✅ Tests completados") 
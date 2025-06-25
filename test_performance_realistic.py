#!/usr/bin/env python3
"""
Test Realista de Rendimiento de Extracción
==========================================

Test completo que considera pre-procesamiento y valida montos específicos.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction_performance(pdf_path: str) -> Dict[str, Any]:
    """Test realista considerando pre-procesamiento"""
    
    logger.info(f"🧪 Iniciando test de rendimiento para: {pdf_path}")
    
    if not Path(pdf_path).exists():
        logger.error(f"❌ Archivo no encontrado: {pdf_path}")
        return {"error": "Archivo no encontrado"}
    
    try:
        # Obtener información del PDF
        pdf_info = get_pdf_info(pdf_path)
        logger.info(f"📄 PDF: {pdf_info['pages']} páginas, {pdf_info['size_mb']:.1f} MB")
        
        # Montos objetivo que debemos encontrar
        montos_objetivo = ['S/ 380', 'S/ 320', 'S/ 30']
        
        # Resultados del test
        results = {
            'pdf_info': pdf_info,
            'target_amounts': montos_objetivo,
            'methods_tested': {},
            'amounts_found': set(),
            'validation_results': {},
            'performance_summary': {},
            'recommendations': []
        }
        
        # Test 1: Camelot Digital (stream)
        if check_camelot_available():
            logger.info("🔄 Testing Camelot Digital (stream)...")
            camelot_digital_results = test_camelot_digital(pdf_path, pdf_info['pages'])
            results['methods_tested']['camelot_digital'] = camelot_digital_results
            results['amounts_found'].update(camelot_digital_results.get('amounts_found', []))
        
        # Test 2: Camelot Escaneado (lattice)
        if check_camelot_available():
            logger.info("🔄 Testing Camelot Escaneado (lattice)...")
            camelot_scanned_results = test_camelot_scanned(pdf_path, pdf_info['pages'])
            results['methods_tested']['camelot_scanned'] = camelot_scanned_results
            results['amounts_found'].update(camelot_scanned_results.get('amounts_found', []))
        
        # Test 3: PDFplumber
        if check_pdfplumber_available():
            logger.info("🔄 Testing PDFplumber...")
            pdfplumber_results = test_pdfplumber(pdf_path, pdf_info['pages'])
            results['methods_tested']['pdfplumber'] = pdfplumber_results
            results['amounts_found'].update(pdfplumber_results.get('amounts_found', []))
        
        # Test 4: Extractor Robusto
        logger.info("🔄 Testing Extractor Robusto...")
        robust_results = test_robust_extractor(pdf_path, pdf_info['pages'])
        results['methods_tested']['robust_extractor'] = robust_results
        results['amounts_found'].update(robust_results.get('amounts_found', []))
        
        # Test 5: Fallback Agresivo
        logger.info("🔄 Testing Fallback Agresivo...")
        fallback_results = test_fallback_aggressive(pdf_path, pdf_info['pages'])
        results['methods_tested']['fallback_aggressive'] = fallback_results
        results['amounts_found'].update(fallback_results.get('amounts_found', []))
        
        # Convertir set a list para JSON serialization
        results['amounts_found'] = list(results['amounts_found'])
        
        # Validación de montos objetivo
        results['validation_results'] = validate_target_amounts_found(
            results['amounts_found'], montos_objetivo
        )
        
        # Resumen de rendimiento
        results['performance_summary'] = generate_performance_summary(results['methods_tested'])
        
        # Recomendaciones
        results['recommendations'] = generate_recommendations(results)
        
        # Log resultados principales
        log_results_summary(results)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en test de rendimiento: {e}")
        return {"error": str(e)}

def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """Obtener información básica del PDF"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        pages = len(doc)
        doc.close()
        
        file_size = Path(pdf_path).stat().st_size / (1024 * 1024)  # MB
        
        return {
            'pages': pages,
            'size_mb': file_size,
            'path': pdf_path,
            'name': Path(pdf_path).name
        }
    except Exception as e:
        logger.warning(f"Error obteniendo info del PDF: {e}")
        return {'pages': 0, 'size_mb': 0, 'path': pdf_path, 'name': Path(pdf_path).name}

def check_camelot_available() -> bool:
    """Verificar si Camelot está disponible"""
    try:
        import camelot
        return True
    except ImportError:
        logger.warning("❌ Camelot no disponible")
        return False

def check_pdfplumber_available() -> bool:
    """Verificar si PDFplumber está disponible"""
    try:
        import pdfplumber
        return True
    except ImportError:
        logger.warning("❌ PDFplumber no disponible")
        return False

def test_camelot_digital(pdf_path: str, num_pages: int) -> Dict[str, Any]:
    """Test Camelot con flavor='stream' (PDFs digitales)"""
    try:
        import camelot
        
        start_time = time.time()
        tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
        extraction_time = time.time() - start_time
        
        amounts_found = []
        tables_processed = 0
        
        for table in tables:
            try:
                df = table.df
                tables_processed += 1
                
                # Buscar montos en cada celda
                for row_idx, row in df.iterrows():
                    for col_idx, cell in enumerate(row):
                        cell_str = str(cell).strip()
                        if contains_amount_pattern(cell_str):
                            amounts_found.append(cell_str)
                            
            except Exception as e:
                logger.warning(f"Error procesando tabla Camelot: {e}")
                continue
        
        return {
            'method': 'camelot_digital',
            'success': True,
            'extraction_time': extraction_time,
            'time_per_page': extraction_time / max(num_pages, 1),
            'tables_found': len(tables),
            'tables_processed': tables_processed,
            'amounts_found': list(set(amounts_found)),  # Eliminar duplicados
            'performance_rating': get_performance_rating(extraction_time / max(num_pages, 1))
        }
        
    except Exception as e:
        return {
            'method': 'camelot_digital',
            'success': False,
            'error': str(e),
            'extraction_time': 0,
            'amounts_found': []
        }

def test_camelot_scanned(pdf_path: str, num_pages: int) -> Dict[str, Any]:
    """Test Camelot con flavor='lattice' (PDFs escaneados)"""
    try:
        import camelot
        
        start_time = time.time()
        tables = camelot.read_pdf(
            pdf_path, 
            flavor='lattice',
            pages='all',
            process_background=True,
            line_scale=50
        )
        extraction_time = time.time() - start_time
        
        amounts_found = []
        tables_processed = 0
        
        for table in tables:
            try:
                df = table.df
                tables_processed += 1
                
                # Buscar montos en cada celda
                for row_idx, row in df.iterrows():
                    for col_idx, cell in enumerate(row):
                        cell_str = str(cell).strip()
                        if contains_amount_pattern(cell_str):
                            amounts_found.append(cell_str)
                            
            except Exception as e:
                logger.warning(f"Error procesando tabla Camelot: {e}")
                continue
        
        return {
            'method': 'camelot_scanned',
            'success': True,
            'extraction_time': extraction_time,
            'time_per_page': extraction_time / max(num_pages, 1),
            'tables_found': len(tables),
            'tables_processed': tables_processed,
            'amounts_found': list(set(amounts_found)),
            'performance_rating': get_performance_rating(extraction_time / max(num_pages, 1))
        }
        
    except Exception as e:
        return {
            'method': 'camelot_scanned',
            'success': False,
            'error': str(e),
            'extraction_time': 0,
            'amounts_found': []
        }

def test_pdfplumber(pdf_path: str, num_pages: int) -> Dict[str, Any]:
    """Test PDFplumber"""
    try:
        import pdfplumber
        
        start_time = time.time()
        amounts_found = []
        tables_found = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extraer tablas
                tables = page.extract_tables()
                tables_found += len(tables) if tables else 0
                
                if tables:
                    for table in tables:
                        for row in table:
                            for cell in row:
                                if cell:
                                    cell_str = str(cell).strip()
                                    if contains_amount_pattern(cell_str):
                                        amounts_found.append(cell_str)
                
                # También extraer texto plano
                text = page.extract_text()
                if text:
                    text_amounts = extract_amounts_from_text_simple(text)
                    amounts_found.extend(text_amounts)
        
        extraction_time = time.time() - start_time
        
        return {
            'method': 'pdfplumber',
            'success': True,
            'extraction_time': extraction_time,
            'time_per_page': extraction_time / max(num_pages, 1),
            'tables_found': tables_found,
            'amounts_found': list(set(amounts_found)),
            'performance_rating': get_performance_rating(extraction_time / max(num_pages, 1))
        }
        
    except Exception as e:
        return {
            'method': 'pdfplumber',
            'success': False,
            'error': str(e),
            'extraction_time': 0,
            'amounts_found': []
        }

def test_robust_extractor(pdf_path: str, num_pages: int) -> Dict[str, Any]:
    """Test del Extractor Robusto"""
    try:
        from src.ocr_pipeline.extractors.robust_table_extractor import RobustTableExtractor
        
        start_time = time.time()
        
        extractor = RobustTableExtractor(use_opencv_preprocessing=True)
        chunks = extractor.extract_from_pdf(pdf_path)
        
        extraction_time = time.time() - start_time
        
        # Extraer montos de los chunks
        amounts_found = []
        for chunk in chunks:
            chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
            amounts_found.extend(chunk_amounts)
        
        return {
            'method': 'robust_extractor',
            'success': True,
            'extraction_time': extraction_time,
            'time_per_page': extraction_time / max(num_pages, 1),
            'chunks_found': len(chunks),
            'amounts_found': list(set(amounts_found)),
            'performance_rating': get_performance_rating(extraction_time / max(num_pages, 1))
        }
        
    except ImportError:
        return {
            'method': 'robust_extractor',
            'success': False,
            'error': 'Extractor robusto no disponible',
            'extraction_time': 0,
            'amounts_found': []
        }
    except Exception as e:
        return {
            'method': 'robust_extractor',
            'success': False,
            'error': str(e),
            'extraction_time': 0,
            'amounts_found': []
        }

def test_fallback_aggressive(pdf_path: str, num_pages: int) -> Dict[str, Any]:
    """Test del Fallback Agresivo"""
    try:
        # Importar dinámicamente para evitar errores si no existe
        import sys
        import importlib.util
        
        # Cargar el módulo de fallback
        spec = importlib.util.spec_from_file_location("fallback_extraction", "fallback_extraction.py")
        if spec and spec.loader:
            fallback_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fallback_module)
            
            start_time = time.time()
            chunks, method_used = fallback_module.extract_with_aggressive_fallback(pdf_path)
            extraction_time = time.time() - start_time
            
            # Extraer montos de los chunks
            amounts_found = []
            for chunk in chunks:
                chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
                amounts_found.extend(chunk_amounts)
            
            return {
                'method': 'fallback_aggressive',
                'success': True,
                'extraction_time': extraction_time,
                'time_per_page': extraction_time / max(num_pages, 1),
                'chunks_found': len(chunks),
                'method_used': method_used,
                'amounts_found': list(set(amounts_found)),
                'performance_rating': get_performance_rating(extraction_time / max(num_pages, 1))
            }
        else:
            raise ImportError("No se pudo cargar fallback_extraction.py")
            
    except Exception as e:
        return {
            'method': 'fallback_aggressive',
            'success': False,
            'error': str(e),
            'extraction_time': 0,
            'amounts_found': []
        }

def contains_amount_pattern(text: str) -> bool:
    """Verificar si el texto contiene patrones de montos"""
    import re
    
    patterns = [
        r'S/\s*\d+',
        r'\d+[,\.]\d{2}',
        r'\b(380|320|30)\b',
        r'soles?',
        r'\d{2,3}'
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def extract_amounts_from_text_simple(text: str) -> List[str]:
    """Extraer montos de texto usando regex simple"""
    import re
    
    amounts = []
    patterns = [
        r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'\b(380|320|30)(?:[,\.]\d{2})?\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches)
    
    return amounts

def get_performance_rating(time_per_page: float) -> str:
    """Obtener calificación de rendimiento"""
    if time_per_page < 0.5:
        return "Excelente"
    elif time_per_page < 2.0:
        return "Bueno"
    elif time_per_page < 5.0:
        return "Aceptable"
    else:
        return "Lento"

def validate_target_amounts_found(amounts_found: List[str], target_amounts: List[str]) -> Dict[str, Any]:
    """Validar que se encontraron los montos objetivo"""
    
    validation = {}
    found_count = 0
    
    for target in target_amounts:
        target_number = target.replace('S/ ', '')
        found = any(target_number in amount for amount in amounts_found)
        validation[target] = {
            'found': found,
            'matches': [amount for amount in amounts_found if target_number in amount]
        }
        if found:
            found_count += 1
    
    return {
        'targets': validation,
        'found_count': found_count,
        'total_targets': len(target_amounts),
        'success_rate': found_count / len(target_amounts),
        'validation_passed': found_count >= 2  # Al menos 2 de 3
    }

def generate_performance_summary(methods_tested: Dict[str, Any]) -> Dict[str, Any]:
    """Generar resumen de rendimiento"""
    
    successful_methods = []
    fastest_method = None
    slowest_method = None
    
    for method_name, results in methods_tested.items():
        if results.get('success', False):
            successful_methods.append(method_name)
            
            time_per_page = results.get('time_per_page', float('inf'))
            
            if fastest_method is None or time_per_page < methods_tested[fastest_method].get('time_per_page', float('inf')):
                fastest_method = method_name
            
            if slowest_method is None or time_per_page > methods_tested[slowest_method].get('time_per_page', 0):
                slowest_method = method_name
    
    return {
        'successful_methods': successful_methods,
        'failed_methods': [name for name, results in methods_tested.items() if not results.get('success', False)],
        'fastest_method': fastest_method,
        'slowest_method': slowest_method,
        'total_methods_tested': len(methods_tested)
    }

def generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generar recomendaciones basadas en resultados"""
    
    recommendations = []
    
    # Recomendaciones por validación
    validation = results.get('validation_results', {})
    if validation.get('success_rate', 0) < 0.6:
        recommendations.append("⚠️  Baja tasa de éxito - considerar ajustar parámetros de extracción")
        recommendations.append("💡 Revisar calidad del PDF original")
    
    if validation.get('success_rate', 0) == 1.0:
        recommendations.append("🎉 ¡Extracción perfecta! Todos los montos objetivo encontrados")
    
    # Recomendaciones por rendimiento
    performance = results.get('performance_summary', {})
    fastest_method = performance.get('fastest_method')
    
    if fastest_method:
        fastest_time = results['methods_tested'][fastest_method].get('time_per_page', 0)
        if fastest_time > 0.5:
            recommendations.append("⏰ Tiempo de extracción alto - considerar procesamiento en paralelo")
            recommendations.append("💾 Implementar caché para PDFs ya procesados")
        else:
            recommendations.append(f"⚡ Método más rápido: {fastest_method}")
    
    # Recomendaciones por métodos exitosos
    successful_methods = performance.get('successful_methods', [])
    if len(successful_methods) > 1:
        recommendations.append(f"✅ Múltiples métodos exitosos: {', '.join(successful_methods)}")
        recommendations.append("💡 Considerar usar el más rápido como método principal")
    
    if not successful_methods:
        recommendations.append("❌ Ningún método fue exitoso - revisar PDF y dependencias")
    
    return recommendations

def log_results_summary(results: Dict[str, Any]):
    """Log resumen de resultados"""
    
    logger.info(f"📊 RESUMEN DE RESULTADOS:")
    logger.info(f"   📄 PDF: {results['pdf_info']['name']}")
    logger.info(f"   📊 Páginas: {results['pdf_info']['pages']}")
    logger.info(f"   💾 Tamaño: {results['pdf_info']['size_mb']:.1f} MB")
    
    performance = results.get('performance_summary', {})
    logger.info(f"   ✅ Métodos exitosos: {len(performance.get('successful_methods', []))}")
    logger.info(f"   ❌ Métodos fallidos: {len(performance.get('failed_methods', []))}")
    
    validation = results.get('validation_results', {})
    logger.info(f"   🎯 Montos encontrados: {validation.get('found_count', 0)}/{validation.get('total_targets', 0)}")
    logger.info(f"   📈 Tasa de éxito: {validation.get('success_rate', 0):.1%}")
    
    if performance.get('fastest_method'):
        fastest_time = results['methods_tested'][performance['fastest_method']].get('time_per_page', 0)
        logger.info(f"   ⚡ Método más rápido: {performance['fastest_method']} ({fastest_time:.3f}s/página)")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test realista de rendimiento de extracción')
    parser.add_argument('pdf_path', help='Ruta al archivo PDF')
    parser.add_argument('--output', help='Archivo de salida JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not Path(args.pdf_path).exists():
        logger.error(f"❌ Archivo no encontrado: {args.pdf_path}")
        return 1
    
    try:
        logger.info("🧪 Iniciando test de rendimiento completo...")
        
        results = test_extraction_performance(args.pdf_path)
        
        if results.get('error'):
            logger.error(f"❌ Error en test: {results['error']}")
            return 1
        
        # Mostrar resultados
        print(f"\n{'='*80}")
        print("📊 RESULTADOS DEL TEST DE RENDIMIENTO REALISTA")
        print(f"{'='*80}")
        
        # Información del PDF
        pdf_info = results['pdf_info']
        print(f"📄 Archivo: {pdf_info['name']}")
        print(f"📊 Páginas: {pdf_info['pages']}")
        print(f"💾 Tamaño: {pdf_info['size_mb']:.1f} MB")
        
        # Métodos probados
        print(f"\n🔧 MÉTODOS PROBADOS:")
        for method_name, method_results in results['methods_tested'].items():
            status = "✅" if method_results.get('success') else "❌"
            time_info = f"{method_results.get('time_per_page', 0):.3f}s/página" if method_results.get('success') else "N/A"
            amounts = len(method_results.get('amounts_found', []))
            print(f"   {status} {method_name}: {time_info}, {amounts} montos")
        
        # Validación
        validation = results['validation_results']
        print(f"\n🎯 VALIDACIÓN DE MONTOS OBJETIVO:")
        print(f"   Encontrados: {validation['found_count']}/{validation['total_targets']}")
        print(f"   Tasa de éxito: {validation['success_rate']:.1%}")
        
        for target, info in validation['targets'].items():
            status = "✅" if info['found'] else "❌"
            matches = len(info['matches'])
            print(f"   {status} {target}: {matches} coincidencias")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        for rec in results['recommendations']:
            print(f"   {rec}")
        
        # Guardar resultados
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Resultados guardados en: {args.output}")
        
        print(f"\n✅ Test completado exitosamente")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 
#!/usr/bin/env python3
"""
Script de Extracción Mejorada con Integración de Pipeline
========================================================

Mejora los resultados de PaddleOCR con extracción robusta de tablas
para encontrar los montos específicos de viáticos.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def enhanced_extraction(pdf_path: str, ocr_results: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Mejora los resultados de PaddleOCR con extracción de tablas
    
    Args:
        pdf_path: Ruta al archivo PDF
        ocr_results: Resultados existentes de PaddleOCR (opcional)
    
    Returns:
        Diccionario con chunks mejorados
    """
    logger.info(f"🚀 Iniciando extracción mejorada para: {pdf_path}")
    
    # Verificar que el archivo existe
    if not Path(pdf_path).exists():
        logger.error(f"❌ Archivo no encontrado: {pdf_path}")
        return {"error": "Archivo no encontrado", "chunks": []}
    
    # 1. Usar resultados existentes de PaddleOCR si están disponibles
    base_text = ""
    ocr_chunks = []
    
    if ocr_results:
        base_text = ocr_results.get('text', '')
        ocr_chunks = ocr_results.get('chunks', [])
        logger.info(f"📄 Usando {len(ocr_chunks)} chunks existentes de OCR")
    else:
        logger.info("📄 No hay resultados de OCR previos, extrayendo solo tablas")
    
    # 2. Extraer tablas con el extractor robusto
    try:
        from src.ocr_pipeline.extractors.robust_table_extractor import RobustTableExtractor
        
        extractor = RobustTableExtractor(
            use_opencv_preprocessing=True,
            preprocessing_params={
                'threshold_type': 'adaptive',  # Mejor para PDFs escaneados
                'blur_kernel': (5, 5),
                'dilate_iterations': 2
            }
        )
        
        # Configurar logging detallado
        logging.getLogger('src.ocr_pipeline.extractors.robust_table_extractor').setLevel(logging.DEBUG)
        
        logger.info("🔍 Extrayendo tablas...")
        start_time = time.time()
        
        table_chunks = extractor.extract_from_pdf(pdf_path)
        
        extraction_time = time.time() - start_time
        logger.info(f"⏱️  Extracción completada en {extraction_time:.3f}s")
        logger.info(f"📊 {len(table_chunks)} chunks de tablas extraídos")
        
    except ImportError as e:
        logger.error(f"❌ Error importando extractor: {e}")
        logger.error("💡 Instalar dependencias: pip install camelot-py[cv] pdfplumber")
        return {"error": "Dependencias faltantes", "chunks": ocr_chunks}
    
    except Exception as e:
        logger.error(f"❌ Error en extracción de tablas: {e}")
        return {"error": str(e), "chunks": ocr_chunks}
    
    # 3. Fusionar con chunks existentes
    enhanced_chunks = merge_with_existing_chunks(ocr_chunks, table_chunks)
    
    # 4. Validar montos objetivo
    validation_results = validate_target_amounts(enhanced_chunks)
    
    # 5. Generar reporte
    report = generate_extraction_report(
        pdf_path, len(ocr_chunks), len(table_chunks), 
        len(enhanced_chunks), validation_results, extraction_time
    )
    
    return {
        "success": True,
        "chunks": enhanced_chunks,
        "validation": validation_results,
        "report": report,
        "stats": {
            "ocr_chunks": len(ocr_chunks),
            "table_chunks": len(table_chunks),
            "total_chunks": len(enhanced_chunks),
            "extraction_time": extraction_time
        }
    }

def merge_with_existing_chunks(ocr_chunks: List[Dict], table_chunks: List[Dict]) -> List[Dict]:
    """Fusionar chunks de OCR con chunks de tablas"""
    
    logger.info(f"🔄 Fusionando {len(ocr_chunks)} chunks OCR + {len(table_chunks)} chunks tablas")
    
    # Comenzar con chunks de OCR existentes
    merged_chunks = ocr_chunks.copy()
    
    # Agregar chunks de tablas con IDs únicos
    for i, table_chunk in enumerate(table_chunks):
        # Asegurar ID único
        table_chunk['id'] = f"table_enhanced_{i}"
        
        # Mantener formato compatible con sistema de búsqueda
        if 'content' in table_chunk and 'texto' not in table_chunk:
            table_chunk['texto'] = table_chunk['content']
        
        if 'metadata' in table_chunk and 'metadatos' not in table_chunk:
            table_chunk['metadatos'] = table_chunk['metadata']
        
        # Agregar marcadores para identificar origen
        table_chunk['metadatos']['enhanced_extraction'] = True
        table_chunk['metadatos']['chunk_source'] = 'table_extraction'
        
        merged_chunks.append(table_chunk)
    
    logger.info(f"✅ {len(merged_chunks)} chunks fusionados")
    return merged_chunks

def validate_target_amounts(chunks: List[Dict]) -> Dict[str, Any]:
    """Validar que se encontraron los montos objetivo"""
    
    target_amounts = {
        'S/ 380': {'found': False, 'chunks': []},
        'S/ 320': {'found': False, 'chunks': []},
        'S/ 30': {'found': False, 'chunks': []}
    }
    
    # Buscar en todos los chunks
    for chunk in chunks:
        chunk_text = ""
        
        # Obtener texto del chunk
        if 'texto' in chunk:
            chunk_text = chunk.get('texto', '')
        elif 'content' in chunk:
            chunk_text = chunk.get('content', '')
        
        # Buscar montos objetivo
        for target in target_amounts:
            if target in chunk_text or target.replace('S/ ', '') in chunk_text:
                target_amounts[target]['found'] = True
                target_amounts[target]['chunks'].append({
                    'chunk_id': chunk.get('id', chunk.get('chunk_id', 'unknown')),
                    'extraction_method': chunk.get('metadatos', {}).get('extraction_method', 'unknown'),
                    'confidence': chunk.get('metadatos', {}).get('confidence', 0.5)
                })
    
    # Calcular estadísticas
    found_count = sum(1 for target in target_amounts.values() if target['found'])
    success_rate = found_count / len(target_amounts)
    
    validation_result = {
        'targets': target_amounts,
        'found_count': found_count,
        'total_targets': len(target_amounts),
        'success_rate': success_rate,
        'validation_passed': success_rate >= 0.6  # Al menos 2 de 3 montos
    }
    
    # Log resultados
    logger.info(f"🎯 Validación de montos objetivo:")
    for target, info in target_amounts.items():
        status = "✅" if info['found'] else "❌"
        logger.info(f"   {status} {target}: {len(info['chunks'])} chunks")
    
    logger.info(f"📊 Tasa de éxito: {success_rate:.1%} ({found_count}/{len(target_amounts)})")
    
    return validation_result

def generate_extraction_report(pdf_path: str, ocr_chunks: int, table_chunks: int, 
                             total_chunks: int, validation: Dict, extraction_time: float) -> Dict[str, Any]:
    """Generar reporte de extracción"""
    
    return {
        'pdf_file': Path(pdf_path).name,
        'pdf_path': pdf_path,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'chunks_summary': {
            'ocr_chunks': ocr_chunks,
            'table_chunks': table_chunks,
            'total_chunks': total_chunks,
            'enhancement_ratio': f"{table_chunks}/{ocr_chunks}" if ocr_chunks > 0 else "N/A"
        },
        'extraction_performance': {
            'total_time_seconds': round(extraction_time, 3),
            'time_per_chunk': round(extraction_time / max(table_chunks, 1), 3),
            'performance_rating': 'Excelente' if extraction_time < 5 else 'Bueno' if extraction_time < 15 else 'Lento'
        },
        'validation_results': validation,
        'recommendations': generate_recommendations(validation, extraction_time)
    }

def generate_recommendations(validation: Dict, extraction_time: float) -> List[str]:
    """Generar recomendaciones basadas en resultados"""
    
    recommendations = []
    
    # Recomendaciones por validación
    if validation['success_rate'] < 0.6:
        recommendations.append("⚠️  Baja tasa de éxito - considerar ajustar parámetros de extracción")
        recommendations.append("💡 Revisar calidad del PDF original")
    
    if validation['success_rate'] == 1.0:
        recommendations.append("🎉 ¡Extracción perfecta! Todos los montos objetivo encontrados")
    
    # Recomendaciones por rendimiento
    if extraction_time > 15:
        recommendations.append("⏰ Tiempo de extracción alto - considerar procesamiento en paralelo")
        recommendations.append("💾 Implementar caché para PDFs ya procesados")
    
    if extraction_time < 2:
        recommendations.append("⚡ Excelente rendimiento de extracción")
    
    # Recomendaciones generales
    if not recommendations:
        recommendations.append("✅ Extracción exitosa sin problemas detectados")
    
    return recommendations

def test_extraction_performance(pdf_path: str) -> Dict[str, Any]:
    """Test realista considerando pre-procesamiento"""
    
    logger.info(f"🧪 Iniciando test de rendimiento para: {pdf_path}")
    
    try:
        # Información del PDF
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
        
        file_size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
        
        logger.info(f"📄 PDF: {num_pages} páginas, {file_size_mb:.1f} MB")
        
        # Test con diferentes métodos si Camelot está disponible
        timings = {}
        montos_encontrados = set()
        
        try:
            import camelot
            
            # 1. Sin pre-procesamiento (PDFs digitales)
            start = time.time()
            tables_digital = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
            timings['digital'] = (time.time() - start) / max(num_pages, 1)
            
            # 2. Con pre-procesamiento (PDFs escaneados)
            start = time.time()
            tables_scanned = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
            timings['scanned'] = (time.time() - start) / max(num_pages, 1)
            
            # 3. Verificar montos específicos
            montos_objetivo = ['S/ 380', 'S/ 320', 'S/ 30']
            
            for table in list(tables_digital) + list(tables_scanned):
                df = table.df
                for value in df.values.flatten():
                    str_val = str(value).strip()
                    if 'S/' in str_val or any(monto.replace('S/ ', '') in str_val for monto in montos_objetivo):
                        montos_encontrados.add(str_val)
            
        except ImportError:
            logger.warning("Camelot no disponible - usando extractor robusto")
            
            # Usar nuestro extractor robusto
            start = time.time()
            result = enhanced_extraction(pdf_path)
            extraction_time = time.time() - start
            
            timings['robust_extractor'] = extraction_time / max(num_pages, 1)
            
            if result.get('validation'):
                for target, info in result['validation']['targets'].items():
                    if info['found']:
                        montos_encontrados.add(target)
        
        # Resultados
        results = {
            'pdf_info': {
                'pages': num_pages,
                'size_mb': file_size_mb
            },
            'performance': timings,
            'amounts_found': list(montos_encontrados),
            'validation': {
                'S/ 380': 'S/ 380' in ' '.join(montos_encontrados) or '380' in ' '.join(montos_encontrados),
                'S/ 320': 'S/ 320' in ' '.join(montos_encontrados) or '320' in ' '.join(montos_encontrados),
                'S/ 30': 'S/ 30' in ' '.join(montos_encontrados) or '30' in ' '.join(montos_encontrados)
            }
        }
        
        # Log resultados
        logger.info(f"📊 RESULTADOS PARA {num_pages} PÁGINAS:")
        for method, time_per_page in timings.items():
            logger.info(f"⏱️  {method}: {time_per_page:.3f}s/página")
        
        logger.info(f"✅ Montos encontrados: {montos_encontrados}")
        
        # Validación
        montos_objetivo = ['S/ 380', 'S/ 320', 'S/ 30']
        for monto in montos_objetivo:
            if results['validation'].get(monto.replace('S/ ', '')) or any(monto in m for m in montos_encontrados):
                logger.info(f"✅ {monto} encontrado")
            else:
                logger.warning(f"❌ {monto} NO encontrado - REVISAR PARÁMETROS")
        
        # Advertencia si es muy lento
        if timings and min(timings.values()) > 0.5:
            logger.warning("⚠️  ADVERTENCIA: Excede 500ms/página")
            logger.info("   Sugerencias:")
            logger.info("   - Procesar en paralelo")
            logger.info("   - Reducir calidad de pre-procesamiento")
            logger.info("   - Usar caché para PDFs ya procesados")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en test de rendimiento: {e}")
        return {"error": str(e)}

def main():
    """Función principal del script"""
    
    parser = argparse.ArgumentParser(description='Extracción mejorada de tablas con validación de montos')
    parser.add_argument('--pdf', required=True, help='Ruta al archivo PDF')
    parser.add_argument('--validate-montos', action='store_true', help='Validar montos específicos')
    parser.add_argument('--test-performance', action='store_true', help='Ejecutar test de rendimiento')
    parser.add_argument('--output', help='Archivo de salida JSON (opcional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verificar archivo PDF
    if not Path(args.pdf).exists():
        logger.error(f"❌ Archivo no encontrado: {args.pdf}")
        return 1
    
    try:
        # Test de rendimiento
        if args.test_performance:
            logger.info("🧪 Ejecutando test de rendimiento...")
            performance_results = test_extraction_performance(args.pdf)
            
            print("\n" + "="*60)
            print("📊 RESULTADOS DEL TEST DE RENDIMIENTO")
            print("="*60)
            print(json.dumps(performance_results, indent=2, ensure_ascii=False))
        
        # Extracción principal
        logger.info("🚀 Ejecutando extracción mejorada...")
        results = enhanced_extraction(args.pdf)
        
        if results.get('error'):
            logger.error(f"❌ Error en extracción: {results['error']}")
            return 1
        
        # Mostrar resultados
        print("\n" + "="*60)
        print("📋 RESULTADOS DE EXTRACCIÓN MEJORADA")
        print("="*60)
        
        print(f"📄 Archivo: {Path(args.pdf).name}")
        print(f"📊 Chunks totales: {results['stats']['total_chunks']}")
        print(f"⏱️  Tiempo: {results['stats']['extraction_time']:.3f}s")
        
        if args.validate_montos:
            validation = results['validation']
            print(f"\n🎯 VALIDACIÓN DE MONTOS:")
            print(f"   Encontrados: {validation['found_count']}/{validation['total_targets']}")
            print(f"   Tasa de éxito: {validation['success_rate']:.1%}")
            
            for target, info in validation['targets'].items():
                status = "✅" if info['found'] else "❌"
                print(f"   {status} {target}: {len(info['chunks'])} chunks")
        
        # Guardar resultados si se especifica
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Resultados guardados en: {args.output}")
        
        print("\n✅ Extracción completada exitosamente")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 
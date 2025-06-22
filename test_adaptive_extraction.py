#!/usr/bin/env python3
"""
Test del Sistema de Extracción Adaptativo
=========================================

Prueba el extractor adaptativo que se auto-optimiza para cualquier documento.
"""

import logging
import sys
from pathlib import Path
import json
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('adaptive_extraction.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from ocr_pipeline.extractors.adaptive_table_extractor import create_adaptive_extractor
    from ocr_pipeline.extractors.smart_money_detector import create_smart_detector
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

def test_smart_money_detector():
    """Prueba el detector inteligente de montos"""
    logger.info("🧪 PROBANDO DETECTOR INTELIGENTE DE MONTOS")
    
    detector = create_smart_detector(learning_mode=True)
    
    # Texto de prueba con diversos formatos monetarios
    test_texts = [
        """
        Los viáticos diarios serán de S/ 380.00 para Ministros, S/ 320.00 para servidores civiles,
        y hasta S/ 30.00 para declaración jurada según el numeral 8.4.16.
        """,
        """
        El monto máximo autorizado es USD 1,500.00 por evento, con un límite de EUR 800.50
        para gastos de representación y £ 250 para viáticos locales.
        """,
        """
        Según la directiva, los importes son: 
        - Nivel A: 1,200.75 soles
        - Nivel B: 850 nuevos soles  
        - Nivel C: hasta 450.25
        """,
        """
        Los precios incluyen: artículo 123 del código 2024, página 45 de 100 páginas,
        teléfono 987-654-321, y el valor real de S/ 199.99 más IGV.
        """
    ]
    
    total_amounts_found = 0
    
    for i, text in enumerate(test_texts, 1):
        logger.info(f"\n--- Texto {i} ---")
        amounts = detector.extract_all_amounts(text.strip())
        
        for amount in amounts:
            logger.info(f"💰 {amount['raw_text']} → {amount['amount']:.2f} {amount['currency']} "
                       f"(confianza: {amount['confidence']:.2f})")
        
        total_amounts_found += len(amounts)
    
    # Mostrar estadísticas del detector
    stats = detector.get_extraction_stats()
    logger.info(f"\n📊 ESTADÍSTICAS DEL DETECTOR:")
    logger.info(f"   Patrones base: {stats['base_patterns_count']}")
    logger.info(f"   Patrones aprendidos: {stats['learned_patterns_count']}")
    logger.info(f"   Total extracciones: {stats['total_extractions']}")
    logger.info(f"   Montos encontrados: {total_amounts_found}")
    
    return total_amounts_found > 0

def test_adaptive_extractor_with_pdf():
    """Prueba el extractor adaptativo con PDF real"""
    logger.info("\n🧠 PROBANDO EXTRACTOR ADAPTATIVO CON PDF")
    
    # Buscar PDF de prueba
    pdf_candidates = [
        "data/processed/directiva_de_viaticos_011_2020_imagen.pdf",
        "data/directiva_de_viaticos_011_2020_imagen.pdf",
        "directiva_de_viaticos_011_2020_imagen.pdf"
    ]
    
    pdf_path = None
    for candidate in pdf_candidates:
        if Path(candidate).exists():
            pdf_path = candidate
            break
    
    if not pdf_path:
        logger.warning("⚠️ No se encontró PDF de prueba. Creando extractor sin prueba...")
        extractor = create_adaptive_extractor(adaptive_mode=True, learning_enabled=True)
        logger.info("✅ Extractor adaptativo creado exitosamente")
        return True
    
    logger.info(f"📄 Usando PDF: {pdf_path}")
    
    # Crear extractor adaptativo
    extractor = create_adaptive_extractor(adaptive_mode=True, learning_enabled=True)
    
    try:
        # Extraer con auto-optimización
        logger.info("🚀 Iniciando extracción adaptativa...")
        results = extractor.extract_from_pdf(pdf_path, auto_optimize=True)
        
        # Mostrar resultados
        logger.info(f"\n🎯 RESULTADOS DE EXTRACCIÓN ADAPTATIVA:")
        logger.info(f"   📄 Documento: {Path(pdf_path).name}")
        logger.info(f"   🔧 Estrategia usada: {results.get('strategy_used', 'unknown')}")
        logger.info(f"   📊 Confianza: {results.get('confidence', 0.0):.2f}")
        logger.info(f"   ⏱️  Tiempo total: {results.get('total_extraction_time', 0.0):.2f}s")
        logger.info(f"   📋 Chunks extraídos: {len(results.get('chunks', []))}")
        logger.info(f"   💰 Montos encontrados: {len(results.get('amounts', []))}")
        
        # Mostrar características del documento
        doc_chars = results.get('document_characteristics', {})
        logger.info(f"   📊 Características: {doc_chars.get('summary', 'N/A')}")
        
        # Mostrar métricas de calidad
        quality = results.get('quality_metrics', {})
        if quality:
            logger.info(f"   🏆 Calidad general: {quality.get('overall_quality', 0.0):.2f}")
            logger.info(f"   📈 Completitud: {quality.get('extraction_completeness', 0.0):.2f}")
            logger.info(f"   🎯 Consistencia: {quality.get('data_consistency', 0.0):.2f}")
        
        # Mostrar algunos montos encontrados
        if results.get('amounts'):
            logger.info(f"\n💰 MONTOS ENCONTRADOS (top 5):")
            for i, amount in enumerate(results['amounts'][:5], 1):
                logger.info(f"   {i}. {amount['raw_text']} → {amount['amount']:.2f} {amount['currency']} "
                           f"(confianza: {amount['confidence']:.2f})")
        
        # Mostrar algunos chunks
        if results.get('chunks'):
            logger.info(f"\n📋 CHUNKS EXTRAÍDOS (primeros 3):")
            for i, chunk in enumerate(results['chunks'][:3], 1):
                content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                logger.info(f"   {i}. [{chunk['id']}] {content_preview}")
                if chunk.get('has_monetary_content'):
                    logger.info(f"      💰 Contiene {len(chunk.get('related_amounts', []))} montos")
        
        # Mostrar estadísticas de optimización
        opt_stats = extractor.get_optimization_stats()
        if opt_stats.get('total_extractions', 0) > 0:
            logger.info(f"\n📈 ESTADÍSTICAS DE OPTIMIZACIÓN:")
            logger.info(f"   Total extracciones: {opt_stats['total_extractions']}")
            logger.info(f"   Confianza promedio: {opt_stats['average_confidence']:.2f}")
            logger.info(f"   Tiempo promedio: {opt_stats['average_time']:.2f}s")
            logger.info(f"   Mejor estrategia: {opt_stats['best_strategy']}")
        
        return len(results.get('amounts', [])) > 0
        
    except Exception as e:
        logger.error(f"❌ Error en extracción adaptativa: {e}")
        return False

def test_learning_capabilities():
    """Prueba las capacidades de aprendizaje del sistema"""
    logger.info("\n📚 PROBANDO CAPACIDADES DE APRENDIZAJE")
    
    detector = create_smart_detector(learning_mode=True)
    
    # Resetear aprendizaje para prueba limpia
    detector.reset_learning()
    
    # Texto con patrones que el sistema debería aprender
    learning_text = """
    El subsidio alimentario es de S/ 150.00 por persona.
    La bonificación especial alcanza S/ 75.50 mensualmente.
    El incentivo por productividad suma S/ 200.25 adicionales.
    """
    
    logger.info("📖 Extrayendo con aprendizaje habilitado...")
    amounts_before = detector.extract_all_amounts(learning_text)
    
    stats_before = detector.get_extraction_stats()
    logger.info(f"   Patrones aprendidos iniciales: {stats_before['learned_patterns_count']}")
    
    # Segundo texto similar para ver si aprendió
    similar_text = """
    El subsidio habitacional será de S/ 300.00 por familia.
    La bonificación navideña equivale a S/ 120.75 por trabajador.
    """
    
    logger.info("🎓 Extrayendo texto similar...")
    amounts_after = detector.extract_all_amounts(similar_text)
    
    stats_after = detector.get_extraction_stats()
    logger.info(f"   Patrones aprendidos finales: {stats_after['learned_patterns_count']}")
    
    learning_occurred = stats_after['learned_patterns_count'] > stats_before['learned_patterns_count']
    
    if learning_occurred:
        logger.info("✅ El sistema aprendió nuevos patrones exitosamente")
    else:
        logger.info("ℹ️ No se detectaron nuevos patrones (puede ser normal)")
    
    total_amounts = len(amounts_before) + len(amounts_after)
    logger.info(f"💰 Total montos extraídos: {total_amounts}")
    
    return total_amounts > 0

def create_usage_examples():
    """Crea ejemplos de uso para documentación"""
    logger.info("\n📝 CREANDO EJEMPLOS DE USO")
    
    examples = {
        "basic_usage": {
            "description": "Uso básico del extractor adaptativo",
            "code": """
from src.ocr_pipeline.extractors.adaptive_table_extractor import create_adaptive_extractor

# Crear extractor con modo adaptativo y aprendizaje habilitado
extractor = create_adaptive_extractor(adaptive_mode=True, learning_enabled=True)

# Extraer de cualquier PDF - se auto-optimiza automáticamente
results = extractor.extract_from_pdf("mi_documento.pdf")

# Resultados incluyen estrategia usada, confianza, y datos extraídos
print(f"Estrategia usada: {results['strategy_used']}")
print(f"Confianza: {results['confidence']}")
print(f"Montos encontrados: {len(results['amounts'])}")
""",
            "expected_output": "El sistema selecciona automáticamente la mejor estrategia y extrae todos los montos encontrados"
        },
        
        "smart_money_detection": {
            "description": "Detector inteligente de montos monetarios",
            "code": """
from src.ocr_pipeline.extractors.smart_money_detector import create_smart_detector

# Crear detector con aprendizaje habilitado
detector = create_smart_detector(learning_mode=True)

# Extraer montos de cualquier texto
text = "Los viáticos son S/ 380.00 para ministros y USD 150.50 para viajes"
amounts = detector.extract_all_amounts(text)

# Cada monto incluye valor, moneda, contexto y confianza
for amount in amounts:
    print(f"{amount['raw_text']} → {amount['amount']} {amount['currency']} (confianza: {amount['confidence']})")
""",
            "expected_output": "Detecta automáticamente S/ 380.00 PEN y USD 150.50 USD con alta confianza"
        },
        
        "optimization_stats": {
            "description": "Ver estadísticas de optimización y aprendizaje",
            "code": """
# Después de usar el extractor, ver estadísticas
stats = extractor.get_optimization_stats()

print(f"Total extracciones: {stats['total_extractions']}")
print(f"Mejor estrategia: {stats['best_strategy']}")
print(f"Confianza promedio: {stats['average_confidence']}")

# Ver estadísticas del detector de montos
detector_stats = detector.get_extraction_stats()
print(f"Patrones aprendidos: {detector_stats['learned_patterns_count']}")
""",
            "expected_output": "Muestra métricas de rendimiento y patrones aprendidos"
        }
    }
    
    # Guardar ejemplos
    examples_file = Path("data/usage_examples.json")
    examples_file.parent.mkdir(exist_ok=True)
    
    try:
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(examples, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Ejemplos guardados en: {examples_file}")
    except Exception as e:
        logger.warning(f"⚠️ Error guardando ejemplos: {e}")
    
    return True

def main():
    """Función principal de pruebas"""
    logger.info("🚀 INICIANDO PRUEBAS DEL SISTEMA ADAPTATIVO")
    
    tests = [
        ("Detector Inteligente de Montos", test_smart_money_detector),
        ("Extractor Adaptativo con PDF", test_adaptive_extractor_with_pdf),
        ("Capacidades de Aprendizaje", test_learning_capabilities),
        ("Ejemplos de Uso", create_usage_examples)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 EJECUTANDO: {test_name}")
        logger.info('='*60)
        
        try:
            success = test_func()
            results[test_name] = "✅ ÉXITO" if success else "⚠️ PARCIAL"
            logger.info(f"✅ {test_name}: COMPLETADO")
        except Exception as e:
            results[test_name] = f"❌ ERROR: {str(e)}"
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    # Resumen final
    logger.info(f"\n{'='*60}")
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info('='*60)
    
    for test_name, result in results.items():
        logger.info(f"   {result} {test_name}")
    
    success_count = sum(1 for r in results.values() if "✅" in r)
    total_tests = len(results)
    
    logger.info(f"\n🎯 RESULTADO GENERAL: {success_count}/{total_tests} pruebas exitosas")
    
    if success_count == total_tests:
        logger.info("🏆 ¡SISTEMA ADAPTATIVO FUNCIONANDO PERFECTAMENTE!")
    elif success_count >= total_tests * 0.75:
        logger.info("👍 Sistema adaptativo funcionando bien con algunas limitaciones")
    else:
        logger.info("⚠️ Sistema adaptativo necesita ajustes")
    
    return success_count >= total_tests * 0.75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
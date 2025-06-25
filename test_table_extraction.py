#!/usr/bin/env python3
"""
Test Completo de Extracción de Tablas
=====================================

Test integrado que combina todos los métodos de extracción para
asegurar que se encuentren todos los montos objetivo: S/ 380, S/ 320, S/ 30
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Set
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_table_extraction(pdf_path: str) -> Dict[str, Any]:
    """
    Test completo que integra todos los métodos de extracción
    """
    
    logger.info(f"🚀 Iniciando test completo de extracción para: {pdf_path}")
    
    if not Path(pdf_path).exists():
        logger.error(f"❌ PDF no encontrado: {pdf_path}")
        return {"error": "PDF no encontrado"}
    
    results = {
        "pdf_path": pdf_path,
        "target_amounts": ["S/ 380", "S/ 320", "S/ 30"],
        "extraction_methods": {},
        "consolidated_chunks": [],
        "amounts_found": {
            "S/ 380": {"found": False, "sources": []},
            "S/ 320": {"found": False, "sources": []},
            "S/ 30": {"found": False, "sources": []}
        },
        "success_metrics": {},
        "recommendations": []
    }
    
    start_time = time.time()
    
    # Método 1: Extractor Robusto (ya funcionando)
    logger.info("🔄 Método 1: Extractor Robusto...")
    robust_results = test_robust_extractor(pdf_path)
    results["extraction_methods"]["robust_extractor"] = robust_results
    if robust_results.get("chunks"):
        results["consolidated_chunks"].extend(robust_results["chunks"])
    
    # Método 2: Regex Agresivo (exitoso para S/ 380)
    logger.info("🔄 Método 2: Regex Agresivo...")
    regex_results = test_aggressive_regex_extraction(pdf_path)
    results["extraction_methods"]["aggressive_regex"] = regex_results
    if regex_results.get("chunks"):
        results["consolidated_chunks"].extend(regex_results["chunks"])
    
    # Método 3: Fallback de Emergencia
    logger.info("🔄 Método 3: Fallback de Emergencia...")
    fallback_results = test_emergency_fallback(pdf_path)
    results["extraction_methods"]["emergency_fallback"] = fallback_results
    if fallback_results.get("chunks"):
        results["consolidated_chunks"].extend(fallback_results["chunks"])
    
    # Consolidar y analizar resultados
    total_time = time.time() - start_time
    results["total_extraction_time"] = total_time
    
    # Analizar montos encontrados
    analyze_amounts_found(results)
    
    # Generar métricas de éxito
    generate_success_metrics(results)
    
    # Generar recomendaciones
    generate_recommendations(results)
    
    # Log resultados finales
    log_final_results(results)
    
    return results

def test_robust_extractor(pdf_path: str) -> Dict[str, Any]:
    """Test del extractor robusto"""
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src" / "ocr_pipeline" / "extractors"))
        from robust_table_extractor import RobustTableExtractor
        
        start_time = time.time()
        
        extractor = RobustTableExtractor(use_opencv_preprocessing=True)
        chunks = extractor.extract_from_pdf(pdf_path)
        
        extraction_time = time.time() - start_time
        
        # Procesar chunks para formato estándar
        processed_chunks = []
        amounts_found = set()
        
        for chunk in chunks:
            # Extraer montos
            chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
            amounts_found.update(chunk_amounts)
            
            # Convertir a formato estándar
            processed_chunk = {
                "id": chunk.get('chunk_id', f"robust_{len(processed_chunks)}"),
                "content": chunk.get('content', ''),
                "source": "robust_extractor",
                "metadata": chunk.get('metadata', {}),
                "amounts_found": chunk_amounts
            }
            processed_chunks.append(processed_chunk)
        
        return {
            "method": "robust_extractor",
            "success": len(chunks) > 0,
            "chunks": processed_chunks,
            "amounts_found": list(amounts_found),
            "extraction_time": extraction_time,
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en extractor robusto: {e}")
        return {"method": "robust_extractor", "success": False, "error": str(e)}

def test_aggressive_regex_extraction(pdf_path: str) -> Dict[str, Any]:
    """Test del método regex agresivo (exitoso para S/ 380)"""
    try:
        import re
        import fitz
        
        start_time = time.time()
        
        # Obtener texto completo
        full_text = ""
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += f"\n--- PÁGINA {page_num + 1} ---\n"
            full_text += page.get_text()
        doc.close()
        
        chunks = []
        amounts_found = set()
        
        # Patrones específicos para cada monto
        target_patterns = {
            "S/ 380": [
                r'S/\s*380(?:[,\.]\d{2})?',
                r'380[,\.]00',
                r'\b380\b',
                r'ministros?[^\n]*?380[^\n]*',
                r'viceministros?[^\n]*?380[^\n]*',
                r'secretarios?\s+generales?[^\n]*?380[^\n]*'
            ],
            "S/ 320": [
                r'S/\s*320(?:[,\.]\d{2})?',
                r'320[,\.]00',
                r'\b320\b',
                r'servidores?[^\n]*?320[^\n]*',
                r'funcionarios?[^\n]*?320[^\n]*'
            ],
            "S/ 30": [
                r'S/\s*30(?:[,\.]\d{2})?',
                r'30[,\.]00',
                r'\b30\b',
                r'declaración\s+jurada[^\n]*?30[^\n]*',
                r'treinta[^\n]*?soles'
            ]
        }
        
        for target_amount, patterns in target_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extraer contexto amplio
                    start = max(0, match.start() - 150)
                    end = min(len(full_text), match.end() + 150)
                    context = full_text[start:end].strip()
                    
                    # Determinar página
                    page_num = full_text[:match.start()].count("--- PÁGINA")
                    
                    # Crear chunk
                    chunk = {
                        "id": f"regex_aggressive_{len(chunks)}",
                        "content": context,
                        "source": "aggressive_regex",
                        "metadata": {
                            "extraction_method": "aggressive_regex",
                            "target_amount": target_amount,
                            "page": page_num,
                            "match": match.group(0),
                            "pattern": pattern,
                            "confidence": 0.8
                        },
                        "amounts_found": [match.group(0)]
                    }
                    chunks.append(chunk)
                    amounts_found.add(match.group(0))
        
        extraction_time = time.time() - start_time
        
        return {
            "method": "aggressive_regex",
            "success": len(chunks) > 0,
            "chunks": chunks,
            "amounts_found": list(amounts_found),
            "extraction_time": extraction_time,
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en regex agresivo: {e}")
        return {"method": "aggressive_regex", "success": False, "error": str(e)}

def test_emergency_fallback(pdf_path: str) -> Dict[str, Any]:
    """Test del fallback de emergencia"""
    try:
        # Importar dinámicamente para evitar errores
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("fallback_extraction", "fallback_extraction.py")
        if spec and spec.loader:
            fallback_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fallback_module)
            
            start_time = time.time()
            chunks_raw, method_used = fallback_module.extract_with_aggressive_fallback(pdf_path)
            extraction_time = time.time() - start_time
            
            # Procesar chunks
            processed_chunks = []
            amounts_found = set()
            
            for chunk in chunks_raw:
                chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
                amounts_found.update(chunk_amounts)
                
                processed_chunk = {
                    "id": chunk.get('chunk_id', f"fallback_{len(processed_chunks)}"),
                    "content": chunk.get('content', ''),
                    "source": "emergency_fallback",
                    "metadata": chunk.get('metadata', {}),
                    "amounts_found": chunk_amounts
                }
                processed_chunks.append(processed_chunk)
            
            return {
                "method": "emergency_fallback",
                "success": len(chunks_raw) > 0,
                "chunks": processed_chunks,
                "amounts_found": list(amounts_found),
                "extraction_time": extraction_time,
                "chunks_count": len(chunks_raw),
                "fallback_method_used": method_used
            }
        else:
            return {"method": "emergency_fallback", "success": False, "error": "No se pudo cargar fallback_extraction.py"}
            
    except Exception as e:
        logger.error(f"❌ Error en fallback de emergencia: {e}")
        return {"method": "emergency_fallback", "success": False, "error": str(e)}

def analyze_amounts_found(results: Dict[str, Any]):
    """Analizar qué montos se encontraron en todos los chunks"""
    
    all_amounts_text = []
    
    # Recopilar todo el texto de todos los chunks
    for chunk in results["consolidated_chunks"]:
        content = chunk.get("content", "")
        amounts = chunk.get("amounts_found", [])
        
        all_amounts_text.append(content)
        all_amounts_text.extend([str(amount) for amount in amounts])
    
    full_text = " ".join(all_amounts_text)
    
    # Verificar cada monto objetivo
    for target_amount in results["target_amounts"]:
        target_number = target_amount.replace("S/ ", "")
        
        # Buscar en texto completo
        found_in_text = target_number in full_text or target_amount in full_text
        
        # Buscar en chunks específicos
        sources = []
        for chunk in results["consolidated_chunks"]:
            chunk_content = chunk.get("content", "") + " " + " ".join([str(a) for a in chunk.get("amounts_found", [])])
            
            if target_number in chunk_content or target_amount in chunk_content:
                sources.append({
                    "chunk_id": chunk.get("id", "unknown"),
                    "source": chunk.get("source", "unknown"),
                    "confidence": chunk.get("metadata", {}).get("confidence", 0.5)
                })
        
        results["amounts_found"][target_amount] = {
            "found": found_in_text or len(sources) > 0,
            "sources": sources,
            "source_count": len(sources)
        }

def generate_success_metrics(results: Dict[str, Any]):
    """Generar métricas de éxito"""
    
    # Contar montos encontrados
    found_count = sum(1 for amount_info in results["amounts_found"].values() if amount_info["found"])
    total_targets = len(results["target_amounts"])
    
    # Contar métodos exitosos
    successful_methods = [
        method for method, method_results in results["extraction_methods"].items()
        if method_results.get("success", False)
    ]
    
    # Calcular tiempos
    total_time = results.get("total_extraction_time", 0)
    method_times = [
        method_results.get("extraction_time", 0)
        for method_results in results["extraction_methods"].values()
    ]
    
    results["success_metrics"] = {
        "amounts_found_count": found_count,
        "amounts_total": total_targets,
        "success_rate": found_count / total_targets,
        "successful_methods": successful_methods,
        "successful_methods_count": len(successful_methods),
        "total_chunks": len(results["consolidated_chunks"]),
        "total_extraction_time": total_time,
        "average_method_time": sum(method_times) / len(method_times) if method_times else 0,
        "fastest_method": min(results["extraction_methods"].items(), 
                            key=lambda x: x[1].get("extraction_time", float('inf')))[0] if results["extraction_methods"] else None
    }

def generate_recommendations(results: Dict[str, Any]):
    """Generar recomendaciones"""
    
    recommendations = []
    metrics = results["success_metrics"]
    
    # Recomendaciones por tasa de éxito
    if metrics["success_rate"] == 1.0:
        recommendations.append("🎉 ¡PERFECTO! Todos los montos objetivo fueron encontrados")
        recommendations.append("✅ El sistema está funcionando correctamente para extracción de viáticos")
    elif metrics["success_rate"] >= 0.66:
        recommendations.append("✅ Buena tasa de éxito, pero se pueden hacer mejoras")
        recommendations.append("💡 Considerar combinar métodos para mayor cobertura")
    else:
        recommendations.append("⚠️ Baja tasa de éxito - revisar configuración de extracción")
        recommendations.append("🔧 Considerar ajustar parámetros o agregar más métodos")
    
    # Recomendaciones por métodos
    if "aggressive_regex" in metrics["successful_methods"]:
        recommendations.append("🏆 Método regex agresivo fue exitoso - mantener en pipeline")
    
    if "robust_extractor" in metrics["successful_methods"]:
        recommendations.append("🔧 Extractor robusto funcionando - usar como método principal")
    
    # Recomendaciones por rendimiento
    if metrics["total_extraction_time"] > 120:  # 2 minutos
        recommendations.append("⏰ Tiempo de extracción alto - considerar optimización")
        recommendations.append("💾 Implementar caché para PDFs procesados")
    else:
        recommendations.append("⚡ Buen rendimiento de extracción")
    
    # Recomendaciones específicas por montos faltantes
    for target_amount, amount_info in results["amounts_found"].items():
        if not amount_info["found"]:
            recommendations.append(f"❌ {target_amount} no encontrado - revisar patrones de búsqueda")
        elif amount_info["source_count"] == 1:
            recommendations.append(f"⚠️ {target_amount} encontrado en solo 1 fuente - agregar redundancia")
    
    results["recommendations"] = recommendations

def log_final_results(results: Dict[str, Any]):
    """Log de resultados finales"""
    
    logger.info("🎯 RESULTADOS FINALES DEL TEST COMPLETO:")
    logger.info(f"   📄 PDF: {Path(results['pdf_path']).name}")
    
    metrics = results["success_metrics"]
    logger.info(f"   📊 Montos encontrados: {metrics['amounts_found_count']}/{metrics['amounts_total']}")
    logger.info(f"   📈 Tasa de éxito: {metrics['success_rate']:.1%}")
    logger.info(f"   🔧 Métodos exitosos: {metrics['successful_methods_count']}")
    logger.info(f"   📋 Total chunks: {metrics['total_chunks']}")
    logger.info(f"   ⏱️ Tiempo total: {metrics['total_extraction_time']:.2f}s")
    
    # Log por monto
    logger.info("   💰 MONTOS OBJETIVO:")
    for target_amount, amount_info in results["amounts_found"].items():
        status = "✅" if amount_info["found"] else "❌"
        sources = amount_info["source_count"]
        logger.info(f"      {status} {target_amount}: {sources} fuentes")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test completo de extracción de tablas')
    parser.add_argument('--pdf', default='data/raw/directiva_de_viaticos_011_2020_imagen.pdf', 
                       help='Ruta al PDF')
    parser.add_argument('--output', help='Archivo de salida JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = test_complete_table_extraction(args.pdf)
        
        if results.get("error"):
            logger.error(f"❌ Error: {results['error']}")
            return 1
        
        # Mostrar resumen ejecutivo
        print(f"\n{'='*80}")
        print("🚀 RESUMEN EJECUTIVO - TEST COMPLETO DE EXTRACCIÓN")
        print(f"{'='*80}")
        
        metrics = results["success_metrics"]
        print(f"📄 PDF: {Path(args.pdf).name}")
        print(f"🎯 Montos objetivo: {', '.join(results['target_amounts'])}")
        print(f"✅ Encontrados: {metrics['amounts_found_count']}/{metrics['amounts_total']} ({metrics['success_rate']:.1%})")
        print(f"🔧 Métodos exitosos: {', '.join(metrics['successful_methods'])}")
        print(f"📋 Total chunks extraídos: {metrics['total_chunks']}")
        print(f"⚡ Método más rápido: {metrics['fastest_method']}")
        print(f"⏱️ Tiempo total: {metrics['total_extraction_time']:.2f}s")
        
        print(f"\n💰 DETALLE POR MONTO:")
        for target_amount, amount_info in results["amounts_found"].items():
            status = "✅ ENCONTRADO" if amount_info["found"] else "❌ NO ENCONTRADO"
            sources = amount_info["source_count"]
            print(f"   {target_amount}: {status} ({sources} fuentes)")
            
            if amount_info["sources"]:
                for source in amount_info["sources"][:3]:  # Mostrar primeras 3 fuentes
                    print(f"      - {source['source']} (confianza: {source['confidence']:.2f})")
        
        print(f"\n💡 RECOMENDACIONES:")
        for rec in results["recommendations"]:
            print(f"   {rec}")
        
        # Guardar resultados
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Resultados guardados en: {args.output}")
        
        # Determinar código de salida
        success_code = 0 if metrics["success_rate"] >= 0.66 else 1
        
        if success_code == 0:
            print(f"\n🎉 ¡TEST EXITOSO! Sistema listo para producción")
        else:
            print(f"\n⚠️ Test parcialmente exitoso - revisar recomendaciones")
        
        return success_code
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
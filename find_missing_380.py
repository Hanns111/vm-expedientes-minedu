#!/usr/bin/env python3
"""
Búsqueda Exhaustiva del Monto S/ 380 Faltante
=============================================

Script que usa múltiples métodos para encontrar el monto S/ 380 que falta
en la extracción de la directiva de viáticos.
"""

import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Set
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_missing_380(pdf_path: str) -> Dict[str, Any]:
    """
    Búsqueda exhaustiva del monto S/ 380 usando múltiples métodos
    """
    
    logger.info(f"🔍 Iniciando búsqueda exhaustiva de S/ 380 en: {pdf_path}")
    
    if not Path(pdf_path).exists():
        logger.error(f"❌ PDF no encontrado: {pdf_path}")
        return {"error": "PDF no encontrado"}
    
    results = {
        "pdf_path": pdf_path,
        "target_amount": "S/ 380",
        "methods_tried": {},
        "found_instances": [],
        "best_method": None,
        "success": False
    }
    
    # Método 1: PyMuPDF (texto directo)
    logger.info("🔄 Método 1: PyMuPDF texto directo...")
    pymupdf_results = search_with_pymupdf(pdf_path)
    results["methods_tried"]["pymupdf"] = pymupdf_results
    if pymupdf_results["found"]:
        results["found_instances"].extend(pymupdf_results["instances"])
    
    # Método 2: PDFplumber (texto + tablas)
    logger.info("🔄 Método 2: PDFplumber texto + tablas...")
    pdfplumber_results = search_with_pdfplumber(pdf_path)
    results["methods_tried"]["pdfplumber"] = pdfplumber_results
    if pdfplumber_results["found"]:
        results["found_instances"].extend(pdfplumber_results["instances"])
    
    # Método 3: Camelot (tablas estructuradas)
    logger.info("🔄 Método 3: Camelot tablas estructuradas...")
    camelot_results = search_with_camelot(pdf_path)
    results["methods_tried"]["camelot"] = camelot_results
    if camelot_results["found"]:
        results["found_instances"].extend(camelot_results["instances"])
    
    # Método 4: Regex agresivo en texto completo
    logger.info("🔄 Método 4: Regex agresivo...")
    regex_results = search_with_aggressive_regex(pdf_path)
    results["methods_tried"]["regex_aggressive"] = regex_results
    if regex_results["found"]:
        results["found_instances"].extend(regex_results["instances"])
    
    # Método 5: OCR con Tesseract (si está disponible)
    logger.info("🔄 Método 5: OCR con Tesseract...")
    try:
        ocr_results = search_with_tesseract_ocr(pdf_path)
        results["methods_tried"]["tesseract_ocr"] = ocr_results
        if ocr_results["found"]:
            results["found_instances"].extend(ocr_results["instances"])
    except Exception as e:
        logger.warning(f"❌ Tesseract OCR no disponible: {e}")
        results["methods_tried"]["tesseract_ocr"] = {"error": str(e), "found": False}
    
    # Método 6: Búsqueda por patrones de contexto
    logger.info("🔄 Método 6: Búsqueda por contexto...")
    context_results = search_with_context_patterns(pdf_path)
    results["methods_tried"]["context_patterns"] = context_results
    if context_results["found"]:
        results["found_instances"].extend(context_results["instances"])
    
    # Analizar resultados
    results["success"] = len(results["found_instances"]) > 0
    
    if results["success"]:
        # Determinar el mejor método
        method_scores = {}
        for method, method_results in results["methods_tried"].items():
            if method_results.get("found", False):
                score = len(method_results.get("instances", []))
                method_scores[method] = score
        
        if method_scores:
            results["best_method"] = max(method_scores, key=method_scores.get)
    
    # Log resultados
    log_search_results(results)
    
    return results

def search_with_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda con PyMuPDF"""
    try:
        import fitz
        
        start_time = time.time()
        instances = []
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Buscar patrones de 380
            patterns = [
                r'S/\s*380(?:[,\.]\d{2})?',
                r'380[,\.]00',
                r'380\s*soles',
                r'trescientos\s+ochenta',
                r'ministros?[^\n]*380',
                r'viceministros?[^\n]*380',
                r'secretarios?\s+generales?[^\n]*380'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extraer contexto
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    instances.append({
                        "page": page_num + 1,
                        "match": match.group(0),
                        "context": context,
                        "pattern": pattern,
                        "position": match.span()
                    })
        
        doc.close()
        
        return {
            "method": "pymupdf",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time,
            "pages_processed": len(doc)
        }
        
    except Exception as e:
        return {"method": "pymupdf", "found": False, "error": str(e)}

def search_with_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda con PDFplumber"""
    try:
        import pdfplumber
        
        start_time = time.time()
        instances = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extraer texto
                text = page.extract_text() or ""
                
                # Buscar en texto
                text_instances = find_380_in_text(text, page_num + 1, "pdfplumber_text")
                instances.extend(text_instances)
                
                # Extraer tablas
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        table_text = ""
                        for row in table:
                            if row:
                                table_text += " ".join([str(cell) for cell in row if cell]) + " "
                        
                        table_instances = find_380_in_text(
                            table_text, page_num + 1, f"pdfplumber_table_{table_idx}"
                        )
                        instances.extend(table_instances)
        
        return {
            "method": "pdfplumber",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time
        }
        
    except Exception as e:
        return {"method": "pdfplumber", "found": False, "error": str(e)}

def search_with_camelot(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda con Camelot"""
    try:
        import camelot
        
        start_time = time.time()
        instances = []
        
        # Probar ambos flavors
        for flavor in ['stream', 'lattice']:
            try:
                tables = camelot.read_pdf(pdf_path, flavor=flavor, pages='all')
                
                for table_idx, table in enumerate(tables):
                    df = table.df
                    
                    # Buscar en cada celda
                    for row_idx, row in df.iterrows():
                        for col_idx, cell in enumerate(row):
                            cell_str = str(cell).strip()
                            
                            if contains_380_pattern(cell_str):
                                instances.append({
                                    "page": getattr(table, 'page', 'unknown'),
                                    "match": cell_str,
                                    "context": f"Tabla {table_idx}, Fila {row_idx}, Columna {col_idx}",
                                    "method": f"camelot_{flavor}",
                                    "table_index": table_idx,
                                    "cell_position": (row_idx, col_idx)
                                })
                
            except Exception as e:
                logger.warning(f"Camelot {flavor} falló: {e}")
                continue
        
        return {
            "method": "camelot",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time
        }
        
    except Exception as e:
        return {"method": "camelot", "found": False, "error": str(e)}

def search_with_aggressive_regex(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda con regex agresivo"""
    try:
        # Obtener todo el texto del PDF
        full_text = ""
        
        import fitz
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += f"\n--- PÁGINA {page_num + 1} ---\n"
            full_text += page.get_text()
        doc.close()
        
        start_time = time.time()
        instances = []
        
        # Patrones más agresivos
        aggressive_patterns = [
            # Patrones directos
            r'S/\s*380(?:[,\.]\d{2})?',
            r'380[,\.]00',
            r'380\s*soles',
            
            # Patrones con contexto de roles
            r'ministros?[^\n]*?380[^\n]*',
            r'viceministros?[^\n]*?380[^\n]*',
            r'secretarios?\s+generales?[^\n]*?380[^\n]*',
            
            # Patrones numéricos sueltos
            r'\b380\b',
            r'380(?=\s|$|[^\d])',
            
            # Patrones con separadores
            r'3\s*8\s*0',
            r'3-8-0',
            r'3\.8\.0',
            
            # Patrones en palabras
            r'trescientos\s+ochenta',
            r'TRESCIENTOS\s+OCHENTA',
            
            # Patrones en contexto de montos
            r'monto[^\n]*?380[^\n]*',
            r'diario[^\n]*?380[^\n]*',
            r'máximo[^\n]*?380[^\n]*',
            
            # Patrones con errores de OCR comunes
            r'38O',  # O en lugar de 0
            r'3B0',  # B en lugar de 8
            r'S8O',  # 5 en lugar de 3
        ]
        
        for pattern in aggressive_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Extraer contexto amplio
                start = max(0, match.start() - 150)
                end = min(len(full_text), match.end() + 150)
                context = full_text[start:end].strip()
                
                # Determinar página aproximada
                page_num = full_text[:match.start()].count("--- PÁGINA")
                
                instances.append({
                    "page": page_num,
                    "match": match.group(0),
                    "context": context,
                    "pattern": pattern,
                    "position": match.span(),
                    "method": "aggressive_regex"
                })
        
        return {
            "method": "aggressive_regex",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time,
            "patterns_tested": len(aggressive_patterns)
        }
        
    except Exception as e:
        return {"method": "aggressive_regex", "found": False, "error": str(e)}

def search_with_tesseract_ocr(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda con OCR Tesseract"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        start_time = time.time()
        instances = []
        
        # Convertir PDF a imágenes (solo primeras 10 páginas para eficiencia)
        pages = convert_from_path(pdf_path, first_page=1, last_page=10)
        
        for page_num, page_image in enumerate(pages):
            # Extraer texto con OCR
            ocr_text = pytesseract.image_to_string(page_image, lang='spa')
            
            # Buscar 380 en texto OCR
            ocr_instances = find_380_in_text(ocr_text, page_num + 1, "tesseract_ocr")
            instances.extend(ocr_instances)
        
        return {
            "method": "tesseract_ocr",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time,
            "pages_processed": len(pages)
        }
        
    except Exception as e:
        return {"method": "tesseract_ocr", "found": False, "error": str(e)}

def search_with_context_patterns(pdf_path: str) -> Dict[str, Any]:
    """Búsqueda por patrones de contexto específicos"""
    try:
        import fitz
        
        start_time = time.time()
        instances = []
        
        doc = fitz.open(pdf_path)
        
        # Patrones de contexto específicos para viáticos
        context_patterns = [
            # Buscar secciones de escalas de viáticos
            r'escala[^\n]*?viático[^\n]*?380[^\n]*',
            r'tabla[^\n]*?monto[^\n]*?380[^\n]*',
            r'anexo[^\n]*?380[^\n]*',
            
            # Buscar por roles específicos
            r'ministro[^\n]*?estado[^\n]*?380[^\n]*',
            r'viceministro[^\n]*?380[^\n]*',
            r'secretario[^\n]*?general[^\n]*?380[^\n]*',
            
            # Buscar por numerales
            r'numeral[^\n]*?380[^\n]*',
            r'\d+\.\d+[^\n]*?380[^\n]*',
            
            # Buscar por decretos y resoluciones
            r'decreto[^\n]*?380[^\n]*',
            r'resolución[^\n]*?380[^\n]*',
            r'directiva[^\n]*?380[^\n]*',
        ]
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            for pattern in context_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extraer contexto amplio
                    start = max(0, match.start() - 200)
                    end = min(len(text), match.end() + 200)
                    context = text[start:end].strip()
                    
                    instances.append({
                        "page": page_num + 1,
                        "match": match.group(0),
                        "context": context,
                        "pattern": pattern,
                        "method": "context_patterns"
                    })
        
        doc.close()
        
        return {
            "method": "context_patterns",
            "found": len(instances) > 0,
            "instances": instances,
            "extraction_time": time.time() - start_time,
            "patterns_tested": len(context_patterns)
        }
        
    except Exception as e:
        return {"method": "context_patterns", "found": False, "error": str(e)}

def find_380_in_text(text: str, page_num: int, method: str) -> List[Dict[str, Any]]:
    """Buscar 380 en texto usando múltiples patrones"""
    instances = []
    
    patterns = [
        r'S/\s*380(?:[,\.]\d{2})?',
        r'380[,\.]00',
        r'380\s*soles',
        r'\b380\b',
        r'trescientos\s+ochenta'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Extraer contexto
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].strip()
            
            instances.append({
                "page": page_num,
                "match": match.group(0),
                "context": context,
                "pattern": pattern,
                "method": method
            })
    
    return instances

def contains_380_pattern(text: str) -> bool:
    """Verificar si el texto contiene patrones de 380"""
    patterns = [
        r'S/\s*380',
        r'380[,\.]00',
        r'380\s*soles',
        r'\b380\b',
        r'trescientos\s+ochenta'
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def log_search_results(results: Dict[str, Any]):
    """Log de resultados de búsqueda"""
    
    logger.info(f"🎯 RESULTADOS DE BÚSQUEDA EXHAUSTIVA:")
    logger.info(f"   📄 PDF: {Path(results['pdf_path']).name}")
    logger.info(f"   🔍 Objetivo: {results['target_amount']}")
    logger.info(f"   ✅ Éxito: {'SÍ' if results['success'] else 'NO'}")
    logger.info(f"   📊 Instancias encontradas: {len(results['found_instances'])}")
    
    if results["best_method"]:
        logger.info(f"   🏆 Mejor método: {results['best_method']}")
    
    # Log por método
    for method, method_results in results["methods_tried"].items():
        if method_results.get("found", False):
            instances_count = len(method_results.get("instances", []))
            time_taken = method_results.get("extraction_time", 0)
            logger.info(f"   ✅ {method}: {instances_count} instancias ({time_taken:.2f}s)")
        else:
            error = method_results.get("error", "No encontrado")
            logger.info(f"   ❌ {method}: {error}")
    
    # Mostrar instancias encontradas
    if results["found_instances"]:
        logger.info(f"\n📋 INSTANCIAS ENCONTRADAS:")
        for i, instance in enumerate(results["found_instances"][:5]):  # Mostrar primeras 5
            logger.info(f"   {i+1}. Página {instance.get('page', '?')}: {instance.get('match', '?')}")
            logger.info(f"      Contexto: {instance.get('context', '')[:100]}...")
            logger.info(f"      Método: {instance.get('method', '?')}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Búsqueda exhaustiva del monto S/ 380')
    parser.add_argument('--pdf', default='data/raw/directiva_de_viaticos_011_2020_imagen.pdf', 
                       help='Ruta al PDF')
    parser.add_argument('--output', help='Archivo de salida JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = find_missing_380(args.pdf)
        
        if results.get("error"):
            logger.error(f"❌ Error: {results['error']}")
            return 1
        
        # Mostrar resumen
        print(f"\n{'='*60}")
        print("🔍 RESUMEN DE BÚSQUEDA EXHAUSTIVA")
        print(f"{'='*60}")
        print(f"📄 PDF: {Path(args.pdf).name}")
        print(f"🎯 Objetivo: {results['target_amount']}")
        print(f"✅ Encontrado: {'SÍ' if results['success'] else 'NO'}")
        print(f"📊 Total instancias: {len(results['found_instances'])}")
        
        if results["success"]:
            print(f"🏆 Mejor método: {results['best_method']}")
            
            print(f"\n💰 INSTANCIAS ENCONTRADAS:")
            for i, instance in enumerate(results["found_instances"]):
                print(f"   {i+1}. Página {instance.get('page', '?')}: '{instance.get('match', '?')}'")
                print(f"      Método: {instance.get('method', '?')}")
                print(f"      Contexto: {instance.get('context', '')[:100]}...")
                print()
        
        # Guardar resultados
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Resultados guardados en: {args.output}")
        
        return 0 if results["success"] else 1
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 
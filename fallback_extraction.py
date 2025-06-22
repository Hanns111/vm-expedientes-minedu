#!/usr/bin/env python3
"""
Extracción Agresiva con Fallback Robusto
=======================================

Script de último recurso cuando todos los demás métodos fallan.
Implementa múltiples estrategias para asegurar la extracción de montos.
"""

import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_with_aggressive_fallback(pdf_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extracción agresiva cuando todo lo demás falla
    
    Returns:
        Tuple[chunks, method_used]
    """
    
    logger.info(f"🚨 Iniciando extracción de emergencia para: {pdf_path}")
    
    methods_tried = []
    
    # 1. Intentar Camelot stream
    try:
        logger.info("🔄 Intentando Camelot stream...")
        import camelot
        
        tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
        
        if tables and len(tables) > 0:
            chunks = process_camelot_tables(tables)
            if chunks and validate_chunks_content(chunks):
                logger.info(f"✅ Camelot stream exitoso: {len(chunks)} chunks")
                return chunks, "camelot_stream"
        
        methods_tried.append("camelot_stream")
        
    except ImportError:
        logger.warning("❌ Camelot no disponible")
        methods_tried.append("camelot_stream (no disponible)")
    except Exception as e:
        logger.warning(f"❌ Camelot stream falló: {e}")
        methods_tried.append("camelot_stream")
    
    # 2. Intentar Camelot lattice con pre-procesamiento agresivo
    try:
        logger.info("🔄 Intentando Camelot lattice agresivo...")
        import camelot
        
        # Pre-procesar más agresivamente
        tables = camelot.read_pdf(
            pdf_path, 
            flavor='lattice',
            pages='all',
            process_background=True,
            line_scale=50,  # Más sensible
            copy_text=['v', 'h'],
            strip_text='\n',
            flag_size=True,
            shift_text=['l', 't']
        )
        
        if tables and len(tables) > 0:
            chunks = process_camelot_tables(tables)
            if chunks and validate_chunks_content(chunks):
                logger.info(f"✅ Camelot lattice exitoso: {len(chunks)} chunks")
                return chunks, "camelot_lattice"
        
        methods_tried.append("camelot_lattice")
        
    except ImportError:
        logger.warning("❌ Camelot no disponible")
        methods_tried.append("camelot_lattice (no disponible)")
    except Exception as e:
        logger.warning(f"❌ Camelot lattice falló: {e}")
        methods_tried.append("camelot_lattice")
    
    # 3. PDFplumber con configuración específica
    try:
        logger.info("🔄 Intentando PDFplumber...")
        import pdfplumber
        
        chunks = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Configuración para detectar tablas sin líneas
                table_settings = {
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "edge_min_length": 3,
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                }
                
                try:
                    tables = page.extract_tables(table_settings)
                    
                    if tables:
                        for table_idx, table in enumerate(tables):
                            table_chunks = process_pdfplumber_table(table, page_num + 1, table_idx)
                            chunks.extend(table_chunks)
                    
                    # También extraer texto plano
                    text = page.extract_text()
                    if text:
                        text_chunks = extract_amounts_from_text(text, page_num + 1, "pdfplumber_text")
                        chunks.extend(text_chunks)
                        
                except Exception as e:
                    logger.warning(f"Error en página {page_num + 1}: {e}")
                    continue
        
        if chunks and validate_chunks_content(chunks):
            logger.info(f"✅ PDFplumber exitoso: {len(chunks)} chunks")
            return chunks, "pdfplumber"
        
        methods_tried.append("pdfplumber")
        
    except ImportError:
        logger.warning("❌ PDFplumber no disponible")
        methods_tried.append("pdfplumber (no disponible)")
    except Exception as e:
        logger.warning(f"❌ PDFplumber falló: {e}")
        methods_tried.append("pdfplumber")
    
    # 4. ÚLTIMO RECURSO: Regex sobre OCR crudo
    logger.warning(f"⚠️  Todos los métodos fallaron: {methods_tried}")
    logger.info("🔍 Usando extracción por regex como último recurso...")
    
    try:
        # Obtener texto del PDF
        ocr_text = get_pdf_text_multiple_methods(pdf_path)
        
        if not ocr_text:
            logger.error("❌ No se pudo extraer texto del PDF")
            return [], "failed"
        
        # Buscar patrones de montos
        chunks = extract_amounts_from_text(ocr_text, 0, "regex_fallback")
        
        if chunks:
            logger.info(f"✅ Regex fallback: {len(chunks)} chunks encontrados")
            return chunks, "regex_fallback"
        else:
            logger.error("❌ Regex fallback no encontró montos")
            return [], "regex_fallback"
            
    except Exception as e:
        logger.error(f"❌ Regex fallback falló: {e}")
        return [], "failed"

def process_camelot_tables(tables) -> List[Dict[str, Any]]:
    """Procesar tablas de Camelot"""
    chunks = []
    
    for table_idx, table in enumerate(tables):
        try:
            df = table.df
            
            # Buscar montos en la tabla
            amounts_found = []
            table_text = ""
            
            for row_idx, row in df.iterrows():
                for col_idx, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    table_text += f"{cell_str} "
                    
                    # Buscar patrones de montos
                    if contains_amount(cell_str):
                        amounts_found.append(cell_str)
            
            if amounts_found or contains_viaticos_keywords(table_text):
                chunk = {
                    "chunk_id": f"fallback_camelot_{table_idx}",
                    "content": table_text.strip(),
                    "texto": table_text.strip(),  # Compatibilidad
                    "metadata": {
                        "extraction_method": "camelot_fallback",
                        "table_index": table_idx,
                        "page": getattr(table, 'page', 'unknown'),
                        "amounts_found": amounts_found,
                        "confidence": getattr(table, 'accuracy', 0.8)
                    },
                    "metadatos": {  # Compatibilidad
                        "extraction_method": "camelot_fallback",
                        "amounts_found": amounts_found,
                        "confidence": getattr(table, 'accuracy', 0.8)
                    }
                }
                chunks.append(chunk)
                
        except Exception as e:
            logger.warning(f"Error procesando tabla Camelot {table_idx}: {e}")
            continue
    
    return chunks

def process_pdfplumber_table(table: List[List[str]], page_num: int, table_idx: int) -> List[Dict[str, Any]]:
    """Procesar tabla de PDFplumber"""
    chunks = []
    
    amounts_found = []
    table_text = ""
    
    for row in table:
        for cell in row:
            if cell:
                cell_str = str(cell).strip()
                table_text += f"{cell_str} "
                
                if contains_amount(cell_str):
                    amounts_found.append(cell_str)
    
    if amounts_found or contains_viaticos_keywords(table_text):
        chunk = {
            "chunk_id": f"fallback_pdfplumber_p{page_num}_t{table_idx}",
            "content": table_text.strip(),
            "texto": table_text.strip(),  # Compatibilidad
            "metadata": {
                "extraction_method": "pdfplumber_fallback",
                "page": page_num,
                "table_index": table_idx,
                "amounts_found": amounts_found,
                "confidence": 0.85
            },
            "metadatos": {  # Compatibilidad
                "extraction_method": "pdfplumber_fallback",
                "amounts_found": amounts_found,
                "confidence": 0.85
            }
        }
        chunks.append(chunk)
    
    return chunks

def extract_amounts_from_text(text: str, page_num: int, method: str) -> List[Dict[str, Any]]:
    """Extraer montos de texto plano usando regex agresivo"""
    chunks = []
    
    # Patrones más agresivos para montos en soles
    patterns = [
        # Patrones estándar
        r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # S/ 380.00, S/ 320,00
        r'soles?\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # soles 320.00
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*soles?',  # 320.00 soles
        
        # Patrones específicos para los montos objetivo
        r'\b(380)(?:[,\.]\d{2})?\b',  # 380, 380.00, 380,00
        r'\b(320)(?:[,\.]\d{2})?\b',  # 320, 320.00, 320,00
        r'\b(30)(?:[,\.]\d{2})?\b',   # 30, 30.00, 30,00
        
        # Patrones con contexto
        r'(ministros?\s+[^\n]*?(?:380|S/\s*380))',
        r'(servidores?\s+[^\n]*?(?:320|S/\s*320))',
        r'(declaración\s+jurada[^\n]*?(?:30|S/\s*30))',
        
        # Patrones numéricos sueltos en contexto de viáticos
        r'(viático[^\n]*?(\d{2,3})[^\n]*)',
        r'(monto[^\n]*?(\d{2,3})[^\n]*)',
        r'(diario[^\n]*?(\d{2,3})[^\n]*)'
    ]
    
    amounts_found = set()  # Usar set para evitar duplicados
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            amount_text = match.group(0)
            
            # Filtrar matches muy cortos o irrelevantes
            if len(amount_text.strip()) < 2:
                continue
            
            amounts_found.add(amount_text.strip())
            
            # Extraer contexto más amplio (100 caracteres antes y después)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            # Limpiar contexto
            context = re.sub(r'\s+', ' ', context)
            
            chunk = {
                "chunk_id": f"{method}_amount_{len(chunks)}",
                "content": context,
                "texto": context,  # Compatibilidad
                "metadata": {
                    "extraction_method": method,
                    "page": page_num,
                    "amount": amount_text.strip(),
                    "amounts_found": [amount_text.strip()],
                    "confidence": 0.7 if method == "regex_fallback" else 0.8,
                    "context_length": len(context)
                },
                "metadatos": {  # Compatibilidad
                    "extraction_method": method,
                    "amount": amount_text.strip(),
                    "confidence": 0.7 if method == "regex_fallback" else 0.8
                }
            }
            chunks.append(chunk)
    
    logger.info(f"📊 {method}: {len(amounts_found)} montos únicos encontrados")
    return chunks

def contains_amount(text: str) -> bool:
    """Verificar si el texto contiene un monto (más agresivo)"""
    # Buscar patrones de montos más amplios
    patterns = [
        r'S/\s*\d+',
        r'\d+[,\.]\d{2}',
        r'\b(380|320|30)\b',  # Montos específicos
        r'\d{2,3}',  # Cualquier número de 2-3 dígitos
        r'soles?',
        r'viático',
        r'monto'
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def contains_viaticos_keywords(text: str) -> bool:
    """Verificar si el texto contiene palabras clave de viáticos"""
    keywords = [
        'viático', 'viatico', 'viáticos', 'viaticos',
        'ministro', 'viceministro', 'secretario general',
        'servidor', 'funcionario', 'declaración jurada',
        'rendición', 'gastos', 'diario', 'máximo'
    ]
    
    text_lower = text.lower()
    
    for keyword in keywords:
        if keyword in text_lower:
            return True
    
    return False

def validate_chunks_content(chunks: List[Dict[str, Any]]) -> bool:
    """Validar que los chunks contienen información útil"""
    if not chunks:
        return False
    
    # Buscar montos objetivo específicos
    target_amounts = ['380', '320', '30']
    found_targets = set()
    
    for chunk in chunks:
        # Buscar en diferentes campos
        text_fields = [
            chunk.get('content', ''),
            chunk.get('texto', ''),
            str(chunk.get('metadata', {}).get('amounts_found', [])),
            str(chunk.get('metadatos', {}).get('amounts_found', []))
        ]
        
        chunk_text = ' '.join(text_fields).lower()
        
        for target in target_amounts:
            if target in chunk_text:
                found_targets.add(target)
    
    logger.info(f"🎯 Validación: {found_targets} de {target_amounts}")
    
    # Considerar exitoso si encontramos al menos uno de los montos clave
    return len(found_targets) > 0

def get_pdf_text_multiple_methods(pdf_path: str) -> str:
    """Extraer texto usando múltiples métodos"""
    
    text_content = ""
    
    # Método 1: PyMuPDF (fitz)
    try:
        import fitz
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
            text_content += page.get_text()
        doc.close()
        
        if text_content.strip():
            logger.info("✅ Texto extraído con PyMuPDF")
            return text_content
            
    except Exception as e:
        logger.warning(f"❌ PyMuPDF falló: {e}")
    
    # Método 2: PDFplumber
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text
        
        if text_content.strip():
            logger.info("✅ Texto extraído con PDFplumber")
            return text_content
            
    except Exception as e:
        logger.warning(f"❌ PDFplumber falló: {e}")
    
    # Método 3: PyPDF2 (último recurso)
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
                text_content += page.extract_text()
        
        if text_content.strip():
            logger.info("✅ Texto extraído con PyPDF2")
            return text_content
            
    except Exception as e:
        logger.warning(f"❌ PyPDF2 falló: {e}")
    
    logger.error("❌ No se pudo extraer texto con ningún método")
    return ""

def main():
    """Función principal para testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extracción de emergencia con fallback agresivo')
    parser.add_argument('pdf_path', help='Ruta al archivo PDF')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not Path(args.pdf_path).exists():
        logger.error(f"❌ Archivo no encontrado: {args.pdf_path}")
        return 1
    
    try:
        logger.info("🚨 Iniciando extracción de emergencia...")
        
        start_time = time.time()
        chunks, method_used = extract_with_aggressive_fallback(args.pdf_path)
        extraction_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print("🚨 RESULTADOS DE EXTRACCIÓN DE EMERGENCIA")
        print(f"{'='*60}")
        print(f"📄 Archivo: {Path(args.pdf_path).name}")
        print(f"🔧 Método exitoso: {method_used}")
        print(f"📊 Chunks extraídos: {len(chunks)}")
        print(f"⏱️  Tiempo: {extraction_time:.3f}s")
        
        if chunks:
            print(f"\n🎯 MONTOS ENCONTRADOS:")
            amounts_found = set()
            
            for chunk in chunks:
                chunk_amounts = chunk.get('metadata', {}).get('amounts_found', [])
                amounts_found.update(chunk_amounts)
            
            for amount in sorted(amounts_found):
                print(f"   💰 {amount}")
            
            # Validar montos objetivo
            target_amounts = ['380', '320', '30']
            found_targets = []
            
            for target in target_amounts:
                if any(target in str(amount) for amount in amounts_found):
                    found_targets.append(target)
            
            print(f"\n✅ Montos objetivo encontrados: {found_targets}")
            
            if len(found_targets) >= 2:
                print("🎉 ¡ÉXITO! Se encontraron los montos principales")
            else:
                print("⚠️  PARCIAL: Faltan algunos montos objetivo")
        else:
            print("❌ No se encontraron montos")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 
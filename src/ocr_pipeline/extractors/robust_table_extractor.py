#!/usr/bin/env python3
"""
Extractor robusto de tablas con múltiples fallbacks
==================================================

Extractor que intenta múltiples métodos para asegurar la captura de tablas
con montos específicos de viáticos.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
import fitz  # PyMuPDF

# Configurar logging
logger = logging.getLogger(__name__)

class RobustTableExtractor:
    """Extractor robusto de tablas con múltiples estrategias de fallback"""
    
    def __init__(self, use_opencv_preprocessing: bool = True, preprocessing_params: Dict = None):
        self.use_opencv_preprocessing = use_opencv_preprocessing
        self.preprocessing_params = preprocessing_params or {
            'threshold_type': 'adaptive',
            'blur_kernel': (5, 5),
            'dilate_iterations': 2
        }
        
        # Verificar disponibilidad de librerías
        self.camelot_available = self._check_camelot()
        self.pdfplumber_available = self._check_pdfplumber()
        self.opencv_available = self._check_opencv()
        
        logger.info(f"RobustTableExtractor initialized:")
        logger.info(f"  - Camelot: {'✅' if self.camelot_available else '❌'}")
        logger.info(f"  - PDFplumber: {'✅' if self.pdfplumber_available else '❌'}")
        logger.info(f"  - OpenCV: {'✅' if self.opencv_available else '❌'}")
    
    def _check_camelot(self) -> bool:
        """Verificar disponibilidad de Camelot"""
        try:
            import camelot
            return True
        except ImportError:
            logger.warning("Camelot no disponible - instalar con: pip install camelot-py[cv]")
            return False
    
    def _check_pdfplumber(self) -> bool:
        """Verificar disponibilidad de PDFplumber"""
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.warning("PDFplumber no disponible - instalar con: pip install pdfplumber")
            return False
    
    def _check_opencv(self) -> bool:
        """Verificar disponibilidad de OpenCV"""
        try:
            import cv2
            return True
        except ImportError:
            logger.warning("OpenCV no disponible - instalar con: pip install opencv-python")
            return False
    
    def extract_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extracción principal con múltiples fallbacks"""
        
        logger.info(f"🔍 Iniciando extracción robusta de: {pdf_path}")
        
        # Verificar que el archivo existe
        if not Path(pdf_path).exists():
            logger.error(f"❌ Archivo no encontrado: {pdf_path}")
            return []
        
        # Obtener información del PDF
        pdf_info = self._get_pdf_info(pdf_path)
        logger.info(f"📄 PDF: {pdf_info['pages']} páginas, {pdf_info['size_mb']:.1f} MB")
        
        # Intentar métodos en orden de preferencia
        methods = [
            ("camelot_stream", self._extract_camelot_stream),
            ("camelot_lattice", self._extract_camelot_lattice),
            ("pdfplumber", self._extract_pdfplumber),
            ("regex_fallback", self._extract_regex_fallback)
        ]
        
        for method_name, method_func in methods:
            if not self._method_available(method_name):
                logger.info(f"⏭️  Saltando {method_name} - no disponible")
                continue
            
            try:
                logger.info(f"🔄 Intentando {method_name}...")
                start_time = time.time()
                
                chunks = method_func(pdf_path)
                
                extraction_time = time.time() - start_time
                logger.info(f"⏱️  {method_name}: {extraction_time:.3f}s")
                
                if chunks and self._validate_chunks(chunks):
                    logger.info(f"✅ {method_name} exitoso: {len(chunks)} chunks")
                    return self._enrich_chunks(chunks, method_name, extraction_time, pdf_info)
                else:
                    logger.warning(f"❌ {method_name}: No se encontraron montos válidos")
                    
            except Exception as e:
                logger.error(f"❌ {method_name} falló: {str(e)}")
                continue
        
        logger.error("🚨 Todos los métodos de extracción fallaron")
        return []
    
    def _method_available(self, method_name: str) -> bool:
        """Verificar si un método está disponible"""
        if method_name.startswith("camelot"):
            return self.camelot_available
        elif method_name == "pdfplumber":
            return self.pdfplumber_available
        else:
            return True  # regex_fallback siempre disponible
    
    def _extract_camelot_stream(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extracción con Camelot flavor='stream' (PDFs digitales)"""
        import camelot
        
        tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
        return self._process_camelot_tables(tables, "stream")
    
    def _extract_camelot_lattice(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extracción con Camelot flavor='lattice' (PDFs escaneados)"""
        import camelot
        
        # Configuración agresiva para PDFs escaneados
        tables = camelot.read_pdf(
            pdf_path, 
            flavor='lattice',
            pages='all',
            process_background=True,
            line_scale=50,  # Más sensible a líneas
            copy_text=['v', 'h']  # Copiar texto vertical y horizontal
        )
        return self._process_camelot_tables(tables, "lattice")
    
    def _extract_pdfplumber(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extracción con PDFplumber"""
        import pdfplumber
        
        chunks = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Configuración para detectar tablas sin líneas visibles
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
                        logger.info(f"📊 Página {page_num + 1}: {len(tables)} tablas encontradas")
                        
                        for table_idx, table in enumerate(tables):
                            table_chunks = self._process_pdfplumber_table(
                                table, page_num + 1, table_idx
                            )
                            chunks.extend(table_chunks)
                    
                    # También extraer texto plano para buscar montos sueltos
                    text = page.extract_text()
                    if text:
                        text_chunks = self._extract_amounts_from_text(
                            text, page_num + 1, "pdfplumber_text"
                        )
                        chunks.extend(text_chunks)
                        
                except Exception as e:
                    logger.warning(f"Error en página {page_num + 1}: {e}")
                    continue
        
        return chunks
    
    def _extract_regex_fallback(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Último recurso: extracción por regex sobre texto OCR"""
        
        logger.info("🔍 Usando extracción regex como último recurso...")
        
        # Extraer texto con PyMuPDF
        text_content = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
                text_content += page.get_text()
            doc.close()
        except Exception as e:
            logger.error(f"Error extrayendo texto: {e}")
            return []
        
        return self._extract_amounts_from_text(text_content, 0, "regex_fallback")
    
    def _process_camelot_tables(self, tables, flavor: str) -> List[Dict[str, Any]]:
        """Procesar tablas de Camelot"""
        chunks = []
        
        logger.info(f"📊 Camelot {flavor}: {len(tables)} tablas encontradas")
        
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
                        if self._contains_amount(cell_str):
                            amounts_found.append(cell_str)
                
                if amounts_found:
                    chunk = {
                        "chunk_id": f"camelot_{flavor}_{table_idx}",
                        "content": table_text.strip(),
                        "metadata": {
                            "extraction_method": f"camelot_{flavor}",
                            "table_index": table_idx,
                            "page": getattr(table, 'page', 'unknown'),
                            "amounts_found": amounts_found,
                            "confidence": table.accuracy if hasattr(table, 'accuracy') else 0.8
                        }
                    }
                    chunks.append(chunk)
                    logger.info(f"✅ Tabla {table_idx}: {len(amounts_found)} montos encontrados")
                
            except Exception as e:
                logger.warning(f"Error procesando tabla {table_idx}: {e}")
                continue
        
        return chunks
    
    def _process_pdfplumber_table(self, table: List[List[str]], page_num: int, table_idx: int) -> List[Dict[str, Any]]:
        """Procesar tabla de PDFplumber"""
        chunks = []
        
        amounts_found = []
        table_text = ""
        
        for row in table:
            for cell in row:
                if cell:
                    cell_str = str(cell).strip()
                    table_text += f"{cell_str} "
                    
                    if self._contains_amount(cell_str):
                        amounts_found.append(cell_str)
        
        if amounts_found:
            chunk = {
                "chunk_id": f"pdfplumber_p{page_num}_t{table_idx}",
                "content": table_text.strip(),
                "metadata": {
                    "extraction_method": "pdfplumber",
                    "page": page_num,
                    "table_index": table_idx,
                    "amounts_found": amounts_found,
                    "confidence": 0.85
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _extract_amounts_from_text(self, text: str, page_num: int, method: str) -> List[Dict[str, Any]]:
        """Extraer montos de texto plano usando regex"""
        chunks = []
        
        # Patrones para montos en soles
        patterns = [
            r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # S/ 380.00, S/ 320,00
            r'soles?\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # soles 320.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*soles?',  # 320.00 soles
            r'(\d{3}),(\d{2})',  # 320,00 (formato peruano)
        ]
        
        amounts_found = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_text = match.group(0)
                amounts_found.append(amount_text)
                
                # Extraer contexto (50 caracteres antes y después)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                chunk = {
                    "chunk_id": f"{method}_amount_{len(chunks)}",
                    "content": context,
                    "metadata": {
                        "extraction_method": method,
                        "page": page_num,
                        "amount": amount_text,
                        "amounts_found": [amount_text],
                        "confidence": 0.7 if method == "regex_fallback" else 0.8
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def _contains_amount(self, text: str) -> bool:
        """Verificar si el texto contiene un monto"""
        # Buscar patrones de montos
        patterns = [
            r'S/\s*\d+',
            r'\d+[,\.]\d{2}',
            r'(380|320|30)(?:[,\.]\d{2})?'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Validar que los chunks contienen información útil"""
        if not chunks:
            return False
        
        # Buscar montos objetivo específicos
        target_amounts = ['380', '320', '30']
        found_targets = set()
        
        for chunk in chunks:
            amounts = chunk.get('metadata', {}).get('amounts_found', [])
            for amount in amounts:
                for target in target_amounts:
                    if target in amount:
                        found_targets.add(target)
        
        logger.info(f"🎯 Montos objetivo encontrados: {found_targets}")
        
        # Considerar exitoso si encontramos al menos uno de los montos clave
        return len(found_targets) > 0
    
    def _enrich_chunks(self, chunks: List[Dict[str, Any]], method: str, 
                      extraction_time: float, pdf_info: Dict) -> List[Dict[str, Any]]:
        """Enriquecer chunks con metadatos adicionales"""
        
        for chunk in chunks:
            chunk['metadata'].update({
                'extraction_time': extraction_time,
                'pdf_pages': pdf_info['pages'],
                'pdf_size_mb': pdf_info['size_mb'],
                'extractor_version': '1.0.0',
                'target_amounts_validated': True
            })
        
        return chunks
    
    def _get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Obtener información básica del PDF"""
        try:
            doc = fitz.open(pdf_path)
            pages = len(doc)
            doc.close()
            
            file_size = Path(pdf_path).stat().st_size / (1024 * 1024)  # MB
            
            return {
                'pages': pages,
                'size_mb': file_size
            }
        except Exception:
            return {'pages': 0, 'size_mb': 0}
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del extractor"""
        return {
            'camelot_available': self.camelot_available,
            'pdfplumber_available': self.pdfplumber_available,
            'opencv_available': self.opencv_available,
            'preprocessing_enabled': self.use_opencv_preprocessing,
            'fallback_methods': 4
        }
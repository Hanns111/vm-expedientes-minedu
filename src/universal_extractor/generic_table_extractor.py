#!/usr/bin/env python3
"""
Generic Table Extractor - Detección Auto-ajustable Universal
===========================================================

Extractor universal que se auto-configura para cualquier tipo de norma legal.
Combina OpenCV, Camelot y algoritmos adaptativos para máxima cobertura.
"""

import cv2
import numpy as np
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF
from dataclasses import dataclass

# Imports con fallbacks
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TableExtractionConfig:
    """Configuración adaptativa para extracción de tablas"""
    flavor: str = "lattice"
    line_scale: int = 40
    process_background: bool = True
    confidence_threshold: float = 0.7
    opencv_kernel_size: Tuple[int, int] = (3, 3)
    adaptive_threshold: bool = True
    edge_enhancement: bool = True
    fallback_methods: List[str] = None
    
    def __post_init__(self):
        if self.fallback_methods is None:
            self.fallback_methods = ["camelot_lattice", "camelot_stream", "pdfplumber", "opencv_lines"]

@dataclass 
class DocumentCharacteristics:
    """Características detectadas del documento"""
    has_visible_lines: bool = False
    table_density: float = 0.0
    text_quality: float = 0.0
    scan_quality: float = 0.0
    document_type: str = "unknown"
    page_count: int = 0
    complexity_score: float = 0.0

class GenericTableExtractor:
    """
    Extractor universal de tablas con auto-configuración para cualquier norma legal.
    
    Características:
    - Auto-detección de características del documento
    - Configuración adaptativa de parámetros
    - Múltiples métodos de fallback
    - Optimización OpenCV automática
    - Medición de confianza en tiempo real
    """
    
    def __init__(self, base_config: Optional[TableExtractionConfig] = None):
        self.base_config = base_config or TableExtractionConfig()
        self.extraction_history = []
        self.learned_optimizations = {}
        
        # Métricas de rendimiento
        self.performance_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'average_confidence': 0.0,
            'method_performance': {}
        }
        
        logger.info(f"GenericTableExtractor initialized - Camelot: {CAMELOT_AVAILABLE}, PDFPlumber: {PDFPLUMBER_AVAILABLE}")
    
    def extract_tables_universal(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extracción universal de tablas con auto-configuración.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con tablas extraídas y metadatos
        """
        start_time = time.time()
        
        # 1. Analizar características del documento
        doc_characteristics = self._analyze_document_characteristics(pdf_path)
        logger.info(f"Document analysis: {doc_characteristics.document_type}, complexity: {doc_characteristics.complexity_score:.2f}")
        
        # 2. Optimizar configuración basada en características
        optimized_config = self._optimize_config_for_document(doc_characteristics)
        logger.info(f"Optimized config: {optimized_config.flavor}, line_scale: {optimized_config.line_scale}")
        
        # 3. Preprocesar con OpenCV si es necesario
        preprocessed_pdf = None
        if doc_characteristics.scan_quality < 0.7 and optimized_config.edge_enhancement:
            preprocessed_pdf = self._preprocess_with_opencv(pdf_path, optimized_config)
        
        # 4. Extraer tablas con método óptimo
        extraction_results = self._extract_with_adaptive_methods(
            preprocessed_pdf or pdf_path, 
            optimized_config,
            doc_characteristics
        )
        
        # 5. Validar y enriquecer resultados
        validated_results = self._validate_and_enrich_results(extraction_results, doc_characteristics)
        
        # 6. Actualizar estadísticas de aprendizaje
        self._update_learning_stats(pdf_path, doc_characteristics, validated_results)
        
        total_time = time.time() - start_time
        
        return {
            'tables': validated_results['tables'],
            'metadata': {
                'extraction_time': total_time,
                'document_characteristics': doc_characteristics,
                'config_used': optimized_config,
                'confidence_score': validated_results['overall_confidence'],
                'extraction_method': validated_results['primary_method'],
                'fallbacks_used': validated_results['fallbacks_used'],
                'total_tables_found': len(validated_results['tables'])
            }
        }
    
    def _analyze_document_characteristics(self, pdf_path: str) -> DocumentCharacteristics:
        """Analizar características del documento para optimización."""
        
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            # Analizar primera página como muestra
            page = doc.load_page(0)
            
            # 1. Detectar líneas visibles (indica tablas con bordes)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.pil_tobytes(format="PNG")
            
            # Convertir a OpenCV
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detectar líneas horizontales y verticales
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            line_density = (np.sum(horizontal_lines > 0) + np.sum(vertical_lines > 0)) / (img.shape[0] * img.shape[1])
            has_visible_lines = line_density > 0.001
            
            # 2. Calcular calidad del escaneo
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            scan_quality = min(laplacian_var / 1000, 1.0)  # Normalizar
            
            # 3. Analizar densidad de tablas aproximada
            text_content = page.get_text()
            
            # Contar patrones tabulares en texto
            tabular_indicators = [
                len([line for line in text_content.split('\n') if '\t' in line or '  ' in line]),
                text_content.count('|'),
                len([line for line in text_content.split('\n') if len(line.split()) > 3])
            ]
            table_density = sum(tabular_indicators) / len(text_content.split('\n')) if text_content else 0
            
            # 4. Detectar tipo de documento
            text_lower = text_content.lower()
            document_type = "legal_norm"
            if "directiva" in text_lower:
                document_type = "directiva"
            elif "resolución" in text_lower:
                document_type = "resolucion"
            elif "decreto" in text_lower:
                document_type = "decreto"
            elif "reglamento" in text_lower:
                document_type = "reglamento"
            
            # 5. Calcular calidad del texto
            text_quality = len(text_content) / max(1, img.shape[0] * img.shape[1] / 10000)
            text_quality = min(text_quality, 1.0)
            
            # 6. Calcular puntuación de complejidad
            complexity_score = (
                (1 - scan_quality) * 0.3 +  # Peor calidad = más complejo
                table_density * 0.4 +       # Más tablas = más complejo  
                (page_count / 100) * 0.2 +  # Más páginas = más complejo
                (1 - text_quality) * 0.1    # Peor texto = más complejo
            )
            
            doc.close()
            
            return DocumentCharacteristics(
                has_visible_lines=has_visible_lines,
                table_density=table_density,
                text_quality=text_quality,
                scan_quality=scan_quality,
                document_type=document_type,
                page_count=page_count,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document characteristics: {e}")
            return DocumentCharacteristics()
    
    def _optimize_config_for_document(self, characteristics: DocumentCharacteristics) -> TableExtractionConfig:
        """Optimizar configuración basada en características del documento."""
        
        config = TableExtractionConfig()
        
        # Seleccionar flavor óptimo
        if characteristics.has_visible_lines:
            config.flavor = "lattice"
            config.line_scale = 40
        else:
            config.flavor = "stream"
            config.line_scale = 15
        
        # Ajustar line_scale basado en complejidad
        if characteristics.complexity_score > 0.7:
            config.line_scale = int(config.line_scale * 1.5)
        elif characteristics.complexity_score < 0.3:
            config.line_scale = int(config.line_scale * 0.7)
        
        # Configurar preprocesamiento
        config.process_background = characteristics.scan_quality < 0.5
        config.edge_enhancement = characteristics.scan_quality < 0.7
        
        # Ajustar umbral de confianza
        if characteristics.document_type in ["directiva", "decreto"]:
            config.confidence_threshold = 0.6  # Más permisivo para docs oficiales
        else:
            config.confidence_threshold = 0.7
        
        # Optimizar kernel OpenCV
        if characteristics.complexity_score > 0.8:
            config.opencv_kernel_size = (5, 5)  # Kernel más grande para docs complejos
        else:
            config.opencv_kernel_size = (3, 3)
        
        return config
    
    def _preprocess_with_opencv(self, pdf_path: str, config: TableExtractionConfig) -> str:
        """Preprocesar PDF con OpenCV para mejorar detección de tablas."""
        
        try:
            import tempfile
            from pdf2image import convert_from_path
            
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path, dpi=300)
            
            processed_images = []
            for img in images:
                # Convertir PIL a OpenCV
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Aplicar preprocesamiento adaptativo
                processed_img = self._apply_opencv_enhancements(img_cv, config)
                processed_images.append(processed_img)
            
            # Guardar PDF procesado (simplificado - en producción usar img2pdf)
            output_path = str(Path(pdf_path).with_suffix('.processed.pdf'))
            
            # Por ahora retornar el path original
            # En implementación completa: convertir imágenes procesadas de vuelta a PDF
            return pdf_path
            
        except ImportError:
            logger.warning("pdf2image not available - skipping OpenCV preprocessing")
            return pdf_path
        except Exception as e:
            logger.error(f"OpenCV preprocessing failed: {e}")
            return pdf_path
    
    def _apply_opencv_enhancements(self, img: np.ndarray, config: TableExtractionConfig) -> np.ndarray:
        """Aplicar mejoras OpenCV específicas para detección de tablas."""
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Mejora de contraste adaptativo
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 2. Reducción de ruido
        denoised = cv2.medianBlur(enhanced, 3)
        
        # 3. Threshold adaptativo
        if config.adaptive_threshold:
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
        else:
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. Mejora de líneas de tabla
        if config.edge_enhancement:
            # Detectar y reforzar líneas horizontales
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detectar y reforzar líneas verticales  
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combinar líneas con imagen original
            lines_combined = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            enhanced_table = cv2.addWeighted(binary, 0.8, lines_combined, 0.2, 0.0)
            
            return enhanced_table
        
        return binary
    
    def _extract_with_adaptive_methods(self, pdf_path: str, config: TableExtractionConfig, 
                                     characteristics: DocumentCharacteristics) -> Dict[str, Any]:
        """Extraer tablas usando métodos adaptativos con fallbacks inteligentes."""
        
        extraction_results = {
            'tables': [],
            'methods_tried': [],
            'method_results': {},
            'primary_method': None,
            'fallbacks_used': []
        }
        
        # Orden de métodos basado en características del documento
        methods = self._get_optimal_method_order(characteristics, config)
        
        for method_name in methods:
            try:
                logger.info(f"Trying extraction method: {method_name}")
                method_results = self._extract_with_method(pdf_path, method_name, config)
                
                extraction_results['methods_tried'].append(method_name)
                extraction_results['method_results'][method_name] = method_results
                
                # Evaluar confianza del método
                confidence = self._evaluate_method_confidence(method_results, characteristics)
                
                if confidence >= config.confidence_threshold:
                    extraction_results['tables'] = method_results['tables']
                    extraction_results['primary_method'] = method_name
                    logger.info(f"Method {method_name} succeeded with confidence {confidence:.3f}")
                    break
                else:
                    extraction_results['fallbacks_used'].append(method_name)
                    logger.info(f"Method {method_name} below threshold: {confidence:.3f}")
                    
            except Exception as e:
                logger.error(f"Method {method_name} failed: {e}")
                extraction_results['fallbacks_used'].append(method_name)
                continue
        
        # Si ningún método alcanza el umbral, usar el mejor disponible
        if not extraction_results['tables'] and extraction_results['method_results']:
            best_method = max(
                extraction_results['method_results'].keys(),
                key=lambda m: self._evaluate_method_confidence(
                    extraction_results['method_results'][m], characteristics
                )
            )
            extraction_results['tables'] = extraction_results['method_results'][best_method]['tables']
            extraction_results['primary_method'] = best_method
            logger.info(f"Using best available method: {best_method}")
        
        return extraction_results
    
    def _get_optimal_method_order(self, characteristics: DocumentCharacteristics, 
                                config: TableExtractionConfig) -> List[str]:
        """Determinar orden óptimo de métodos basado en características."""
        
        methods = []
        
        # Priorizar según características del documento
        if characteristics.has_visible_lines and CAMELOT_AVAILABLE:
            methods.append("camelot_lattice")
            methods.append("camelot_stream")
        elif CAMELOT_AVAILABLE:
            methods.append("camelot_stream") 
            methods.append("camelot_lattice")
        
        if PDFPLUMBER_AVAILABLE:
            methods.append("pdfplumber")
        
        # Métodos de respaldo
        methods.extend(["opencv_contours", "regex_patterns"])
        
        return methods
    
    def _extract_with_method(self, pdf_path: str, method: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer tablas usando un método específico."""
        
        if method == "camelot_lattice" and CAMELOT_AVAILABLE:
            return self._extract_camelot_lattice(pdf_path, config)
        elif method == "camelot_stream" and CAMELOT_AVAILABLE:
            return self._extract_camelot_stream(pdf_path, config)
        elif method == "pdfplumber" and PDFPLUMBER_AVAILABLE:
            return self._extract_pdfplumber(pdf_path, config)
        elif method == "opencv_contours":
            return self._extract_opencv_contours(pdf_path, config)
        elif method == "regex_patterns":
            return self._extract_regex_patterns(pdf_path, config)
        else:
            raise ValueError(f"Method {method} not available or not implemented")
    
    def _extract_camelot_lattice(self, pdf_path: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer tablas usando Camelot lattice."""
        
        tables = camelot.read_pdf(
            pdf_path,
            pages='all',
            flavor='lattice',
            line_scale=config.line_scale,
            process_background=config.process_background
        )
        
        extracted_tables = []
        for i, table in enumerate(tables):
            if table.accuracy > 0.5:  # Umbral mínimo
                extracted_tables.append({
                    'id': f'camelot_lattice_{i}',
                    'data': table.df.values.tolist(),
                    'headers': table.df.columns.tolist(),
                    'confidence': table.accuracy,
                    'page': getattr(table, 'page', 'unknown'),
                    'method': 'camelot_lattice'
                })
        
        return {'tables': extracted_tables, 'total_found': len(tables)}
    
    def _extract_camelot_stream(self, pdf_path: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer tablas usando Camelot stream."""
        
        tables = camelot.read_pdf(
            pdf_path,
            pages='all', 
            flavor='stream',
            row_tol=10
        )
        
        extracted_tables = []
        for i, table in enumerate(tables):
            if table.accuracy > 0.5:
                extracted_tables.append({
                    'id': f'camelot_stream_{i}',
                    'data': table.df.values.tolist(),
                    'headers': table.df.columns.tolist(),
                    'confidence': table.accuracy,
                    'page': getattr(table, 'page', 'unknown'),
                    'method': 'camelot_stream'
                })
        
        return {'tables': extracted_tables, 'total_found': len(tables)}
    
    def _extract_pdfplumber(self, pdf_path: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer tablas usando PDFPlumber."""
        
        extracted_tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                for i, table in enumerate(tables):
                    if table and len(table) > 1:  # Al menos header + 1 fila
                        extracted_tables.append({
                            'id': f'pdfplumber_{page_num}_{i}',
                            'data': table[1:],  # Datos sin header
                            'headers': table[0],  # Primera fila como header
                            'confidence': 0.8,  # Confianza fija para PDFPlumber
                            'page': page_num + 1,
                            'method': 'pdfplumber'
                        })
        
        return {'tables': extracted_tables, 'total_found': len(extracted_tables)}
    
    def _extract_opencv_contours(self, pdf_path: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer tablas usando detección de contornos OpenCV."""
        
        # Implementación simplificada - en producción sería más compleja
        extracted_tables = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                img_data = pix.pil_tobytes(format="PNG")
                
                # Convertir a OpenCV
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Detectar contornos de tablas
                edges = cv2.Canny(gray, 50, 150, apertureSize=3)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filtrar contornos que parecen tablas
                table_contours = [c for c in contours if cv2.contourArea(c) > 1000]
                
                if table_contours:
                    extracted_tables.append({
                        'id': f'opencv_contours_{page_num}',
                        'data': [['Table detected via OpenCV contours']],
                        'headers': ['Content'],
                        'confidence': 0.6,
                        'page': page_num + 1,
                        'method': 'opencv_contours',
                        'contour_count': len(table_contours)
                    })
            
            doc.close()
            
        except Exception as e:
            logger.error(f"OpenCV contours extraction failed: {e}")
        
        return {'tables': extracted_tables, 'total_found': len(extracted_tables)}
    
    def _extract_regex_patterns(self, pdf_path: str, config: TableExtractionConfig) -> Dict[str, Any]:
        """Extraer estructuras tabulares usando patrones regex."""
        
        extracted_tables = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # Patrones para estructuras tabulares
            table_patterns = [
                r'(\d+(?:\.\d+)*)\s+([^\n]+?)\s+(S/\s*\d+(?:,\d{3})*(?:\.\d{2})?)',  # Numeral + descripción + monto
                r'([A-Z][^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|\s*(S/\s*\d+(?:,\d{3})*(?:\.\d{2})?)',  # Formato con pipes
            ]
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                for pattern_idx, pattern in enumerate(table_patterns):
                    import re
                    matches = re.findall(pattern, text, re.MULTILINE)
                    
                    if matches:
                        table_data = []
                        for match in matches:
                            table_data.append(list(match))
                        
                        extracted_tables.append({
                            'id': f'regex_pattern_{page_num}_{pattern_idx}',
                            'data': table_data,
                            'headers': ['Numeral', 'Descripción', 'Monto'],
                            'confidence': 0.7,
                            'page': page_num + 1,
                            'method': 'regex_patterns',
                            'pattern_used': pattern_idx
                        })
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Regex patterns extraction failed: {e}")
        
        return {'tables': extracted_tables, 'total_found': len(extracted_tables)}
    
    def _evaluate_method_confidence(self, method_results: Dict[str, Any], 
                                  characteristics: DocumentCharacteristics) -> float:
        """Evaluar confianza de un método de extracción."""
        
        if not method_results['tables']:
            return 0.0
        
        # Factores de confianza
        table_count = len(method_results['tables'])
        avg_confidence = sum(t.get('confidence', 0) for t in method_results['tables']) / table_count
        
        # Bonus por tipo de documento
        document_bonus = 0.1 if characteristics.document_type in ["directiva", "decreto"] else 0.0
        
        # Penalty por baja calidad de escaneo
        scan_penalty = (1 - characteristics.scan_quality) * 0.2
        
        final_confidence = avg_confidence + document_bonus - scan_penalty
        
        return max(0.0, min(1.0, final_confidence))
    
    def _validate_and_enrich_results(self, extraction_results: Dict[str, Any], 
                                   characteristics: DocumentCharacteristics) -> Dict[str, Any]:
        """Validar y enriquecer resultados de extracción."""
        
        validated_tables = []
        
        for table in extraction_results['tables']:
            # Validar estructura básica
            if self._is_valid_table_structure(table):
                # Enriquecer con metadatos
                enriched_table = self._enrich_table_metadata(table, characteristics)
                validated_tables.append(enriched_table)
        
        # Calcular confianza general
        if validated_tables:
            overall_confidence = sum(t['confidence'] for t in validated_tables) / len(validated_tables)
        else:
            overall_confidence = 0.0
        
        return {
            'tables': validated_tables,
            'overall_confidence': overall_confidence,
            'primary_method': extraction_results.get('primary_method'),
            'fallbacks_used': extraction_results.get('fallbacks_used', [])
        }
    
    def _is_valid_table_structure(self, table: Dict[str, Any]) -> bool:
        """Validar que la tabla tiene una estructura válida."""
        
        # Verificaciones básicas
        if not table.get('data') or not table.get('headers'):
            return False
        
        # Al menos una fila de datos
        if len(table['data']) == 0:
            return False
        
        # Headers y datos deben tener estructura consistente
        header_count = len(table['headers'])
        for row in table['data']:
            if len(row) != header_count:
                # Permitir ligera inconsistencia
                if abs(len(row) - header_count) > 1:
                    return False
        
        return True
    
    def _enrich_table_metadata(self, table: Dict[str, Any], 
                             characteristics: DocumentCharacteristics) -> Dict[str, Any]:
        """Enriquecer tabla con metadatos adicionales."""
        
        enriched = table.copy()
        
        # Detectar tipo de contenido
        content_type = self._detect_table_content_type(table)
        enriched['content_type'] = content_type
        
        # Calcular métricas de calidad
        enriched['quality_metrics'] = {
            'completeness': self._calculate_completeness(table),
            'consistency': self._calculate_consistency(table),
            'relevance': self._calculate_relevance(table, characteristics)
        }
        
        # Detectar numerales y montos en la tabla
        enriched['extracted_entities'] = self._extract_entities_from_table(table)
        
        return enriched
    
    def _detect_table_content_type(self, table: Dict[str, Any]) -> str:
        """Detectar tipo de contenido de la tabla."""
        
        # Analizar headers y contenido
        headers = ' '.join(table.get('headers', [])).lower()
        content = ' '.join([' '.join(row) for row in table.get('data', [])]).lower()
        
        if 'viático' in headers or 'viático' in content:
            return 'viaticos'
        elif 'monto' in headers or 'amount' in headers:
            return 'financial'
        elif 'numeral' in headers or any(c.isdigit() and '.' in c for c in content.split()):
            return 'regulatory'
        else:
            return 'general'
    
    def _calculate_completeness(self, table: Dict[str, Any]) -> float:
        """Calcular completitud de la tabla."""
        
        total_cells = len(table['headers']) * len(table['data'])
        if total_cells == 0:
            return 0.0
        
        filled_cells = 0
        for row in table['data']:
            for cell in row:
                if cell and str(cell).strip():
                    filled_cells += 1
        
        return filled_cells / total_cells
    
    def _calculate_consistency(self, table: Dict[str, Any]) -> float:
        """Calcular consistencia de la tabla."""
        
        if not table['data']:
            return 0.0
        
        # Verificar consistencia en número de columnas
        header_count = len(table['headers'])
        consistent_rows = sum(1 for row in table['data'] if len(row) == header_count)
        
        return consistent_rows / len(table['data'])
    
    def _calculate_relevance(self, table: Dict[str, Any], 
                           characteristics: DocumentCharacteristics) -> float:
        """Calcular relevancia de la tabla para el documento."""
        
        # Factores de relevancia basados en contenido
        content = ' '.join([' '.join(row) for row in table.get('data', [])]).lower()
        
        relevance_keywords = {
            'directiva': ['viático', 'monto', 'límite', 'declaración'],
            'decreto': ['artículo', 'disposición', 'numeral'],
            'resolucion': ['aprobar', 'establecer', 'modificar']
        }
        
        doc_keywords = relevance_keywords.get(characteristics.document_type, [])
        keyword_matches = sum(1 for keyword in doc_keywords if keyword in content)
        
        return min(1.0, keyword_matches / max(1, len(doc_keywords)))
    
    def _extract_entities_from_table(self, table: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extraer entidades (numerales, montos) de la tabla."""
        
        import re
        
        entities = {
            'numerals': [],
            'amounts': [],
            'articles': []
        }
        
        # Patrones para entidades
        numeral_pattern = r'\b\d+(?:\.\d+)+\b'  # 8.4.17, 10.2.3
        amount_pattern = r'S/\s*\d+(?:,\d{3})*(?:\.\d{2})?'  # S/ 380.00
        article_pattern = r'(?:art|artículo)\.?\s*\d+'  # Art. 23
        
        # Buscar en toda la tabla
        all_content = ' '.join(table.get('headers', []))
        for row in table.get('data', []):
            all_content += ' ' + ' '.join(str(cell) for cell in row)
        
        # Extraer entidades
        entities['numerals'] = re.findall(numeral_pattern, all_content)
        entities['amounts'] = re.findall(amount_pattern, all_content, re.IGNORECASE)
        entities['articles'] = re.findall(article_pattern, all_content, re.IGNORECASE)
        
        return entities
    
    def _update_learning_stats(self, pdf_path: str, characteristics: DocumentCharacteristics, 
                             results: Dict[str, Any]):
        """Actualizar estadísticas de aprendizaje."""
        
        self.performance_stats['total_extractions'] += 1
        
        if results['overall_confidence'] > 0.7:
            self.performance_stats['successful_extractions'] += 1
        
        # Actualizar confianza promedio
        total_conf = self.performance_stats['average_confidence'] * (self.performance_stats['total_extractions'] - 1)
        self.performance_stats['average_confidence'] = (total_conf + results['overall_confidence']) / self.performance_stats['total_extractions']
        
        # Estadísticas por método
        method = results.get('primary_method', 'unknown')
        if method not in self.performance_stats['method_performance']:
            self.performance_stats['method_performance'][method] = {'count': 0, 'avg_confidence': 0.0}
        
        method_stats = self.performance_stats['method_performance'][method]
        method_stats['count'] += 1
        total_method_conf = method_stats['avg_confidence'] * (method_stats['count'] - 1)
        method_stats['avg_confidence'] = (total_method_conf + results['overall_confidence']) / method_stats['count']
        
        # Guardar configuración exitosa para tipos de documento similares
        if results['overall_confidence'] > 0.8:
            doc_type = characteristics.document_type
            if doc_type not in self.learned_optimizations:
                self.learned_optimizations[doc_type] = []
            
            self.learned_optimizations[doc_type].append({
                'characteristics': characteristics,
                'successful_method': method,
                'confidence_achieved': results['overall_confidence']
            })
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Obtener reporte de rendimiento del extractor."""
        
        success_rate = 0.0
        if self.performance_stats['total_extractions'] > 0:
            success_rate = self.performance_stats['successful_extractions'] / self.performance_stats['total_extractions']
        
        return {
            'total_extractions': self.performance_stats['total_extractions'],
            'success_rate': success_rate,
            'average_confidence': self.performance_stats['average_confidence'],
            'method_performance': self.performance_stats['method_performance'],
            'learned_optimizations_count': sum(len(opts) for opts in self.learned_optimizations.values()),
            'supported_document_types': list(self.learned_optimizations.keys())
        }
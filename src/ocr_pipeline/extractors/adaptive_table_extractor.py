#!/usr/bin/env python3
"""
Extractor Adaptativo de Tablas
==============================

Sistema inteligente que se auto-optimiza para extraer información de CUALQUIER documento
sin configuración manual. Aprende y se adapta automáticamente.
"""

import logging
import time
import cv2
import numpy as np
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import json
from collections import defaultdict, Counter

from .smart_money_detector import SmartMoneyDetector

logger = logging.getLogger(__name__)

class AdaptiveTableExtractor:
    """Extractor que se adapta automáticamente a cualquier tipo de documento"""
    
    def __init__(self, adaptive_mode: bool = True, learning_enabled: bool = True):
        self.adaptive_mode = adaptive_mode
        self.learning_enabled = learning_enabled
        
        # Detector inteligente de montos
        self.money_detector = SmartMoneyDetector(learning_mode=learning_enabled)
        
        # Estrategias de extracción ordenadas por eficiencia
        self.extraction_strategies = [
            {
                'name': 'camelot_stream_fast',
                'method': self._extract_camelot_stream,
                'params': {'flavor': 'stream', 'edge_tol': 50},
                'expected_time': 2.0,
                'best_for': ['digital_pdf', 'simple_tables']
            },
            {
                'name': 'camelot_lattice_normal',
                'method': self._extract_camelot_lattice,
                'params': {'flavor': 'lattice', 'line_scale': 15},
                'expected_time': 5.0,
                'best_for': ['scanned_pdf', 'bordered_tables']
            },
            {
                'name': 'camelot_lattice_sensitive',
                'method': self._extract_camelot_lattice,
                'params': {'flavor': 'lattice', 'line_scale': 40, 'process_background': True},
                'expected_time': 10.0,
                'best_for': ['poor_quality', 'faint_lines']
            },
            {
                'name': 'pdfplumber_adaptive',
                'method': self._extract_pdfplumber_adaptive,
                'params': {'adaptive_settings': True},
                'expected_time': 3.0,
                'best_for': ['text_based', 'no_borders']
            },
            {
                'name': 'opencv_preprocessing',
                'method': self._extract_with_opencv,
                'params': {'aggressive_preprocessing': True},
                'expected_time': 15.0,
                'best_for': ['very_poor_quality', 'handwritten']
            }
        ]
        
        # Historial de rendimiento para optimización
        self.performance_history = []
        self.document_characteristics_cache = {}
        
        # Cargar configuración optimizada
        self._load_optimization_data()
    
    def extract_from_pdf(self, pdf_path: str, auto_optimize: bool = True) -> Dict[str, Any]:
        """
        Extracción principal que se auto-optimiza para el documento
        
        Args:
            pdf_path: Ruta al archivo PDF
            auto_optimize: Si debe auto-optimizar la estrategia
            
        Returns:
            Resultados de extracción con metadatos de optimización
        """
        logger.info(f"🧠 Iniciando extracción adaptativa para: {Path(pdf_path).name}")
        
        start_time = time.time()
        
        # Analizar características del documento
        doc_characteristics = self._analyze_document_characteristics(pdf_path)
        logger.info(f"📊 Características detectadas: {doc_characteristics['summary']}")
        
        # Seleccionar estrategia óptima
        if auto_optimize:
            optimal_strategy = self._select_optimal_strategy(doc_characteristics)
        else:
            optimal_strategy = self.extraction_strategies[0]  # Usar la primera por defecto
        
        logger.info(f"🎯 Estrategia seleccionada: {optimal_strategy['name']}")
        
        # Intentar extracción con estrategia óptima
        results = self._attempt_extraction_with_fallback(pdf_path, optimal_strategy, doc_characteristics)
        
        # Post-procesamiento inteligente
        results = self._intelligent_post_processing(results, doc_characteristics)
        
        # Calcular métricas finales
        total_time = time.time() - start_time
        results.update({
            'total_extraction_time': total_time,
            'document_characteristics': doc_characteristics,
            'strategy_used': optimal_strategy['name'],
            'adaptive_mode': self.adaptive_mode,
            'optimization_applied': auto_optimize
        })
        
        # Aprender de esta extracción
        if self.learning_enabled:
            self._learn_from_extraction(pdf_path, results, optimal_strategy)
        
        # Log resultados
        self._log_extraction_results(results)
        
        return results
    
    def _analyze_document_characteristics(self, pdf_path: str) -> Dict[str, Any]:
        """Analiza las características del documento para optimizar extracción"""
        
        # Verificar caché
        file_stat = Path(pdf_path).stat()
        cache_key = f"{pdf_path}_{file_stat.st_mtime}_{file_stat.st_size}"
        
        if cache_key in self.document_characteristics_cache:
            return self.document_characteristics_cache[cache_key]
        
        logger.info("🔍 Analizando características del documento...")
        
        characteristics = {
            'file_size_mb': file_stat.st_size / (1024 * 1024),
            'is_scanned': False,
            'has_complex_tables': False,
            'text_quality': 'good',
            'page_count': 0,
            'has_borders': False,
            'layout_complexity': 'simple',
            'summary': ''
        }
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            characteristics['page_count'] = len(doc)
            
            # Analizar primeras páginas para determinar características
            sample_pages = min(3, len(doc))
            text_lengths = []
            image_counts = []
            
            for page_num in range(sample_pages):
                page = doc.load_page(page_num)
                
                # Analizar texto
                text = page.get_text()
                text_lengths.append(len(text))
                
                # Analizar imágenes (indicador de documento escaneado)
                images = page.get_images()
                image_counts.append(len(images))
                
                # Analizar calidad del texto
                if text:
                    # Buscar caracteres extraños que indican OCR pobre
                    ocr_artifacts = len(re.findall(r'[^\w\s\.,;:!?\-()"]', text))
                    if ocr_artifacts > len(text) * 0.05:  # Más del 5% de caracteres extraños
                        characteristics['text_quality'] = 'poor'
                
                # Detectar bordes de tabla (líneas horizontales/verticales)
                if self._detect_table_borders(page):
                    characteristics['has_borders'] = True
            
            doc.close()
            
            # Determinar si es documento escaneado
            avg_images_per_page = sum(image_counts) / len(image_counts) if image_counts else 0
            avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
            
            if avg_images_per_page > 0.5 or avg_text_length < 500:
                characteristics['is_scanned'] = True
            
            # Determinar complejidad del layout
            if characteristics['file_size_mb'] > 10 or characteristics['page_count'] > 20:
                characteristics['layout_complexity'] = 'complex'
            elif avg_text_length > 2000:
                characteristics['layout_complexity'] = 'medium'
            
            # Detectar tablas complejas
            if characteristics['has_borders'] and characteristics['page_count'] > 5:
                characteristics['has_complex_tables'] = True
            
        except Exception as e:
            logger.warning(f"Error analizando documento: {e}")
        
        # Crear resumen
        characteristics['summary'] = self._create_characteristics_summary(characteristics)
        
        # Guardar en caché
        self.document_characteristics_cache[cache_key] = characteristics
        
        return characteristics
    
    def _detect_table_borders(self, page) -> bool:
        """Detecta si la página tiene bordes de tabla visibles"""
        try:
            # Obtener imagen de la página
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            # Convertir a OpenCV
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detectar líneas horizontales y verticales
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Contar líneas detectadas
            h_lines = cv2.countNonZero(horizontal_lines)
            v_lines = cv2.countNonZero(vertical_lines)
            
            # Si hay suficientes líneas, probablemente hay tablas con bordes
            return (h_lines + v_lines) > 1000
            
        except Exception:
            return False
    
    def _create_characteristics_summary(self, chars: Dict[str, Any]) -> str:
        """Crea un resumen legible de las características"""
        summary_parts = []
        
        if chars['is_scanned']:
            summary_parts.append("escaneado")
        else:
            summary_parts.append("digital")
        
        summary_parts.append(f"{chars['page_count']} páginas")
        summary_parts.append(f"calidad {chars['text_quality']}")
        
        if chars['has_complex_tables']:
            summary_parts.append("tablas complejas")
        elif chars['has_borders']:
            summary_parts.append("con bordes")
        
        summary_parts.append(f"layout {chars['layout_complexity']}")
        
        return ", ".join(summary_parts)
    
    def _select_optimal_strategy(self, doc_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Selecciona la estrategia óptima basada en características del documento"""
        
        # Buscar en historial de rendimiento
        similar_docs = self._find_similar_documents(doc_characteristics)
        
        if similar_docs:
            # Usar estrategia que mejor funcionó con documentos similares
            best_strategy_name = max(similar_docs, key=lambda x: similar_docs[x]['avg_confidence'])
            
            for strategy in self.extraction_strategies:
                if strategy['name'] == best_strategy_name:
                    logger.info(f"📈 Estrategia seleccionada por historial: {best_strategy_name}")
                    return strategy
        
        # Selección basada en características
        if doc_characteristics['is_scanned']:
            if doc_characteristics['text_quality'] == 'poor':
                # Documento escaneado de mala calidad
                return next(s for s in self.extraction_strategies if s['name'] == 'opencv_preprocessing')
            else:
                # Documento escaneado de buena calidad
                return next(s for s in self.extraction_strategies if s['name'] == 'camelot_lattice_sensitive')
        
        elif doc_characteristics['has_complex_tables']:
            # Tablas complejas
            return next(s for s in self.extraction_strategies if s['name'] == 'camelot_lattice_normal')
        
        elif doc_characteristics['layout_complexity'] == 'simple':
            # Documento simple
            return next(s for s in self.extraction_strategies if s['name'] == 'camelot_stream_fast')
        
        else:
            # Por defecto, usar PDFplumber adaptativo
            return next(s for s in self.extraction_strategies if s['name'] == 'pdfplumber_adaptive')
    
    def _attempt_extraction_with_fallback(self, pdf_path: str, primary_strategy: Dict[str, Any], 
                                        doc_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Intenta extracción con estrategia principal y fallbacks inteligentes"""
        
        strategies_to_try = [primary_strategy]
        
        # Agregar fallbacks basados en características
        for strategy in self.extraction_strategies:
            if strategy != primary_strategy and strategy not in strategies_to_try:
                strategies_to_try.append(strategy)
        
        best_results = {'confidence': 0, 'amounts': [], 'chunks': [], 'method_used': 'none'}
        
        for strategy in strategies_to_try:
            try:
                logger.info(f"🔄 Probando estrategia: {strategy['name']}")
                
                start_time = time.time()
                results = strategy['method'](pdf_path, strategy['params'])
                extraction_time = time.time() - start_time
                
                # Calcular confianza de la extracción
                confidence = self._calculate_extraction_confidence(results, doc_characteristics)
                
                results.update({
                    'confidence': confidence,
                    'extraction_time': extraction_time,
                    'method_used': strategy['name']
                })
                
                logger.info(f"✅ {strategy['name']}: confianza {confidence:.2f}, tiempo {extraction_time:.2f}s")
                
                # Si confianza es alta, usar estos resultados
                if confidence > best_results['confidence']:
                    best_results = results
                
                # Si confianza > 90%, no probar más estrategias
                if confidence > 0.9:
                    logger.info(f"🎯 Confianza alta alcanzada, usando {strategy['name']}")
                    break
                
            except Exception as e:
                logger.warning(f"❌ Estrategia {strategy['name']} falló: {e}")
                continue
        
        return best_results
    
    def _extract_camelot_stream(self, pdf_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracción con Camelot stream"""
        try:
            import camelot
            
            tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all', **params)
            return self._process_camelot_tables(tables, 'stream')
            
        except ImportError:
            raise Exception("Camelot no disponible")
        except Exception as e:
            raise Exception(f"Error en Camelot stream: {e}")
    
    def _extract_camelot_lattice(self, pdf_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracción con Camelot lattice"""
        try:
            import camelot
            
            tables = camelot.read_pdf(pdf_path, flavor='lattice', pages='all', **params)
            return self._process_camelot_tables(tables, 'lattice')
            
        except ImportError:
            raise Exception("Camelot no disponible")
        except Exception as e:
            raise Exception(f"Error en Camelot lattice: {e}")
    
    def _extract_pdfplumber_adaptive(self, pdf_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracción adaptativa con PDFplumber"""
        try:
            import pdfplumber
            
            chunks = []
            amounts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Configuración adaptativa basada en la página
                    table_settings = self._get_adaptive_table_settings(page)
                    
                    # Extraer tablas
                    tables = page.extract_tables(table_settings)
                    
                    if tables:
                        for table_idx, table in enumerate(tables):
                            table_chunks = self._process_pdfplumber_table(table, page_num + 1, table_idx)
                            chunks.extend(table_chunks)
                    
                    # Extraer texto para montos
                    text = page.extract_text()
                    if text:
                        page_amounts = self.money_detector.extract_all_amounts(text)
                        amounts.extend(page_amounts)
            
            return {
                'chunks': chunks,
                'amounts': amounts,
                'tables_found': len(chunks),
                'method': 'pdfplumber_adaptive'
            }
            
        except ImportError:
            raise Exception("PDFplumber no disponible")
        except Exception as e:
            raise Exception(f"Error en PDFplumber: {e}")
    
    def _extract_with_opencv(self, pdf_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracción con pre-procesamiento OpenCV agresivo"""
        try:
            # Implementación básica - usar PyMuPDF + OpenCV para preprocesamiento
            import fitz
            
            chunks = []
            amounts = []
            
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Obtener imagen de la página
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Convertir a OpenCV
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is not None:
                    # Pre-procesamiento básico
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Mejorar contraste
                    enhanced = cv2.equalizeHist(gray)
                    
                    # Extraer texto básico de la página original
                    text = page.get_text()
                    
                    if text:
                        page_amounts = self.money_detector.extract_all_amounts(text)
                        amounts.extend(page_amounts)
                        
                        if page_amounts:
                            chunk = {
                                'id': f'opencv_p{page_num + 1}',
                                'content': text,
                                'metadata': {
                                    'extraction_method': 'opencv_preprocessing',
                                    'page': page_num + 1,
                                    'confidence': 0.7,
                                    'amounts_found': [a['raw_text'] for a in page_amounts]
                                }
                            }
                            chunks.append(chunk)
            
            doc.close()
            
            return {
                'chunks': chunks,
                'amounts': amounts,
                'tables_found': len(chunks),
                'method': 'opencv_preprocessing'
            }
            
        except Exception as e:
            raise Exception(f"Error en OpenCV: {e}")
    
    def _process_camelot_tables(self, tables, method: str) -> Dict[str, Any]:
        """Procesa tablas de Camelot"""
        chunks = []
        amounts = []
        
        for table_idx, table in enumerate(tables):
            try:
                df = table.df
                
                # Extraer texto de la tabla
                table_text = ""
                for row_idx, row in df.iterrows():
                    for col_idx, cell in enumerate(row):
                        cell_str = str(cell).strip()
                        table_text += f"{cell_str} "
                
                # Detectar montos en la tabla
                table_amounts = self.money_detector.extract_all_amounts(table_text)
                amounts.extend(table_amounts)
                
                # Crear chunk si tiene contenido valioso
                if table_amounts or len(table_text.strip()) > 50:
                    chunk = {
                        'id': f'{method}_table_{table_idx}',
                        'content': table_text.strip(),
                        'metadata': {
                            'extraction_method': method,
                            'table_index': table_idx,
                            'page': getattr(table, 'page', 'unknown'),
                            'confidence': getattr(table, 'accuracy', 0.8),
                            'amounts_found': [a['raw_text'] for a in table_amounts]
                        }
                    }
                    chunks.append(chunk)
                    
            except Exception as e:
                logger.warning(f"Error procesando tabla {table_idx}: {e}")
                continue
        
        return {
            'chunks': chunks,
            'amounts': amounts,
            'tables_found': len(tables),
            'method': method
        }
    
    def _process_pdfplumber_table(self, table: List[List[str]], page_num: int, table_idx: int) -> List[Dict[str, Any]]:
        """Procesa tabla de PDFplumber"""
        chunks = []
        
        # Convertir tabla a texto
        table_text = ""
        for row in table:
            for cell in row:
                if cell:
                    table_text += f"{str(cell).strip()} "
        
        # Detectar montos
        amounts = self.money_detector.extract_all_amounts(table_text)
        
        # Crear chunk si tiene contenido valioso
        if amounts or len(table_text.strip()) > 30:
            chunk = {
                'id': f'pdfplumber_p{page_num}_t{table_idx}',
                'content': table_text.strip(),
                'metadata': {
                    'extraction_method': 'pdfplumber',
                    'page': page_num,
                    'table_index': table_idx,
                    'confidence': 0.85,
                    'amounts_found': [a['raw_text'] for a in amounts]
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _get_adaptive_table_settings(self, page) -> Dict[str, Any]:
        """Obtiene configuración adaptativa para extracción de tablas"""
        # Configuración base
        settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 1,
            "min_words_horizontal": 1,
        }
        
        # Adaptar basado en características de la página
        try:
            text = page.extract_text()
            
            # Si hay mucho texto, usar configuración más estricta
            if text and len(text) > 2000:
                settings["snap_tolerance"] = 5
                settings["join_tolerance"] = 5
            
            # Si hay poco texto, ser más permisivo
            elif text and len(text) < 500:
                settings["snap_tolerance"] = 2
                settings["min_words_vertical"] = 0
                settings["min_words_horizontal"] = 0
                
        except Exception:
            pass
        
        return settings
    
    def _calculate_extraction_confidence(self, results: Dict[str, Any], 
                                       doc_characteristics: Dict[str, Any]) -> float:
        """Calcula la confianza de la extracción"""
        confidence = 0.0
        
        # Factor 1: Cantidad de contenido extraído (30%)
        chunks_count = len(results.get('chunks', []))
        amounts_count = len(results.get('amounts', []))
        
        if chunks_count > 0:
            confidence += 0.15
        if chunks_count > 5:
            confidence += 0.15
        
        if amounts_count > 0:
            confidence += 0.15
        if amounts_count > 3:
            confidence += 0.15
        
        # Factor 2: Calidad del contenido (40%)
        if results.get('amounts'):
            avg_amount_confidence = sum(a.get('confidence', 0.5) for a in results['amounts']) / len(results['amounts'])
            confidence += 0.4 * avg_amount_confidence
        
        # Factor 3: Coherencia con características del documento (20%)
        method_used = results.get('method', '')
        
        if doc_characteristics['is_scanned'] and 'lattice' in method_used:
            confidence += 0.1
        elif not doc_characteristics['is_scanned'] and 'stream' in method_used:
            confidence += 0.1
        
        if doc_characteristics['has_complex_tables'] and chunks_count > 3:
            confidence += 0.1
        
        # Factor 4: Tiempo de extracción razonable (10%)
        extraction_time = results.get('extraction_time', 0)
        expected_time = 10.0  # segundos
        
        if extraction_time <= expected_time:
            confidence += 0.1
        elif extraction_time <= expected_time * 2:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _intelligent_post_processing(self, results: Dict[str, Any], 
                                   doc_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Post-procesamiento inteligente de resultados"""
        
        # Eliminar duplicados inteligentemente
        if results.get('amounts'):
            results['amounts'] = self._remove_duplicate_amounts_smart(results['amounts'])
        
        # Enriquecer chunks con información contextual
        if results.get('chunks'):
            results['chunks'] = self._enrich_chunks_with_context(results['chunks'], results.get('amounts', []))
        
        # Agregar metadatos de calidad
        results['quality_metrics'] = self._calculate_quality_metrics(results)
        
        return results
    
    def _remove_duplicate_amounts_smart(self, amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Elimina duplicados de manera inteligente"""
        if not amounts:
            return amounts
        
        # Agrupar por valor similar
        amount_groups = defaultdict(list)
        
        for amount in amounts:
            # Redondear para agrupar valores similares
            rounded_value = round(amount['amount'], 2)
            amount_groups[rounded_value].append(amount)
        
        # Mantener el mejor de cada grupo
        unique_amounts = []
        
        for value, group in amount_groups.items():
            if len(group) == 1:
                unique_amounts.append(group[0])
            else:
                # Mantener el de mayor confianza
                best_amount = max(group, key=lambda x: x['confidence'])
                unique_amounts.append(best_amount)
        
        return sorted(unique_amounts, key=lambda x: x['confidence'], reverse=True)
    
    def _enrich_chunks_with_context(self, chunks: List[Dict[str, Any]], 
                                  amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enriquece chunks con información contextual"""
        
        for chunk in chunks:
            # Agregar montos relacionados
            chunk_amounts = []
            chunk_content = chunk.get('content', '').lower()
            
            for amount in amounts:
                amount_context = amount.get('context', '').lower()
                
                # Verificar si el monto está relacionado con el chunk
                if (chunk_content in amount_context or 
                    amount_context in chunk_content or
                    abs(len(chunk_content) - len(amount_context)) < 100):
                    chunk_amounts.append(amount)
            
            chunk['related_amounts'] = chunk_amounts
            chunk['has_monetary_content'] = len(chunk_amounts) > 0
        
        return chunks
    
    def _calculate_quality_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de calidad de la extracción"""
        
        metrics = {
            'extraction_completeness': 0.0,
            'data_consistency': 0.0,
            'content_richness': 0.0,
            'overall_quality': 0.0
        }
        
        # Completeness: basado en cantidad de contenido extraído
        chunks_count = len(results.get('chunks', []))
        amounts_count = len(results.get('amounts', []))
        
        if chunks_count > 0 and amounts_count > 0:
            metrics['extraction_completeness'] = min(1.0, (chunks_count + amounts_count) / 10)
        
        # Consistency: basado en coherencia de los datos
        if results.get('amounts'):
            confidences = [a.get('confidence', 0.5) for a in results['amounts']]
            metrics['data_consistency'] = sum(confidences) / len(confidences)
        
        # Content richness: basado en diversidad del contenido
        if results.get('chunks'):
            total_content_length = sum(len(c.get('content', '')) for c in results['chunks'])
            metrics['content_richness'] = min(1.0, total_content_length / 5000)
        
        # Overall quality
        metrics['overall_quality'] = (
            metrics['extraction_completeness'] * 0.4 +
            metrics['data_consistency'] * 0.4 +
            metrics['content_richness'] * 0.2
        )
        
        return metrics
    
    def _find_similar_documents(self, doc_characteristics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Encuentra documentos similares en el historial"""
        similar_docs = {}
        
        for record in self.performance_history:
            similarity_score = self._calculate_document_similarity(
                doc_characteristics, 
                record.get('document_characteristics', {})
            )
            
            if similarity_score > 0.7:  # Umbral de similitud
                strategy_name = record.get('strategy_used', 'unknown')
                
                if strategy_name not in similar_docs:
                    similar_docs[strategy_name] = {
                        'count': 0,
                        'avg_confidence': 0.0,
                        'avg_time': 0.0
                    }
                
                similar_docs[strategy_name]['count'] += 1
                similar_docs[strategy_name]['avg_confidence'] += record.get('confidence', 0.0)
                similar_docs[strategy_name]['avg_time'] += record.get('extraction_time', 0.0)
        
        # Calcular promedios
        for strategy_data in similar_docs.values():
            if strategy_data['count'] > 0:
                strategy_data['avg_confidence'] /= strategy_data['count']
                strategy_data['avg_time'] /= strategy_data['count']
        
        return similar_docs
    
    def _calculate_document_similarity(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
        """Calcula similitud entre dos documentos"""
        if not doc1 or not doc2:
            return 0.0
        
        similarity_factors = []
        
        # Comparar tipo (escaneado vs digital)
        if doc1.get('is_scanned') == doc2.get('is_scanned'):
            similarity_factors.append(0.3)
        
        # Comparar calidad del texto
        if doc1.get('text_quality') == doc2.get('text_quality'):
            similarity_factors.append(0.2)
        
        # Comparar complejidad del layout
        if doc1.get('layout_complexity') == doc2.get('layout_complexity'):
            similarity_factors.append(0.2)
        
        # Comparar presencia de bordes
        if doc1.get('has_borders') == doc2.get('has_borders'):
            similarity_factors.append(0.1)
        
        # Comparar tamaño (similar rango)
        size1 = doc1.get('file_size_mb', 0)
        size2 = doc2.get('file_size_mb', 0)
        
        if size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            if size_ratio > 0.5:  # Tamaños similares
                similarity_factors.append(0.2)
        
        return sum(similarity_factors)
    
    def _learn_from_extraction(self, pdf_path: str, results: Dict[str, Any], strategy: Dict[str, Any]):
        """Aprende de la extracción para mejorar futuras extracciones"""
        
        learning_record = {
            'timestamp': datetime.now().isoformat(),
            'pdf_path': pdf_path,
            'document_characteristics': results.get('document_characteristics', {}),
            'strategy_used': strategy['name'],
            'confidence': results.get('confidence', 0.0),
            'extraction_time': results.get('extraction_time', 0.0),
            'chunks_count': len(results.get('chunks', [])),
            'amounts_count': len(results.get('amounts', [])),
            'quality_metrics': results.get('quality_metrics', {})
        }
        
        self.performance_history.append(learning_record)
        
        # Mantener solo los últimos 100 registros
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Guardar datos de optimización
        self._save_optimization_data()
        
        logger.info(f"📚 Aprendizaje registrado: confianza {results.get('confidence', 0.0):.2f}")
    
    def _load_optimization_data(self):
        """Carga datos de optimización previos"""
        optimization_file = Path("data/optimization_data.json")
        
        if optimization_file.exists():
            try:
                with open(optimization_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.performance_history = data.get('performance_history', [])
                    logger.info(f"📚 Cargados {len(self.performance_history)} registros de optimización")
            except Exception as e:
                logger.warning(f"Error cargando datos de optimización: {e}")
    
    def _save_optimization_data(self):
        """Guarda datos de optimización"""
        optimization_file = Path("data/optimization_data.json")
        optimization_file.parent.mkdir(exist_ok=True)
        
        try:
            data = {
                'performance_history': self.performance_history,
                'last_updated': datetime.now().isoformat(),
                'total_extractions': len(self.performance_history)
            }
            
            with open(optimization_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Error guardando datos de optimización: {e}")
    
    def _log_extraction_results(self, results: Dict[str, Any]):
        """Log detallado de resultados"""
        
        logger.info("🎯 RESULTADOS DE EXTRACCIÓN ADAPTATIVA:")
        logger.info(f"   🔧 Estrategia: {results.get('strategy_used', 'unknown')}")
        logger.info(f"   📊 Confianza: {results.get('confidence', 0.0):.2f}")
        logger.info(f"   ⏱️  Tiempo: {results.get('extraction_time', 0.0):.2f}s")
        logger.info(f"   📋 Chunks: {len(results.get('chunks', []))}")
        logger.info(f"   💰 Montos: {len(results.get('amounts', []))}")
        
        quality = results.get('quality_metrics', {})
        if quality:
            logger.info(f"   🏆 Calidad general: {quality.get('overall_quality', 0.0):.2f}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de optimización"""
        
        if not self.performance_history:
            return {'message': 'No hay datos de optimización disponibles'}
        
        # Calcular estadísticas
        confidences = [r.get('confidence', 0.0) for r in self.performance_history]
        times = [r.get('extraction_time', 0.0) for r in self.performance_history]
        strategies = [r.get('strategy_used', 'unknown') for r in self.performance_history]
        
        strategy_performance = defaultdict(list)
        for record in self.performance_history:
            strategy_name = record.get('strategy_used', 'unknown')
            strategy_performance[strategy_name].append(record.get('confidence', 0.0))
        
        return {
            'total_extractions': len(self.performance_history),
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0.0,
            'average_time': sum(times) / len(times) if times else 0.0,
            'best_strategy': max(strategy_performance.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if strategy_performance else 'none',
            'strategy_usage': dict(Counter(strategies)),
            'learning_enabled': self.learning_enabled
        }


def create_adaptive_extractor(adaptive_mode: bool = True, learning_enabled: bool = True) -> AdaptiveTableExtractor:
    """Factory function para crear extractor adaptativo"""
    return AdaptiveTableExtractor(adaptive_mode=adaptive_mode, learning_enabled=learning_enabled)
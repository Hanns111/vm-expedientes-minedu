#!/usr/bin/env python3
"""
Adaptive Pipeline - Orquestador Universal para Extracción de Normas Legales
===========================================================================

Pipeline adaptativo que combina todos los componentes para procesar
automáticamente millones de normas legales sin configuración manual.
"""

import logging
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from .generic_table_extractor import GenericTableExtractor, DocumentCharacteristics
from .generic_money_detector import GenericMoneyDetector
from .config_optimizer import ConfigOptimizer, DocumentProfile, ExtractionConfig

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Resultado completo del procesamiento de un documento"""
    document_path: str
    success: bool
    processing_time: float
    
    # Datos extraídos
    tables: List[Dict[str, Any]]
    money_entities: List[Dict[str, Any]]
    numeral_entities: List[Dict[str, Any]]
    
    # Metadatos de procesamiento
    document_profile: DocumentProfile
    config_used: ExtractionConfig
    extraction_confidence: float
    
    # Estadísticas
    tables_found: int
    entities_found: int
    fallback_methods_used: List[str]
    
    # Control de versiones y fecha
    document_date: Optional[datetime] = None
    document_version: Optional[str] = None
    
    # Errores (si los hay)
    errors: List[str] = None
    warnings: List[str] = None

@dataclass
class BatchProcessingStats:
    """Estadísticas de procesamiento en lote"""
    total_documents: int = 0
    successful_documents: int = 0
    failed_documents: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    total_tables_found: int = 0
    total_entities_found: int = 0
    document_types_processed: Dict[str, int] = None
    
    def __post_init__(self):
        if self.document_types_processed is None:
            self.document_types_processed = {}

class AdaptivePipeline:
    """
    Pipeline adaptativo universal para procesamiento automático de normas legales.
    
    Características principales:
    - Procesamiento automático sin configuración manual
    - Auto-optimización basada en características del documento
    - Fallbacks inteligentes para máxima cobertura
    - Filtrado por fecha/versión para normas históricas
    - Procesamiento en lote de millones de documentos
    - Métricas detalladas de rendimiento y cobertura
    """
    
    def __init__(self, 
                 output_dir: str = "data/universal_extraction_results",
                 enable_learning: bool = True,
                 enable_caching: bool = True,
                 max_processing_time: int = 300):  # 5 minutos por documento
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_learning = enable_learning
        self.enable_caching = enable_caching
        self.max_processing_time = max_processing_time
        
        # Inicializar componentes
        self.table_extractor = GenericTableExtractor()
        self.money_detector = GenericMoneyDetector(learning_enabled=enable_learning)
        self.config_optimizer = ConfigOptimizer()
        
        # Estadísticas globales
        self.global_stats = BatchProcessingStats()
        
        # Cache de resultados exitosos
        self.results_cache: Dict[str, ProcessingResult] = {}
        
        # Filtros de fecha y versión
        self.date_filters = {
            'min_date': None,
            'max_date': None,
            'exclude_superseded': True
        }
        
        logger.info("AdaptivePipeline initialized with universal components")
    
    def process_document(self, pdf_path: str, 
                        document_metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Procesar un documento individual de forma completamente automática.
        
        Args:
            pdf_path: Ruta al documento PDF
            document_metadata: Metadatos opcionales del documento
            
        Returns:
            Resultado completo del procesamiento
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting adaptive processing: {Path(pdf_path).name}")
        
        # Verificar si el documento debe ser procesado
        if not self._should_process_document(pdf_path, document_metadata):
            return self._create_skipped_result(pdf_path, "Filtered by date/version criteria")
        
        # Verificar cache si está habilitado
        if self.enable_caching:
            cached_result = self._check_cache(pdf_path)
            if cached_result:
                logger.info(f"✅ Using cached result for {Path(pdf_path).name}")
                return cached_result
        
        errors = []
        warnings = []
        
        try:
            # 1. Optimizar configuración automáticamente
            logger.info("🔧 Optimizing configuration...")
            optimized_config = self.config_optimizer.optimize_config_for_document(pdf_path)
            
            # 2. Extraer tablas con configuración optimizada
            logger.info("📊 Extracting tables...")
            table_results = self._extract_tables_with_fallbacks(pdf_path, optimized_config, errors, warnings)
            
            # 3. Extraer entidades monetarias y numerales
            logger.info("💰 Extracting money and numeral entities...")
            entity_results = self._extract_entities_comprehensive(pdf_path, table_results, errors, warnings)
            
            # 4. Validar y enriquecer resultados
            logger.info("✅ Validating and enriching results...")
            validated_results = self._validate_and_enrich_results(
                pdf_path, table_results, entity_results, optimized_config, errors, warnings
            )
            
            # 5. Generar resultado final
            processing_time = time.time() - start_time
            result = self._create_processing_result(
                pdf_path, True, processing_time, validated_results, 
                optimized_config, errors, warnings, document_metadata
            )
            
            # 6. Aprender de los resultados si está habilitado
            if self.enable_learning:
                self._learn_from_results(result)
            
            # 7. Guardar en cache si está habilitado
            if self.enable_caching:
                self._cache_result(pdf_path, result)
            
            # 8. Actualizar estadísticas globales
            self._update_global_stats(result)
            
            logger.info(f"🎉 Processing completed: {result.tables_found} tables, {result.entities_found} entities in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Critical processing error: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            # Crear resultado de error
            return self._create_error_result(pdf_path, processing_time, errors, warnings)
    
    def process_batch(self, pdf_paths: List[str], 
                     max_workers: int = 4,
                     progress_callback: Optional[callable] = None) -> Dict[str, ProcessingResult]:
        """
        Procesar múltiples documentos en lote de forma eficiente.
        
        Args:
            pdf_paths: Lista de rutas a documentos PDF
            max_workers: Número máximo de trabajadores paralelos
            progress_callback: Función de callback para progreso
            
        Returns:
            Diccionario con resultados de procesamiento
        """
        logger.info(f"🚀 Starting batch processing: {len(pdf_paths)} documents")
        
        # Reiniciar estadísticas de lote
        batch_stats = BatchProcessingStats()
        batch_results = {}
        
        # Filtrar documentos que deben ser procesados
        filtered_paths = [path for path in pdf_paths if self._should_process_document(path)]
        logger.info(f"📋 Processing {len(filtered_paths)} documents after filtering")
        
        start_time = time.time()
        
        if max_workers == 1:
            # Procesamiento secuencial
            batch_results = self._process_batch_sequential(filtered_paths, progress_callback)
        else:
            # Procesamiento paralelo
            batch_results = self._process_batch_parallel(filtered_paths, max_workers, progress_callback)
        
        # Calcular estadísticas finales
        total_time = time.time() - start_time
        batch_stats = self._calculate_batch_stats(batch_results, total_time)
        
        # Guardar resultados de lote
        self._save_batch_results(batch_results, batch_stats)
        
        logger.info(f"🎉 Batch processing completed: {batch_stats.successful_documents}/{batch_stats.total_documents} successful in {total_time:.2f}s")
        
        return batch_results
    
    def _extract_tables_with_fallbacks(self, pdf_path: str, config: ExtractionConfig, 
                                     errors: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Extraer tablas con fallbacks inteligentes."""
        
        try:
            # Configurar extractor con parámetros optimizados
            extraction_result = self.table_extractor.extract_tables_universal(pdf_path)
            
            if not extraction_result['tables']:
                warnings.append("No tables found with primary method")
                
                # Intentar con configuración más agresiva
                logger.info("🔄 Trying fallback table extraction...")
                fallback_result = self._try_fallback_table_extraction(pdf_path, config)
                
                if fallback_result['tables']:
                    extraction_result = fallback_result
                    warnings.append(f"Used fallback method: {fallback_result['metadata']['extraction_method']}")
            
            return extraction_result
            
        except Exception as e:
            error_msg = f"Table extraction failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return {'tables': [], 'metadata': {'error': error_msg}}
    
    def _try_fallback_table_extraction(self, pdf_path: str, config: ExtractionConfig) -> Dict[str, Any]:
        """Intentar extracción de tablas con métodos de fallback."""
        
        # Configuraciones de fallback más agresivas
        fallback_configs = [
            # Configuración más sensible
            {
                'camelot_flavor': 'stream' if config.camelot_flavor == 'lattice' else 'lattice',
                'camelot_line_scale': config.camelot_line_scale + 20,
                'opencv_enable_preprocessing': True
            },
            # Configuración muy permisiva
            {
                'camelot_flavor': 'stream',
                'camelot_line_scale': 60,
                'opencv_enable_preprocessing': True,
                'camelot_confidence_threshold': 0.3
            }
        ]
        
        for fallback_config in fallback_configs:
            try:
                # Aplicar configuración de fallback
                modified_config = config
                for key, value in fallback_config.items():
                    setattr(modified_config, key, value)
                
                result = self.table_extractor.extract_tables_universal(pdf_path)
                
                if result['tables']:
                    result['metadata']['fallback_config'] = fallback_config
                    return result
                    
            except Exception as e:
                logger.debug(f"Fallback config failed: {e}")
                continue
        
        return {'tables': [], 'metadata': {'fallback_attempted': True}}
    
    def _extract_entities_comprehensive(self, pdf_path: str, table_results: Dict[str, Any],
                                      errors: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Extraer entidades de forma comprehensiva."""
        
        try:
            # Extraer texto completo del documento
            full_text = self._extract_full_text(pdf_path)
            
            # Añadir texto de tablas extraídas
            table_text = self._extract_text_from_tables(table_results.get('tables', []))
            combined_text = f"{full_text}\n\n{table_text}"
            
            # Detectar tipo de documento para contexto
            document_type = self._detect_document_type_from_text(combined_text)
            
            # Extraer entidades
            entity_results = self.money_detector.extract_entities_universal(combined_text, document_type)
            
            if not entity_results['money_entities'] and not entity_results['numeral_entities']:
                warnings.append("No monetary or numeral entities found")
            
            return entity_results
            
        except Exception as e:
            error_msg = f"Entity extraction failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return {'money_entities': [], 'numeral_entities': [], 'all_entities': []}
    
    def _extract_full_text(self, pdf_path: str) -> str:
        """Extraer texto completo del PDF."""
        
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page in doc:
                full_text += page.get_text() + "\n"
            
            doc.close()
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract full text: {e}")
            return ""
    
    def _extract_text_from_tables(self, tables: List[Dict[str, Any]]) -> str:
        """Extraer texto de las tablas encontradas."""
        
        table_text = ""
        
        for table in tables:
            # Añadir headers
            headers = table.get('headers', [])
            if headers:
                table_text += " ".join(str(h) for h in headers) + "\n"
            
            # Añadir datos
            data = table.get('data', [])
            for row in data:
                if row:
                    table_text += " ".join(str(cell) for cell in row) + "\n"
            
            table_text += "\n"
        
        return table_text
    
    def _detect_document_type_from_text(self, text: str) -> str:
        """Detectar tipo de documento del texto extraído."""
        
        text_lower = text.lower()
        
        # Patrones de detección más específicos
        patterns = {
            'directiva': ['directiva', 'directriz'],
            'resolucion': ['resolución', 'resolucion'],
            'decreto': ['decreto supremo', 'decreto'],
            'reglamento': ['reglamento'],
            'circular': ['circular'],
            'manual': ['manual', 'guía'],
            'norma_tecnica': ['norma técnica', 'especificación técnica']
        }
        
        for doc_type, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        return "legal_norm"
    
    def _validate_and_enrich_results(self, pdf_path: str, table_results: Dict[str, Any],
                                   entity_results: Dict[str, Any], config: ExtractionConfig,
                                   errors: List[str], warnings: List[str]) -> Dict[str, Any]:
        """Validar y enriquecer todos los resultados."""
        
        # Validar coherencia entre tablas y entidades
        table_entities = self._extract_entities_from_table_results(table_results)
        text_entities = entity_results.get('all_entities', [])
        
        # Cross-validation: entidades encontradas en tablas deben aparecer en texto
        cross_validated_entities = self._cross_validate_entities(table_entities, text_entities)
        
        # Enriquecer con metadatos de documento
        document_metadata = self._extract_document_metadata(pdf_path)
        
        # Calcular métricas de confianza global
        confidence_metrics = self._calculate_global_confidence(table_results, entity_results, cross_validated_entities)
        
        return {
            'tables': table_results.get('tables', []),
            'money_entities': entity_results.get('money_entities', []),
            'numeral_entities': entity_results.get('numeral_entities', []),
            'cross_validated_entities': cross_validated_entities,
            'document_metadata': document_metadata,
            'confidence_metrics': confidence_metrics,
            'validation_warnings': warnings,
            'validation_errors': errors
        }
    
    def _extract_entities_from_table_results(self, table_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extraer entidades específicamente de los resultados de tablas."""
        
        entities = []
        
        for table in table_results.get('tables', []):
            # Buscar entidades pre-extraídas en las tablas
            table_entities = table.get('extracted_entities', {})
            
            for entity_type, entity_list in table_entities.items():
                for entity in entity_list:
                    entities.append({
                        'value': entity,
                        'type': entity_type,
                        'source': f"table_{table.get('id', 'unknown')}",
                        'confidence': table.get('confidence', 0.5)
                    })
        
        return entities
    
    def _cross_validate_entities(self, table_entities: List[Dict[str, Any]], 
                               text_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cross-validar entidades entre tablas y texto."""
        
        validated_entities = []
        
        # Crear sets de valores para comparación rápida
        table_values = {e['value'] for e in table_entities}
        text_values = {e.value for e in text_entities}
        
        # Entidades que aparecen en ambos contextos tienen mayor confianza
        for entity in text_entities:
            validated_entity = {
                'value': entity.value,
                'type': entity.type,
                'confidence': entity.confidence,
                'context': entity.context,
                'cross_validated': entity.value in table_values
            }
            
            # Boost de confianza para entidades cross-validadas
            if validated_entity['cross_validated']:
                validated_entity['confidence'] = min(1.0, validated_entity['confidence'] + 0.2)
            
            validated_entities.append(validated_entity)
        
        # Añadir entidades únicas de tablas
        for entity in table_entities:
            if entity['value'] not in text_values:
                validated_entities.append({
                    'value': entity['value'],
                    'type': entity['type'],
                    'confidence': entity['confidence'] * 0.8,  # Menor confianza si no está en texto
                    'context': f"Found only in {entity['source']}",
                    'cross_validated': False
                })
        
        return validated_entities
    
    def _extract_document_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extraer metadatos del documento."""
        
        metadata = {
            'file_path': str(pdf_path),
            'file_name': Path(pdf_path).name,
            'file_size_mb': Path(pdf_path).stat().st_size / (1024 * 1024),
            'extracted_at': datetime.now().isoformat()
        }
        
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            
            # Metadatos del PDF
            pdf_metadata = doc.metadata
            if pdf_metadata:
                metadata.update({
                    'title': pdf_metadata.get('title', ''),
                    'author': pdf_metadata.get('author', ''),
                    'subject': pdf_metadata.get('subject', ''),
                    'creator': pdf_metadata.get('creator', ''),
                    'creation_date': pdf_metadata.get('creationDate', ''),
                    'modification_date': pdf_metadata.get('modDate', '')
                })
            
            metadata['page_count'] = len(doc)
            
            # Intentar extraer fecha y versión del contenido
            first_page_text = doc.load_page(0).get_text()
            date_version_info = self._extract_date_version_from_text(first_page_text)
            metadata.update(date_version_info)
            
            doc.close()
            
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata: {e}")
        
        return metadata
    
    def _extract_date_version_from_text(self, text: str) -> Dict[str, Any]:
        """Extraer fecha y versión del texto del documento."""
        
        import re
        
        date_version_info = {}
        
        # Patrones para fechas
        date_patterns = [
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',  # "15 de marzo de 2023"
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # "15/03/2023"
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # "2023-03-15"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_version_info['document_date_raw'] = match.group(0)
                break
        
        # Patrones para versiones
        version_patterns = [
            r'versión\s+(\d+\.?\d*)',
            r'v\.?\s*(\d+\.?\d*)',
            r'revisión\s+(\d+)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_version_info['document_version'] = match.group(1)
                break
        
        # Detectar si es versión superseded
        superseded_patterns = [
            r'derogad[oa]',
            r'sustituir\w*',
            r'reemplaza\w*',
            r'anulad[oa]'
        ]
        
        for pattern in superseded_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                date_version_info['is_superseded'] = True
                break
        else:
            date_version_info['is_superseded'] = False
        
        return date_version_info
    
    def _calculate_global_confidence(self, table_results: Dict[str, Any], 
                                   entity_results: Dict[str, Any],
                                   cross_validated_entities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcular métricas de confianza global."""
        
        # Confianza de extracción de tablas
        table_confidence = table_results.get('metadata', {}).get('confidence_score', 0.0)
        
        # Confianza promedio de entidades
        entity_confidences = [e.get('confidence', 0.0) for e in cross_validated_entities]
        avg_entity_confidence = sum(entity_confidences) / len(entity_confidences) if entity_confidences else 0.0
        
        # Porcentaje de entidades cross-validadas
        cross_validated_count = sum(1 for e in cross_validated_entities if e.get('cross_validated', False))
        cross_validation_rate = cross_validated_count / len(cross_validated_entities) if cross_validated_entities else 0.0
        
        # Confianza global ponderada
        global_confidence = (
            table_confidence * 0.4 +
            avg_entity_confidence * 0.4 +
            cross_validation_rate * 0.2
        )
        
        return {
            'table_confidence': table_confidence,
            'entity_confidence': avg_entity_confidence,
            'cross_validation_rate': cross_validation_rate,
            'global_confidence': global_confidence
        }
    
    def _should_process_document(self, pdf_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Determinar si un documento debe ser procesado basado en filtros."""
        
        # Verificar filtros de fecha si están configurados
        if self.date_filters['min_date'] or self.date_filters['max_date']:
            # Aquí se implementaría la lógica de filtrado por fecha
            # Por ahora, procesar todos los documentos
            pass
        
        # Verificar si debe excluir documentos superseded
        if self.date_filters['exclude_superseded'] and metadata:
            if metadata.get('is_superseded', False):
                logger.info(f"Skipping superseded document: {Path(pdf_path).name}")
                return False
        
        # Verificar que el archivo existe y es accesible
        if not Path(pdf_path).exists():
            logger.warning(f"File not found: {pdf_path}")
            return False
        
        return True
    
    def _check_cache(self, pdf_path: str) -> Optional[ProcessingResult]:
        """Verificar si existe resultado en cache."""
        
        # Usar hash del archivo como clave de cache
        try:
            import hashlib
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            return self.results_cache.get(file_hash)
            
        except Exception:
            return None
    
    def _cache_result(self, pdf_path: str, result: ProcessingResult):
        """Guardar resultado en cache."""
        
        try:
            import hashlib
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            self.results_cache[file_hash] = result
            
        except Exception as e:
            logger.warning(f"Could not cache result: {e}")
    
    def _create_processing_result(self, pdf_path: str, success: bool, processing_time: float,
                                validated_results: Dict[str, Any], config: ExtractionConfig,
                                errors: List[str], warnings: List[str],
                                document_metadata: Optional[Dict[str, Any]]) -> ProcessingResult:
        """Crear resultado de procesamiento."""
        
        tables = validated_results.get('tables', [])
        money_entities = validated_results.get('money_entities', [])
        numeral_entities = validated_results.get('numeral_entities', [])
        
        # Crear perfil de documento simplificado
        doc_profile = DocumentProfile(
            file_hash="computed",
            file_size_mb=Path(pdf_path).stat().st_size / (1024 * 1024),
            page_count=validated_results.get('document_metadata', {}).get('page_count', 0),
            text_density=1.0,
            image_density=0.1,
            table_indicators=len(tables),
            scan_quality=0.8,
            document_type=validated_results.get('document_metadata', {}).get('document_type', 'legal_norm')
        )
        
        return ProcessingResult(
            document_path=pdf_path,
            success=success,
            processing_time=processing_time,
            tables=tables,
            money_entities=money_entities,
            numeral_entities=numeral_entities,
            document_profile=doc_profile,
            config_used=config,
            extraction_confidence=validated_results.get('confidence_metrics', {}).get('global_confidence', 0.0),
            tables_found=len(tables),
            entities_found=len(money_entities) + len(numeral_entities),
            fallback_methods_used=validated_results.get('fallback_methods_used', []),
            errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _create_skipped_result(self, pdf_path: str, reason: str) -> ProcessingResult:
        """Crear resultado para documento saltado."""
        
        return ProcessingResult(
            document_path=pdf_path,
            success=False,
            processing_time=0.0,
            tables=[],
            money_entities=[],
            numeral_entities=[],
            document_profile=DocumentProfile(
                file_hash="skipped",
                file_size_mb=0,
                page_count=0,
                text_density=0,
                image_density=0,
                table_indicators=0,
                scan_quality=0,
                document_type="skipped"
            ),
            config_used=ExtractionConfig(),
            extraction_confidence=0.0,
            tables_found=0,
            entities_found=0,
            fallback_methods_used=[],
            errors=[f"Document skipped: {reason}"]
        )
    
    def _create_error_result(self, pdf_path: str, processing_time: float, 
                           errors: List[str], warnings: List[str]) -> ProcessingResult:
        """Crear resultado para error de procesamiento."""
        
        return ProcessingResult(
            document_path=pdf_path,
            success=False,
            processing_time=processing_time,
            tables=[],
            money_entities=[],
            numeral_entities=[],
            document_profile=DocumentProfile(
                file_hash="error",
                file_size_mb=0,
                page_count=0,
                text_density=0,
                image_density=0,
                table_indicators=0,
                scan_quality=0,
                document_type="error"
            ),
            config_used=ExtractionConfig(),
            extraction_confidence=0.0,
            tables_found=0,
            entities_found=0,
            fallback_methods_used=[],
            errors=errors,
            warnings=warnings
        )
    
    def _learn_from_results(self, result: ProcessingResult):
        """Aprender de los resultados para mejorar futuras extracciones."""
        
        # Proporcionar feedback al optimizador de configuración
        extraction_results = {
            'metadata': {
                'confidence_score': result.extraction_confidence,
                'extraction_time': result.processing_time,
                'total_tables_found': result.tables_found,
                'fallbacks_used': result.fallback_methods_used
            }
        }
        
        self.config_optimizer.learn_from_feedback(
            result.document_profile,
            result.config_used,
            extraction_results
        )
    
    def _update_global_stats(self, result: ProcessingResult):
        """Actualizar estadísticas globales."""
        
        self.global_stats.total_documents += 1
        
        if result.success:
            self.global_stats.successful_documents += 1
        else:
            self.global_stats.failed_documents += 1
        
        self.global_stats.total_processing_time += result.processing_time
        self.global_stats.total_tables_found += result.tables_found
        self.global_stats.total_entities_found += result.entities_found
        
        # Actualizar tiempo promedio
        self.global_stats.average_processing_time = (
            self.global_stats.total_processing_time / self.global_stats.total_documents
        )
        
        # Actualizar distribución por tipo de documento
        doc_type = result.document_profile.document_type
        self.global_stats.document_types_processed[doc_type] = (
            self.global_stats.document_types_processed.get(doc_type, 0) + 1
        )
    
    def _process_batch_sequential(self, pdf_paths: List[str], 
                                progress_callback: Optional[callable]) -> Dict[str, ProcessingResult]:
        """Procesar lote de forma secuencial."""
        
        results = {}
        
        for i, pdf_path in enumerate(pdf_paths):
            try:
                result = self.process_document(pdf_path)
                results[pdf_path] = result
                
                if progress_callback:
                    progress_callback(i + 1, len(pdf_paths), result)
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                results[pdf_path] = self._create_error_result(pdf_path, 0.0, [str(e)], [])
        
        return results
    
    def _process_batch_parallel(self, pdf_paths: List[str], max_workers: int,
                              progress_callback: Optional[callable]) -> Dict[str, ProcessingResult]:
        """Procesar lote de forma paralela."""
        
        # Por simplicidad, usar procesamiento secuencial por ahora
        # En producción se implementaría con ThreadPoolExecutor o ProcessPoolExecutor
        logger.info(f"Parallel processing not yet implemented, using sequential with max_workers={max_workers}")
        return self._process_batch_sequential(pdf_paths, progress_callback)
    
    def _calculate_batch_stats(self, results: Dict[str, ProcessingResult], 
                             total_time: float) -> BatchProcessingStats:
        """Calcular estadísticas de procesamiento en lote."""
        
        stats = BatchProcessingStats()
        stats.total_documents = len(results)
        stats.total_processing_time = total_time
        
        for result in results.values():
            if result.success:
                stats.successful_documents += 1
            else:
                stats.failed_documents += 1
            
            stats.total_tables_found += result.tables_found
            stats.total_entities_found += result.entities_found
            
            doc_type = result.document_profile.document_type
            stats.document_types_processed[doc_type] = (
                stats.document_types_processed.get(doc_type, 0) + 1
            )
        
        if stats.total_documents > 0:
            stats.average_processing_time = stats.total_processing_time / stats.total_documents
        
        return stats
    
    def _save_batch_results(self, results: Dict[str, ProcessingResult], 
                          stats: BatchProcessingStats):
        """Guardar resultados de procesamiento en lote."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar resultados individuales
        results_file = self.output_dir / f"batch_results_{timestamp}.json"
        
        serializable_results = {}
        for path, result in results.items():
            serializable_results[path] = asdict(result)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Guardar estadísticas de lote
        stats_file = self.output_dir / f"batch_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(stats), f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Batch results saved to {results_file}")
        logger.info(f"Batch stats saved to {stats_file}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generar reporte completo de rendimiento del pipeline."""
        
        return {
            'global_stats': asdict(self.global_stats),
            'table_extractor_performance': self.table_extractor.get_performance_report(),
            'money_detector_performance': self.money_detector.get_performance_report(),
            'config_optimizer_performance': self.config_optimizer.get_optimization_report(),
            'cache_stats': {
                'cached_results': len(self.results_cache),
                'cache_enabled': self.enable_caching
            },
            'learning_stats': {
                'learning_enabled': self.enable_learning,
                'patterns_learned': self.money_detector.performance_stats.get('patterns_learned', 0),
                'optimizations_learned': self.config_optimizer.performance_metrics.get('rules_learned', 0)
            }
        }
    
    def set_date_filters(self, min_date: Optional[datetime] = None, 
                        max_date: Optional[datetime] = None,
                        exclude_superseded: bool = True):
        """Configurar filtros de fecha para procesamiento."""
        
        self.date_filters = {
            'min_date': min_date,
            'max_date': max_date,
            'exclude_superseded': exclude_superseded
        }
        
        logger.info(f"Date filters configured: min={min_date}, max={max_date}, exclude_superseded={exclude_superseded}")
    
    def save_learned_patterns(self, filepath: Optional[str] = None):
        """Guardar todos los patrones aprendidos."""
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"learned_patterns_{timestamp}.json"
        
        self.money_detector.save_learned_patterns(filepath)
        logger.info(f"Learned patterns saved to {filepath}")
    
    def load_learned_patterns(self, filepath: str):
        """Cargar patrones aprendidos previamente."""
        
        self.money_detector.load_learned_patterns(filepath)
        logger.info(f"Learned patterns loaded from {filepath}")
    
    def clear_cache(self):
        """Limpiar cache de resultados."""
        
        self.results_cache.clear()
        self.config_optimizer.clear_cache()
        logger.info("Pipeline cache cleared")
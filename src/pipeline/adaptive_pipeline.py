#!/usr/bin/env python3
"""
Adaptive Pipeline v2 - Pipeline Unificado con Separación Declarativa
====================================================================

Pipeline que combina extracción pura con motor de reglas declarativas
y gestión de diálogos interactivos.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# Importar componentes del sistema
try:
    from ..extractors.generic_table_extractor import GenericTableExtractor, ExtractedDocument
    from ..rules.normative_rules import NormativeRulesEngine, ValidationResult
    from ..dialog.dialog_manager import DialogManager, DialogPrompt, DialogResponse
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Algunos componentes no disponibles: {e}")
    COMPONENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    """Resultado completo del pipeline adaptativo"""
    # Datos de extracción
    extracted_document: Any  # ExtractedDocument
    extraction_confidence: float
    
    # Validación normativa
    validation_result: Any  # ValidationResult
    normative_compliance: bool
    
    # Diálogo interactivo
    dialog_prompt: Optional[Any] = None  # DialogPrompt
    requires_interaction: bool = False
    
    # Metadatos del pipeline
    processing_time: float = 0.0
    pipeline_version: str = "2.0"
    timestamp: datetime = None
    
    # Resultados finales
    final_concepts: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    next_steps: List[str] = None

class AdaptivePipelineV2:
    """
    Pipeline adaptativo que implementa separación completa entre:
    - Extracción de datos (sin lógica de negocio)
    - Motor de reglas declarativas (sin extracción)
    - Gestión de diálogos interactivos
    
    Características:
    - Plug-and-play para cualquier norma
    - Diálogos automáticos para conflictos
    - Validación declarativa completa
    - Exportación de resultados estructurados
    """
    
    def __init__(self, 
                 catalog_path: Optional[str] = None,
                 enable_interactive_dialogs: bool = True,
                 default_location: str = "regiones"):
        
        if not COMPONENTS_AVAILABLE:
            raise ImportError("Componentes del pipeline no disponibles")
        
        # Inicializar componentes
        self.extractor = GenericTableExtractor()
        self.rules_engine = NormativeRulesEngine(catalog_path)
        self.dialog_manager = DialogManager(self.rules_engine)
        
        # Configuración
        self.enable_interactive_dialogs = enable_interactive_dialogs
        self.default_location = default_location
        
        # Estadísticas de pipeline
        self.pipeline_stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'validation_passed': 0,
            'dialogs_required': 0,
            'average_processing_time': 0.0
        }
        
        logger.info(f"AdaptivePipelineV2 inicializado - Diálogos: {enable_interactive_dialogs}")
        logger.info(f"Catálogo cargado: {self.rules_engine.catalog.get('metadata', {}).get('directive', 'N/A')}")
    
    def process_document(self, pdf_path: str, 
                        location: Optional[str] = None,
                        user_context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Procesar documento completo con separación declarativa.
        
        Args:
            pdf_path: Ruta al documento PDF
            location: "lima" o "regiones" (opcional)
            user_context: Contexto adicional del usuario
            
        Returns:
            PipelineResult con extracción, validación y diálogos
        """
        start_time = time.time()
        
        if location is None:
            location = self.default_location
        
        logger.info(f"🚀 Procesando documento: {Path(pdf_path).name} para {location}")
        
        try:
            # FASE 1: EXTRACCIÓN PURA (sin lógica normativa)
            logger.info("📊 FASE 1: Extracción de datos...")
            extracted_document = self.extractor.extract(pdf_path)
            
            if extracted_document.extraction_confidence < 0.3:
                logger.warning(f"⚠️ Baja confianza de extracción: {extracted_document.extraction_confidence:.2f}")
            
            # FASE 2: ESTRUCTURACIÓN PARA VALIDACIÓN
            logger.info("🔧 FASE 2: Estructurando conceptos...")
            structured_concepts = self._structure_concepts_for_validation(extracted_document)
            
            if not structured_concepts:
                logger.warning("⚠️ No se encontraron conceptos válidos para validar")
                return self._create_empty_result(extracted_document, start_time, "No concepts found")
            
            # FASE 3: VALIDACIÓN NORMATIVA DECLARATIVA  
            logger.info("⚖️ FASE 3: Validación normativa...")
            validation_result = self.rules_engine.evaluate_concepts(structured_concepts, location)
            
            # FASE 4: GESTIÓN DE DIÁLOGOS (si es necesaria)
            dialog_prompt = None
            if not validation_result.valid and self.enable_interactive_dialogs:
                logger.info("💬 FASE 4: Generando diálogo interactivo...")
                dialog_prompt = self.dialog_manager.create_dialog_for_validation(
                    validation_result, structured_concepts
                )
            
            # FASE 5: RESULTADO FINAL
            processing_time = time.time() - start_time
            result = self._create_pipeline_result(
                extracted_document, validation_result, dialog_prompt, 
                structured_concepts, processing_time
            )
            
            # Actualizar estadísticas
            self._update_pipeline_stats(result, processing_time)
            
            logger.info(f"✅ Pipeline completado en {processing_time:.2f}s - Válido: {validation_result.valid}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error en pipeline: {e}")
            return self._create_error_result(pdf_path, str(e), processing_time)
    
    def _structure_concepts_for_validation(self, extracted_document: ExtractedDocument) -> List[Dict[str, Any]]:
        """Estructurar filas extraídas en formato para validación normativa"""
        
        structured_concepts = []
        
        for row in extracted_document.structured_rows:
            if row.numeral and row.tarifa:  # Mínimo requerido para validación
                concept = {
                    'numeral': row.numeral,
                    'concepto': row.concepto or "Concepto extraído",
                    'amount': row.tarifa,
                    'ubicacion': row.ubicacion,
                    'unidad': row.unidad,
                    'confidence': row.confidence,
                    'source': f"Table {row.source_table}, Page {row.page_number}",
                    'raw_data': row.raw_data
                }
                structured_concepts.append(concept)
        
        # Enriquecer con entidades extraídas si no hay filas estructuradas
        if not structured_concepts and extracted_document.raw_entities:
            structured_concepts = self._create_concepts_from_entities(extracted_document)
        
        logger.info(f"📋 Estructurados {len(structured_concepts)} conceptos para validación")
        
        return structured_concepts
    
    def _create_concepts_from_entities(self, extracted_document: ExtractedDocument) -> List[Dict[str, Any]]:
        """Crear conceptos básicos desde entidades extraídas"""
        
        concepts = []
        amounts = extracted_document.raw_entities.get('amounts', [])
        numerals = extracted_document.raw_entities.get('numerals', [])
        
        # Intentar emparejar numerales con montos
        for i, numeral in enumerate(numerals):
            amount_value = None
            
            # Buscar monto correspondiente
            if i < len(amounts):
                try:
                    amount_text = amounts[i].replace(',', '').replace('S/', '').strip()
                    amount_value = float(amount_text)
                except (ValueError, AttributeError):
                    continue
            
            if amount_value:
                concepts.append({
                    'numeral': numeral,
                    'concepto': f"Concepto extraído automáticamente",
                    'amount': amount_value,
                    'confidence': 0.6,  # Confianza reducida por emparejamiento automático
                    'source': "entity_extraction"
                })
        
        return concepts
    
    def _create_pipeline_result(self, extracted_document: ExtractedDocument,
                              validation_result: ValidationResult,
                              dialog_prompt: Optional[DialogPrompt],
                              structured_concepts: List[Dict[str, Any]],
                              processing_time: float) -> PipelineResult:
        """Crear resultado completo del pipeline"""
        
        # Determinar conceptos finales
        final_concepts = structured_concepts
        if validation_result.valid:
            final_concepts = self._enrich_valid_concepts(structured_concepts, validation_result)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(validation_result, dialog_prompt)
        
        # Determinar próximos pasos
        next_steps = self._determine_next_steps(validation_result, dialog_prompt)
        
        return PipelineResult(
            extracted_document=extracted_document,
            extraction_confidence=extracted_document.extraction_confidence,
            validation_result=validation_result,
            normative_compliance=validation_result.valid,
            dialog_prompt=dialog_prompt,
            requires_interaction=dialog_prompt is not None,
            processing_time=processing_time,
            timestamp=datetime.now(),
            final_concepts=final_concepts,
            recommendations=recommendations,
            next_steps=next_steps
        )
    
    def _create_empty_result(self, extracted_document: ExtractedDocument, 
                           start_time: float, reason: str) -> PipelineResult:
        """Crear resultado vacío por falta de datos"""
        
        processing_time = time.time() - start_time
        
        # Crear ValidationResult vacío
        empty_validation = ValidationResult(
            valid=False,
            total_amount=0.0,
            daily_limit=30.0,
            location=self.default_location,
            concepts_used=[],
            violations=[f"No se pudieron extraer conceptos válidos: {reason}"],
            warnings=[],
            suggestions=["Verificar calidad del documento", "Intentar con otro método de extracción"],
            alternative_distributions=[]
        )
        
        return PipelineResult(
            extracted_document=extracted_document,
            extraction_confidence=extracted_document.extraction_confidence,
            validation_result=empty_validation,
            normative_compliance=False,
            requires_interaction=False,
            processing_time=processing_time,
            timestamp=datetime.now(),
            final_concepts=[],
            recommendations=["Mejorar calidad de extracción", "Revisar documento manualmente"],
            next_steps=["manual_review", "improve_extraction"]
        )
    
    def _create_error_result(self, pdf_path: str, error_message: str, 
                           processing_time: float) -> PipelineResult:
        """Crear resultado de error"""
        
        # Crear ExtractedDocument vacío
        empty_document = ExtractedDocument(
            file_path=pdf_path,
            tables=[],
            structured_rows=[],
            raw_entities={},
            metadata={'error': error_message},
            extraction_confidence=0.0
        )
        
        # Crear ValidationResult de error
        error_validation = ValidationResult(
            valid=False,
            total_amount=0.0,
            daily_limit=0.0,
            location=self.default_location,
            concepts_used=[],
            violations=[f"Error de procesamiento: {error_message}"],
            warnings=[],
            suggestions=["Verificar archivo PDF", "Contactar soporte técnico"],
            alternative_distributions=[]
        )
        
        return PipelineResult(
            extracted_document=empty_document,
            extraction_confidence=0.0,
            validation_result=error_validation,
            normative_compliance=False,
            requires_interaction=False,
            processing_time=processing_time,
            timestamp=datetime.now(),
            final_concepts=[],
            recommendations=["Revisar error", "Intentar nuevamente"],
            next_steps=["error_handling", "retry_processing"]
        )
    
    def _enrich_valid_concepts(self, concepts: List[Dict[str, Any]], 
                             validation_result: ValidationResult) -> List[Dict[str, Any]]:
        """Enriquecer conceptos válidos con información normativa"""
        
        enriched_concepts = []
        
        for concept in concepts:
            numeral = concept.get('numeral')
            
            # Obtener definición completa del catálogo
            definition = self.rules_engine.get_concept_definition(numeral)
            
            enriched_concept = concept.copy()
            if definition:
                enriched_concept.update({
                    'official_concepto': definition.get('concepto'),
                    'scope': definition.get('scope'),
                    'unidad_oficial': definition.get('unidad'),
                    'observaciones': definition.get('observaciones', []),
                    'validated': True
                })
            
            enriched_concepts.append(enriched_concept)
        
        return enriched_concepts
    
    def _generate_recommendations(self, validation_result: ValidationResult, 
                                dialog_prompt: Optional[DialogPrompt]) -> List[str]:
        """Generar recomendaciones basadas en resultados"""
        
        recommendations = []
        
        if validation_result.valid:
            recommendations.append("✅ Todos los conceptos cumplen con la normativa")
            recommendations.append("Proceder con la solicitud de viáticos")
        else:
            recommendations.extend(validation_result.suggestions)
            
            if dialog_prompt:
                recommendations.append("💬 Se requiere clarificación interactiva")
                recommendations.append("Revisar opciones de diálogo propuestas")
        
        # Recomendaciones de optimización
        if validation_result.total_amount > 0:
            efficiency = validation_result.total_amount / validation_result.daily_limit
            if efficiency > 0.9:
                recommendations.append("⚠️ Solicitud cercana al límite diario")
            elif efficiency < 0.5:
                recommendations.append("💡 Oportunidad de optimizar solicitud")
        
        return recommendations
    
    def _determine_next_steps(self, validation_result: ValidationResult, 
                            dialog_prompt: Optional[DialogPrompt]) -> List[str]:
        """Determinar próximos pasos del proceso"""
        
        next_steps = []
        
        if validation_result.valid:
            next_steps = ["generate_viaticos_form", "submit_request"]
        else:
            if dialog_prompt:
                next_steps = ["await_user_response", "process_dialog_choice"]
            else:
                next_steps = ["manual_review", "adjust_concepts"]
        
        # Pasos adicionales según tipo de problema
        if any('excede límite' in v for v in validation_result.violations):
            next_steps.append("consider_multi_day_distribution")
        
        if any('mutuamente excluyentes' in v for v in validation_result.violations):
            next_steps.append("resolve_concept_conflicts")
        
        return next_steps
    
    def _update_pipeline_stats(self, result: PipelineResult, processing_time: float):
        """Actualizar estadísticas del pipeline"""
        
        self.pipeline_stats['total_processed'] += 1
        
        if result.extraction_confidence > 0.5:
            self.pipeline_stats['successful_extractions'] += 1
        
        if result.normative_compliance:
            self.pipeline_stats['validation_passed'] += 1
        
        if result.requires_interaction:
            self.pipeline_stats['dialogs_required'] += 1
        
        # Actualizar tiempo promedio
        total_time = (self.pipeline_stats['average_processing_time'] * 
                     (self.pipeline_stats['total_processed'] - 1) + processing_time)
        self.pipeline_stats['average_processing_time'] = total_time / self.pipeline_stats['total_processed']
    
    def process_dialog_response(self, dialog_prompt: DialogPrompt, 
                              user_response: DialogResponse) -> Dict[str, Any]:
        """Procesar respuesta del usuario a diálogo interactivo"""
        
        logger.info(f"💬 Procesando respuesta de diálogo: {user_response.selected_option_id}")
        
        try:
            result = self.dialog_manager.process_dialog_response(dialog_prompt, user_response)
            
            # Si el resultado requiere revalidación
            if 'revalidate' in result.get('next_steps', []):
                # Aquí se podría reiniciar el pipeline con nuevos parámetros
                result['requires_pipeline_restart'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta de diálogo: {e}")
            return {
                'success': False,
                'error': str(e),
                'next_steps': ['manual_intervention']
            }
    
    def export_pipeline_result(self, result: PipelineResult, output_path: str):
        """Exportar resultado completo del pipeline"""
        
        export_data = {
            'metadata': {
                'timestamp': result.timestamp.isoformat() if result.timestamp else datetime.now().isoformat(),
                'pipeline_version': result.pipeline_version,
                'processing_time': result.processing_time
            },
            'extraction': {
                'confidence': result.extraction_confidence,
                'tables_found': len(result.extracted_document.tables),
                'structured_rows': len(result.extracted_document.structured_rows),
                'file_path': result.extracted_document.file_path
            },
            'validation': {
                'normative_compliance': result.normative_compliance,
                'total_amount': result.validation_result.total_amount,
                'daily_limit': result.validation_result.daily_limit,
                'location': result.validation_result.location,
                'violations': result.validation_result.violations,
                'warnings': result.validation_result.warnings
            },
            'interaction': {
                'requires_dialog': result.requires_interaction,
                'dialog_type': result.dialog_prompt.dialog_type.value if result.dialog_prompt else None
            },
            'final_results': {
                'concepts': result.final_concepts,
                'recommendations': result.recommendations,
                'next_steps': result.next_steps
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Resultado del pipeline exportado a: {output_path}")
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado del pipeline"""
        
        return {
            'pipeline_version': '2.0',
            'components_status': {
                'extractor': 'active',
                'rules_engine': 'active',
                'dialog_manager': 'active' if self.enable_interactive_dialogs else 'disabled'
            },
            'configuration': {
                'default_location': self.default_location,
                'interactive_dialogs': self.enable_interactive_dialogs
            },
            'statistics': self.pipeline_stats,
            'catalog_info': {
                'version': self.rules_engine.catalog.get('metadata', {}).get('version'),
                'directive': self.rules_engine.catalog.get('metadata', {}).get('directive'),
                'numerals_available': len(self.rules_engine.catalog.get('numerals', {}))
            }
        }

# Función de conveniencia para uso directo
def process_pdf_with_normative_validation(pdf_path: str, location: str = "regiones") -> PipelineResult:
    """Función de conveniencia para procesar PDF con validación normativa completa"""
    pipeline = AdaptivePipelineV2()
    return pipeline.process_document(pdf_path, location)
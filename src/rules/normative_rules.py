#!/usr/bin/env python3
"""
Normative Rules Engine - Motor de Reglas Declarativas
====================================================

Motor de reglas que carga el catálogo normativo y evalúa validaciones
sin mezclarse con la extracción de datos.
"""

import yaml
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado de validación normativa"""
    valid: bool
    total_amount: float
    daily_limit: float
    location: str
    concepts_used: List[str]
    violations: List[str]
    warnings: List[str]
    suggestions: List[str]
    alternative_distributions: List[Dict[str, Any]]

@dataclass
class ConceptEvaluation:
    """Evaluación de un concepto individual"""
    numeral: str
    concepto: str
    amount: float
    valid: bool
    location: str
    violation_reason: Optional[str] = None
    confidence: float = 1.0

class NormativeRulesEngine:
    """
    Motor de reglas declarativas que evalúa conceptos contra catálogo normativo.
    
    Principios:
    - Carga catálogo YAML declarativo
    - NO extrae datos - solo evalúa
    - Devuelve validaciones estructuradas
    - Genera sugerencias automáticas
    """
    
    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            catalog_path = Path(__file__).parent / "normative_catalog.yaml"
        
        self.catalog_path = Path(catalog_path)
        self.catalog = self._load_catalog()
        self.validation_cache = {}
        
        logger.info(f"NormativeRulesEngine inicializado con catálogo: {self.catalog_path}")
        logger.info(f"Numerales cargados: {list(self.catalog.get('numerals', {}).keys())}")
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Cargar catálogo normativo desde YAML"""
        
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                catalog = yaml.safe_load(f)
            
            # Validar estructura básica del catálogo
            required_sections = ['metadata', 'global_limits', 'numerals', 'validation_rules']
            missing_sections = [s for s in required_sections if s not in catalog]
            
            if missing_sections:
                raise ValueError(f"Catálogo incompleto. Faltan secciones: {missing_sections}")
            
            logger.info(f"Catálogo cargado: {catalog['metadata']['directive']}")
            return catalog
            
        except FileNotFoundError:
            logger.error(f"❌ Catálogo no encontrado: {self.catalog_path}")
            raise FileNotFoundError(f"No existe definición normativa en {self.catalog_path}")
        
        except Exception as e:
            logger.error(f"❌ Error cargando catálogo: {e}")
            raise ValueError(f"Catálogo normativo inválido: {e}")
    
    def evaluate_concepts(self, extracted_concepts: List[Dict[str, Any]], 
                         location: str = "regiones") -> ValidationResult:
        """
        Evaluar lista de conceptos extraídos contra reglas normativas.
        
        Args:
            extracted_concepts: Lista de conceptos con {numeral, amount, ...}
            location: "lima" o "regiones"
            
        Returns:
            ValidationResult con validaciones y sugerencias
        """
        logger.info(f"🔍 Evaluando {len(extracted_concepts)} conceptos para {location}")
        
        # 1. Validar que todos los numerales existen en el catálogo
        self._validate_numerals_exist(extracted_concepts)
        
        # 2. Evaluar cada concepto individualmente
        concept_evaluations = []
        for concept in extracted_concepts:
            evaluation = self._evaluate_single_concept(concept, location)
            concept_evaluations.append(evaluation)
        
        # 3. Evaluar reglas globales
        global_validation = self._evaluate_global_rules(concept_evaluations, location)
        
        # 4. Generar sugerencias si hay violaciones
        suggestions = self._generate_suggestions(concept_evaluations, global_validation, location)
        
        # 5. Crear resultado final
        result = ValidationResult(
            valid=global_validation['valid'],
            total_amount=global_validation['total_amount'],
            daily_limit=global_validation['daily_limit'],
            location=location,
            concepts_used=[eval.numeral for eval in concept_evaluations],
            violations=global_validation['violations'],
            warnings=global_validation['warnings'],
            suggestions=suggestions,
            alternative_distributions=self._generate_alternatives(concept_evaluations, location)
        )
        
        logger.info(f"✅ Evaluación completada: válido={result.valid}, total=S/{result.total_amount}")
        
        return result
    
    def _validate_numerals_exist(self, extracted_concepts: List[Dict[str, Any]]):
        """Validar que todos los numerales existen en el catálogo"""
        
        catalog_numerals = set(self.catalog['numerals'].keys())
        
        for concept in extracted_concepts:
            numeral = str(concept.get('numeral', '')).strip()
            if numeral and numeral not in catalog_numerals:
                error_msg = self.catalog['error_messages']['unknown_numeral'].format(numeral=numeral)
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
    
    def _evaluate_single_concept(self, concept: Dict[str, Any], location: str) -> ConceptEvaluation:
        """Evaluar un concepto individual"""
        
        numeral = str(concept.get('numeral', '')).strip()
        amount = float(concept.get('amount', 0))
        
        # Obtener definición del catálogo
        numeral_def = self.catalog['numerals'].get(numeral)
        if not numeral_def:
            return ConceptEvaluation(
                numeral=numeral,
                concepto="Desconocido",
                amount=amount,
                valid=False,
                location=location,
                violation_reason=f"Numeral {numeral} no definido en catálogo"
            )
        
        # Verificar si procede en la ubicación
        location_config = numeral_def['ubicacion'].get(location, {})
        if not location_config.get('procede', False):
            return ConceptEvaluation(
                numeral=numeral,
                concepto=numeral_def['concepto'],
                amount=amount,
                valid=False,
                location=location,
                violation_reason=f"No procede en {location}: {location_config.get('justificacion', 'Sin justificación')}"
            )
        
        # Verificar monto correcto
        expected_amount = location_config.get('tarifa', 0)
        if amount != expected_amount:
            return ConceptEvaluation(
                numeral=numeral,
                concepto=numeral_def['concepto'],
                amount=amount,
                valid=False,
                location=location,
                violation_reason=f"Monto incorrecto: esperado S/{expected_amount}, recibido S/{amount}"
            )
        
        # Si llegamos aquí, el concepto individual es válido
        return ConceptEvaluation(
            numeral=numeral,
            concepto=numeral_def['concepto'],
            amount=amount,
            valid=True,
            location=location
        )
    
    def _evaluate_global_rules(self, evaluations: List[ConceptEvaluation], 
                             location: str) -> Dict[str, Any]:
        """Evaluar reglas globales (límites diarios, exclusiones mutuas, etc.)"""
        
        violations = []
        warnings = []
        
        # Filtrar solo conceptos válidos para reglas globales
        valid_concepts = [e for e in evaluations if e.valid]
        total_amount = sum(e.amount for e in valid_concepts)
        
        # Obtener límite diario
        global_limits = self.catalog['global_limits']
        daily_limit = global_limits.get(location, {}).get('daily_limit', 0)
        
        # Regla 1: Límite diario global
        if total_amount > daily_limit:
            violations.append(f"Total S/{total_amount} excede límite diario S/{daily_limit}")
        
        # Regla 2: Exclusiones mutuas
        self._check_mutual_exclusions(valid_concepts, violations, warnings)
        
        # Regla 3: Límites por concepto
        self._check_concept_limits(valid_concepts, violations, warnings, location)
        
        # Agregar violaciones de conceptos individuales
        for eval in evaluations:
            if not eval.valid:
                violations.append(f"{eval.numeral}: {eval.violation_reason}")
        
        return {
            'valid': len(violations) == 0,
            'total_amount': total_amount,
            'daily_limit': daily_limit,
            'violations': violations,
            'warnings': warnings
        }
    
    def _check_mutual_exclusions(self, valid_concepts: List[ConceptEvaluation], 
                                violations: List[str], warnings: List[str]):
        """Verificar exclusiones mutuas entre conceptos"""
        
        used_numerals = {concept.numeral for concept in valid_concepts}
        
        # Verificar exclusiones definidas en el catálogo
        mutual_exclusions = self.catalog['validation_rules'].get('mutual_exclusions', [])
        
        for exclusion_group in mutual_exclusions:
            group_concepts = set(exclusion_group['group'])
            exclusions = set(exclusion_group.get('exclusions', []))
            
            # Si usamos conceptos del grupo y también de las exclusiones
            if used_numerals & group_concepts and used_numerals & exclusions:
                group_used = list(used_numerals & group_concepts)
                exclusions_used = list(used_numerals & exclusions)
                violations.append(
                    f"Conceptos mutuamente excluyentes: {group_used} no puede usarse con {exclusions_used}"
                )
    
    def _check_concept_limits(self, valid_concepts: List[ConceptEvaluation], 
                            violations: List[str], warnings: List[str], location: str):
        """Verificar límites específicos por concepto"""
        
        # Agrupar por numeral para verificar repeticiones
        concept_counts = {}
        for concept in valid_concepts:
            concept_counts[concept.numeral] = concept_counts.get(concept.numeral, 0) + 1
        
        # Verificar límites de servicios por día
        same_day_rules = self.catalog['validation_rules'].get('same_day_services', {})
        max_per_day = same_day_rules.get('max_per_day', 999)
        applies_to = same_day_rules.get('applies_to', [])
        
        for numeral, count in concept_counts.items():
            if numeral in applies_to and count > max_per_day:
                warnings.append(f"Concepto {numeral} repetido {count} veces (máximo recomendado: {max_per_day})")
    
    def _generate_suggestions(self, evaluations: List[ConceptEvaluation], 
                            global_validation: Dict[str, Any], location: str) -> List[str]:
        """Generar sugerencias automáticas basadas en violaciones"""
        
        suggestions = []
        
        if not global_validation['valid']:
            # Sugerencias por exceso de límite diario
            if global_validation['total_amount'] > global_validation['daily_limit']:
                excess = global_validation['total_amount'] - global_validation['daily_limit']
                
                auto_suggestions = self.catalog.get('auto_suggestions', {}).get('when_limit_exceeded', [])
                for suggestion_template in auto_suggestions:
                    suggestion = suggestion_template.format(
                        suggested_days=2,  # Simplificado
                        reduction_needed=excess,
                        highest_amount_concept=self._get_highest_amount_concept(evaluations)
                    )
                    suggestions.append(suggestion)
            
            # Sugerencias por conflictos de conceptos
            if any('mutuamente excluyentes' in v for v in global_validation['violations']):
                conflict_suggestions = self.catalog.get('auto_suggestions', {}).get('when_concepts_conflict', [])
                suggestions.extend(conflict_suggestions)
        
        # Sugerencias de optimización general
        optimization_hints = self.catalog.get('auto_suggestions', {}).get('optimization_hints', [])
        if len(evaluations) > 3:  # Muchos conceptos
            suggestions.extend(optimization_hints)
        
        return suggestions
    
    def _get_highest_amount_concept(self, evaluations: List[ConceptEvaluation]) -> str:
        """Obtener el concepto con mayor monto"""
        
        if not evaluations:
            return "N/A"
        
        highest = max(evaluations, key=lambda e: e.amount)
        return f"{highest.numeral} (S/{highest.amount})"
    
    def _generate_alternatives(self, evaluations: List[ConceptEvaluation], 
                             location: str) -> List[Dict[str, Any]]:
        """Generar distribuciones alternativas automáticamente"""
        
        alternatives = []
        
        total_amount = sum(e.amount for e in evaluations if e.valid)
        daily_limit = self.catalog['global_limits'].get(location, {}).get('daily_limit', 0)
        
        if total_amount > daily_limit:
            # Alternativa 1: Distribuir en 2 días
            day1_concepts = evaluations[:len(evaluations)//2]
            day2_concepts = evaluations[len(evaluations)//2:]
            
            alternatives.append({
                'type': 'distribute_days',
                'description': 'Distribuir en 2 días',
                'distribution': {
                    'day_1': {
                        'concepts': [asdict(c) for c in day1_concepts],
                        'total': sum(c.amount for c in day1_concepts if c.valid)
                    },
                    'day_2': {
                        'concepts': [asdict(c) for c in day2_concepts],
                        'total': sum(c.amount for c in day2_concepts if c.valid)
                    }
                }
            })
            
            # Alternativa 2: Usar movilidad local general
            if any(e.numeral in ['8.4.17.1', '8.4.17.2'] for e in evaluations):
                alternatives.append({
                    'type': 'use_general_mobility',
                    'description': 'Usar movilidad local general (8.4.17.3)',
                    'replacement': {
                        'numeral': '8.4.17.3',
                        'concepto': 'Movilidad local para el desarrollo de actividades oficiales',
                        'amount': daily_limit,
                        'covers': [e.numeral for e in evaluations if e.numeral.startswith('8.4.17')]
                    }
                })
        
        return alternatives
    
    def get_concept_definition(self, numeral: str) -> Optional[Dict[str, Any]]:
        """Obtener definición completa de un numeral"""
        
        return self.catalog['numerals'].get(str(numeral))
    
    def get_dialog_prompt(self, violation_type: str, **kwargs) -> Dict[str, Any]:
        """Obtener prompt de diálogo para una violación específica"""
        
        dialog_prompts = self.catalog.get('dialog_prompts', {})
        prompt_template = dialog_prompts.get(violation_type)
        
        if not prompt_template:
            return {
                'message': f"Violación detectada: {violation_type}",
                'options': [
                    {'id': 'continue', 'text': 'Continuar con validación', 'action': 'ignore_violation'}
                ]
            }
        
        # Formatear mensaje con parámetros
        formatted_message = prompt_template['message'].format(**kwargs)
        
        return {
            'message': formatted_message,
            'options': prompt_template.get('options', [])
        }
    
    def validate_catalog_integrity(self) -> Dict[str, Any]:
        """Validar integridad del catálogo normativo"""
        
        issues = []
        warnings = []
        
        # Verificar que todos los numerales tienen estructura completa
        for numeral, definition in self.catalog['numerals'].items():
            required_fields = ['concepto', 'scope', 'ubicacion', 'unidad']
            missing_fields = [f for f in required_fields if f not in definition]
            
            if missing_fields:
                issues.append(f"Numeral {numeral}: faltan campos {missing_fields}")
            
            # Verificar que ubicaciones tienen configuración completa
            for location in ['lima', 'regiones']:
                location_config = definition.get('ubicacion', {}).get(location)
                if location_config and 'procede' in location_config and location_config['procede']:
                    if 'tarifa' not in location_config:
                        issues.append(f"Numeral {numeral}: falta tarifa para {location}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'numerals_count': len(self.catalog['numerals']),
            'catalog_version': self.catalog.get('metadata', {}).get('version', 'unknown')
        }
    
    def export_validation_report(self, result: ValidationResult, output_path: str):
        """Exportar reporte de validación detallado"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_summary': asdict(result),
            'catalog_info': {
                'version': self.catalog.get('metadata', {}).get('version'),
                'directive': self.catalog.get('metadata', {}).get('directive'),
                'numerals_available': list(self.catalog['numerals'].keys())
            },
            'detailed_analysis': {
                'concepts_breakdown': result.concepts_used,
                'location_analysis': result.location,
                'financial_summary': {
                    'total_requested': result.total_amount,
                    'daily_limit': result.daily_limit,
                    'compliance_percentage': (result.total_amount / result.daily_limit * 100) if result.daily_limit > 0 else 0
                }
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Reporte de validación guardado en: {output_path}")

# Función de conveniencia
def validate_concepts(concepts: List[Dict[str, Any]], location: str = "regiones") -> ValidationResult:
    """Función de conveniencia para validar conceptos"""
    engine = NormativeRulesEngine()
    return engine.evaluate_concepts(concepts, location)
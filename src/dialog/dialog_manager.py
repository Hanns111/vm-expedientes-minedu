#!/usr/bin/env python3
"""
Dialog Manager - Gestión de Ambigüedades y Clarificaciones
===========================================================

Gestiona diálogos interactivos cuando hay conflictos o ambigüedades
en la validación normativa.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class DialogType(Enum):
    """Tipos de diálogo interactivo"""
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    CONCEPT_CONFLICT = "concept_conflict"
    LOCATION_MISMATCH = "location_mismatch"
    AMOUNT_MISMATCH = "amount_mismatch"
    CLARIFICATION_NEEDED = "clarification_needed"

@dataclass
class DialogOption:
    """Opción de diálogo interactivo"""
    id: str
    text: str
    action: str
    parameters: Dict[str, Any] = None

@dataclass
class DialogPrompt:
    """Prompt de diálogo completo"""
    dialog_type: DialogType
    message: str
    context: Dict[str, Any]
    options: List[DialogOption]
    default_option: Optional[str] = None
    timeout_seconds: int = 60

@dataclass
class DialogResponse:
    """Respuesta del usuario al diálogo"""
    selected_option_id: str
    additional_data: Dict[str, Any] = None
    timestamp: datetime = None

class DialogManager:
    """
    Gestor de diálogos interactivos para resolver ambigüedades.
    
    Características:
    - Detecta automáticamente conflictos que requieren clarificación
    - Genera prompts contextuales
    - Procesa respuestas del usuario
    - Sugiere soluciones automáticas
    """
    
    def __init__(self, normative_engine=None):
        self.normative_engine = normative_engine
        self.dialog_history: List[DialogPrompt] = []
        self.response_handlers = {
            'distribute_days': self._handle_distribute_days,
            'reduce_amounts': self._handle_reduce_amounts,
            'specify_location': self._handle_specify_location,
            'use_general_mobility': self._handle_use_general_mobility,
            'ignore_violation': self._handle_ignore_violation,
            'detailed_breakdown': self._handle_detailed_breakdown
        }
        
        logger.info("DialogManager inicializado para gestión de ambigüedades")
    
    def create_dialog_for_validation(self, validation_result, extracted_concepts: List[Dict[str, Any]]) -> Optional[DialogPrompt]:
        """
        Crear diálogo apropiado basado en resultado de validación.
        
        Returns:
            DialogPrompt si se necesita clarificación, None si todo está correcto
        """
        
        if validation_result.valid:
            return None  # No se necesita diálogo
        
        # Analizar tipo de violación principal
        primary_violation = self._identify_primary_violation(validation_result)
        
        if primary_violation == DialogType.DAILY_LIMIT_EXCEEDED:
            return self._create_daily_limit_dialog(validation_result, extracted_concepts)
        
        elif primary_violation == DialogType.CONCEPT_CONFLICT:
            return self._create_concept_conflict_dialog(validation_result, extracted_concepts)
        
        elif primary_violation == DialogType.LOCATION_MISMATCH:
            return self._create_location_mismatch_dialog(validation_result, extracted_concepts)
        
        else:
            return self._create_generic_clarification_dialog(validation_result, extracted_concepts)
    
    def _identify_primary_violation(self, validation_result) -> DialogType:
        """Identificar el tipo principal de violación"""
        
        violations = validation_result.violations
        
        # Priorizar por tipo de problema
        if any('excede límite diario' in v for v in violations):
            return DialogType.DAILY_LIMIT_EXCEEDED
        
        elif any('mutuamente excluyentes' in v for v in violations):
            return DialogType.CONCEPT_CONFLICT
        
        elif any('ubicación' in v.lower() for v in violations):
            return DialogType.LOCATION_MISMATCH
        
        else:
            return DialogType.CLARIFICATION_NEEDED
    
    def _create_daily_limit_dialog(self, validation_result, extracted_concepts: List[Dict[str, Any]]) -> DialogPrompt:
        """Crear diálogo para exceso de límite diario"""
        
        excess_amount = validation_result.total_amount - validation_result.daily_limit
        
        message = f"""🚨 LÍMITE DIARIO EXCEDIDO
        
El total solicitado S/ {validation_result.total_amount:.2f} excede el límite diario para {validation_result.location} (S/ {validation_result.daily_limit:.2f}).

Exceso: S/ {excess_amount:.2f}

Conceptos incluidos:
{self._format_concepts_list(extracted_concepts)}

¿Cómo desea proceder?"""
        
        options = [
            DialogOption(
                id="distribute_days",
                text=f"Distribuir servicios en varios días (recomendado)",
                action="distribute_days",
                parameters={"excess_amount": excess_amount}
            ),
            DialogOption(
                id="reduce_amounts",
                text=f"Reducir montos para cumplir límite (S/ {excess_amount:.2f} menos)",
                action="reduce_amounts",
                parameters={"reduction_needed": excess_amount}
            ),
            DialogOption(
                id="use_general_mobility", 
                text="Usar movilidad local general (8.4.17.3) que incluye todos los traslados",
                action="use_general_mobility",
                parameters={"daily_limit": validation_result.daily_limit}
            ),
            DialogOption(
                id="detailed_breakdown",
                text="Mostrar desglose detallado y alternativas",
                action="detailed_breakdown"
            )
        ]
        
        return DialogPrompt(
            dialog_type=DialogType.DAILY_LIMIT_EXCEEDED,
            message=message,
            context={
                "total_amount": validation_result.total_amount,
                "daily_limit": validation_result.daily_limit,
                "excess": excess_amount,
                "location": validation_result.location,
                "concepts": extracted_concepts
            },
            options=options,
            default_option="distribute_days"
        )
    
    def _create_concept_conflict_dialog(self, validation_result, extracted_concepts: List[Dict[str, Any]]) -> DialogPrompt:
        """Crear diálogo para conflictos entre conceptos"""
        
        # Identificar conceptos conflictivos
        conflict_info = self._analyze_concept_conflicts(validation_result.violations)
        
        message = f"""⚠️ CONFLICTO ENTRE CONCEPTOS
        
{conflict_info['description']}

Conceptos en conflicto:
{conflict_info['conflicting_concepts']}

Los conceptos mutuamente excluyentes no pueden usarse juntos en la misma solicitud.

¿Cómo desea resolver el conflicto?"""
        
        options = [
            DialogOption(
                id="use_general_mobility",
                text="Usar movilidad local general (recomendado)",
                action="use_general_mobility"
            ),
            DialogOption(
                id="separate_days",
                text="Separar conceptos en días diferentes",
                action="distribute_days"
            ),
            DialogOption(
                id="select_priority",
                text="Seleccionar solo los conceptos de mayor prioridad",
                action="reduce_amounts"
            )
        ]
        
        return DialogPrompt(
            dialog_type=DialogType.CONCEPT_CONFLICT,
            message=message,
            context={
                "conflicts": conflict_info,
                "concepts": extracted_concepts
            },
            options=options,
            default_option="use_general_mobility"
        )
    
    def _create_location_mismatch_dialog(self, validation_result, extracted_concepts: List[Dict[str, Any]]) -> DialogPrompt:
        """Crear diálogo para inconsistencias de ubicación"""
        
        message = f"""📍 INCONSISTENCIA DE UBICACIÓN
        
Los conceptos solicitados corresponden a ubicaciones diferentes o hay inconsistencias.

Ubicación actual: {validation_result.location}

Algunos conceptos podrían no aplicar para esta ubicación.

¿Desea especificar la ubicación correcta?"""
        
        options = [
            DialogOption(
                id="specify_lima",
                text="Especificar Lima como ubicación principal",
                action="specify_location",
                parameters={"location": "lima"}
            ),
            DialogOption(
                id="specify_regiones", 
                text="Especificar Regiones como ubicación principal",
                action="specify_location",
                parameters={"location": "regiones"}
            ),
            DialogOption(
                id="split_locations",
                text="Dividir solicitud por ubicaciones",
                action="detailed_breakdown"
            )
        ]
        
        return DialogPrompt(
            dialog_type=DialogType.LOCATION_MISMATCH,
            message=message,
            context={
                "current_location": validation_result.location,
                "concepts": extracted_concepts
            },
            options=options,
            default_option="specify_regiones"
        )
    
    def _create_generic_clarification_dialog(self, validation_result, extracted_concepts: List[Dict[str, Any]]) -> DialogPrompt:
        """Crear diálogo genérico para clarificaciones"""
        
        violations_text = "\\n".join(f"• {v}" for v in validation_result.violations)
        
        message = f"""❓ CLARIFICACIÓN NECESARIA
        
Se detectaron las siguientes inconsistencias:

{violations_text}

¿Cómo desea proceder?"""
        
        options = [
            DialogOption(
                id="show_suggestions",
                text="Mostrar sugerencias automáticas",
                action="detailed_breakdown"
            ),
            DialogOption(
                id="ignore_warnings",
                text="Continuar ignorando advertencias",
                action="ignore_violation"
            ),
            DialogOption(
                id="manual_review",
                text="Revisar manualmente cada concepto",
                action="detailed_breakdown"
            )
        ]
        
        return DialogPrompt(
            dialog_type=DialogType.CLARIFICATION_NEEDED,
            message=message,
            context={
                "violations": validation_result.violations,
                "concepts": extracted_concepts
            },
            options=options,
            default_option="show_suggestions"
        )
    
    def process_dialog_response(self, dialog_prompt: DialogPrompt, 
                              response: DialogResponse) -> Dict[str, Any]:
        """
        Procesar respuesta del usuario y ejecutar acción correspondiente.
        
        Returns:
            Dict con resultado de la acción y próximos pasos
        """
        
        selected_option = None
        for option in dialog_prompt.options:
            if option.id == response.selected_option_id:
                selected_option = option
                break
        
        if not selected_option:
            return {
                'success': False,
                'error': f"Opción inválida: {response.selected_option_id}",
                'next_steps': ['retry_dialog']
            }
        
        # Ejecutar handler de la acción
        handler = self.response_handlers.get(selected_option.action)
        if handler:
            result = handler(dialog_prompt, selected_option, response)
        else:
            result = {
                'success': False,
                'error': f"Handler no implementado para acción: {selected_option.action}",
                'next_steps': ['manual_intervention']
            }
        
        # Registrar en historial
        self.dialog_history.append(dialog_prompt)
        
        return result
    
    def _handle_distribute_days(self, dialog_prompt: DialogPrompt, 
                              selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar distribución en varios días"""
        
        concepts = dialog_prompt.context['concepts']
        daily_limit = dialog_prompt.context.get('daily_limit', 30.0)
        
        # Algoritmo simple de distribución
        distributions = []
        current_day_total = 0
        current_day_concepts = []
        day_number = 1
        
        for concept in concepts:
            amount = float(concept.get('amount', 0))
            
            if current_day_total + amount <= daily_limit:
                current_day_concepts.append(concept)
                current_day_total += amount
            else:
                # Cerrar día actual y empezar nuevo
                if current_day_concepts:
                    distributions.append({
                        'day': day_number,
                        'concepts': current_day_concepts.copy(),
                        'total': current_day_total
                    })
                
                day_number += 1
                current_day_concepts = [concept]
                current_day_total = amount
        
        # Agregar último día
        if current_day_concepts:
            distributions.append({
                'day': day_number,
                'concepts': current_day_concepts,
                'total': current_day_total
            })
        
        return {
            'success': True,
            'action_taken': 'distribute_days',
            'result': {
                'distribution': distributions,
                'total_days': len(distributions),
                'all_within_limits': all(d['total'] <= daily_limit for d in distributions)
            },
            'next_steps': ['validate_distribution', 'confirm_with_user']
        }
    
    def _handle_reduce_amounts(self, dialog_prompt: DialogPrompt, 
                             selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar reducción de montos"""
        
        concepts = dialog_prompt.context['concepts']
        daily_limit = dialog_prompt.context.get('daily_limit', 30.0)
        total_amount = dialog_prompt.context.get('total_amount', 0)
        
        reduction_needed = total_amount - daily_limit
        
        # Estrategia: reducir proporcionalmente
        reduction_factor = daily_limit / total_amount
        
        adjusted_concepts = []
        for concept in concepts:
            original_amount = float(concept.get('amount', 0))
            adjusted_amount = original_amount * reduction_factor
            
            adjusted_concept = concept.copy()
            adjusted_concept['amount'] = round(adjusted_amount, 2)
            adjusted_concept['adjustment_note'] = f"Reducido de S/{original_amount} (factor: {reduction_factor:.3f})"
            adjusted_concepts.append(adjusted_concept)
        
        return {
            'success': True,
            'action_taken': 'reduce_amounts',
            'result': {
                'adjusted_concepts': adjusted_concepts,
                'total_reduction': reduction_needed,
                'new_total': daily_limit,
                'reduction_factor': reduction_factor
            },
            'next_steps': ['validate_adjustments', 'confirm_with_user']
        }
    
    def _handle_specify_location(self, dialog_prompt: DialogPrompt, 
                               selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar especificación de ubicación"""
        
        new_location = selected_option.parameters.get('location', 'regiones')
        concepts = dialog_prompt.context['concepts']
        
        return {
            'success': True,
            'action_taken': 'specify_location',
            'result': {
                'new_location': new_location,
                'concepts': concepts,
                'requires_revalidation': True
            },
            'next_steps': ['revalidate_with_new_location']
        }
    
    def _handle_use_general_mobility(self, dialog_prompt: DialogPrompt, 
                                   selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar uso de movilidad local general"""
        
        daily_limit = dialog_prompt.context.get('daily_limit', 30.0)
        location = dialog_prompt.context.get('location', 'regiones')
        
        general_mobility_concept = {
            'numeral': '8.4.17.3',
            'concepto': 'Movilidad local para el desarrollo de actividades oficiales',
            'amount': daily_limit,
            'location': location,
            'replaces': [c.get('numeral') for c in dialog_prompt.context.get('concepts', [])]
        }
        
        return {
            'success': True,
            'action_taken': 'use_general_mobility',
            'result': {
                'replacement_concept': general_mobility_concept,
                'covers_all_transport': True,
                'within_limits': True
            },
            'next_steps': ['validate_replacement_concept']
        }
    
    def _handle_ignore_violation(self, dialog_prompt: DialogPrompt, 
                                selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar ignorar violaciones (con advertencias)"""
        
        return {
            'success': True,
            'action_taken': 'ignore_violation',
            'result': {
                'ignored_violations': dialog_prompt.context.get('violations', []),
                'warning': 'Procediendo con violaciones normativas ignoradas',
                'requires_supervisor_approval': True
            },
            'next_steps': ['require_supervisor_approval', 'document_exception']
        }
    
    def _handle_detailed_breakdown(self, dialog_prompt: DialogPrompt, 
                                 selected_option: DialogOption, response: DialogResponse) -> Dict[str, Any]:
        """Manejar solicitud de desglose detallado"""
        
        concepts = dialog_prompt.context.get('concepts', [])
        
        breakdown = []
        for concept in concepts:
            breakdown.append({
                'numeral': concept.get('numeral'),
                'concepto': concept.get('concepto', 'No definido'),
                'amount': concept.get('amount', 0),
                'location': concept.get('location', 'No especificada'),
                'valid': concept.get('valid', False),
                'issues': concept.get('violation_reason', 'Ninguna')
            })
        
        return {
            'success': True,
            'action_taken': 'detailed_breakdown',
            'result': {
                'concept_breakdown': breakdown,
                'summary': {
                    'total_concepts': len(breakdown),
                    'valid_concepts': sum(1 for c in breakdown if c['valid']),
                    'total_amount': sum(c['amount'] for c in breakdown)
                }
            },
            'next_steps': ['review_breakdown', 'select_next_action']
        }
    
    def _format_concepts_list(self, concepts: List[Dict[str, Any]]) -> str:
        """Formatear lista de conceptos para mostrar"""
        
        formatted_lines = []
        for concept in concepts:
            numeral = concept.get('numeral', 'N/A')
            amount = concept.get('amount', 0)
            concepto = concept.get('concepto', 'No definido')[:50] + "..." if len(concept.get('concepto', '')) > 50 else concept.get('concepto', 'No definido')
            formatted_lines.append(f"• {numeral}: {concepto} - S/ {amount:.2f}")
        
        return "\\n".join(formatted_lines)
    
    def _analyze_concept_conflicts(self, violations: List[str]) -> Dict[str, Any]:
        """Analizar conflictos específicos entre conceptos"""
        
        conflict_info = {
            'description': 'Conceptos mutuamente excluyentes detectados',
            'conflicting_concepts': '',
            'resolution_suggestions': []
        }
        
        # Extraer información de las violaciones
        for violation in violations:
            if 'mutuamente excluyentes' in violation:
                # Parsear violación para extraer conceptos
                parts = violation.split(':')
                if len(parts) > 1:
                    conflict_info['conflicting_concepts'] = parts[1].strip()
        
        return conflict_info
    
    def get_dialog_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de diálogos"""
        
        return [asdict(dialog) for dialog in self.dialog_history]
    
    def export_dialog_session(self, output_path: str):
        """Exportar sesión de diálogo completa"""
        
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'total_dialogs': len(self.dialog_history),
            'dialog_history': self.get_dialog_history(),
            'session_summary': {
                'dialog_types_used': list(set(d.dialog_type.value for d in self.dialog_history)),
                'most_common_issue': self._get_most_common_dialog_type()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Sesión de diálogo exportada a: {output_path}")
    
    def _get_most_common_dialog_type(self) -> str:
        """Obtener tipo de diálogo más común en la sesión"""
        
        if not self.dialog_history:
            return "none"
        
        type_counts = {}
        for dialog in self.dialog_history:
            dialog_type = dialog.dialog_type.value
            type_counts[dialog_type] = type_counts.get(dialog_type, 0) + 1
        
        return max(type_counts, key=type_counts.get) if type_counts else "none"

# Función de conveniencia para crear diálogos
def create_dialog_for_violations(validation_result, extracted_concepts: List[Dict[str, Any]]) -> Optional[DialogPrompt]:
    """Función de conveniencia para crear diálogos"""
    manager = DialogManager()
    return manager.create_dialog_for_validation(validation_result, extracted_concepts)
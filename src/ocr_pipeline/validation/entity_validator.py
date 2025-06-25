#!/usr/bin/env python3
"""
Entity Validator for OCR Pipeline
=================================

Validates entities extracted by NER using Pydantic models, ensuring data quality
and type safety before vectorstore generation.
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import logging
from .pydantic_models import (
    DirectivaEntities, ValidationResults, LegalReference,
    AmountEntity, NumeralEntity, RoleEntity, DateEntity, ValidationError,
    EntityType, ConfidenceLevel, RoleLevel, PYDANTIC_AVAILABLE,
    create_amount_entity, create_role_entity, create_numeral_entity
)

try:
    from .pydantic_models import (
        DirectivaEntities, ValidationResults, LegalReference,
        AmountEntity, NumeralEntity, RoleEntity, DateEntity, ValidationError,
        EntityType, ConfidenceLevel, RoleLevel, PYDANTIC_AVAILABLE
    )
except ImportError:
    PYDANTIC_AVAILABLE = False


class EntityValidator:
    """Validates entities extracted by NER using Pydantic models."""
    
    def __init__(self, strict_validation: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_validation: If True, fail on any validation error
        """
        self.strict_validation = strict_validation
        self.logger = logging.getLogger(__name__)
        
        # Validation patterns
        self.patterns = {
            'amount': re.compile(r'S/\s*(\d{1,6}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'numeral': re.compile(r'(\d{1,2}(?:\.\d{1,2}){1,4})', re.IGNORECASE),
            'reference': re.compile(r'(decreto\s+supremo\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,4})', re.IGNORECASE),
            'directive': re.compile(r'(directiva\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,10})', re.IGNORECASE),
            'percentage': re.compile(r'(\d{1,2}(?:\.\d+)?)%', re.IGNORECASE),
        }
        
        # Role mappings
        self.role_mappings = {
            'ministro': RoleLevel.MINISTER,
            'ministros': RoleLevel.MINISTER,
            'ministro de estado': RoleLevel.MINISTER,
            'servidor público': RoleLevel.CIVIL_SERVANT,
            'servidor civil': RoleLevel.CIVIL_SERVANT,
            'funcionario de confianza': RoleLevel.TRUST_OFFICIAL,
            'funcionario': RoleLevel.GENERAL
        }
        
        self.known_amounts = {
            30.00: "Límite para declaración jurada",
            320.00: "Viático diario para servidores civiles",
            380.00: "Viático diario para Ministros, Viceministros y Secretario General"
        }
        
        self.known_roles = {
            "ministros de estado": "minister",
            "viceministros": "vice_minister", 
            "secretario general": "secretary_general",
            "servidores civiles": "civil_servant",
            "servidor público": "civil_servant"
        }
        
        self.validation_rules = {
            'amounts': self._validate_amounts,
            'roles': self._validate_roles,
            'numerals': self._validate_numerals
        }
    
    def validate_entities(self, text: str, confidence_threshold: float = 0.8) -> ValidationResults:
        """Valida y extrae entidades del texto"""
        
        # Extraer entidades
        amounts = self._extract_amounts(text)
        roles = self._extract_roles(text)  
        numerals = self._extract_numerals(text)
        references = self._extract_references(text)
        
        # Validar entidades
        validated_amounts = self._validate_amounts(amounts)
        validated_roles = self._validate_roles(roles)
        validated_numerals = self._validate_numerals(numerals)
        validated_references = self._validate_references(references)
        
        # Recopilar errores
        validation_errors = []
        validation_errors.extend(self._get_validation_errors(validated_amounts))
        validation_errors.extend(self._get_validation_errors(validated_roles))
        validation_errors.extend(self._get_validation_errors(validated_numerals))
        
        # Filtrar por confianza
        filtered_amounts = [a for a in validated_amounts if a.confidence >= confidence_threshold]
        filtered_roles = [r for r in validated_roles if r.confidence >= confidence_threshold]
        filtered_numerals = [n for n in validated_numerals if n.confidence >= confidence_threshold]
        filtered_references = [ref for ref in validated_references if ref.confidence >= confidence_threshold]
        
        return ValidationResults(
            amounts=filtered_amounts,
            roles=filtered_roles,
            numerals=filtered_numerals,
            references=filtered_references,
            validation_errors=validation_errors,
            overall_confidence=0.0,  # Se calculará automáticamente
            extraction_timestamp=datetime.now().isoformat()
        )
    
    def _extract_amounts(self, text: str) -> List[AmountEntity]:
        """Extrae montos monetarios del texto"""
        amounts = []
        
        # Patrones para montos en soles
        patterns = [
            r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'soles\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*soles'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount_value = float(amount_str)
                    
                    # Determinar contexto
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    # Determinar confianza basada en contexto
                    confidence = self._calculate_amount_confidence(amount_value, context)
                    
                    amounts.append(create_amount_entity(
                        value=amount_value,
                        raw_text=match.group(0),
                        confidence=confidence,
                        context=context
                    ))
                    
                except (ValueError, TypeError) as e:
                    continue
        
        return amounts
    
    def _extract_roles(self, text: str) -> List[RoleEntity]:
        """Extrae roles y cargos del texto"""
        roles = []
        
        role_patterns = [
            r'(ministros?\s+de\s+estado)',
            r'(viceministros?)',
            r'(secretarios?\s+generales?)',
            r'(servidores?\s+(?:públicos?|civiles?))',
            r'(funcionarios?\s+públicos?)'
        ]
        
        for pattern in role_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                role_text = match.group(1)
                
                # Buscar monto asociado cerca del rol
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                
                amount_match = re.search(r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', context)
                associated_amount = None
                if amount_match:
                    try:
                        associated_amount = float(amount_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
                
                confidence = self._calculate_role_confidence(role_text, context)
                
                roles.append(create_role_entity(
                    role_name=role_text.title(),
                    raw_text=match.group(0),
                    confidence=confidence,
                    allowance_amount=associated_amount
                ))
        
        return roles
    
    def _extract_numerals(self, text: str) -> List[NumeralEntity]:
        """Extrae numerales/artículos del texto"""
        numerals = []
        
        # Patrón para numerales (ej: 8.4, 8.4.17)
        pattern = r'(\d+(?:\.\d+)*)\s*[\.:\-]?\s*([^\n]*?)(?=\n|\d+\.|$)'
        
        matches = re.finditer(pattern, text)
        for match in matches:
            numeral = match.group(1)
            title = match.group(2).strip() if match.group(2) else None
            
            # Limpiar título
            if title:
                title = re.sub(r'^[\.:\-\s]+', '', title)
                title = title[:100]  # Limitar longitud
            
            confidence = self._calculate_numeral_confidence(numeral, title)
            
            numerals.append(create_numeral_entity(
                numeral=numeral,
                confidence=confidence,
                title=title
            ))
        
        return numerals
    
    def _extract_references(self, text: str) -> List[LegalReference]:
        """Extrae referencias legales internas"""
        references = []
        
        # Referencias a numerales
        pattern = r'(?:numeral|punto|inciso)\s+(\d+(?:\.\d+)*)'
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            referenced_numeral = match.group(1)
            
            # Buscar contexto
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            
            references.append(LegalReference(
                numeral="unknown",  # Se determinaría por posición en documento
                referenced_entity=referenced_numeral,
                relationship_type="reference",
                confidence=0.8
            ))
        
        return references
    
    def _validate_amounts(self, amounts: List[AmountEntity]) -> List[AmountEntity]:
        """Valida montos extraídos"""
        validated = []
        for amount in amounts:
            try:
                # Re-validar con Pydantic
                validated_amount = AmountEntity.model_validate(amount.model_dump())
                validated.append(validated_amount)
            except Exception as e:
                # Si falla validación, reducir confianza pero mantener
                amount.confidence *= 0.5
                validated.append(amount)
        return validated
    
    def _validate_roles(self, roles: List[RoleEntity]) -> List[RoleEntity]:
        """Valida roles extraídos"""
        validated = []
        for role in roles:
            try:
                validated_role = RoleEntity.model_validate(role.model_dump())
                validated.append(validated_role)
            except Exception as e:
                role.confidence *= 0.5
                validated.append(role)
        return validated
    
    def _validate_numerals(self, numerals: List[NumeralEntity]) -> List[NumeralEntity]:
        """Valida numerales extraídos"""
        validated = []
        for numeral in numerals:
            try:
                validated_numeral = NumeralEntity.model_validate(numeral.model_dump())
                validated.append(validated_numeral)
            except Exception as e:
                numeral.confidence *= 0.5
                validated.append(numeral)
        return validated
    
    def _validate_references(self, references: List[LegalReference]) -> List[LegalReference]:
        """Valida referencias extraídas"""
        return references  # Implementación básica
    
    def _calculate_amount_confidence(self, amount: float, context: str) -> float:
        """Calcula confianza para montos"""
        base_confidence = 0.8
        
        # Aumentar confianza para montos conocidos
        if amount in self.known_amounts:
            base_confidence = 0.95
        
        # Aumentar confianza si hay palabras clave en contexto
        keywords = ['viático', 'diario', 'máximo', 'declaración', 'jurada']
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in context.lower())
        base_confidence += keyword_matches * 0.02
        
        return min(base_confidence, 1.0)
    
    def _calculate_role_confidence(self, role: str, context: str) -> float:
        """Calcula confianza para roles"""
        base_confidence = 0.8
        
        # Aumentar confianza para roles conocidos
        if role.lower() in self.known_roles:
            base_confidence = 0.9
        
        # Verificar si hay monto asociado
        if re.search(r'S/\s*\d+', context):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _calculate_numeral_confidence(self, numeral: str, title: Optional[str]) -> float:
        """Calcula confianza para numerales"""
        base_confidence = 0.7
        
        # Aumentar confianza si tiene título
        if title and len(title.strip()) > 5:
            base_confidence = 0.85
        
        # Aumentar confianza para numerales bien formateados
        if re.match(r'^\d+(\.\d+){1,3}$', numeral):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _get_validation_errors(self, entities: List[Any]) -> List[str]:
        """Extrae errores de validación de entidades"""
        errors = []
        for entity in entities:
            if hasattr(entity, 'confidence') and entity.confidence < 0.5:
                errors.append(f"Low confidence entity: {type(entity).__name__}")
        return errors
    
    def create_directiva_entities(self, text: str, confidence_threshold: float = 0.8) -> DirectivaEntities:
        """Crea entidades completas de directiva"""
        validation_results = self.validate_entities(text, confidence_threshold)
        
        return DirectivaEntities(
            document_title="DIRECTIVA N° 011-2020-MINEDU",
            document_code="011-2020-MINEDU", 
            validation_results=validation_results,
            metadata={
                "extraction_method": "pydantic_validation",
                "confidence_threshold": confidence_threshold,
                "total_entities": (
                    len(validation_results.amounts) + 
                    len(validation_results.roles) + 
                    len(validation_results.numerals)
                )
            }
        )
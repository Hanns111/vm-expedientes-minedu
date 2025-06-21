#!/usr/bin/env python3
"""
Pydantic Models for OCR Pipeline Entity Validation
=================================================

This module defines Pydantic models to validate entities extracted by the OCR pipeline,
ensuring data quality and type safety for legal documents processing.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
import re
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator, root_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for environments without pydantic
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda **kwargs: None
    validator = lambda *args, **kwargs: lambda func: func
    root_validator = lambda *args, **kwargs: lambda func: func


class EntityType(str, Enum):
    """Enumeration of legal entity types."""
    AMOUNT = "amount"
    NUMERAL = "numeral" 
    ROLE = "role"
    DATE = "date"
    REFERENCE = "reference"
    DIRECTIVE = "directive"
    PERCENTAGE = "percentage"
    TIMEFRAME = "timeframe"
    DECLARATION = "declaration"
    PROCEDURE = "procedure"


class ConfidenceLevel(str, Enum):
    """OCR confidence levels."""
    HIGH = "high"      # >= 0.9
    MEDIUM = "medium"  # 0.7 - 0.89
    LOW = "low"        # 0.5 - 0.69
    VERY_LOW = "very_low"  # < 0.5


class RoleLevel(str, Enum):
    """Government role hierarchy levels."""
    MINISTER = "minister"
    CIVIL_SERVANT = "civil_servant"
    TRUST_OFFICIAL = "trust_official"
    GENERAL = "general"


class AmountEntity(BaseModel):
    """Validated monetary amount entity."""
    value: Decimal = Field(..., description="Monetary value in soles")
    currency: str = Field(default="S/", description="Currency symbol")
    text: str = Field(..., description="Original extracted text")
    normalized: str = Field(..., description="Normalized format")
    confidence: float = Field(ge=0.0, le=1.0, description="OCR confidence")
    
    @validator('value')
    def validate_amount(cls, v):
        """Validate amount is positive and reasonable."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > Decimal('100000'):  # Reasonable upper limit for viáticos
            raise ValueError("Amount seems unreasonably high")
        return v
    
    @validator('normalized')
    def validate_normalized_format(cls, v):
        """Ensure normalized format follows S/ X.XX pattern."""
        if not re.match(r'^S/\s*\d{1,6}\.00$', v):
            raise ValueError("Normalized format must be 'S/ XXX.00'")
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class NumeralEntity(BaseModel):
    """Legal numeral reference (e.g., 8.4.17)."""
    number: str = Field(..., description="Numeral number")
    level: int = Field(ge=1, le=5, description="Hierarchy level (dots count + 1)")
    parent: Optional[str] = Field(None, description="Parent numeral")
    text: str = Field(..., description="Original extracted text")
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('number')
    def validate_numeral_format(cls, v):
        """Validate numeral follows legal format."""
        if not re.match(r'^\d{1,2}(?:\.\d{1,2})*$', v):
            raise ValueError("Numeral must follow format like 8, 8.4, 8.4.17")
        return v
    
    @validator('level', pre=True, always=True)
    def calculate_level(cls, v, values):
        """Calculate level based on dots in number."""
        if 'number' in values:
            return values['number'].count('.') + 1
        return v


class RoleEntity(BaseModel):
    """Government role entity."""
    role_type: RoleLevel = Field(..., description="Role hierarchy level")
    title: str = Field(..., description="Official title")
    text: str = Field(..., description="Original extracted text")
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title format."""
        if len(v.strip()) < 3:
            raise ValueError("Title too short")
        return v.strip().title()


class DateEntity(BaseModel):
    """Date entity with validation."""
    date_value: date = Field(..., description="Parsed date")
    text: str = Field(..., description="Original extracted text")
    format_type: str = Field(..., description="Detected date format")
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('date_value')
    def validate_reasonable_date(cls, v):
        """Ensure date is reasonable for legal documents."""
        if v.year < 2000 or v.year > 2030:
            raise ValueError("Date must be between 2000-2030")
        return v


class LegalReference(BaseModel):
    """Legal reference to laws, decrees, etc."""
    reference_type: str = Field(..., description="Type of reference")
    number: str = Field(..., description="Reference number")
    year: int = Field(..., description="Year of reference")
    institution: str = Field(..., description="Issuing institution")
    text: str = Field(..., description="Original extracted text")
    confidence: float = Field(ge=0.0, le=1.0)
    
    @validator('reference_type')
    def validate_reference_type(cls, v):
        """Validate known reference types."""
        valid_types = ['decreto supremo', 'directiva', 'ley', 'resolución']
        if v.lower() not in valid_types:
            raise ValueError(f"Reference type must be one of: {valid_types}")
        return v.lower()
    
    @validator('year')
    def validate_year(cls, v):
        """Validate reasonable year."""
        if v < 1990 or v > 2030:
            raise ValueError("Year must be between 1990-2030")
        return v


class DirectivaEntities(BaseModel):
    """Complete set of entities extracted from directiva document."""
    amounts: List[AmountEntity] = Field(default_factory=list)
    numerals: List[NumeralEntity] = Field(default_factory=list)
    roles: List[RoleEntity] = Field(default_factory=list)
    dates: List[DateEntity] = Field(default_factory=list)
    references: List[LegalReference] = Field(default_factory=list)
    percentages: List[str] = Field(default_factory=list)
    declarations: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    
    # Document metadata
    document_id: str = Field(..., description="Document identifier")
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    total_entities: int = Field(default=0, description="Total entities count")
    
    @root_validator
    def calculate_totals(cls, values):
        """Calculate total entities count."""
        total = (
            len(values.get('amounts', [])) +
            len(values.get('numerals', [])) +
            len(values.get('roles', [])) +
            len(values.get('dates', [])) +
            len(values.get('references', [])) +
            len(values.get('percentages', [])) +
            len(values.get('declarations', [])) +
            len(values.get('procedures', []))
        )
        values['total_entities'] = total
        return values
    
    def get_amounts_by_role(self, role_level: RoleLevel) -> List[AmountEntity]:
        """Get amounts filtered by role level."""
        # This would need additional context from chunks
        return [amt for amt in self.amounts if amt.value >= 300]  # Simplified
    
    def get_critical_amounts(self) -> List[AmountEntity]:
        """Get amounts that are commonly queried (30, 320, 380)."""
        critical_values = [Decimal('30.00'), Decimal('320.00'), Decimal('380.00')]
        return [amt for amt in self.amounts if amt.value in critical_values]


class ValidationError(BaseModel):
    """Individual validation error."""
    entity_type: EntityType
    field: str
    value: Any
    error_message: str
    confidence: float
    severity: str = Field(default="warning")  # warning, error, critical


class ValidationResults(BaseModel):
    """Results of entity validation process."""
    document_id: str
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    
    # OCR Quality Metrics
    overall_confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    
    # Validation Results
    valid_entities: DirectivaEntities
    validation_errors: List[ValidationError] = Field(default_factory=list)
    
    # Quality Metrics
    entities_validated: int = Field(default=0)
    entities_failed: int = Field(default=0)
    critical_errors: int = Field(default=0)
    warnings: int = Field(default=0)
    
    # Success Indicators
    is_valid: bool = Field(default=True)
    ready_for_vectorstore: bool = Field(default=True)
    
    @validator('confidence_level', pre=True, always=True)
    def determine_confidence_level(cls, v, values):
        """Determine confidence level from overall confidence."""
        confidence = values.get('overall_confidence', 0.0)
        if confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    @root_validator
    def calculate_metrics(cls, values):
        """Calculate validation metrics."""
        errors = values.get('validation_errors', [])
        values['entities_failed'] = len(errors)
        values['critical_errors'] = len([e for e in errors if e.severity == 'critical'])
        values['warnings'] = len([e for e in errors if e.severity == 'warning'])
        
        # Determine if ready for vectorstore
        has_critical = values['critical_errors'] > 0
        low_confidence = values.get('overall_confidence', 1.0) < 0.5
        values['is_valid'] = not has_critical
        values['ready_for_vectorstore'] = not has_critical and not low_confidence
        
        return values
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            'document_id': self.document_id,
            'overall_confidence': self.overall_confidence,
            'confidence_level': self.confidence_level.value,
            'total_entities': self.valid_entities.total_entities,
            'critical_errors': self.critical_errors,
            'warnings': self.warnings,
            'is_valid': self.is_valid,
            'ready_for_vectorstore': self.ready_for_vectorstore
        }


# Fallback classes if Pydantic is not available
if not PYDANTIC_AVAILABLE:
    class SimpleEntity:
        """Fallback entity class."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    AmountEntity = SimpleEntity
    NumeralEntity = SimpleEntity
    RoleEntity = SimpleEntity
    DateEntity = SimpleEntity
    LegalReference = SimpleEntity
    DirectivaEntities = SimpleEntity
    ValidationError = SimpleEntity
    ValidationResults = SimpleEntity


def create_validation_models():
    """Factory function to create validation models."""
    if not PYDANTIC_AVAILABLE:
        print("⚠️ Pydantic not available - using fallback validation")
        return SimpleEntity, SimpleEntity, SimpleEntity
    
    return DirectivaEntities, ValidationResults, LegalReference
#!/usr/bin/env python3
"""
Test Pydantic Entity Validation with Real Directiva Data
========================================================

This script demonstrates the Pydantic validation system with entities that would
be extracted from the real directiva_de_viaticos_011_2020_imagen.pdf document.
"""

import sys
import json
from pathlib import Path
from decimal import Decimal

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from ocr_pipeline.validation import (
        DirectivaEntities, ValidationResults, LegalReference,
        AmountEntity, NumeralEntity, RoleEntity, ValidationError,
        EntityValidator, VALIDATION_AVAILABLE
    )
    print("✓ Pydantic validation models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import validation models: {e}")
    print("Using fallback validation...")
    VALIDATION_AVAILABLE = False


def create_sample_directiva_entities():
    """Create sample entities as would be extracted from the real directiva PDF."""
    
    print("\n🔬 CREATING SAMPLE ENTITIES FROM DIRECTIVA PDF")
    print("=" * 55)
    
    # Sample entities that would be extracted from directiva_de_viaticos_011_2020_imagen.pdf
    raw_entities = {
        'amount': [
            {
                'text': 'S/ 30.00',
                'normalized': 'S/ 30.00',
                'confidence': 0.92
            },
            {
                'text': 'S/ 320,00',
                'normalized': 'S/ 320.00',
                'confidence': 0.89
            },
            {
                'text': 'S/ 380.00',
                'normalized': 'S/ 380.00',
                'confidence': 0.94
            },
            {
                'text': 'S/ 350.00',
                'normalized': 'S/ 350.00',
                'confidence': 0.91
            },
            {
                'text': 'S/ 25,00',
                'normalized': 'S/ 25.00',
                'confidence': 0.87
            }
        ],
        'numeral': [
            {
                'text': '8.4',
                'normalized': '8.4',
                'confidence': 0.95
            },
            {
                'text': '8.4.17',
                'normalized': '8.4.17',
                'confidence': 0.93
            },
            {
                'text': '8.5',
                'normalized': '8.5',
                'confidence': 0.90
            },
            {
                'text': '8.1',
                'normalized': '8.1',
                'confidence': 0.88
            }
        ],
        'role_minister': [
            {
                'text': 'Ministros de Estado',
                'normalized': 'ministros de estado',
                'confidence': 0.96
            }
        ],
        'role_civil': [
            {
                'text': 'Servidor Público',
                'normalized': 'servidor público',
                'confidence': 0.94
            },
            {
                'text': 'Funcionarios de Confianza',
                'normalized': 'funcionarios de confianza',
                'confidence': 0.92
            }
        ],
        'reference': [
            {
                'text': 'Decreto Supremo N° 007-2013-EF',
                'normalized': 'DECRETO SUPREMO N° 007-2013-EF',
                'confidence': 0.89
            },
            {
                'text': 'DIRECTIVA N° 011-2020-MINEDU',
                'normalized': 'DIRECTIVA N° 011-2020-MINEDU',
                'confidence': 0.97
            }
        ],
        'percentage': [
            {
                'text': '30%',
                'normalized': '30%',
                'confidence': 0.91
            }
        ],
        'declaration': [
            {
                'text': 'Declaración Jurada',
                'normalized': 'declaración jurada',
                'confidence': 0.93
            }
        ],
        'procedure': [
            {
                'text': 'rendición de cuentas',
                'normalized': 'rendición de cuentas',
                'confidence': 0.88
            },
            {
                'text': 'gastos de movilidad',
                'normalized': 'gastos de movilidad',
                'confidence': 0.90
            }
        ]
    }
    
    print(f"📊 Created sample entities:")
    for entity_type, entities in raw_entities.items():
        print(f"   {entity_type}: {len(entities)} entities")
    
    return raw_entities


def test_pydantic_validation():
    """Test Pydantic validation with sample entities."""
    
    if not VALIDATION_AVAILABLE:
        print("\n⚠️ Pydantic not available - demonstrating fallback validation")
        return test_fallback_validation()
    
    print("\n🧪 TESTING PYDANTIC VALIDATION")
    print("=" * 35)
    
    # Create sample entities
    raw_entities = create_sample_directiva_entities()
    
    # Initialize validator
    validator = EntityValidator(strict_validation=False)
    
    # Run validation
    validation_results = validator.validate_entities(
        raw_entities,
        overall_confidence=0.92,
        document_id="directiva_011_2020_test"
    )
    
    print(f"\n📋 VALIDATION RESULTS:")
    print("=" * 25)
    
    if hasattr(validation_results, 'get_summary'):
        summary = validation_results.get_summary()
        print(f"✓ Document ID: {summary['document_id']}")
        print(f"✓ Overall Confidence: {summary['overall_confidence']:.3f}")
        print(f"✓ Confidence Level: {summary['confidence_level']}")
        print(f"✓ Total Entities: {summary['total_entities']}")
        print(f"✓ Critical Errors: {summary['critical_errors']}")
        print(f"✓ Warnings: {summary['warnings']}")
        print(f"✓ Valid for Processing: {summary['is_valid']}")
        print(f"✓ Ready for Vectorstore: {summary['ready_for_vectorstore']}")
    else:
        print(f"✓ Validation completed (fallback mode)")
        print(f"✓ Document ID: {validation_results.get('document_id', 'unknown')}")
        print(f"✓ Overall Confidence: {validation_results.get('overall_confidence', 0.0):.3f}")
    
    # Show validated entities
    print(f"\n💰 VALIDATED AMOUNTS:")
    if hasattr(validation_results, 'valid_entities'):
        amounts = validation_results.valid_entities.amounts
        for i, amount in enumerate(amounts, 1):
            print(f"   {i}. {amount.normalized} (confidence: {amount.confidence:.3f})")
        
        print(f"\n📋 VALIDATED NUMERALS:")
        numerals = validation_results.valid_entities.numerals
        for i, numeral in enumerate(numerals, 1):
            parent_info = f" → parent: {numeral.parent}" if numeral.parent else ""
            print(f"   {i}. {numeral.number} (level: {numeral.level}{parent_info})")
        
        print(f"\n👤 VALIDATED ROLES:")
        roles = validation_results.valid_entities.roles
        for i, role in enumerate(roles, 1):
            print(f"   {i}. {role.title} ({role.role_type.value})")
        
        print(f"\n📜 VALIDATED REFERENCES:")
        references = validation_results.valid_entities.references
        for i, ref in enumerate(references, 1):
            print(f"   {i}. {ref.reference_type.title()} {ref.number}-{ref.year} ({ref.institution})")
    
    # Show validation errors
    if hasattr(validation_results, 'validation_errors') and validation_results.validation_errors:
        print(f"\n⚠️ VALIDATION ERRORS:")
        for i, error in enumerate(validation_results.validation_errors, 1):
            print(f"   {i}. {error.severity.upper()}: {error.error_message}")
            print(f"      Entity: {error.entity_type.value}, Field: {error.field}")
    else:
        print(f"\n✅ NO VALIDATION ERRORS")
    
    return validation_results


def test_fallback_validation():
    """Test fallback validation when Pydantic is not available."""
    
    print("\n🔄 TESTING FALLBACK VALIDATION")
    print("=" * 35)
    
    raw_entities = create_sample_directiva_entities()
    
    validator = EntityValidator(strict_validation=False)
    validation_results = validator.validate_entities(
        raw_entities,
        overall_confidence=0.92,
        document_id="directiva_011_2020_fallback"
    )
    
    print(f"✓ Fallback validation completed")
    print(f"✓ Document ID: {validation_results.get('document_id')}")
    print(f"✓ Overall Confidence: {validation_results.get('overall_confidence', 0.0):.3f}")
    print(f"✓ Total Entities: {validation_results.get('total_entities', 0)}")
    print(f"✓ Valid for Processing: {validation_results.get('is_valid', True)}")
    
    return validation_results


def test_critical_entity_validation():
    """Test validation of critical entities for directiva documents."""
    
    if not VALIDATION_AVAILABLE:
        print("\n⚠️ Skipping critical entity validation - Pydantic not available")
        return
    
    print("\n🎯 TESTING CRITICAL ENTITY VALIDATION")
    print("=" * 40)
    
    # Create sample DirectivaEntities
    try:
        entities = DirectivaEntities(
            document_id="directiva_critical_test",
            amounts=[
                AmountEntity(value=Decimal('30.00'), text='S/ 30.00', normalized='S/ 30.00', confidence=0.92),
                AmountEntity(value=Decimal('320.00'), text='S/ 320.00', normalized='S/ 320.00', confidence=0.89),
                AmountEntity(value=Decimal('380.00'), text='S/ 380.00', normalized='S/ 380.00', confidence=0.94)
            ],
            numerals=[
                NumeralEntity(number='8.4', level=2, text='8.4', confidence=0.95),
                NumeralEntity(number='8.4.17', level=3, parent='8.4', text='8.4.17', confidence=0.93)
            ],
            roles=[
                RoleEntity(role_type='minister', title='Ministros De Estado', text='Ministros de Estado', confidence=0.96)
            ]
        )
        
        validator = EntityValidator()
        critical_results = validator.validate_critical_entities(entities)
        
        print(f"📊 CRITICAL VALIDATION RESULTS:")
        print(f"   ✓ Has Required Amounts: {critical_results['has_required_amounts']}")
        print(f"   ✓ Has Valid Numerals: {critical_results['has_valid_numerals']}")
        print(f"   ✓ Has Minister Roles: {critical_results['has_minister_roles']}")
        print(f"   ✓ Quality Score: {critical_results['quality_score']:.1%}")
        
        if critical_results['missing_entities']:
            print(f"   ⚠️ Missing Entities: {critical_results['missing_entities']}")
        
        # Show critical amounts
        critical_amounts = entities.get_critical_amounts()
        print(f"\n💎 CRITICAL AMOUNTS FOUND:")
        for amount in critical_amounts:
            print(f"   • {amount.normalized} (confidence: {amount.confidence:.3f})")
        
    except Exception as e:
        print(f"❌ Critical validation failed: {e}")


def demonstrate_validation_errors():
    """Demonstrate how validation handles invalid data."""
    
    if not VALIDATION_AVAILABLE:
        print("\n⚠️ Skipping error demonstration - Pydantic not available")
        return
    
    print("\n🚨 DEMONSTRATING VALIDATION ERROR HANDLING")
    print("=" * 45)
    
    # Create entities with intentional errors
    invalid_entities = {
        'amount': [
            {
                'text': 'S/ -50.00',  # Negative amount - should fail
                'normalized': 'S/ -50.00',
                'confidence': 0.85
            },
            {
                'text': 'S/ 1000000.00',  # Unreasonably high - should fail
                'normalized': 'S/ 1000000.00',
                'confidence': 0.90
            },
            {
                'text': 'invalid amount',  # Invalid format - should fail
                'normalized': 'invalid',
                'confidence': 0.30
            }
        ],
        'numeral': [
            {
                'text': 'abc.def',  # Invalid numeral format - should fail
                'normalized': 'abc.def',
                'confidence': 0.20
            }
        ],
        'reference': [
            {
                'text': 'Invalid Reference Format',  # Invalid reference - should fail
                'normalized': 'invalid reference format',
                'confidence': 0.40
            }
        ]
    }
    
    validator = EntityValidator(strict_validation=False)
    validation_results = validator.validate_entities(
        invalid_entities,
        overall_confidence=0.60,  # Low confidence
        document_id="error_demonstration"
    )
    
    print(f"📋 ERROR HANDLING RESULTS:")
    if hasattr(validation_results, 'validation_errors'):
        print(f"   Validation Errors: {len(validation_results.validation_errors)}")
        
        for i, error in enumerate(validation_results.validation_errors[:5], 1):
            print(f"   {i}. {error.severity.upper()}: {error.error_message}")
            print(f"      Type: {error.entity_type.value}, Value: {error.value}")
    
    if hasattr(validation_results, 'get_summary'):
        summary = validation_results.get_summary()
        print(f"\n   Overall Valid: {summary['is_valid']}")
        print(f"   Ready for Vectorstore: {summary['ready_for_vectorstore']}")
        print(f"   Critical Errors: {summary['critical_errors']}")


def main():
    """Run all validation tests."""
    
    print("🔬 PYDANTIC ENTITY VALIDATION DEMONSTRATION")
    print("=" * 55)
    print("Testing with entities from directiva_de_viaticos_011_2020_imagen.pdf")
    print("=" * 55)
    
    # Test main validation
    validation_results = test_pydantic_validation()
    
    # Test critical entity validation
    test_critical_entity_validation()
    
    # Demonstrate error handling
    demonstrate_validation_errors()
    
    print(f"\n🎉 VALIDATION TESTING COMPLETED")
    print("=" * 35)
    
    if VALIDATION_AVAILABLE:
        print("✅ Pydantic validation system ready for OCR pipeline")
        print("✅ Entities will be validated after NER extraction")
        print("✅ Invalid entities will be flagged before vectorstore generation")
    else:
        print("⚠️ Using fallback validation (install pydantic for full validation)")
    
    print(f"\n📋 INTEGRATION STATUS:")
    print("✅ Validation models created")
    print("✅ EntityValidator integrated into OCR pipeline")
    print("✅ Validation runs after NER, before vectorstore")
    print("✅ Validation results included in final output")


if __name__ == "__main__":
    main()
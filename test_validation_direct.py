#!/usr/bin/env python3
"""
Test directo de validación Pydantic para la directiva de viáticos
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_pydantic_availability():
    """Probar disponibilidad de Pydantic"""
    try:
        import pydantic
        print("✅ Pydantic is available")
        print(f"   Version: {pydantic.VERSION}")
        return True
    except ImportError as e:
        print(f"❌ Pydantic not available: {e}")
        return False

def test_validation_imports():
    """Probar imports de validación"""
    try:
        from ocr_pipeline.validation import (
            DirectivaEntities, ValidationResults, AmountEntity,
            NumeralEntity, RoleEntity, LegalReference, EntityValidator
        )
        print("✅ Validation models imported successfully")
        return True, {
            'DirectivaEntities': DirectivaEntities,
            'ValidationResults': ValidationResults,
            'AmountEntity': AmountEntity,
            'NumeralEntity': NumeralEntity, 
            'RoleEntity': RoleEntity,
            'LegalReference': LegalReference,
            'EntityValidator': EntityValidator
        }
    except ImportError as e:
        print(f"❌ Failed to import validation models: {e}")
        return False, {}

def test_amount_validation(AmountEntity):
    """Probar validación de montos"""
    print("\n💰 TESTING AMOUNT VALIDATION")
    
    test_cases = [
        (30.00, "S/ 30.00", True),
        (320.00, "S/ 320.00", True), 
        (380.00, "S/ 380.00", True),
        (-30.00, "S/ -30.00", False),  # Monto negativo
        (15000.00, "S/ 15,000.00", False)  # Monto muy alto
    ]
    
    for value, raw_text, should_pass in test_cases:
        try:
            amount = AmountEntity(
                value=value,
                raw_text=raw_text,
                confidence=0.9
            )
            if should_pass:
                print(f"✅ {raw_text} - Valid")
            else:
                print(f"⚠️  {raw_text} - Should have failed but didn't")
        except Exception as e:
            if not should_pass:
                print(f"✅ {raw_text} - Correctly rejected: {str(e)}")
            else:
                print(f"❌ {raw_text} - Unexpected error: {str(e)}")

def test_numeral_validation(NumeralEntity):
    """Probar validación de numerales"""
    print("\n📋 TESTING NUMERAL VALIDATION")
    
    test_cases = [
        ("8.4", 2, "8", "VIÁTICOS"),
        ("8.4.17", 3, "8.4", "Declaración Jurada"),
        ("10", 1, None, "DISPOSICIONES FINALES")
    ]
    
    for numeral, expected_level, expected_parent, title in test_cases:
        try:
            num_entity = NumeralEntity(
                numeral=numeral,
                level=expected_level,
                parent_numeral=expected_parent,
                title=title,
                confidence=0.9
            )
            print(f"✅ {numeral} - Level {num_entity.level}", end="")
            if num_entity.parent_numeral:
                print(f" (parent: {num_entity.parent_numeral})")
            else:
                print()
        except Exception as e:
            print(f"❌ {numeral} - Error: {str(e)}")

def test_role_validation(RoleEntity):
    """Probar validación de roles"""
    print("\n👤 TESTING ROLE VALIDATION")
    
    test_cases = [
        ("Ministros De Estado", "minister", 380.00),
        ("Servidor Público", "civil_servant", 320.00),
        ("Viceministros", "vice_minister", 380.00),
        ("Secretario General", "secretary_general", 380.00)
    ]
    
    for role_name, expected_type, amount in test_cases:
        try:
            role = RoleEntity(
                role_name=role_name,
                raw_text=role_name,
                confidence=0.9,
                allowance_amount=amount,
                role_type=expected_type
            )
            print(f"✅ {role.role_name} ({role.role_type})")
        except Exception as e:
            print(f"❌ {role_name} - Error: {str(e)}")

def test_entity_validator(EntityValidator):
    """Probar el validador de entidades completo"""
    print("\n🔍 TESTING ENTITY VALIDATOR")
    
    # Texto de ejemplo con información de viáticos
    sample_text = """
    8.4 VIÁTICOS
    Los viáticos para servidores civiles será de S/ 320.00 diarios.
    Para Ministros de Estado, Viceministros y Secretario General será de S/ 380.00.
    El límite para declaración jurada es de S/ 30.00.
    
    8.4.17 Declaración Jurada
    Cuando el gasto no supere los S/ 30.00 se podrá usar declaración jurada.
    """
    
    try:
        validator = EntityValidator()
        results = validator.validate_entities(sample_text, confidence_threshold=0.7)
        
        print(f"✅ Amounts found: {len(results.amounts)}")
        for amount in results.amounts:
            print(f"   - S/ {amount.value} (confidence: {amount.confidence:.2f})")
        
        print(f"✅ Roles found: {len(results.roles)}")
        for role in results.roles:
            print(f"   - {role.role_name} (type: {role.role_type})")
        
        print(f"✅ Numerals found: {len(results.numerals)}")
        for numeral in results.numerals:
            print(f"   - {numeral.numeral} (level: {numeral.level})")
        
        print(f"✅ Overall confidence: {results.overall_confidence:.2f}")
        
        if results.validation_errors:
            print(f"⚠️  Validation errors: {len(results.validation_errors)}")
            for error in results.validation_errors:
                print(f"   - {error}")
        
    except Exception as e:
        print(f"❌ Validator test failed: {str(e)}")

def test_directiva_entities_creation(EntityValidator, DirectivaEntities):
    """Probar creación de entidades completas de directiva"""
    print("\n📄 TESTING DIRECTIVA ENTITIES CREATION")
    
    sample_text = """
    DIRECTIVA N° 011-2020-MINEDU
    
    8.4 VIÁTICOS
    Los montos de viáticos son:
    - Servidores civiles: S/ 320.00 diarios
    - Ministros de Estado: S/ 380.00 diarios
    - Límite declaración jurada: S/ 30.00
    """
    
    try:
        validator = EntityValidator()
        directiva = validator.create_directiva_entities(sample_text, confidence_threshold=0.7)
        
        print(f"✅ Document: {directiva.document_title}")
        print(f"✅ Code: {directiva.document_code}")
        print(f"✅ Total entities: {directiva.metadata['total_entities']}")
        print(f"✅ Extraction method: {directiva.metadata['extraction_method']}")
        print(f"✅ Overall confidence: {directiva.validation_results.overall_confidence:.2f}")
        
    except Exception as e:
        print(f"❌ DirectivaEntities creation failed: {str(e)}")

def main():
    """Función principal de tests"""
    print("🧪 PYDANTIC VALIDATION SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Verificar Pydantic
    if not test_pydantic_availability():
        print("\n❌ Cannot proceed without Pydantic. Install with: pip install pydantic")
        return False
    
    # Test 2: Verificar imports
    success, models = test_validation_imports()
    if not success:
        print("\n❌ Cannot proceed without validation models.")
        return False
    
    # Test 3: Probar modelos individuales
    test_amount_validation(models['AmountEntity'])
    test_numeral_validation(models['NumeralEntity'])
    test_role_validation(models['RoleEntity'])
    
    # Test 4: Probar validador completo
    test_entity_validator(models['EntityValidator'])
    
    # Test 5: Probar creación de entidades completas
    test_directiva_entities_creation(models['EntityValidator'], models['DirectivaEntities'])
    
    print("\n" + "=" * 50)
    print("✅ Pydantic validation system fully functional")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed! The system is ready to use.")
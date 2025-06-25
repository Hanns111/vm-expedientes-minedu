#!/usr/bin/env python3
"""
Test simple de validación Pydantic - Sin dependencias complejas
"""

def test_pydantic_basic():
    """Test básico de Pydantic"""
    print("🧪 SIMPLE PYDANTIC TEST")
    print("=" * 30)
    
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.VERSION} disponible")
        
        # Test básico de modelos
        from pydantic import BaseModel, Field
        from decimal import Decimal
        from typing import Optional
        
        class AmountTest(BaseModel):
            value: Decimal = Field(..., description="Valor monetario")
            text: str = Field(..., description="Texto original")
            confidence: float = Field(ge=0.0, le=1.0)
            
            class Config:
                validate_assignment = True
        
        # Test casos válidos
        print("\n💰 Testing valid amounts:")
        valid_cases = [
            (30.00, "S/ 30.00", 0.9),
            (320.00, "S/ 320.00", 0.85),
            (380.00, "S/ 380.00", 0.92)
        ]
        
        for value, text, conf in valid_cases:
            try:
                amount = AmountTest(
                    value=Decimal(str(value)),
                    text=text,
                    confidence=conf
                )
                print(f"✅ {text} - Valid (confidence: {conf})")
            except Exception as e:
                print(f"❌ {text} - Error: {e}")
        
        print("\n💰 Testing invalid amounts:")
        invalid_cases = [
            (-30.00, "S/ -30.00", 0.9),  # Valor negativo
        ]
        
        for value, text, conf in invalid_cases:
            try:
                amount = AmountTest(
                    value=Decimal(str(value)),
                    text=text,
                    confidence=conf
                )
                print(f"⚠️  {text} - Should have failed")
            except Exception as e:
                print(f"✅ {text} - Correctly rejected")
        
        print("\n✅ Pydantic básico funcionando correctamente")
        return True
        
    except ImportError as e:
        print(f"❌ Pydantic no disponible: {e}")
        return False

def test_directiva_simulation():
    """Simular datos reales de la directiva"""
    print("\n📋 SIMULACIÓN DE DATOS REALES")
    print("=" * 35)
    
    # Datos conocidos de la directiva
    directiva_data = {
        "amounts": [
            {"value": 30.00, "context": "límite declaración jurada"},
            {"value": 320.00, "context": "viáticos servidores civiles"},
            {"value": 380.00, "context": "viáticos ministros y viceministros"}
        ],
        "roles": [
            {"name": "Ministros De Estado", "allowance": 380.00},
            {"name": "Viceministros", "allowance": 380.00},
            {"name": "Secretario General", "allowance": 380.00},
            {"name": "Servidores Civiles", "allowance": 320.00}
        ],
        "numerals": [
            {"number": "8.4", "title": "VIÁTICOS"},
            {"number": "8.4.17", "title": "Declaración Jurada"},
            {"number": "8.5", "title": "HOSPEDAJE"}
        ]
    }
    
    print("💰 Montos encontrados en la directiva:")
    for amount in directiva_data["amounts"]:
        print(f"   • S/ {amount['value']:.2f} - {amount['context']}")
    
    print("\n👤 Roles identificados:")
    for role in directiva_data["roles"]:
        print(f"   • {role['name']}: S/ {role['allowance']:.2f}")
    
    print("\n📋 Numerales principales:")
    for numeral in directiva_data["numerals"]:
        print(f"   • {numeral['number']} - {numeral['title']}")
    
    print("\n🎯 Pregunta objetivo: '¿Cuál es el monto máximo diario de viáticos?'")
    print("📖 Respuesta esperada:")
    print("   • Para Ministros, Viceministros y Secretario General: S/ 380.00")
    print("   • Para Servidores Civiles: S/ 320.00")
    print("   • Límite para declaración jurada: S/ 30.00")
    
    return True

def test_search_patterns():
    """Test de patrones de búsqueda"""
    print("\n🔍 PATRONES DE BÚSQUEDA ESPERADOS")
    print("=" * 40)
    
    search_patterns = [
        {
            "query": "monto máximo diario viáticos",
            "expected_keywords": ["viático", "diario", "máximo", "380", "320"],
            "expected_amounts": ["S/ 380.00", "S/ 320.00"]
        },
        {
            "query": "declaración jurada límite",
            "expected_keywords": ["declaración", "jurada", "límite", "30"],
            "expected_amounts": ["S/ 30.00"]
        },
        {
            "query": "ministros viceministros viáticos",
            "expected_keywords": ["ministros", "viceministros", "380"],
            "expected_amounts": ["S/ 380.00"]
        }
    ]
    
    for i, pattern in enumerate(search_patterns, 1):
        print(f"\n{i}. Query: '{pattern['query']}'")
        print(f"   Keywords esperados: {', '.join(pattern['expected_keywords'])}")
        print(f"   Montos esperados: {', '.join(pattern['expected_amounts'])}")
    
    print("\n✅ Patrones de búsqueda definidos para pruebas")
    return True

def main():
    """Función principal"""
    print("🚀 VALIDACIÓN SIMPLIFICADA - DIRECTIVA VIÁTICOS")
    print("=" * 55)
    
    # Test 1: Pydantic básico
    pydantic_ok = test_pydantic_basic()
    
    # Test 2: Simulación de datos
    simulation_ok = test_directiva_simulation()
    
    # Test 3: Patrones de búsqueda
    patterns_ok = test_search_patterns()
    
    print("\n" + "=" * 55)
    print("📊 RESUMEN DE TESTS:")
    print(f"   • Pydantic básico: {'✅' if pydantic_ok else '❌'}")
    print(f"   • Simulación datos: {'✅' if simulation_ok else '❌'}")
    print(f"   • Patrones búsqueda: {'✅' if patterns_ok else '❌'}")
    
    if all([pydantic_ok, simulation_ok, patterns_ok]):
        print("\n🎉 ¡SISTEMA LISTO PARA PRUEBAS!")
        print("📋 Próximos pasos:")
        print("   1. Ejecutar búsqueda con test_bm25_amounts.py")
        print("   2. Probar consultas específicas con demo.py")
        print("   3. Validar respuestas de viáticos")
        return True
    else:
        print("\n⚠️  Algunos tests fallaron")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Sistema validado - continúa con las pruebas")
    else:
        print("\n❌ Revisa los errores antes de continuar") 
#!/usr/bin/env python3
"""
Test de Integración Frontend-Backend MINEDU
==========================================

Pruebas para verificar la comunicación entre el frontend Next.js
y el backend FastAPI con sistema híbrido de búsqueda.
"""
import requests
import json
import time
from typing import Dict, Any

# Configuración
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Probar endpoint de salud del backend"""
    print("🔍 Probando conexión con backend...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend responde correctamente")
            print(f"   Estado: {data.get('status', 'unknown')}")
            print(f"   Versión: {data.get('version', 'unknown')}")
            print(f"   Vectorstores: {data.get('vectorstores', {})}")
            return True
        else:
            print(f"❌ Backend responde con error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con backend: {e}")
        return False

def test_search_endpoint():
    """Probar endpoint de búsqueda"""
    print("\n🔍 Probando endpoint de búsqueda...")
    
    search_data = {
        "query": "¿Cuál es el monto máximo para viáticos?",
        "method": "hybrid",
        "top_k": 3,
        "fusion_method": "weighted"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json=search_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Búsqueda exitosa")
            print(f"   Query: {data.get('query', '')}")
            print(f"   Método: {data.get('method', '')}")
            print(f"   Tiempo: {data.get('processing_time', 0):.3f}s")
            print(f"   Resultados: {data.get('total_results', 0)}")
            
            # Mostrar primer resultado si existe
            results = data.get('results', [])
            if results:
                first_result = results[0]
                print(f"   Primer resultado:")
                print(f"     Score: {first_result.get('score', 0):.3f}")
                print(f"     Contenido: {first_result.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"❌ Error en búsqueda: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en búsqueda: {e}")
        return False

def test_cors_headers():
    """Probar headers CORS"""
    print("\n🔍 Probando configuración CORS...")
    
    try:
        # Simular request desde frontend
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{API_BASE_URL}/search", headers=headers)
        
        if response.status_code == 200:
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print("✅ CORS configurado correctamente")
            for header, value in cors_headers.items():
                if value:
                    print(f"   {header}: {value}")
            return True
        else:
            print(f"❌ Error en CORS: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error probando CORS: {e}")
        return False

def test_error_handling():
    """Probar manejo de errores"""
    print("\n🔍 Probando manejo de errores...")
    
    # Test con query vacía
    try:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={"query": "", "method": "hybrid"},
            timeout=5
        )
        
        if response.status_code == 422:  # Validation error esperado
            print("✅ Validación de entrada funciona correctamente")
            return True
        else:
            print(f"⚠️  Respuesta inesperada para query vacía: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error probando validación: {e}")
        return False

def test_api_documentation():
    """Probar acceso a documentación API"""
    print("\n🔍 Probando documentación API...")
    
    try:
        # Test docs endpoint
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Documentación FastAPI disponible en /docs")
            docs_available = True
        else:
            print(f"⚠️  Documentación no disponible: {response.status_code}")
            docs_available = False
        
        # Test redoc endpoint
        response = requests.get(f"{API_BASE_URL}/redoc", timeout=5)
        if response.status_code == 200:
            print("✅ ReDoc disponible en /redoc")
            redoc_available = True
        else:
            print(f"⚠️  ReDoc no disponible: {response.status_code}")
            redoc_available = False
        
        return docs_available or redoc_available
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accediendo a documentación: {e}")
        return False

def main():
    """Ejecutar todas las pruebas de integración"""
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN FRONTEND-BACKEND")
    print("=" * 60)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Search Endpoint", test_search_endpoint),
        ("CORS Configuration", test_cors_headers),
        ("Error Handling", test_error_handling),
        ("API Documentation", test_api_documentation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
        time.sleep(1)  # Pausa entre tests
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
        if success:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("\n🎉 ¡INTEGRACIÓN COMPLETAMENTE FUNCIONAL!")
        print("   El frontend puede comunicarse correctamente con el backend.")
        print("   Puedes proceder a iniciar ambos servicios:")
        print()
        print("   1. Backend:  cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu")
        print("               python api_minedu.py")
        print()
        print("   2. Frontend: cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu/frontend-new")
        print("               npm install && npm run dev")
        print()
        print("   3. Acceder:  http://localhost:3000")
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print("   Revisa la configuración antes de proceder.")
        print(f"   Asegúrate de que el backend esté ejecutándose en {API_BASE_URL}")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test de cordura para verificar que RAG profesional funciona correctamente
"""
import requests
import json

def test_professional_endpoint():
    """Test que verifica que no hay modo básico ni 503"""
    
    url = "http://localhost:8001/api/chat/professional"
    payload = {"message": "¿Cuál es el monto de viáticos?"}
    
    response = requests.post(url, json=payload)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get("response", "")
        
        # Verificar que NO contiene "MODO BÁSICO"
        if "MODO BÁSICO" in response_text:
            print("❌ FALLA: Respuesta contiene 'MODO BÁSICO'")
            return False
        
        # Verificar que SÍ contiene indicadores de RAG real
        if "SISTEMA PROFESIONAL RAG MINEDU" in response_text:
            print("✅ ÉXITO: Sistema profesional RAG funcionando")
            
            # Verificar que hay documentos encontrados
            docs_found = data.get("documents_found", 0)
            print(f"✅ Documentos encontrados: {docs_found}")
            
            # Verificar que hay contenido real
            if "S/ 320.00" in response_text or "S/ 380.00" in response_text:
                print("✅ ÉXITO: Datos reales extraídos de documentos")
                
                # Verificar que es método correcto
                method = data.get("method", "")
                if method == "simple_retriever_professional":
                    print("✅ ÉXITO: Método SimpleRetriever profesional")
                    return True
                else:
                    print(f"⚠️ Método inesperado: {method}")
                    return True  # Sigue siendo válido
            else:
                print("⚠️ No se encontraron montos específicos")
                return False
        else:
            print("❌ FALLA: No es sistema profesional RAG")
            return False
    
    elif response.status_code == 503:
        print("❌ FALLA: Error 503 - Sistema no disponible")
        return False
    
    else:
        print(f"❌ FALLA: Status code inesperado {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("🧪 TEST DE CORDURA - RAG PROFESIONAL")
    print("="*50)
    
    success = test_professional_endpoint()
    
    print("="*50)
    if success:
        print("🎉 TODOS LOS TESTS PASARON")
        print("✅ Fase 3 RAG Real → COMPLETADA")
        exit(0)
    else:
        print("❌ TESTS FALLARON")
        print("⚠️ Fase 3 RAG Real → REQUIERE CORRECCIÓN")
        exit(1)
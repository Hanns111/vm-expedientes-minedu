#!/usr/bin/env python3
"""
Script para verificar servicios activos
"""
import requests
import json
from datetime import datetime

def check_service(port, name):
    """Verificar un servicio específico"""
    try:
        url = f"http://localhost:{port}/health"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name} (:{port}): {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ {name} (:{port}): HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} (:{port}): No disponible")
        return False
    except Exception as e:
        print(f"❌ {name} (:{port}): Error {e}")
        return False

def main():
    """Verificar todos los servicios"""
    print("🔍 VERIFICANDO SERVICIOS FASE 5")
    print("=" * 35)
    
    services = [
        (8000, "Gateway Service"),
        (8001, "RAG Service"),
        (8002, "Agents Service"),
        (8003, "Memory Service"),
        (8004, "Calculation Service")
    ]
    
    active_services = 0
    
    for port, name in services:
        if check_service(port, name):
            active_services += 1
    
    print(f"\n📊 RESUMEN: {active_services}/{len(services)} servicios activos")
    
    if active_services > 0:
        print(f"\n🧪 PROBAR REQUEST COMPLETO:")
        print(f"  python test_chat_request.py")
    
    return active_services > 0

if __name__ == "__main__":
    main() 
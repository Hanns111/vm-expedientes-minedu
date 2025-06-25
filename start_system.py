#!/usr/bin/env python3
"""
Script de inicio para el sistema MINEDU AI Frontend-Backend
===========================================================

Inicia el backend FastAPI y proporciona instrucciones para el frontend.
"""
import subprocess
import sys
import time
import requests
from pathlib import Path

def check_backend_health(max_retries=10, delay=2):
    """Verificar que el backend esté funcionando"""
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=3)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"Esperando backend... intento {i+1}/{max_retries}")
            time.sleep(delay)
    
    return False

def start_backend():
    """Iniciar el backend FastAPI"""
    print("🚀 Iniciando backend FastAPI...")
    
    try:
        # Verificar que el archivo principal existe
        api_file = Path("api_minedu.py")
        if not api_file.exists():
            print("❌ Error: api_minedu.py no encontrado")
            return False
        
        # Iniciar el backend en background
        process = subprocess.Popen([
            sys.executable, "api_minedu.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("⏳ Esperando que el backend esté listo...")
        
        if check_backend_health():
            print("✅ Backend iniciado correctamente en http://localhost:8000")
            print("📖 Documentación disponible en http://localhost:8000/docs")
            return True
        else:
            print("❌ Error: Backend no responde después de varios intentos")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        return False

def show_frontend_instructions():
    """Mostrar instrucciones para el frontend"""
    print("\n" + "="*60)
    print("📱 INSTRUCCIONES PARA EL FRONTEND")
    print("="*60)
    
    frontend_path = Path("frontend-new")
    
    if frontend_path.exists():
        print("✅ Directorio frontend encontrado")
        print("\n🔧 Para iniciar el frontend, ejecuta en otra terminal:")
        print(f"   cd {frontend_path.absolute()}")
        print("   npm install")
        print("   npm run dev")
        print()
        print("🌐 Una vez iniciado, accede a: http://localhost:3000")
    else:
        print("❌ Directorio frontend-new no encontrado")
        print("   Asegúrate de que el frontend esté en ./frontend-new/")

def show_system_status():
    """Mostrar el estado del sistema"""
    print("\n" + "="*60)
    print("📊 ESTADO DEL SISTEMA")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend: FUNCIONANDO")
            print(f"   Estado: {data.get('status', 'unknown')}")
            print(f"   Versión: {data.get('version', 'unknown')}")
            
            vectorstores = data.get('vectorstores', {})
            print(f"   Vectorstores disponibles:")
            for name, available in vectorstores.items():
                status = "✅" if available else "❌"
                print(f"     {status} {name}")
                
            if not any(vectorstores.values()):
                print("\n⚠️  ADVERTENCIA: No hay vectorstores disponibles")
                print("   Las búsquedas podrían fallar. Ejecuta:")
                print("   python src/data_pipeline/generate_vectorstores.py")
        else:
            print("❌ Backend: ERROR DE CONEXIÓN")
    except:
        print("❌ Backend: NO RESPONDE")

def main():
    """Función principal"""
    print("🎯 MINEDU AI - SISTEMA HÍBRIDO DE BÚSQUEDA")
    print("=" * 60)
    print("Iniciando sistema completo Frontend + Backend...")
    print()
    
    # Verificar Python
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detectado")
    
    # Iniciar backend
    if not start_backend():
        print("\n❌ No se pudo iniciar el backend. Verifica:")
        print("   • Que todas las dependencias estén instaladas")
        print("   • Que no haya otro proceso usando el puerto 8000")
        print("   • Ejecuta: pip install -r requirements.txt")
        sys.exit(1)
    
    # Mostrar estado
    show_system_status()
    
    # Mostrar instrucciones para frontend
    show_frontend_instructions()
    
    print("\n" + "="*60)
    print("🎉 SISTEMA LISTO PARA USAR")
    print("="*60)
    print("📝 PRÓXIMOS PASOS:")
    print("   1. Inicia el frontend siguiendo las instrucciones arriba")
    print("   2. Accede a http://localhost:3000")
    print("   3. Prueba la búsqueda híbrida con consultas como:")
    print("      '¿Cuál es el monto máximo para viáticos?'")
    print()
    print("🔧 COMANDOS ÚTILES:")
    print("   • Documentación API: http://localhost:8000/docs")
    print("   • Test integración: python test_integration.py")
    print("   • Detener backend: Ctrl+C")
    print()
    print("💡 El backend seguirá ejecutándose en background...")
    
    # Mantener el script activo
    try:
        print("\n⏸️  Presiona Ctrl+C para detener el backend...")
        while True:
            time.sleep(60)
            # Verificar que el backend siga activo
            if not check_backend_health(max_retries=1):
                print("⚠️  Backend desconectado")
                break
    except KeyboardInterrupt:
        print("\n👋 Deteniendo sistema...")

if __name__ == "__main__":
    main()
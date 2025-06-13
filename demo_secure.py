#!/usr/bin/env python
"""
Demo SEGURO del Sistema de Búsqueda Híbrido MINEDU
Uso: python demo_secure.py "tu consulta aquí"
"""
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from src.core.secure_search import SecureHybridSearch
    from src.core.security.logger import app_logger
    print("✅ Módulos de seguridad importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def main():
    """Demo con todas las medidas de seguridad"""
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python demo_secure.py 'tu consulta aquí'")
        print("Ejemplo: python demo_secure.py '¿Cuál es el monto máximo para viáticos?'")
        return
    
    query = " ".join(sys.argv[1:])
    
    # Simular datos de usuario (en producción vendrían de la sesión)
    user_id = "demo_user_001"
    ip_address = "127.0.0.1"
    session_id = "demo_session_001"
    
    print(f"\n🔒 Búsqueda SEGURA: {query}")
    print("-" * 50)
    
    try:
        print("🔄 Inicializando búsqueda segura...")
        # Inicializar búsqueda segura
        searcher = SecureHybridSearch()
        
        print("🔍 Realizando búsqueda con validaciones de seguridad...")
        # Realizar búsqueda
        results, error_msg = searcher.search(
            query=query,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            top_k=3
        )
        
        if error_msg:
            print(f"\n❌ Error: {error_msg}")
            return
        
        # Mostrar resultados
        print(f"\n📊 Encontrados {len(results)} resultados seguros:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.3f} | Método: {result['method']}")
            print(f"   {result['text'][:200]}...")
            print()
        
        print("✅ Búsqueda completada de forma segura")
        print("🔒 Todas las medidas de seguridad aplicadas:")
        print("   - Validación de entrada")
        print("   - Rate limiting")
        print("   - Monitoreo de amenazas")
        print("   - Sanitización de resultados")
        print("   - Logging seguro")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
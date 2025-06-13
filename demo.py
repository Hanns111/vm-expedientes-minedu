#!/usr/bin/env python
"""
Demo clásico del Sistema de Búsqueda Híbrido MINEDU (ahora con rutas seguras)
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config.security_config import SecurityConfig
from src.core.secure_search import SecureHybridSearch

def main():
    if len(sys.argv) < 2:
        print("Uso: python demo.py 'tu consulta aquí'")
        return
    query = " ".join(sys.argv[1:])
    user_id = "demo_user_001"
    ip_address = "127.0.0.1"
    session_id = "demo_session_001"
    print(f"\n🔒 Búsqueda SEGURA: {query}")
    print("-" * 50)
    searcher = SecureHybridSearch()
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
    print(f"\n📊 Encontrados {len(results)} resultados seguros:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.3f} | Método: {result['method']}")
        print(f"   {result['text'][:200]}...")
        print()
    print("✅ Búsqueda completada de forma segura")

if __name__ == "__main__":
    main()

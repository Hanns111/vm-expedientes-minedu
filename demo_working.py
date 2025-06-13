#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo extendido del Sistema de Búsqueda Híbrido MINEDU (rutas seguras)

Este demo usa los archivos existentes que ya funcionan correctamente.
Uso: python demo_working.py "tu consulta aquí"
"""
import sys
import time
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config.security_config import SecurityConfig
from src.core.secure_search import SecureHybridSearch

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("🚀 DEMO FUNCIONAL - Sistema de Búsqueda Híbrido MINEDU")
        print("=" * 60)
        print("Uso: python demo_working.py 'tu consulta aquí'")
        print("\n📝 Consultas de ejemplo:")
        print("  - ¿Cuál es el monto máximo diario para viáticos nacionales?")
        print("  - ¿Quién autoriza los viáticos en el MINEDU?")
        print("  - ¿Qué documentos se requieren para solicitar viáticos?")
        print("  - ¿Cuántos días antes debo solicitar viáticos?")
        print("  - ¿Cómo se rinden los gastos de viáticos?")
        print("  - ¿Cuáles son las responsabilidades del comisionado?")
        print("  - ¿Qué sucede si no rindo mis viáticos a tiempo?")
        print("  - ¿Se pueden solicitar viáticos para viajes internacionales?")
        return
    
    query = " ".join(sys.argv[1:])
    user_id = "demo_user_001"
    ip_address = "127.0.0.1"
    session_id = "demo_session_001"
    
    print(f"\n🔒 Búsqueda SEGURA: {query}")
    print("-" * 50)
    
    try:
        searcher = SecureHybridSearch()
        results, error_msg = searcher.search(
            query=query,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            top_k=5
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
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verificando estado del proyecto...")
        
        # Verificar archivos clave
        key_files = [
            "src/ai/search_vectorstore_bm25_fixed.py",
            "src/ai/search_vectorstore_hybrid.py",
            "data/processed/vectorstore_bm25_test.pkl",
            "data/processed/vectorstore_semantic_full_v2.pkl"
        ]
        
        print("\n📋 Estado de archivos clave:")
        for file_path in key_files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")

if __name__ == "__main__":
    main() 
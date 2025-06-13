#!/usr/bin/env python
"""
Inspección segura de vectorstore usando rutas centralizadas
"""
from src.core.config.security_config import SecurityConfig
import pickle
from pathlib import Path

def main():
    path = SecurityConfig.VECTORSTORE_PATH
    print(f"Inspeccionando vectorstore seguro: {path}")
    if not Path(path).exists():
        print("❌ Vectorstore no encontrado.")
        return
    with open(path, 'rb') as f:
        data = pickle.load(f)
    print(f"Claves en el vectorstore: {list(data.keys())}")
    print(f"Total de elementos: {len(data.get('chunks', []))}")

if __name__ == "__main__":
    main()

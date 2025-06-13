#!/usr/bin/env python
"""
Búsqueda semántica usando rutas seguras con validación de pickle
"""
from src.core.config.security_config import SecurityConfig
from src.core.security.file_validator import FileValidator
from src.core.security.input_validator import InputValidator, SecurityError
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

def safe_load_pickle(file_path: Path):
    """
    Carga un archivo pickle de forma segura con validación
    """
    # Validar archivo antes de cargar
    is_valid, error_msg = FileValidator.validate_file(file_path)
    if not is_valid:
        raise SecurityError(f"Archivo no válido: {error_msg}")
    
    # Calcular hash para verificación de integridad
    file_hash = FileValidator.calculate_file_hash(file_path)
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    # Validar estructura del vectorstore
    required_keys = ['index', 'embeddings', 'chunks']
    for key in required_keys:
        if key not in data:
            raise SecurityError(f"Vectorstore inválido: falta la clave '{key}'")
    
    return data, file_hash

def main():
    path = SecurityConfig.VECTORSTORE_PATH
    print(f"Usando vectorstore seguro: {path}")
    
    if not Path(path).exists():
        print("❌ Vectorstore no encontrado.")
        return
    
    try:
        # Cargar vectorstore de forma segura
        data, file_hash = safe_load_pickle(path)
        print(f"✅ Vectorstore cargado de forma segura (hash: {file_hash[:16]}...)")
        print(f"Claves en el vectorstore: {list(data.keys())}")
    except SecurityError as e:
        print(f"❌ Error de seguridad: {e}")
        return
    except Exception as e:
        print(f"❌ Error al cargar vectorstore: {e}")
        return

    index = data["index"]
    embeddings = data["embeddings"]
    chunks = data["chunks"]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    try:
        query = input("Ingrese la consulta: ")
        # Sanitizar entrada del usuario
        clean_query = InputValidator.sanitize_query(query)
        if clean_query != query:
            print("⚠️  Consulta sanitizada por seguridad")
        
        query_embedding = model.encode([clean_query])
        distances, indices = index.kneighbors(query_embedding)

        results = []
        for rank, idx in enumerate(indices[0]):
            results.append({
                "rank": rank + 1,
                "similarity": 1 - distances[0][rank],
                "text": chunks[idx]["texto"]
            })

        print("\n📌 Resultados más cercanos:")
        for res in results:
            print(f"\n#{res['rank']} – (similitud: {res['similarity']:.2f})")
            print(res["text"][:1000])  # muestra los primeros 1000 caracteres
            
    except SecurityError as e:
        print(f"❌ Consulta no válida: {e}")
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")

if __name__ == "__main__":
    main()

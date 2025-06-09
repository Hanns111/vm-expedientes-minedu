#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Script mínimo para expansión del dataset
def minimal_expansion():
    # Buscar dataset actual
    dataset_paths = [
        "data/golden_dataset.json", 
        "golden_dataset.json", 
        "paper_cientifico/dataset/golden_dataset.json",
        "paper_cientifico/dataset/golden_dataset_expanded.json"
    ]
    
    current_dataset = None
    dataset_path = None
    
    for path in dataset_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    current_dataset = json.load(f)
                dataset_path = path
                print(f"[OK] Dataset encontrado: {path} ({len(current_dataset)} preguntas)")
                break
            except Exception as e:
                print(f"[ERROR] Error en {path}: {e}")
    
    if current_dataset is None:
        print("[ERROR] No se pudo cargar el dataset actual")
        return False
    
    # Una sola pregunta de prueba
    test_question = {
        "query_id": f"{len(current_dataset) + 1:04d}",
        "question": "¿Qué pasa si no se presenta la rendición de cuentas a tiempo?",
        "category": "procedures",
        "query_type": "consequence",
        "difficulty": "medium",
        "ground_truth_answer": "Se aplicará recuperación de viáticos según artículo 8.7",
        "supporting_chunks": ["chunk_test"],
        "metadata": {
            "entities_required": ["rendicion", "plazo"],
            "context_type": "specific"
        }
    }
    
    # Combinar
    expanded_dataset = current_dataset + [test_question]
    
    # Guardar con backup
    backup_path = f"{dataset_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(current_dataset, f, indent=2, ensure_ascii=False)
        print(f"[OK] Backup creado: {backup_path}")
        
        # Guardar expandido
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(expanded_dataset, f, indent=2, ensure_ascii=False)
        print(f"[OK] Dataset expandido guardado: {len(expanded_dataset)} preguntas")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error guardando: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] EXPANSIÓN MÍNIMA DE PRUEBA")
    print("=" * 40)
    if minimal_expansion():
        print("[OK] Expansión mínima exitosa")
    else:
        print("[ERROR] Expansión mínima falló")

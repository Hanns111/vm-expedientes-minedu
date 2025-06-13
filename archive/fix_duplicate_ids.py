#!/usr/bin/env python3
"""
Script para corregir IDs duplicados en las preguntas adicionales
"""

import json
import os

# CONFIGURACIÓN
DATASET_PATH = "paper_cientifico/dataset/golden_dataset.json"
ADDITIONAL_QUESTIONS_PATH = "paper_cientifico/dataset/additional_questions_19.json"
FIXED_QUESTIONS_PATH = "paper_cientifico/dataset/additional_questions_19_fixed.json"

def fix_duplicate_ids():
    print("[INFO] Corrigiendo IDs duplicados en preguntas adicionales...")
    
    # Cargar dataset actual
    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            current_dataset = json.load(f)
        print(f"[OK] Dataset actual cargado: {len(current_dataset)} preguntas")
    except Exception as e:
        print(f"[ERROR] Error cargando dataset actual: {e}")
        return False
    
    # Cargar preguntas adicionales
    try:
        with open(ADDITIONAL_QUESTIONS_PATH, 'r', encoding='utf-8') as f:
            additional_questions = json.load(f)
        print(f"[OK] Preguntas adicionales cargadas: {len(additional_questions)} preguntas")
    except Exception as e:
        print(f"[ERROR] Error cargando preguntas adicionales: {e}")
        return False
    
    # Obtener IDs actuales
    current_ids = set(q['query_id'] for q in current_dataset)
    print(f"[INFO] IDs en dataset actual: {sorted(list(current_ids))}")
    
    # Encontrar el ID más alto en el dataset actual
    max_id = 0
    for q in current_dataset:
        try:
            id_num = int(q['query_id'])
            max_id = max(max_id, id_num)
        except ValueError:
            # Si hay IDs que no son numéricos, los ignoramos
            pass
    
    print(f"[INFO] ID más alto en dataset actual: {max_id}")
    
    # Corregir IDs en preguntas adicionales
    for i, question in enumerate(additional_questions):
        new_id = str(max_id + i + 1).zfill(4)
        old_id = question['query_id']
        question['query_id'] = new_id
        print(f"[INFO] Cambiando ID: {old_id} -> {new_id}")
    
    # Guardar preguntas adicionales con IDs corregidos
    try:
        with open(FIXED_QUESTIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(additional_questions, f, indent=2, ensure_ascii=False)
        print(f"[OK] Preguntas adicionales con IDs corregidos guardadas: {FIXED_QUESTIONS_PATH}")
        return True
    except Exception as e:
        print(f"[ERROR] Error guardando preguntas adicionales corregidas: {e}")
        return False

if __name__ == "__main__":
    print("[INFO] CORRECCIÓN DE IDs DUPLICADOS")
    print("=" * 40)
    
    if fix_duplicate_ids():
        print("[OK] Corrección de IDs completada exitosamente")
        print("[INFO] Ahora puedes ejecutar part3a_combine_and_validate.py nuevamente")
    else:
        print("[ERROR] Corrección de IDs falló")

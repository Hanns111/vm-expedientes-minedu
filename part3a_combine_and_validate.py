#!/usr/bin/env python3
"""
PARTE 3A: Combinación y Validación del Dataset Expandido
Combina dataset actual con preguntas adicionales y valida resultado
"""

import json
import os
from datetime import datetime
from collections import Counter

# CONFIGURACIÓN
DATASET_PATH = "paper_cientifico/dataset/golden_dataset.json"
ADDITIONAL_QUESTIONS_PATH = "paper_cientifico/dataset/additional_questions_19_fixed.json"
BACKUP_DIR = "paper_cientifico/dataset/backups"
TEMP_EXPANDED_PATH = "paper_cientifico/dataset/temp_expanded_dataset.json"

def load_datasets():
    """Cargar dataset actual y preguntas adicionales"""
    print("[INFO] Cargando datasets...")
    
    # Cargar dataset actual
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] No se encontró dataset actual: {DATASET_PATH}")
        return None, None
    
    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            current_dataset = json.load(f)
        print(f"[OK] Dataset actual cargado: {len(current_dataset)} preguntas")
    except Exception as e:
        print(f"[ERROR] Error cargando dataset actual: {e}")
        return None, None
    
    # Cargar preguntas adicionales
    if not os.path.exists(ADDITIONAL_QUESTIONS_PATH):
        print(f"[ERROR] No se encontraron preguntas adicionales: {ADDITIONAL_QUESTIONS_PATH}")
        print(f"[INFO] Verificar que se ejecutaron partes 2A y 2B correctamente")
        return None, None
    
    try:
        with open(ADDITIONAL_QUESTIONS_PATH, 'r', encoding='utf-8') as f:
            additional_questions = json.load(f)
        print(f"[OK] Preguntas adicionales cargadas: {len(additional_questions)} preguntas")
    except Exception as e:
        print(f"[ERROR] Error cargando preguntas adicionales: {e}")
        return None, None
    
    return current_dataset, additional_questions

def validate_combination(current_dataset, additional_questions):
    """Validar que la combinación sea válida"""
    print("[INFO] Validando combinación...")
    
    # Verificar IDs únicos
    current_ids = set(q['query_id'] for q in current_dataset)
    additional_ids = set(q['query_id'] for q in additional_questions)
    
    duplicates = current_ids & additional_ids
    if duplicates:
        print(f"[ERROR] IDs duplicados encontrados: {duplicates}")
        return False
    
    print(f"[INFO] IDs actuales: {sorted(list(current_ids))}")
    print(f"[INFO] IDs adicionales: {sorted(list(additional_ids))}")
    
    # Verificar estructura
    required_fields = ['query_id', 'question', 'category', 'ground_truth_answer', 'supporting_chunks']
    
    for dataset, name in [(current_dataset, "actual"), (additional_questions, "adicionales")]:
        for i, q in enumerate(dataset):
            for field in required_fields:
                if field not in q:
                    print(f"[ERROR] Campo faltante '{field}' en dataset {name}, pregunta {i+1}")
                    return False
            
            # Verificar que query_type y difficulty estén en el lugar correcto
            # Pueden estar directamente en el objeto o dentro de metadata
            if 'query_type' not in q and ('metadata' not in q or 'query_type' not in q.get('metadata', {})):
                print(f"[ERROR] Campo 'query_type' faltante en dataset {name}, pregunta {i+1}")
                return False
            
            if 'difficulty' not in q and ('metadata' not in q or 'difficulty' not in q.get('metadata', {})):
                print(f"[ERROR] Campo 'difficulty' faltante en dataset {name}, pregunta {i+1}")
                return False
    
    print(f"[OK] Validación exitosa - Sin conflictos")
    return True

def combine_datasets(current_dataset, additional_questions):
    """Combinar datasets y mostrar estadísticas"""
    print("[INFO] Combinando datasets...")
    
    # Combinar
    expanded_dataset = current_dataset + additional_questions
    
    # Estadísticas antes y después
    # Manejar tanto query_type directo como dentro de metadata
    def get_query_type(q):
        if 'query_type' in q:
            return q['query_type']
        elif 'metadata' in q and 'query_type' in q['metadata']:
            return q['metadata']['query_type']
        return "unknown"
    
    current_types = Counter(get_query_type(q) for q in current_dataset)
    additional_types = Counter(get_query_type(q) for q in additional_questions)
    final_types = Counter(get_query_type(q) for q in expanded_dataset)
    
    print(f"[INFO] ESTADÍSTICAS DE COMBINACIÓN:")
    print(f"  Dataset original: {len(current_dataset)} preguntas")
    print(f"    {dict(current_types)}")
    print(f"  Preguntas adicionales: {len(additional_questions)} preguntas")
    print(f"    {dict(additional_types)}")
    print(f"  Dataset final: {len(expanded_dataset)} preguntas")
    print(f"    {dict(final_types)}")
    
    return expanded_dataset

def validate_scientific_criteria(expanded_dataset):
    """Validar criterios científicos del dataset final"""
    print("[INFO] Validando criterios científicos...")
    
    # Manejar tanto query_type directo como dentro de metadata
    def get_query_type(q):
        if 'query_type' in q:
            return q['query_type']
        elif 'metadata' in q and 'query_type' in q['metadata']:
            return q['metadata']['query_type']
        return "unknown"
    
    # Manejar tanto difficulty directo como dentro de metadata
    def get_difficulty(q):
        if 'difficulty' in q:
            return q['difficulty']
        elif 'metadata' in q and 'difficulty' in q['metadata']:
            return q['metadata']['difficulty']
        return "unknown"
    
    query_types = Counter(get_query_type(q) for q in expanded_dataset)
    categories = Counter(q['category'] for q in expanded_dataset)
    difficulties = Counter(get_difficulty(q) for q in expanded_dataset)
    
    # Criterios de validación
    validation_results = []
    all_passed = True
    
    # 1. Suficientes preguntas consequence
    consequence_count = query_types.get('consequence', 0)
    if consequence_count >= 5:
        validation_results.append(f"[OK] Preguntas consequence: {consequence_count} >= 5")
    else:
        validation_results.append(f"[ERROR] Preguntas consequence: {consequence_count} < 5")
        all_passed = False
    
    # 2. Tamaño mínimo del dataset
    if len(expanded_dataset) >= 35:
        validation_results.append(f"[OK] Tamaño dataset: {len(expanded_dataset)} >= 35")
    else:
        validation_results.append(f"[ERROR] Tamaño dataset: {len(expanded_dataset)} < 35")
        all_passed = False
    
    # 3. Diversidad de categorías
    if len(categories) >= 4:
        validation_results.append(f"[OK] Diversidad categorías: {len(categories)} >= 4")
    else:
        validation_results.append(f"[ERROR] Diversidad categorías: {len(categories)} < 4")
        all_passed = False
    
    # 4. Diversidad de tipos
    if len(query_types) >= 4:
        validation_results.append(f"[OK] Diversidad tipos: {len(query_types)} >= 4")
    else:
        validation_results.append(f"[ERROR] Diversidad tipos: {len(query_types)} < 4")
        all_passed = False
    
    # Mostrar resultados
    for result in validation_results:
        print(f"  {result}")
    
    return all_passed, validation_results

def save_temp_dataset(expanded_dataset):
    """Guardar dataset expandido temporalmente"""
    print("[INFO] Guardando dataset expandido temporal...")
    
    try:
        os.makedirs(os.path.dirname(TEMP_EXPANDED_PATH), exist_ok=True)
        
        with open(TEMP_EXPANDED_PATH, 'w', encoding='utf-8') as f:
            json.dump(expanded_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Dataset temporal guardado: {TEMP_EXPANDED_PATH}")
        print(f"[INFO] Total preguntas: {len(expanded_dataset)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error guardando dataset temporal: {e}")
        return False

def main_part3a():
    """Ejecutar Parte 3A: Combinación y validación"""
    print("[INFO] PARTE 3A: COMBINACIÓN Y VALIDACIÓN")
    print("[INFO] Combinando datasets y validando resultado científico")
    print("=" * 55)
    
    # Paso 1: Cargar datasets
    current_dataset, additional_questions = load_datasets()
    if not current_dataset or not additional_questions:
        print("[ERROR] No se pudieron cargar los datasets")
        return False
    
    # Paso 2: Validar combinación
    if not validate_combination(current_dataset, additional_questions):
        print("[ERROR] Validación de combinación falló")
        return False
    
    # Paso 3: Combinar datasets
    expanded_dataset = combine_datasets(current_dataset, additional_questions)
    
    # Paso 4: Validar criterios científicos
    is_valid, validation_results = validate_scientific_criteria(expanded_dataset)
    if not is_valid:
        print("[ERROR] Dataset no pasa validación científica")
        return False
    
    # Paso 5: Guardar dataset temporal
    if not save_temp_dataset(expanded_dataset):
        print("[ERROR] No se pudo guardar dataset temporal")
        return False
    
    print(f"\n[OK] PARTE 3A COMPLETADA EXITOSAMENTE")
    print(f"[INFO] Dataset combinado: {len(expanded_dataset)} preguntas")
    print(f"[INFO] Validación científica: APROBADA")
    print(f"[INFO] Ejecutar part3b_finalize_and_report.py")
    
    return True

if __name__ == "__main__":
    if main_part3a():
        print(f"\n[OK] ¡Parte 3A exitosa! Continuar con Parte 3B.")
    else:
        print(f"\n[ERROR] Parte 3A falló. Revisar errores arriba.")

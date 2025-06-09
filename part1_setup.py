#!/usr/bin/env python3
"""
PARTE 1: Configuración y Setup para Expansión del Golden Dataset
Basado en diagnóstico exitoso del proyecto MINEDU RAG

Dataset actual: paper_cientifico/dataset/golden_dataset.json (20 preguntas)
Objetivo: Preparar para expansión a 39 preguntas
"""

import json
import os
from datetime import datetime
from collections import Counter
from pathlib import Path

# CONFIGURACIÓN BASADA EN DIAGNÓSTICO
DATASET_PATH = "paper_cientifico/dataset/golden_dataset.json"
BACKUP_DIR = "paper_cientifico/dataset/backups"
REPORTS_DIR = "paper_cientifico/reports"

def setup_directories():
    """Crear directorios necesarios"""
    print("[INFO] Configurando directorios...")
    
    dirs_to_create = [BACKUP_DIR, REPORTS_DIR]
    
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"[OK] Directorio creado: {dir_path}")
        else:
            print(f"[OK] Directorio existe: {dir_path}")

def load_current_dataset():
    """Cargar dataset actual con validación"""
    print("[INFO] Cargando dataset actual...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Error: No se encontró {DATASET_PATH}")
        return None
    
    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"[OK] Dataset cargado: {len(dataset)} preguntas")
        
        # Mostrar distribución actual
        query_types = Counter(q.get('metadata', {}).get('query_type', 'unknown') for q in dataset)
        print(f"[INFO] Distribución actual: {dict(query_types)}")
        
        return dataset
        
    except Exception as e:
        print(f"[ERROR] Error cargando dataset: {e}")
        return None

def create_backup(dataset):
    """Crear backup con timestamp"""
    print("[INFO] Creando backup...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{BACKUP_DIR}/golden_dataset_backup_{timestamp}.json"
    
    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Backup creado: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"[ERROR] Error creando backup: {e}")
        return None

def analyze_current_dataset(dataset):
    """Analizar dataset actual para identificar gaps"""
    print("[INFO] Analizando dataset actual...")
    
    if not dataset:
        return False
    
    # Análisis de distribución
    query_types = Counter(q.get('metadata', {}).get('query_type', 'unknown') for q in dataset)
    categories = Counter(q.get('category', 'unknown') for q in dataset)
    difficulties = Counter(q.get('metadata', {}).get('difficulty', 'unknown') for q in dataset)
    
    print(f"[INFO] Estadísticas actuales:")
    print(f"  Total preguntas: {len(dataset)}")
    print(f"  Tipos: {dict(query_types)}")
    print(f"  Categorías: {dict(categories)}")
    print(f"  Dificultades: {dict(difficulties)}")
    
    # Identificar problemas
    problems = []
    
    # Verificar preguntas consequence
    consequence_count = query_types.get('consequence', 0)
    if consequence_count < 5:
        problems.append(f"Insuficientes preguntas 'consequence': {consequence_count} (necesita >=5)")
    
    # Verificar tamaño total
    if len(dataset) < 35:
        problems.append(f"Dataset pequeño: {len(dataset)} preguntas (objetivo: 35+)")
    
    if problems:
        print(f"[ADVERTENCIA] Problemas identificados:")
        for problem in problems:
            print(f"  - {problem}")
        return False
    else:
        print(f"[OK] Dataset en buen estado")
        return True

def main_part1():
    """Ejecutar Parte 1: Setup y análisis"""
    print("[INFO] PARTE 1: SETUP Y CONFIGURACIÓN")
    print("[INFO] Preparando expansión del Golden Dataset")
    print("=" * 50)
    
    # Paso 1: Setup directorios
    setup_directories()
    
    # Paso 2: Cargar dataset actual
    current_dataset = load_current_dataset()
    if not current_dataset:
        print("[ERROR] No se puede continuar sin dataset actual")
        return None
    
    # Paso 3: Crear backup
    backup_path = create_backup(current_dataset)
    if not backup_path:
        print("[ERROR] No se pudo crear backup")
        return None
    
    # Paso 4: Analizar dataset
    is_healthy = analyze_current_dataset(current_dataset)
    
    print(f"\n[OK] PARTE 1 COMPLETADA")
    print(f"[INFO] Dataset actual: {len(current_dataset)} preguntas")
    print(f"[INFO] Backup en: {backup_path}")
    print(f"[INFO] Listo para Parte 2: Definición de preguntas adicionales")
    
    return current_dataset

if __name__ == "__main__":
    dataset = main_part1()
    if dataset:
        print(f"\n[OK] ¡Parte 1 exitosa! Ejecutar parte2_additional_questions.py")
    else:
        print(f"\n[ERROR] Parte 1 falló. Revisar errores arriba.")

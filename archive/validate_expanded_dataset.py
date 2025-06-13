#!/usr/bin/env python3
"""
Script de Validación Completa del Golden Dataset Expandido
Verifica que la expansión del dataset fue exitosa y cumple criterios científicos

OBJETIVO: Validar que el proceso de expansión en 5 partes funcionó correctamente
RESULTADO ESPERADO: Dataset con 40 preguntas, incluyendo suficientes preguntas 'consequence'
"""

import json
import os
from collections import Counter
from pathlib import Path

def print_header(title):
    """Imprimir encabezado con formato"""
    print(f"\n{'='*60}")
    print(f"[INFO] {title}")
    print(f"{'='*60}")

def check_file_structure():
    """Verificar estructura de archivos generados"""
    print_header("VERIFICACIÓN DE ESTRUCTURA DE ARCHIVOS")
    
    expected_files = {
        "paper_cientifico/dataset/golden_dataset.json": "Dataset expandido final",
        "paper_cientifico/dataset/additional_questions_19_fixed.json": "Preguntas adicionales",
        "paper_cientifico/dataset/backups/": "Directorio de backups",
        "paper_cientifico/reports/": "Directorio de reportes"
    }
    
    results = {}
    
    for file_path, description in expected_files.items():
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"[OK] {description}: {file_path} ({size} bytes)")
                results[file_path] = True
            else:  # Es directorio
                files_in_dir = list(Path(file_path).glob("*"))
                print(f"[OK] {description}: {file_path} ({len(files_in_dir)} archivos)")
                results[file_path] = True
        else:
            print(f"[ERROR] {description}: {file_path} - NO ENCONTRADO")
            results[file_path] = False
    
    return results

def load_and_validate_dataset():
    """Cargar y validar el dataset expandido"""
    print_header("CARGA Y VALIDACIÓN DEL DATASET")
    
    dataset_path = "paper_cientifico/dataset/golden_dataset.json"
    
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset no encontrado: {dataset_path}")
        return None
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"[OK] Dataset cargado exitosamente")
        print(f"[INFO] Total preguntas: {len(dataset)}")
        
        return dataset
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error de formato JSON: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error cargando dataset: {e}")
        return None

def analyze_dataset_distribution(dataset):
    """Analizar distribución del dataset"""
    print_header("ANÁLISIS DE DISTRIBUCIÓN")
    
    if not dataset:
        print("[ERROR] No hay dataset para analizar")
        return None
    
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
    
    # Contar distribuciones
    query_types = Counter(get_query_type(q) for q in dataset)
    categories = Counter(q['category'] for q in dataset)
    difficulties = Counter(get_difficulty(q) for q in dataset)
    
    print(f"[INFO] DISTRIBUCIÓN DE TIPOS DE CONSULTA:")
    for qtype, count in query_types.most_common():
        percentage = (count / len(dataset)) * 100
        print(f"  {qtype}: {count} preguntas ({percentage:.1f}%)")
    
    print(f"\n[INFO] DISTRIBUCIÓN DE CATEGORÍAS:")
    for category, count in categories.most_common():
        percentage = (count / len(dataset)) * 100
        print(f"  {category}: {count} preguntas ({percentage:.1f}%)")
    
    print(f"\n[INFO] DISTRIBUCIÓN DE DIFICULTADES:")
    for difficulty, count in difficulties.most_common():
        percentage = (count / len(dataset)) * 100
        print(f"  {difficulty}: {count} preguntas ({percentage:.1f}%)")
    
    return {
        'query_types': query_types,
        'categories': categories, 
        'difficulties': difficulties
    }

def validate_scientific_criteria(dataset, distributions):
    """Validar criterios científicos"""
    print_header("VALIDACIÓN DE CRITERIOS CIENTÍFICOS")
    
    if not dataset or not distributions:
        print("[ERROR] No hay datos para validar")
        return False
    
    query_types = distributions['query_types']
    categories = distributions['categories']
    
    validation_results = []
    all_passed = True
    
    # Criterio 1: Tamaño mínimo del dataset
    min_size = 35
    if len(dataset) >= min_size:
        validation_results.append(f"[OK] Tamaño del dataset: {len(dataset)} >= {min_size}")
    else:
        validation_results.append(f"[ERROR] Tamaño del dataset: {len(dataset)} < {min_size}")
        all_passed = False
    
    # Criterio 2: Suficientes preguntas consequence (objetivo crítico)
    min_consequence = 5
    consequence_count = query_types.get('consequence', 0)
    if consequence_count >= min_consequence:
        validation_results.append(f"[OK] Preguntas consequence: {consequence_count} >= {min_consequence}")
    else:
        validation_results.append(f"[ERROR] Preguntas consequence: {consequence_count} < {min_consequence}")
        all_passed = False
    
    # Criterio 3: Diversidad de tipos de consulta
    min_types = 4
    type_count = len(query_types)
    if type_count >= min_types:
        validation_results.append(f"[OK] Diversidad de tipos: {type_count} >= {min_types}")
    else:
        validation_results.append(f"[ERROR] Diversidad de tipos: {type_count} < {min_types}")
        all_passed = False
    
    # Criterio 4: Diversidad de categorías
    min_categories = 4
    category_count = len(categories)
    if category_count >= min_categories:
        validation_results.append(f"[OK] Diversidad de categorías: {category_count} >= {min_categories}")
    else:
        validation_results.append(f"[ERROR] Diversidad de categorías: {category_count} < {min_categories}")
        all_passed = False
    
    # Mostrar resultados
    for result in validation_results:
        print(f"  {result}")
    
    return all_passed

def validate_data_quality(dataset):
    """Validar calidad de los datos"""
    print_header("VALIDACIÓN DE CALIDAD DE DATOS")
    
    if not dataset:
        print("[ERROR] No hay dataset para validar")
        return False
    
    # Verificar estructura de preguntas
    required_fields = ['query_id', 'question', 'category', 'ground_truth_answer', 'supporting_chunks']
    
    structural_issues = []
    
    for i, question in enumerate(dataset):
        for field in required_fields:
            if field not in question:
                structural_issues.append(f"Pregunta {i+1}: campo faltante '{field}'")
        
        # Verificar que query_type y difficulty estén en el lugar correcto
        if 'query_type' not in question and ('metadata' not in question or 'query_type' not in question.get('metadata', {})):
            structural_issues.append(f"Pregunta {i+1}: campo faltante 'query_type'")
        
        if 'difficulty' not in question and ('metadata' not in question or 'difficulty' not in question.get('metadata', {})):
            structural_issues.append(f"Pregunta {i+1}: campo faltante 'difficulty'")
    
    if structural_issues:
        print(f"[ERROR] Problemas estructurales encontrados:")
        for issue in structural_issues[:5]:  # Mostrar solo primeros 5
            print(f"  - {issue}")
        if len(structural_issues) > 5:
            print(f"  ... y {len(structural_issues) - 5} más")
        return False
    else:
        print(f"[OK] Estructura de datos: Todas las preguntas tienen campos requeridos")
    
    # Verificar IDs únicos
    ids = [q['query_id'] for q in dataset]
    if len(ids) == len(set(ids)):
        print(f"[OK] IDs únicos: Todos los {len(ids)} IDs son únicos")
    else:
        duplicates = len(ids) - len(set(ids))
        print(f"[ERROR] IDs únicos: {duplicates} IDs duplicados encontrados")
        return False
    
    # Verificar longitud de respuestas
    answer_lengths = [len(q['ground_truth_answer'].split()) for q in dataset]
    avg_length = sum(answer_lengths) / len(answer_lengths)
    min_length = min(answer_lengths)
    max_length = max(answer_lengths)
    
    print(f"[OK] Longitud de respuestas:")
    print(f"  - Promedio: {avg_length:.1f} palabras")
    print(f"  - Rango: {min_length} - {max_length} palabras")
    
    return True

def show_sample_questions(dataset):
    """Mostrar preguntas de ejemplo"""
    print_header("MUESTRAS DE PREGUNTAS EXPANDIDAS")
    
    if not dataset:
        print("[ERROR] No hay dataset para mostrar")
        return
    
    # Manejar tanto query_type directo como dentro de metadata
    def get_query_type(q):
        if 'query_type' in q:
            return q['query_type']
        elif 'metadata' in q and 'query_type' in q['metadata']:
            return q['metadata']['query_type']
        return "unknown"
    
    # Mostrar una pregunta de cada tipo clave
    key_types = ['consequence', 'definition', 'conditional']
    
    for qtype in key_types:
        sample = next((q for q in dataset if get_query_type(q) == qtype), None)
        if sample:
            print(f"\n[INFO] EJEMPLO - Tipo '{qtype.upper()}':")
            print(f"  ID: {sample['query_id']}")
            print(f"  Pregunta: {sample['question']}")
            print(f"  Categoría: {sample['category']}")
            print(f"  Dificultad: {sample.get('difficulty') or sample.get('metadata', {}).get('difficulty', 'N/A')}")
            answer_preview = sample['ground_truth_answer'][:100]
            if len(sample['ground_truth_answer']) > 100:
                answer_preview += "..."
            print(f"  Respuesta: {answer_preview}")
        else:
            print(f"\n[ERROR] No se encontraron preguntas tipo '{qtype}'")

def generate_validation_summary(file_check, dataset, distributions, scientific_valid, quality_valid):
    """Generar resumen final de validación"""
    print_header("RESUMEN DE VALIDACIÓN")
    
    all_files_ok = all(file_check.values()) if file_check else False
    dataset_loaded = dataset is not None
    
    print(f"[INFO] RESULTADOS DE VALIDACIÓN:")
    print(f"  {'[OK]' if all_files_ok else '[ERROR]'} Estructura de archivos: {'OK' if all_files_ok else 'PROBLEMAS'}")
    print(f"  {'[OK]' if dataset_loaded else '[ERROR]'} Carga del dataset: {'OK' if dataset_loaded else 'ERROR'}")
    print(f"  {'[OK]' if scientific_valid else '[ERROR]'} Criterios científicos: {'APROBADOS' if scientific_valid else 'FALLÓ'}")
    print(f"  {'[OK]' if quality_valid else '[ERROR]'} Calidad de datos: {'OK' if quality_valid else 'PROBLEMAS'}")
    
    if dataset and distributions:
        print(f"\n[INFO] ESTADÍSTICAS FINALES:")
        print(f"  Total preguntas: {len(dataset)}")
        print(f"  Preguntas 'consequence': {distributions['query_types'].get('consequence', 0)}")
        print(f"  Tipos únicos: {len(distributions['query_types'])}")
        print(f"  Categorías únicas: {len(distributions['categories'])}")
    
    overall_success = all_files_ok and dataset_loaded and scientific_valid and quality_valid
    
    if overall_success:
        print(f"\n[OK] ¡VALIDACIÓN EXITOSA!")
        print(f"[OK] El dataset expandido cumple todos los criterios científicos")
        print(f"[INFO] LISTO PARA: Sprint 1.2 - Evaluación BM25 vs TF-IDF")
    else:
        print(f"\n[ERROR] VALIDACIÓN FALLÓ")
        print(f"[AVISO] Es necesario revisar y corregir los problemas identificados")
    
    return overall_success

def main():
    """Función principal de validación"""
    print("[INFO] VALIDACIÓN COMPLETA DEL GOLDEN DATASET EXPANDIDO")
    print("[INFO] Verificando que el proceso de expansión fue exitoso")
    print("[INFO] Objetivo: Confirmar dataset listo para evaluación científica")
    
    # Ejecutar todas las validaciones
    file_check = check_file_structure()
    dataset = load_and_validate_dataset()
    distributions = analyze_dataset_distribution(dataset)
    scientific_valid = validate_scientific_criteria(dataset, distributions)
    quality_valid = validate_data_quality(dataset)
    
    # Mostrar muestras
    show_sample_questions(dataset)
    
    # Generar resumen
    success = generate_validation_summary(file_check, dataset, distributions, scientific_valid, quality_valid)
    
    return success

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n[INFO] PRÓXIMO PASO: Implementar evaluación BM25 vs TF-IDF")
    else:
        print(f"\n[AVISO] ACCIÓN REQUERIDA: Resolver problemas antes de continuar")

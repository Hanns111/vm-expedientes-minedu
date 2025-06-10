#!/usr/bin/env python3
"""
Script de validación para el Golden Dataset expandido
Verifica la calidad científica del dataset antes de usar en evaluaciones
"""

import json
import sys
from collections import Counter

def cargar_dataset(filepath):
    """Cargar y validar estructura básica del dataset"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        print(f"[OK] Dataset cargado: {len(dataset)} preguntas")
        return dataset
    except Exception as e:
        print(f"[ERROR] Error cargando dataset: {e}")
        return None

def validar_calidad_cientifica(dataset):
    """Validaciones específicas para rigor científico"""
    
    print("\n[ANALISIS] VALIDACIÓN CIENTÍFICA DEL DATASET")
    print("=" * 50)
    
    # 1. Distribución de tipos de consulta
    query_types = Counter(q['metadata']['query_type'] for q in dataset if 'metadata' in q and 'query_type' in q['metadata'])
    print(f"\n[ESTADISTICAS] Distribución de tipos de consulta:")
    for qtype, count in query_types.most_common():
        print(f"  {qtype}: {count} preguntas ({count/len(dataset)*100:.1f}%)")
    
    # 2. Distribución de dificultades
    difficulties = Counter(q['metadata']['difficulty'] for q in dataset if 'metadata' in q and 'difficulty' in q['metadata'])
    print(f"\n[ESTADISTICAS] Distribución de dificultades:")
    for diff, count in difficulties.most_common():
        print(f"  {diff}: {count} preguntas ({count/len(dataset)*100:.1f}%)")
    
    # 3. Distribución de categorías
    categories = Counter(q['category'] for q in dataset)
    print(f"\n[ESTADISTICAS] Distribución de categorías:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count} preguntas ({count/len(dataset)*100:.1f}%)")
    
    # 4. Validar longitud de respuestas
    answer_lengths = [len(q['ground_truth_answer'].split()) for q in dataset]
    avg_length = sum(answer_lengths) / len(answer_lengths)
    print(f"\n[DATOS] Estadísticas de respuestas:")
    print(f"  Longitud promedio: {avg_length:.1f} palabras")
    print(f"  Longitud mínima: {min(answer_lengths)} palabras")
    print(f"  Longitud máxima: {max(answer_lengths)} palabras")
    
    # 5. Verificar cobertura de entidades clave
    all_entities = []
    for q in dataset:
        all_entities.extend(q['metadata'].get('entities_required', []))
    
    entity_coverage = Counter(all_entities)
    print(f"\n[INFO]  Top 10 entidades más referenciadas:")
    for entity, count in entity_coverage.most_common(10):
        print(f"  {entity}: {count} veces")
    
    # 6. Validaciones de calidad
    issues = []
    
    # Verificar balance mínimo
    if 'consequence' in query_types and query_types['consequence'] < 5:
        issues.append("Insuficientes preguntas de consecuencia")
    if 'definition' in query_types and query_types['definition'] < 4:
        issues.append("Insuficientes preguntas de definición")
    
    # Verificar diversidad de categorías
    if len(categories) < 4:
        issues.append("Insuficiente diversidad de categorías")
    
    # Verificar respuestas muy cortas
    short_answers = sum(1 for length in answer_lengths if length < 10)
    if short_answers > len(dataset) * 0.2:
        issues.append(f"Demasiadas respuestas cortas: {short_answers}")
    
    if issues:
        print(f"\n[ADVERTENCIA]  Problemas detectados:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"\n[OK] Dataset aprobado para uso científico")
        return True

def generar_reporte_estadistico(dataset):
    """Generar reporte estadístico completo"""
    
    reporte = {
        "resumen": {
            "total_preguntas": len(dataset),
            "fecha_generacion": "2025-06-08",
            "version": "1.2_expanded"
        },
        "distribuciones": {
            "query_types": dict(Counter(q['metadata']['query_type'] for q in dataset if 'metadata' in q and 'query_type' in q['metadata'])),
            "categories": dict(Counter(q['category'] for q in dataset)),
            "difficulties": dict(Counter(q['metadata']['difficulty'] for q in dataset if 'metadata' in q and 'difficulty' in q['metadata']))
        },
        "metricas_calidad": {
            "longitud_promedio_respuesta": sum(len(q['ground_truth_answer'].split()) for q in dataset) / len(dataset),
            "entidades_unicas": len(set(entity for q in dataset for entity in q['metadata'].get('entities_required', []))),
            "cobertura_secciones": len(set(chunk for q in dataset for chunk in q['supporting_chunks']))
        }
    }
    
    # Guardar reporte
    with open('dataset_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n[ESTADISTICAS] Reporte estadístico guardado en: dataset_quality_report.json")
    return reporte

def main():
    """Función principal de validación"""
    
    dataset_path = "paper_cientifico/dataset/golden_dataset_expanded.json"
    
    print("[VALIDACION] VALIDACIÓN DEL GOLDEN DATASET EXPANDIDO")
    print("[OBJETIVO] Objetivo: Verificar calidad científica para SIGIR/CLEF 2025-2026")
    print("=" * 60)
    
    # Cargar dataset
    dataset = cargar_dataset(dataset_path)
    if not dataset:
        sys.exit(1)
    
    # Validar calidad científica
    is_valid = validar_calidad_cientifica(dataset)
    
    # Generar reporte
    reporte = generar_reporte_estadistico(dataset)
    
    # Conclusión
    if is_valid:
        print("\n[EXITO] DATASET APROBADO: Cumple con los criterios de calidad científica")
        sys.exit(0)
    else:
        print("\n[ADVERTENCIA] DATASET REQUIERE MEJORAS: Revisar problemas detectados")
        sys.exit(1)

if __name__ == "__main__":
    main()

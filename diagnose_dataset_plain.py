#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en la expansión del dataset
Ejecuta verificaciones paso a paso para encontrar la causa del error
"""

import json
import os
import sys
import traceback
from pathlib import Path

def print_section(title):
    """Imprimir sección con formato"""
    print(f"\n{'='*60}")
    print(f"[SECCION] {title}")
    print(f"{'='*60}")

def check_environment():
    """Verificar entorno y dependencias"""
    print_section("VERIFICACIÓN DE ENTORNO")
    
    print(f"[OK] Python version: {sys.version}")
    print(f"[OK] Working directory: {os.getcwd()}")
    print(f"[OK] Script location: {__file__}")
    
    # Verificar módulos necesarios
    try:
        import json
        print("[OK] Módulo json: OK")
    except ImportError as e:
        print(f"[ERROR] Módulo json: {e}")
    
    try:
        from datetime import datetime
        print("[OK] Módulo datetime: OK")
    except ImportError as e:
        print(f"[ERROR] Módulo datetime: {e}")
    
    try:
        from collections import Counter
        print("[OK] Módulo collections: OK")
    except ImportError as e:
        print(f"[ERROR] Módulo collections: {e}")

def check_directory_structure():
    """Verificar estructura de directorios"""
    print_section("VERIFICACIÓN DE ESTRUCTURA DE DIRECTORIOS")
    
    current_dir = Path.cwd()
    print(f"[INFO] Directorio actual: {current_dir}")
    
    # Directorios esperados
    expected_dirs = ["data", "src", "config", "docs", "paper_cientifico"]
    
    for dir_name in expected_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"[OK] Directorio {dir_name}: Existe")
            if dir_name == "data":
                # Listar contenido del directorio data
                data_files = list(dir_path.glob("*"))
                print(f"   [INFO] Archivos en data: {[f.name for f in data_files]}")
            elif dir_name == "paper_cientifico":
                # Verificar si existe el subdirectorio dataset
                dataset_dir = dir_path / "dataset"
                if dataset_dir.exists():
                    dataset_files = list(dataset_dir.glob("*"))
                    print(f"   [INFO] Archivos en paper_cientifico/dataset: {[f.name for f in dataset_files]}")
        else:
            print(f"[ERROR] Directorio {dir_name}: No existe")
            if dir_name == "data":
                print(f"   [INFO] Creando directorio data...")
                try:
                    dir_path.mkdir(exist_ok=True)
                    print(f"   [OK] Directorio data creado")
                except Exception as e:
                    print(f"   [ERROR] Error creando directorio data: {e}")

def check_golden_dataset():
    """Verificar dataset actual"""
    print_section("VERIFICACIÓN DEL GOLDEN DATASET ACTUAL")
    
    possible_paths = [
        "data/golden_dataset.json",
        "golden_dataset.json",
        "data/processed/golden_dataset.json",
        "dataset/golden_dataset.json",
        "paper_cientifico/dataset/golden_dataset.json",
        "paper_cientifico/dataset/golden_dataset_expanded.json"
    ]
    
    dataset_found = False
    dataset_path = None
    dataset_content = None
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[OK] Encontrado dataset en: {path}")
            dataset_found = True
            dataset_path = path
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    dataset_content = json.load(f)
                print(f"[OK] Dataset cargado: {len(dataset_content)} preguntas")
                
                # Mostrar estructura de la primera pregunta
                if dataset_content:
                    print(f"[INFO] Estructura de primera pregunta:")
                    first_q = dataset_content[0]
                    for key, value in first_q.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"   {key}: {value[:50]}...")
                        else:
                            print(f"   {key}: {value}")
                
                break
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] Error JSON en {path}: {e}")
            except Exception as e:
                print(f"[ERROR] Error leyendo {path}: {e}")
        else:
            print(f"[INFO] No encontrado: {path}")
    
    if not dataset_found:
        print(f"[ERROR] PROBLEMA CRÍTICO: No se encontró golden_dataset.json en ninguna ubicación")
        print(f"[INFO] Ubicaciones buscadas: {possible_paths}")
        return None, None
    
    return dataset_path, dataset_content

def test_json_operations():
    """Probar operaciones JSON básicas"""
    print_section("PRUEBA DE OPERACIONES JSON")
    
    test_data = {
        "query_id": "test_001",
        "question": "¿Esta es una pregunta de prueba?",
        "category": "test",
        "query_type": "factual",
        "difficulty": "easy",
        "ground_truth_answer": "Esta es una respuesta de prueba.",
        "supporting_chunks": ["chunk_test"],
        "metadata": {
            "entities_required": ["test_entity"],
            "context_type": "test"
        }
    }
    
    try:
        # Probar escritura JSON
        test_file = "test_write.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump([test_data], f, indent=2, ensure_ascii=False)
        print(f"[OK] Escritura JSON: OK")
        
        # Probar lectura JSON
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"[OK] Lectura JSON: OK")
        
        # Limpiar archivo de prueba
        os.remove(test_file)
        print(f"[OK] Operaciones JSON: Todas exitosas")
        
    except Exception as e:
        print(f"[ERROR] Error en operaciones JSON: {e}")
        print(f"[INFO] Traceback: {traceback.format_exc()}")

def test_file_permissions():
    """Probar permisos de archivos"""
    print_section("VERIFICACIÓN DE PERMISOS DE ARCHIVOS")
    
    test_dir = "data"
    
    try:
        # Verificar si podemos crear archivos en data/
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            print(f"[OK] Directorio {test_dir} creado")
        
        test_file = os.path.join(test_dir, "permission_test.txt")
        
        # Probar escritura
        with open(test_file, 'w') as f:
            f.write("test")
        print(f"[OK] Permisos de escritura: OK")
        
        # Probar lectura
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"[OK] Permisos de lectura: OK")
        
        # Limpiar
        os.remove(test_file)
        print(f"[OK] Permisos de eliminación: OK")
        
    except Exception as e:
        print(f"[ERROR] Error de permisos: {e}")
        print(f"[INFO] Traceback: {traceback.format_exc()}")

def analyze_previous_error():
    """Analizar posibles causas de errores anteriores"""
    print_section("ANÁLISIS DE POSIBLES CAUSAS DE ERROR")
    
    print("[INFO] Posibles causas de error en intentos anteriores:")
    print("1. [POSIBLE] Archivo golden_dataset.json no encontrado en la ubicación esperada")
    print("2. [POSIBLE] Formato JSON inválido en el dataset actual")
    print("3. [POSIBLE] Permisos insuficientes para escribir archivos")
    print("4. [POSIBLE] Conflicto de encoding (UTF-8 vs otros)")
    print("5. [POSIBLE] IDs duplicados en el dataset actual")
    print("6. [POSIBLE] Estructura de directorio incorrecta")
    print("7. [POSIBLE] Dependencias faltantes")
    print("8. [POSIBLE] Path relativo vs absoluto")

def provide_solutions():
    """Proporcionar soluciones basadas en diagnóstico"""
    print_section("SOLUCIONES RECOMENDADAS")
    
    print("[INFO] Soluciones paso a paso:")
    print("1. [PASO] Ejecutar este script de diagnóstico completamente")
    print("2. [PASO] Verificar que el archivo golden_dataset.json existe y es válido")
    print("3. [PASO] Crear estructura de directorios si es necesaria")
    print("4. [PASO] Usar paths absolutos en lugar de relativos")
    print("5. [PASO] Verificar permisos de escritura en el directorio")
    print("6. [PASO] Intentar operación simplificada paso a paso")

def create_minimal_expansion_script():
    """Crear script mínimo para expansión"""
    print_section("CREANDO SCRIPT MÍNIMO DE EXPANSIÓN")
    
    minimal_script = """#!/usr/bin/env python3
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
"""
    
    try:
        with open("minimal_expansion.py", 'w', encoding='utf-8') as f:
            f.write(minimal_script)
        print("[OK] Script mínimo creado: minimal_expansion.py")
        print("[INFO] Ejecutar con: python minimal_expansion.py")
    except Exception as e:
        print(f"[ERROR] Error creando script mínimo: {e}")

def main():
    """Función principal de diagnóstico"""
    
    print("[INFO] DIAGNÓSTICO DE PROBLEMAS DE EXPANSIÓN DEL DATASET")
    print("[INFO] Identificando la causa de los errores en los 4 intentos anteriores")
    print("=" * 70)
    
    try:
        # Ejecutar todas las verificaciones
        check_environment()
        check_directory_structure()
        dataset_path, dataset_content = check_golden_dataset()
        test_json_operations()
        test_file_permissions()
        analyze_previous_error()
        provide_solutions()
        create_minimal_expansion_script()
        
        print("\n" + "=" * 70)
        print("[INFO] DIAGNÓSTICO COMPLETADO")
        print("=" * 70)
        
        if dataset_path and dataset_content:
            print("[OK] Dataset encontrado y cargado correctamente")
            print("[INFO] Siguiente paso: Ejecutar 'python minimal_expansion.py' para prueba")
        else:
            print("[ERROR] Problema crítico: Dataset no encontrado")
            print("[INFO] Siguiente paso: Verificar ubicación del archivo golden_dataset.json")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR DURANTE DIAGNÓSTICO: {e}")
        print(f"[INFO] Traceback completo:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

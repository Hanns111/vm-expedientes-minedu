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
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_environment():
    """Verificar entorno y dependencias"""
    print_section("VERIFICACIÓN DE ENTORNO")
    
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Working directory: {os.getcwd()}")
    print(f"✅ Script location: {__file__}")
    
    # Verificar módulos necesarios
    try:
        import json
        print("✅ Módulo json: OK")
    except ImportError as e:
        print(f"❌ Módulo json: {e}")
    
    try:
        from datetime import datetime
        print("✅ Módulo datetime: OK")
    except ImportError as e:
        print(f"❌ Módulo datetime: {e}")
    
    try:
        from collections import Counter
        print("✅ Módulo collections: OK")
    except ImportError as e:
        print(f"❌ Módulo collections: {e}")

def check_directory_structure():
    """Verificar estructura de directorios"""
    print_section("VERIFICACIÓN DE ESTRUCTURA DE DIRECTORIOS")
    
    current_dir = Path.cwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # Directorios esperados
    expected_dirs = ["data", "src", "config", "docs"]
    
    for dir_name in expected_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"✅ Directorio {dir_name}: Existe")
            if dir_name == "data":
                # Listar contenido del directorio data
                data_files = list(dir_path.glob("*"))
                print(f"   📄 Archivos en data: {[f.name for f in data_files]}")
        else:
            print(f"❌ Directorio {dir_name}: No existe")
            if dir_name == "data":
                print(f"   💡 Creando directorio data...")
                try:
                    dir_path.mkdir(exist_ok=True)
                    print(f"   ✅ Directorio data creado")
                except Exception as e:
                    print(f"   ❌ Error creando directorio data: {e}")

def check_golden_dataset():
    """Verificar dataset actual"""
    print_section("VERIFICACIÓN DEL GOLDEN DATASET ACTUAL")
    
    possible_paths = [
        "data/golden_dataset.json",
        "golden_dataset.json",
        "data/processed/golden_dataset.json",
        "dataset/golden_dataset.json",
        "paper_cientifico/dataset/golden_dataset.json"
    ]
    
    dataset_found = False
    dataset_path = None
    dataset_content = None
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Encontrado dataset en: {path}")
            dataset_found = True
            dataset_path = path
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    dataset_content = json.load(f)
                print(f"✅ Dataset cargado: {len(dataset_content)} preguntas")
                
                # Mostrar estructura de la primera pregunta
                if dataset_content:
                    print(f"📋 Estructura de primera pregunta:")
                    first_q = dataset_content[0]
                    for key, value in first_q.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"   {key}: {value[:50]}...")
                        else:
                            print(f"   {key}: {value}")
                
                break
                
            except json.JSONDecodeError as e:
                print(f"❌ Error JSON en {path}: {e}")
            except Exception as e:
                print(f"❌ Error leyendo {path}: {e}")
        else:
            print(f"❌ No encontrado: {path}")
    
    if not dataset_found:
        print(f"❌ PROBLEMA CRÍTICO: No se encontró golden_dataset.json en ninguna ubicación")
        print(f"💡 Ubicaciones buscadas: {possible_paths}")
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
        print(f"✅ Escritura JSON: OK")
        
        # Probar lectura JSON
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"✅ Lectura JSON: OK")
        
        # Limpiar archivo de prueba
        os.remove(test_file)
        print(f"✅ Operaciones JSON: Todas exitosas")
        
    except Exception as e:
        print(f"❌ Error en operaciones JSON: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")

def test_file_permissions():
    """Probar permisos de archivos"""
    print_section("VERIFICACIÓN DE PERMISOS DE ARCHIVOS")
    
    test_dir = "data"
    
    try:
        # Verificar si podemos crear archivos en data/
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            print(f"✅ Directorio {test_dir} creado")
        
        test_file = os.path.join(test_dir, "permission_test.txt")
        
        # Probar escritura
        with open(test_file, 'w') as f:
            f.write("test")
        print(f"✅ Permisos de escritura: OK")
        
        # Probar lectura
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"✅ Permisos de lectura: OK")
        
        # Limpiar
        os.remove(test_file)
        print(f"✅ Permisos de eliminación: OK")
        
    except Exception as e:
        print(f"❌ Error de permisos: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")

def analyze_previous_error():
    """Analizar posibles causas de errores anteriores"""
    print_section("ANÁLISIS DE POSIBLES CAUSAS DE ERROR")
    
    print("🔍 Posibles causas de error en intentos anteriores:")
    print("1. ❌ Archivo golden_dataset.json no encontrado en la ubicación esperada")
    print("2. ❌ Formato JSON inválido en el dataset actual")
    print("3. ❌ Permisos insuficientes para escribir archivos")
    print("4. ❌ Conflicto de encoding (UTF-8 vs otros)")
    print("5. ❌ IDs duplicados en el dataset actual")
    print("6. ❌ Estructura de directorio incorrecta")
    print("7. ❌ Dependencias faltantes")
    print("8. ❌ Path relativo vs absoluto")

def provide_solutions():
    """Proporcionar soluciones basadas en diagnóstico"""
    print_section("SOLUCIONES RECOMENDADAS")
    
    print("💡 Soluciones paso a paso:")
    print("1. ✅ Ejecutar este script de diagnóstico completamente")
    print("2. 📁 Verificar que el archivo golden_dataset.json existe y es válido")
    print("3. 🔧 Crear estructura de directorios si es necesaria")
    print("4. 🛠️ Usar paths absolutos en lugar de relativos")
    print("5. 🔒 Verificar permisos de escritura en el directorio")
    print("6. 🔄 Intentar operación simplificada paso a paso")

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
    dataset_paths = ["data/golden_dataset.json", "golden_dataset.json", "paper_cientifico/dataset/golden_dataset.json"]
    
    current_dataset = None
    dataset_path = None
    
    for path in dataset_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    current_dataset = json.load(f)
                dataset_path = path
                print(f"✅ Dataset encontrado: {path} ({len(current_dataset)} preguntas)")
                break
            except Exception as e:
                print(f"❌ Error en {path}: {e}")
    
    if current_dataset is None:
        print("❌ No se pudo cargar el dataset actual")
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
        print(f"✅ Backup creado: {backup_path}")
        
        # Guardar expandido
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(expanded_dataset, f, indent=2, ensure_ascii=False)
        print(f"✅ Dataset expandido guardado: {len(expanded_dataset)} preguntas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return False

if __name__ == "__main__":
    print("🧪 EXPANSIÓN MÍNIMA DE PRUEBA")
    print("=" * 40)
    if minimal_expansion():
        print("✅ Expansión mínima exitosa")
    else:
        print("❌ Expansión mínima falló")
"""
    
    try:
        with open("minimal_expansion.py", 'w', encoding='utf-8') as f:
            f.write(minimal_script)
        print("✅ Script mínimo creado: minimal_expansion.py")
        print("💡 Ejecutar con: python minimal_expansion.py")
    except Exception as e:
        print(f"❌ Error creando script mínimo: {e}")

def main():
    """Función principal de diagnóstico"""
    
    print("🚨 DIAGNÓSTICO DE PROBLEMAS DE EXPANSIÓN DEL DATASET")
    print("🎯 Identificando la causa de los errores en los 4 intentos anteriores")
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
        print("🎯 DIAGNÓSTICO COMPLETADO")
        print("=" * 70)
        
        if dataset_path and dataset_content:
            print("✅ Dataset encontrado y cargado correctamente")
            print("💡 Siguiente paso: Ejecutar 'python minimal_expansion.py' para prueba")
        else:
            print("❌ Problema crítico: Dataset no encontrado")
            print("💡 Siguiente paso: Verificar ubicación del archivo golden_dataset.json")
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE DIAGNÓSTICO: {e}")
        print(f"📋 Traceback completo:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

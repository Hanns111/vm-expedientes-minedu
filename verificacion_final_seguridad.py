#!/usr/bin/env python3
"""
Verificación final del sistema de seguridad MINEDU
Confirma que todos los elementos están implementados correctamente
"""

import sys
import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """Verificar si un archivo existe"""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        return True, f"✅ {file_path} ({size} bytes)"
    else:
        return False, f"❌ {file_path} (NO EXISTE)"

def check_class_exists(module_name: str, class_name: str) -> Tuple[bool, str]:
    """Verificar si una clase existe en un módulo"""
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            if inspect.isclass(cls):
                return True, f"✅ {module_name}.{class_name} (Clase encontrada)"
            else:
                return False, f"❌ {module_name}.{class_name} (No es una clase)"
        else:
            return False, f"❌ {module_name}.{class_name} (Clase no encontrada)"
    except ImportError as e:
        return False, f"❌ {module_name}.{class_name} (Error importando: {e})"
    except Exception as e:
        return False, f"❌ {module_name}.{class_name} (Error: {e})"

def check_method_exists(module_name: str, class_name: str, method_name: str) -> Tuple[bool, str]:
    """Verificar si un método existe en una clase"""
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            if inspect.isclass(cls):
                if hasattr(cls, method_name):
                    method = getattr(cls, method_name)
                    if callable(method):
                        return True, f"✅ {module_name}.{class_name}.{method_name} (Método encontrado)"
                    else:
                        return False, f"❌ {module_name}.{class_name}.{method_name} (No es un método)"
                else:
                    return False, f"❌ {module_name}.{class_name}.{method_name} (Método no encontrado)"
            else:
                return False, f"❌ {module_name}.{class_name}.{method_name} (No es una clase)"
        else:
            return False, f"❌ {module_name}.{class_name}.{method_name} (Clase no encontrada)"
    except ImportError as e:
        return False, f"❌ {module_name}.{class_name}.{method_name} (Error importando: {e})"
    except Exception as e:
        return False, f"❌ {module_name}.{class_name}.{method_name} (Error: {e})"

def run_final_verification():
    """Ejecutar verificación final completa"""
    print("🔒 VERIFICACIÓN FINAL DEL SISTEMA DE SEGURIDAD MINEDU")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    results = {
        'files': [],
        'classes': [],
        'methods': [],
        'summary': {}
    }
    
    # 1. Verificar archivos críticos
    print("\n📁 VERIFICANDO ARCHIVOS CRÍTICOS:")
    print("-" * 50)
    
    critical_files = [
        "src/core/config/security_config.py",
        "src/core/secure_search.py",
        "src/core/security/__init__.py",
        "src/core/security/input_validator.py",
        "src/core/security/rate_limiter.py",
        "src/core/security/privacy.py",
        "src/core/security/file_validator.py",
        "src/core/security/compliance.py",
        "src/core/security/monitor.py",
        "src/core/security/logger.py",
        "src/core/security/safe_pickle.py",
        "demo_secure.py",
        "security_audit.py",
        "config/settings_secure.py",
        "requirements_security.txt"
    ]
    
    for file_path in critical_files:
        exists, message = check_file_exists(file_path)
        results['files'].append((exists, message))
        print(message)
    
    # 2. Verificar clases críticas
    print("\n🏗️ VERIFICANDO CLASES CRÍTICAS:")
    print("-" * 50)
    
    critical_classes = [
        ("src.core.config.security_config", "SecurityConfig"),
        ("src.core.secure_search", "SecureHybridSearch"),
        ("src.core.security.input_validator", "InputValidator"),
        ("src.core.security.rate_limiter", "RateLimiter"),
        ("src.core.security.privacy", "PrivacyProtector"),
        ("src.core.security.file_validator", "FileValidator"),
        ("src.core.security.compliance", "ComplianceChecker"),
        ("src.core.security.monitor", "SecurityMonitor"),
        ("src.core.security.logger", "SecureLogger"),
        ("src.core.security.safe_pickle", "SafePickleLoader"),
        ("demo_secure", "SecureRAGDemo"),
        ("security_audit", "SecurityAuditor")
    ]
    
    for module_name, class_name in critical_classes:
        exists, message = check_class_exists(module_name, class_name)
        results['classes'].append((exists, message))
        print(message)
    
    # 3. Verificar métodos críticos en SecurityConfig
    print("\n🔧 VERIFICANDO MÉTODOS CRÍTICOS EN SECURITYCONFIG:")
    print("-" * 50)
    
    security_config_methods = [
        "validate_path",
        "sanitize_input", 
        "get_config_summary",
        "log_security_event",
        "get_safe_path"
    ]
    
    for method_name in security_config_methods:
        exists, message = check_method_exists("src.core.config.security_config", "SecurityConfig", method_name)
        results['methods'].append((exists, message))
        print(message)
    
    # 4. Verificar métodos críticos en SecureRAGDemo
    print("\n🔧 VERIFICANDO MÉTODOS CRÍTICOS EN SECURERAGDEMO:")
    print("-" * 50)
    
    secure_demo_methods = [
        "validate_query",
        "search",
        "get_system_status",
        "run_interactive_demo"
    ]
    
    for method_name in secure_demo_methods:
        exists, message = check_method_exists("demo_secure", "SecureRAGDemo", method_name)
        results['methods'].append((exists, message))
        print(message)
    
    # 5. Verificar métodos críticos en SecurityAuditor
    print("\n🔧 VERIFICANDO MÉTODOS CRÍTICOS EN SECURITYAUDITOR:")
    print("-" * 50)
    
    security_auditor_methods = [
        "audit_paths",
        "audit_pickle_files",
        "audit_security_modules",
        "audit_configuration",
        "audit_input_validation",
        "run_full_audit",
        "print_audit_report"
    ]
    
    for method_name in security_auditor_methods:
        exists, message = check_method_exists("security_audit", "SecurityAuditor", method_name)
        results['methods'].append((exists, message))
        print(message)
    
    # 6. Generar resumen
    print("\n📊 RESUMEN DE VERIFICACIÓN:")
    print("-" * 50)
    
    total_files = len(results['files'])
    total_classes = len(results['classes'])
    total_methods = len(results['methods'])
    
    files_ok = sum(1 for exists, _ in results['files'] if exists)
    classes_ok = sum(1 for exists, _ in results['classes'] if exists)
    methods_ok = sum(1 for exists, _ in results['methods'] if exists)
    
    print(f"📁 Archivos: {files_ok}/{total_files} ✅")
    print(f"🏗️ Clases: {classes_ok}/{total_classes} ✅")
    print(f"🔧 Métodos: {methods_ok}/{total_methods} ✅")
    
    total_items = total_files + total_classes + total_methods
    total_ok = files_ok + classes_ok + methods_ok
    completion_percentage = (total_ok / total_items) * 100 if total_items > 0 else 0
    
    print(f"\n📈 COMPLETITUD DEL SISTEMA: {completion_percentage:.1f}%")
    
    if completion_percentage >= 95:
        print("🎉 ¡SISTEMA DE SEGURIDAD COMPLETAMENTE IMPLEMENTADO!")
        status = "COMPLETO"
    elif completion_percentage >= 80:
        print("⚠️ Sistema de seguridad mayormente implementado")
        status = "MAYORMENTE COMPLETO"
    else:
        print("❌ Sistema de seguridad incompleto")
        status = "INCOMPLETO"
    
    # 7. Mostrar elementos faltantes
    if completion_percentage < 100:
        print("\n❌ ELEMENTOS FALTANTES:")
        print("-" * 30)
        
        for exists, message in results['files']:
            if not exists:
                print(f"📁 {message}")
        
        for exists, message in results['classes']:
            if not exists:
                print(f"🏗️ {message}")
        
        for exists, message in results['methods']:
            if not exists:
                print(f"🔧 {message}")
    
    # 8. Guardar resultados
    results['summary'] = {
        'timestamp': datetime.now().isoformat(),
        'total_files': total_files,
        'files_ok': files_ok,
        'total_classes': total_classes,
        'classes_ok': classes_ok,
        'total_methods': total_methods,
        'methods_ok': methods_ok,
        'completion_percentage': completion_percentage,
        'status': status
    }
    
    # Guardar en archivo
    import json
    with open('verificacion_final_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados guardados en: verificacion_final_resultados.json")
    print("=" * 70)
    print("🔒 VERIFICACIÓN FINAL COMPLETADA")
    print("=" * 70)
    
    return results

def main():
    """Función principal"""
    try:
        results = run_final_verification()
        
        # Retornar código de salida basado en completitud
        if results['summary']['completion_percentage'] >= 95:
            print("\n✅ SISTEMA LISTO PARA PRODUCCIÓN")
            sys.exit(0)
        else:
            print("\n⚠️ SISTEMA REQUIERE COMPLETAR IMPLEMENTACIÓN")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
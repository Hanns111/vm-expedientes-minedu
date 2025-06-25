#!/usr/bin/env python3
"""
Validador de Configuración de Deployment
=========================================

Valida que todos los archivos y configuraciones estén listos
para deployment sin necesidad de ejecutar servicios.
"""
import os
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """Verificar que un archivo existe"""
    path = Path(file_path)
    if path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} FALTANTE: {file_path}")
        return False

def check_directory_exists(dir_path, description):
    """Verificar que un directorio existe"""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description} FALTANTE: {dir_path}")
        return False

def validate_json_file(file_path, description):
    """Validar que un archivo JSON es válido"""
    if not Path(file_path).exists():
        print(f"❌ {description} NO EXISTE: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        print(f"✅ {description} JSON VÁLIDO: {file_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {description} JSON INVÁLIDO: {file_path} - {e}")
        return False

def check_package_json_dependencies():
    """Verificar dependencias en package.json"""
    package_path = "frontend-new/package.json"
    if not Path(package_path).exists():
        print(f"❌ package.json no encontrado: {package_path}")
        return False
    
    try:
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        
        required_deps = ["next", "react", "typescript", "tailwindcss"]
        deps = package_data.get("dependencies", {})
        
        missing = [dep for dep in required_deps if dep not in deps]
        if missing:
            print(f"❌ Dependencias faltantes en package.json: {missing}")
            return False
        else:
            print(f"✅ Todas las dependencias críticas presentes en package.json")
            return True
            
    except Exception as e:
        print(f"❌ Error validando package.json: {e}")
        return False

def validate_environment_files():
    """Validar archivos de entorno"""
    env_files = [
        ("frontend-new/.env.example", "Frontend environment example"),
        ("frontend-new/.env.local", "Frontend local environment"),
        (".env.production", "Backend production environment")
    ]
    
    results = []
    for file_path, description in env_files:
        exists = check_file_exists(file_path, description)
        results.append(exists)
    
    return all(results)

def validate_docker_config():
    """Validar configuración Docker"""
    docker_files = [
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose configuration"),
        (".dockerignore", "Docker ignore file")
    ]
    
    results = []
    for file_path, description in docker_files:
        exists = check_file_exists(file_path, description)
        results.append(exists)
    
    return all(results)

def validate_frontend_structure():
    """Validar estructura del frontend"""
    frontend_structure = [
        ("frontend-new", "Frontend directory"),
        ("frontend-new/app", "Next.js app directory"),
        ("frontend-new/components", "Components directory"),
        ("frontend-new/lib", "Library directory"),
        ("frontend-new/app/page.tsx", "Main page component"),
        ("frontend-new/app/layout.tsx", "Root layout component"),
        ("frontend-new/components/search-interface.tsx", "Search interface"),
        ("frontend-new/lib/api.ts", "API client"),
        ("frontend-new/tailwind.config.js", "Tailwind configuration"),
        ("frontend-new/next.config.js", "Next.js configuration"),
        ("frontend-new/tsconfig.json", "TypeScript configuration")
    ]
    
    results = []
    for path, description in frontend_structure:
        if path.endswith('/'):
            exists = check_directory_exists(path, description)
        else:
            exists = check_file_exists(path, description)
        results.append(exists)
    
    return all(results)

def validate_backend_structure():
    """Validar estructura del backend"""
    backend_files = [
        ("api_minedu.py", "Main FastAPI application"),
        ("requirements.txt", "Python dependencies"),
        ("src/core/hybrid/hybrid_search.py", "Hybrid search system"),
        ("data/vectorstores", "Vectorstores directory")
    ]
    
    results = []
    for path, description in backend_files:
        if path.endswith('/') or 'vectorstores' in path:
            exists = check_directory_exists(path, description)
        else:
            exists = check_file_exists(path, description)
        results.append(exists)
    
    return all(results)

def validate_deployment_scripts():
    """Validar scripts de deployment"""
    scripts = [
        ("deploy.sh", "Deployment script"),
        ("test_integration.py", "Integration test script"),
        ("start_system.py", "System starter script")
    ]
    
    results = []
    for file_path, description in scripts:
        exists = check_file_exists(file_path, description)
        if exists and file_path.endswith('.sh'):
            # Verificar que el script sea ejecutable
            path = Path(file_path)
            if os.access(path, os.X_OK):
                print(f"✅ {description} es ejecutable")
            else:
                print(f"⚠️  {description} no es ejecutable (run: chmod +x {file_path})")
        results.append(exists)
    
    return all(results)

def validate_vectorstores():
    """Validar vectorstores necesarios"""
    vectorstore_path = Path("data/vectorstores")
    if not vectorstore_path.exists():
        print("❌ Directorio vectorstores no existe")
        return False
    
    required_vectorstores = ["bm25.pkl", "tfidf.pkl", "transformers.pkl"]
    results = []
    
    for vs_file in required_vectorstores:
        vs_path = vectorstore_path / vs_file
        if vs_path.exists():
            size = vs_path.stat().st_size
            print(f"✅ Vectorstore {vs_file}: {size:,} bytes")
            results.append(True)
        else:
            print(f"❌ Vectorstore faltante: {vs_file}")
            results.append(False)
    
    return all(results)

def main():
    """Ejecutar todas las validaciones"""
    print("🔍 VALIDACIÓN DE CONFIGURACIÓN DE DEPLOYMENT")
    print("=" * 60)
    
    validations = [
        ("Frontend Structure", validate_frontend_structure),
        ("Backend Structure", validate_backend_structure),
        ("Docker Configuration", validate_docker_config),
        ("Environment Files", validate_environment_files),
        ("Deployment Scripts", validate_deployment_scripts),
        ("Package.json Dependencies", check_package_json_dependencies),
        ("Vectorstores", validate_vectorstores)
    ]
    
    results = []
    
    for validation_name, validation_func in validations:
        print(f"\n📋 {validation_name}")
        print("-" * 40)
        success = validation_func()
        results.append((validation_name, success))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = 0
    for validation_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{validation_name:.<40} {status}")
        if success:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} validaciones exitosas")
    
    if passed == len(results):
        print("\n🎉 ¡CONFIGURACIÓN COMPLETAMENTE VÁLIDA!")
        print("   El sistema está listo para deployment.")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Instalar Docker en tu sistema")
        print("   2. Ejecutar: ./deploy.sh production")
        print("   3. Configurar dominios y SSL")
    else:
        print("\n⚠️  ALGUNAS VALIDACIONES FALLARON")
        print("   Revisa los elementos marcados como FAILED")
        
        if not validate_vectorstores():
            print("\n💡 Para generar vectorstores faltantes:")
            print("   python src/data_pipeline/generate_vectorstores.py")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
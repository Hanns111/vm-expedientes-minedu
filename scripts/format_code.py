#!/usr/bin/env python3
"""
Script para formatear y validar todo el código del proyecto con Ruff.

Uso:
    python scripts/format_code.py [--check] [--fix] [--stats]
    
Argumentos:
    --check: Solo verificar, no modificar archivos
    --fix: Aplicar correcciones automáticas (por defecto)
    --stats: Mostrar estadísticas detalladas
    --security: Ejecutar análisis de seguridad
    --types: Ejecutar verificación de tipos con MyPy
    --all: Ejecutar todas las verificaciones
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any


class CodeFormatter:
    """Formateador de código usando Ruff y herramientas relacionadas."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.stats = {
            "files_processed": 0,
            "issues_found": 0,
            "issues_fixed": 0,
            "execution_time": 0.0,
            "tools_used": []
        }
    
    def run_command(self, cmd: List[str], description: str = "") -> Dict[str, Any]:
        """Ejecutar comando y capturar resultado."""
        start_time = time.time()
        
        print(f"\n🔄 {description or ' '.join(cmd)}")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            execution_time = time.time() - start_time
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
                
            status = "✅ SUCCESS" if result.returncode == 0 else "❌ FAILED"
            print(f"\n{status} (Tiempo: {execution_time:.2f}s)")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "return_code": result.returncode
            }
            
        except FileNotFoundError:
            print(f"❌ Comando no encontrado: {cmd[0]}")
            return {
                "success": False,
                "error": f"Command not found: {cmd[0]}",
                "execution_time": time.time() - start_time
            }
    
    def format_with_ruff(self, check_only: bool = False) -> bool:
        """Formatear código con Ruff."""
        self.stats["tools_used"].append("ruff-format")
        
        # Comando de formateo
        format_cmd = ["ruff", "format"]
        if check_only:
            format_cmd.extend(["--check", "--diff"])
        format_cmd.append(".")
        
        result = self.run_command(
            format_cmd,
            f"Ruff Formatter ({'Check Only' if check_only else 'Apply Fixes'})"
        )
        
        return result["success"]
    
    def lint_with_ruff(self, fix: bool = False) -> bool:
        """Linter con Ruff."""
        self.stats["tools_used"].append("ruff-lint")
        
        # Comando de linting
        lint_cmd = ["ruff", "check"]
        if fix:
            lint_cmd.append("--fix")
        lint_cmd.extend(["--output-format", "grouped", "."])
        
        result = self.run_command(
            lint_cmd,
            f"Ruff Linter ({'Auto-fix' if fix else 'Check Only'})"
        )
        
        # Extraer estadísticas del output
        if result["stdout"]:
            lines = result["stdout"].split("\n")
            for line in lines:
                if "error" in line.lower() or "warning" in line.lower():
                    self.stats["issues_found"] += 1
                if fix and "fixed" in line.lower():
                    self.stats["issues_fixed"] += 1
        
        return result["success"]
    
    def check_types_with_mypy(self) -> bool:
        """Verificar tipos con MyPy."""
        self.stats["tools_used"].append("mypy")
        
        result = self.run_command(
            ["mypy", "--config-file=pyproject.toml", "src/", "backend/"],
            "MyPy Type Checker"
        )
        
        return result["success"]
    
    def security_scan_with_bandit(self) -> bool:
        """Análisis de seguridad con Bandit."""
        self.stats["tools_used"].append("bandit")
        
        result = self.run_command(
            [
                "bandit", 
                "-r", "src/", "backend/",
                "-f", "txt",
                "--severity-level", "medium",
                "--confidence-level", "medium"
            ],
            "Bandit Security Scanner"
        )
        
        return result["success"]
    
    def run_tests(self) -> bool:
        """Ejecutar tests con pytest."""
        self.stats["tools_used"].append("pytest")
        
        result = self.run_command(
            ["pytest", "--tb=short", "-v"],
            "Pytest Test Suite"
        )
        
        return result["success"]
    
    def show_statistics(self):
        """Mostrar estadísticas del proceso."""
        print("\n" + "=" * 60)
        print("📊 ESTADÍSTICAS DEL FORMATEO")
        print("=" * 60)
        
        print(f"⏱️  Tiempo total: {self.stats['execution_time']:.2f}s")
        print(f"🔧 Herramientas usadas: {', '.join(self.stats['tools_used'])}")
        print(f"🐛 Issues encontrados: {self.stats['issues_found']}")
        print(f"✅ Issues corregidos: {self.stats['issues_fixed']}")
        print(f"📁 Archivos procesados: {self.stats['files_processed']}")
        
        # Mostrar resumen por herramienta
        print(f"\n🛠️  HERRAMIENTAS EJECUTADAS:")
        for tool in set(self.stats['tools_used']):
            print(f"   • {tool}")
    
    def count_python_files(self) -> int:
        """Contar archivos Python en el proyecto."""
        python_files = list(self.project_root.rglob("*.py"))
        # Filtrar archivos en directorios excluidos
        excluded_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules"}
        
        filtered_files = [
            f for f in python_files 
            if not any(excluded in str(f) for excluded in excluded_dirs)
        ]
        
        self.stats["files_processed"] = len(filtered_files)
        return len(filtered_files)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Formatear y validar código con Ruff",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python scripts/format_code.py                    # Formatear y corregir
    python scripts/format_code.py --check            # Solo verificar
    python scripts/format_code.py --all              # Todas las verificaciones
    python scripts/format_code.py --stats --security # Seguridad + estadísticas
        """
    )
    
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Solo verificar formato, no modificar archivos"
    )
    
    parser.add_argument(
        "--fix", 
        action="store_true", 
        default=True,
        help="Aplicar correcciones automáticas (por defecto)"
    )
    
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Mostrar estadísticas detalladas"
    )
    
    parser.add_argument(
        "--security", 
        action="store_true", 
        help="Ejecutar análisis de seguridad con Bandit"
    )
    
    parser.add_argument(
        "--types", 
        action="store_true", 
        help="Verificar tipos con MyPy"
    )
    
    parser.add_argument(
        "--tests", 
        action="store_true", 
        help="Ejecutar suite de tests"
    )
    
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Ejecutar todas las verificaciones"
    )
    
    args = parser.parse_args()
    
    # Si se especifica --all, habilitar todas las opciones
    if args.all:
        args.security = True
        args.types = True
        args.tests = True
        args.stats = True
    
    # Si se especifica --check, deshabilitar --fix
    if args.check:
        args.fix = False
    
    print("🎨 FORMATEADOR DE CÓDIGO GUBERNAMENTAL")
    print("=" * 60)
    print(f"📁 Directorio: {Path.cwd()}")
    print(f"🔧 Modo: {'Check Only' if args.check else 'Apply Fixes'}")
    
    formatter = CodeFormatter()
    start_time = time.time()
    
    # Contar archivos
    file_count = formatter.count_python_files()
    print(f"📄 Archivos Python encontrados: {file_count}")
    
    success = True
    
    # 1. Formateo con Ruff
    print(f"\n{'🔍' if args.check else '🎨'} PASO 1: Formateo de código")
    if not formatter.format_with_ruff(check_only=args.check):
        success = False
        if args.check:
            print("⚠️  Archivos necesitan formateo")
    
    # 2. Linting con Ruff
    print(f"\n🔍 PASO 2: Análisis de código")
    if not formatter.lint_with_ruff(fix=args.fix and not args.check):
        if not args.check:  # Si estamos aplicando fixes, warnings no son fatales
            print("⚠️  Se encontraron warnings (no fatal)")
        else:
            success = False
    
    # 3. Verificación de tipos (opcional)
    if args.types:
        print(f"\n🔬 PASO 3: Verificación de tipos")
        if not formatter.check_types_with_mypy():
            print("⚠️  Se encontraron errores de tipos (no fatal)")
    
    # 4. Análisis de seguridad (opcional)
    if args.security:
        print(f"\n🔒 PASO 4: Análisis de seguridad")
        if not formatter.security_scan_with_bandit():
            print("⚠️  Se encontraron issues de seguridad (revisar)")
    
    # 5. Tests (opcional)
    if args.tests:
        print(f"\n🧪 PASO 5: Suite de tests")
        if not formatter.run_tests():
            success = False
            print("❌ Tests fallaron")
    
    # Calcular tiempo total
    formatter.stats["execution_time"] = time.time() - start_time
    
    # Mostrar estadísticas
    if args.stats:
        formatter.show_statistics()
    
    # Resultado final
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        if not args.check:
            print("✅ Código formateado y validado correctamente")
        else:
            print("✅ Código cumple con los estándares")
    else:
        print("❌ PROCESO COMPLETADO CON ERRORES")
        print("🔧 Revisa los mensajes anteriores y corrige los issues")
    
    print(f"⏱️  Tiempo total: {formatter.stats['execution_time']:.2f}s")
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
"""
Script para migrar todas las rutas hardcodeadas a rutas relativas
Ejecutar: python src/core/path_migration.py
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

class PathMigrator:
    """Migra rutas absolutas a relativas en todo el proyecto"""
    
    # Patrones de rutas hardcodeadas
    PATTERNS = [
        (r'C:[/\\]Users[/\\]\w+[/\\].*?\.(?:pkl|json|pdf)', 'WINDOWS_PATH'),
        (r'/home/\w+/.*?\.(?:pkl|json|pdf)', 'LINUX_PATH'),
        (r'data[/\\]processed[/\\][\w\-_]+\.pkl', 'RELATIVE_PATH')
    ]
    
    @staticmethod
    def find_hardcoded_paths(directory: Path) -> List[Tuple[Path, int, str, str]]:
        """Encuentra todas las rutas hardcodeadas en el proyecto"""
        issues = []
        
        for py_file in directory.rglob('*.py'):
            # Saltar archivos en directorios de caché
            if '__pycache__' in str(py_file) or '.git' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, path_type in PathMigrator.PATTERNS:
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                issues.append((
                                    py_file,
                                    line_num,
                                    match.group(0),
                                    path_type
                                ))
            except Exception as e:
                print(f"Error leyendo {py_file}: {e}")
        
        return issues
    
    @staticmethod
    def generate_migration_report(issues: List[Tuple[Path, int, str, str]]) -> None:
        """Genera reporte de rutas a migrar"""
        print("\n🔍 REPORTE DE RUTAS HARDCODEADAS")
        print("=" * 80)
        
        if not issues:
            print("✅ No se encontraron rutas hardcodeadas!")
            return
        
        # Agrupar por archivo
        by_file = {}
        for file_path, line_num, path, path_type in issues:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((line_num, path, path_type))
        
        for file_path, file_issues in by_file.items():
            print(f"\n📄 {file_path}")
            for line_num, path, path_type in file_issues:
                print(f"   Línea {line_num}: {path} [{path_type}]")
                
                # Sugerir reemplazo
                if 'vectorstore' in path:
                    print(f"   ✏️  Sugerencia: SecurityConfig.VECTORSTORE_PATH")
                elif 'chunks' in path:
                    print(f"   ✏️  Sugerencia: SecurityConfig.CHUNKS_PATH")
                elif '.pdf' in path:
                    print(f"   ✏️  Sugerencia: SecurityConfig.get_safe_path('data/raw/archivo.pdf')")
        
        print(f"\n📊 Total: {len(issues)} rutas hardcodeadas en {len(by_file)} archivos")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    issues = PathMigrator.find_hardcoded_paths(project_root)
    PathMigrator.generate_migration_report(issues) 
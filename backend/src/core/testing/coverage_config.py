"""
Configuración profesional de coverage para testing
Métricas de calidad del código y reports automáticos
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class CoverageManager:
    """Manager para ejecutar y analizar coverage"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.coverage_dir = self.project_root / "coverage_reports"
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_tests_with_coverage(
        self, 
        test_path: str = "backend/tests/", 
        min_coverage: int = 80
    ) -> Dict[str, Any]:
        """Ejecutar tests con coverage"""
        
        print("🧪 Ejecutando tests con coverage...")
        
        # Comando coverage
        commands = [
            # Limpiar coverage anterior
            ["coverage", "erase"],
            
            # Ejecutar tests con coverage
            [
                "coverage", "run", 
                "--source=backend/src",
                "--omit=*/tests/*,*/venv/*,*/__pycache__/*",
                "-m", "pytest", 
                test_path, 
                "-v", 
                "--tb=short"
            ],
            
            # Generar report de consola
            ["coverage", "report", "--show-missing"],
            
            # Generar HTML report
            ["coverage", "html", f"--directory={self.coverage_dir}/html"],
            
            # Generar XML report
            ["coverage", "xml", f"-o", f"{self.coverage_dir}/coverage.xml"],
            
            # Generar JSON report
            ["coverage", "json", f"-o", f"{self.coverage_dir}/coverage.json"]
        ]
        
        results = {}
        
        for i, cmd in enumerate(commands):
            try:
                print(f"📋 Ejecutando: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=self.project_root
                )
                
                if result.returncode != 0:
                    print(f"⚠️ Warning en comando {i}: {result.stderr}")
                else:
                    print(f"✅ Comando {i} exitoso")
                
                results[f"cmd_{i}"] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            except Exception as e:
                print(f"❌ Error en comando {i}: {e}")
                results[f"cmd_{i}"] = {"error": str(e)}
        
        # Analizar resultados
        coverage_data = self._analyze_coverage_results()
        
        # Verificar umbral mínimo
        if coverage_data.get("total_coverage", 0) < min_coverage:
            print(f"❌ Coverage {coverage_data.get('total_coverage', 0)}% está debajo del mínimo {min_coverage}%")
        else:
            print(f"✅ Coverage {coverage_data.get('total_coverage', 0)}% supera el mínimo {min_coverage}%")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "commands_executed": results,
            "coverage_data": coverage_data,
            "min_coverage": min_coverage,
            "passed_threshold": coverage_data.get("total_coverage", 0) >= min_coverage
        }
    
    def _analyze_coverage_results(self) -> Dict[str, Any]:
        """Analizar resultados de coverage"""
        try:
            json_file = self.coverage_dir / "coverage.json"
            
            if not json_file.exists():
                return {"error": "Archivo coverage.json no encontrado"}
            
            with open(json_file, 'r') as f:
                coverage_data = json.load(f)
            
            # Extraer métricas principales
            totals = coverage_data.get("totals", {})
            
            analyzed_data = {
                "total_coverage": round(totals.get("percent_covered", 0), 2),
                "lines_covered": totals.get("covered_lines", 0),
                "lines_total": totals.get("num_statements", 0),
                "lines_missing": totals.get("missing_lines", 0),
                "branches_covered": totals.get("covered_branches", 0),
                "branches_total": totals.get("num_branches", 0),
                "files_analyzed": len(coverage_data.get("files", {}))
            }
            
            # Análisis por archivo
            files_coverage = {}
            for file_path, file_data in coverage_data.get("files", {}).items():
                file_summary = file_data.get("summary", {})
                files_coverage[file_path] = {
                    "coverage": round(file_summary.get("percent_covered", 0), 2),
                    "lines_covered": file_summary.get("covered_lines", 0),
                    "lines_total": file_summary.get("num_statements", 0),
                    "missing_lines": file_data.get("missing_lines", [])
                }
            
            analyzed_data["files_coverage"] = files_coverage
            
            # Identificar archivos con cobertura baja
            low_coverage_files = {
                file_path: data 
                for file_path, data in files_coverage.items() 
                if data["coverage"] < 70  # Umbral de 70%
            }
            
            analyzed_data["low_coverage_files"] = low_coverage_files
            
            return analyzed_data
            
        except Exception as e:
            return {"error": f"Error analizando coverage: {str(e)}"}
    
    def generate_coverage_report(self) -> str:
        """Generar reporte de coverage legible"""
        coverage_data = self._analyze_coverage_results()
        
        if "error" in coverage_data:
            return f"❌ Error: {coverage_data['error']}"
        
        report = f"""
📊 **REPORTE DE COBERTURA DE CÓDIGO**
{'='*50}

📈 **MÉTRICAS PRINCIPALES:**
• Cobertura total: {coverage_data['total_coverage']}%
• Líneas cubiertas: {coverage_data['lines_covered']}/{coverage_data['lines_total']}
• Líneas faltantes: {coverage_data['lines_missing']}
• Archivos analizados: {coverage_data['files_analyzed']}

🎯 **ESTADO DE COBERTURA:**
"""
        
        if coverage_data['total_coverage'] >= 80:
            report += "✅ EXCELENTE - Cobertura superior al 80%\n"
        elif coverage_data['total_coverage'] >= 70:
            report += "✅ BUENO - Cobertura aceptable\n"
        elif coverage_data['total_coverage'] >= 60:
            report += "⚠️ REGULAR - Mejorar cobertura\n"
        else:
            report += "❌ BAJO - Cobertura insuficiente\n"
        
        # Archivos con baja cobertura
        low_coverage = coverage_data.get('low_coverage_files', {})
        if low_coverage:
            report += f"\n⚠️ **ARCHIVOS CON BAJA COBERTURA (<70%):**\n"
            for file_path, data in low_coverage.items():
                short_path = file_path.split('/')[-2:] if '/' in file_path else [file_path]
                report += f"• {'/'.join(short_path)}: {data['coverage']}%\n"
        
        # Top archivos con buena cobertura
        good_coverage = {
            file_path: data 
            for file_path, data in coverage_data.get('files_coverage', {}).items() 
            if data['coverage'] >= 90
        }
        
        if good_coverage:
            report += f"\n✅ **ARCHIVOS CON EXCELENTE COBERTURA (≥90%):**\n"
            for file_path, data in list(good_coverage.items())[:5]:  # Top 5
                short_path = file_path.split('/')[-2:] if '/' in file_path else [file_path]
                report += f"• {'/'.join(short_path)}: {data['coverage']}%\n"
        
        report += f"""
📁 **ARCHIVOS DE REPORTE:**
• HTML: {self.coverage_dir}/html/index.html
• XML: {self.coverage_dir}/coverage.xml
• JSON: {self.coverage_dir}/coverage.json

💡 **COMANDOS ÚTILES:**
coverage run --source=backend/src -m pytest backend/tests/ -v
coverage report --show-missing
coverage html --directory=coverage_reports/html
"""
        
        return report
    
    def check_coverage_diff(self, baseline_file: str = None) -> Dict[str, Any]:
        """Comparar coverage actual vs baseline"""
        current_data = self._analyze_coverage_results()
        
        if not baseline_file:
            baseline_file = self.coverage_dir / "baseline_coverage.json"
        
        if not Path(baseline_file).exists():
            # Crear baseline si no existe
            with open(baseline_file, 'w') as f:
                json.dump(current_data, f, indent=2)
            return {"message": "Baseline creado", "baseline_file": str(baseline_file)}
        
        # Cargar baseline
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        
        # Comparar
        current_coverage = current_data.get('total_coverage', 0)
        baseline_coverage = baseline_data.get('total_coverage', 0)
        
        diff = current_coverage - baseline_coverage
        
        return {
            "current_coverage": current_coverage,
            "baseline_coverage": baseline_coverage,
            "difference": round(diff, 2),
            "improved": diff > 0,
            "degraded": diff < -1.0,  # Tolerancia de 1%
            "files_improved": [],  # TODO: implementar comparación por archivo
            "files_degraded": []
        }

# Funciones de utilidad
def run_quick_coverage():
    """Función rápida para ejecutar coverage"""
    manager = CoverageManager()
    results = manager.run_tests_with_coverage()
    report = manager.generate_coverage_report()
    
    print(report)
    
    return results

def setup_coverage_githooks():
    """Configurar git hooks para coverage automático"""
    githook_content = """#!/bin/bash
# Pre-push hook para verificar coverage

echo "🧪 Verificando coverage antes de push..."

coverage run --source=backend/src -m pytest backend/tests/ -q
coverage_percent=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')

if [ "$coverage_percent" -lt 80 ]; then
    echo "❌ Coverage $coverage_percent% está debajo del mínimo 80%"
    echo "🔧 Ejecuta: coverage html --directory=coverage_reports/html"
    echo "🌐 Abre: coverage_reports/html/index.html"
    exit 1
fi

echo "✅ Coverage $coverage_percent% - OK para push"
"""
    
    githook_path = Path(".git/hooks/pre-push")
    githook_path.parent.mkdir(exist_ok=True)
    
    with open(githook_path, 'w') as f:
        f.write(githook_content)
    
    # Hacer ejecutable
    import stat
    githook_path.chmod(githook_path.stat().st_mode | stat.S_IEXEC)
    
    print(f"✅ Git hook configurado en {githook_path}")

if __name__ == "__main__":
    # Ejecutar coverage cuando se llama directamente
    run_quick_coverage()
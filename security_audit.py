#!/usr/bin/env python3
"""
Auditoría de seguridad completa del proyecto MINEDU
Ejecutar: python security_audit.py
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class SecurityAuditor:
    """Auditor de seguridad para el proyecto"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Ejecuta auditoría completa de seguridad"""
        print("🔒 AUDITORÍA DE SEGURIDAD MINEDU")
        print("=" * 80)
        
        # Ejecutar todas las verificaciones
        self.check_hardcoded_paths()
        self.check_pickle_usage()
        self.check_credentials()
        self.check_input_validation()
        self.check_logging_security()
        self.check_file_permissions()
        self.check_dependencies()
        self.check_security_headers()
        
        # Generar reporte
        return self.generate_report()
    
    def check_hardcoded_paths(self) -> None:
        """Verifica rutas hardcodeadas"""
        print("\n🔍 Verificando rutas hardcodeadas...")
        
        patterns = [
            r'C:[/\\]',
            r'/home/[\w]+/',
            r'/usr/local/',
            r'\\\\[\w]+'  # UNC paths
        ]
        
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern in patterns:
                    if re.search(pattern, content):
                        self.issues.append({
                            'type': 'hardcoded_path',
                            'file': str(py_file),
                            'severity': 'HIGH',
                            'description': f'Ruta hardcodeada encontrada: {pattern}'
                        })
            except:
                pass
        
        if not any(i['type'] == 'hardcoded_path' for i in self.issues):
            self.passed.append('✅ No se encontraron rutas hardcodeadas')
    
    def check_pickle_usage(self) -> None:
        """Verifica uso inseguro de pickle"""
        print("\n🔍 Verificando uso de pickle...")
        
        pickle_files = []
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                if 'pickle.load' in content and 'pickle' not in str(py_file):
                    # Verificar si hay validación
                    if 'validate' not in content and 'verify' not in content:
                        pickle_files.append(py_file)
            except:
                pass
        
        if pickle_files:
            for f in pickle_files:
                self.warnings.append({
                    'type': 'pickle_usage',
                    'file': str(f),
                    'severity': 'MEDIUM',
                    'description': 'Uso de pickle sin validación aparente'
                })
        else:
            self.passed.append('✅ Uso de pickle parece seguro o no se usa')
    
    def check_credentials(self) -> None:
        """Verifica credenciales hardcodeadas"""
        print("\n🔍 Verificando credenciales...")
        
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Verificar si es una asignación real o ejemplo
                        if 'example' not in match.group(0).lower():
                            self.issues.append({
                                'type': 'hardcoded_credential',
                                'file': str(py_file),
                                'severity': 'CRITICAL',
                                'description': f'Posible credencial hardcodeada: {match.group(0)[:30]}...'
                            })
            except:
                pass
        
        if not any(i['type'] == 'hardcoded_credential' for i in self.issues):
            self.passed.append('✅ No se encontraron credenciales hardcodeadas')
    
    def check_input_validation(self) -> None:
        """Verifica validación de entradas"""
        print("\n🔍 Verificando validación de entradas...")
        
        # Buscar funciones de búsqueda sin validación
        search_files = []
        for py_file in self.project_root.rglob('*search*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                if 'def search' in content:
                    # Verificar si hay sanitización
                    if not any(word in content for word in ['sanitize', 'validate', 'clean']):
                        search_files.append(py_file)
            except:
                pass
        
        if search_files:
            for f in search_files:
                self.warnings.append({
                    'type': 'missing_validation',
                    'file': str(f),
                    'severity': 'HIGH',
                    'description': 'Función de búsqueda sin validación aparente'
                })
        else:
            self.passed.append('✅ Funciones de búsqueda parecen tener validación')
    
    def check_logging_security(self) -> None:
        """Verifica seguridad en logs"""
        print("\n🔍 Verificando seguridad de logs...")
        
        log_issues = []
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                # Buscar logs que puedan contener info sensible
                if 'logger' in content or 'logging' in content:
                    if not any(word in content for word in ['sanitize', 'remove_pii', 'filter']):
                        if 'query' in content or 'user' in content:
                            log_issues.append(py_file)
            except:
                pass
        
        if log_issues:
            for f in log_issues:
                self.warnings.append({
                    'type': 'unsafe_logging',
                    'file': str(f),
                    'severity': 'MEDIUM',
                    'description': 'Logging sin sanitización aparente de datos sensibles'
                })
        else:
            self.passed.append('✅ Logging parece seguro')
    
    def check_file_permissions(self) -> None:
        """Verifica permisos de archivos sensibles"""
        print("\n🔍 Verificando permisos de archivos...")
        
        sensitive_files = ['.env', 'config.json', '*.key', '*.pem']
        
        for pattern in sensitive_files:
            for file in self.project_root.glob(pattern):
                if file.exists():
                    # En Windows, verificar si el archivo es de solo lectura
                    if os.name == 'nt':
                        import stat
                        mode = file.stat().st_mode
                        if mode & stat.S_IWRITE:
                            self.warnings.append({
                                'type': 'file_permissions',
                                'file': str(file),
                                'severity': 'MEDIUM',
                                'description': 'Archivo sensible con permisos de escritura'
                            })
        
        self.passed.append('✅ Verificación de permisos completada')
    
    def check_dependencies(self) -> None:
        """Verifica dependencias con vulnerabilidades conocidas"""
        print("\n🔍 Verificando dependencias...")
        
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            # Lista de dependencias con vulnerabilidades conocidas (simplificado)
            vulnerable_packages = {
                'pickle': 'Uso inseguro para deserialización',
                'flask<2.0': 'Versiones antiguas tienen vulnerabilidades de seguridad',
                'django<3.2': 'Versiones antiguas tienen vulnerabilidades de seguridad',
                'pyyaml<5.4': 'Vulnerabilidad de ejecución de código',
                'jinja2<2.11.3': 'Vulnerabilidad XSS',
                'urllib3<1.26.5': 'Vulnerabilidades de seguridad'
            }
            
            try:
                content = requirements_file.read_text()
                for package, reason in vulnerable_packages.items():
                    if package in content.lower():
                        self.warnings.append({
                            'type': 'vulnerable_dependency',
                            'file': 'requirements.txt',
                            'severity': 'HIGH',
                            'description': f'{package}: {reason}'
                        })
            except:
                pass
        
        self.passed.append('✅ Verificación de dependencias completada')
    
    def check_security_headers(self) -> None:
        """Verifica configuración de seguridad para API/Web"""
        print("\n🔍 Verificando configuración de seguridad web...")
        
        # Buscar archivos de configuración web
        web_files = list(self.project_root.rglob('*app*.py')) + \
                   list(self.project_root.rglob('*api*.py')) + \
                   list(self.project_root.rglob('*server*.py'))
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Content-Security-Policy',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        for web_file in web_files:
            if '__pycache__' in str(web_file):
                continue
                
            try:
                content = web_file.read_text(encoding='utf-8')
                missing_headers = []
                for header in security_headers:
                    if header not in content:
                        missing_headers.append(header)
                
                if missing_headers and ('flask' in content.lower() or 'fastapi' in content.lower()):
                    self.warnings.append({
                        'type': 'missing_security_headers',
                        'file': str(web_file),
                        'severity': 'MEDIUM',
                        'description': f'Headers de seguridad faltantes: {", ".join(missing_headers)}'
                    })
            except:
                pass
        
        if not web_files:
            self.passed.append('✅ No se encontraron archivos de API/Web')
        else:
            self.passed.append('✅ Verificación de headers completada')
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte de auditoría"""
        report = {
            'audit_date': datetime.now().isoformat(),
            'project_path': str(self.project_root),
            'summary': {
                'total_issues': len(self.issues),
                'total_warnings': len(self.warnings),
                'total_passed': len(self.passed),
                'critical_issues': len([i for i in self.issues if i['severity'] == 'CRITICAL']),
                'high_issues': len([i for i in self.issues if i['severity'] == 'HIGH']),
                'medium_issues': len([i for i in self.warnings if i['severity'] == 'MEDIUM'])
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'passed': self.passed,
            'recommendations': self._generate_recommendations()
        }
        
        # Mostrar resumen
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE AUDITORÍA")
        print("=" * 80)
        
        print(f"\n🚨 Problemas Críticos: {report['summary']['critical_issues']}")
        print(f"⚠️  Problemas Altos: {report['summary']['high_issues']}")
        print(f"⚡ Advertencias: {report['summary']['medium_issues']}")
        print(f"✅ Verificaciones Pasadas: {report['summary']['total_passed']}")
        
        if self.issues:
            print("\n❌ PROBLEMAS ENCONTRADOS:")
            for issue in self.issues[:5]:  # Mostrar primeros 5
                print(f"  [{issue['severity']}] {issue['description']}")
                print(f"         Archivo: {issue['file']}")
        
        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings[:5]:  # Mostrar primeras 5
                print(f"  [{warning['severity']}] {warning['description']}")
                print(f"         Archivo: {warning['file']}")
        
        # Guardar reporte
        report_file = self.project_root / 'security_audit_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte completo guardado en: {report_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los hallazgos"""
        recommendations = []
        
        if any(i['type'] == 'hardcoded_path' for i in self.issues):
            recommendations.append(
                "1. Migrar todas las rutas hardcodeadas a configuración centralizada"
            )
        
        if any(i['type'] == 'hardcoded_credential' for i in self.issues):
            recommendations.append(
                "2. Mover credenciales a variables de entorno o gestor de secretos"
            )
        
        if any(w['type'] == 'pickle_usage' for w in self.warnings):
            recommendations.append(
                "3. Reemplazar pickle por JSON para datos no complejos"
            )
        
        if any(w['type'] == 'missing_validation' for w in self.warnings):
            recommendations.append(
                "4. Implementar validación de entrada en todas las funciones de búsqueda"
            )
        
        if any(w['type'] == 'unsafe_logging' for w in self.warnings):
            recommendations.append(
                "5. Implementar filtros de sanitización en todos los loggers"
            )
        
        recommendations.append(
            "6. Implementar monitoreo continuo de seguridad"
        )
        recommendations.append(
            "7. Realizar auditorías de seguridad periódicas"
        )
        recommendations.append(
            "8. Capacitar al equipo en mejores prácticas de seguridad"
        )
        
        return recommendations

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Auditoría de seguridad MINEDU')
    parser.add_argument(
        '--path',
        type=str,
        default='.',
        help='Ruta del proyecto (default: directorio actual)'
    )
    
    args = parser.parse_args()
    project_path = Path(args.path).resolve()
    
    if not project_path.exists():
        print(f"❌ Error: La ruta {project_path} no existe")
        exit(1)
    
    auditor = SecurityAuditor(project_path)
    report = auditor.run_full_audit()
    
    # Código de salida basado en severidad
    if report['summary']['critical_issues'] > 0:
        exit(2)  # Problemas críticos
    elif report['summary']['high_issues'] > 0:
        exit(1)  # Problemas altos
    else:
        exit(0)  # Solo advertencias o todo OK 
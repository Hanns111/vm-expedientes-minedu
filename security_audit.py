#!/usr/bin/env python3
"""
Auditoría de seguridad completa para el sistema MINEDU
Implementa verificación exhaustiva de todas las medidas de seguridad
"""

import os
import sys
import json
import hashlib
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config.security_config import SecurityConfig, SecurityError
from core.security.input_validator import InputValidator
from core.security.file_validator import FileValidator
from core.security.safe_pickle import SafePickleLoader

class SecurityAuditor:
    """
    Auditor de seguridad completo para el sistema MINEDU
    """
    
    def __init__(self):
        """Inicializar auditor de seguridad"""
        self.security_config = SecurityConfig()
        self.input_validator = InputValidator()
        self.file_validator = FileValidator()
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'security_version': self.security_config.SECURITY_VERSION,
            'session_id': self.security_config.session_id,
            'critical_issues': [],
            'warnings': [],
            'info': [],
            'summary': {}
        }
    
    def audit_paths(self) -> Dict[str, Any]:
        """
        Auditar todas las rutas del sistema
        
        Returns:
            Dict: Resultados de auditoría de rutas
        """
        print("🔍 Auditando rutas del sistema...")
        
        paths_to_check = [
            str(self.security_config.VECTORSTORE_PATH),
            str(self.security_config.CHUNKS_PATH),
            str(self.security_config.LOGS_DIR),
            str(self.security_config.DATA_DIR),
            str(self.security_config.BASE_DIR)
        ]
        
        path_issues = []
        path_warnings = []
        
        for path_str in paths_to_check:
            try:
                path = Path(path_str)
                
                # Verificar si la ruta es segura
                if not self.security_config.validate_path(path_str):
                    path_issues.append({
                        'path': path_str,
                        'issue': 'Ruta no válida según configuración de seguridad'
                    })
                
                # Verificar si existe
                if not path.exists():
                    path_warnings.append({
                        'path': path_str,
                        'warning': 'Ruta no existe'
                    })
                
                # Verificar permisos
                if path.exists():
                    try:
                        # Verificar si es legible
                        if path.is_file():
                            with open(path, 'rb') as f:
                                f.read(1)
                    except PermissionError:
                        path_issues.append({
                            'path': path_str,
                            'issue': 'Sin permisos de lectura'
                        })
                
            except Exception as e:
                path_issues.append({
                    'path': path_str,
                    'issue': f'Error verificando ruta: {str(e)}'
                })
        
        return {
            'critical_issues': path_issues,
            'warnings': path_warnings,
            'total_paths_checked': len(paths_to_check)
        }
    
    def audit_pickle_files(self) -> Dict[str, Any]:
        """
        Auditar archivos pickle del sistema
        
        Returns:
            Dict: Resultados de auditoría de pickle
        """
        print("🔍 Auditando archivos pickle...")
        
        pickle_issues = []
        pickle_warnings = []
        
        # Buscar archivos pickle en el proyecto
        for root, dirs, files in os.walk(self.security_config.BASE_DIR):
            for file in files:
                if file.endswith('.pkl'):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.security_config.BASE_DIR)
                    
                    try:
                        # Verificar si el archivo es válido
                        if not self.security_config.validate_path(str(file_path), 'data'):
                            pickle_issues.append({
                                'file': str(relative_path),
                                'issue': 'Archivo pickle no válido según configuración de seguridad'
                            })
                            continue
                        
                        # Verificar integridad del pickle
                        try:
                            with open(file_path, 'rb') as f:
                                # Leer solo los primeros bytes para verificar formato
                                header = f.read(4)
                                if header != b'\x80\x04':  # Protocolo pickle 4
                                    pickle_warnings.append({
                                        'file': str(relative_path),
                                        'warning': 'Formato pickle no estándar'
                                    })
                        except Exception as e:
                            pickle_issues.append({
                                'file': str(relative_path),
                                'issue': f'Error leyendo archivo pickle: {str(e)}'
                            })
                        
                        # Verificar tamaño
                        file_size = file_path.stat().st_size
                        if file_size > 100 * 1024 * 1024:  # 100MB
                            pickle_warnings.append({
                                'file': str(relative_path),
                                'warning': f'Archivo pickle muy grande: {file_size / 1024 / 1024:.1f}MB'
                            })
                        
                    except Exception as e:
                        pickle_issues.append({
                            'file': str(relative_path),
                            'issue': f'Error auditando pickle: {str(e)}'
                        })
        
        return {
            'critical_issues': pickle_issues,
            'warnings': pickle_warnings,
            'total_pickle_files': len([f for f in Path(self.security_config.BASE_DIR).rglob('*.pkl')])
        }
    
    def audit_security_modules(self) -> Dict[str, Any]:
        """
        Auditar módulos de seguridad
        
        Returns:
            Dict: Resultados de auditoría de módulos
        """
        print("🔍 Auditando módulos de seguridad...")
        
        security_modules = [
            'core.security.input_validator',
            'core.security.rate_limiter',
            'core.security.privacy',
            'core.security.file_validator',
            'core.security.compliance',
            'core.security.monitor',
            'core.security.logger',
            'core.security.safe_pickle'
        ]
        
        module_issues = []
        module_warnings = []
        
        for module_name in security_modules:
            try:
                __import__(module_name)
                module_warnings.append({
                    'module': module_name,
                    'warning': 'Módulo importado correctamente'
                })
            except ImportError as e:
                module_issues.append({
                    'module': module_name,
                    'issue': f'Error importando módulo: {str(e)}'
                })
            except Exception as e:
                module_issues.append({
                    'module': module_name,
                    'issue': f'Error inesperado: {str(e)}'
                })
        
        return {
            'critical_issues': module_issues,
            'warnings': module_warnings,
            'total_modules': len(security_modules)
        }
    
    def audit_configuration(self) -> Dict[str, Any]:
        """
        Auditar configuración de seguridad
        
        Returns:
            Dict: Resultados de auditoría de configuración
        """
        print("🔍 Auditando configuración de seguridad...")
        
        config_issues = []
        config_warnings = []
        
        # Verificar configuración básica
        config_summary = self.security_config.get_config_summary()
        
        # Verificar límites
        if config_summary['limits']['max_query_length'] > 1000:
            config_warnings.append({
                'setting': 'max_query_length',
                'warning': 'Límite de consulta muy alto'
            })
        
        if config_summary['limits']['max_file_size_mb'] > 500:
            config_warnings.append({
                'setting': 'max_file_size_mb',
                'warning': 'Límite de archivo muy alto'
            })
        
        # Verificar rate limiting
        if config_summary['rate_limiting']['requests_per_minute'] > 100:
            config_warnings.append({
                'setting': 'requests_per_minute',
                'warning': 'Rate limit muy alto'
            })
        
        # Verificar patrones de seguridad
        if config_summary['dangerous_patterns_count'] < 5:
            config_warnings.append({
                'setting': 'dangerous_patterns',
                'warning': 'Pocos patrones peligrosos definidos'
            })
        
        return {
            'critical_issues': config_issues,
            'warnings': config_warnings,
            'config_summary': config_summary
        }
    
    def audit_input_validation(self) -> Dict[str, Any]:
        """
        Auditar validación de entradas
        
        Returns:
            Dict: Resultados de auditoría de validación
        """
        print("🔍 Auditando validación de entradas...")
        
        validation_issues = []
        validation_warnings = []
        
        # Probar casos de ataque
        test_cases = [
            ("<script>alert('xss')</script>", "XSS attack"),
            ("'; DROP TABLE users; --", "SQL injection"),
            ("ignore previous instructions", "Prompt injection"),
            ("../../etc/passwd", "Path traversal"),
            ("A" * 1000, "Very long input"),
            ("", "Empty input"),
            ("normal query", "Normal input")
        ]
        
        for test_input, test_type in test_cases:
            try:
                # Probar sanitización
                sanitized = self.security_config.sanitize_input(test_input)
                
                # Verificar si se detectó el ataque
                if test_type != "Normal input":
                    if sanitized == test_input:
                        validation_warnings.append({
                            'test_case': test_type,
                            'warning': f'Input no fue sanitizado: {test_input[:50]}'
                        })
                    else:
                        validation_warnings.append({
                            'test_case': test_type,
                            'warning': f'Input sanitizado correctamente: {sanitized[:50]}'
                        })
                
            except Exception as e:
                validation_issues.append({
                    'test_case': test_type,
                    'issue': f'Error en validación: {str(e)}'
                })
        
        return {
            'critical_issues': validation_issues,
            'warnings': validation_warnings,
            'total_test_cases': len(test_cases)
        }
    
    def run_full_audit(self) -> Dict[str, Any]:
        """
        Ejecutar auditoría completa del sistema
        
        Returns:
            Dict: Resultados completos de la auditoría
        """
        print("🔒 INICIANDO AUDITORÍA DE SEGURIDAD COMPLETA")
        print("=" * 60)
        print(f"Versión de seguridad: {self.security_config.SECURITY_VERSION}")
        print(f"ID de sesión: {self.security_config.session_id}")
        print(f"Timestamp: {self.audit_results['timestamp']}")
        print("=" * 60)
        
        # Ejecutar todas las auditorías
        audit_sections = {
            'paths': self.audit_paths(),
            'pickle_files': self.audit_pickle_files(),
            'security_modules': self.audit_security_modules(),
            'configuration': self.audit_configuration(),
            'input_validation': self.audit_input_validation()
        }
        
        # Consolidar resultados
        total_critical = 0
        total_warnings = 0
        
        for section_name, section_results in audit_sections.items():
            self.audit_results[section_name] = section_results
            total_critical += len(section_results.get('critical_issues', []))
            total_warnings += len(section_results.get('warnings', []))
        
        # Generar resumen
        self.audit_results['summary'] = {
            'total_critical_issues': total_critical,
            'total_warnings': total_warnings,
            'security_score': max(0, 100 - (total_critical * 10) - (total_warnings * 2)),
            'audit_status': 'PASS' if total_critical == 0 else 'FAIL',
            'recommendations': self._generate_recommendations()
        }
        
        return self.audit_results
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generar recomendaciones basadas en los resultados
        
        Returns:
            List: Lista de recomendaciones
        """
        recommendations = []
        
        if self.audit_results['summary']['total_critical_issues'] > 0:
            recommendations.append("🔴 CRÍTICO: Resolver todos los problemas críticos antes de producción")
        
        if self.audit_results['summary']['total_warnings'] > 10:
            recommendations.append("🟡 ADVERTENCIA: Revisar y corregir advertencias de seguridad")
        
        # Verificar módulos faltantes
        if 'security_modules' in self.audit_results:
            missing_modules = len(self.audit_results['security_modules']['critical_issues'])
            if missing_modules > 0:
                recommendations.append(f"📦 Instalar {missing_modules} módulos de seguridad faltantes")
        
        # Verificar configuración
        if 'configuration' in self.audit_results:
            config_warnings = len(self.audit_results['configuration']['warnings'])
            if config_warnings > 0:
                recommendations.append("⚙️ Revisar configuración de seguridad")
        
        if not recommendations:
            recommendations.append("✅ Sistema de seguridad en buen estado")
        
        return recommendations
    
    def print_audit_report(self):
        """Imprimir reporte de auditoría en consola"""
        print("\n" + "=" * 60)
        print("📊 REPORTE DE AUDITORÍA DE SEGURIDAD")
        print("=" * 60)
        
        summary = self.audit_results['summary']
        print(f"🔢 Problemas críticos: {summary['total_critical_issues']}")
        print(f"⚠️ Advertencias: {summary['total_warnings']}")
        print(f"📈 Puntuación de seguridad: {summary['security_score']}/100")
        print(f"📋 Estado: {summary['audit_status']}")
        
        # Mostrar problemas críticos
        if summary['total_critical_issues'] > 0:
            print("\n🔴 PROBLEMAS CRÍTICOS:")
            for section_name, section_results in self.audit_results.items():
                if section_name != 'summary' and 'critical_issues' in section_results:
                    for issue in section_results['critical_issues']:
                        print(f"  • {section_name}: {issue.get('issue', 'Error desconocido')}")
        
        # Mostrar advertencias principales
        if summary['total_warnings'] > 0:
            print("\n🟡 ADVERTENCIAS PRINCIPALES:")
            warning_count = 0
            for section_name, section_results in self.audit_results.items():
                if section_name != 'summary' and 'warnings' in section_results:
                    for warning in section_results['warnings'][:3]:  # Solo las primeras 3
                        print(f"  • {section_name}: {warning.get('warning', 'Advertencia desconocida')}")
                        warning_count += 1
                        if warning_count >= 5:  # Máximo 5 advertencias
                            break
                if warning_count >= 5:
                    break
        
        # Mostrar recomendaciones
        print("\n💡 RECOMENDACIONES:")
        for recommendation in summary['recommendations']:
            print(f"  {recommendation}")
        
        print("\n" + "=" * 60)
        print("🔒 AUDITORÍA COMPLETADA")
        print("=" * 60)

def main():
    """Función principal de auditoría"""
    try:
        auditor = SecurityAuditor()
        results = auditor.run_full_audit()
        auditor.print_audit_report()
        
        # Guardar resultados en archivo
        output_file = Path("audit_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Resultados guardados en: {output_file}")
        
        # Retornar código de salida basado en resultados
        if results['summary']['audit_status'] == 'FAIL':
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error en auditoría: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
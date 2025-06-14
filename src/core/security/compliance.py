"""
Logger de cumplimiento para normativas MINEDU y gobierno peruano
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple, List
from enum import Enum
from src.core.config.security_config import SecurityConfig

class AuditEventType(Enum):
    """Tipos de eventos para auditoría"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SEARCH = "SEARCH"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    ADMIN_ACTION = "ADMIN_ACTION"
    SECURITY_ALERT = "SECURITY_ALERT"
    ACCESS_DENIED = "ACCESS_DENIED"
    ERROR = "ERROR"

class ComplianceLogger:
    """Logger de cumplimiento para normativas MINEDU y gobierno peruano"""
    
    def __init__(self):
        # Crear directorio de logs si no existe
        SecurityConfig.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.audit_file = SecurityConfig.AUDIT_LOG_FILE
        self.security_file = SecurityConfig.SECURITY_LOG_FILE
    
    def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Registra un evento de auditoría según normativas de cumplimiento
        
        Args:
            event_type: Tipo de evento
            user_id: ID del usuario
            details: Detalles del evento
            ip_address: IP del usuario
            session_id: ID de sesión
        """
        # Crear entrada de auditoría
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'user_hash': hashlib.sha256(user_id.encode()).hexdigest()[:16],
            'ip_hash': hashlib.sha256(ip_address.encode()).hexdigest()[:16] if ip_address else None,
            'session_hash': hashlib.sha256(session_id.encode()).hexdigest()[:16] if session_id else None,
            'success': details.get('success', True),
            'resource': details.get('resource', 'N/A'),
            'action': details.get('action', 'N/A'),
            'metadata': self._sanitize_details(details)
        }
        
        # Escribir al log de auditoría (append-only)
        with open(self.audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')
    
    def log_security_event(
        self,
        severity: str,
        event_description: str,
        user_id: Optional[str] = None,
        additional_info: Optional[Dict] = None
    ) -> None:
        """
        Registra un evento de seguridad
        
        Args:
            severity: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
            event_description: Descripción del evento
            user_id: ID del usuario (opcional)
            additional_info: Información adicional
        """
        security_entry = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'description': event_description,
            'user_hash': hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else None,
            'additional_info': self._sanitize_details(additional_info or {})
        }
        
        with open(self.security_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(security_entry, ensure_ascii=False) + '\n')
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Sanitiza detalles para no incluir información sensible"""
        from src.core.security.privacy import PrivacyProtector
        
        sanitized = {}
        for key, value in details.items():
            if isinstance(value, str):
                sanitized[key] = PrivacyProtector.remove_pii(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(type(value))
        
        return sanitized
    
    def verify_access_hours(self, user_role: str = 'user') -> Tuple[bool, Optional[str]]:
        """
        Verifica si el acceso está permitido en el horario actual
        
        Args:
            user_role: Rol del usuario (admin tiene acceso 24/7)
            
        Returns:
            (permitido, mensaje)
        """
        if user_role == 'admin':
            return True, None
        
        current_hour = datetime.now().hour
        
        if (SecurityConfig.ALLOWED_HOURS['start'] <= current_hour < SecurityConfig.ALLOWED_HOURS['end']):
            return True, None
        else:
            return False, f"Acceso fuera de horario permitido ({SecurityConfig.ALLOWED_HOURS['start']}:00 - {SecurityConfig.ALLOWED_HOURS['end']}:00)"
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Genera reporte de cumplimiento para auditorías gubernamentales
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Reporte de cumplimiento
        """
        events = []
        security_incidents = []
        
        # Leer eventos de auditoría
        if self.audit_file.exists():
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event['timestamp'])
                        if start_date <= event_time <= end_date:
                            events.append(event)
                    except:
                        continue
        
        # Leer incidentes de seguridad
        if self.security_file.exists():
            with open(self.security_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        incident = json.loads(line)
                        incident_time = datetime.fromisoformat(incident['timestamp'])
                        if start_date <= incident_time <= end_date:
                            security_incidents.append(incident)
                    except:
                        continue
        
        # Generar estadísticas
        event_counts = {}
        for event in events:
            event_type = event.get('event_type', 'UNKNOWN')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_events': len(events),
            'event_breakdown': event_counts,
            'security_incidents': len(security_incidents),
            'failed_attempts': sum(1 for e in events if not e.get('success', True)),
            'unique_users': len(set(e.get('user_hash', '') for e in events)),
            'compliance_status': 'COMPLIANT' if len(security_incidents) == 0 else 'REVIEW_REQUIRED',
            'generated_at': datetime.now().isoformat()
        }

class ComplianceChecker:
    """
    Verificador de cumplimiento para normativas gubernamentales peruanas
    Implementa verificaciones específicas para MINEDU y estándares de gobierno
    """
    
    def __init__(self):
        """Inicializar verificador de cumplimiento"""
        self.security_config = SecurityConfig()
        self.compliance_logger = ComplianceLogger()
        
        # Estándares de cumplimiento gubernamental
        self.compliance_standards = {
            'ISO27001': {
                'access_control': True,
                'audit_logging': True,
                'data_protection': True,
                'incident_response': True
            },
            'NIST_Cybersecurity': {
                'identify': True,
                'protect': True,
                'detect': True,
                'respond': True,
                'recover': True
            },
            'MINEDU_Standards': {
                'data_retention': 365,  # días
                'audit_retention': 730,  # días
                'pii_protection': True,
                'access_controls': True,
                'security_monitoring': True
            }
        }
    
    def check_data_retention_compliance(self) -> Dict[str, Any]:
        """
        Verificar cumplimiento de retención de datos
        
        Returns:
            Dict: Resultados de verificación
        """
        retention_issues = []
        compliance_status = True
        
        # Verificar logs de auditoría
        if self.security_config.AUDIT_LOG_FILE.exists():
            file_age = datetime.now() - datetime.fromtimestamp(
                self.security_config.AUDIT_LOG_FILE.stat().st_mtime
            )
            if file_age.days > self.compliance_standards['MINEDU_Standards']['audit_retention']:
                retention_issues.append({
                    'file': 'audit.log',
                    'issue': f'Log de auditoría más antiguo que {self.compliance_standards["MINEDU_Standards"]["audit_retention"]} días'
                })
                compliance_status = False
        
        # Verificar logs de seguridad
        if self.security_config.SECURITY_LOG_FILE.exists():
            file_age = datetime.now() - datetime.fromtimestamp(
                self.security_config.SECURITY_LOG_FILE.stat().st_mtime
            )
            if file_age.days > self.compliance_standards['MINEDU_Standards']['data_retention']:
                retention_issues.append({
                    'file': 'security.log',
                    'issue': f'Log de seguridad más antiguo que {self.compliance_standards["MINEDU_Standards"]["data_retention"]} días'
                })
                compliance_status = False
        
        return {
            'compliant': compliance_status,
            'issues': retention_issues,
            'standard': 'MINEDU_Standards',
            'checked_at': datetime.now().isoformat()
        }
    
    def check_access_control_compliance(self) -> Dict[str, Any]:
        """
        Verificar cumplimiento de controles de acceso
        
        Returns:
            Dict: Resultados de verificación
        """
        access_issues = []
        compliance_status = True
        
        # Verificar configuración de rate limiting
        if self.security_config.REQUESTS_PER_MINUTE > 100:
            access_issues.append({
                'setting': 'requests_per_minute',
                'issue': 'Rate limit muy alto para cumplimiento gubernamental'
            })
            compliance_status = False
        
        # Verificar límites de consulta
        if self.security_config.MAX_QUERY_LENGTH > 1000:
            access_issues.append({
                'setting': 'max_query_length',
                'issue': 'Límite de consulta muy alto'
            })
            compliance_status = False
        
        # Verificar horarios de acceso
        if not hasattr(self.security_config, 'ALLOWED_HOURS'):
            access_issues.append({
                'setting': 'allowed_hours',
                'issue': 'Horarios de acceso no configurados'
            })
            compliance_status = False
        
        return {
            'compliant': compliance_status,
            'issues': access_issues,
            'standard': 'ISO27001',
            'checked_at': datetime.now().isoformat()
        }
    
    def check_data_protection_compliance(self) -> Dict[str, Any]:
        """
        Verificar cumplimiento de protección de datos
        
        Returns:
            Dict: Resultados de verificación
        """
        protection_issues = []
        compliance_status = True
        
        # Verificar patrones de PII
        if len(self.security_config.PII_PATTERNS) < 3:
            protection_issues.append({
                'setting': 'pii_patterns',
                'issue': 'Pocos patrones de PII configurados'
            })
            compliance_status = False
        
        # Verificar patrones peligrosos
        if len(self.security_config.DANGEROUS_PATTERNS) < 5:
            protection_issues.append({
                'setting': 'dangerous_patterns',
                'issue': 'Pocos patrones peligrosos configurados'
            })
            compliance_status = False
        
        # Verificar validación de archivos
        if len(self.security_config.ALLOWED_FILE_EXTENSIONS) < 3:
            protection_issues.append({
                'setting': 'allowed_extensions',
                'issue': 'Pocas extensiones de archivo permitidas'
            })
            compliance_status = False
        
        return {
            'compliant': compliance_status,
            'issues': protection_issues,
            'standard': 'NIST_Cybersecurity',
            'checked_at': datetime.now().isoformat()
        }
    
    def check_security_monitoring_compliance(self) -> Dict[str, Any]:
        """
        Verificar cumplimiento de monitoreo de seguridad
        
        Returns:
            Dict: Resultados de verificación
        """
        monitoring_issues = []
        compliance_status = True
        
        # Verificar que los logs existen
        if not self.security_config.LOGS_DIR.exists():
            monitoring_issues.append({
                'component': 'logs_directory',
                'issue': 'Directorio de logs no existe'
            })
            compliance_status = False
        
        # Verificar que los archivos de log son escribibles
        try:
            test_log = self.security_config.LOGS_DIR / "compliance_test.log"
            with open(test_log, 'w') as f:
                f.write("test")
            test_log.unlink()  # Limpiar archivo de prueba
        except Exception as e:
            monitoring_issues.append({
                'component': 'log_writing',
                'issue': f'No se puede escribir en logs: {str(e)}'
            })
            compliance_status = False
        
        return {
            'compliant': compliance_status,
            'issues': monitoring_issues,
            'standard': 'MINEDU_Standards',
            'checked_at': datetime.now().isoformat()
        }
    
    def run_full_compliance_check(self) -> Dict[str, Any]:
        """
        Ejecutar verificación completa de cumplimiento
        
        Returns:
            Dict: Resultados completos de cumplimiento
        """
        print("🔍 Ejecutando verificación completa de cumplimiento...")
        
        checks = {
            'data_retention': self.check_data_retention_compliance(),
            'access_control': self.check_access_control_compliance(),
            'data_protection': self.check_data_protection_compliance(),
            'security_monitoring': self.check_security_monitoring_compliance()
        }
        
        # Calcular puntuación general
        total_checks = len(checks)
        compliant_checks = sum(1 for check in checks.values() if check['compliant'])
        compliance_score = (compliant_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Determinar estado general
        if compliance_score >= 95:
            overall_status = 'FULLY_COMPLIANT'
        elif compliance_score >= 80:
            overall_status = 'MOSTLY_COMPLIANT'
        else:
            overall_status = 'NON_COMPLIANT'
        
        # Generar recomendaciones
        recommendations = []
        for check_name, check_result in checks.items():
            if not check_result['compliant']:
                recommendations.append(f"Revisar {check_name}: {len(check_result['issues'])} problemas encontrados")
        
        if not recommendations:
            recommendations.append("Sistema cumple con todas las normativas verificadas")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'compliance_score': compliance_score,
            'total_checks': total_checks,
            'compliant_checks': compliant_checks,
            'checks': checks,
            'recommendations': recommendations,
            'standards_checked': list(self.compliance_standards.keys())
        }
        
        # Registrar evento de cumplimiento
        self.compliance_logger.log_audit_event(
            event_type=AuditEventType.ADMIN_ACTION,
            user_id='system',
            details={
                'action': 'compliance_check',
                'success': overall_status == 'FULLY_COMPLIANT',
                'score': compliance_score,
                'status': overall_status
            }
        )
        
        return result
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de cumplimiento
        
        Returns:
            Dict: Resumen de cumplimiento
        """
        return {
            'standards': self.compliance_standards,
            'config_summary': self.security_config.get_config_summary(),
            'last_check': datetime.now().isoformat()
        }

# Instancia global del logger de cumplimiento
compliance_logger = ComplianceLogger() 
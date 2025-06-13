"""
Logger de cumplimiento para normativas MINEDU y gobierno peruano
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
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

# Instancia global del logger de cumplimiento
compliance_logger = ComplianceLogger() 
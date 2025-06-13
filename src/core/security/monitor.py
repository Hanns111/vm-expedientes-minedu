"""
Monitor de seguridad en tiempo real para detectar amenazas
"""
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
from typing import Dict, List, Set
from src.core.config.security_config import SecurityConfig
from src.core.security.compliance import compliance_logger, AuditEventType

class SecurityMonitor:
    """Monitor de seguridad en tiempo real para detectar amenazas"""
    
    def __init__(self):
        # Contadores para detección de anomalías
        self.query_history: Dict[str, List[datetime]] = defaultdict(list)
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Set[str] = set()
        
        # Umbrales
        self.ANOMALY_THRESHOLD = 5
        self.FAILED_LOGIN_THRESHOLD = 3
        self.PATTERN_THRESHOLD = 3
    
    def monitor_query(self, user_id: str, query: str, ip_address: str) -> None:
        """
        Monitorea una consulta en busca de comportamiento anómalo
        
        Args:
            user_id: ID del usuario
            query: Consulta realizada
            ip_address: IP del usuario
        """
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:16]
        
        # Limpiar historial antiguo
        self._clean_old_history()
        
        # Detectar consultas repetitivas (posible bot)
        key = f"{user_hash}:{query_hash}"
        self.query_history[key].append(datetime.now())
        
        if len(self.query_history[key]) > self.ANOMALY_THRESHOLD:
            self._raise_security_alert(
                severity="WARNING",
                description=f"Consultas repetitivas detectadas",
                user_id=user_id,
                details={
                    'pattern': 'repetitive_queries',
                    'count': len(self.query_history[key]),
                    'query_hash': query_hash
                }
            )
        
        # Detectar patrones sospechosos
        if self._contains_suspicious_patterns(query):
            pattern_key = f"{user_hash}:suspicious"
            self.suspicious_patterns[pattern_key] += 1
            
            if self.suspicious_patterns[pattern_key] >= self.PATTERN_THRESHOLD:
                self._raise_security_alert(
                    severity="CRITICAL",
                    description="Múltiples patrones sospechosos detectados",
                    user_id=user_id,
                    details={
                        'pattern': 'suspicious_queries',
                        'count': self.suspicious_patterns[pattern_key]
                    }
                )
                # Bloquear IP
                self.blocked_ips.add(ip_address)
    
    def monitor_failed_login(self, user_id: str, ip_address: str) -> None:
        """Monitorea intentos fallidos de login"""
        key = f"{user_id}:{ip_address}"
        self.failed_attempts[key] += 1
        
        if self.failed_attempts[key] >= self.FAILED_LOGIN_THRESHOLD:
            self._raise_security_alert(
                severity="WARNING",
                description="Múltiples intentos de login fallidos",
                user_id=user_id,
                details={
                    'pattern': 'failed_login',
                    'attempts': self.failed_attempts[key],
                    'ip_address': ip_address
                }
            )
            # Bloquear IP después de muchos intentos
            if self.failed_attempts[key] >= self.FAILED_LOGIN_THRESHOLD * 2:
                self.blocked_ips.add(ip_address)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Verifica si una IP está bloqueada"""
        return ip_address in self.blocked_ips
    
    def _contains_suspicious_patterns(self, query: str) -> bool:
        """Detecta patrones sospechosos en la consulta"""
        query_lower = query.lower()
        
        # Patrones de SQL injection
        sql_patterns = ['union select', 'drop table', '1=1', 'or 1=1']
        
        # Patrones de XSS
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=']
        
        # Patrones de path traversal
        path_patterns = ['../', '..\\', '%2e%2e', '../..']
        
        all_patterns = sql_patterns + xss_patterns + path_patterns
        
        return any(pattern in query_lower for pattern in all_patterns)
    
    def _clean_old_history(self) -> None:
        """Limpia historial antiguo para liberar memoria"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Limpiar historial de consultas
        for key in list(self.query_history.keys()):
            self.query_history[key] = [
                timestamp for timestamp in self.query_history[key]
                if timestamp > cutoff_time
            ]
            if not self.query_history[key]:
                del self.query_history[key]
    
    def _raise_security_alert(
        self, 
        severity: str, 
        description: str, 
        user_id: str, 
        details: Dict
    ) -> None:
        """Genera una alerta de seguridad"""
        # Registrar en log de seguridad
        compliance_logger.log_security_event(
            severity=severity,
            event_description=description,
            user_id=user_id,
            additional_info=details
        )
        
        # En producción: enviar notificación al equipo de seguridad
        # self._send_security_notification(severity, description, details)
    
    def get_security_status(self) -> Dict:
        """Obtiene el estado actual de seguridad"""
        return {
            'active_monitors': len(self.query_history),
            'blocked_ips': len(self.blocked_ips),
            'suspicious_users': len(self.suspicious_patterns),
            'failed_login_attempts': sum(self.failed_attempts.values()),
            'status': 'SECURE' if len(self.blocked_ips) == 0 else 'THREATS_DETECTED'
        }
    
    def unblock_ip(self, ip_address: str) -> None:
        """Desbloquea una IP (solo para administradores)"""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            compliance_logger.log_security_event(
                severity="INFO",
                event_description=f"IP desbloqueada manualmente: {ip_address}",
                additional_info={'action': 'manual_unblock'}
            )
    
    def get_threat_summary(self) -> Dict:
        """Obtiene un resumen de amenazas detectadas"""
        return {
            'total_blocked_ips': len(self.blocked_ips),
            'blocked_ips_list': list(self.blocked_ips),
            'suspicious_activities': len(self.suspicious_patterns),
            'failed_login_attempts': sum(self.failed_attempts.values()),
            'repetitive_queries': sum(1 for queries in self.query_history.values() if len(queries) > self.ANOMALY_THRESHOLD),
            'last_cleanup': datetime.now().isoformat()
        }

# Instancia global del monitor de seguridad
security_monitor = SecurityMonitor() 
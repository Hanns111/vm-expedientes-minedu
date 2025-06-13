"""
Limitador de tasa de peticiones para prevenir abuso
"""
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
from typing import Dict, Optional, Tuple
from src.core.config.security_config import SecurityConfig

class RateLimiter:
    """Limitador de tasa de peticiones para prevenir abuso"""
    
    def __init__(self):
        # Almacenar: {user_hash: [timestamp1, timestamp2, ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._blocked_users: Dict[str, datetime] = {}
        
    def _hash_identifier(self, identifier: str) -> str:
        """Hashea el identificador del usuario para privacidad"""
        return hashlib.sha256(identifier.encode()).hexdigest()
    
    def _clean_old_requests(self, user_hash: str) -> None:
        """Elimina peticiones antiguas del registro"""
        now = datetime.now()
        # Mantener solo peticiones del último día
        self._requests[user_hash] = [
            req_time for req_time in self._requests[user_hash]
            if now - req_time < timedelta(days=1)
        ]
    
    def check_rate_limit(self, user_identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el usuario puede hacer una petición
        
        Args:
            user_identifier: ID único del usuario (IP, session_id, etc.)
            
        Returns:
            (permitido, mensaje_error)
        """
        user_hash = self._hash_identifier(user_identifier)
        now = datetime.now()
        
        # Verificar si el usuario está bloqueado
        if user_hash in self._blocked_users:
            block_until = self._blocked_users[user_hash]
            if now < block_until:
                remaining = (block_until - now).total_seconds()
                return False, f"Usuario bloqueado por {remaining:.0f} segundos más"
            else:
                del self._blocked_users[user_hash]
        
        # Limpiar peticiones antiguas
        self._clean_old_requests(user_hash)
        
        # Contar peticiones en diferentes ventanas de tiempo
        minute_requests = sum(
            1 for req_time in self._requests[user_hash]
            if now - req_time < timedelta(minutes=1)
        )
        
        hour_requests = sum(
            1 for req_time in self._requests[user_hash]
            if now - req_time < timedelta(hours=1)
        )
        
        day_requests = len(self._requests[user_hash])
        
        # Verificar límites
        if minute_requests >= SecurityConfig.REQUESTS_PER_MINUTE:
            # Bloquear por 5 minutos
            self._blocked_users[user_hash] = now + timedelta(minutes=5)
            return False, f"Límite por minuto excedido ({SecurityConfig.REQUESTS_PER_MINUTE} peticiones/minuto)"
        
        if hour_requests >= SecurityConfig.REQUESTS_PER_HOUR:
            # Bloquear por 1 hora
            self._blocked_users[user_hash] = now + timedelta(hours=1)
            return False, f"Límite por hora excedido ({SecurityConfig.REQUESTS_PER_HOUR} peticiones/hora)"
        
        if day_requests >= SecurityConfig.REQUESTS_PER_DAY:
            # Bloquear por 24 horas
            self._blocked_users[user_hash] = now + timedelta(days=1)
            return False, f"Límite diario excedido ({SecurityConfig.REQUESTS_PER_DAY} peticiones/día)"
        
        # Registrar petición
        self._requests[user_hash].append(now)
        
        return True, None
    
    def get_user_stats(self, user_identifier: str) -> Dict:
        """Obtiene estadísticas de uso del usuario"""
        user_hash = self._hash_identifier(user_identifier)
        self._clean_old_requests(user_hash)
        
        now = datetime.now()
        
        return {
            'requests_last_minute': sum(
                1 for req_time in self._requests[user_hash]
                if now - req_time < timedelta(minutes=1)
            ),
            'requests_last_hour': sum(
                1 for req_time in self._requests[user_hash]
                if now - req_time < timedelta(hours=1)
            ),
            'requests_last_day': len(self._requests[user_hash]),
            'is_blocked': user_hash in self._blocked_users
        }
    
    def reset_user_limits(self, user_identifier: str) -> None:
        """Resetea los límites para un usuario específico (solo para administradores)"""
        user_hash = self._hash_identifier(user_identifier)
        
        if user_hash in self._requests:
            del self._requests[user_hash]
        
        if user_hash in self._blocked_users:
            del self._blocked_users[user_hash]
    
    def get_system_stats(self) -> Dict:
        """Obtiene estadísticas generales del sistema"""
        now = datetime.now()
        
        total_users = len(self._requests)
        blocked_users = len(self._blocked_users)
        
        total_requests_today = sum(len(requests) for requests in self._requests.values())
        
        return {
            'total_active_users': total_users,
            'blocked_users': blocked_users,
            'total_requests_today': total_requests_today,
            'average_requests_per_user': total_requests_today / max(total_users, 1)
        }

# Instancia global del rate limiter
rate_limiter = RateLimiter() 